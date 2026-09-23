# Nghiên cứu phương pháp trích xuất đặc trưng đối với dữ liệu log trong phát hiện tấn công

**Đơn vị:** Học viện Kỹ thuật Mật mã  
**Học phần:** Chuyên đề chuyên sâu  
**Sinh viên thực hiện:** Đoàn Ngọc Hoàng Minh – AT180632  
**Giảng viên hướng dẫn:** ThS. Nguyễn Thị Thu Thủy  

---

## 1. TÀI LIỆU CHUYÊN ĐỀ CHÍNH THỨC

| Văn bản | Định dạng | Mục đích |
| :--- | :---: | :--- |
| **Bản chuyên đề chính thức** | [PDF](Chuyên%20đề%20chuyên%20sâu.pdf) | Bản dùng để đọc và phản biện (120 trang) |
| **Bản Word** | [DOCX](Chuyên%20đề%20chuyên%20sâu.docx) | Bản nguồn có thể chỉnh sửa |
| **Hướng dẫn kiểm chứng** | [Markdown](HUONG_DAN_CHAY_VA_XAC_MINH.md) | Hướng dẫn tái lập thực nghiệm |
| **Chỉ mục thực nghiệm** | [CSV](experiments/experiment_index.csv) | Đối chiếu các run và kết quả (18 cột) |
| **Bằng chứng thực nghiệm** | [Thư mục](evidence/) | Ảnh minh họa, tóm tắt phiên chạy và kết quả V3 |

---

## 2. TỔNG QUAN ĐỀ TÀI VÀ ĐÓNG GÓP KỸ THUẬT

Chuyên đề tập trung giải quyết bài toán biểu diễn dữ liệu log phục vụ phát hiện tấn công mạng, bảo toàn ngữ nghĩa an ninh và cấu trúc quan hệ thực thể, tuân thủ tính quy nạp theo dòng thời gian nhân quả:

1. **Kiến trúc biểu diễn đa góc nhìn (Multi-View Representation):**
   - *Góc nhìn tuần tự (Sequence View):* Mạng Transformer Encoder xử lý đồng thời chuỗi sự kiện cú pháp và các tham số động đa khe (`d_model=128`, 4 layers, 4 heads).
   - *Góc nhìn đồ thị động (Temporal Graph View):* Bộ mã hóa đồ thị thời gian tích hợp bộ nhớ `GRUCell` và hàm nhúng thời gian liên tục, bảo toàn quan hệ tương tác giữa các thực thể hệ thống.
   - *Hòa trộn dựa trên cổng độ tin cậy động (Gated Fusion):* Mạng cổng MLP tự động cân bằng đóng góp giữa chuỗi cú pháp và cấu trúc đồ thị.

2. **Bảo tồn tham số động có nhận thức an ninh (Security-Aware Dynamic Parameter Preservation):**
   - Lược đồ phân loại kiểu dữ liệu an ninh (IP nội bộ/ngoại vi theo RFC 1918, cổng dịch vụ, đường dẫn hệ điều hành trọng yếu, mã tiến trình).
   - Cơ chế tạo mã giả danh nhất quán theo phiên dựa trên hàm băm HMAC có khóa ngắn hạn nhằm giảm lộ trực tiếp identifier thô (pseudonymization và controlled linkability; không loại bỏ hoàn toàn privacy risk).

3. **Giao thức phân chia dữ liệu nhân quả chống rò rỉ (SPL-HDFS-001):**
   - Phân chia 11,17 triệu dòng log HDFS theo đúng thứ tự thời gian (Train < Val < Test).
   - Loại bỏ các phiên vắt ngang ranh giới chuyển tiếp (purging cross-boundary sessions).
   - Tập Test được giữ ở trạng thái chưa mở (`TEST_OPENED=false`, `TEST_READ_COUNT=0`); đây là trạng thái protocol ghi nhận, không phải tuyên bố bảo đảm tuyệt đối.

---

## 3. KẾT QUẢ THỰC NGHIỆM CHÍNH (NINEPLUS V3 STANDARDIZED)

> [!NOTE]
> Toàn bộ chỉ số AP và ROC-AUC dưới đây được đánh giá trên tập **Validation** (7.500 phiên), **không phải** tập Test. Tập Test chưa được mở trong phạm vi chuyên đề này.

Giao thức đánh giá: Frozen Linear Probe V3 (`FROZEN_PROBE_V3_STANDARDIZED`) — đóng băng toàn bộ trọng số backbone, huấn luyện đầu dò tuyến tính trên 35.000 vector Train và đo hiệu năng trên 7.500 vector Validation:

