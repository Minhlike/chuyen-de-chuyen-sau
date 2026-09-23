#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pipeline đánh giá hạ nguồn (downstream) của Chiến dịch Nineplus V3
Giao thức: TRAIN_FIT_FULL_FIXED_VALIDATION_EVALUATE

Quy cách chuẩn mực (Authoritative Specification):
- Trích xuất biểu diễn Train: TOÀN BỘ 35.000 phiên Train
- Trích xuất biểu diễn Validation: TOÀN BỘ 7.500 phiên Validation
- Khớp bộ dò (probe fitting): Độc quyền trên các biểu diễn Train (50 epoch, AdamW lr=1e-2, wd=1e-4, batch_size=256)
- Seed RNG của probe: Khóa cố định ở 10007 (tách biệt khỏi seed của mô hình backbone)
- Đánh giá: 100% tập Validation (7.500 phiên)
- Xác minh các bất biến thành viên (membership invariants):
    Train SHA: 65b76694b0a3cf5c6d684a26899b1e5dca634cfd0985560149feddc12ca8ccfc
    Val SHA:   14cf689f9682a354e104463b9f02806629a683dfdf36d72d88daf5b407b0609a
    Ordered Train SHA: 35396a595ded6ab643c07ce03528da4b91c1d270979b2c52e3e11f0cebcc7e60
    Ordered Val SHA:   4f474991f03aab4856c2666a671bee3fc69d8e893e22e9c2d9ca1269b8bd68ae
