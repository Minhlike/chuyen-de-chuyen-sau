# Nghiệm thu chỉnh sửa hình thức có kiểm soát

Ngày: 2026-09-29. Kết quả các cổng nghiệm thu trong yêu cầu: PASS.

## Baseline và phạm vi

- Dùng chính Word hiện tại tại `D:\chuyen-de-chuyen-sau`, SHA-256 `d29077dbecb3fff58b417734e0b19e49d271c34750b361c89f534b6d6d15c319`; không lấy bản Git cũ ghi đè.
- PDF baseline: `649b63d107276d8b1123397d2d2e01c2c7fa6cce010ee5e2fe7e222244d903f1`.
- HEAD xuất xưởng ban đầu: `ad32ebe2ec9a22c9cb78feb7ad2e79ed489f5721`, trùng remote main. HEAD worktree xưởng ban đầu: `52447775a12bf1497425606cb5bfca773dd98723`.
- Branch xưởng: `codex/controlled-thesis-formatting`. Remote main xưởng vẫn là `a99d5dc0e1499f8454293a2931a4962ad214d4af`; giữ nguyên checkout chính và công việc chưa theo dõi ở `D:\Research`.
- Backup nguyên trạng DOCX/PDF: `C:\Users\Acer\Downloads\chuyen-de-chuyen-sau-before-controlled-formatting-2026-09-29`.

## Vị trí sửa và lý do hình thức

| Vị trí | Thay đổi có kiểm soát |
| --- | --- |
| Lời nói đầu, 11 đoạn prose đầu | Times New Roman 14 pt, line spacing 1.5; giữ nguyên chữ, indent, căn lề và cấu trúc đoạn |
| 2.2.1, đoạn giải thích tokenize_line | Prose 13 → 14 pt, line spacing 1.3 → 1.5 |
| 2.3.1, đoạn giải thích mất mát đa khe sau Đoạn mã 2.2 | Cùng sửa font/spacing prose |
| 2.3.2, đoạn giải thích reset_node_states sau Đoạn mã 2.3 | Cùng sửa font/spacing prose |
| 2.4.4, đoạn giải thích GatedMultiViewFusion sau Đoạn mã 2.4 | Cùng sửa font/spacing prose |
| 3.1.1–3.1.3, bốn đoạn giải thích dưới các đoạn mã | Cùng sửa font/spacing prose; không tăng font code hoặc caption |
| 3.2.4, ba đoạn mô tả tái lập thủ công và kết quả | Cùng sửa font/spacing prose; không đổi dữ liệu, mã run, commit hoặc kết quả |
| Đoạn giải thích dưới Hình 3.1 | Cùng sửa font/spacing prose; chuyển tham chiếu hình thành REF native |
| Caption Hình 3.1 | Sao chép pPr/rPr của Hình 2.4: Caption, TNR 14 pt, đậm, căn giữa, Before 6 pt / After 12 pt; native SEQ Hình bắt đầu lại tại 1, bookmark nhãn và bookmark danh mục |
| Danh mục hình | Thêm Hình 3.1 bên trong field TOC danh mục hiện có, hyperlink và PAGEREF native |
| Bốn caption đoạn mã Chương 3 | Theo thứ tự: SHA-256 → 3.1; chia dữ liệu → 3.2; đầu dò tuyến tính → 3.3; AP/ROC-AUC → 3.4. Dùng SEQ ĐoạnMã; giữ nguyên mô tả caption và code |
| Bảng 3.3 | Giữ grid/cỡ font 10.5 pt; padding ngang mỗi ô 6 → 1.8 pt. Epoch và các số thập phân không còn bị bẻ |
| Bảng 3.7b, 3.8 cũ, 3.9 cũ | Lần lượt thành 3.8, 3.9, 3.10; native SEQ, bookmark, danh mục và năm tham chiếu prose cập nhật đúng đối tượng |
| Danh mục bảng | Chỉ tại 17 entry: line spacing 1.5 → 1.4, Before/After 0, giữ font 11 pt. Toàn bộ danh mục vừa một trang |

Điều chỉnh phân trang cần thiết: chuyển field end của danh mục bảng vào entry cuối và bỏ đoạn đóng field trống có spacing thừa; field vẫn cân bằng, section break giữ nguyên. Để tránh lỗi phát sinh sau tăng font prose, giữ header Bảng 3.8 cùng dòng dữ liệu đầu và giữ toàn bộ caption Hình 3.1 cùng ảnh. Không đổi kích thước ảnh hay font/nội dung bảng.

## Các khác biệt chủ động giữ nguyên

- 32 tiêu đề Heading4 trực tiếp 13 pt ở Chương 2 là tiêu đề, không phải body prose.
- Bảng chính sách Chương 2 đang dùng 13 pt, các bảng/metadata, code, caption đoạn mã 10 pt và toàn bộ công thức giữ định dạng riêng.
- Không chuẩn hóa toàn tài liệu. Toàn bộ Chương 1 giữ nguyên XML, kể cả mọi bullet người dùng đã chỉnh.
- Các hình/bảng ngoài hai bảng được nêu và điểm phân trang liên quan không đổi XML. Tất cả ảnh/hình giữ nguyên; không đổi Representation Contract, H1–H5, ER1 hoặc kết luận khoa học.
- Trang trắng PDF số 3 đã có trong baseline trước phần mục lục được giữ nguyên vì ngoài phạm vi. Không tạo trang trắng mới.

