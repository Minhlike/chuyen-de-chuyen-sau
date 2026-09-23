# -*- coding: utf-8 -*-
"""
Các bài kiểm tra tương ứng đa góc nhìn (multi-view) VICReg và mỗi mẫu
Xác minh:
  1. Cách ly phạm vi bộ nhớ đa góc nhìn (multi-view): Biểu diễn mẫu B là bất biến cho dù được đánh giá một mình hay sau mẫu A không liên quan.
  2. Sự tương ứng trên mỗi mẫu: Hai mẫu biểu đồ riêng biệt trong cùng một lô tạo ra hai phần nhúng biểu đồ riêng biệt.
  3. Tối ưu hóa mất mát (loss) VICreg hàng loạt thực với gradient khác 0.
"""

import pytest

pytest.importorskip("torch")
import torch

from research_agent.experiments.extractor.multi_view import (
    MultiViewRepresentationModel,
    MultiViewCorrespondence,
    VICRegLoss
)

def test_01_independent_sample_memory_isolation():
    model = MultiViewRepresentationModel(
        seq_vocab_size=30,
        graph_node_attr_dim=8,
        embed_dim=16,
        mode="aligned",
        memory_scope_mode="independent"
    )
    model.eval()
    device = torch.device("cpu")

    seq_a = torch.randint(1, 30, (1, 6))
    events_a = [{"timestamp": 1.0, "src": 1, "dst": 2, "relation_type": 1}]

    seq_b = torch.randint(1, 30, (1, 6))
    events_b = [{"timestamp": 1.0, "src": 3, "dst": 4, "relation_type": 2}]

    # Đánh giá riêng mẫu B
    z_b_alone = model.extract_representation(seq_b, graph_events_batch=[events_b], device=device)

    # Đánh giá lô [mẫu A, mẫu B]
    seq_batch = torch.cat([seq_a, seq_b], dim=0)
    events_batch = [events_a, events_b]
    z_batch = model.extract_representation(seq_batch, graph_events_batch=events_batch, device=device)

    # Sự thể hiện mẫu B trong lô phải khớp chính xác với mẫu B (Rò rỉ trạng thái bằng 0)
    assert torch.allclose(z_b_alone[0], z_batch[1], atol=1e-5), "Sample B representation must be invariant to preceding batch items in independent mode."

def test_02_per_sample_distinct_graph_embeddings():
    model = MultiViewRepresentationModel(
        seq_vocab_size=40,
        graph_node_attr_dim=8,
        embed_dim=32,
        mode="aligned"
    )

    batch_size = 2
    events_sample_0 = [{"timestamp": 1.0, "src": 1, "dst": 2, "relation_type": 1}]
    events_sample_1 = [{"timestamp": 10.0, "src": 5, "dst": 6, "relation_type": 3}]
    graph_events_batch = [events_sample_0, events_sample_1]

    z_g_batch, valid_mask = model.extract_per_sample_graph_embeddings(
        graph_events_batch=graph_events_batch,
        batch_size=batch_size,
        correspondence_list=None,
        device=torch.device("cpu")
    )

    assert z_g_batch.shape == (2, 32)
    assert valid_mask.all()
    assert not torch.allclose(z_g_batch[0], z_g_batch[1], atol=1e-3)

def test_03_real_batch_vicreg_loss_and_gradients():
    model = MultiViewRepresentationModel(
        seq_vocab_size=40,
        graph_node_attr_dim=8,
        embed_dim=32,
        mode="aligned"
    )

    batch_size = 2
    seq_inputs = torch.randint(1, 40, (batch_size, 10))
    true_event_targets = torch.randint(0, 40, (batch_size, 10))

    graph_events_batch = [
        [{"timestamp": 1.0, "src": 1, "dst": 2, "relation_type": 1}],
        [{"timestamp": 2.0, "src": 3, "dst": 4, "relation_type": 2}]
    ]

    total_loss, metrics = model.compute_stage_a_loss(
        seq_inputs=seq_inputs,
        true_event_targets=true_event_targets,
        graph_events_batch=graph_events_batch
    )

    assert torch.isfinite(total_loss)
    assert metrics["loss_vicreg_align"] >= 0.0

    total_loss.backward()

    for name, p in model.seq_proj_align.named_parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all()
    for name, p in model.graph_proj_align.named_parameters():
        assert p.grad is not None and torch.isfinite(p.grad).all()
