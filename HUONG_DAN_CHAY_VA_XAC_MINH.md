# CẨM NANG HƯỚNG DẪN CHẠY VÀ XÁC MINH THỰC NGHIỆM
**Dành cho:** Giảng viên Hướng dẫn, Giảng viên Phản biện và Hội đồng Đánh giá Chuyên đề  
**Đề tài:** *Nghiên cứu phương pháp trích xuất đặc trưng đối với dữ liệu log trong phát hiện tấn công*  
**Sinh viên thực hiện:** Đoàn Ngọc Hoàng Minh – AT180632  
**Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thu Thủy  
**Thời gian kiểm chứng dự kiến:** Khoảng 2–3 phút trên máy thử nghiệm (RTX 3050 Ti Laptop GPU 4 GB VRAM)

---

## 1. ĐIỀU KIỆN TIÊN QUYẾT (PREREQUISITES)

- **Hệ điều hành:** Windows 10/11 (64-bit).
- **Môi trường Python:** Python 3.12 (đã kiểm chứng trên Python 3.12.8).
- **Phần cứng đề xuất:** Card đồ họa rời NVIDIA (đã kiểm chứng trên NVIDIA GeForce RTX 3050 Ti Laptop GPU 4 GB VRAM) hoặc CPU tương thích.
- **Công cụ dòng lệnh:** Windows PowerShell thông thường.

---

## 2. QUY TRÌNH THIẾT LẬP MÔI TRƯỜNG (KHOẢNG 1 PHÚT)

Từ thư mục gốc của repository, mở cửa sổ Windows PowerShell và thực hiện các lệnh sau:

```powershell
# 1. Khởi tạo môi trường ảo Python biệt lập
python -m venv .venv

# 2. Kích hoạt môi trường ảo
.\.venv\Scripts\Activate.ps1

# 3. Đảm bảo hỗ trợ UTF-8 cho PowerShell và nâng cấp pip
$env:PYTHONUTF8 = "1"
python -m pip install --upgrade pip

# 4. Cài đặt các thư viện phụ thuộc chính thức (có hỗ trợ CUDA 12.4)
pip install --extra-index-url https://download.pytorch.org/whl/cu124 -r requirements-lock.txt

# 5. Liên kết gói mã nguồn nghiên cứu ở chế độ phát triển
pip install -e .
```

---

## 3. NẠP ARTIFACT NGOẠI VI (KHOẢNG 30 GIÂY)

> [!NOTE]
> Do chính sách không lưu trữ dữ liệu nhị phân lớn trong Git (tuân thủ `.gitignore`), 7 artifact thực nghiệm ngoại vi (tổng dung lượng 108.856.472 bytes, bao gồm tensor đặc trưng `.pt`, từ vựng, nhãn kiểm định và checkpoint tối ưu `best_checkpoint.pt`; không bao gồm raw HDFS archive) cần được nạp trước khi chạy.

Sử dụng script tự động để nạp và đối soát mã băm SHA-256 đối chiếu với `experiments/nineplus/ARTIFACT-MANIFEST.json`:

```powershell
# Nạp và đối soát toàn vẹn 7 artifact từ thư mục lưu trữ cục bộ/ngoại vi
python scripts/provision_cleanroom_artifacts.py <đường_dẫn_thư_mục_chứa_artifact>
```

*Kỳ vọng:* In ra `[PASS] All 7 external artifacts successfully provisioned and verified.` và xuất báo cáo tại `evidence/ARTIFACT_PROVISIONING_REPORT.json`.

---

## 4. BA LỆNH KIỂM CHỨNG NHANH CỦA HỘI ĐỒNG (QUICK VERIFICATION)

### Lệnh 1: Kiểm tra phần cứng GPU và môi trường tính toán xác định
```powershell
$env:CUBLAS_WORKSPACE_CONFIG=":4096:8"
python scripts/gpu_smoke_test.py
```
- **Thời gian chạy:** ~3 giây trên máy thử nghiệm.
- **Kỳ vọng:** In ra `[PASS] GPU Smoke Test Passed` với mã thoát 0.
- **Mục đích:** Xác nhận GPU NVIDIA khả dụng, PyTorch 2.6.0+cu124, PyG 2.6.1 và cờ tái lập `CUBLAS_WORKSPACE_CONFIG` hoạt động đúng.

---

### Lệnh 2: Thẩm định tính toàn vẹn của Bảng chỉ mục Thực nghiệm
```powershell
python scripts/validate_experiment_index.py
```
- **Thời gian chạy:** ~2 giây trên máy thử nghiệm.
- **Kỳ vọng:** In ra:
  ```text
  [VALIDATOR-PASS] records in experiment_index.csv match source JSON artifacts
  [VALIDATOR-PASS] artifacts in ARTIFACT-MANIFEST.json verified
  ```
