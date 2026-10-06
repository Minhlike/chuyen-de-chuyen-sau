# Kiểm tra bộ slide và trình diễn VS Code ngày 06-10-2026

## Bản được kiểm tra

- Word master: `Chuyên đề chuyên sâu.docx`, SHA-256 `2425ffb1b8c109a410a93a30e76c99251d234fa20ab33efbb9922bdc44f0e92f`.
- Slide hiện hành: `Bao-cao-chuyen-de-10-slide-v4.pptx`, SHA-256 `0b4f110f69fc962e1c5accc21a3075b57a2a1e9b122f6a09e94567096ea63098`.
- PDF do PowerPoint COM phiên bản 16.0 xuất: `Bao-cao-chuyen-de-10-slide-v4.pdf`, SHA-256 `c0fb46181e662d7085a5654c73f5f8593dd036a56982e3bd0e5f7c3c4453ac90`.

## Vấn đề phát hiện và xử lý

| Vị trí | Vấn đề ở v3 | Sửa ở v4 |
| --- | --- | --- |
| Trang bìa | Tên đề tài thiếu cụm “đối với” so với Word master | Khôi phục nguyên văn tên đề tài và tách thành bốn dòng dễ đọc |
| Slide 5 | Chú dẫn chỉ nêu manifest tổng, trong khi ngân sách 35.000/7.500 ở manifest tập con | Ghi cả `SPL-HDFS-001` và `SUBSET-MANIFEST-HDFS` |
| Slide 6 | Câu chú giải ở nửa phải bị cắt gần mép trang | Rút gọn câu, giữ nguyên ý nghĩa khoa học |
| Slide 7 | Chưa nói rõ chứng cứ chạy lại đủ sáu checkpoint | Nêu trích xuất và fit probe đã chạy lại; Stage A2 chưa huấn luyện lại |
| Slide 8 | Hai nhãn dưới bảng quá sát nhau | Rút ngắn nhãn, giữ nội dung bảng và kết luận H2 |
| Kịch bản VS Code | Trỏ manifest tổng khi chỉ số lượng tập con | Chỉ đúng `SUBSET-MANIFEST-HDFS.json`; thêm cách xem dữ liệu HDFS gốc và mã huấn luyện |

## Các cổng đã kiểm tra

- 10 slide, 10 phần ghi chú người nói, 4 bảng native; PPTX ZIP CRC hợp lệ. Bộ kiểm tra bố cục/gói trình chiếu báo 0 phát hiện.
- Mở được bằng PowerPoint COM 16.0, xuất PDF 10 trang tỉ lệ 16:9. Đã xem từng trang PDF; không còn câu bị cắt ở slide 6 hoặc nhãn va nhau ở slide 8. Năm trang không sửa (2, 3, 4, 9, 10) có ảnh xuất PDF trùng hash với v3.
- `python scripts/validate_experiment_index.py`: 9 bản ghi chỉ mục và 10 artifact PASS.
- `python scripts/verify_reported_results.py`: hash Word và các số HDFS/V3/H1/H2 được kiểm tra PASS; đây là đối chiếu tĩnh.
- `python -m pytest tests -q`: 31 PASS, 2 cảnh báo deprecation của PyTorch.
- Môi trường `D:\Research\.venv-stage-a2-cuda\Scripts\python.exe` vượt qua GPU smoke test với PyTorch `2.6.0+cu124`, PyG `2.6.1`, CUDA và phép nhân ma trận trên GPU.
- Sáu log chạy lại V3 còn tại `C:\Users\Acer\Downloads\ChuyenDe-backup-truoc-bao-ve-20261002\`, SHA-256 từng log khớp `V3-ALL-BACKBONES-RERUN-20261003.md`. Hai tệp HDFS gốc ở `D:\Research\datasets\raw\hdfs\` khớp hash trong `SPL-HDFS-001.json`.

Word master, JSON kết quả và checkpoint không được chỉnh trong vòng kiểm tra này. Thời lượng nói 15 phút vẫn cần người báo cáo đọc thử và bấm giờ thực tế; kiểm tra bằng văn bản không xác nhận được tốc độ nói của người trình bày.
