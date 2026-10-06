# Hướng dẫn mở và kiểm chứng chuyên đề

Hướng dẫn này dành cho buổi bảo vệ trên máy hiện tại. Mọi chỉ số AP/ROC-AUC đã lưu là trên **HDFS Validation**, không phải Test. Bản Word master ở thư mục gốc là nguồn diễn giải khoa học; các JSON/CSV là chứng cứ số liệu.

Bản trình chiếu hiện hành là `bao-ve/Bao-cao-chuyen-de-10-slide-v4.pptx`; bản v3 chỉ giữ để đối chiếu. Xem [kịch bản trình diễn VS Code](bao-ve/KICH-BAN-DEMO-VSCODE.md) trước khi mở terminal trước hội đồng.

## 1. Mở repo và xem mã theo đường đi của dữ liệu

```powershell
cd D:\chuyen-de-chuyen-sau
code .
```

Đọc theo thứ tự: `datasets/manifests/` → `src/research_agent/experiments/data/` → `extractor/` → `models/` → `training/` → `scripts/evaluate_nineplus_v3.py` → `experiments/nineplus/evaluation_v3/`. [Bản đồ chứng cứ](bao-ve/BAN-DO-CHUNG-CU.md) ghép từng phần với mục và bảng trong Word.

## 2. Các lệnh không cần GPU

```powershell
python scripts/validate_experiment_index.py
python scripts/verify_reported_results.py
python -m pytest tests -q
```

Ngày 03-10-2026: chỉ mục thực nghiệm PASS (9 dòng và 10 artifact trong manifest); đối chiếu số Word PASS; 31 bài kiểm thử PASS (2 cảnh báo deprecation của PyTorch). Lệnh `verify_reported_results.py` đối chiếu các giá trị đã đưa vào slide/tài liệu bảo vệ với JSON kết quả và manifest, **không** huấn luyện mô hình hay đọc tập Test. Nếu một artifact cục bộ thiếu, validator sẽ báo thiếu; không ghi PASS thay.

## 3. Chọn đúng môi trường CUDA

Python mặc định hiện là `C:\Users\Acer\AppData\Local\Programs\Python\Python312\python.exe`, PyTorch 2.13.0+cpu. Đây không phải môi trường huấn luyện của chuyên đề. Môi trường đã dùng cho Stage A2 nằm ở `D:\Research\.venv-stage-a2-cuda\Scripts\python.exe` trên **máy này**; đường dẫn đó không thuộc repo Git và không tồn tại trên bản clone khác.

```powershell
$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'
& 'D:\Research\.venv-stage-a2-cuda\Scripts\python.exe' scripts/gpu_smoke_test.py
```

Kiểm tra này đã PASS ngày 02-10-2026 với PyTorch 2.6.0+cu124 và CUDA khả dụng. Nó chỉ kiểm tra môi trường, không tái huấn luyện. Máy khác cần tạo môi trường theo `requirements-lock.txt`, có NVIDIA GPU/CUDA tương thích, rồi nạp artifact.

## 4. Artifact cần cho đánh giá V3

`experiments/nineplus/ARTIFACT-MANIFEST.json` kiểm kê 10 tệp; bảy tệp dữ liệu/cache/nhãn/checkpoint lớn chỉ lưu cục bộ. Raw archive HDFS cũng không nằm trong Git. Repo có script nạp artifact bằng mã băm:

```powershell
python scripts/provision_cleanroom_artifacts.py <thu_muc_chua_artifact>
python scripts/validate_experiment_index.py
```

Hiện `clean_clone_ready=false`: một bản clone sạch không tự chạy được V3 nếu chưa nạp đúng các tệp. Không copy đại một checkpoint khác seed hoặc khác commit để “chạy cho được”.

## 5. Đánh giá lại một mô hình V3 khi đã đủ điều kiện

Trước khi chạy, sao lưu `experiments/nineplus/evaluation_v3/` vì kịch bản có thể ghi lại JSON kết quả và thời gian chạy. Sau đó:

```powershell
$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'
& 'D:\Research\.venv-stage-a2-cuda\Scripts\python.exe' scripts/evaluate_nineplus_v3.py --architecture SEQUENCE_ONLY --seed 42
```

Kịch bản đóng băng backbone, fit probe trên 35.000 phiên Train và đánh giá trên 7.500 phiên Validation; nó không đánh giá Test. Ngày 02–03/10/2026 đã chạy `--force-extract` cho đủ sáu backbone Sequence-Only/Multi-View, mỗi loại ba seed 42, 7, 999. Các chỉ số in ra khớp giá trị Word/JSON ở độ chính xác được báo cáo; xem [biên nhận sáu lượt](bao-ve/V3-ALL-BACKBONES-RERUN-20261003.md). Đây là đánh giá lại **checkpoint đã huấn luyện**, không phải huấn luyện lại Stage A2 từ đầu. Trình diễn ngắn trong VS Code theo [kịch bản này](bao-ve/KICH-BAN-DEMO-VSCODE.md) để tránh ghi đè artifact trong buổi bảo vệ.

## 6. Trả lời khi được yêu cầu chỉ chứng cứ

- **Phân chia chống rò rỉ:** Word Bảng 3.2; `datasets/manifests/SPL-HDFS-001.json`; `src/research_agent/experiments/data/hdfs_split_authority.py`.
- **Huấn luyện và loss Stage A2:** Word Bảng 3.3–3.4; `src/research_agent/experiments/training/stage_a2_trainer.py`; manifest từng run trong `experiments/nineplus/confirmatory/`.
- **V3 và H2:** Word Bảng 3.6–3.7, 3.10; `V3_SIX_BACKBONE_EVALUATION_SUMMARY.json`, `H2_SEQUENCE_NOPARAM_SENSITIVITY.json`.
- **H1:** Word Bảng 3.9; `h1_ablation/H1_FROZEN_MASKING_ABLATION_SUMMARY.json`.
- **Lượt chạy thủ công:** Word Bảng 3.8; `evidence/MANUAL_RUN_SUMMARY.txt`, `evidence/03_training_epochs_loss.png`.

Không dùng giá trị Graph-Only theo probe nội bộ để xếp hạng trực tiếp với V3. Không dùng loss tự giám sát thay AP. Không gọi AP trên Validation là kết quả Test. Khi hội đồng hỏi về giới hạn, mở Kết luận Chương 3 thay vì suy đoán.
