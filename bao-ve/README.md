# Bộ tài liệu bảo vệ chuyên đề

- `Bao-cao-chuyen-de-10-slide-v4.pptx`: bản trình chiếu hiện hành, 10 slide, đối chiếu với Word master.
- `Bao-cao-chuyen-de-10-slide-v4.pdf`: bản xem nhanh của v4, xuất bằng Microsoft PowerPoint.
- `Bao-cao-chuyen-de-10-slide-v3.pptx` và `.pdf`: bản trước ngày 06-10-2026, giữ lại để đối chiếu; không dùng khi bảo vệ.
- `LOI-THUYET-TRINH-15-PHUT.docx`: bản Word dễ đọc để tập nói theo từng slide và mốc thời gian.
- `LOI-THUYET-TRINH-15-PHUT.md`: bản văn bản nguồn để chỉnh sửa trong VS Code.
- `TU-DIEN-PHAN-BIEN.md`: câu hỏi lý thuyết và câu trả lời theo đúng phạm vi bằng chứng.
- `BAN-DO-CHUNG-CU.md`: vị trí cần mở trong Word, mã nguồn và tệp kết quả khi được yêu cầu kiểm chứng.
- `V3-SEED42-RERUN-20261002.md`: biên nhận lần trích xuất lại vector và đánh giá V3 trực tiếp cho Sequence seed 42.
- `V3-ALL-BACKBONES-RERUN-20261003.md`: biên nhận sáu lượt V3 chạy lại từ checkpoint trên GPU.
- `KICH-BAN-DEMO-VSCODE.md`: thứ tự mở tệp, lệnh kiểm chứng nhanh và câu trả lời ngắn khi trình diễn.
- `QA-SLIDE-VSCODE-20261006.md`: các lỗi đã sửa và phạm vi kiểm tra bản v4.
- `HANDOFF-CHO-AGENT-TIEP-THEO.md`: trạng thái đã chốt, giới hạn bằng chứng và việc chỉ làm khi có yêu cầu tiếp.

Các chỉ số phát hiện trong bộ này thuộc tập **Validation HDFS**, không phải tập Test. Tập Test vẫn niêm phong trong phạm vi chuyên đề. Các mô hình Graph-Only xác nhận mới chưa được huấn luyện theo giao thức V3.

Mở repo bằng VS Code, đọc `README.md` ở thư mục gốc và chạy lệnh kiểm tra chỉ mục trước khi trình diễn GPU. Môi trường Python mặc định trên máy có thể là bản PyTorch CPU; dùng môi trường CUDA đã ghi trong hướng dẫn nếu cần chạy lại mô hình.
