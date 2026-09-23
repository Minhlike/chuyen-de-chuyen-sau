#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
pipeline loại trừ mặt nạ (masking ablation) đầu vào đóng băng (frozen) H1
Giao thức: FROZEN_INPUT_MASKING_ABLATION

Đánh giá các backbone SEQUENCE_ONLY được đóng băng (frozen) giống hệt nhau (Seed 42, 7, 999)
với thông số đầu vào PRESENT (param_slots=params) so với MASKED (param_slots=None).

Suy luận được phép:
Các khe tham số động đóng góp thông tin được sử dụng bởi biểu diễn cố định đã học.

Cấm suy luận:
Huấn luyện nhận biết tham số được chứng minh là vượt trội so với mô hình chỉ có mẫu được huấn luyện riêng biệt.
"""

import json
import time
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import torch
import torch.nn.functional as F

import sys
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR / "src") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "src"))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from research_agent.experiments.extractor.sequence_view import SequenceViewExtractor
from scripts.evaluate_nineplus_v3 import compute_ap_and_roc_auc, MAX_SEQ_LEN

OUTPUT_DIR = BASE_DIR / "experiments" / "nineplus" / "evaluation_v3" / "h1_ablation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 7, 999]
RUNS = {
    42: "CONF_SEQUENCE_ONLY_seed42_1789413645",
    7: "CONF_SEQUENCE_ONLY_seed7_1789415728",
    999: "CONF_SEQUENCE_ONLY_seed999_1789420295"
}


def run_ablation():
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = BASE_DIR / "experiments" / "runs" / "data" / "hdfs"
    vault_dir = BASE_DIR / "experiments" / "runs" / "data" / "vault"

    val_ssl = torch.load(data_dir / "hdfs_ssl_val.pt", map_location="cpu", weights_only=False)
    vault_val = torch.load(vault_dir / "hdfs_probe_labels_val.pt", map_location="cpu", weights_only=False)
    vocab = json.loads((data_dir / "hdfs_vocab.json").read_text(encoding="utf-8"))
    y_val = np.array(vault_val["labels"], dtype=np.int64)

    results = []
    batch_size = 256
    n_total = 7500

    print("="*75)
    print("H1 FROZEN INPUT MASKING ABLATION (SEEDS 42, 7, 999)")
    print("="*75)

    for seed in SEEDS:
        run_id = RUNS[seed]
        ckpt_p = BASE_DIR / "experiments" / "nineplus" / "confirmatory" / run_id / "best_checkpoint.pt"
        ckpt = torch.load(ckpt_p, map_location=dev, weights_only=False)

        model = SequenceViewExtractor(
            event_vocab_size=len(vocab["template_to_id"]),
            param_vocab_size=len(vocab["param_to_id"]),
            d_model=128, nhead=4, num_layers=4, dim_feedforward=512,
            dropout=0.10, max_len=MAX_SEQ_LEN, max_param_slots=4, projection_dim=128
        ).to(dev)
        model.load_state_dict(ckpt["model_state_dict"])
        model.eval()

        # 1. Tải biểu diễn không được che giấu được lưu trong bộ nhớ đệm (từ đánh giá V3)
        cached_val = BASE_DIR / "experiments" / "nineplus" / "evaluation_v3" / run_id / "val_rep.pt"
        z_present = torch.load(cached_val, map_location="cpu", weights_only=False)

        # 2. Trích xuất biểu diễn bị che (param_slots=None)
        reps_masked = []
        with torch.no_grad():
            for i in range(0, n_total, batch_size):
                end = min(i + batch_size, n_total)
                cur_b = end - i
                raw_seqs = [val_ssl["sequences"][idx][:MAX_SEQ_LEN] for idx in range(i, end)]
                max_l = max(max(len(s) for s in raw_seqs), 1)
                padded_seqs = torch.full((cur_b, max_l), fill_value=1, dtype=torch.long, device=dev)
                for b_idx in range(cur_b):
                    padded_seqs[b_idx, :len(raw_seqs[b_idx])] = raw_seqs[b_idx].to(dev)
                z_m = model.forward_pool(padded_seqs, param_slots=None)
                reps_masked.append(z_m.cpu())
        z_masked = torch.cat(reps_masked, dim=0)

        # Tính độ tương tự cosin và khoảng cách L2 giữa biểu diễn hiện tại và biểu diễn bị che
        cos_sim = F.cosine_similarity(z_present, z_masked, dim=-1)
        mean_cos_sim = float(cos_sim.mean().item())
        min_cos_sim = float(cos_sim.min().item())
        l2_dist = torch.norm(z_present - z_masked, dim=-1)
        mean_l2_dist = float(l2_dist.mean().item())

        # 3. Đánh giá hạ nguồn (downstream) của thăm dò đã được huấn luyện trên các biểu diễn bị che
        # probe được nạp được huấn luyện về biểu diễn Train với seed 10007
        train_rep_p = BASE_DIR / "experiments" / "nineplus" / "evaluation_v3" / run_id / "train_rep.pt"
        train_rep = torch.load(train_rep_p, map_location=dev, weights_only=False)
        y_train = torch.tensor(torch.load(vault_dir / "hdfs_probe_labels_train.pt", weights_only=False)["labels"], dtype=torch.float32, device=dev)

        torch.manual_seed(10007)
        probe = torch.nn.Linear(128, 1).to(dev)
        opt = torch.optim.AdamW(probe.parameters(), lr=1e-2, weight_decay=1e-4)
        crit = torch.nn.BCEWithLogitsLoss()
        probe.train()
        for ep in range(50):
            g = torch.Generator().manual_seed(10007 + ep)
            perm = torch.randperm(35000, generator=g)
            for b in range(0, 35000, 256):
                idx = perm[b:b+256]
                opt.zero_grad()
                logits = probe(train_rep[idx]).squeeze(-1)
                loss = crit(logits, y_train[idx])
                loss.backward()
                opt.step()

        probe.eval()
        with torch.no_grad():
            scores_present = torch.sigmoid(probe(z_present.to(dev)).squeeze(-1)).cpu().numpy()
            scores_masked = torch.sigmoid(probe(z_masked.to(dev)).squeeze(-1)).cpu().numpy()

        ap_pres, roc_pres = compute_ap_and_roc_auc(scores_present, y_val)
        ap_mask, roc_mask = compute_ap_and_roc_auc(scores_masked, y_val)

        record = {
            "model_seed": seed,
            "run_id": run_id,
            "mean_cosine_similarity": mean_cos_sim,
            "min_cosine_similarity": min_cos_sim,
            "mean_l2_distance": mean_l2_dist,
            "ap_params_present": ap_pres,
            "ap_params_masked": ap_mask,
            "delta_ap_masking": ap_mask - ap_pres,
            "roc_params_present": roc_pres,
            "roc_params_masked": roc_mask,
            "delta_roc_masking": roc_mask - roc_pres,
            "semantic_contribution_detected": (mean_cos_sim < 0.9999 or mean_l2_dist > 1e-4)
        }
        results.append(record)
        print(f"Seed {seed:3d} | CosSim: {mean_cos_sim:.4f} | L2Dist: {mean_l2_dist:.4f} | AP Pres: {ap_pres:.4f} -> Mask: {ap_mask:.4f} (Delta: {record['delta_ap_masking']:+.4f})")

    summary_file = OUTPUT_DIR / "H1_FROZEN_MASKING_ABLATION_SUMMARY.json"
    summary_file.write_text(json.dumps({
        "protocol": "FROZEN_INPUT_MASKING_ABLATION",
        "allowed_inference": "Dynamic parameter slots contribute information used by the learned frozen representation.",
        "forbidden_inference": "Parameter-aware training is proven superior to a separately trained template-only model.",
        "results": results,
        "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }, indent=2), encoding="utf-8")
    print(f"\nAblation summary written to {summary_file}")


if __name__ == "__main__":
    run_ablation()
