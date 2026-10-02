# Biên nhận đánh giá lại V3 — Toàn bộ 6 backbone từ checkpoint

Tại mốc kiểm chứng ngày 02–03/10/2026, toàn bộ **06 backbone xác nhận của Chiến dịch Nineplus V3** đã được chạy trích xuất lại trực tiếp từ checkpoint đã huấn luyện trên GPU (`--force-extract`), huấn luyện đầu dò tuyến tính 50 epoch chỉ trên Train, và đánh giá trên 100% tập Validation. Đây là đánh giá lại từ checkpoint, không phải huấn luyện lại Stage A2.

## 1. Môi trường thực thi & Tham số tái lập
- **Phần cứng:** NVIDIA GeForce RTX 3050 Ti Laptop GPU (Compute Capability 8.6).
- **Môi trường:** Python 3.12.8, PyTorch 2.6.0+cu124, CUDA 12.4 (`D:\Research\.venv-stage-a2-cuda\Scripts\python.exe`).
- **Khóa xác định:** `$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'`.
- **Giao thức:** `TRAIN_FIT_FULL_FIXED_VALIDATION_EVALUATE`. Khóa seed probe tại `10007`.
- **Bất biến tập dữ liệu & Niêm phong Test:**
  * Train Membership SHA (35.000 phiên): `65b76694b0a3cf5c6d684a26899b1e5dca634cfd0985560149feddc12ca8ccfc` (PASS).
  * Val Membership SHA (7.500 phiên): `14cf689f9682a354e104463b9f02806629a683dfdf36d72d88daf5b407b0609a` (PASS).
  * Ordered Train Session-ID SHA: `35396a595ded6ab643c07ce03528da4b91c1d270979b2c52e3e11f0cebcc7e60` (PASS).
  * Ordered Val Session-ID SHA: `4f474991f03aab4856c2666a671bee3fc69d8e893e22e9c2d9ca1269b8bd68ae` (PASS).
  * Trạng thái Test do kịch bản ghi và kiểm tra: `TEST_OPENED=False`, `TEST_READ_COUNT=0` (PASS trong phạm vi lượt chạy này).

## 2. Bảng kết quả kiểm chứng trực tiếp đối chiếu với Word Master

| Kiến trúc | Seed | Thời gian trích xuất Train / Val | AP thực nghiệm | ROC-AUC thực nghiệm | Var(z) | Steps probe | Đối chiếu số công bố | Mã băm SHA-256 Log thực thi |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `SEQUENCE_ONLY` | 42 | 4.35s / 0.77s | **1.0000** | **1.0000** | 0.004535 | 6.850 | Khớp ở mức báo cáo | `09edddd1e1cfa28a683956f73219d9dcb97a8e312233e792c9c4704bdac8f889` |
| `SEQUENCE_ONLY` | 7 | 3.90s / 0.79s | **1.0000** | **1.0000** | 0.005755 | 6.850 | Khớp ở mức báo cáo | `09cc6eb0ebd213595ffe0e053af21877ae64cfe72f175eadc65d663d171941ce` |
| `SEQUENCE_ONLY` | 999 | 3.93s / 0.79s | **1.0000** | **1.0000** | 0.006098 | 6.850 | Khớp ở mức báo cáo | `c97ec35e212e6973fde1062cde0f9c6fef692c6ab8f3f158c4fefe5685810a5c` |
| `MULTI_VIEW_ALIGNED` | 42 | 554.86s / 112.36s | **0.7604** | **0.9946** | 0.005513 | 6.850 | Khớp ở mức báo cáo | `2bc4ddca9b672514647421a0eef2b0cf3c8cae39ed98dce5130d28516f1fc006` |
| `MULTI_VIEW_ALIGNED` | 7 | 572.02s / 116.98s | **0.6309** | **0.8081** | 0.004682 | 6.850 | Khớp ở mức báo cáo | `d8ac393122b3148a5a1b26d212c5c5d1479e2aafbaa04aa4c474c3c8cd28972f` |
| `MULTI_VIEW_ALIGNED` | 999 | 1288.26s / 205.80s | **0.5911** | **0.7693** | 0.008013 | 6.850 | Khớp ở mức báo cáo | `28f5da5868aa3c160ee3b6fd5bcf5a6ba33f8022569dd923a109c6020b09e131` |

## 3. Tổng hợp thống kê & Bất biến khoa học H2
- **Multi-View AP:** $0{,}7604$; $0{,}6309$; $0{,}5911$. Trung bình: $0{,}6608 \pm 0{,}0885$ (độ lệch chuẩn mẫu).
- **Sequence-Only AP:** $1{,}0000$; $1{,}0000$; $1{,}0000$. Trung bình: $1{,}0000 \pm 0{,}0000$.
- **Độ lệch AP (Multi-View trừ Sequence):** $-0{,}2396$; $-0{,}3691$; $-0{,}4089$. Trung bình: $-0{,}3392 \pm 0{,}0885$.
- **Kết luận H2:** Tất cả các cặp seed đều vi phạm sâu biên không thua kém ($-0{,}02$). Lần đánh giá lại từ cùng checkpoint và mã nguồn trên GPU tiếp tục cho thấy H2 **không được hỗ trợ** trên tập Validation HDFS.

## 4. Quản lý trạng thái Git và Lưu trữ bằng chứng
- Toàn bộ log chi tiết 6 lần chạy được lưu giữ cục bộ tại `C:\Users\Acer\Downloads\ChuyenDe-backup-truoc-bao-ve-20261002\`.
- Sau lần chạy kiểm chứng, các tệp kết quả JSON lịch sử được bảo toàn nguyên trạng mã băm ban đầu; Git working tree được duy trì hoàn toàn sạch.
