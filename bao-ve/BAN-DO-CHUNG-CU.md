# Bản đồ chứng cứ khi mở VS Code

Mở `D:\chuyen-de-chuyen-sau` trong VS Code. Bản Word master là nguồn diễn giải khoa học; mã nguồn và JSON/CSV là chứng cứ cho phần thực nghiệm. Không dùng README để thay cho việc chỉ đúng tệp kết quả.

| Khi được hỏi | Mở trong Word | Mở trong repo | Điều có thể nói |
|---|---|---|---|
| Đóng góp C1–C3 | Mục 2.1, Kết luận Chương 3 | `src/research_agent/experiments/` | Khung đặc tả, tích hợp kiến trúc, thực hiện và kiểm toán; không nhận là phát minh Transformer/VICReg. |
| Hợp đồng Biểu diễn | Mục 1.1.3, Bảng 1.2 | `src/research_agent/experiments/extractor/` | PRESERVE/INVARIANT/EXCLUDE là yêu cầu, chưa phải bảo đảm đã chứng minh. |
| Dữ liệu và phân chia | Mục 3.1.2, Bảng 3.2 | `datasets/manifests/SPL-HDFS-001.json`, `datasets/manifests/SUBSET-MANIFEST-HDFS.json`, `src/research_agent/experiments/data/hdfs_split_authority.py` | SPL ghi giao thức và toàn ngữ liệu; SUBSET ghi 35.000 Train, 7.500 Validation và trạng thái Test. |
| Cấu trúc chuỗi | Mục 2.2–2.3 | `src/research_agent/experiments/extractor/sequence_view.py` | Transformer, biểu diễn tham số và trích xuất vector. |
| Cấu trúc đồ thị | Mục 2.2–2.4 | `src/research_agent/experiments/models/temporal_graph_view_encoder.py`, `src/research_agent/experiments/extractor/graph_view.py` | Thông điệp, thời gian, trạng thái; chi phí toàn trình chưa đo. |
| Multi-View/VICReg | Mục 2.4 | `src/research_agent/experiments/extractor/multi_view.py` | Thiết kế gióng hàng và dung hợp, không phải bằng chứng thắng Sequence. |
| Stage A2 | Mục 3.1.3, Bảng 3.3–3.4 | `src/research_agent/experiments/training/stage_a2_trainer.py`, `scripts/run_nineplus_confirmatory.py`, `experiments/plans/` | Ba loss có trọng số 1/1/0,1; năm lượt có sai lệch thủ tục khác nhau. |
| Kết quả V3 | Mục 3.2.2, Bảng 3.6 | `scripts/evaluate_nineplus_v3.py`, `experiments/nineplus/evaluation_v3/V3_SIX_BACKBONE_EVALUATION_SUMMARY.json` | Sáu backbone đóng băng; probe fit Train, đo Validation. |
| H2 và bỏ tham số | Mục 3.2.3, Bảng 3.7, 3.10 | `scripts/run_h2_sequence_noparam_sensitivity.py`, `experiments/nineplus/evaluation_v3/H2_SEQUENCE_NOPARAM_SENSITIVITY.json` | Ba độ lệch AP âm; kết quả không đổi trong phép kiểm tra bỏ tham số cụ thể. |
| H1 và che tham số | Mục 3.2.3, Bảng 3.9 | `scripts/run_h1_masking_ablation.py`, `experiments/nineplus/evaluation_v3/h1_ablation/H1_FROZEN_MASKING_ABLATION_SUMMARY.json` | Vector đổi, AP không đổi; H1 chưa đo trực tiếp ở cấp token. |
| Tái lập thủ công | Mục 3.2.2–3.2.3, Bảng 3.8 | `evidence/MANUAL_RUN_SUMMARY.txt`, `evidence/03_training_epochs_loss.png`, `experiments/nineplus/confirmatory/CONF_SEQUENCE_ONLY_seed42_1789413645/` | Sáu epoch, checkpoint tốt nhất epoch ba, hai AP thuộc hai giao thức probe. |
| Artifact nhị phân | Giới hạn Chương 3 | `experiments/nineplus/ARTIFACT-MANIFEST.json` | Bảy artifact lớn chỉ có cục bộ; clone Git sạch chưa đủ để chạy V3. |

## Thứ tự trình diễn an toàn

1. Mở `Chuyên đề chuyên sâu.docx` tại Bảng 3.6 và `V3_SIX_BACKBONE_EVALUATION_SUMMARY.json`; đối chiếu sáu hàng AP/ROC-AUC.
2. Chạy `python scripts/validate_experiment_index.py`. Đây là kiểm tra chỉ mục và mã băm, không huấn luyện lại.
3. Chỉ khi dùng đúng môi trường CUDA: đặt `CUBLAS_WORKSPACE_CONFIG=:4096:8`, chạy `scripts/gpu_smoke_test.py` và chỉ ra Python/PyTorch/GPU đang dùng.
4. Chạy V3 khi bảy artifact cục bộ có mặt và mã băm khớp. Lệnh đánh giá có thể ghi đè JSON kết quả trong cây làm việc; tạo bản sao trước khi chạy minh họa.

## Trạng thái đã xác minh trên máy này, ngày 02-10-2026

- `python -m pytest tests -q`: 31 bài kiểm thử qua; hai cảnh báo deprecation từ PyTorch CPU.
- `python scripts/validate_experiment_index.py`: 9 dòng chỉ mục và 10 artifact trong manifest được đối soát PASS trên máy hiện tại.
- Python mặc định `C:\Users\Acer\AppData\Local\Programs\Python\Python312\python.exe` dùng PyTorch CPU 2.13.0; kiểm tra GPU thất bại đúng thiết kế.
- `D:\Research\.venv-stage-a2-cuda\Scripts\python.exe` dùng PyTorch 2.6.0+cu124 và GPU khả dụng; kiểm tra GPU PASS khi đặt biến môi trường đúng.
- Đã chạy lại trực tiếp V3 với `--force-extract` cho đủ **sáu backbone xác nhận**: ba Sequence-Only và ba Multi-View ở seed 42, 7, 999. Mỗi lượt trích xuất `[35000,128]` và `[7500,128]`, fit probe 50 epoch. Xem `V3-ALL-BACKBONES-RERUN-20261003.md`; chưa huấn luyện lại Stage A2.
