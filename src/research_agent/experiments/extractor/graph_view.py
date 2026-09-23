# -*- coding: utf-8 -*-
"""
Trình trích xuất biểu đồ xuất xứ theo thời gian và quan hệ
Triển khai đặc tả đã đóng băng (frozen specification) Chương 2 (Phần 2.2 & Bang 2.2):
  - Sự kiện tương tác chứng minh nguồn động: e_i = (t_i, relation_type, src, dst, edge_features, src_node_attr, dst_node_attr)
  - Mã hóa thời gian tương đối hình sin: Phi(delta_t)
  - Ngân hàng bộ nhớ thực thể thời gian liên tục với bản cập nhật GRU, giới hạn dung lượng LRU và tính toán trạng thái
  - Chức năng thông báo: Msg(h_src_pre, h_dst_pre, Phi(delta_src), relation_emb, edge_feat_emb, src_node_attr, dst_node_attr)
  - Tập hợp cùng thời gian được nhóm: m_u_agg(t) = Agg({m_v->u(t)}) trước khi cập nhật bộ nhớ đơn
  - Đọc đồ thị: z_graph(t)
  - Ba đầu học tập tự giám sát đồ thị chống rò rỉ (SSL):
      1. L_mask_node: Tái tạo vectơ thuộc tính nút an toàn quyền riêng tư liên tục được che dấu x_v^priv với Smooth L1
      2. L_mask_edge: Dự đoán loại mối quan hệ từ việc nhúng cạnh bị che (không rò rỉ mục tiêu)
      3. L_time_gap: Dự đoán nhật ký khoảng cách thời gian(1 + delta_t) với mất Smooth L1
  - Xác thực đơn hàng sự kiện tạm thời đơn điệu toàn cầu nghiêm ngặt & Từ chối sự kiện muộn
"""

import math
from collections import OrderedDict
from typing import Dict, Any, List, Optional, Tuple, Set
import torch
import torch.nn as nn
import torch.nn.functional as F

class SinusoidalTimeEncoding(nn.Module):
    """
    Mã hóa thời gian tương đối Fourier / hài hòa:
    Phi(delta_t) = [cos(w_1 delta_t), sin(w_1 delta_t), ..., cos(w_k delta_t), sin(w_k delta_t)]
    """
    def __init__(self, time_dim: int):
        super().__init__()
        if time_dim % 2 != 0:
            raise ValueError(f"time_dim must be even, got {time_dim}")
        self.time_dim = time_dim
        half_dim = time_dim // 2
        inv_freq = 1.0 / (10000.0 ** (torch.arange(0, half_dim, dtype=torch.float32) / half_dim))
        self.register_buffer("inv_freq", inv_freq)

    def forward(self, delta_t: torch.Tensor) -> torch.Tensor:
        delta_t = delta_t.view(-1, 1).float()
        sinusoid_inp = delta_t * self.inv_freq.unsqueeze(0)
        enc = torch.cat([torch.cos(sinusoid_inp), torch.sin(sinusoid_inp)], dim=-1)
        return enc