## Field, caption và tham chiếu

| Loại field | Trước | Sau |
| --- | ---: | ---: |
| CITATION | 186 | 186 |
| BIBLIOGRAPHY | 1 | 1 |
| TOC | 3 | 3 |
| SEQ | 24 | 30 |
| REF | 8 | 14 |
| PAGEREF | 82 | 83 |

- Thay đổi 8 caption: 4 đoạn mã, 3 bảng và 1 hình. Ba nhãn bảng trong danh mục được đổi, một entry hình được thêm.
- Thêm 6 SEQ, 6 REF và 1 PAGEREF; giữ 8 REF gốc. Hai kết quả SEQ bảng gốc đổi 8 → 9 và 9 → 10.
- Cập nhật 78 kết quả PAGEREF sau phân trang. Kiểm tra toàn bộ 83 PAGEREF khớp bookmark và trang do Word tính; giữ cách ghi số La Mã ở phần đầu.
- Đổi ba tên bookmark liên quan: BK_TBL_3_008 → BK_TBL_3_009, BK_TBL_3_009 → BK_TBL_3_010, _Toc_B37b → _TocCF_Table38. Tạo BK_TBL_3_008 cho đúng bảng mới. Các định danh TOC không chứa số bảng vẫn theo đúng đối tượng cũ.
- Word kiểm tra thành công 15 SEQ caption: 10 bảng, 4 đoạn mã, 1 hình ở Chương 3. Không còn 3.7b hoặc tham chiếu prose gắn nhầm đối tượng.

## Bằng chứng nghiệm thu

- SHA XML toàn Chương 1 trước/sau cùng là `205f56de4723b630b85b00e31171b65e8261eec13df9e40f4bebc07d86cb5985`. Bullet glyph, indentation, numbering, paragraph style, spacing và cấu trúc nguyên trạng.
- Chương 2 chỉ khác XML tại đúng bốn đoạn prose đã liệt kê; không sửa các vùng khác.
- 861 OMML nguyên XML và thứ tự. Nội dung tất cả bảng, số liệu thực nghiệm và code giữ nguyên. Các field CITATION/BIBLIOGRAPHY giữ code và kết quả hiển thị.
- Chỉ `word/document.xml` khác baseline; styles, numbering, relationships, font, hình nhúng, header/footer, metadata giữ nguyên byte. ZIP/XML/relationships/bookmark/field stack PASS.
- Microsoft Word COM mở với OpenAndRepair=False, kiểm tra SEQ/REF, phân trang, xuất PDF và mở lại bản cuối PASS. Word chỉ đọc và không lưu lại DOCX để tránh tự viết lại cấu trúc bullet.
- PDF cuối 130 trang, font nhúng PASS; kiểm tra toàn tài liệu không glyph vượt trang hoặc trang trắng mới. Đã rà trực quan 52 trang liên quan, gồm toàn Chương 3 đến hết References và các trang prose/đầu tài liệu bị tác động.
- Danh mục hình: trang PDF 9; danh mục bảng: trang 10, đầy đủ đến Bảng 3.10. Bảng 3.3: trang 107, toàn bộ giá trị thập phân nguyên dòng, gồm 0.0887/0.4407/0.0857/0.6771/0.0867/0.2050. Bảng 3.8: trang 115; ảnh và toàn caption Hình 3.1: trang 116.
- Xuất bằng thiết lập PDF/A của Word và kiểm tra nhúng font; không tuyên bố có kiểm định PDF/A độc lập.

## SHA-256 cuối

- DOCX: `a8d225253a83965050a0efd5843b20b0ebecea5df3954d9ecad12d9274e48d71`.
- PDF: `8c36df58cd16c85ad0c1ea9697603d7db370c98410d8d82fe95e8435b185508c`.

Các JSON đi kèm ghi từng thay đổi, phân trang, Word COM, QA cấu trúc và các trang rà bố cục. Repo xuất xưởng chỉ nhận DOCX/PDF và báo cáo phát hành cần thiết; không nhận script, ảnh rà hoặc tệp tạm.

## Nghiệm thu trực tiếp repo xuất xưởng

Mở lại chính DOCX tại `D:\chuyen-de-chuyen-sau` bằng Word COM PASS. Xuất PDF kiểm tra riêng; toàn bộ 130 trang giữ nguyên chữ và ngắt dòng so với PDF phát hành. Hash DOCX sau mở lại không đổi. QA XML/bullet/OMML/số liệu/citation và 83 PAGEREF chạy lại trực tiếp trên bản xuất xưởng PASS.

Commit xưởng đã push: `9552c0215180328756798d5064a0078fb6c3406c`. Branch xuất xưởng: `codex/controlled-thesis-formatting-release`. Commit xuất xưởng là commit chứa báo cáo này; tra bằng lịch sử Git của báo cáo.
