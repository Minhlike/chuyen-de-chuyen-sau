# -*- coding: utf-8 -*-
"""
StageA2Trainer: Trình thực thi tiền huấn luyện (pretraining runner) bằng đồ thị thời gian quan hệ nhân quả tất định (deterministic causal temporal graph) (Hợp đồng V1.4.1 đã bị khóa).

Tính năng:
  1. Bảo vệ thiết bị thực thi: Thiết bị thực thi bị khóa rõ ràng ('cuda' hoặc 'cpu').
     Thất bại ngay trước bất kỳ bước tối ưu hóa nào nếu CUDA được yêu cầu nhưng không có sẵn,
     với tuyệt đối không tự động fallback về CPU (zero automatic CPU fallback).
  2. Mục tiêu chính xác của nhóm đa tác vụ (multi-task group): Trong huấn luyện, các cửa sổ được sắp xếp theo trình tự thời gian
     nhóm tích lũy (tối đa gradient_accumulation_steps = 4 cửa sổ).
     Mục tiêu chính xác của nhóm đa tác vụ được tính toán trên tất cả các mục tiêu được che giấu trong nhóm:
       L_rel_group  = sum(rel_loss_sum_k) / max(1, sum(rel_target_count_k))
       L_node_group = sum(node_sq_err_sum_k) / max(1, sum(node_element_count_k))
       L_time_group = sum(time_loss_sum_k) / max(1, sum(time_target_count_k))
       L_graph_group = 1.0 * L_rel_group + 1.0 * L_node_group + 0.1 * L_time_group
     Truyền ngược mục tiêu nhóm chính xác trong một lần truyền ngược cho mỗi bước tối ưu hóa.
  3. Mặt nạ xác thực xác định đã sửa lỗi: Sử dụng trình tạo RNG xác thực chuyên dụng được đặt lại thành
     VALIDATION_MASK_SEED = 20260823 on each validation epoch (Bernoulli p=0.15 for relations and nodes).
     Độc lập với quỹ đạo huấn luyện RNG.
  4. Tổng hợp mất mát (loss) epoch toàn cầu: Tổng hợp chính xác các tử số mất mát (loss) và số lượng mục tiêu trên tất cả
     cửa sổ trong một epoch (không có nghĩa là cửa sổ).
  5. Cửa sổ cuối cùng một phần & Trọng số nhóm: 2.291 cửa sổ đầy đủ (256 sự kiện) + 1 cửa sổ một phần (81 sự kiện)
     được nhóm thành 572 nhóm gồm 1024 sự kiện + 1 nhóm 849 sự kiện (256 + 256 + 256 + 81).
  6. Con trỏ luồng hoạt động: stream_cursor tiến lên trên mọi cửa sổ; tuần tự hóa các checkpoint
     khe chính xác của cửa sổ tiếp theo; quá trình resume sử dụng stream_cursor trực tiếp.
  7. Bộ lập lịch giới hạn phạm vi động: Tính toán chính xác từ tập hợp con thực thi được ủy quyền (586.577 sự kiện).
  8. Đặt lại ranh giới phân chia quy nạp: Xóa bộ nhớ nút động khi chuyển đổi xác thực.
  9. NaN/Inf Fail-Closed Protection: Phát hiện các điểm bất thường của dấu phẩy động và hủy bỏ ngay lập tức.
  10. Chính sách ranh giới checkpoint: CHECKPOINT_ONLY_AT_OPTIMIZER_BOUNDARY (grad_accum_position == 0).
  11. 14 Trạng thái có thể thay đổi bắt buộc: Tuần tự hóa trạng thái đầy đủ và khôi phục chính xác.
"""

import os
import time
import random
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Iterable

import numpy as np
import torch
import torch.nn as nn
from torch.optim import AdamW
from torch.optim.lr_scheduler import LambdaLR

from research_agent.experiments.models.temporal_graph_view_encoder import TemporalGraphViewEncoder

VALIDATION_MASK_SEED = 20260823

class EmpiricalExecutionNotAuthorizedError(RuntimeError):
    """Xảy ra khi cố gắng thực hiện thực nghiệm thực tế mà không được phép."""
    pass

