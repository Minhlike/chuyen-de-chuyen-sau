#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quy trình đánh giá độ nhạy không có thông số trình tự H2
Giao diện: H2_SEQUENCE_NOPARAM_SENSITIVITY

Kiểm tra xem lợi thế về hiệu suất của SEQUENCE_ONLY so với MULTI_VIEW
là một artifact của các đầu vào tham số rõ ràng trong Trình tự so với tham số ẩn
xử lý trong MultiViewRepresentationModel.extract_representation().

Giao thức:
Đối với seed trình tự [42, 7, 999]:
1. Trích xuất ALL 35.000 Huấn luyện biểu diễn với param_slots=None.
2. Trích xuất ALL 7.500 biểu diễn xác thực với param_slots=None.
3. Lắp bộ dò (probe) tuyến tính NEW trên biểu diễn MASKED TRAIN (Seed 10007, 50 epoch, AdamW lr=1e-2, wd=1e-4, batch 256).
4. Đánh giá các biểu diễn MASKED VALIDATION.
5. Tính toán các delta được ghép nối với MULTI_VIEW_ALIGNED.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import torch
import torch.nn as nn

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR / "src") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "src"))
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from research_agent.experiments.extractor.sequence_view import SequenceViewExtractor
from scripts.evaluate_nineplus_v3 import compute_ap_and_roc_auc, MAX_SEQ_LEN

OUTPUT_DIR = BASE_DIR / "experiments" / "nineplus" / "evaluation_v3"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SEEDS = [42, 7, 999]
SEQUENCE_RUNS = {
    42: "CONF_SEQUENCE_ONLY_seed42_1789413645",
    7: "CONF_SEQUENCE_ONLY_seed7_1789415728",
    999: "CONF_SEQUENCE_ONLY_seed999_1789420295"
}

# Tải kết quả V3 MULTI_VIEW đã được tính toán để so sánh phù hợp
V3_SUMMARY_P = OUTPUT_DIR / "V3_SIX_BACKBONE_EVALUATION_SUMMARY.json"
v3_summary = json.loads(V3_SUMMARY_P.read_text(encoding="utf-8"))
mv_results = {r["model_seed"]: r for r in v3_summary["results"] if r["architecture"] == "MULTI_VIEW_ALIGNED"}


