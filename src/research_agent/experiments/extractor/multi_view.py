# -*- coding: utf-8 -*-
"""
Công cụ tối ưu hóa và trích xuất đa góc nhìn (multi-view)
Triển khai Hợp đồng đại diện đa góc nhìn (multi-view) cố định theo Chương 2 (Phần 2.4 & Bang 2.4):
  - Tương ứng đúng trên mỗi mẫu: Mỗi mẫu i có danh sách sự kiện đồ thị và đầu vào trình tự riêng
  - Phạm vi bộ nhớ đa góc nhìn (multi-view) rõ ràng:
      * "độc lập" (Mặc định để phát hiện dị thường theo cửa sổ): Mỗi mẫu tôi có ngân hàng bộ nhớ bị cô lập/đặt lại.
      * "continuous_streaming": Trạng thái bộ nhớ liên tục được duy trì trên luồng nhân quả nghiêm ngặt.
  - Tối ưu hóa chống thu gọn VICReg hàng loạt thực tế trên các biểu diễn được ghép nối [z_seq, z_graph]
  - Kết hợp đa góc nhìn (multi-view) với mất mát (loss) tái tạo:
      L_fuse_rec = 0.5 * ||z_mv - stopgrad(z_seq)||^2 + 0.5 * ||z_mv - stopgrad(z_graph)||^2
      Huấn luyện cơ chế kiểm soát W_gate mà không xung đột gradient của bộ trích xuất.
  - Hoàn thành Giai đoạn A Mục tiêu đa tác vụ (multi-task):
      L_StageA = L_seq_self + L_graph_self + lambda_align * L_align + lambda_fuse * L_fuse_rec
"""

from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Tuple, Set
import torch
import torch.nn as nn
import torch.nn.functional as F

from research_agent.experiments.extractor.sequence_view import SequenceViewExtractor
from research_agent.experiments.extractor.graph_view import TemporalGraphViewExtractor

@dataclass
class MultiViewCorrespondence:
    """
    Hợp đồng siêu dữ liệu tương ứng rõ ràng liên kết phép đo từ xa ở góc nhìn (view) Trình tự và Biểu đồ trên mỗi mẫu.
    """
    correspondence_id: str
    time_interval: Tuple[float, float]
    entity_scope: str
    seq_view_id: str
    graph_view_id: str
    overlap_ratio: float
    seq_available: bool = True
    graph_available: bool = True

    def is_valid_for_alignment(self, min_overlap: float = 0.5) -> bool:
        return self.seq_available and self.graph_available and (self.overlap_ratio >= min_overlap)