class BoundedEntityMemoryBank(nn.Module):
    """
    Trạng thái theo dõi Ngân hàng bộ nhớ thực thể động được giới hạn LRU h_u(t) và dấu thời gian tương tác cuối cùng t_u.
    """
    def __init__(self, memory_dim: int, max_entities: int = 10000):
        super().__init__()
        self.memory_dim = memory_dim
        self.max_entities = max_entities
        self.h_init = nn.Parameter(torch.zeros(1, memory_dim))
        nn.init.normal_(self.h_init, std=0.02)
        
        self.memory_store: OrderedDict[int, torch.Tensor] = OrderedDict()
        self.last_timestamps: Dict[int, float] = {}
        self.last_global_timestamp: float = -1.0
        self.peak_active_entities: int = 0
        self.peak_state_bytes: int = 0

    def get_memory(self, entity_id: int, current_timestamp: float, device: torch.device) -> Tuple[torch.Tensor, float]:
        if entity_id in self.memory_store:
            self.memory_store.move_to_end(entity_id)
            h_prev = self.memory_store[entity_id]
            t_prev = self.last_timestamps[entity_id]
            if current_timestamp < t_prev:
                raise ValueError(
                    f"Entity {entity_id} late event: current timestamp {current_timestamp} < last seen {t_prev}"
                )
            delta = float(current_timestamp - t_prev)
        else:
            h_prev = self.h_init.squeeze(0).to(device)
            delta = 0.0

        return h_prev, delta

    def update_entity(self, entity_id: int, new_state: torch.Tensor, timestamp: float):
        if entity_id in self.memory_store:
            self.memory_store.move_to_end(entity_id)
        self.memory_store[entity_id] = new_state
        self.last_timestamps[entity_id] = timestamp
        self.last_global_timestamp = max(self.last_global_timestamp, timestamp)

        # LRU Trục xuất khi vượt quá dung lượng
        while len(self.memory_store) > self.max_entities:
            oldest_id, _ = self.memory_store.popitem(last=False)
            if oldest_id in self.last_timestamps:
                del self.last_timestamps[oldest_id]

        active_count = len(self.memory_store)
        self.peak_active_entities = max(self.peak_active_entities, active_count)
        current_bytes = active_count * self.memory_dim * 4 + active_count * 8
        self.peak_state_bytes = max(self.peak_state_bytes, current_bytes)

    def get_state_metrics(self) -> Dict[str, Any]:
        active_count = len(self.memory_store)
        tensor_bytes = active_count * self.memory_dim * 4
        timestamp_bytes = active_count * 8
        total_bytes = tensor_bytes + timestamp_bytes
        return {
            "active_entities": active_count,
            "peak_active_entities": self.peak_active_entities,
            "max_capacity": self.max_entities,
            "state_size_bytes": total_bytes,
            "peak_state_bytes": self.peak_state_bytes,
            "state_size_mb": total_bytes / (1024 * 1024),
            "peak_state_mb": self.peak_state_bytes / (1024 * 1024)
        }

    def detach_memory(self):
        for e_id in list(self.memory_store.keys()):
            self.memory_store[e_id] = self.memory_store[e_id].detach()

    def reset_memory(self):
        self.memory_store.clear()
        self.last_timestamps.clear()
        self.last_global_timestamp = -1.0
        self.peak_active_entities = 0
        self.peak_state_bytes = 0