| Kiến trúc | Seed | Best Val Loss | Internal Probe AP / ROC-AUC | Frozen Linear Probe V3 AP / ROC-AUC | Trạng thái bằng chứng |
| :--- | :---: | :---: | :---: | :---: | :---: |
| SEQUENCE_ONLY | 42 | 0.0092 | 0.8994 / 0.9973 | 1.0000 / 1.0000 | COMPLETED (Có sẵn trong Git) |
| SEQUENCE_ONLY | 7 | 0.0063 | 0.9179 / 0.9984 | 1.0000 / 1.0000 | COMPLETED (Có sẵn trong Git) |
| SEQUENCE_ONLY | 999 | 0.0073 | 0.7887 / 0.9263 | 1.0000 / 1.0000 | COMPLETED (Có sẵn trong Git) |
| MULTI_VIEW_ALIGNED | 42 | 49.1768 | 0.7032 / 0.9319 | 0.7604 / 0.9946 | COMPLETED (Có sẵn trong Git) |
| MULTI_VIEW_ALIGNED | 7 | 49.0099 | 0.6082 / 0.8899 | 0.6309 / 0.8081 | RESULT_JSON_ONLY_IN_GIT |
| MULTI_VIEW_ALIGNED | 999 | 48.7659 | 0.6855 / 0.8580 | 0.5911 / 0.7693 | RESULT_JSON_ONLY_IN_GIT |
| GRAPH_ONLY | 42 | 6.0814 | 0.7090 / 0.8053 | *(Chưa đánh giá V3)* | HISTORICAL_REF_PENDING_AUDIT |
| GRAPH_ONLY | 7 | 0.5503 | 0.6178 / 0.7516 | *(Chưa đánh giá V3)* | HISTORICAL_REF_PENDING_AUDIT |
| GRAPH_ONLY | 999 | 0.6095 | 0.6815 / 0.8857 | *(Chưa đánh giá V3)* | HISTORICAL_REF_PENDING_AUDIT |

*GRAPH_ONLY sử dụng giao thức nội bộ `HISTORICAL_STAGE_A2_INTERNAL_PROBE` (80/20 split trên tập Train); chưa có đánh giá Frozen Linear Probe V3 chuẩn hóa. Các chỉ số internal probe và best val loss của GRAPH_ONLY không thể so sánh trực tiếp với SEQUENCE_ONLY/MULTI_VIEW_ALIGNED.*

*Chi tiết đối soát từng dòng xem tại:* [`experiments/experiment_index.csv`](experiments/experiment_index.csv).

---

## 4. CẤU TRÚC REPOSITORY THỰC TẾ

Cây thư mục phản ánh các tệp tin hiện hữu trong repository:

```text
├── datasets/
│   ├── manifests/
│   │   ├── REAL-DATA-CONTRACT-HDFS.json
│   │   ├── SPL-HDFS-001.json
│   │   └── SUBSET-MANIFEST-HDFS.json
│   ├── processed/
│   │   └── .gitkeep
│   └── raw/
│       └── .gitkeep
├── evidence/
│   ├── stage-a2/
│   │   └── preexecution/
│   │       └── STAGE-A2-LOCAL-EXECUTION-ENVIRONMENT-V1.5.json # Khóa môi trường thực thi gốc
│   ├── 03_training_epochs_loss.png      # Ảnh chụp console đợt huấn luyện xác nhận
│   ├── MANUAL_RUN_SUMMARY.txt           # Tóm tắt số liệu đợt chạy xác nhận
│   └── V3-PROBE-RESULT.json             # Kết quả đánh giá hạ nguồn V3
├── experiments/
│   ├── plans/
│   │   ├── STAGE-A2-FINAL-12-EPOCH-AUTHORITY.json       # Kế hoạch thực nghiệm 12-epoch chính thức
│   │   └── STAGE-A2-FIVE-SEED-EXECUTION-PLAN-V1.5.json  # Kế hoạch thực nghiệm lịch sử (nguyên bản)
│   ├── nineplus/
│   │   ├── confirmatory/                # Manifest cấu hình các đợt chạy xác nhận
│   │   ├── evaluation_v3/               # Kết quả đánh giá hạ nguồn V3 (JSON)
│   │   └── ARTIFACT-MANIFEST.json       # Bảng kê mã băm toàn bộ artifact
│   └── experiment_index.csv             # Chỉ mục thực nghiệm 18 cột
├── scripts/
│   ├── evaluate_nineplus_v3.py          # Đánh giá đầu dò tuyến tính đóng băng V3
│   ├── gpu_smoke_test.py                # Kiểm tra phần cứng GPU
│   ├── provision_cleanroom_artifacts.py # Nạp và đối soát mã băm artifact ngoại vi
│   ├── run_h1_masking_ablation.py       # Kiểm định cắt bỏ mặt nạ (Ablation H1)
│   ├── run_h2_sequence_noparam_sensitivity.py # Phân tích độ nhạy tham số (H2)
│   ├── run_nineplus_confirmatory.py     # Huấn luyện xác nhận
│   └── validate_experiment_index.py     # Đối soát experiment_index.csv
├── src/research_agent/                  # Mã nguồn khoa học cốt lõi
│   ├── experiments/
│   │   ├── data/                        # Bộ điều hợp dữ liệu HDFS/BGL, split authority
│   │   ├── extractor/                   # Tokenizer, Sequence View, Graph View, Multi-View
│   │   ├── models/                      # Temporal Graph View Encoder
│   │   └── training/                    # Trainer Stage A2
│   └── __init__.py
├── tests/                               # Bộ kiểm thử đơn vị (31 bài kiểm thử)
├── .gitignore
├── Chuyên đề chuyên sâu.docx            # Bản thảo Word
├── Chuyên đề chuyên sâu.pdf             # Bản chuyên đề chính thức (120 trang)
├── HUONG_DAN_CHAY_VA_XAC_MINH.md        # Hướng dẫn kiểm chứng dành cho Hội đồng
├── pyproject.toml                       # Metadata gói research-agent
├── README.md                            # Tài liệu tổng quan này
└── requirements-lock.txt                # Khóa phụ thuộc (CUDA 12.4)
```

