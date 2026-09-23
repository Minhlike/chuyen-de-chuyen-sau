# -*- coding: utf-8 -*-
"""
TemporalGraphViewEncoder: Mạng nơ-ron đồ thị động thời gian liên tục nhân quả (Causal Continuous-Time Dynamic Graph Neural Network)
cho tiền huấn luyện tự giám sát Giai đoạn A2 trên log sự kiện - thực thể (Contract V1.3 Amended).

Các bất biến (Invariants):
  1. Dự đoán trước khi cập nhật (Predict-Before-Update): Đánh giá các dự đoán SSL phụ trợ (L_rel, L_node, L_time)
     nghiêm ngặt trên các trạng thái ẩn trước đó h(t-) TRƯỚC KHI cập nhật bộ nhớ (BEFORE memory updates).
  2. Tường lửa mục tiêu quan hệ (Relation Target Firewall): Đầu vào dự đoán [h_v(t-) || h_u(t-) || phi(delta_t)]
     tuyệt đối không chứa ID quan hệ thực sự và vector nhúng quan hệ. Chính xác 8 quan hệ chuẩn.
  3. Tường lửa mục tiêu nút (Node Target Firewall): Head tái thiết dự đoán chính xác x_v_fixed_priv trong R^6
     từ h_v(t-) sử dụng Mean Squared Error (MSE), không cho phép truyền thẳng vector mục tiêu.
  4. Vector nhúng loại nút hoạt động: Nhúng loại nút nguồn và đích làm điều kiện cho hàm thông điệp thời gian Msg().
  5. Mục tiêu bậc nhân quả (Causal Degree Targets): Đặc trưng bậc được tính tại t- trước khi cạnh được cập nhật.
  6. Khởi tạo lại khi sang phân vùng (Inductive Split Reset): Toàn bộ bộ nhớ động và trạng thái tương tác được đặt về 0 tại ranh giới phân vùng.
"""

import math
from typing import Dict, Any, List, Optional, Tuple, Set

import torch
import torch.nn as nn
import torch.nn.functional as F

class TimeProjection(nn.Module):
    """Phép chiếu thời gian liên tục hình sin phi(delta_t) -> R^d_time."""
    def __init__(self, d_time: int = 32):
        super().__init__()
        self.d_time = d_time
        half_dim = d_time // 2
        inv_freq = torch.exp(
            torch.arange(0, half_dim, dtype=torch.float32) * (-math.log(10000.0) / half_dim)
        )
        self.register_buffer("inv_freq", inv_freq)

    def forward(self, delta_t: torch.Tensor) -> torch.Tensor:
        # delta_t: (B, 1) hoặc (B,) hoặc vô hướng -> trả về (B, d_time)
        if delta_t.dim() == 0:
            delta_t = delta_t.view(1, 1)
        elif delta_t.dim() == 1:
            delta_t = delta_t.unsqueeze(-1)
        phases = delta_t * self.inv_freq.unsqueeze(0) # (B, half_dim)
        proj = torch.cat([torch.sin(phases), torch.cos(phases)], dim=-1) # (B, d_time)
        return proj

