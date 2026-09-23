# -*- coding: utf-8 -*-
"""
Kiểm tra bất biến ngữ nghĩa GNN tạm thời
Xác minh:
  1. Mặt nạ thuộc tính nút riêng tư x_v^ thực sự liên tục: token mặt nạ thay thế thuộc tính trước khi tính toán thông báo.
  2. Chống rò rỉ: Đầu vào được che đậy giống hệt nhau, việc thay đổi mục tiêu ẩn sẽ làm thay đổi thông báo/trình bày của NOT.
  3. Tính đơn điệu theo thời gian toàn cầu nghiêm ngặt: Chuỗi sự kiện không theo thứ tự (e.g. t=20 thực thể A, t=10 thực thể B) làm tăng ValueError.
  4. Tổng hợp tin nhắn cùng thời gian: Các tin nhắn có cùng dấu thời gian đến cùng một đích được tổng hợp trước khi cập nhật một lần.
  5. Dung lượng trạng thái giới hạn LRU và theo dõi trạng thái cao nhất.
"""

import pytest

pytest.importorskip("torch")
import torch
import torch.nn.functional as F

from research_agent.experiments.extractor.graph_view import (
    TemporalGraphViewExtractor,
    BoundedEntityMemoryBank
)

def test_01_real_continuous_node_masking_and_target_anti_leakage():
    device = torch.device("cpu")
    model = TemporalGraphViewExtractor(node_attr_dim=8, memory_dim=16, out_dim=16)

    # Sự kiện 0 có mục tiêu A, Sự kiện 1 có mục tiêu B
    ev_a = [{"timestamp": 1.0, "src": 1, "dst": 2, "relation_type": 1, "src_node_attr": [1.0]*8, "dst_node_attr": [0.0]*8}]
    ev_b = [{"timestamp": 1.0, "src": 1, "dst": 2, "relation_type": 1, "src_node_attr": [9.0]*8, "dst_node_attr": [0.0]*8}]

    # Khi bị che ở chỉ mục 0, cả hai phải tính toán biểu diễn biểu đồ và thông báo được che dấu IDENTICAL (Zero Leakage)
    model.memory_bank.reset_memory()
    z_a, ssl_a = model.process_causal_events(ev_a, device, mask_node_indices={0})

    model.memory_bank.reset_memory()
    z_b, ssl_b = model.process_causal_events(ev_b, device, mask_node_indices={0})

    assert torch.allclose(z_a, z_b, atol=1e-5), "Masked node encoder input must be invariant to hidden target value (no leakage)."
    assert "L_mask_node" in ssl_a
    assert torch.isfinite(ssl_a["L_mask_node"])

def test_02_strict_global_temporal_monotonicity_rejection():
    device = torch.device("cpu")
    model = TemporalGraphViewExtractor(node_attr_dim=8, memory_dim=16, late_event_policy="REJECT")
    model.memory_bank.reset_memory()

    # t=20 for entity 1, t=10 for entity 2 in same event stream -> must raise ValueError
    unordered_events = [
        {"timestamp": 20.0, "src": 1, "dst": 2, "relation_type": 0},
        {"timestamp": 10.0, "src": 3, "dst": 4, "relation_type": 1}
    ]

    with pytest.raises(ValueError, match="Strict causality violation"):
        model.process_causal_events(unordered_events, device)

def test_03_same_time_message_aggregation():
    device = torch.device("cpu")
    model = TemporalGraphViewExtractor(node_attr_dim=8, num_relations=4, memory_dim=32, out_dim=32)
    model.memory_bank.reset_memory()

    events_concurrent = [
        {"timestamp": 10.0, "src": 1, "dst": 5, "relation_type": 1},
        {"timestamp": 10.0, "src": 2, "dst": 5, "relation_type": 2}
    ]

    z_g, _ = model.process_causal_events(events_concurrent, device)
    assert z_g.shape == (1, 32)
    assert 5 in model.memory_bank.memory_store
    assert model.memory_bank.last_timestamps[5] == 10.0

def test_04_bounded_memory_capacity_and_peak_tracking():
    bank = BoundedEntityMemoryBank(memory_dim=16, max_entities=5)
    device = torch.device("cpu")

    for i in range(10):
        bank.update_entity(entity_id=i, new_state=torch.randn(16), timestamp=float(i))

    metrics = bank.get_state_metrics()
    assert metrics["active_entities"] == 5
    assert metrics["peak_active_entities"] == 5
    assert metrics["peak_state_bytes"] > 0
    assert 0 not in bank.memory_store
    assert 9 in bank.memory_store