---

## 5. HƯỚNG DẪN KIỂM CHỨNG NHANH

Giảng viên hoặc người phản biện có thể kiểm chứng hệ thống qua các lệnh sau:

1. **Kiểm tra phần cứng và môi trường tính toán:**
   ```powershell
   $env:CUBLAS_WORKSPACE_CONFIG=":4096:8"
   python scripts/gpu_smoke_test.py
   ```
   *Kỳ vọng trên máy thử nghiệm:* `[PASS] GPU Smoke Test Passed` (Exit Code 0).

2. **Kiểm tra tính nhất quán của bảng chỉ mục thực nghiệm:**
   ```powershell
   python scripts/validate_experiment_index.py
   ```
   *Kỳ vọng:* Báo cáo đối soát từng dòng trong `experiment_index.csv` với nguồn JSON artifact.

3. **Tái lập kết quả đánh giá hạ nguồn V3 trên máy thử nghiệm:**
   ```powershell
   $env:CUBLAS_WORKSPACE_CONFIG=":4096:8"
   python scripts/evaluate_nineplus_v3.py --architecture SEQUENCE_ONLY --seed 42
   ```
   *Kết quả kỳ vọng (trên Validation set):* `AP=1.0000 | ROC-AUC=1.0000` (~15 giây trên GPU RTX 3050 Ti Laptop).

4. **Chạy bộ kiểm thử đơn vị:**
   ```powershell
   python -m pytest tests
   ```
   *Kết quả trong môi trường hiện tại:* 31 bài kiểm thử vượt qua (`31 passed`).

*Xem chi tiết hướng dẫn đầy đủ tại:* [`HUONG_DAN_CHAY_VA_XAC_MINH.md`](HUONG_DAN_CHAY_VA_XAC_MINH.md).

---

## 6. TUYÊN BỐ VỀ ARTIFACT NGOẠI VI VÀ BẢN CLONE SẠCH

> [!CAUTION]
> **Trạng thái kho lưu trữ ngoại vi:** `PUBLIC_CLEAN_CLONE_READY = false`  
> Artifact ngoại vi chưa được phát hành công khai. Một bản clone Git sạch từ Internet sẽ cần bước nạp artifact cục bộ trước khi chạy được.

- **Chính sách Git:** Tuân thủ chuẩn mực kỹ thuật phần mềm, toàn bộ tệp nhị phân kích thước lớn (`*.pt`, trọng số mô hình `best_checkpoint.pt`) không lưu trực tiếp trong Git.
- **Để chạy tái lập trên bản clone sạch:** Cần nạp 7 artifact ngoại vi (tổng dung lượng 108.856.472 bytes, bao gồm 4 tensor/cache HDFS, 2 nhãn probe vault và checkpoint tối ưu; không bao gồm raw HDFS archive) vào các thư mục tương ứng theo bảng kê [`experiments/nineplus/ARTIFACT-MANIFEST.json`](experiments/nineplus/ARTIFACT-MANIFEST.json), hoặc dùng script tự động:
  ```powershell
  python scripts/provision_cleanroom_artifacts.py <đường_dẫn_chứa_artifact_ngoại_vi>
  ```
- Các bằng chứng thực nghiệm đã lưu tại thư mục [`evidence/`](evidence/).

