# Bộ tài liệu bảo vệ chuyên đề

- `Bao-cao-chuyen-de-10-slide-v3.pptx`: 10 slide, nội dung đối chiếu với bản Word master trong thư mục gốc.
- `Bao-cao-chuyen-de-10-slide-v3.pdf`: bản xem nhanh được xuất bằng Microsoft PowerPoint.
- `LOI-THUYET-TRINH-15-PHUT.md`: lời nói theo từng slide, có mốc thời gian để tập.
- `TU-DIEN-PHAN-BIEN.md`: câu hỏi lý thuyết và câu trả lời theo đúng phạm vi bằng chứng.
- `BAN-DO-CHUNG-CU.md`: vị trí cần mở trong Word, mã nguồn và tệp kết quả khi được yêu cầu kiểm chứng.
- `V3-SEED42-RERUN-20261002.md`: biên nhận lần trích xuất lại vector và đánh giá V3 trực tiếp cho Sequence seed 42.
- `HANDOFF-CHO-AGENT-TIEP-THEO.md`: trạng thái đã chốt, giới hạn bằng chứng và việc chỉ làm khi có yêu cầu tiếp.

Các chỉ số phát hiện trong bộ này thuộc tập **Validation HDFS**, không phải tập Test. Tập Test vẫn niêm phong trong phạm vi chuyên đề. Các mô hình Graph-Only xác nhận mới chưa được huấn luyện theo giao thức V3.

Mở repo bằng VS Code, đọc `README.md` ở thư mục gốc và chạy lệnh kiểm tra chỉ mục trước khi trình diễn GPU. Môi trường Python mặc định trên máy có thể là bản PyTorch CPU; dùng môi trường CUDA đã ghi trong hướng dẫn nếu cần chạy lại mô hình.