class TemporalGraphViewExtractor(nn.Module):
    """
    Bộ trích xuất GNN tạm thời theo thời gian liên tục để đo từ xa nguồn gốc.
    Triển khai tin nhắn -> Tổng hợp cùng thời gian -> Cập nhật bộ nhớ -> Đọc.
    """
    def __init__(
        self,
        node_attr_dim: int = 16,
        time_dim: int = 32,
        memory_dim: int = 64,
        edge_feat_dim: int = 16,
        out_dim: int = 64,
        num_relations: int = 8,
        max_entities: int = 10000,
        late_event_policy: str = "REJECT"
    ):
        super().__init__()
        self.node_attr_dim = node_attr_dim
        self.time_dim = time_dim
        self.memory_dim = memory_dim
        self.edge_feat_dim = edge_feat_dim
        self.out_dim = out_dim
        self.num_relations = num_relations
        self.late_event_policy = late_event_policy

        # Nhúng & Bộ mã hóa
        self.node_attr_encoder = nn.Sequential(
            nn.Linear(node_attr_dim, node_attr_dim),
            nn.GELU(),
            nn.Linear(node_attr_dim, node_attr_dim)
        )
        self.mask_node_token = nn.Parameter(torch.zeros(1, node_attr_dim))
        nn.init.normal_(self.mask_node_token, std=0.02)

        self.relation_emb = nn.Embedding(num_relations + 1, memory_dim)  # +1 cho MASK_RELATION
        self.mask_relation_idx = num_relations
        self.time_encoder = SinusoidalTimeEncoding(time_dim=time_dim)

        # Bộ mã hóa tính năng cạnh (x_e)
        self.edge_feat_encoder = nn.Sequential(
            nn.Linear(edge_feat_dim, edge_feat_dim),
            nn.GELU(),
            nn.Linear(edge_feat_dim, edge_feat_dim)
        )

        # Ngân hàng bộ nhớ
        self.memory_bank = BoundedEntityMemoryBank(memory_dim=memory_dim, max_entities=max_entities)

        # Chức năng thông báo: Msg(h_src, h_dst, phi(delta), r_emb, edge_feat, x_v_src, x_v_dst)
        msg_in_dim = memory_dim * 2 + time_dim + memory_dim + edge_feat_dim + node_attr_dim * 2
        self.msg_net = nn.Sequential(
            nn.Linear(msg_in_dim, memory_dim),
            nn.GELU(),
            nn.LayerNorm(memory_dim),
            nn.Linear(memory_dim, memory_dim)
        )

        # Ô cập nhật bộ nhớ (GRU)
        self.gru_cell = nn.GRUCell(input_size=memory_dim, hidden_size=memory_dim)

        # Chiếu đọc
        self.readout_proj = nn.Sequential(
            nn.Linear(memory_dim, out_dim),
            nn.LayerNorm(out_dim)
        )

        # ---------------------------------------------------------------------
        # THREE ANTI-LEAKAGE GRAPH SSL HEADS
        # ---------------------------------------------------------------------
        # 1. L_mask_node: Đầu tái tạo x_v^priv liên tục
        self.ssl_mask_node_head = nn.Sequential(
            nn.Linear(memory_dim, memory_dim),
            nn.GELU(),
            nn.LayerNorm(memory_dim),
            nn.Linear(memory_dim, node_attr_dim)
        )

        # 2. L_mask_edge: Đầu dự đoán mối quan hệ đeo mặt nạ
        self.ssl_mask_edge_head = nn.Sequential(
            nn.Linear(memory_dim, memory_dim),
            nn.GELU(),
            nn.LayerNorm(memory_dim),
            nn.Linear(memory_dim, num_relations)
        )

        # 3. L_time_gap: Đầu dự đoán khoảng cách thời gian (nhật ký dự đoán(1 + delta_t))
        self.ssl_time_gap_head = nn.Sequential(
            nn.Linear(memory_dim, memory_dim),
            nn.GELU(),
            nn.LayerNorm(memory_dim),
            nn.Linear(memory_dim, 1)
        )

    def process_causal_events(
        self,
        events: List[Dict[str, Any]],
        device: torch.device,
        mask_edge_indices: Optional[Set[int]] = None,
        mask_node_indices: Optional[Set[int]] = None
    ) -> Tuple[torch.Tensor, Dict[str, torch.Tensor]]:
        """
        Xử lý các sự kiện động với:
          1. Kiểm tra tính đơn điệu thời gian toàn cục một cách nghiêm ngặt xuyên suốt chuỗi sự kiện
          2. Vectơ thuộc tính nút rõ ràng x_v^priv trong đường dẫn thông báo với mặt nạ thực sự
          3. Tập hợp tin nhắn cùng lúc được nhóm theo đích đến: Agg({m_{v->u}(t)})
          4. Cập nhật bộ nhớ đơn cho mỗi đích tại thời điểm t
        """
        if not events:
            h_init = self.memory_bank.h_init.to(device)
            return self.readout_proj(h_init), {}

        mask_edge_indices = mask_edge_indices or set()
        mask_node_indices = mask_node_indices or set()

        # 1. Kiểm tra tính đơn điệu nghiêm ngặt trên toàn bộ luồng sự kiện
        for i in range(1, len(events)):
            if events[i]["timestamp"] < events[i - 1]["timestamp"]:
                if self.late_event_policy == "REJECT":
                    raise ValueError(
                        f"Strict causality violation: Event {i} timestamp {events[i]['timestamp']} "
                        f"< preceding event timestamp {events[i-1]['timestamp']}"
                    )

        for ev in events:
            t = ev["timestamp"]
            if t < self.memory_bank.last_global_timestamp:
                if self.late_event_policy == "REJECT":
                    raise ValueError(
                        f"Global late event rejected: event timestamp {t} < last processed {self.memory_bank.last_global_timestamp}"
                    )

        # Nhóm các sự kiện theo dấu thời gian để triển khai các đợt vi mô nhân quả
        time_to_events: Dict[float, List[Tuple[int, Dict[str, Any]]]] = OrderedDict()
        for idx, ev in enumerate(events):
            t = ev["timestamp"]
            time_to_events.setdefault(t, []).append((idx, ev))

        all_messages = []
        all_delta_dests = []
        all_pred_node_attrs = []
        all_true_node_attrs = []
        all_pred_edges = []
        all_true_edges = []

        for t_step, ev_group in time_to_events.items():
            dest_messages: Dict[int, List[torch.Tensor]] = {}
            dest_prev_h: Dict[int, torch.Tensor] = {}

            for global_idx, ev in ev_group:
                s_id = ev["src"]
                d_id = ev["dst"]
                r_type = ev["relation_type"]

                # 1. Thuộc tính nút x_v^priv (Nguồn và Đích)
                raw_src_attr = ev.get("src_node_attr", None)
                if raw_src_attr is not None:
                    src_attr_tensor = torch.tensor(raw_src_attr, dtype=torch.float32, device=device).view(1, -1)
                else:
                    src_attr_tensor = torch.zeros(1, self.node_attr_dim, dtype=torch.float32, device=device)

                raw_dst_attr = ev.get("dst_node_attr", None)
                if raw_dst_attr is not None:
                    dst_attr_tensor = torch.tensor(raw_dst_attr, dtype=torch.float32, device=device).view(1, -1)
                else:
                    dst_attr_tensor = torch.zeros(1, self.node_attr_dim, dtype=torch.float32, device=device)

                # Mặt nạ nút: Thay thế x_v^priv bằng tính toán thông báo token mặt nạ BEFORE
                if global_idx in mask_node_indices:
                    enc_src_attr = self.mask_node_token
                else:
                    enc_src_attr = self.node_attr_encoder(src_attr_tensor)

                enc_dst_attr = self.node_attr_encoder(dst_attr_tensor)

                # 2. Tính năng cạnh (x_e)
                raw_ef = ev.get("edge_features", None)
                if raw_ef is not None:
                    ef_tensor = torch.tensor(raw_ef, dtype=torch.float32, device=device).view(1, -1)
                else:
                    ef_tensor = torch.zeros(1, self.edge_feat_dim, dtype=torch.float32, device=device)
                ef_emb = self.edge_feat_encoder(ef_tensor)

                # 3. Bộ nhớ & Thời gian Delta
                h_s_pre, delta_s = self.memory_bank.get_memory(s_id, t_step, device)
                h_d_pre, delta_d = self.memory_bank.get_memory(d_id, t_step, device)

                dest_prev_h[d_id] = h_d_pre
                all_delta_dests.append(delta_d)

                phi_delta = self.time_encoder(torch.tensor([delta_s], dtype=torch.float32, device=device))

                # Nhúng mối quan hệ với sự hỗ trợ mặt nạ
                if global_idx in mask_edge_indices:
                    r_emb = self.relation_emb(torch.tensor([self.mask_relation_idx], dtype=torch.long, device=device))
                else:
                    r_emb = self.relation_emb(torch.tensor([r_type], dtype=torch.long, device=device))

                # Msg bao gồm: h_src, h_dst, phi(delta), r_emb, ef_emb, enc_src_attr, enc_dst_attr
                msg_in = torch.cat([
                    h_s_pre.unsqueeze(0),
                    h_d_pre.unsqueeze(0),
                    phi_delta,
                    r_emb,
                    ef_emb,
                    enc_src_attr,
                    enc_dst_attr
                ], dim=-1)
                msg_v_u = self.msg_net(msg_in).squeeze(0)
                
                dest_messages.setdefault(d_id, []).append(msg_v_u)
                all_messages.append(msg_v_u)

                if global_idx in mask_edge_indices:
                    all_pred_edges.append(self.ssl_mask_edge_head(msg_v_u.unsqueeze(0)))
                    all_true_edges.append(r_type)

                if global_idx in mask_node_indices:
                    all_pred_node_attrs.append(self.ssl_mask_node_head(msg_v_u.unsqueeze(0)))
                    all_true_node_attrs.append(src_attr_tensor)

            # Tổng hợp cùng thời gian cho mỗi điểm đến
            for d_id, msg_list in dest_messages.items():
                m_agg = torch.stack(msg_list, dim=0).mean(dim=0, keepdim=True)
                h_prev = dest_prev_h[d_id].unsqueeze(0)
                h_new = self.gru_cell(m_agg, h_prev).squeeze(0)
                self.memory_bank.update_entity(d_id, h_new, t_step)

        # Nhóm đọc đồ thị
        active_states = list(self.memory_bank.memory_store.values())
        if active_states:
            pooled_state = torch.stack(active_states, dim=0).mean(dim=0, keepdim=True)
        else:
            pooled_state = self.memory_bank.h_init.to(device)
        z_graph = self.readout_proj(pooled_state)

        # ---------------------------------------------------------------------
        # COMPUTE GRAPH SSL LOSSES
        # ---------------------------------------------------------------------
        ssl_losses = {}
        all_msg_tensor = torch.stack(all_messages, dim=0)

        # 1. L_mask_node: Tái tạo vectơ của x_v^priv
        if all_pred_node_attrs:
            pred_n_attr = torch.cat(all_pred_node_attrs, dim=0)
            true_n_attr = torch.cat(all_true_node_attrs, dim=0)
            ssl_losses["L_mask_node"] = F.smooth_l1_loss(pred_n_attr, true_n_attr)
        else:
            pred_n_attr = self.ssl_mask_node_head(all_msg_tensor)
            dummy_n = torch.zeros_like(pred_n_attr)
            ssl_losses["L_mask_node"] = F.smooth_l1_loss(pred_n_attr, dummy_n) * 0.0

        # 2. L_mask_edge
        if all_pred_edges:
            pred_e = torch.cat(all_pred_edges, dim=0)
            true_e = torch.tensor(all_true_edges, dtype=torch.long, device=device)
            ssl_losses["L_mask_edge"] = F.cross_entropy(pred_e, true_e)
        else:
            pred_e = self.ssl_mask_edge_head(all_msg_tensor)
            dummy_e = torch.zeros(pred_e.size(0), dtype=torch.long, device=device)
            ssl_losses["L_mask_edge"] = F.cross_entropy(pred_e, dummy_e) * 0.0

        # 3. L_time_gap: log(1 + delta_t) với Smooth L1
        pred_time = self.ssl_time_gap_head(all_msg_tensor).squeeze(-1)
        true_deltas = torch.tensor(all_delta_dests, dtype=torch.float32, device=device)
        target_log_gap = torch.log1p(true_deltas)
        ssl_losses["L_time_gap"] = F.smooth_l1_loss(pred_time, target_log_gap)

        return z_graph, ssl_losses

    def forward(self, events: List[Dict[str, Any]], device: torch.device) -> torch.Tensor:
        z_graph, _ = self.process_causal_events(events, device)
        return z_graph