class CheckpointBoundaryViolationError(RuntimeError):
    """Tăng lên khi cố gắng lưu checkpoint khi cố gắng tích lũy giữa gradient."""
    pass

class FloatingPointAnomalyError(FloatingPointError):
    """Tăng lên khi gặp NaN hoặc Inf trong tình trạng mất mát hoặc gradient (Đóng không thành công)."""
    pass

class ExecutionDeviceMismatchError(RuntimeError):
    """Xảy ra khi không thể đáp ứng được thiết bị thực thi bị khóa (Không dự phòng)."""
    pass

def get_cosine_schedule_with_warmup(
    optimizer: torch.optim.Optimizer,
    num_warmup_steps: int,
    num_training_steps: int,
    min_lr_ratio: float = 0.02
):
    """Sự khởi động tuyến tính theo sau là sự phân rã cosin."""
    def lr_lambda(current_step: int):
        if current_step < num_warmup_steps:
            return float(current_step) / float(max(1, num_warmup_steps))
        progress = float(current_step - num_warmup_steps) / float(max(1, num_training_steps - num_warmup_steps))
        cosine_decay = 0.5 * (1.0 + math.cos(math.pi * progress))
        return min_lr_ratio + (1.0 - min_lr_ratio) * cosine_decay
    return LambdaLR(optimizer, lr_lambda)