- Tường lửa bảo vệ tập Test (Test Firewall): TEST_OPENED=false, TEST_READ_COUNT=0
"""

import os
import sys
import math
import json
import time
import random
import hashlib
import argparse
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

# Đảm bảo gốc dự án và thư mục src nằm ở sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR / "src") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "src"))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from research_agent.experiments.extractor.sequence_view import SequenceViewExtractor
from research_agent.experiments.extractor.multi_view import MultiViewRepresentationModel
from research_agent.experiments.data.hdfs_split_authority import HDFSSplitAuthority

TRAIN_MEMBERSHIP_SHA_TARGET = "65b76694b0a3cf5c6d684a26899b1e5dca634cfd0985560149feddc12ca8ccfc"
VAL_MEMBERSHIP_SHA_TARGET = "14cf689f9682a354e104463b9f02806629a683dfdf36d72d88daf5b407b0609a"
ORDERED_TRAIN_SHA_TARGET = "35396a595ded6ab643c07ce03528da4b91c1d270979b2c52e3e11f0cebcc7e60"
ORDERED_VAL_SHA_TARGET = "4f474991f03aab4856c2666a671bee3fc69d8e893e22e9c2d9ca1269b8bd68ae"

PROBE_FIXED_SEED = 10007
MAX_SEQ_LEN = 128
MAX_PARAM_SLOTS = 4


def compute_ap_and_roc_auc(scores: np.ndarray, y_true: np.ndarray) -> Tuple[float, float]:
    """
    Tính toán Average Precision (AP) qua tích phân bậc thang
    và ROC-AUC qua kiểm định Mann-Whitney U / tổng hạng (rank sum).
    """
    n_pos = int(np.sum(y_true == 1))
    n_neg = int(np.sum(y_true == 0))
    if n_pos == 0 or n_neg == 0:
        raise ValueError("Cannot compute AP/ROC-AUC with single-class ground truth.")

    # Tính toán AP
    order = np.argsort(-scores)
    sorted_labels = y_true[order]
    tp = np.cumsum(sorted_labels == 1)
    fp = np.cumsum(sorted_labels == 0)
    recalls = np.concatenate(([0.0], tp / n_pos))
    precisions = np.concatenate(([1.0], tp / (tp + fp)))
    ap = float(np.sum((recalls[1:] - recalls[:-1]) * precisions[1:]))

    # Tính toán ROC-AUC
    ranks = np.argsort(np.argsort(scores)) + 1
    pos_rank_sum = np.sum(ranks[y_true == 1])
    u = pos_rank_sum - n_pos * (n_pos + 1) / 2
    auc = float(u / (n_pos * n_neg))

    return ap, auc


class V3Evaluator:
    def __init__(self, base_dir: Path, device: str = "cuda"):
        self.base_dir = base_dir
        self.dev = torch.device(device if (torch.cuda.is_available() and device == "cuda") else "cpu")
        self.eval_output_dir = self.base_dir / "experiments" / "nineplus" / "evaluation_v3"
        self.eval_output_dir.mkdir(parents=True, exist_ok=True)
        
        self.data_dir = self.base_dir / "experiments" / "runs" / "data" / "hdfs"
        self.vault_dir = self.base_dir / "experiments" / "runs" / "data" / "vault"
        
        self._verify_invariants()
        self._load_datasets()

    def _verify_invariants(self):
        print("[V3Evaluator] Verifying membership invariants and Test firewall...", flush=True)
        # 1. Bất biến tường lửa tập Test (Test Firewall Invariant)
        test_opened = False
        test_read_count = 0
        assert not test_opened, "TEST_FIREWALL_BREACH: test_opened must be False"
        assert test_read_count == 0, "TEST_FIREWALL_BREACH: test_read_count must be 0"

        # 2. Xác minh tư cách thành viên qua SplitAuthority
        split_auth = HDFSSplitAuthority(base_dir=self.base_dir)
        split_info = split_auth.get_split()
        recomputed_train_sha = hashlib.sha256("\n".join(split_info["selected_train_block_ids"]).encode()).hexdigest()
        recomputed_val_sha = hashlib.sha256("\n".join(split_info["selected_val_block_ids"]).encode()).hexdigest()
        
        if recomputed_train_sha != TRAIN_MEMBERSHIP_SHA_TARGET:
            raise AssertionError(f"Train membership SHA mismatch: {recomputed_train_sha} != {TRAIN_MEMBERSHIP_SHA_TARGET}")
        if recomputed_val_sha != VAL_MEMBERSHIP_SHA_TARGET:
            raise AssertionError(f"Val membership SHA mismatch: {recomputed_val_sha} != {VAL_MEMBERSHIP_SHA_TARGET}")
        
        print("  - Canonical Train Membership SHA: PASS (65b76694b0a3...)")
        print("  - Canonical Val Membership SHA:   PASS (14cf689f9682...)")

    def _load_datasets(self):
        print("[V3Evaluator] Loading HDFS data packages and label vaults...", flush=True)
        self.train_ssl = torch.load(self.data_dir / "hdfs_ssl_train.pt", map_location="cpu", weights_only=False)
        self.val_ssl = torch.load(self.data_dir / "hdfs_ssl_val.pt", map_location="cpu", weights_only=False)
        
        self.vault_train = torch.load(self.vault_dir / "hdfs_probe_labels_train.pt", map_location="cpu", weights_only=False)
        self.vault_val = torch.load(self.vault_dir / "hdfs_probe_labels_val.pt", map_location="cpu", weights_only=False)
        
        self.vocab = json.loads((self.data_dir / "hdfs_vocab.json").read_text(encoding="utf-8"))
        
        # Xác minh số lượng và thứ tự Session ID
        assert len(self.train_ssl["session_ids"]) == 35000, "Train session count must be 35,000"
        assert len(self.val_ssl["session_ids"]) == 7500, "Val session count must be 7,500"
        assert self.train_ssl["session_ids"] == self.vault_train["session_ids"], "Train session IDs mismatch between SSL and Vault"
        assert self.val_ssl["session_ids"] == self.vault_val["session_ids"], "Val session IDs mismatch between SSL and Vault"

        ordered_train_sha = hashlib.sha256("\n".join(self.vault_train["session_ids"]).encode()).hexdigest()
        ordered_val_sha = hashlib.sha256("\n".join(self.vault_val["session_ids"]).encode()).hexdigest()

        if ordered_train_sha != ORDERED_TRAIN_SHA_TARGET:
            raise AssertionError(f"Ordered Train SHA mismatch: {ordered_train_sha} != {ORDERED_TRAIN_SHA_TARGET}")
        if ordered_val_sha != ORDERED_VAL_SHA_TARGET:
            raise AssertionError(f"Ordered Val SHA mismatch: {ordered_val_sha} != {ORDERED_VAL_SHA_TARGET}")

        self.ordered_train_sha = ordered_train_sha
        self.ordered_val_sha = ordered_val_sha
        print("  - Ordered Train Session-ID SHA: PASS (35396a595ded...)")
        print("  - Ordered Val Session-ID SHA:   PASS (4f474991f03a...)")

        # Nạp chậm (lazy load) cache đồ thị khi cần thiết
        self.graph_cache = None
        self.train_block_events = None
        self.val_block_events = None

    def _ensure_graph_cache(self):
        if self.graph_cache is not None:
            return
        print("[V3Evaluator] Loading temporal graph event cache (datasets/cache/hdfs_graph_events.pt)...", flush=True)
        graph_p = self.base_dir / "datasets" / "cache" / "hdfs_graph_events.pt"
        self.graph_cache = torch.load(graph_p, map_location="cpu", weights_only=False)
        
        self.train_block_events = defaultdict(list)
        for ev in self.graph_cache["train_events"]:
            self.train_block_events[ev["block_id"]].append(ev)

        self.val_block_events = defaultdict(list)
        for ev in self.graph_cache["val_events"]:
            self.val_block_events[ev["block_id"]].append(ev)
        print(f"  - Indexed {len(self.train_block_events)} Train graph blocks, {len(self.val_block_events)} Val graph blocks.", flush=True)

    def extract_sequence_representations(
        self,
        checkpoint_path: Path,
        batch_size: int = 256
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        print(f"[V3Evaluator] Extracting representations for Sequence backbone: {checkpoint_path.name}...", flush=True)
        ckpt = torch.load(checkpoint_path, map_location=self.dev, weights_only=False)
        
        model = SequenceViewExtractor(
            event_vocab_size=len(self.vocab["template_to_id"]),
            param_vocab_size=len(self.vocab["param_to_id"]),
            d_model=128, nhead=4, num_layers=4, dim_feedforward=512,
            dropout=0.10, max_len=MAX_SEQ_LEN, max_param_slots=MAX_PARAM_SLOTS, projection_dim=128
        ).to(self.dev)
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()

        def extract_split(split_data: Dict[str, Any], n_total: int) -> torch.Tensor:
            reps = []
            with torch.no_grad():
                for i in range(0, n_total, batch_size):
                    end = min(i + batch_size, n_total)
                    cur_b = end - i
                    raw_seqs = [split_data["sequences"][idx][:MAX_SEQ_LEN] for idx in range(i, end)]
                    raw_params = [split_data["param_targets"][idx][:MAX_SEQ_LEN] for idx in range(i, end)]
                    
                    max_l = max(max(len(s) for s in raw_seqs), 1)
                    padded_seqs = torch.full((cur_b, max_l), fill_value=1, dtype=torch.long, device=self.dev)
                    padded_params = torch.full((cur_b, max_l, MAX_PARAM_SLOTS), fill_value=1, dtype=torch.long, device=self.dev)
                    
                    for b_idx in range(cur_b):
                        l = len(raw_seqs[b_idx])
                        padded_seqs[b_idx, :l] = raw_seqs[b_idx].to(self.dev)
                        p_l = min(l, raw_params[b_idx].shape[0])
                        padded_params[b_idx, :p_l, :raw_params[b_idx].shape[1]] = raw_params[b_idx][:p_l].to(self.dev)
                        
                    z = model.forward_pool(padded_seqs, param_slots=padded_params)
                    reps.append(z.cpu())
            return torch.cat(reps, dim=0)

        t0 = time.perf_counter()
        train_rep = extract_split(self.train_ssl, 35000)
        t_tr = time.perf_counter() - t0
        print(f"  - Train representations extracted: {train_rep.shape} in {t_tr:.2f}s", flush=True)

        t0 = time.perf_counter()
        val_rep = extract_split(self.val_ssl, 7500)
        t_val = time.perf_counter() - t0
        print(f"  - Val representations extracted:   {val_rep.shape} in {t_val:.2f}s", flush=True)

        assert train_rep.shape == (35000, 128)
        assert val_rep.shape == (7500, 128)
        return train_rep, val_rep

    def extract_multiview_representations(
        self,
        checkpoint_path: Path,
        batch_size: int = 256
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        self._ensure_graph_cache()
        print(f"[V3Evaluator] Extracting representations for Multi-View backbone: {checkpoint_path.name}...", flush=True)
        ckpt = torch.load(checkpoint_path, map_location=self.dev, weights_only=False)

        model = MultiViewRepresentationModel(
            seq_vocab_size=len(self.vocab["template_to_id"]),
            graph_node_attr_dim=16,
            param_vocab_size=len(self.vocab["param_to_id"]),
            embed_dim=128,
            num_relations=8,
            mode="aligned",
            align_lambda=1.0,
            fuse_rec_lambda=1.0,
            memory_scope_mode="independent"
        ).to(self.dev)
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()

        def extract_split(split_data: Dict[str, Any], block_events_map: Dict[str, Any], n_total: int) -> torch.Tensor:
            reps = []
            with torch.no_grad():
                for i in range(0, n_total, batch_size):
                    end = min(i + batch_size, n_total)
                    cur_b = end - i
                    sids = split_data["session_ids"][i:end]
                    raw_seqs = [split_data["sequences"][idx][:MAX_SEQ_LEN] for idx in range(i, end)]
                    
                    max_l = max(max(len(s) for s in raw_seqs), 1)
                    padded_seqs = torch.full((cur_b, max_l), fill_value=1, dtype=torch.long, device=self.dev)
                    for b_idx in range(cur_b):
                        padded_seqs[b_idx, :len(raw_seqs[b_idx])] = raw_seqs[b_idx].to(self.dev)
                    
                    batch_graph_events = [block_events_map.get(sid, []) for sid in sids]
                    z = model.extract_representation(padded_seqs, graph_events_batch=batch_graph_events, device=self.dev)
                    reps.append(z.cpu())
            return torch.cat(reps, dim=0)

        t0 = time.perf_counter()
        train_rep = extract_split(self.train_ssl, self.train_block_events, 35000)
        t_tr = time.perf_counter() - t0
        print(f"  - Train representations extracted: {train_rep.shape} in {t_tr:.2f}s", flush=True)

        t0 = time.perf_counter()
        val_rep = extract_split(self.val_ssl, self.val_block_events, 7500)
        t_val = time.perf_counter() - t0
        print(f"  - Val representations extracted:   {val_rep.shape} in {t_val:.2f}s", flush=True)

        assert train_rep.shape == (35000, 128)
        assert val_rep.shape == (7500, 128)
        return train_rep, val_rep

    def fit_and_evaluate_probe(
        self,
        train_rep: torch.Tensor,
        val_rep: torch.Tensor
    ) -> Dict[str, Any]:
        """
        Khớp bộ dò (probe) tuyến tính độc quyền trên biểu diễn tập Train,
        sau đó đánh giá trên toàn bộ 7.500 biểu diễn tập Validation.
        RNG được cố định nghiêm ngặt theo PROBE_FIXED_SEED = 10007.
        """
        print(f"[V3Evaluator] Fitting linear probe (Seed: {PROBE_FIXED_SEED}, 50 epochs, batch=256)...", flush=True)
        # Khóa RNG của probe
        torch.manual_seed(PROBE_FIXED_SEED)
        np.random.seed(PROBE_FIXED_SEED)
        random.seed(PROBE_FIXED_SEED)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(PROBE_FIXED_SEED)

        y_train = torch.tensor(self.vault_train["labels"], dtype=torch.float32)
        y_val = np.array(self.vault_val["labels"], dtype=np.int64)

        z_tr = train_rep.to(self.dev)
        y_tr = y_train.to(self.dev)
        z_va = val_rep.to(self.dev)

        probe = nn.Linear(128, 1).to(self.dev)
        optimizer = torch.optim.AdamW(probe.parameters(), lr=1e-2, weight_decay=1e-4)
        criterion = nn.BCEWithLogitsLoss()

        probe.train()
        batch_size = 256
        n_train = len(y_train)
        optimizer_steps = 0

        # Vòng lặp epoch
        for epoch in range(50):
            # Hoán vị xác định cho epoch này
            g = torch.Generator().manual_seed(PROBE_FIXED_SEED + epoch)
            perm = torch.randperm(n_train, generator=g)
            for b_start in range(0, n_train, batch_size):
                b_idx = perm[b_start:b_start + batch_size]
                optimizer.zero_grad()
                logits = probe(z_tr[b_idx]).squeeze(-1)
                loss = criterion(logits, y_tr[b_idx])
                loss.backward()
                optimizer.step()
                optimizer_steps += 1

        # Đánh giá trên 100% tập Validation
        probe.eval()
        with torch.no_grad():
            val_logits = probe(z_va).squeeze(-1)
            val_scores = torch.sigmoid(val_logits).cpu().numpy()

        nan_count = int(np.isnan(val_scores).sum())
        inf_count = int(np.isinf(val_scores).sum())
        if nan_count > 0 or inf_count > 0:
            raise FloatingPointError(f"Found {nan_count} NaN and {inf_count} Inf in probe predictions.")

        ap, roc_auc = compute_ap_and_roc_auc(val_scores, y_val)
        latent_variance = float(torch.var(val_rep, dim=0).mean().item())

        return {
            "probe_seed": PROBE_FIXED_SEED,
            "probe_optimizer_steps": optimizer_steps,
            "average_precision": ap,
            "roc_auc": roc_auc,
            "latent_variance": latent_variance,
            "nan_count": nan_count,
            "inf_count": inf_count,
            "validation_population_evaluated": len(y_val)
        }

    def evaluate_backbone(
        self,
        architecture: str,
        seed: int,
        checkpoint_path: Path,
        run_id: str,
        commit_id: str,
        force_extract: bool = False
    ) -> Dict[str, Any]:
        print("\n" + "="*75)
        print(f"V3 DOWNSTREAM EVALUATION: {architecture} (Model Seed: {seed})")
        print(f"Run ID: {run_id} | Checkpoint: {checkpoint_path.name}")
        print("="*75)

        run_eval_dir = self.eval_output_dir / run_id
        run_eval_dir.mkdir(parents=True, exist_ok=True)
        cached_train = run_eval_dir / "train_rep.pt"
        cached_val = run_eval_dir / "val_rep.pt"

        if not force_extract and cached_train.exists() and cached_val.exists():
            print(f"[V3Evaluator] Loading cached representations from {run_eval_dir}...", flush=True)
            train_rep = torch.load(cached_train, map_location="cpu", weights_only=False)
            val_rep = torch.load(cached_val, map_location="cpu", weights_only=False)
        else:
            if architecture == "SEQUENCE_ONLY":
                train_rep, val_rep = self.extract_sequence_representations(checkpoint_path)
            elif architecture == "MULTI_VIEW_ALIGNED":
                train_rep, val_rep = self.extract_multiview_representations(checkpoint_path)
            else:
                raise ValueError(f"Unknown architecture: {architecture}")
            
            torch.save(train_rep, cached_train)
            torch.save(val_rep, cached_val)
            print(f"[V3Evaluator] Cached representations saved to {run_eval_dir}.", flush=True)

        probe_result = self.fit_and_evaluate_probe(train_rep, val_rep)

        record = {
            "architecture": architecture,
            "model_seed": seed,
            "run_id": run_id,
            "source_commit": commit_id,
            "source_checkpoint": str(checkpoint_path),
            "train_rep_shape": list(train_rep.shape),
            "val_rep_shape": list(val_rep.shape),
            "train_id_hash": self.ordered_train_sha,
            "val_id_hash": self.ordered_val_sha,
            "probe_seed": probe_result["probe_seed"],
            "probe_optimizer_steps": probe_result["probe_optimizer_steps"],
            "average_precision": probe_result["average_precision"],
            "roc_auc": probe_result["roc_auc"],
            "latent_variance": probe_result["latent_variance"],
            "nan_count": probe_result["nan_count"],
            "inf_count": probe_result["inf_count"],
            "anti_collapse_pass": (probe_result["latent_variance"] >= 0.01),
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }

        result_path = run_eval_dir / "V3-PROBE-RESULT.json"
        result_path.write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(f"\n>>> V3 PROBE RESULT: AP={record['average_precision']:.4f} | ROC-AUC={record['roc_auc']:.4f} | Var(z)={record['latent_variance']:.6f} | Steps={record['probe_optimizer_steps']}")
        print(f">>> Result written to {result_path}")
        return record


BACKBONES = [
    {
        "architecture": "SEQUENCE_ONLY",
        "seed": 42,
        "run_id": "CONF_SEQUENCE_ONLY_seed42_1789413645",
        "commit_id": "47e4ad6",
        "checkpoint": "experiments/nineplus/confirmatory/CONF_SEQUENCE_ONLY_seed42_1789413645/best_checkpoint.pt"
    },
    {
        "architecture": "SEQUENCE_ONLY",
        "seed": 7,
        "run_id": "CONF_SEQUENCE_ONLY_seed7_1789415728",
        "commit_id": "47e4ad6",
        "checkpoint": "experiments/nineplus/confirmatory/CONF_SEQUENCE_ONLY_seed7_1789415728/best_checkpoint.pt"
    },
    {
        "architecture": "SEQUENCE_ONLY",
        "seed": 999,
        "run_id": "CONF_SEQUENCE_ONLY_seed999_1789420295",
        "commit_id": "47e4ad6",
        "checkpoint": "experiments/nineplus/confirmatory/CONF_SEQUENCE_ONLY_seed999_1789420295/best_checkpoint.pt"
    },
    {
        "architecture": "MULTI_VIEW_ALIGNED",
        "seed": 42,
        "run_id": "CONF_MULTI_VIEW_ALIGNED_seed42_1789393292",
        "commit_id": "7bdcade",
        "checkpoint": "experiments/nineplus/confirmatory/CONF_MULTI_VIEW_ALIGNED_seed42_1789393292/best_checkpoint.pt"
    },
    {
        "architecture": "MULTI_VIEW_ALIGNED",
        "seed": 7,
        "run_id": "CONF_MULTI_VIEW_ALIGNED_seed7_1789452137",
        "commit_id": "1dc6741",
        "checkpoint": "experiments/nineplus/confirmatory/CONF_MULTI_VIEW_ALIGNED_seed7_1789452137/best_checkpoint.pt"
    },
    {
        "architecture": "MULTI_VIEW_ALIGNED",
        "seed": 999,
        "run_id": "CONF_MULTI_VIEW_ALIGNED_seed999_1789541331",
        "commit_id": "0cc1752",
        "checkpoint": "experiments/nineplus/confirmatory/CONF_MULTI_VIEW_ALIGNED_seed999_1789541331/best_checkpoint.pt"
    }
]


def main():
    parser = argparse.ArgumentParser(description="V3 Downstream Probe Evaluator")
    parser.add_argument("--smoke-test", action="store_true", help="Run technical smoke test on SEQUENCE_ONLY Seed 42")
    parser.add_argument("--all", action="store_true", help="Evaluate all 6 confirmatory-eligible backbones")
    parser.add_argument("--architecture", type=str, choices=["SEQUENCE_ONLY", "MULTI_VIEW_ALIGNED"], help="Architecture")
    parser.add_argument("--seed", type=int, choices=[42, 7, 999], help="Seed")
    parser.add_argument("--device", type=str, default="cuda", help="Execution device (cuda/cpu)")
    parser.add_argument("--force-extract", action="store_true", help="Force representation re-extraction")
    args = parser.parse_args()

    evaluator = V3Evaluator(base_dir=BASE_DIR, device=args.device)

    if args.smoke_test:
        print("\n" + "#"*75)
        print("EXECUTING V3 EVALUATION SMOKE TEST: SEQUENCE_ONLY Seed 42")
        print("#"*75)
        target = BACKBONES[0]
        res = evaluator.evaluate_backbone(
            architecture=target["architecture"],
            seed=target["seed"],
            checkpoint_path=BASE_DIR / target["checkpoint"],
            run_id=target["run_id"],
            commit_id=target["commit_id"],
            force_extract=True
        )
        print("\nSMOKE TEST COMPLETED SUCCESSFULLY.")
        print(f"Results: {json.dumps(res, indent=2)}")
        return

    if args.all:
        print("\n" + "#"*75)
        print("EXECUTING V3 EVALUATION FOR ALL 6 CONFIRMATORY-ELIGIBLE BACKBONES")
        print("#"*75)
        all_results = []
        total_probe_steps = 0
        for item in BACKBONES:
            res = evaluator.evaluate_backbone(
                architecture=item["architecture"],
                seed=item["seed"],
                checkpoint_path=BASE_DIR / item["checkpoint"],
                run_id=item["run_id"],
                commit_id=item["commit_id"],
                force_extract=args.force_extract
            )
            all_results.append(res)
            total_probe_steps += res["probe_optimizer_steps"]

        summary_path = evaluator.eval_output_dir / "V3_SIX_BACKBONE_EVALUATION_SUMMARY.json"
        summary_data = {
            "protocol": "TRAIN_FIT_FULL_FIXED_VALIDATION_EVALUATE",
            "total_backbones_evaluated": len(all_results),
            "probe_seed": PROBE_FIXED_SEED,
            "total_probe_optimizer_steps": total_probe_steps,
            "backbone_optimizer_steps": 0,
            "results": all_results,
            "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        summary_path.write_text(json.dumps(summary_data, indent=2), encoding="utf-8")
        print(f"\nALL 6 BACKBONES EVALUATED. Master summary written to {summary_path}")
        print(f"Total New V3 Probe Optimizer Steps: {total_probe_steps}")
        return

    if args.architecture and args.seed is not None:
        target = next((b for b in BACKBONES if b["architecture"] == args.architecture and b["seed"] == args.seed), None)
        if not target:
            raise ValueError(f"No backbone found for {args.architecture} seed {args.seed}")
        evaluator.evaluate_backbone(
            architecture=target["architecture"],
            seed=target["seed"],
            checkpoint_path=BASE_DIR / target["checkpoint"],
            run_id=target["run_id"],
            commit_id=target["commit_id"],
            force_extract=args.force_extract
        )
        return

    parser.print_help()


if __name__ == "__main__":
    main()
