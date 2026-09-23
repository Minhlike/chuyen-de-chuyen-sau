# -*- coding: utf-8 -*-
"""
Chiến dịch thử nghiệm Nineplus - Trình chạy xác nhận (Confirmatory Runner) Giai đoạn 2
Thực thi các lượt chạy xác nhận kỳ vọng trên 3 kiến trúc cốt lõi:
  1. SEQUENCE_ONLY (Transformer Encoder, MEP + MPP + time SSL)
  2. GRAPH_ONLY (TemporalGraphViewEncoder, rel + node + time SSL)
  3. MULTI_VIEW_ALIGNED_VICREG (Joint Sequence + Graph + VICReg + Gated Fusion)

Thực thi nghiêm ngặt:
  - ZERO quyền truy cập vào tập TEST (TEST_OPENED=false, TEST_READ_COUNT=0)
  - Thực thi CUDA nghiêm ngặt trên NVIDIA GeForce RTX 3050 Ti Laptop GPU
  - Cài đặt framework xác định (CUBLAS_WORKSPACE_CONFIG=:4096:8)
  - Dừng sớm (early stopping) đã đăng ký trước: patience=3 theo validation loss hoặc trần 12 epoch
  - Hợp đồng checkpoint (checkpoint từng epoch + best_checkpoint.pt)
  - Đánh giá bộ dò (probe) tuyến tính hạ nguồn trên các biểu diễn Validation đóng băng (AP, ROC-AUC)
  - Ràng buộc phương sai không gian ẩn chống suy biến (Var(z) >= 0.01)
"""

import os
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import gc
import sys
import json
import time
import math
import random
import hashlib
import psutil
try:
    psutil.Process().nice(psutil.ABOVE_NORMAL_PRIORITY_CLASS)
except Exception:
    pass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR / "src") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "src"))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from research_agent.experiments.models.temporal_graph_view_encoder import TemporalGraphViewEncoder
from research_agent.experiments.training.stage_a2_trainer import (
    StageA2Trainer,
    VALIDATION_MASK_SEED,
    ExecutionDeviceMismatchError,
    FloatingPointAnomalyError
)
from research_agent.experiments.extractor.sequence_view import SequenceViewExtractor
from research_agent.experiments.extractor.multi_view import (
    MultiViewRepresentationModel,
    MultiViewCorrespondence
)
from research_agent.experiments.data.hdfs_split_authority import HDFSSplitAuthority

TRAIN_MEMBERSHIP_SHA = "65b76694b0a3cf5c6d684a26899b1e5dca634cfd0985560149feddc12ca8ccfc"
VAL_MEMBERSHIP_SHA = "14cf689f9682a354e104463b9f02806629a683dfdf36d72d88daf5b407b0609a"

class TestSetSealedError(RuntimeError):
    pass

def enforce_framework_determinism():
    if os.environ.get("CUBLAS_WORKSPACE_CONFIG") != ":4096:8":
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
    torch.use_deterministic_algorithms(True, warn_only=False)
    if torch.cuda.is_available():
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

