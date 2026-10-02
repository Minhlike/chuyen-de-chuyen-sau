"""Đối chiếu các số trên slide với artifact và bản Word master hiện tại."""

import hashlib
import json
import statistics
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CLAIMS = ROOT / "bao-ve" / "WORD-MASTER-CLAIMS.json"
V3 = ROOT / "experiments" / "nineplus" / "evaluation_v3"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def require_equal(name: str, actual, expected, digits: int | None = None) -> None:
    if digits is None:
        matched = actual == expected
    else:
        matched = abs(actual - expected) < 0.5 * 10 ** (-digits) + 1e-12
    if not matched:
        raise AssertionError(f"{name}: artifact={actual!r}, Word/slide={expected!r}")
    print(f"[PASS] {name}: {expected}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    claims = read_json(CLAIMS)
    require_equal("SHA-256 Word master", sha256(ROOT / "Chuyên đề chuyên sâu.docx"), claims["source_docx_sha256"])

    raw = read_json(ROOT / "datasets" / "manifests" / "SPL-HDFS-001.json")
    subset = read_json(ROOT / "datasets" / "manifests" / "SUBSET-MANIFEST-HDFS.json")
    require_equal("Số dòng HDFS", raw["verified_raw_artifacts"][0]["raw_total_line_count"], claims["data"]["raw_log_records"])
    require_equal("Số phiên HDFS", raw["verified_raw_artifacts"][1]["labeled_block_count"], claims["data"]["raw_block_sessions"])
    require_equal("Phiên Train", subset["selected_train_sessions"], claims["data"]["train_sessions"])
    require_equal("Phiên Validation", subset["selected_val_sessions"], claims["data"]["validation_sessions"])
    require_equal("Trạng thái Test", subset["test_metadata"]["test_status"], "SEALED")
    require_equal("Số mẫu Test đã phân tích", subset["test_metadata"]["test_feature_parse_count"], 0)

    summary = read_json(V3 / "V3_SIX_BACKBONE_EVALUATION_SUMMARY.json")
    require_equal("Số backbone V3", summary["total_backbones_evaluated"], 6)
    require_equal("Bước tối ưu backbone ở V3", summary["backbone_optimizer_steps"], 0)
    results = {(row["architecture"], str(row["model_seed"])): row for row in summary["results"]}
    deltas = []
    multi_aps = []
    multi_rocs = []
    for seed in ("42", "7", "999"):
        seq = results[("SEQUENCE_ONLY", seed)]
        multi = results[("MULTI_VIEW_ALIGNED", seed)]
        seq_ap = seq["average_precision"]
        multi_ap = multi["average_precision"]
        multi_roc = multi["roc_auc"]
        delta = multi_ap - seq_ap
        require_equal(f"Sequence AP seed {seed}", seq_ap, claims["v3"]["sequence_ap_by_seed"][seed], 4)
        require_equal(f"Multi-View AP seed {seed}", multi_ap, claims["v3"]["multi_view_ap_by_seed"][seed], 4)
        require_equal(f"Multi-View ROC-AUC seed {seed}", multi_roc, claims["v3"]["multi_view_roc_auc_by_seed"][seed], 4)
        require_equal(f"Độ lệch AP seed {seed}", delta, claims["h2"]["delta_ap_by_seed"][seed], 4)
        deltas.append(delta)
        multi_aps.append(multi_ap)
        multi_rocs.append(multi_roc)

    require_equal("Multi-View AP trung bình", statistics.mean(multi_aps), claims["v3"]["multi_view_mean_ap"], 4)
    require_equal("Multi-View AP độ lệch chuẩn mẫu", statistics.stdev(multi_aps), claims["v3"]["multi_view_sample_sd_ap"], 4)
    require_equal("Multi-View ROC-AUC trung bình", statistics.mean(multi_rocs), claims["v3"]["multi_view_mean_roc_auc"], 4)
    require_equal("Độ lệch AP trung bình", statistics.mean(deltas), claims["h2"]["mean_delta_ap"], 4)
    require_equal("Độ lệch AP độ lệch chuẩn mẫu", statistics.stdev(deltas), claims["h2"]["sample_sd_delta_ap"], 4)
    if not all(delta < claims["h2"]["non_inferiority_margin_ap"] for delta in deltas):
        raise AssertionError("Có cặp seed không vi phạm biên H2 như báo cáo")

    h2 = read_json(V3 / "H2_SEQUENCE_NOPARAM_SENSITIVITY.json")
    for row in h2["results"]:
        seed = str(row["model_seed"])
        require_equal(f"Sequence bỏ tham số AP seed {seed}", row["sequence_noparam_ap"], claims["h2"]["sequence_no_parameter_ap_by_seed"][seed], 4)

    h1 = read_json(V3 / "h1_ablation" / "H1_FROZEN_MASKING_ABLATION_SUMMARY.json")
    for row in h1["results"]:
        seed = str(row["model_seed"])
        require_equal(f"H1 cosine seed {seed}", row["mean_cosine_similarity"], claims["h1"]["mean_cosine_by_seed"][seed], 4)
        require_equal(f"H1 L2 seed {seed}", row["mean_l2_distance"], claims["h1"]["mean_l2_by_seed"][seed], 4)
        require_equal(f"H1 AP có tham số seed {seed}", row["ap_params_present"], claims["h1"]["ap_with_and_without_parameters"], 4)
        require_equal(f"H1 AP che tham số seed {seed}", row["ap_params_masked"], claims["h1"]["ap_with_and_without_parameters"], 4)

    print("[PASS] Các số kiểm tra khớp bản Word master và artifact hiện có.")
    print("[GIỚI HẠN] Đây là đối chiếu tĩnh; không chạy lại mô hình và không chứng minh Test chưa từng bị đọc ngoài các trạng thái được ghi.")


if __name__ == "__main__":
    main()
