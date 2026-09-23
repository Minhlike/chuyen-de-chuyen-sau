# -*- coding: utf-8 -*-
"""
Kiểm tra đơn vị cho compute_ap_and_roc_auc
Xác minh việc xử lý ràng buộc, xếp hạng hoàn hảo/đảo ngược và từ chối một lớp.
"""

import os
import sys
import unittest
import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

# Đảm bảo thư mục scripts có trên sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.run_nineplus_confirmatory import compute_ap_and_roc_auc

class TestRocAucMetrics(unittest.TestCase):

    def test_perfect_ranking(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        scores = np.array([0.1, 0.2, 0.3, 0.7, 0.8, 0.9])
        ap, auc = compute_ap_and_roc_auc(scores, y_true)

        sk_ap = average_precision_score(y_true, scores)
        sk_auc = roc_auc_score(y_true, scores)

        self.assertAlmostEqual(ap, 1.0, places=7)
        self.assertAlmostEqual(auc, 1.0, places=7)
        self.assertAlmostEqual(ap, sk_ap, places=7)
        self.assertAlmostEqual(auc, sk_auc, places=7)

    def test_reversed_ranking(self):
        y_true = np.array([0, 0, 0, 1, 1, 1])
        scores = np.array([0.9, 0.8, 0.7, 0.3, 0.2, 0.1])
        ap, auc = compute_ap_and_roc_auc(scores, y_true)

        sk_ap = average_precision_score(y_true, scores)
        sk_auc = roc_auc_score(y_true, scores)

        self.assertAlmostEqual(auc, 0.0, places=7)
        self.assertAlmostEqual(ap, sk_ap, places=7)
        self.assertAlmostEqual(auc, sk_auc, places=7)

    def test_tied_scores(self):
        # Trường hợp 1: Điểm hòa 4 mẫu đơn giản
        y_true1 = np.array([0, 0, 1, 1])
        scores1 = np.array([0.2, 0.5, 0.5, 0.8])
        ap1, auc1 = compute_ap_and_roc_auc(scores1, y_true1)

        sk_ap1 = average_precision_score(y_true1, scores1)
        sk_auc1 = roc_auc_score(y_true1, scores1)

        self.assertAlmostEqual(ap1, sk_ap1, places=7, msg="AP mismatch on tied scores case 1")
        self.assertAlmostEqual(auc1, sk_auc1, places=7, msg="ROC-AUC mismatch on tied scores case 1")
        self.assertAlmostEqual(auc1, 0.875, places=4)

        # Trường hợp 2: Mảng rời rạc nhiều nhánh
        y_true2 = np.array([0, 1, 0, 1, 0, 1, 0, 1])
        scores2 = np.array([0.1, 0.1, 0.4, 0.4, 0.4, 0.7, 0.7, 0.9])
        ap2, auc2 = compute_ap_and_roc_auc(scores2, y_true2)

        sk_ap2 = average_precision_score(y_true2, scores2)
        sk_auc2 = roc_auc_score(y_true2, scores2)

        self.assertAlmostEqual(ap2, sk_ap2, places=7, msg="AP mismatch on tied scores case 2")
        self.assertAlmostEqual(auc2, sk_auc2, places=7, msg="ROC-AUC mismatch on tied scores case 2")

    def test_single_class_rejection(self):
        # Tất cả số không
        with self.assertRaises(ValueError):
            compute_ap_and_roc_auc(np.array([0.1, 0.5, 0.9]), np.array([0, 0, 0]))

        # Tất cả những cái đó
        with self.assertRaises(ValueError):
            compute_ap_and_roc_auc(np.array([0.1, 0.5, 0.9]), np.array([1, 1, 1]))

        # Ba lớp
        with self.assertRaises(ValueError):
            compute_ap_and_roc_auc(np.array([0.1, 0.5, 0.9]), np.array([0, 1, 2]))

if __name__ == "__main__":
    unittest.main()