class VICRegLoss(nn.Module):
    """
    Mất chính quy phương sai-bất biến-hiệp phương sai cho việc căn chỉnh tiềm ẩn đa góc nhìn (multi-view).
    """
    def __init__(self, sim_coeff: float = 25.0, var_coeff: float = 25.0, cov_coeff: float = 1.0, gamma: float = 1.0):
        super().__init__()
        self.sim_coeff = sim_coeff
        self.var_coeff = var_coeff
        self.cov_coeff = cov_coeff
        self.gamma = gamma

    def forward(
        self,
        z_seq: torch.Tensor,
        z_graph: torch.Tensor,
        valid_mask: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        if valid_mask is not None:
            if not valid_mask.any():
                zero_loss = torch.tensor(0.0, device=z_seq.device, requires_grad=True)
                return zero_loss, {"sim_loss": 0.0, "var_loss": 0.0, "cov_loss": 0.0}
            z_seq = z_seq[valid_mask]
            z_graph = z_graph[valid_mask]

        N, D = z_seq.size()
        if N < 2:
            sim_loss = F.mse_loss(z_seq, z_graph)
            return self.sim_coeff * sim_loss, {"sim_loss": float(sim_loss.item()), "var_loss": 0.0, "cov_loss": 0.0}

        # 1. Mất tính bất biến (invariance)/sự tương đồng (MSE)
        sim_loss = F.mse_loss(z_seq, z_graph)

        # 2. Mất phương sai (Chống sụp đổ)
        std_seq = torch.sqrt(z_seq.var(dim=0) + 1e-04)
        std_graph = torch.sqrt(z_graph.var(dim=0) + 1e-04)
        var_loss = torch.mean(F.relu(self.gamma - std_seq)) + torch.mean(F.relu(self.gamma - std_graph))

        # 3. Mất hiệp phương sai (Giải tương quan)
        z_seq_centered = z_seq - z_seq.mean(dim=0)
        z_graph_centered = z_graph - z_graph.mean(dim=0)
        
        cov_seq = (z_seq_centered.T @ z_seq_centered) / (N - 1)
        cov_graph = (z_graph_centered.T @ z_graph_centered) / (N - 1)
        
        diag = torch.eye(D, device=z_seq.device).bool()
        cov_loss = (cov_seq[~diag].pow(2).sum() / D) + (cov_graph[~diag].pow(2).sum() / D)

        total_loss = self.sim_coeff * sim_loss + self.var_coeff * var_loss + self.cov_coeff * cov_loss
        
        metrics = {
            "sim_loss": float(sim_loss.item()),
            "var_loss": float(var_loss.item()),
            "cov_loss": float(cov_loss.item()),
            "mean_std_seq": float(std_seq.mean().item()),
            "mean_std_graph": float(std_graph.mean().item())
        }
        return total_loss, metrics

class GatedMultiViewFusion(nn.Module):
    """
    Cơ chế kết hợp động có cổng:
    alpha = sigmoid(W_gate [z^(seq); z^(graph)])
    z_mv = alpha * z^(seq) + (1 - alpha) * z^(graph)
    """
    def __init__(self, embed_dim: int):
        super().__init__()
        self.gate_net = nn.Sequential(
            nn.Linear(embed_dim * 2, embed_dim),
            nn.GELU(),
            nn.Linear(embed_dim, embed_dim),
            nn.Sigmoid()
        )

    def forward(self, z_seq: torch.Tensor, z_graph: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        concat = torch.cat([z_seq, z_graph], dim=-1)
        alpha = self.gate_net(concat)
        z_mv = alpha * z_seq + (1.0 - alpha) * z_graph
        return z_mv, alpha

class MultiViewRepresentationModel(nn.Module):
    """
    Kiến trúc đa góc nhìn (multi-view) hoàn chỉnh kết nối góc nhìn (view) trình tự, góc nhìn (view) biểu đồ tạm thời,
    Căn chỉnh VICReg và Gated Fusion.
    """
    def __init__(
        self,
        seq_vocab_size: int,
        graph_node_attr_dim: int = 16,
        param_vocab_size: int = 30,
        embed_dim: int = 64,
        num_relations: int = 8,
        mode: str = "aligned",
        align_lambda: float = 1.0,
        fuse_rec_lambda: float = 1.0,
        memory_scope_mode: str = "independent"
    ):
        super().__init__()
        valid_modes = ["sequence_only", "graph_only", "unaligned", "aligned"]
        if mode not in valid_modes:
            raise ValueError(f"Invalid mode {mode}. Must be one of {valid_modes}")
        self.mode = mode
        self.embed_dim = embed_dim
        self.align_lambda = align_lambda
        self.fuse_rec_lambda = fuse_rec_lambda
        self.memory_scope_mode = memory_scope_mode

        # Máy chiết
        self.seq_extractor = SequenceViewExtractor(
            event_vocab_size=seq_vocab_size,
            param_vocab_size=param_vocab_size,
            projection_dim=embed_dim
        )
        self.graph_extractor = TemporalGraphViewExtractor(
            node_attr_dim=graph_node_attr_dim,
            out_dim=embed_dim,
            num_relations=num_relations
        )

        # Căn chỉnh và dự đoán tiềm ẩn trong góc nhìn (view) chéo
        self.seq_proj_align = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.GELU(),
            nn.Linear(embed_dim, embed_dim)
        )
        self.graph_proj_align = nn.Sequential(
            nn.Linear(embed_dim, embed_dim),
            nn.GELU(),
            nn.Linear(embed_dim, embed_dim)
        )

        self.vicreg = VICRegLoss()
        self.fusion = GatedMultiViewFusion(embed_dim=embed_dim)
        
        # Thiếu token dự phòng đã học của góc nhìn (view)
        self.missing_graph_token = nn.Parameter(torch.zeros(1, embed_dim))
        nn.init.normal_(self.missing_graph_token, std=0.02)
        
        self.unaligned_proj = nn.Linear(embed_dim * 2, embed_dim)

    def extract_per_sample_graph_embeddings(
        self,
        graph_events_batch: Optional[List[List[Dict[str, Any]]]],
        batch_size: int,
        correspondence_list: Optional[List[MultiViewCorrespondence]],
        device: torch.device
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        """
        Trích xuất các phần nhúng biểu đồ chính hãng trên mỗi mẫu cho từng mục trong lô.
        Ở chế độ 'độc lập', đặt lại ngân hàng bộ nhớ cho mỗi mẫu để cách ly nghiêm ngặt.
        """
        z_graph_list = []
        valid_flags = []

        for i in range(batch_size):
            events_i = graph_events_batch[i] if (graph_events_batch and i < len(graph_events_batch)) else None
            corr_i = correspondence_list[i] if (correspondence_list and i < len(correspondence_list)) else None
            
            is_avail = (corr_i is None or corr_i.graph_available) and bool(events_i)
            if is_avail and events_i:
                if self.memory_scope_mode == "independent":
                    self.graph_extractor.memory_bank.reset_memory()
                z_g_i = self.graph_extractor.forward(events_i, device=device)
                z_graph_list.append(z_g_i.squeeze(0))
                valid_flags.append(corr_i.is_valid_for_alignment() if corr_i else True)
            else:
                z_graph_list.append(self.missing_graph_token.squeeze(0))
                valid_flags.append(False)

        z_graph_batch = torch.stack(z_graph_list, dim=0)
        valid_mask = torch.tensor(valid_flags, dtype=torch.bool, device=device)
        return z_graph_batch, valid_mask

    def extract_representation(
        self,
        seq_inputs: torch.Tensor,
        graph_events_batch: Optional[List[List[Dict[str, Any]]]] = None,
        correspondence_list: Optional[List[MultiViewCorrespondence]] = None,
        device: Optional[torch.device] = None
    ) -> torch.Tensor:
        if device is None:
            device = seq_inputs.device

        batch_size = seq_inputs.size(0)

        if self.mode == "sequence_only":
            return self.seq_extractor.forward_pool(seq_inputs)
        
        z_graph_batch, _ = self.extract_per_sample_graph_embeddings(
            graph_events_batch=graph_events_batch,
            batch_size=batch_size,
            correspondence_list=correspondence_list,
            device=device
        )

        if self.mode == "graph_only":
            return z_graph_batch

        z_seq = self.seq_extractor.forward_pool(seq_inputs)

        if self.mode == "unaligned":
            concat = torch.cat([z_seq, z_graph_batch], dim=-1)
            return self.unaligned_proj(concat)
        
        elif self.mode == "aligned":
            z_mv, _ = self.fusion(z_seq, z_graph_batch)
            return z_mv

        return z_seq

    def compute_stage_a_loss(
        self,
        seq_inputs: torch.Tensor,
        true_event_targets: torch.Tensor,
        mep_mask: Optional[torch.Tensor] = None,
        param_targets: Optional[torch.Tensor] = None,
        mpp_mask: Optional[torch.Tensor] = None,
        time_gap_targets: Optional[torch.Tensor] = None,
        graph_events_batch: Optional[List[List[Dict[str, Any]]]] = None,
        mask_edge_indices_batch: Optional[List[Set[int]]] = None,
        mask_node_indices_batch: Optional[List[Set[int]]] = None,
        correspondence_list: Optional[List[MultiViewCorrespondence]] = None,
        device: Optional[torch.device] = None
    ) -> Tuple[torch.Tensor, Dict[str, float]]:
        """
        Tính toán chính xác Chương 2 Giai đoạn Một mục tiêu đa nhiệm:
          L_StageA = L_seq_self + L_graph_self + lambda_align * L_align + lambda_fuse * L_fuse_rec
        """
        if device is None:
            device = seq_inputs.device

        batch_size = seq_inputs.size(0)

        # 1. mất mát (loss) chuỗi SSL
        seq_losses = self.seq_extractor.compute_sequence_ssl_losses(
            masked_events=seq_inputs,
            true_event_targets=true_event_targets,
            mep_mask=mep_mask,
            masked_param_slots=param_targets,
            true_param_targets=param_targets,
            mpp_mask=mpp_mask,
            true_adjacent_time_gaps=time_gap_targets
        )
        l_seq_total = sum(seq_losses.values())

        # 2. Biểu đồ mất mát (loss) SSL và trích xuất trên mỗi mẫu
        z_graph_list = []
        graph_loss_list = []
        graph_ssl_detailed: Dict[str, List[torch.Tensor]] = {}
        valid_align_flags = []

        for i in range(batch_size):
            events_i = graph_events_batch[i] if (graph_events_batch and i < len(graph_events_batch)) else None
            corr_i = correspondence_list[i] if (correspondence_list and i < len(correspondence_list)) else None

            is_avail = (corr_i is None or corr_i.graph_available) and bool(events_i)
            if is_avail and events_i:
                if self.memory_scope_mode == "independent":
                    self.graph_extractor.memory_bank.reset_memory()
                mask_e = mask_edge_indices_batch[i] if (mask_edge_indices_batch and i < len(mask_edge_indices_batch)) else ({0} if len(events_i) > 0 else set())
                mask_n = mask_node_indices_batch[i] if (mask_node_indices_batch and i < len(mask_node_indices_batch)) else ({0} if len(events_i) > 0 else set())
                z_g_i, ssl_g_i = self.graph_extractor.process_causal_events(
                    events_i,
                    device=device,
                    mask_edge_indices=mask_e,
                    mask_node_indices=mask_n
                )
                z_graph_list.append(z_g_i.squeeze(0))
                if ssl_g_i:
                    graph_loss_list.append(sum(ssl_g_i.values()))
                    for k, v in ssl_g_i.items():
                        graph_ssl_detailed.setdefault(k, []).append(v)
                valid_align_flags.append(corr_i.is_valid_for_alignment() if corr_i else True)
            else:
                z_graph_list.append(self.missing_graph_token.squeeze(0))
                valid_align_flags.append(False)

        z_graph_batch = torch.stack(z_graph_list, dim=0)
        valid_mask = torch.tensor(valid_align_flags, dtype=torch.bool, device=device)

        if graph_loss_list:
            l_graph_total = torch.stack(graph_loss_list).mean()
        else:
            l_graph_total = torch.tensor(0.0, device=device, requires_grad=True)

        # 3. Mất căn chỉnh VICreg hàng loạt thực
        z_seq_pool = self.seq_extractor.forward_pool(seq_inputs)
        p_seq = self.seq_proj_align(z_seq_pool)
        p_graph = self.graph_proj_align(z_graph_batch)

        l_vicreg, vicreg_metrics = self.vicreg(p_seq, p_graph, valid_mask=valid_mask)

        # 4. Mất khả năng tái tạo kết hợp cổng đa góc nhìn (view)
        # L_fuse_rec = 0.5 * ||z_mv - stopgrad(z_seq)||^2 + 0.5 * ||z_mv - stopgrad(z_graph)||^2
        z_mv, alpha_gate = self.fusion(z_seq_pool, z_graph_batch)
        l_fuse_rec = 0.5 * F.mse_loss(z_mv, z_seq_pool.detach()) + 0.5 * F.mse_loss(z_mv, z_graph_batch.detach())

        # 5. Tổng hợp giai đoạn A Mục tiêu
        total_loss = l_seq_total + l_graph_total + self.align_lambda * l_vicreg + self.fuse_rec_lambda * l_fuse_rec

        metrics_summary = {
            "loss_stage_a_total": float(total_loss.item()),
            "loss_seq_ssl": float(l_seq_total.item()),
            "loss_graph_ssl": float(l_graph_total.item()),
            "loss_vicreg_align": float(l_vicreg.item()),
            "loss_fuse_rec": float(l_fuse_rec.item()),
            "gate_alpha_mean": float(alpha_gate.mean().item())
        }
        for k, v in seq_losses.items():
            metrics_summary[f"seq_{k}"] = float(v.item())
        for k, v_list in graph_ssl_detailed.items():
            if v_list:
                metrics_summary[f"graph_{k}"] = float(torch.stack(v_list).mean().item())
        for k, v in vicreg_metrics.items():
            metrics_summary[f"vicreg_{k}"] = float(v)

        return total_loss, metrics_summary
