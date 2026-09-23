# -*- coding: utf-8 -*-
"""
Kiểm tra tích hợp cho evaluate_downstream_linear_probe trong scripts/run_nineplus_confirmatory.py.
Xác minh rằng việc đánh giá thăm dò trả về một từ điển hợp lệ với probe_ap và probe_roc_auc hữu hạn trong [0, 1].
Cụ thể nắm bắt hồi quy trong đó evaluate_downstream_linear_probe kết thúc mà không trả về từ điển (trả về Không).
"""

import math
import unittest
import torch
from scripts.run_nineplus_confirmatory import evaluate_downstream_linear_probe


class TestLinearProbeIntegration(unittest.TestCase):
    def test_evaluate_downstream_linear_probe_returns_valid_metrics(self):
        # Tạo một tập dữ liệu tổng hợp nhỏ trên CPU: 100 mẫu, dim 128
        torch.manual_seed(42)
        n_samples = 100
        z_dim = 128
        z_all = torch.randn(n_samples, z_dim, dtype=torch.float32)

        # Nhãn có cả lớp dương và âm (e.g. 20 dương, 80 âm)
        labels = [1] * 20 + [0] * 80

        # Gọi evaluate_downstream_linear_probe trên CPU
        metrics = evaluate_downstream_linear_probe(
            z_all=z_all,
            labels=labels,
            seed=42,
            device="cpu"
        )

        # 1. Khẳng định hồi quy: Không được là None
        self.assertIsNotNone(metrics, "Regression detected: evaluate_downstream_linear_probe returned None!")

        # 2. Phải trả lại một lệnh
        self.assertIsInstance(metrics, dict, "Expected evaluate_downstream_linear_probe to return a dict")

        # 3. Phải chứa các khóa cần thiết
        self.assertIn("probe_ap", metrics, "Missing 'probe_ap' in returned metrics dict")
        self.assertIn("probe_roc_auc", metrics, "Missing 'probe_roc_auc' in returned metrics dict")

        ap = metrics["probe_ap"]
        auc = metrics["probe_roc_auc"]

        # 4. Các giá trị phải hữu hạn và nằm trong [0,0, 1,0]
        self.assertTrue(math.isfinite(ap), f"probe_ap is not finite: {ap}")
        self.assertTrue(math.isfinite(auc), f"probe_roc_auc is not finite: {auc}")
        self.assertGreaterEqual(ap, 0.0, f"probe_ap out of bounds: {ap}")
        self.assertLessEqual(ap, 1.0, f"probe_ap out of bounds: {ap}")
        self.assertGreaterEqual(auc, 0.0, f"probe_roc_auc out of bounds: {auc}")
        self.assertLessEqual(auc, 1.0, f"probe_roc_auc out of bounds: {auc}")

    def test_regression_guard_catches_none(self):
        """Xác minh cụ thể rằng việc trả về Không gây ra lỗi xác nhận hồi quy."""
        broken_output = None
        with self.assertRaises(AssertionError) as ctx:
            self.assertIsNotNone(broken_output, "Regression detected: evaluate_downstream_linear_probe returned None!")
        self.assertIn("Regression detected: evaluate_downstream_linear_probe returned None!", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
