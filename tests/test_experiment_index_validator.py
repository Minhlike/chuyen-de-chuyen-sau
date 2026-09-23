# -*- coding: utf-8 -*-
"""
Kiểm tra scripts/validate_experiment_index.py
Bao gồm xác minh tích cực và kiểm tra tiêu cực xác minh rằng việc giả mạo hàm băm CSV hoặc tính khả dụng không thành công.
"""

import unittest
import tempfile
import csv
from pathlib import Path
from scripts.validate_experiment_index import validate_experiment_index, validate_artifact_manifest


class TestExperimentIndexValidator(unittest.TestCase):
    def test_positive_validation(self):
        """Các tệp kho lưu trữ tiêu chuẩn phải vượt qua xác thực 100%."""
        self.assertTrue(validate_experiment_index(), "Expected standard experiment_index.csv to pass")
        self.assertTrue(validate_artifact_manifest(), "Expected standard ARTIFACT-MANIFEST.json to pass")

    def test_negative_tampered_hash_fails(self):
        """Việc giả mạo một ký tự trong manifest_sha256 phải được phát hiện và không thành công."""
        repo_root = Path(__file__).resolve().parent.parent
        original_csv = repo_root / "experiments" / "experiment_index.csv"

        with open(original_csv, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            fieldnames = reader.fieldnames
            rows = list(reader)

        # Cố ý giả mạo ký tự đầu tiên của hàng 0 manifest_sha256
        old_hash = rows[0]["manifest_sha256"]
        tampered_hash = ("0" if old_hash[0] != "0" else "1") + old_hash[1:]
        rows[0]["manifest_sha256"] = tampered_hash

        with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".csv", newline="") as tf:
            writer = csv.DictWriter(tf, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            temp_csv_path = Path(tf.name)

        try:
            # Truyền đường dẫn tương đối hoặc tuyệt đối tới trình xác thực
            rel_temp = temp_csv_path.relative_to(repo_root) if temp_csv_path.is_relative_to(repo_root) else str(temp_csv_path)
            result = validate_experiment_index(csv_path=str(temp_csv_path))
            self.assertFalse(result, "Validator should have FAILED on tampered manifest_sha256!")
        finally:
            if temp_csv_path.exists():
                temp_csv_path.unlink()


if __name__ == "__main__":
    unittest.main()
