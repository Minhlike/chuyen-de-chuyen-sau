# Trích xuất đặc trưng log phục vụ phát hiện tấn công

Chuyên đề chuyên sâu của Đoàn Ngọc Hoàng Minh, AT180632 — Học viện Kỹ thuật Mật mã. [Bản Word master](Chuyên%20đề%20chuyên%20sâu.docx) là nguồn nội dung khoa học; [PDF](Chuyên%20đề%20chuyên%20sâu.pdf) là bản đọc. Bộ [slide và tài liệu bảo vệ](bao-ve/README.md) dẫn về đúng bản Word này.

## Phạm vi kết quả

Repo chứa mã xử lý HDFS, mô hình chuỗi–đồ thị, kịch bản huấn luyện/đánh giá, manifest và các kết quả máy đọc được. Các chỉ số dưới đây thuộc **HDFS Validation**, không phải Test. Test niêm phong trong phạm vi chuyên đề (`test_opened=false`, `test_reads=0`).

| Đối chứng Frozen Linear Probe V3 | Seed 42 | Seed 7 | Seed 999 | Trung bình |
|---|---:|---:|---:|---:|
| Sequence-Only AP | 1,0000 | 1,0000 | 1,0000 | 1,0000 |
| Multi-View AP | 0,7604 | 0,6309 | 0,5911 | 0,6608 |
| Multi-View ROC-AUC | 0,9946 | 0,8081 | 0,7693 | 0,8573 |
| ΔAP = Multi-View − Sequence | −0,2396 | −0,3691 | −0,4089 | −0,3392 |

Biên không thua kém H2 đặt trước là −0,02 AP. Ba cặp seed đều vi phạm biên nên H2 **không được hỗ trợ trong đối chứng này**. Đây không phải kết luận cho mọi bộ dữ liệu hoặc mọi kiến trúc đa góc nhìn. H1 chưa đo trực tiếp vì mục tiêu tham số ở cấp token/khe còn vector đánh giá ở cấp phiên. H3–H5 chưa được kiểm chứng thực nghiệm; ER1 mới có quan sát bộ nhớ cục bộ. Nguồn: Word Mục 3.2.2–3.3.3 và `experiments/nineplus/evaluation_v3/`.

## Tìm mã nguồn

| Việc cần xem | Đường dẫn |
|---|---|
| Nạp, chuẩn hóa và phân chia HDFS | `src/research_agent/experiments/data/` |
| Tokenizer, nhánh chuỗi, nhánh đồ thị, Multi-View | `src/research_agent/experiments/extractor/` |
| Temporal GNN | `src/research_agent/experiments/models/` |
| Trainer Stage A2 | `src/research_agent/experiments/training/` |
| Chạy huấn luyện xác nhận | `scripts/run_nineplus_confirmatory.py` |
| Đầu dò tuyến tính V3 | `scripts/evaluate_nineplus_v3.py` |
| Phép thử H1/H2 | `scripts/run_h1_masking_ablation.py`, `scripts/run_h2_sequence_noparam_sensitivity.py` |
| Chỉ mục, kế hoạch, kết quả | `experiments/` |
| Kiểm thử | `tests/` |

## Kiểm chứng nhanh trên máy hiện tại

Từ thư mục gốc repo:

```powershell
python scripts/validate_experiment_index.py
python -m pytest tests -q
```

Lệnh đầu đối soát 9 dòng chỉ mục thực nghiệm với JSON nguồn và mã băm 10 tệp trong manifest. Lệnh thứ hai chạy 31 bài kiểm thử. Cả hai đã PASS ngày 02-10-2026; chúng **không** huấn luyện lại mô hình.

Để chạy kiểm tra GPU và tái đánh giá V3, cần dùng đúng môi trường CUDA, dữ liệu cache, nhãn và checkpoint cục bộ. Python mặc định trên máy này là bản PyTorch CPU; đừng dùng nó để kết luận CUDA hỏng. Xem [hướng dẫn chạy](HUONG_DAN_CHAY_VA_XAC_MINH.md) và [bản đồ chứng cứ](bao-ve/BAN-DO-CHUNG-CU.md).

## Dữ liệu và giới hạn tái lập

Tệp HDFS thô, các tensor `.pt`, nhãn probe và checkpoint lớn không được đưa vào Git. `experiments/nineplus/ARTIFACT-MANIFEST.json` ghi đường dẫn, dung lượng và SHA-256 của 10 tệp được kiểm kê; bảy tệp nhị phân/cache cần nạp cục bộ trước khi chạy V3 trên clone sạch. Trạng thái `clean_clone_ready` hiện là `false`. Những JSON kết quả đã lưu cho phép kiểm toán số liệu, nhưng **không thay thế một lần chạy lại**.

Năm lượt Stage A2 được báo cáo kèm sai lệch thủ tục riêng; không có lượt nào đạt trọn bộ điều kiện chuẩn. Graph-Only xác nhận mới chưa được huấn luyện/đánh giá theo V3. Các số Graph-Only lịch sử theo probe nội bộ không được so trực tiếp với V3. Seed 999 Multi-View có sai lệch khôi phục RNG đã công bố trong Word.

Không có script biên tập Word hoặc tạo phương trình trong repo này. Lịch sử các đợt biên tập văn bản vẫn nằm trong Git; cây làm việc hiện tập trung vào tài liệu master, mã thực nghiệm, dữ liệu mô tả và chứng cứ khoa học.
