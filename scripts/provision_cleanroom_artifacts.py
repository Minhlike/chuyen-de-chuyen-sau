# -*- coding: utf-8 -*-
"""
Artifact Provisioning Script for Reviewer Clean-Room Verification
Tự động sao chép và xác thực các artifact ngoại vi từ kho lưu trữ/máy chủ vào bản clone sạch.
Đối soát kích thước và mã băm SHA-256 đối chiếu nghiêm ngặt với experiments/nineplus/ARTIFACT-MANIFEST.json.
Xuất báo cáo kết quả tại evidence/ARTIFACT_PROVISIONING_REPORT.json.
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime, timezone

REPO_ROOT = Path(__file__).resolve().parent.parent

def compute_sha256(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(1024 * 1024):
            h.update(chunk)
    return h.hexdigest()

def provision_artifacts(source_dir: str):
    source_root = Path(source_dir).resolve()
    manifest_path = REPO_ROOT / "experiments" / "nineplus" / "ARTIFACT-MANIFEST.json"
    
    if not manifest_path.exists():
        print(f"[FAIL] Manifest not found: {manifest_path}")
        sys.exit(1)
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    artifacts_to_provision = [
        "experiments/runs/data/hdfs/hdfs_ssl_train.pt",
        "experiments/runs/data/hdfs/hdfs_ssl_val.pt",
        "experiments/runs/data/hdfs/hdfs_vocab.json",
        "experiments/runs/data/hdfs/hdfs_split_authority_cache.json",
        "experiments/runs/data/vault/hdfs_probe_labels_train.pt",
        "experiments/runs/data/vault/hdfs_probe_labels_val.pt",
        "experiments/nineplus/confirmatory/CONF_SEQUENCE_ONLY_seed42_1789413645/best_checkpoint.pt"
    ]
    
    manifest_lookup = {item["relative_path"]: item for item in manifest.get("artifacts", [])}
    
    results = []
    all_passed = True
    
    print("=" * 80)
    print("  ARTIFACT PROVISIONING & CRYPTOGRAPHIC VERIFICATION")
    print("=" * 80)
    print(f"Destination Root: {REPO_ROOT}")
    print(f"Source Store:     {source_root}")
    print("-" * 80)
    
    for rel_path in artifacts_to_provision:
        dest_file = REPO_ROOT / rel_path
        src_file = source_root / rel_path
        meta = manifest_lookup.get(rel_path, {})
        expected_sha = meta.get("sha256")
        expected_size = meta.get("size_bytes")
        
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        
        if not src_file.exists():
            print(f"[FAIL] Source file missing: {src_file}")
            results.append({
                "relative_path": rel_path,
                "status": "SOURCE_MISSING",
                "source_path": str(src_file)
            })
            all_passed = False
            continue
            
        # Copy file
        shutil.copy2(src_file, dest_file)
        
        # Verify
        actual_size = dest_file.stat().st_size
        actual_sha = compute_sha256(dest_file)
        
        size_match = (actual_size == expected_size)
        sha_match = (actual_sha.lower() == expected_sha.lower())
        passed = size_match and sha_match
        
        if not passed:
            all_passed = False
            status = "MISMATCH"
        else:
            status = "VERIFIED_PASS"
            
        print(f"[{status}] {rel_path}")
        print(f"  Size: expected {expected_size} | actual {actual_size} ({'OK' if size_match else 'FAIL'})")
        print(f"  SHA:  expected {expected_sha}")
        print(f"        actual   {actual_sha} ({'OK' if sha_match else 'FAIL'})")
        
        results.append({
            "relative_path": rel_path,
            "status": status,
            "expected_size_bytes": expected_size,
            "actual_size_bytes": actual_size,
            "size_match": size_match,
            "expected_sha256": expected_sha,
            "actual_sha256": actual_sha,
            "sha256_match": sha_match
        })
        
    print("=" * 80)
    if all_passed:
        print(f"[PASS] All {len(artifacts_to_provision)} external artifacts successfully provisioned and verified.")
    else:
        print("[FAIL] Some artifacts failed verification.")
    print("=" * 80)
    
    report = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "cleanroom_root": str(REPO_ROOT),
        "source_storage": str(source_root),
        "total_provisioned": len(artifacts_to_provision),
        "all_passed": all_passed,
        "artifacts": results
    }
    
    out_path = REPO_ROOT / "evidence" / "ARTIFACT_PROVISIONING_REPORT.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
        
    print(f"Report written to: {out_path}")
    if not all_passed:
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python provision_cleanroom_artifacts.py <source_dir>")
        sys.exit(1)
    provision_artifacts(sys.argv[1])