- **Mục đích:** Đối soát từng dòng trong `experiments/experiment_index.csv` (18 cột) với các tệp JSON nguồn, bảo đảm không có hiện tượng trộn lẫn chỉ số giữa đầu dò nội bộ và đầu dò V3 chuẩn hóa.

---

### Lệnh 3: Tái lập chỉ số Đánh giá Hạ nguồn V3 trên Validation set
```powershell
$env:CUBLAS_WORKSPACE_CONFIG=":4096:8"
python scripts/evaluate_nineplus_v3.py --architecture SEQUENCE_ONLY --seed 42
```
- **Thời gian chạy:** ~15 giây trên máy thử nghiệm (RTX 3050 Ti Laptop GPU).
- **Tiến trình tự động:**
  1. Kiểm tra 4 bất biến mật mã phân chia nhân quả (Train Membership SHA: `65b76694b0a3...`, Val Membership SHA: `14cf689f9682...`, Ordered Train/Val SHA) → PASS.
  2. Xác nhận trạng thái tập Test (`TEST_OPENED=false`, `TEST_READ_COUNT=0`).
  3. Trích xuất đặc trưng 35.000 phiên Train và 7.500 phiên Validation.
  4. Huấn luyện Frozen Linear Probe V3 trong 50 epochs (Seed 10007, AdamW).
  5. In ra kết quả đánh giá hạ nguồn trên Validation set:
     ```text
     >>> V3 PROBE RESULT: AP=1.0000 | ROC-AUC=1.0000 | Var(z)=0.004535 | Steps=6850
     >>> Result written to experiments/nineplus/evaluation_v3/.../V3-PROBE-RESULT.json
     ```
- **Lưu ý:** Kết quả AP=1.0000 và ROC-AUC=1.0000 là trên tập **Validation** (7.500 phiên). Tập Test chưa được đánh giá trong phạm vi chuyên đề.
- **Mã thoát:** `0`.

---

## 5. ĐỐI SOÁT VỚI BẢN THẢO CHUYÊN ĐỀ CHÍNH THỨC

Sau khi chạy xong, Thầy/Cô có thể mở bản thảo [`Chuyên đề chuyên sâu.pdf`](Chuyên%20đề%20chuyên%20sâu.pdf) (120 trang) để đối chiếu trực tiếp:

1. **Mục 3.2.4 "Kiểm chứng tái lập trên máy trạm" (Trang 85–88):**
   - **Bảng 3.7b:** Đối chiếu các chỉ số hội tụ của đợt huấn luyện xác nhận: `best_epoch = 3`, `best_val_loss = 0.009218`, dừng sớm tại `Epoch 6` với `patience = 3`, VRAM đỉnh `170.4 MB`.
   - **Hình 3.1:** Ảnh chụp console thực tế thể hiện quá trình tối ưu hóa qua các epochs và lưu vết checkpoint.
2. **Bảng 3.7 "Hiệu năng phát hiện bất thường qua các cấu hình kiến trúc":**
   - Hàng cấu hình `SEQUENCE_ONLY` (Seed 42): AP = 1.0000 và ROC-AUC = 1.0000 trên Validation.
3. **Bằng chứng thực nghiệm đã lưu trữ:**
   - Xem kết quả đánh giá tại [`evidence/V3-PROBE-RESULT.json`](evidence/V3-PROBE-RESULT.json).
   - Xem tóm tắt phiên chạy huấn luyện tại [`evidence/MANUAL_RUN_SUMMARY.txt`](evidence/MANUAL_RUN_SUMMARY.txt).
   - Xem ảnh chụp màn hình console tại [`evidence/03_training_epochs_loss.png`](evidence/03_training_epochs_loss.png).

---

## 6. TUYÊN BỐ VỀ TÍNH SẴN SÀNG CÔNG KHAI

- **Trạng thái hiện tại:** `PUBLIC_CLEAN_CLONE_READY = false`.
- **Lý do kỹ thuật:** 7 artifact ngoại vi (tổng dung lượng 108.856.472 bytes) chưa được phát hành trên kho lưu trữ công khai (Zenodo/OSF). Một bản clone Git sạch từ Internet sẽ cần bước nạp artifact cục bộ như hướng dẫn ở Mục 3.
- **Ghi chú về tính xác định:** Toàn bộ thuật toán, mã nguồn và kịch bản đối soát sử dụng seed cố định và cờ `CUBLAS_WORKSPACE_CONFIG` để tái lập được kết quả trên cấu hình phần cứng tương đương. Kết quả có thể có sai số nhỏ trên phần cứng hoặc phiên bản CUDA khác.