class TemporalGraphViewEncoder(nn.Module):
    """
    Bộ mã hóa góc nhìn (view) biểu đồ tạm thời sử dụng bộ nhớ động GRUCell, Chú ý nhiều đầu theo thời gian,
    và các đầu phụ trợ tự giám sát đa nhiệm.
    """
    def __init__(
        self,
        d_node: int = 128,
        d_edge: int = 64,
        d_msg: int = 128,
        n_heads: int = 4,
        d_time_proj: int = 32,
        d_rel_emb: int = 32,
        d_type_emb: int = 32,
        dropout: float = 0.10,
        num_canonical_relations: int = 8, # 8 lớp chuẩn (ID 1..8 -> chỉ số lớp 0..7)
        num_node_types: int = 4,          # 0: DATA_BLOCK, 1: STORAGE_NODE, 2: MANAGEMENT_SYSTEM, 3: EXECUTION_THREAD
        max_node_history: int = 64,
        lambda_rel: float = 1.0,
        lambda_node: float = 1.0,
        lambda_time: float = 0.1,
        rel_mask_prob: float = 0.15,
        node_mask_prob: float = 0.15
    ):
        super().__init__()
        self.d_node = d_node
        self.d_edge = d_edge
        self.d_msg = d_msg
        self.n_heads = n_heads
        self.d_time_proj = d_time_proj
        self.d_rel_emb = d_rel_emb
        self.d_type_emb = d_type_emb
        self.dropout_p = dropout
        self.num_canonical_relations = num_canonical_relations
        self.num_node_types = num_node_types
        self.max_node_history = max_node_history
        self.lambda_rel = lambda_rel
        self.lambda_node = lambda_node
        self.lambda_time = lambda_time
        self.rel_mask_prob = rel_mask_prob
        self.node_mask_prob = node_mask_prob

        # Nhúng & Chiếu
        # Bảng nhúng quan hệ có 9 mục (0: UNK/PAD, 1..8: Canonical Relations) để tra cứu
        self.relation_embedding = nn.Embedding(num_canonical_relations + 1, d_rel_emb)
        self.type_embedding = nn.Embedding(num_node_types, d_type_emb)
        self.edge_proj = nn.Linear(1, d_edge)
        self.time_proj = TimeProjection(d_time_proj)

        # Trình tạo tin nhắn: [h_src || h_dst || e_edge || e_rel || e_src_type || e_dst_type || phi(dt)] -> d_msg
        msg_in_dim = d_node + d_node + d_edge + d_rel_emb + d_type_emb + d_type_emb + d_time_proj
        self.msg_mlp = nn.Sequential(
            nn.Linear(msg_in_dim, d_msg),
            nn.LayerNorm(d_msg),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(d_msg, d_msg)
        )

        # Tự chú ý nhiều đầu theo thời gian đối với bộ đệm lịch sử
        self.history_attn = nn.MultiheadAttention(
            embed_dim=d_msg,
            num_heads=n_heads,
            dropout=dropout,
            batch_first=True
        )
        self.norm_history = nn.LayerNorm(d_msg)

        # Ô nhớ động GRU
        self.memory_cell = nn.GRUCell(d_msg, d_node)
        self.norm_memory = nn.LayerNorm(d_node)

        # Đầu dự đoán SSL phụ trợ (Dự đoán trước khi cập nhật)
        # 1. Đầu phân loại quan hệ: [h_v(t-) || h_u(t-) || phi(dt)] -> EXACTLY 8 CANONICAL CLASSES
        rel_in_dim = d_node + d_node + d_time_proj
        self.rel_head = nn.Sequential(
            nn.Linear(rel_in_dim, 128),
            nn.LayerNorm(128),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(128, num_canonical_relations)
        )

        # 2. Đầu tái tạo đặc trưng nút: h_v(t-) -> 6 (4-dim one-hot type + 2-dim log1p degrees)
        self.node_head = nn.Sequential(
            nn.Linear(d_node, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 6)
        )

        # 3. Đầu khoảng cách thời gian liên tục: [h_v(t-) || h_u(t-)] -> 1
        time_in_dim = d_node + d_node
        self.time_head = nn.Sequential(
            nn.Linear(time_in_dim, 64),
            nn.LayerNorm(64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1)
        )

        # Hàm mất: L_rel = CrossEntropy (8 lớp), L_node = MSELoss, L_time = SmoothL1Loss
        self.loss_rel_fn = nn.CrossEntropyLoss()
        self.loss_node_fn = nn.MSELoss()
        self.loss_time_fn = nn.SmoothL1Loss(beta=1.0)

        # Bảng trạng thái nút có thể thay đổi (Đặt lại khi chuyển đổi phân tách)
        self.node_memory: Dict[str, torch.Tensor] = {}
        self.node_last_ts: Dict[str, float] = {}
        self.node_in_degrees: Dict[str, int] = {}
        self.node_out_degrees: Dict[str, int] = {}
        self.node_history_buffers: Dict[str, List[torch.Tensor]] = {}

    def reset_node_states(self):
        """Thiết lập lại phân chia quy nạp: Xóa tất cả các trạng thái tương tác và bộ nhớ nút động."""
        self.node_memory.clear()
        self.node_last_ts.clear()
        self.node_in_degrees.clear()
        self.node_out_degrees.clear()
        self.node_history_buffers.clear()

    def get_node_states(self) -> Dict[str, Any]:
        """Sắp xếp theo thứ tự tất cả các bảng trạng thái nút có thể thay đổi để kiểm tra điểm nguyên tử."""
        mem_clones = {k: v.detach().cpu().clone() for k, v in self.node_memory.items()}
        hist_clones = {k: [msg.detach().cpu().clone() for msg in msgs] for k, msgs in self.node_history_buffers.items()}
        return {
            "node_memory_states": mem_clones,
            "node_last_interaction_timestamps": dict(self.node_last_ts),
            "node_causal_in_degrees": dict(self.node_in_degrees),
            "node_causal_out_degrees": dict(self.node_out_degrees),
            "node_temporal_history_buffers": hist_clones
        }

    def set_node_states(self, states: Dict[str, Any], device: torch.device):
        """Khôi phục tất cả các bảng trạng thái nút có thể thay đổi từ checkpoint."""
        self.node_memory = {k: v.to(device) for k, v in states.get("node_memory_states", {}).items()}
        self.node_last_ts = dict(states.get("node_last_interaction_timestamps", {}))
        self.node_in_degrees = dict(states.get("node_causal_in_degrees", {}))
        self.node_out_degrees = dict(states.get("node_causal_out_degrees", {}))
        self.node_history_buffers = {
            k: [msg.to(device) for msg in msgs]
            for k, msgs in states.get("node_temporal_history_buffers", {}).items()
        }

    def _get_h_prev(self, node_id: str, device: torch.device) -> torch.Tensor:
        """Truy xuất h(t-) từ bảng bộ nhớ động hoặc khởi tạo với vectơ 0."""
        if node_id not in self.node_memory:
            return torch.zeros(self.d_node, device=device)
        return self.node_memory[node_id]

    def _get_causal_degrees_t_minus(self, node_id: str) -> Tuple[int, int]:
        """Truy xuất mức độ nhân quả trong và mức độ ngoài tại t-."""
        in_d = self.node_in_degrees.get(node_id, 0)
        out_d = self.node_out_degrees.get(node_id, 0)
        return in_d, out_d

    def _get_temporal_gap_t_minus(self, src: str, dst: str, curr_t: float) -> float:
        """Tính toán khoảng cách thời gian liên tục delta_t = curr_t - max(last_src, last_dst)."""
        last_src = self.node_last_ts.get(src, None)
        last_dst = self.node_last_ts.get(dst, None)
        if last_src is None and last_dst is None:
            return 0.0
        elif last_src is None:
            last_t = last_dst
        elif last_dst is None:
            last_t = last_src
        else:
            last_t = max(last_src, last_dst)
        return max(0.0, curr_t - last_t)

    def forward_event_window(
        self,
        events: List[Dict[str, Any]],
        mask_generator: Optional[torch.Generator] = None,
        is_training: bool = True
    ) -> Dict[str, Any]:
        """
        Xử lý tuần tự một cửa sổ sự kiện tạm thời, thực thi nghiêm ngặt:
          1. Dự đoán trước khi cập nhật trên h(t-)
          2. Tường lửa rò rỉ mục tiêu cho L_rel và L_node
          3. Bộ đệm lịch sử FIFO nguyên nhân
          4. Việc nhúng loại thực thể đang hoạt động trong Msg()
          5. Cập nhật bộ nhớ GRU sau dự đoán
        """
        if not events:
            dummy_zero = torch.tensor(0.0, device=next(self.parameters()).device, requires_grad=True)
            return {
                "loss": dummy_zero,
                "loss_rel": dummy_zero,
                "loss_node": dummy_zero,
                "loss_time": dummy_zero,
                "num_events": 0,
                "masked_rel_count": 0,
                "masked_node_count": 0
            }

        device = next(self.parameters()).device
        loss_rel_list = []
        loss_node_list = []
        loss_time_list = []

        masked_rel_count = 0
        masked_node_count = 0

        for event in events:
            src = event["source_node"]
            dst = event["dest_node"]
            src_type = int(event["source_type"])
            dst_type = int(event["dest_type"])
            rel_id = int(event["relation_id"]) # ID quan hệ chuẩn: 1..8
            curr_t = float(event["event_timestamp_utc_exact"])
            size_b = float(event.get("size_bytes", 0.0) or 0.0)

            # Xác thực NaN/Inf trên sự kiện đầu vào
            if math.isnan(curr_t) or math.isinf(curr_t) or math.isnan(size_b) or math.isinf(size_b):
                raise FloatingPointError(
                    f"NaN/Inf detected in event inputs: timestamp={curr_t}, size={size_b}"
                )

            # Bản đồ thô relation_id 1..8 -> chỉ mục lớp 0..7
            target_class_idx = rel_id - 1
            if not (0 <= target_class_idx < self.num_canonical_relations):
                raise ValueError(
                    f"Invalid relation_id {rel_id}. Expected canonical ID in [1..{self.num_canonical_relations}]."
                )

            # -------------------------------------------------------------
            # STEP 1: PREDICT-BEFORE-UPDATE (Đánh giá nghiêm ngặt về h(t-))
            # -------------------------------------------------------------
            h_src_prev = self._get_h_prev(src, device)  # (d_node,)
            h_dst_prev = self._get_h_prev(dst, device)  # (d_node,)

            h_src_2d = h_src_prev.unsqueeze(0)          # (1, d_node)
            h_dst_2d = h_dst_prev.unsqueeze(0)          # (1, d_node)

            # Khoảng cách thời gian nhân quả ở t-
            dt_raw = self._get_temporal_gap_t_minus(src, dst, curr_t)
            dt_log1p_val = math.log1p(dt_raw)
            dt_tensor = torch.tensor([[dt_log1p_val]], dtype=torch.float32, device=device) # (1, 1)
            phi_dt = self.time_proj(dt_tensor)                                             # (1, d_time_proj)

            # Mục tiêu mức độ nhân quả tại t-
            in_src_prev, out_src_prev = self._get_causal_degrees_t_minus(src)
            in_dst_prev, out_dst_prev = self._get_causal_degrees_t_minus(dst)

            # Biểu diễn mục tiêu để tái thiết nút (MSE)
            x_src_target = torch.zeros(6, dtype=torch.float32, device=device)
            x_src_target[src_type] = 1.0
            x_src_target[4] = math.log1p(in_src_prev)
            x_src_target[5] = math.log1p(out_src_prev)

            x_dst_target = torch.zeros(6, dtype=torch.float32, device=device)
            x_dst_target[dst_type] = 1.0
            x_dst_target[4] = math.log1p(in_dst_prev)
            x_dst_target[5] = math.log1p(out_dst_prev)

            # Quyết định mặt nạ một cách xác định thông qua trình tạo RNG (15% cho cả tàu và val)
            mask_rel = torch.rand(1, generator=mask_generator).item() < self.rel_mask_prob
            mask_node_src = torch.rand(1, generator=mask_generator).item() < self.node_mask_prob
            mask_node_dst = torch.rand(1, generator=mask_generator).item() < self.node_mask_prob

            # 1a. Đầu dự đoán mối quan hệ Masked Edge (Mục tiêu được giữ lại từ đầu vào, 8 lớp đầu ra)
            rel_in = torch.cat([h_src_2d, h_dst_2d, phi_dt], dim=-1) # (1, rel_in_dim)
            rel_logits = self.rel_head(rel_in)                       # (1, 8)
            if mask_rel:
                target_rel_tensor = torch.tensor([target_class_idx], dtype=torch.long, device=device)
                loss_rel_val = self.loss_rel_fn(rel_logits, target_rel_tensor)
                loss_rel_list.append(loss_rel_val)
                masked_rel_count += 1

            # 1b. Đầu tái tạo tính năng nút bị che (Mất MSE trên R^6, Mục tiêu bị giữ lại khỏi đầu vào)
            if mask_node_src:
                node_src_pred = self.node_head(h_src_2d) # (1, 6)
                sq_err_src = torch.sum((node_src_pred.squeeze(0) - x_src_target) ** 2)
                loss_node_list.append(sq_err_src)
                masked_node_count += 1
            if mask_node_dst:
                node_dst_pred = self.node_head(h_dst_2d) # (1, 6)
                sq_err_dst = torch.sum((node_dst_pred.squeeze(0) - x_dst_target) ** 2)
                loss_node_list.append(sq_err_dst)
                masked_node_count += 1

            # 1c. Đầu dự đoán khoảng cách thời gian liên tục
            time_in = torch.cat([h_src_2d, h_dst_2d], dim=-1)      # (1, 2*d_node)
            time_pred = F.relu(self.time_head(time_in)).squeeze(0) # (1,)
            loss_time_val = self.loss_time_fn(time_pred, dt_tensor.squeeze(0))
            loss_time_list.append(loss_time_val)

            # -------------------------------------------------------------
            # STEP 2: TEMPORAL MESSAGE PASSING & MEMORY UPDATE (Sau mất mát (loss))
            # -------------------------------------------------------------
            size_norm = math.log1p(max(0.0, size_b))
            size_tensor = torch.tensor([[size_norm]], dtype=torch.float32, device=device)
            e_edge = self.edge_proj(size_tensor)                                    # (1, d_edge)
            
            rel_tensor = torch.tensor([rel_id], dtype=torch.long, device=device)
            e_rel = self.relation_embedding(rel_tensor)                             # (1, d_rel_emb)

            src_type_t = torch.tensor([src_type], dtype=torch.long, device=device)
            dst_type_t = torch.tensor([dst_type], dtype=torch.long, device=device)
            e_src_type = self.type_embedding(src_type_t)                            # (1, d_type_emb)
            e_dst_type = self.type_embedding(dst_type_t)                            # (1, d_type_emb)

            # Điều kiện hiện hoạt có nhúng loại thực thể trong trình tạo thông báo
            msg_src_in = torch.cat([h_src_2d, h_dst_2d, e_edge, e_rel, e_src_type, e_dst_type, phi_dt], dim=-1)
            msg_dst_in = torch.cat([h_dst_2d, h_src_2d, e_edge, e_rel, e_dst_type, e_src_type, phi_dt], dim=-1)

            raw_m_src = self.msg_mlp(msg_src_in) # (1, d_msg)
            raw_m_dst = self.msg_mlp(msg_dst_in) # (1, d_msg)

            # Tổng hợp chú ý lịch sử (nếu bộ đệm không trống)
            m_src = self._aggregate_history(src, raw_m_src, device) # (1, d_msg)
            m_dst = self._aggregate_history(dst, raw_m_dst, device) # (1, d_msg)

            # Cập nhật trạng thái bộ nhớ động GRU
            h_src_new = self.norm_memory(self.memory_cell(m_src, h_src_2d)).squeeze(0) # (d_node,)
            h_dst_new = self.norm_memory(self.memory_cell(m_dst, h_dst_2d)).squeeze(0) # (d_node,)

            # Lưu các trạng thái đã cập nhật (mang biểu đồ tự động chuyển đổi qua các tương tác trong cửa sổ này)
            self.node_memory[src] = h_src_new
            self.node_memory[dst] = h_dst_new
            self.node_last_ts[src] = curr_t
            self.node_last_ts[dst] = curr_t
            self.node_out_degrees[src] = out_src_prev + 1
            self.node_in_degrees[dst] = in_dst_prev + 1

            # Thêm vào bộ đệm tương tác lịch sử FIFO
            self._append_history(src, raw_m_src.squeeze(0).detach())
            self._append_history(dst, raw_m_dst.squeeze(0).detach())

        # Ranh giới BPTT bị cắt ngắn: Tách trạng thái bộ nhớ qua ranh giới cửa sổ
        self.node_memory = {k: v.detach() for k, v in self.node_memory.items()}
        self.node_history_buffers = {k: [msg.detach() for msg in msgs] for k, msgs in self.node_history_buffers.items()}

        # Tính toán số tiền và số đếm chính xác
        rel_loss_sum = torch.stack(loss_rel_list).sum() if loss_rel_list else torch.tensor(0.0, device=device)
        node_sq_err_sum = torch.stack(loss_node_list).sum() if loss_node_list else torch.tensor(0.0, device=device)
        time_loss_sum = torch.stack(loss_time_list).sum() if loss_time_list else torch.tensor(0.0, device=device)

        node_element_count = 6 * masked_node_count
        time_target_count = len(events)

        loss_rel = rel_loss_sum / max(1, masked_rel_count) if masked_rel_count > 0 else torch.tensor(0.0, device=device)
        loss_node = node_sq_err_sum / max(1, node_element_count) if node_element_count > 0 else torch.tensor(0.0, device=device)
        loss_time = time_loss_sum / max(1, time_target_count) if time_target_count > 0 else torch.tensor(0.0, device=device)

        total_loss = self.lambda_rel * loss_rel + self.lambda_node * loss_node + self.lambda_time * loss_time

        return {
            "loss": total_loss,
            "loss_rel": loss_rel,
            "loss_node": loss_node,
            "loss_time": loss_time,
            "rel_loss_sum_tensor": rel_loss_sum,
            "node_sq_err_sum_tensor": node_sq_err_sum,
            "time_loss_sum_tensor": time_loss_sum,
            "rel_loss_sum": rel_loss_sum.item() if isinstance(rel_loss_sum, torch.Tensor) else float(rel_loss_sum),
            "rel_target_count": masked_rel_count,
            "node_sq_err_sum": node_sq_err_sum.item() if isinstance(node_sq_err_sum, torch.Tensor) else float(node_sq_err_sum),
            "node_element_count": node_element_count,
            "node_target_count": masked_node_count,
            "time_loss_sum": time_loss_sum.item() if isinstance(time_loss_sum, torch.Tensor) else float(time_loss_sum),
            "time_target_count": time_target_count,
            "num_events": len(events),
            "masked_rel_count": masked_rel_count,
            "masked_node_count": masked_node_count
        }

    def _aggregate_history(self, node_id: str, current_msg: torch.Tensor, device: torch.device) -> torch.Tensor:
        """Tổng hợp các thông điệp tương tác lịch sử bằng cách sử dụng tính năng Tự chú ý của nhiều đầu."""
        hist = self.node_history_buffers.get(node_id, [])
        if not hist:
            return current_msg
        
        hist_tensor = torch.stack(hist).unsqueeze(0).to(device) # (1, seq_len, d_msg)
        query = current_msg.unsqueeze(1)                        # (1, 1, d_msg)
        attn_out, _ = self.history_attn(query, hist_tensor, hist_tensor)
        agg = self.norm_history(current_msg + attn_out.squeeze(1))
        return agg

    def _append_history(self, node_id: str, msg: torch.Tensor):
        """Thêm thông báo vào hàng đợi FIFO tôn trọng max_node_history = 64."""
        if node_id not in self.node_history_buffers:
            self.node_history_buffers[node_id] = []
        buf = self.node_history_buffers[node_id]
        buf.append(msg)
        if len(buf) > self.max_node_history:
            buf.pop(0)