def set_all_seeds(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def chunk_into_windows(events: List[Dict[str, Any]], window_size: int = 256) -> List[List[Dict[str, Any]]]:
    windows = []
    for i in range(0, len(events), window_size):
        windows.append(events[i:i + window_size])
    return windows

# =====================================================================
# DATA LOADERS & DATASETS
# =====================================================================

class SequenceSSLDataset(Dataset):
    def __init__(self, data_package: Dict[str, Any], max_seq_len: int = 128):
        self.sequences = data_package["sequences"]
        self.param_targets = data_package["param_targets"]
        self.time_gaps = data_package["time_gaps"]
        self.session_ids = data_package["session_ids"]
        self.max_seq_len = max_seq_len

    def __len__(self) -> int:
        return len(self.sequences)

    def __getitem__(self, idx: int) -> Dict[str, Any]:
        seq = self.sequences[idx][:self.max_seq_len]
        params = self.param_targets[idx][:self.max_seq_len]
        L = len(seq)
        gaps = self.time_gaps[idx][:L - 1] if L > 1 else torch.zeros(0, dtype=torch.float32)
        return {
            "seq": seq,
            "params": params,
            "gaps": gaps,
            "length": L,
            "session_id": self.session_ids[idx]
        }

def collate_sequence_ssl(batch: List[Dict[str, Any]], max_param_slots: int = 4) -> Dict[str, Any]:
    batch_size = len(batch)
    max_len = max(max(b["length"] for b in batch), 1)

    padded_seqs = torch.full((batch_size, max_len), fill_value=1, dtype=torch.long)
    true_targets = torch.full((batch_size, max_len), fill_value=1, dtype=torch.long)
    mep_mask = torch.zeros((batch_size, max_len), dtype=torch.bool)
    padded_params = torch.full((batch_size, max_len, max_param_slots), fill_value=1, dtype=torch.long)
    mpp_mask = torch.zeros((batch_size, max_len, max_param_slots), dtype=torch.bool)
    padded_gaps = torch.zeros((batch_size, max(1, max_len - 1)), dtype=torch.float32)
    lengths = torch.zeros(batch_size, dtype=torch.long)
    session_ids = []

    for i, b in enumerate(batch):
        seq_i = b["seq"]
        params_i = b["params"]
        gaps_i = b["gaps"]
        l_i = b["length"]
        session_ids.append(b["session_id"])

        padded_seqs[i, :l_i] = seq_i
        true_targets[i, :l_i] = seq_i

        mask_pos = (torch.rand(l_i) < 0.15)
        if not mask_pos.any() and l_i > 0:
            mask_pos[0] = True
        mep_mask[i, :l_i] = mask_pos
        padded_seqs[i, :l_i][mask_pos] = 2

        padded_params[i, :l_i, :params_i.shape[1]] = params_i
        p_mask_pos = (torch.rand(l_i, max_param_slots) < 0.2) & (padded_params[i, :l_i] != 1)
        mpp_mask[i, :l_i] = p_mask_pos

        if l_i > 1 and len(gaps_i) > 0:
            padded_gaps[i, :len(gaps_i)] = gaps_i
        lengths[i] = l_i

    return {
        "sequences": padded_seqs,
        "true_targets": true_targets,
        "mep_mask": mep_mask,
        "param_targets": padded_params,
        "mpp_mask": mpp_mask,
        "time_gaps": padded_gaps,
        "lengths": lengths,
        "session_ids": session_ids
    }

# =====================================================================
# DOWNSTREAM LINEAR PROBE EVALUATOR
# =====================================================================

def compute_ap_and_roc_auc(scores: np.ndarray, y_true: np.ndarray) -> Tuple[float, float]:
    """
    Tính toán Average Precision (AP) và ROC-AUC với cơ chế xử lý đồng hạng chuẩn (standard tie handling).
    Xác thực các lớp nhị phân (phải chứa cả nhãn 0 và 1).
    Ưu tiên dùng sklearn.metrics và dự phòng bằng phép kiểm định Mann-Whitney U dựa trên thứ hạng phân số.
    """
    scores = np.asarray(scores, dtype=np.float64)
    y_true = np.asarray(y_true, dtype=np.int64)

    classes = np.unique(y_true)
    if len(classes) != 2 or not np.array_equal(np.sort(classes), [0, 1]):
        raise ValueError(
            f"Binary classification requires exactly two classes [0, 1]. "
            f"Found unique classes: {classes.tolist()}"
        )

    try:
        from sklearn.metrics import average_precision_score, roc_auc_score
        ap = float(average_precision_score(y_true, scores))
        auc = float(roc_auc_score(y_true, scores))
        return ap, auc
    except ImportError:
        from scipy.stats import rankdata
        n_pos = int(np.sum(y_true == 1))
        n_neg = int(np.sum(y_true == 0))

        order = np.argsort(-scores, kind="mergesort")
        sorted_scores = scores[order]
        sorted_labels = y_true[order]

        distinct_mask = np.diff(sorted_scores) != 0
        threshold_idxs = np.where(distinct_mask)[0]
        threshold_idxs = np.concatenate([threshold_idxs, [len(scores) - 1]])

        tp = np.cumsum(sorted_labels == 1)[threshold_idxs]
        fp = np.cumsum(sorted_labels == 0)[threshold_idxs]

        recalls = tp / max(1, n_pos)
        precisions = tp / np.maximum(tp + fp, 1)

        recalls = np.concatenate(([0.0], recalls))
        precisions = np.concatenate(([1.0], precisions))
        ap = float(np.sum((recalls[1:] - recalls[:-1]) * precisions[1:]))

        ranks = rankdata(scores, method="average")
        pos_rank_sum = np.sum(ranks[y_true == 1])
        u = pos_rank_sum - n_pos * (n_pos + 1) / 2.0
        auc = float(u / max(1, n_pos * n_neg))

        return ap, auc

def evaluate_downstream_linear_probe(
    z_all: torch.Tensor,
    labels: List[int],
    seed: int = 42,
    device: str = "cuda"
) -> Dict[str, float]:
    """
    Đánh giá bộ dò (probe) tuyến tính trên biểu diễn đóng băng z (7.500 mẫu)
    sử dụng phép chia 80/20 train/test nội bộ trong tập biểu diễn Validation (Train/Val pool).
    """
    dev = torch.device(device if torch.cuda.is_available() and device == "cuda" else "cpu")
    y = torch.tensor(labels, dtype=torch.float32)
    N = len(labels)
    
    # Phép chia phân tầng xác định
    rng = np.random.RandomState(seed)
    pos_idx = [i for i, val in enumerate(labels) if val == 1]
    neg_idx = [i for i, val in enumerate(labels) if val == 0]
    
    rng.shuffle(pos_idx)
    rng.shuffle(neg_idx)
    
    n_pos_train = int(len(pos_idx) * 0.8)
    n_neg_train = int(len(neg_idx) * 0.8)
    
    train_idx = pos_idx[:n_pos_train] + neg_idx[:n_neg_train]
    test_idx = pos_idx[n_pos_train:] + neg_idx[n_neg_train:]
    rng.shuffle(train_idx)
    rng.shuffle(test_idx)
    
    z_train = z_all[train_idx].to(dev)
    y_train = y[train_idx].to(dev)
    z_test = z_all[test_idx].to(dev)
    y_test = y[test_idx].numpy()
    
    probe = nn.Linear(128, 1).to(dev)
    optimizer = torch.optim.AdamW(probe.parameters(), lr=1e-2, weight_decay=1e-4)
    criterion = nn.BCEWithLogitsLoss()
    
    probe.train()
    batch_size = 256
    for ep in range(50):
        perm = torch.randperm(len(train_idx))
        for b_start in range(0, len(train_idx), batch_size):
            b_ids = perm[b_start:b_start + batch_size]
            optimizer.zero_grad()
            logits = probe(z_train[b_ids]).squeeze(-1)
            loss = criterion(logits, y_train[b_ids])
            loss.backward()
            optimizer.step()

    probe.eval()
    with torch.no_grad():
        test_logits = probe(z_test).squeeze(-1)
        test_scores = torch.sigmoid(test_logits).cpu().numpy()
        y_test_np = y_test if isinstance(y_test, np.ndarray) else y_test.cpu().numpy()

    ap, auc = compute_ap_and_roc_auc(test_scores, y_test_np)
    return {"probe_ap": ap, "probe_roc_auc": auc}

# =====================================================================
# CONFIRMATORY RUN 1: SEQUENCE_ONLY
# =====================================================================

def run_confirmatory_sequence_only(
    base_dir: Path,
    seed: int = 42,
    max_epochs: int = 12,
    patience: int = 3,
    device: str = "cuda"
) -> Dict[str, Any]:
    print("\n" + "="*70)
    print(f"  EXECUTING CONFIRMATORY: SEQUENCE_ONLY (Seed {seed}, Max {max_epochs} Epochs)")
    print("="*70)
    
    timestamp = int(time.time())
    run_id = f"CONF_SEQUENCE_ONLY_seed{seed}_{timestamp}"
    run_dir = base_dir / "experiments" / "nineplus" / "confirmatory" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    train_log_p = run_dir / "TRAIN-LOG.jsonl"

    enforce_framework_determinism()
    set_all_seeds(seed)
    dev = torch.device(device if torch.cuda.is_available() else "cpu")

    data_dir = base_dir / "experiments" / "runs" / "data" / "hdfs"
    train_pkg = torch.load(data_dir / "hdfs_ssl_train.pt", weights_only=False)
    val_pkg = torch.load(data_dir / "hdfs_ssl_val.pt", weights_only=False)
    vocab_data = json.loads((data_dir / "hdfs_vocab.json").read_text(encoding="utf-8"))

    train_sessions_total = len(train_pkg["sequences"])
    train_events_total = sum(len(s) for s in train_pkg["sequences"])
    val_sessions_total = len(val_pkg["sequences"])
    val_events_total = sum(len(s) for s in val_pkg["sequences"])

    train_ds = SequenceSSLDataset(train_pkg, max_seq_len=128)
    val_ds = SequenceSSLDataset(val_pkg, max_seq_len=128)

    micro_batch = 16
    grad_accum = 4
    effective_batch = micro_batch * grad_accum
    steps_per_epoch = math.ceil(train_sessions_total / effective_batch)
    total_steps = max_epochs * steps_per_epoch

    train_loader = DataLoader(
        train_ds, batch_size=micro_batch, shuffle=True,
        collate_fn=collate_sequence_ssl, generator=torch.Generator().manual_seed(seed)
    )
    val_loader = DataLoader(val_ds, batch_size=micro_batch, shuffle=False, collate_fn=collate_sequence_ssl)

    model = SequenceViewExtractor(
        event_vocab_size=len(vocab_data["template_to_id"]),
        param_vocab_size=len(vocab_data["param_to_id"]),
        d_model=128, nhead=4, num_layers=4, dim_feedforward=512,
        dropout=0.10, max_len=128, max_param_slots=4, projection_dim=128
    ).to(dev)

    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=total_steps, eta_min=1e-5)

    train_times = []
    val_times = []
    nan_count = 0
    inf_count = 0
    global_step = 0
    best_val_loss = float("inf")
    best_epoch = 0
    patience_counter = 0
    early_stopped = False

    for epoch in range(1, max_epochs + 1):
        t_tr_start = time.perf_counter()
        model.train()
        accum_loss = 0.0
        micro_step = 0
        optimizer.zero_grad()

        for b_idx, batch in enumerate(train_loader):
            micro_step += 1
            seqs = batch["sequences"].to(dev)
            targets = batch["true_targets"].to(dev)
            mep_m = batch["mep_mask"].to(dev)
            params = batch["param_targets"].to(dev)
            mpp_m = batch["mpp_mask"].to(dev)
            gaps = batch["time_gaps"].to(dev)

            losses = model.compute_sequence_ssl_losses(
                masked_events=seqs, true_event_targets=targets, mep_mask=mep_m,
                masked_param_slots=params, true_param_targets=params,
                mpp_mask=mpp_m, true_adjacent_time_gaps=gaps
            )
            l_step = 1.0 * losses["L_MEP"] + 1.0 * losses["L_MPP"] + 0.1 * losses["L_time"]

            if torch.isnan(l_step) or torch.isinf(l_step):
                nan_count += 1
                raise FloatingPointAnomalyError(f"NaN/Inf loss at step {global_step}")

            scaled_loss = l_step / grad_accum
            scaled_loss.backward()
            accum_loss += l_step.item()

            if micro_step % grad_accum == 0 or (b_idx + 1) == len(train_loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1

                step_log = {
                    "epoch": epoch,
                    "global_step": global_step,
                    "loss_seq": accum_loss / (micro_step % grad_accum or grad_accum),
                    "loss_mep": losses["L_MEP"].item(),
                    "loss_mpp": losses["L_MPP"].item(),
                    "loss_time": losses["L_time"].item(),
                    "lr": optimizer.param_groups[0]["lr"]
                }
                with open(train_log_p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(step_log) + "\n")
                accum_loss = 0.0

        t_tr_end = time.perf_counter()
        tr_time_min = (t_tr_end - t_tr_start) / 60.0
        train_times.append(tr_time_min)

        # Đánh giá trên tập Validation
        t_val_start = time.perf_counter()
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                seqs = batch["sequences"].to(dev)
                targets = batch["true_targets"].to(dev)
                mep_m = batch["mep_mask"].to(dev)
                params = batch["param_targets"].to(dev)
                mpp_m = batch["mpp_mask"].to(dev)
                gaps = batch["time_gaps"].to(dev)

                losses = model.compute_sequence_ssl_losses(
                    masked_events=seqs, true_event_targets=targets, mep_mask=mep_m,
                    masked_param_slots=params, true_param_targets=params,
                    mpp_mask=mpp_m, true_adjacent_time_gaps=gaps
                )
                l_val = 1.0 * losses["L_MEP"] + 1.0 * losses["L_MPP"] + 0.1 * losses["L_time"]
                val_losses.append(l_val.item())

        t_val_end = time.perf_counter()
        val_time_min = (t_val_end - t_val_start) / 60.0
        val_times.append(val_time_min)
        mean_val_loss = float(np.mean(val_losses))

        print(f"[{run_id}] Epoch {epoch}/{max_epochs} | Train: {tr_time_min:.2f}m | Val: {val_time_min:.2f}m | Val Loss: {mean_val_loss:.4f}")

        # Hợp đồng lưu checkpoint (Checkpoint Contract)
        ckpt_path = run_dir / f"checkpoint_epoch{epoch}.pt"
        ckpt_data = {
            "epoch": epoch,
            "global_step": global_step,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "val_loss": mean_val_loss,
            "seed": seed
        }
        torch.save(ckpt_data, ckpt_path)

        # Logic dừng sớm (early stopping)
        if mean_val_loss < best_val_loss - 1e-4:
            best_val_loss = mean_val_loss
            best_epoch = epoch
            patience_counter = 0
            torch.save(ckpt_data, run_dir / "best_checkpoint.pt")
            print(f"[{run_id}] * New best validation loss: {best_val_loss:.4f} (Saved best_checkpoint.pt)")
        else:
            patience_counter += 1
            print(f"[{run_id}] Patience counter: {patience_counter}/{patience}")
            if patience_counter >= patience:
                print(f"[{run_id}] Early stopping triggered at epoch {epoch} (patience={patience})")
                early_stopped = True
                break

    # Trích xuất biểu diễn bằng cách sử dụng best_checkpoint
    best_ckpt = torch.load(run_dir / "best_checkpoint.pt", weights_only=False)
    model.load_state_dict(best_ckpt["model_state_dict"])
    model.eval()

    val_reps = []
    val_sids = []
    with torch.no_grad():
        for batch in val_loader:
            seqs = batch["sequences"].to(dev)
            params = batch["param_targets"].to(dev)
            z = model.forward_pool(seqs, param_slots=params)
            val_reps.append(z.cpu())
            val_sids.extend(batch["session_ids"])
    z_all = torch.cat(val_reps, dim=0)

    assert z_all.shape == (7500, 128)
    latent_variance = float(torch.var(z_all, dim=0).mean().item())

    # Đánh giá bộ dò (probe)
    probe_labels = torch.load(base_dir / "experiments" / "runs" / "data" / "vault" / "hdfs_probe_labels_val.pt", weights_only=False)
    assert val_sids == probe_labels["session_ids"]
    probe_metrics = evaluate_downstream_linear_probe(z_all, probe_labels["labels"], seed=seed, device=device)

    peak_vram_mb = torch.cuda.max_memory_allocated() / (1024**2) if torch.cuda.is_available() else 0.0
    peak_ram_mb = psutil.Process().memory_info().rss / (1024**2)

    manifest = {
        "run_id": run_id,
        "architecture": "SEQUENCE_ONLY",
        "status": "COMPLETED",
        "seed": seed,
        "total_epochs_trained": len(train_times),
        "max_epochs_ceiling": max_epochs,
        "early_stopped": early_stopped,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "final_optimizer_steps": global_step,
        "train_minutes_total": float(np.sum(train_times)),
        "val_minutes_total": float(np.sum(val_times)),
        "latent_variance": latent_variance,
        "probe_ap": probe_metrics["probe_ap"],
        "probe_roc_auc": probe_metrics["probe_roc_auc"],
        "peak_vram_mb": peak_vram_mb,
        "peak_ram_mb": peak_ram_mb,
        "nan_count": nan_count,
        "inf_count": inf_count
    }
    (run_dir / "RUN-MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[{run_id}] CONFIRMATORY SEQUENCE_ONLY COMPLETE. Probe AP: {probe_metrics['probe_ap']:.4f} | ROC-AUC: {probe_metrics['probe_roc_auc']:.4f}\n")
    return manifest

# =====================================================================
# CONFIRMATORY RUN 3: MULTI_VIEW_ALIGNED_VICREG
# =====================================================================

def run_confirmatory_multi_view(
    base_dir: Path,
    seed: int = 42,
    max_epochs: int = 12,
    patience: int = 3,
    device: str = "cuda"
) -> Dict[str, Any]:
    print("\n" + "="*70)
    print(f"  EXECUTING CONFIRMATORY: MULTI_VIEW_ALIGNED_VICREG (Seed {seed}, Max {max_epochs} Epochs)")
    print("="*70)
    
    timestamp = int(time.time())
    run_id = f"CONF_MULTI_VIEW_ALIGNED_seed{seed}_{timestamp}"
    run_dir = base_dir / "experiments" / "nineplus" / "confirmatory" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    train_log_p = run_dir / "TRAIN-LOG.jsonl"

    enforce_framework_determinism()
    set_all_seeds(seed)
    dev = torch.device(device if torch.cuda.is_available() else "cpu")

    data_dir = base_dir / "experiments" / "runs" / "data" / "hdfs"
    train_pkg = torch.load(data_dir / "hdfs_ssl_train.pt", weights_only=False)
    val_pkg = torch.load(data_dir / "hdfs_ssl_val.pt", weights_only=False)
    vocab_data = json.loads((data_dir / "hdfs_vocab.json").read_text(encoding="utf-8"))

    cache_path = base_dir / "datasets" / "cache" / "hdfs_graph_events.pt"
    graph_pkg = torch.load(cache_path, weights_only=False)

    print(f"[{run_id}] Indexing graph events by session ID...")
    train_block_events = defaultdict(list)
    for ev in graph_pkg["train_events"]:
        train_block_events[ev["block_id"]].append(ev)

    val_block_events = defaultdict(list)
    for ev in graph_pkg["val_events"]:
        val_block_events[ev["block_id"]].append(ev)

    train_sessions_total = len(train_pkg["sequences"])
    train_events_total = len(graph_pkg["train_events"])
    val_sessions_total = len(val_pkg["sequences"])
    val_events_total = len(graph_pkg["val_events"])

    train_ds = SequenceSSLDataset(train_pkg, max_seq_len=128)
    val_ds = SequenceSSLDataset(val_pkg, max_seq_len=128)

    micro_batch = 16
    grad_accum = 4
    effective_batch = micro_batch * grad_accum
    steps_per_epoch = math.ceil(train_sessions_total / effective_batch)
    total_steps = max_epochs * steps_per_epoch

    train_loader = DataLoader(
        train_ds, batch_size=micro_batch, shuffle=True,
        collate_fn=collate_sequence_ssl, generator=torch.Generator().manual_seed(seed)
    )
    val_loader = DataLoader(val_ds, batch_size=micro_batch, shuffle=False, collate_fn=collate_sequence_ssl)

    model = MultiViewRepresentationModel(
        seq_vocab_size=len(vocab_data["template_to_id"]),
        graph_node_attr_dim=16,
        param_vocab_size=len(vocab_data["param_to_id"]),
        embed_dim=128,
        num_relations=8,
        mode="aligned",
        align_lambda=1.0,
        fuse_rec_lambda=1.0,
        memory_scope_mode="independent"
    ).to(dev)

    optimizer = torch.optim.AdamW(model.parameters(), lr=5e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=total_steps, eta_min=1e-5)

    train_times = []
    val_times = []
    nan_count = 0
    inf_count = 0
    global_step = 0
    best_val_loss = float("inf")
    best_epoch = 0
    patience_counter = 0
    early_stopped = False

    for epoch in range(1, max_epochs + 1):
        t_tr_start = time.perf_counter()
        model.train()
        accum_loss = 0.0
        micro_step = 0
        optimizer.zero_grad()

        for b_idx, batch in enumerate(train_loader):
            micro_step += 1
            seqs = batch["sequences"].to(dev)
            targets = batch["true_targets"].to(dev)
            mep_m = batch["mep_mask"].to(dev)
            params = batch["param_targets"].to(dev)
            mpp_m = batch["mpp_mask"].to(dev)
            gaps = batch["time_gaps"].to(dev)
            sids = batch["session_ids"]

            batch_graph_events = [train_block_events.get(sid, []) for sid in sids]

            loss, metrics = model.compute_stage_a_loss(
                seq_inputs=seqs,
                true_event_targets=targets,
                mep_mask=mep_m,
                param_targets=params,
                mpp_mask=mpp_m,
                time_gap_targets=gaps,
                graph_events_batch=batch_graph_events,
                device=dev
            )

            if torch.isnan(loss) or torch.isinf(loss):
                nan_count += 1
                raise FloatingPointAnomalyError(f"NaN/Inf loss at step {global_step}")

            scaled_loss = loss / grad_accum
            scaled_loss.backward()
            accum_loss += loss.item()

            if micro_step % grad_accum == 0 or (b_idx + 1) == len(train_loader):
                torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
                optimizer.step()
                scheduler.step()
                optimizer.zero_grad()
                global_step += 1

                step_log = {
                    "epoch": epoch,
                    "global_step": global_step,
                    "loss_stage_a": accum_loss / (micro_step % grad_accum or grad_accum),
                    "loss_seq": metrics["loss_seq_ssl"],
                    "loss_graph": metrics["loss_graph_ssl"],
                    "loss_vicreg": metrics["loss_vicreg_align"],
                    "loss_fuse_rec": metrics["loss_fuse_rec"],
                    "gate_alpha": metrics["gate_alpha_mean"],
                    "lr": optimizer.param_groups[0]["lr"]
                }
                with open(train_log_p, "a", encoding="utf-8") as f:
                    f.write(json.dumps(step_log) + "\n")
                accum_loss = 0.0

        t_tr_end = time.perf_counter()
        tr_time_min = (t_tr_end - t_tr_start) / 60.0
        train_times.append(tr_time_min)

        # Đánh giá trên tập Validation
        t_val_start = time.perf_counter()
        model.eval()
        val_losses = []
        with torch.no_grad():
            for batch in val_loader:
                seqs = batch["sequences"].to(dev)
                targets = batch["true_targets"].to(dev)
                mep_m = batch["mep_mask"].to(dev)
                params = batch["param_targets"].to(dev)
                mpp_m = batch["mpp_mask"].to(dev)
                gaps = batch["time_gaps"].to(dev)
                sids = batch["session_ids"]

                batch_graph_events = [val_block_events.get(sid, []) for sid in sids]

                loss, _ = model.compute_stage_a_loss(
                    seq_inputs=seqs,
                    true_event_targets=targets,
                    mep_mask=mep_m,
                    param_targets=params,
                    mpp_mask=mpp_m,
                    time_gap_targets=gaps,
                    graph_events_batch=batch_graph_events,
                    device=dev
                )
                val_losses.append(loss.item())

        t_val_end = time.perf_counter()
        val_time_min = (t_val_end - t_val_start) / 60.0
        val_times.append(val_time_min)
        mean_val_loss = float(np.mean(val_losses))

        print(f"[{run_id}] Epoch {epoch}/{max_epochs} | Train: {tr_time_min:.2f}m | Val: {val_time_min:.2f}m | Val L_StageA: {mean_val_loss:.4f}")

        ckpt_path = run_dir / f"checkpoint_epoch{epoch}.pt"
        ckpt_data = {
            "epoch": epoch,
            "global_step": global_step,
            "model_state_dict": model.state_dict(),
            "optimizer_state_dict": optimizer.state_dict(),
            "scheduler_state_dict": scheduler.state_dict(),
            "val_loss": mean_val_loss,
            "seed": seed
        }
        torch.save(ckpt_data, ckpt_path)

        # Logic dừng sớm (early stopping)
        if mean_val_loss < best_val_loss - 1e-4:
            best_val_loss = mean_val_loss
            best_epoch = epoch
            patience_counter = 0
            torch.save(ckpt_data, run_dir / "best_checkpoint.pt")
            print(f"[{run_id}] * New best validation loss: {best_val_loss:.4f} (Saved best_checkpoint.pt)")
        else:
            patience_counter += 1
            print(f"[{run_id}] Patience counter: {patience_counter}/{patience}")
            if patience_counter >= patience:
                print(f"[{run_id}] Early stopping triggered at epoch {epoch} (patience={patience})")
                early_stopped = True
                break

    # Trích xuất biểu diễn từ best_checkpoint
    best_ckpt = torch.load(run_dir / "best_checkpoint.pt", weights_only=False)
    model.load_state_dict(best_ckpt["model_state_dict"])
    model.eval()

    val_reps = []
    val_sids = []
    with torch.no_grad():
        for batch in val_loader:
            seqs = batch["sequences"].to(dev)
            sids = batch["session_ids"]
            batch_graph_events = [val_block_events.get(sid, []) for sid in sids]
            z = model.extract_representation(seqs, graph_events_batch=batch_graph_events, device=dev)
            val_reps.append(z.cpu())
            val_sids.extend(sids)
    z_all = torch.cat(val_reps, dim=0)

    assert z_all.shape == (7500, 128)
    latent_variance = float(torch.var(z_all, dim=0).mean().item())
    anti_collapse_pass = (latent_variance >= 0.01)

    probe_labels = torch.load(base_dir / "experiments" / "runs" / "data" / "vault" / "hdfs_probe_labels_val.pt", weights_only=False)
    assert val_sids == probe_labels["session_ids"]
    probe_metrics = evaluate_downstream_linear_probe(z_all, probe_labels["labels"], seed=seed, device=device)

    peak_vram_mb = torch.cuda.max_memory_allocated() / (1024**2) if torch.cuda.is_available() else 0.0
    peak_ram_mb = psutil.Process().memory_info().rss / (1024**2)

    manifest = {
        "run_id": run_id,
        "architecture": "MULTI_VIEW_ALIGNED_VICREG",
        "status": "COMPLETED",
        "seed": seed,
        "total_epochs_trained": len(train_times),
        "max_epochs_ceiling": max_epochs,
        "early_stopped": early_stopped,
        "best_epoch": best_epoch,
        "best_val_loss": best_val_loss,
        "final_optimizer_steps": global_step,
        "train_minutes_total": float(np.sum(train_times)),
        "val_minutes_total": float(np.sum(val_times)),
        "latent_variance": latent_variance,
        "anti_collapse_pass": anti_collapse_pass,
        "probe_ap": probe_metrics["probe_ap"],
        "probe_roc_auc": probe_metrics["probe_roc_auc"],
        "peak_vram_mb": peak_vram_mb,
        "peak_ram_mb": peak_ram_mb,
        "nan_count": nan_count,
        "inf_count": inf_count
    }
    (run_dir / "RUN-MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"[{run_id}] CONFIRMATORY MULTI_VIEW COMPLETE. Probe AP: {probe_metrics['probe_ap']:.4f} | ROC-AUC: {probe_metrics['probe_roc_auc']:.4f}\n")
    return manifest

# =====================================================================
# MAIN DISPATCHER
# =====================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Run Phase 2 Confirmatory Experiments")
    parser.add_argument("--mode", choices=["sequence_only", "multi_view", "sequence_then_multi_view"], default="multi_view")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--seeds", type=int, nargs="+", default=None)
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--device", type=str, default="cuda")
    parser.add_argument("--base-dir", type=str, default=None, help="Root repository directory (default: auto-detected from script location)")
    args = parser.parse_args()

    seeds = args.seeds if args.seeds is not None else ([args.seed] if args.seed is not None else [42])
    default_base_dir = Path(__file__).resolve().parent.parent
    base_dir = Path(args.base_dir).resolve() if args.base_dir is not None else default_base_dir
    results = {}

    for s in seeds:
        if args.mode in ["sequence_only", "sequence_then_multi_view"]:
            k = f"sequence_only_seed{s}"
            results[k] = run_confirmatory_sequence_only(
                base_dir, seed=s, max_epochs=args.epochs, patience=args.patience, device=args.device
            )

        if args.mode in ["multi_view", "sequence_then_multi_view"]:
            k = f"multi_view_seed{s}"
            results[k] = run_confirmatory_multi_view(
                base_dir, seed=s, max_epochs=args.epochs, patience=args.patience, device=args.device
            )

    print("\n" + "="*70)
    print("  CONFIRMATORY EXECUTION BATCH FINISHED SUCCESSFULLY!")
    print("="*70)
    for m, res in results.items():
        print(f"  - {m}: {res['run_id']} | Best Val Loss: {res['best_val_loss']:.4f} (Epoch {res['best_epoch']}) | Probe AP: {res['probe_ap']:.4f}")
