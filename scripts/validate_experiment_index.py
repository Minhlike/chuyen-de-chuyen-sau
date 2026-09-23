# -*- coding: utf-8 -*-
"""
Trình xác thực tự động cho thử nghiệm/experiment_index.csv
Xác thực từng bản ghi CSV dựa trên các artifact JSON nguồn.
Thoát với mã 1 nếu có bất kỳ sự khác biệt nào.
"""

import os
import sys
import csv
import json
from pathlib import Path

def validate_experiment_index(csv_path: str = "experiments/experiment_index.csv") -> bool:
    repo_root = Path(__file__).resolve().parent.parent
    full_csv_path = repo_root / csv_path

    if not full_csv_path.exists():
        print(f"[VALIDATOR-FAIL] CSV not found at: {full_csv_path}")
        return False

    with open(full_csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        print("[VALIDATOR-FAIL] CSV is empty!")
        return False

    print(f"[VALIDATOR] Validating {len(rows)} records from {csv_path}...")
    errors = []

    for idx, row in enumerate(rows, 1):
        run_id = row.get("run_id", "").strip()
        arch = row.get("architecture", "").strip()
        seed_str = row.get("seed", "").strip()
        best_epoch_str = row.get("best_epoch", "").strip()
        best_loss_str = row.get("best_val_loss", "").strip()
        m_path = row.get("manifest_source_path", "").strip()
        v3_path = row.get("v3_result_artifact", "").strip()
        v3_proto = row.get("v3_probe_protocol", "").strip()
        v3_ap_str = row.get("frozen_probe_v3_ap", "").strip()
        v3_auc_str = row.get("frozen_probe_v3_roc_auc", "").strip()
        internal_proto = row.get("internal_probe_protocol", "").strip()
        internal_ap_str = row.get("internal_probe_ap", "").strip()
        internal_auc_str = row.get("internal_probe_roc_auc", "").strip()

        prefix = f"Row {idx} ({run_id}):"

        m_avail = row.get("manifest_availability", "").strip()
        csv_m_hash = row.get("manifest_sha256", "").strip()

        # 1. Sự tồn tại của tệp kê khai và xác thực SHA-256
        if m_avail not in ["AVAILABLE_IN_GIT", "LOCAL_EVIDENCE_ONLY"]:
            errors.append(f"{prefix} invalid manifest_availability: '{m_avail}'")
            continue

        full_m_path = repo_root / m_path
        if m_avail == "AVAILABLE_IN_GIT":
            try:
                import subprocess, hashlib
                git_bytes = subprocess.check_output(
                    ["git", "show", f"HEAD:{m_path}"],
                    cwd=repo_root,
                    stderr=subprocess.PIPE
                )
                computed_hash = hashlib.sha256(git_bytes).hexdigest()
                if computed_hash.lower() != csv_m_hash.lower():
                    errors.append(
                        f"{prefix} manifest_sha256 mismatch for AVAILABLE_IN_GIT: "
                        f"CSV={csv_m_hash} vs Git={computed_hash}"
                    )
            except Exception as e:
                errors.append(f"{prefix} failed to read manifest from git at {m_path}: {e}")
                continue
        elif m_avail == "LOCAL_EVIDENCE_ONLY":
            if not full_m_path.exists():
                errors.append(f"{prefix} LOCAL_EVIDENCE_ONLY manifest not found on disk at {m_path}")
                continue
            import hashlib
            data = full_m_path.read_bytes()
            computed_hash = hashlib.sha256(data).hexdigest()
            if computed_hash.lower() != csv_m_hash.lower():
                errors.append(
                    f"{prefix} manifest_sha256 mismatch for LOCAL_EVIDENCE_ONLY: "
                    f"CSV={csv_m_hash} vs Disk={computed_hash}"
                )

        if not full_m_path.exists():
            errors.append(f"{prefix} manifest not found at {m_path}")
            continue

        try:
            with open(full_m_path, "r", encoding="utf-8") as mf:
                m_data = json.load(mf)
        except Exception as e:
            errors.append(f"{prefix} failed to parse JSON in {m_path}: {e}")
            continue

        # 2. Kiểm tra họ kiến trúc
        m_arch = m_data.get("architecture", "")
        if arch == "MULTI_VIEW_ALIGNED" and m_arch not in ["MULTI_VIEW_ALIGNED", "MULTI_VIEW_ALIGNED_VICREG"]:
            errors.append(f"{prefix} architecture mismatch: CSV={arch} vs JSON={m_arch}")
        elif arch != "MULTI_VIEW_ALIGNED" and arch != m_arch:
            errors.append(f"{prefix} architecture mismatch: CSV={arch} vs JSON={m_arch}")

        # 3. Kiểm tra seed
        if int(seed_str) != int(m_data.get("seed", -1)):
            errors.append(f"{prefix} seed mismatch: CSV={seed_str} vs JSON={m_data.get('seed')}")

        # 4. Kiểm tra best_epoch
        if int(best_epoch_str) != int(m_data.get("best_epoch", -1)):
            errors.append(f"{prefix} best_epoch mismatch: CSV={best_epoch_str} vs JSON={m_data.get('best_epoch')}")

        # 5. Kiểm tra best_val_loss
        m_loss = float(m_data.get("best_val_loss", -1.0))
        csv_loss = float(best_loss_str)
        if abs(m_loss - csv_loss) > 1e-9:
            errors.append(f"{prefix} best_val_loss mismatch: CSV={csv_loss} vs JSON={m_loss}")

        # 6. Kiểm tra số liệu thăm dò nội bộ
        if "probe_ap" in m_data:
            m_iap = float(m_data["probe_ap"])
            csv_iap = float(internal_ap_str)
            if abs(m_iap - csv_iap) > 1e-9:
                errors.append(f"{prefix} internal probe_ap mismatch: CSV={csv_iap} vs JSON={m_iap}")

        if "probe_roc_auc" in m_data:
            m_iauc = float(m_data["probe_roc_auc"])
            csv_iauc = float(internal_auc_str)
            if abs(m_iauc - csv_iauc) > 1e-9:
                errors.append(f"{prefix} internal probe_roc_auc mismatch: CSV={csv_iauc} vs JSON={m_iauc}")

        # 7. Kiểm tra sự tách biệt giữa kết quả và giao thức V3
        if v3_path != "NO_V3_RESULT_ARTIFACT":
            full_v3_path = repo_root / v3_path
            if not full_v3_path.exists():
                errors.append(f"{prefix} V3 result artifact missing at {v3_path}")
                continue
            try:
                with open(full_v3_path, "r", encoding="utf-8") as vf:
                    v3_data = json.load(vf)
            except Exception as e:
                errors.append(f"{prefix} failed to parse V3 JSON in {v3_path}: {e}")
                continue

            v3_ap = float(v3_data.get("average_precision", -1.0))
            v3_auc = float(v3_data.get("roc_auc", -1.0))

            if v3_proto != "FROZEN_PROBE_V3_STANDARDIZED":
                errors.append(f"{prefix} protocol mixed: has V3 artifact but protocol is {v3_proto}")

            if abs(v3_ap - float(v3_ap_str)) > 1e-6:
                errors.append(f"{prefix} V3 AP mismatch: CSV={v3_ap_str} vs JSON={v3_ap}")

            if abs(v3_auc - float(v3_auc_str)) > 1e-6:
                errors.append(f"{prefix} V3 ROC-AUC mismatch: CSV={v3_auc_str} vs JSON={v3_auc}")
        else:
            if v3_proto != "NOT_EVALUATED_V3":
                errors.append(f"{prefix} protocol mixed: NO_V3_RESULT_ARTIFACT but protocol={v3_proto}")
            if v3_ap_str != "" or v3_auc_str != "":
                errors.append(f"{prefix} protocol mixed: NO_V3_RESULT_ARTIFACT but contains V3 metrics ({v3_ap_str}, {v3_auc_str})")

    if errors:
        print("[VALIDATOR-FAIL] Found discrepancies:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("[VALIDATOR-PASS] 100% records in experiment_index.csv match source JSON artifacts!")
    return True

def validate_artifact_manifest(manifest_path: str = "experiments/nineplus/ARTIFACT-MANIFEST.json") -> bool:
    repo_root = Path(__file__).resolve().parent.parent
    full_manifest_path = repo_root / manifest_path
    if not full_manifest_path.exists():
        print(f"[VALIDATOR-FAIL] ARTIFACT-MANIFEST not found at: {full_manifest_path}")
        return False

    with open(full_manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    clean_clone_ready = data.get("clean_clone_ready", False)
    artifacts = data.get("artifacts", [])
    print(f"[VALIDATOR] Validating {len(artifacts)} cataloged artifacts in {manifest_path}...")
    errors = []

    for art in artifacts:
        rel_path = art.get("relative_path", "")
        avail = art.get("availability", "")
        exp_size = art.get("size_bytes")
        exp_sha = art.get("sha256")
        target_file = repo_root / rel_path

        if avail == "AVAILABLE_IN_GIT":
            try:
                import subprocess, hashlib
                git_bytes = subprocess.check_output(
                    ["git", "show", f"HEAD:{rel_path}"],
                    cwd=repo_root,
                    stderr=subprocess.PIPE
                )
                actual_size = len(git_bytes)
                actual_sha = hashlib.sha256(git_bytes).hexdigest()
                if actual_size != exp_size:
                    errors.append(f"{rel_path} git size mismatch: exp={exp_size} vs actual={actual_size}")
                if actual_sha.lower() != str(exp_sha).lower():
                    errors.append(f"{rel_path} git sha mismatch: exp={exp_sha} vs actual={actual_sha}")
            except Exception as e:
                errors.append(f"{rel_path} failed to read from git: {e}")
        elif avail == "LOCAL_ONLY":
            if not target_file.exists():
                if not clean_clone_ready:
                    print(f"[VALIDATOR-NOTICE] {rel_path} is LOCAL_ONLY and pending provisioning (clean_clone_ready=false)")
                    continue
                errors.append(f"{rel_path} marked LOCAL_ONLY but does not exist on disk (must be UNVERIFIED_LOCAL_ONLY)")
            else:
                import hashlib
                raw_bytes = target_file.read_bytes()
                actual_size = len(raw_bytes)
                actual_sha = hashlib.sha256(raw_bytes).hexdigest()
                if actual_size != exp_size:
                    errors.append(f"{rel_path} disk size mismatch: exp={exp_size} vs actual={actual_size}")
                if actual_sha.lower() != str(exp_sha).lower():
                    errors.append(f"{rel_path} disk sha mismatch: exp={exp_sha} vs actual={actual_sha}")
        elif avail == "UNVERIFIED_LOCAL_ONLY":
            if exp_size is not None or exp_sha is not None:
                errors.append(f"{rel_path} marked UNVERIFIED_LOCAL_ONLY but size/sha are not null")
        else:
            errors.append(f"{rel_path} unknown availability: {avail}")

    if errors:
        print("[VALIDATOR-FAIL] ARTIFACT-MANIFEST discrepancies:")
        for err in errors:
            print(f"  - {err}")
        return False

    print("[VALIDATOR-PASS] 100% artifacts in ARTIFACT-MANIFEST.json verified!")
    return True

if __name__ == "__main__":
    v1 = validate_experiment_index()
    v2 = validate_artifact_manifest()
    if not (v1 and v2):
        sys.exit(1)
    sys.exit(0)