def run_sequence_noparam_sensitivity():
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    data_dir = BASE_DIR / "experiments" / "runs" / "data" / "hdfs"
    vault_dir = BASE_DIR / "experiments" / "runs" / "data" / "vault"

    print("="*75)
    print("H2 SEQUENCE NO-PARAM SENSITIVITY CHECK (SEEDS 42, 7, 999)")
    print("="*75)

    train_ssl = torch.load(data_dir / "hdfs_ssl_train.pt", map_location="cpu", weights_only=False)
    val_ssl = torch.load(data_dir / "hdfs_ssl_val.pt", map_location="cpu", weights_only=False)
    vault_train = torch.load(vault_dir / "hdfs_probe_labels_train.pt", map_location="cpu", weights_only=False)
    vault_val = torch.load(vault_dir / "hdfs_probe_labels_val.pt", map_location="cpu", weights_only=False)
    vocab = json.loads((data_dir / "hdfs_vocab.json").read_text(encoding="utf-8"))

    y_train = torch.tensor(vault_train["labels"], dtype=torch.float32, device=dev)
    y_val = np.array(vault_val["labels"], dtype=np.int64)

    batch_size = 256
    results = []
    total_probe_steps = 0

    def extract_noparam(model: nn.Module, split_data: Dict[str, Any], n_total: int) -> torch.Tensor:
        reps = []
        with torch.no_grad():
            for i in range(0, n_total, batch_size):
                end = min(i + batch_size, n_total)
                cur_b = end - i
                raw_seqs = [split_data["sequences"][idx][:MAX_SEQ_LEN] for idx in range(i, end)]
                max_l = max(max(len(s) for s in raw_seqs), 1)
                padded_seqs = torch.full((cur_b, max_l), fill_value=1, dtype=torch.long, device=dev)
                for b_idx in range(cur_b):
                    padded_seqs[b_idx, :len(raw_seqs[b_idx])] = raw_seqs[b_idx].to(dev)
                z = model.forward_pool(padded_seqs, param_slots=None)
                reps.append(z.cpu())
        return torch.cat(reps, dim=0)

    for seed in SEEDS:
        run_id = SEQUENCE_RUNS[seed]
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

        print(f"\n[Seed {seed}] Extracting Train representations with param_slots=None...", flush=True)
        t0 = time.perf_counter()
        train_rep = extract_noparam(model, train_ssl, 35000)
        t_tr = time.perf_counter() - t0
        print(f"  - Train extracted: {train_rep.shape} in {t_tr:.2f}s", flush=True)

        print(f"[Seed {seed}] Extracting Val representations with param_slots=None...", flush=True)
        t0 = time.perf_counter()
        val_rep = extract_noparam(model, val_ssl, 7500)
        t_va = time.perf_counter() - t0
        print(f"  - Val extracted:   {val_rep.shape} in {t_va:.2f}s", flush=True)

        # Huấn luyện probe tuyến tính trên các biểu diễn Train đeo mặt nạ độc quyền
        print(f"[Seed {seed}] Fitting linear probe on MASKED Train representations (Seed 10007)...", flush=True)
        torch.manual_seed(10007)
        np.random.seed(10007)
        probe = nn.Linear(128, 1).to(dev)
        opt = torch.optim.AdamW(probe.parameters(), lr=1e-2, weight_decay=1e-4)
        crit = nn.BCEWithLogitsLoss()

        z_tr = train_rep.to(dev)
        z_va = val_rep.to(dev)

        probe.train()
        probe_steps = 0
        for ep in range(50):
            g = torch.Generator().manual_seed(10007 + ep)
            perm = torch.randperm(35000, generator=g)
            for b in range(0, 35000, 256):
                idx = perm[b:b+256]
                opt.zero_grad()
                logits = probe(z_tr[idx]).squeeze(-1)
                loss = crit(logits, y_train[idx])
                loss.backward()
                opt.step()
                probe_steps += 1

        total_probe_steps += probe_steps

        # Đánh giá các biểu diễn xác thực MASKED
        probe.eval()
        with torch.no_grad():
            val_logits = probe(z_va).squeeze(-1)
            val_scores = torch.sigmoid(val_logits).cpu().numpy()

        ap_noparam, roc_noparam = compute_ap_and_roc_auc(val_scores, y_val)
        var_z_noparam = float(torch.var(val_rep, dim=0).mean().item())

        mv_seed_res = mv_results[seed]
        mv_ap = mv_seed_res["average_precision"]
        mv_roc = mv_seed_res["roc_auc"]
        delta_ap = mv_ap - ap_noparam
        delta_roc = mv_roc - roc_noparam

        rec = {
            "model_seed": seed,
            "sequence_run_id": run_id,
            "sequence_noparam_ap": ap_noparam,
            "sequence_noparam_roc_auc": roc_noparam,
            "sequence_noparam_latent_variance": var_z_noparam,
            "matched_multiview_ap": mv_ap,
            "matched_multiview_roc_auc": mv_roc,
            "delta_ap_mv_vs_seq_noparam": delta_ap,
            "delta_roc_mv_vs_seq_noparam": delta_roc,
            "probe_optimizer_steps": probe_steps,
            "non_inferiority_satisfied": (delta_ap >= -0.02)
        }
        results.append(rec)
        print(f">>> Seed {seed} Seq(No-Param): AP={ap_noparam:.4f} | ROC={roc_noparam:.4f} | Var={var_z_noparam:.6f}")
        print(f"    vs MultiView: AP={mv_ap:.4f} | Delta_AP={delta_ap:+.4f} (Margin >= -0.02: {rec['non_inferiority_satisfied']})")

    all_delta_aps = [r["delta_ap_mv_vs_seq_noparam"] for r in results]
    mean_delta_ap = float(np.mean(all_delta_aps))
    std_delta_ap = float(np.std(all_delta_aps, ddof=1))
    all_violate = all(d < -0.02 for d in all_delta_aps)

    summary = {
        "analysis": "H2_SEQUENCE_NOPARAM_SENSITIVITY",
        "description": "Evaluates SEQUENCE_ONLY without parameter slots (param_slots=None) for both Train representation probe fitting and Validation evaluation, comparing against MULTI_VIEW_ALIGNED.",
        "results": results,
        "total_new_probe_optimizer_steps": total_probe_steps,
        "backbone_optimizer_steps": 0,
        "mean_delta_ap": mean_delta_ap,
        "std_delta_ap": std_delta_ap,
        "h2_negative_result_robust_to_sequence_parameter_input_removal": all_violate,
        "completed_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

    out_file = OUTPUT_DIR / "H2_SEQUENCE_NOPARAM_SENSITIVITY.json"
    out_file.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nSensitivity summary written to {out_file}")
    print(f"Mean Delta AP (MV vs Seq-NoParam): {mean_delta_ap:+.4f} +/- {std_delta_ap:.4f}")
    print(f"H2_NEGATIVE_RESULT_ROBUST_TO_SEQUENCE_PARAMETER_INPUT_REMOVAL: {all_violate}")
    return summary


if __name__ == "__main__":
    run_sequence_noparam_sensitivity()