class StageA2Trainer:
    """
    Sắp xếp quá trình huấn luyện trước biểu đồ thời gian nhân quả Giai đoạn A2 với khả năng tiếp tục xác định nghiêm ngặt.
    """
    def __init__(
        self,
        model: TemporalGraphViewEncoder,
        learning_rate: float = 5e-4,
        weight_decay: float = 0.01,
        min_lr: float = 1e-5,
        warmup_ratio: float = 0.05,
        temporal_window_size: int = 256,
        gradient_accumulation_steps: int = 4,
        clip_norm: float = 1.0,
        max_epochs: int = 12,
        early_stopping_patience: int = 3,
        seed: int = 42,
        execution_device: str = "cuda", # "cuda" hoặc "cpu"
        execution_mode: str = "FIXTURE_TEST", # "FIXTURE_TEST" hoặc "REAL_EMPIRICAL"
        empirical_authorized: bool = False,
        total_steps_override: Optional[int] = None
    ):
        self.model = model
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay
        self.min_lr = min_lr
        self.warmup_ratio = warmup_ratio
        self.temporal_window_size = temporal_window_size
        self.gradient_accumulation_steps = gradient_accumulation_steps
        self.clip_norm = clip_norm
        self.max_epochs = max_epochs
        self.early_stopping_patience = early_stopping_patience
        self.seed = seed
        self.execution_device = execution_device
        self.execution_mode = execution_mode
        self.empirical_authorized = empirical_authorized

        # Xác minh thiết bị & Bảo vệ không dự phòng nghiêm ngặt
        if self.execution_device == "cuda":
            if not torch.cuda.is_available():
                raise ExecutionDeviceMismatchError(
                    "FATAL: Execution device is explicitly locked to 'cuda', but torch.cuda.is_available() is False! "
                    "Automatic CPU fallback is strictly prohibited by Protocol V1.4."
                )
            self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cuda")
        elif self.execution_device == "cpu":
            self.device = torch.device("cpu")
        else:
            raise ValueError(f"Unknown execution_device: {self.execution_device}")

        self.model.to(self.device)

        # Trình tối ưu hóa: AdamW
        self.optimizer = AdamW(
            self.model.parameters(),
            lr=self.learning_rate,
            betas=(0.9, 0.98),
            eps=1e-8,
            weight_decay=self.weight_decay
        )

        # Lên lịch cấu hình
        if total_steps_override is not None:
            self.total_steps = total_steps_override
            self.warmup_steps = max(1, int(self.total_steps * self.warmup_ratio))
        else:
            self.configure_empirical_schedule(train_events_count=586577)

        min_ratio = self.min_lr / self.learning_rate
        self.scheduler = get_cosine_schedule_with_warmup(
            self.optimizer,
            num_warmup_steps=self.warmup_steps,
            num_training_steps=self.total_steps,
            min_lr_ratio=min_ratio
        )

        # Trình tạo mặt nạ huấn luyện RNG cho trình tự huấn luyện xác định
        self.mask_generator = torch.Generator(device="cpu")
        self.mask_generator.manual_seed(seed)

        # Trình tạo mặt nạ xác thực RNG cho mặt nạ xác thực cố định trên các epoch/seed
        self.val_mask_generator = torch.Generator(device="cpu")
        self.val_mask_generator.manual_seed(VALIDATION_MASK_SEED)

        # Trạng thái quỹ đạo có thể thay đổi
        self.current_epoch = 0
        self.completed_epoch = 0
        self.next_epoch_to_run = 0
        self.global_step = 0
        self.grad_accum_position = 0 # 0..gradient_accumulation_steps-1
        self.stream_cursor = 0        # Lập chỉ mục con trỏ hoạt động của cửa sổ tiếp theo để xử lý
        self.current_split = "TRAIN"

        # Trạng thái dừng sớm (early stopping)
        self.best_val_loss = float("inf")
        self.patience_counter = 0
        self.best_epoch = 0
        self.best_checkpoint_global_step = 0
        self.best_checkpoint_path: Optional[str] = None

        # bảo vệ
        if self.execution_mode == "REAL_EMPIRICAL" and not self.empirical_authorized:
            raise EmpiricalExecutionNotAuthorizedError(
                "Real empirical HDFS execution is NOT authorized in this session."
            )

    def configure_empirical_schedule(self, train_events_count: int = 586577):
        """
        Lấy các tham số bộ lập lịch chính xác từ tập hợp con thực thi được ủy quyền:
          - Sự kiện đồ thị tàu: 586.577
          - Kích thước cửa sổ: 256
          - Windows mỗi epoch: ceil(586577/256) = 2292
          - Điểm tích lũy tốt nghiệp: 4
          - Các bước tối ưu hóa trên mỗi epoch: 2292 // 4 = 573
          - epoch tối đa: 12
          - Các bước tối ưu hóa tối đa: 12 * 573 = 6.876
          - Các bước khởi động: 6.876 * 0,05 = 343
        """
        self.train_windows_per_epoch = math.ceil(train_events_count / self.temporal_window_size)
        self.optimizer_steps_per_epoch = self.train_windows_per_epoch // self.gradient_accumulation_steps
        self.total_steps = self.max_epochs * self.optimizer_steps_per_epoch
        self.warmup_steps = int(self.total_steps * self.warmup_ratio)

    def process_group(
        self,
        group_windows: List[List[Dict[str, Any]]],
        is_training: bool = True
    ) -> Dict[str, Any]:
        """
        Xử lý nhóm tích lũy nhiều cửa sổ (tối đa cửa sổ gradient_accumulation_steps):
          1. Chuyển tiếp tuần tự qua các cửa sổ theo thứ tự thời gian với các cập nhật bộ nhớ động.
          2. Giữ nguyên BPTT bị cắt bớt bằng cách tách bộ nhớ ở mỗi ranh giới cửa sổ.
          3. Thu thập các tensor tử số mất mát (loss) chính xác và che số mục tiêu trên tất cả các cửa sổ trong nhóm.
          4. Tính toán chính xác mục tiêu nhóm đa tác vụ:
               L_rel_group  = sum(rel_loss_sum_k) / max(1, sum(rel_target_count_k))
               L_node_group = sum(node_sq_err_sum_k) / max(1, sum(node_element_count_k))
               L_time_group = sum(time_loss_sum_k) / max(1, sum(time_target_count_k))
               L_graph_group = 1.0 * L_rel_group + 1.0 * L_node_group + 0.1 * L_time_group
          5. Truyền ngược mục tiêu nhóm chính xác trong một lần truyền ngược cho mỗi bước tối ưu hóa.
          6. Thực hiện cắt gradient, bước tối ưu hóa và bước lập lịch ở ranh giới nhóm.
          7. Tiến hành hoạt động stream_cursor theo len(group_windows).
        """
        self.model.train() if is_training else self.model.eval()

        gen = self.mask_generator if is_training else self.val_mask_generator

        group_rel_losses = []
        group_node_losses = []
        group_time_losses = []

        total_rel_targets = 0
        total_node_elements = 0
        total_node_targets = 0
        total_time_targets = 0
        total_events = 0

        for window in group_windows:
            res = self.model.forward_event_window(
                events=window,
                mask_generator=gen,
                is_training=is_training
            )
            group_rel_losses.append(res["rel_loss_sum_tensor"])
            group_node_losses.append(res["node_sq_err_sum_tensor"])
            group_time_losses.append(res["time_loss_sum_tensor"])

            total_rel_targets += res["rel_target_count"]
            total_node_elements += res["node_element_count"]
            total_node_targets += res["node_target_count"]
            total_time_targets += res["time_target_count"]
            total_events += res["num_events"]

            self.stream_cursor += 1

        # Tổng các tử số trong nhóm
        sum_rel_tensor = torch.stack(group_rel_losses).sum() if group_rel_losses else torch.tensor(0.0, device=self.device)
        sum_node_tensor = torch.stack(group_node_losses).sum() if group_node_losses else torch.tensor(0.0, device=self.device)
        sum_time_tensor = torch.stack(group_time_losses).sum() if group_time_losses else torch.tensor(0.0, device=self.device)

        # Mẫu số nhóm đa tác vụ chính xác
        L_rel_group = sum_rel_tensor / max(1, total_rel_targets) if total_rel_targets > 0 else torch.tensor(0.0, device=self.device)
        L_node_group = sum_node_tensor / max(1, total_node_elements) if total_node_elements > 0 else torch.tensor(0.0, device=self.device)
        L_time_group = sum_time_tensor / max(1, total_time_targets) if total_time_targets > 0 else torch.tensor(0.0, device=self.device)

        L_graph_group = 1.0 * L_rel_group + 1.0 * L_node_group + 0.1 * L_time_group

        loss_val = L_graph_group.item()
        if math.isnan(loss_val) or math.isinf(loss_val):
            raise FloatingPointAnomalyError(
                f"FATAL: NaN/Inf detected in group loss value ({loss_val}) at global_step={self.global_step}, cursor={self.stream_cursor}!"
            )

        if is_training:
            L_graph_group.backward()

            # Kiểm tra NaN / Inf trên gradient tham số
            for name, param in self.model.named_parameters():
                if param.grad is not None:
                    if torch.isnan(param.grad).any() or torch.isinf(param.grad).any():
                        raise FloatingPointAnomalyError(
                            f"FATAL: NaN/Inf detected in gradients for parameter '{name}' at step {self.global_step}!"
                        )

            if self.clip_norm > 0:
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), self.clip_norm)
            self.optimizer.step()
            self.scheduler.step()
            self.optimizer.zero_grad()
            self.global_step += 1
            self.grad_accum_position = 0

        return {
            "loss": loss_val,
            "loss_rel": L_rel_group.item() if isinstance(L_rel_group, torch.Tensor) else float(L_rel_group),
            "loss_node": L_node_group.item() if isinstance(L_node_group, torch.Tensor) else float(L_node_group),
            "loss_time": L_time_group.item() if isinstance(L_time_group, torch.Tensor) else float(L_time_group),
            "rel_loss_sum": sum_rel_tensor.item() if isinstance(sum_rel_tensor, torch.Tensor) else float(sum_rel_tensor),
            "rel_target_count": total_rel_targets,
            "node_sq_err_sum": sum_node_tensor.item() if isinstance(sum_node_tensor, torch.Tensor) else float(sum_node_tensor),
            "node_element_count": total_node_elements,
            "node_target_count": total_node_targets,
            "time_loss_sum": sum_time_tensor.item() if isinstance(sum_time_tensor, torch.Tensor) else float(sum_time_tensor),
            "time_target_count": total_time_targets,
            "global_step": self.global_step,
            "grad_accum_position": self.grad_accum_position,
            "stream_cursor": self.stream_cursor,
            "masked_rel_count": total_rel_targets,
            "masked_node_count": total_node_targets,
            "num_events": total_events,
            "num_windows": len(group_windows)
        }

    def process_window(
        self,
        window_events: List[Dict[str, Any]],
        is_training: bool = True,
        group_total_events: Optional[int] = None
    ) -> Dict[str, Any]:
        """Phương pháp xử lý một cửa sổ tiện lợi."""
        return self.process_group([window_events], is_training=is_training)

    def train_one_epoch(self, window_stream: Iterable[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Thực hiện một epoch huấn luyện đầy đủ trên các cửa sổ theo trình tự thời gian bằng cách gộp vào
        nhóm tích lũy và tính toán chính xác các mục tiêu của nhóm đa tác vụ (multi-task group).
        """
        self.current_split = "TRAIN"
        self.model.train()

        total_rel_loss_sum = 0.0
        total_rel_target_count = 0
        total_node_sq_err_sum = 0.0
        total_node_element_count = 0
        total_time_loss_sum = 0.0
        total_time_target_count = 0
        total_events = 0
        windows_count = 0

        t0 = time.time()
        curr_group = []
        for window in window_stream:
            curr_group.append(window)
            windows_count += 1
            if len(curr_group) == self.gradient_accumulation_steps:
                stats = self.process_group(curr_group, is_training=True)
                total_rel_loss_sum += stats["rel_loss_sum"]
                total_rel_target_count += stats["rel_target_count"]
                total_node_sq_err_sum += stats["node_sq_err_sum"]
                total_node_element_count += stats["node_element_count"]
                total_time_loss_sum += stats["time_loss_sum"]
                total_time_target_count += stats["time_target_count"]
                total_events += stats["num_events"]
                curr_group = []

        # Xóa nhóm phần cuối cùng nếu có
        if curr_group:
            stats = self.process_group(curr_group, is_training=True)
            total_rel_loss_sum += stats["rel_loss_sum"]
            total_rel_target_count += stats["rel_target_count"]
            total_node_sq_err_sum += stats["node_sq_err_sum"]
            total_node_element_count += stats["node_element_count"]
            total_time_loss_sum += stats["time_loss_sum"]
            total_time_target_count += stats["time_target_count"]
            total_events += stats["num_events"]
            curr_group = []

        epoch_runtime = time.time() - t0
        curr_lr = self.optimizer.param_groups[0]["lr"]

        epoch_L_rel = total_rel_loss_sum / max(1, total_rel_target_count) if total_rel_target_count > 0 else 0.0
        epoch_L_node = total_node_sq_err_sum / max(1, total_node_element_count) if total_node_element_count > 0 else 0.0
        epoch_L_time = total_time_loss_sum / max(1, total_time_target_count) if total_time_target_count > 0 else 0.0
        epoch_L_graph = 1.0 * epoch_L_rel + 1.0 * epoch_L_node + 0.1 * epoch_L_time

        return {
            "epoch": self.current_epoch,
            "split": "TRAIN",
            "train_L_graph": epoch_L_graph,
            "train_L_rel": epoch_L_rel,
            "train_L_node": epoch_L_node,
            "train_L_time": epoch_L_time,
            "rel_loss_sum": total_rel_loss_sum,
            "rel_target_count": total_rel_target_count,
            "node_sq_err_sum": total_node_sq_err_sum,
            "node_element_count": total_node_element_count,
            "node_target_count": total_node_element_count // 6,
            "time_loss_sum": total_time_loss_sum,
            "time_target_count": total_time_target_count,
            "windows_count": windows_count,
            "events_count": total_events,
            "optimizer_steps": self.global_step,
            "learning_rate": curr_lr,
            "epoch_runtime_sec": epoch_runtime,
            "nan_inf_count": 0
        }

    def validate_one_epoch(self, window_stream: Iterable[List[Dict[str, Any]]]) -> Dict[str, Any]:
        """
        Thực hiện một epoch xác thực đầy đủ:
          - Áp dụng INDUCTIVE_SPLIT_RESET_ZERO_MEMORY trước khi xác thực
          - Đặt lại trình tạo mặt nạ xác thực thành VALIDATION_MASK_SEED cố định = 20260823
          - Tính toán tổng hợp số liệu toàn cầu chính xác (tử số / mẫu số)
          - Không có gradient, không có cập nhật trình tối ưu hóa/lập lịch
          - Áp dụng INDUCTIVE_SPLIT_RESET_ZERO_MEMORY sau khi xác thực trước khi quay lại huấn luyện
        """
        self.current_split = "VAL"
        self.model.eval()

        # Thiết lập lại ranh giới phân chia: Đánh giá quy nạp không yêu cầu bộ nhớ ban đầu
        self.model.reset_node_states()

        # Đặt lại trình tạo mặt nạ xác thực cố định để đảm bảo mặt nạ giống hệt nhau trên các epoch và seed
        self.val_mask_generator.manual_seed(VALIDATION_MASK_SEED)

        total_rel_loss_sum = 0.0
        total_rel_target_count = 0
        total_node_sq_err_sum = 0.0
        total_node_element_count = 0
        total_time_loss_sum = 0.0
        total_time_target_count = 0
        total_events = 0
        windows_count = 0

        t0 = time.time()
        with torch.no_grad():
            for window in window_stream:
                res = self.model.forward_event_window(
                    events=window,
                    mask_generator=self.val_mask_generator,
                    is_training=False
                )
                total_rel_loss_sum += res["rel_loss_sum"]
                total_rel_target_count += res["rel_target_count"]
                total_node_sq_err_sum += res["node_sq_err_sum"]
                total_node_element_count += res["node_element_count"]
                total_time_loss_sum += res["time_loss_sum"]
                total_time_target_count += res["time_target_count"]
                total_events += res["num_events"]
                windows_count += 1
                self.stream_cursor += 1

        # Đặt lại ranh giới phân chia sau xác thực: Không thực hiện các tương tác xác thực vào epoch huấn luyện tiếp theo
        self.model.reset_node_states()

        epoch_runtime = time.time() - t0

        val_L_rel = total_rel_loss_sum / max(1, total_rel_target_count) if total_rel_target_count > 0 else 0.0
        val_L_node = total_node_sq_err_sum / max(1, total_node_element_count) if total_node_element_count > 0 else 0.0
        val_L_time = total_time_loss_sum / max(1, total_time_target_count) if total_time_target_count > 0 else 0.0
        val_L_graph = 1.0 * val_L_rel + 1.0 * val_L_node + 0.1 * val_L_time

        return {
            "epoch": self.current_epoch,
            "split": "VAL",
            "val_L_graph": val_L_graph,
            "val_L_rel": val_L_rel,
            "val_L_node": val_L_node,
            "val_L_time": val_L_time,
            "rel_loss_sum": total_rel_loss_sum,
            "rel_target_count": total_rel_target_count,
            "node_sq_err_sum": total_node_sq_err_sum,
            "node_element_count": total_node_element_count,
            "node_target_count": total_node_element_count // 6,
            "time_loss_sum": total_time_loss_sum,
            "time_target_count": total_time_target_count,
            "windows_count": windows_count,
            "events_count": total_events,
            "epoch_runtime_sec": epoch_runtime,
            "nan_inf_count": 0
        }

    def save_checkpoint(self, path: Path, metadata: Optional[Dict[str, Any]] = None):
        """
        Lưu nguyên tử trạng thái checkpoint có thể thay đổi 14 phần tử hoàn chỉnh.
        Thực thi CHECKPOINT_ONLY_AT_OPTIMIZER_BOUNDARY (grad_accum_position == 0).
        """
        if self.grad_accum_position != 0:
            raise CheckpointBoundaryViolationError(
                f"Checkpoints are strictly permitted only at optimizer step boundaries! "
                f"(current grad_accum_position={self.grad_accum_position} != 0)"
            )

        path.parent.mkdir(parents=True, exist_ok=True)

        # 4-bộ trạng thái RNG
        rng_states_4tuple = {
            "python_random": random.getstate(),
            "numpy_random": np.random.get_state(),
            "torch_cpu": torch.get_rng_state(),
            "torch_cuda": torch.cuda.get_rng_state_all() if torch.cuda.is_available() else None
        }

        node_states = self.model.get_node_states()

        state_dict = {
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.optimizer.state_dict(),
            "scheduler_state_dict": self.scheduler.state_dict(),
            "node_memory_states": node_states["node_memory_states"],
            "node_last_interaction_timestamps": node_states["node_last_interaction_timestamps"],
            "node_causal_in_degrees": node_states["node_causal_in_degrees"],
            "node_causal_out_degrees": node_states["node_causal_out_degrees"],
            "node_temporal_history_buffers": node_states["node_temporal_history_buffers"],
            "rng_states_4tuple": rng_states_4tuple,
            "stream_iterator_state": {
                "current_split": self.current_split,
                "current_epoch": self.current_epoch,
                "completed_epoch": self.completed_epoch,
                "next_epoch_to_run": self.next_epoch_to_run,
                "stream_cursor": self.stream_cursor, # Trỏ tới cửa sổ NEXT chính xác để xử lý
                "grad_accum_position": self.grad_accum_position
            },
            "masking_rng_state": self.mask_generator.get_state(),
            "early_stopping_state": {
                "best_val_loss": self.best_val_loss,
                "patience_counter": self.patience_counter,
                "best_epoch": self.best_epoch,
                "best_checkpoint_global_step": self.best_checkpoint_global_step,
                "best_checkpoint_path": self.best_checkpoint_path
            },
            "completed_epoch": self.completed_epoch,
            "next_epoch_to_run": self.next_epoch_to_run,
            "global_step": self.global_step,
            "current_epoch": self.current_epoch,
            "checkpoint_boundary_policy": "CHECKPOINT_ONLY_AT_OPTIMIZER_BOUNDARY",
            "checkpoint_metadata": metadata or {}
        }

        torch.save(state_dict, path)

    def load_checkpoint(self, path: Path):
        """Khôi phục trạng thái 14 phần tử hoàn chỉnh từ checkpoint."""
        if not path.exists():
            raise FileNotFoundError(f"Checkpoint not found at {path}")

        checkpoint = torch.load(path, map_location=self.device, weights_only=False)

        # 1. Mô hình, Trình tối ưu hóa, Trình lập lịch
        self.model.load_state_dict(checkpoint["model_state_dict"])
        self.optimizer.load_state_dict(checkpoint["optimizer_state_dict"])
        self.scheduler.load_state_dict(checkpoint["scheduler_state_dict"])

        # 2. Bộ nhớ động và trạng thái tương tác của nút
        self.model.set_node_states(checkpoint, self.device)

        # 3. Trạng thái RNG
        rng_4tuple = checkpoint["rng_states_4tuple"]
        random.setstate(rng_4tuple["python_random"])
        np.random.set_state(rng_4tuple["numpy_random"])
        
        cpu_rng = rng_4tuple["torch_cpu"]
        if isinstance(cpu_rng, torch.Tensor):
            cpu_rng = cpu_rng.cpu()
        torch.set_rng_state(cpu_rng)

        if torch.cuda.is_available() and rng_4tuple.get("torch_cuda") is not None:
            cuda_rng = rng_4tuple["torch_cuda"]
            if isinstance(cuda_rng, list):
                cuda_rng = [s.cpu() if isinstance(s, torch.Tensor) else s for s in cuda_rng]
            elif isinstance(cuda_rng, torch.Tensor):
                cuda_rng = cuda_rng.cpu()
            torch.cuda.set_rng_state_all(cuda_rng)

        # 4. Che dấu trạng thái máy phát RNG
        mask_rng = checkpoint["masking_rng_state"]
        if isinstance(mask_rng, torch.Tensor):
            mask_rng = mask_rng.cpu()
        self.mask_generator.set_state(mask_rng)

        # 5. Trạng thái quỹ đạo và luồng lặp
        stream_st = checkpoint["stream_iterator_state"]
        self.current_split = stream_st["current_split"]
        self.current_epoch = stream_st["current_epoch"]
        self.completed_epoch = checkpoint.get("completed_epoch", stream_st.get("completed_epoch", self.current_epoch))
        self.next_epoch_to_run = checkpoint.get("next_epoch_to_run", stream_st.get("next_epoch_to_run", self.completed_epoch))
        self.stream_cursor = stream_st["stream_cursor"]
        self.grad_accum_position = stream_st["grad_accum_position"]
        self.global_step = checkpoint["global_step"]

        # 6. Trạng thái dừng sớm (early stopping)
        es_st = checkpoint["early_stopping_state"]
        self.best_val_loss = es_st["best_val_loss"]
        self.patience_counter = es_st["patience_counter"]
        self.best_epoch = es_st.get("best_epoch", 0)
        self.best_checkpoint_global_step = es_st.get("best_checkpoint_global_step", 0)
        self.best_checkpoint_path = es_st.get("best_checkpoint_path")
        return checkpoint
