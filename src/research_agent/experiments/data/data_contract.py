# -*- coding: utf-8 -*-
"""
Mô-đun xác thực tính toàn vẹn và hợp đồng dữ liệu
Thực thi các bất biến khoa học nghiêm ngặt đối với việc hiện thực hóa dữ liệu thực của Chương 3:
  - Bảo vệ chống lại các proxy tổng hợp trong quy trình huấn luyện thực tế (RealTrainingDataViolation).
  - Bảo vệ không đóng chống rò rỉ nhãn hạ nguồn (downstream) trong quá trình huấn luyện trước tự giám sát (LabelLeakageError).
  - Theo dõi rõ ràng việc phân loại dữ liệu, xuất xứ nguồn, phù hợp từ vựng và Con dấu kiểm tra.
  - Xây dựng các bảng kê khai REAL-DATA-CONTRACT chuẩn cho bộ dữ liệu HDFS và BGL.
"""

import json
import hashlib
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Set

class RealTrainingDataViolation(Exception):
    """Xảy ra khi quy trình huấn luyện thực gặp phải proxy khói tổng hợp hoặc dữ liệu phân tách không hợp lệ."""
    __test__ = False

class LabelLeakageError(Exception):
    """Xảy ra khi gói tiền huấn luyện (pretraining) Giai đoạn A1 tự giám sát có chứa nhãn giám sát hạ nguồn (downstream)."""
    __test__ = False

def enforce_real_training_data_purity(dataset_classification: str, record_metadata: Optional[Dict[str, Any]] = None):
    """
    Đảm bảo rằng các pipeline huấn luyện thực sự không thể đóng lại nếu được cung cấp proxy khói hoặc thiết bị kết hợp.
    """
    forbidden_classes = ["SYNTHETIC_PROXY", "SYNTHETIC_SMOKE_ONLY", "HYBRID_SMOKE_FIXTURE"]
    if dataset_classification.upper() in forbidden_classes:
        raise RealTrainingDataViolation(
            f"RealTrainingDataViolation: Data classification '{dataset_classification}' is prohibited in real training. "
            f"Only REAL_TRAINING_MATERIALIZED is permitted."
        )
    if record_metadata:
        for k in ["parameter_source", "temporal_source", "graph_source"]:
            val = str(record_metadata.get(k, "")).upper()
            if "SYNTHETIC" in val:
                raise RealTrainingDataViolation(
                    f"RealTrainingDataViolation: Field '{k}' contains '{val}'. Synthetic proxies are forbidden in real training."
                )

def enforce_ssl_package_label_free(package_dict: Dict[str, Any]):
    """
    Đảm bảo rằng các gói tiền huấn luyện (pretraining) tự giám sát Giai đoạn A1 hoàn toàn không có nhãn phía sau.
    """
    forbidden_label_keys = [
        "labels", "label", "anomaly", "anomalies", "alert", "alerts",
        "is_alert", "attack", "attack_class", "downstream_labels", "target_labels"
    ]
    found_keys = [k for k in forbidden_label_keys if k in package_dict]
    if found_keys:
        raise LabelLeakageError(
            f"LabelLeakageError: Self-supervised pretraining package contains prohibited label fields {found_keys}. "
            f"Stage A1 pretraining must be strictly label-free. Labels must reside in evaluation vaults only."
        )

@dataclass
class RealDataContract:
    dataset_id: str
    dataset_name: str
    dataset_tier: str
    raw_artifact_sha256: str
    parser_version_hash: str
    source_record_count: int
    valid_record_count: int
    malformed_count: int
    event_time_coverage: float
    template_vocabulary_size: int
    dynamic_parameter_types: List[str]
    excluded_shortcut_fields: List[str]
    train_hash: str
    validation_hash: str
    test_status: str = "SEALED"
    synthetic_proxy_count: int = 0
    data_classification: str = "REAL_TRAINING_MATERIALIZED"
    reference_record_count: Optional[int] = None
    observed_local_record_count: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def write_manifest(self, output_path: Path):
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)
