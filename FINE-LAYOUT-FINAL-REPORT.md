# Nghiệm thu QA hình thức tinh

Ngày: 2026-09-29. Các cổng nghiệm thu theo phạm vi yêu cầu: **PASS**. Hai candidate REVIEW giữ nguyên, không tự sửa.

## Baseline và quy trình

- Bản Word/PDF hiện tại từ `D:\chuyen-de-chuyen-sau`, HEAD `441866d323baa73f876109fdfda5d391dec3181c`, trùng remote main khi bắt đầu. Không checkout bản Word cũ.
- HEAD checkout chính xưởng: `cb6b30028501690c8b7dc70f8e72f78a68ce38f0`; HEAD worktree xưởng ban đầu: `9552c0215180328756798d5064a0078fb6c3406c`. Giữ nguyên công việc và file chưa theo dõi ở checkout chính.
- Branch xưởng: `codex/fine-thesis-layout-qa`; branch xuất xưởng: `codex/fine-thesis-layout-release`.
- Backup nguyên trạng: `C:\Users\Acer\Downloads\Chuyen-de-before-fine-layout-QA-2026-09-29`.
- Kiểm kê và phân loại trước sửa; các candidate phát sinh sau phân trang cũng được ghi trước khi chỉnh. Chỉ sửa nhóm FIX. Tận dụng các bộ đọc/ghi OOXML và Word COM đang có.

## FIX: 14 nhóm, 21 đoạn được chỉnh pagination cục bộ

Các số trang dưới đây là số trang vật lý PDF; vị trí mục là định danh nội dung.

| ID | Vị trí | Thay đổi và kết quả |
| --- | --- | --- |
| F01 | Đoạn trống mang section break sau hai bìa | Tắt pageBreakBefore/keepNext kế thừa từ style Mục lục. Trang trắng 3 dư được loại; cả ba section là New Page, không Odd/Even. Giữ nguyên section XML, hệ số trang, hai bìa và font/spacing |
| F02 | 2.1.3 / Hình 2.1 | Bỏ pageBreakBefore trực tiếp trên đoạn ảnh; ảnh/caption nay đi cùng phần dẫn trên trang 49, bỏ lỗ trắng lớn ở trang 50 cũ |
| F03 | 1.1.3 / Hợp đồng Biểu diễn | Keep with next công thức với phần đọc ba điều kiện; xem trang 21 |
| F04 | 1.2.1 / phép chiếu phần dư PCA | Giữ công thức với định nghĩa và ví dụ; xem trang 28 |
| F05 | 2.1.1 / H2 | Giữ công thức ràng buộc với chú giải; xem trang 45 |
| F06 | 2.3.1.3 / tổng hợp chú ý | Giữ cặp alpha/z_seq với chú giải; xem trang 67 |
| F07 | 2.4.1.2 / hai đầu chiếu | Giữ p_seq/p_graph cùng nhau và với chú giải; xem trang 79 |
| F08 | 2.4.3.2 / mục tiêu Stage A | Giữ công thức tổng hợp với chú giải/phép thay số; xem trang 89 |
| F09 | 2.4.4.1 / vector dung hợp | Giữ công thức với chú giải Hadamard; xem trang 94 |
| F10 | Câu dẫn ngắn trước mục tiêu Stage A | Giữ câu dẫn kết thúc bằng dấu hai chấm với công thức; xem trang 89 |
| F11 | 2.1.2 / watermark | Giữ công thức với định nghĩa/ví dụ; xem trang 48 |
| F12 | 2.2.1.2 / Retain và Normalize | Giữ cặp công thức với chú giải; xem trang 52 |
| F13 | 2.4.3.3 / tính điểm và trọng số dung hợp | Chỉ giữ s/w với chú giải/phép thay số ở trang 90. Vector q vẫn đi cùng câu dẫn ở trang 89. Bỏ phương án nối toàn cụm sau thử PDF vì tạo khoảng trắng quá lớn |
| F14 | 2.4.3.4 / Attention-MIL | Giữ bốn phương trình phụ thuộc nhau với chú giải ở trang 92 |

Không thay font, cỡ chữ, spacing thân bài, độ rộng cột, kích thước hình hoặc nội dung công thức. Các công thức chỉ nhận keepNext ở cấp đoạn bên ngoài OMML.

## KEEP: 8 nhóm

1. **Heading 1–4:** 82 heading không tách khỏi đoạn đầu. Giữ style và thiết lập hiện hành.
2. **Khoảng trắng hợp lý:** đuôi danh mục/đầu chương, đoạn cuối Chương 1–2, khối hình-caption, trang cuối References. Các trang 8/9/14/16/41/98/115/126/130 cũ không bị ép nén. Phần trống trước khối công thức-chú giải vừa một trang được giữ khi cần để đọc liền mạch.
3. **Caption và bảng dài:** đã giữ cùng phần đầu đối tượng; header lặp và cantSplit của hàng dữ liệu đối chiếu XML/PDF. Cho phép bảng qua trang.
4. **Prose/list tách 2+ dòng:** widow control đang bật; không phát hiện dòng đơn cô độc. Chú giải message passing chia 2+2 dòng giữ nguyên để tránh chuỗi keep quá dài.
5. **Mục lục/danh mục:** dấu chấm dẫn, số trang, font và spacing đã phù hợp. Chỉ cập nhật cache trang; danh mục bảng vẫn một trang.
6. **Bảng 3.3 và các bảng kết quả:** Epoch, seed và số thập phân nguyên vẹn. Không chỉnh cột/padding thêm.
7. **Mất mát quan hệ cuối trang 105 cũ:** công thức trọn vẹn cùng phần dẫn; đầu trang tiếp theo là mất mát khác, không phải chú giải bị tách.
8. **Font riêng theo vai trò:** code, caption code, Heading4, bảng và metadata giữ nguyên.

## REVIEW: 2 nhóm giữ nguyên

- **Bảng 3.8, mã SHA-256 checkpoint 64 ký tự:** đầy đủ trong cùng ô/hàng nhưng xuống hai dòng. Giữ một dòng cần mở rộng cột đáng kể hoặc giảm font; chưa sửa vì có nguy cơ phá bố cục bảng.
- **Hai bìa trang 1–2:** gần giống nhau, chưa có bằng chứng một bìa là dư. Giữ cả hai. Render hai bìa trùng hoàn toàn trước/sau.

## QA và đối chiếu

- PDF **130 → 128 trang**. Trang trắng 3 dư bị loại; bỏ ngắt trang thừa trước Hình 2.1 giảm thêm một trang. Không có trang trắng mới, clipping hoặc overflow mới được phát hiện.
- Rà trực quan toàn bộ 130 trang trước và 128 trang sau, đối chiếu riêng các vùng FIX. Render sản phẩm cuối trùng 128/128 trang với vòng đã rà. Chương 3 đến References giữ bố cục: 20 trang trùng pixel thân trang, 12 trang chỉ khác tối đa 0,302% pixel chữ khi bỏ vùng số trang; đã đối chiếu trực quan.
- Word COM mở với OpenAndRepair=False, repaginate, resolve **14 REF / 30 SEQ / 83 PAGEREF**, xuất PDF, đóng và mở lại bản cuối PASS. **82 heading** và **34 caption** không treo/tách đối tượng. Tổng Word Fields=400; Word OMaths=827 khác đơn vị đếm XML oMath=861, cả hai giữ nguyên so với baseline.
- Word chỉ đọc, cập nhật field trong bộ nhớ và không Save DOCX để bảo toàn XML bullet. **46 cache PAGEREF** được cập nhật có kiểm soát; 83/83 khớp trang bookmark do Word tính. Không tái tạo TOC/LOF/LOT hoặc đổi label/caption.
- Mục lục trang 3–4; danh mục hình trang 8 (9 hình); danh mục bảng trang 9 (17 bảng, đủ đến 3.10). Các dấu chấm dẫn/số trang thẳng hàng. Hình 3.1 ở trang 114, Bảng 3.3 ở trang 105.
- **861 OMML** nguyên XML và thứ tự; **186 CITATION** nguyên code/kết quả. CITATION/BIBLIOGRAPHY/REF/SEQ không thay đổi. Field stack, ZIP/XML, relationships và bookmark PASS.
- Bullet Chương 1 nguyên XML: glyph, indent, numbering, style, spacing, cấu trúc. Toàn bộ Chương 3 nguyên XML. Nội dung khoa học, claim, số liệu, code, bảng, hình, styles, numbering, section, header/footer, metadata, font và media giữ nguyên.
- Chỉ `word/document.xml` khác; sau phục hồi đúng 21 pPr được phép và cache PAGEREF, toàn document.xml trùng baseline theo C14N. Mọi ZIP part khác trùng byte.
- Font PDF nhúng PASS. Xuất bằng thiết lập PDF/A của Word; không tuyên bố có kiểm định PDF/A độc lập.
- COM không đọc được Rows collection ở các bảng này; không dùng lỗi đó làm bằng chứng. Header/cantSplit xác nhận bằng XML và PDF. Một lượt COM đồng thời bị kẹt đã được dừng bằng đúng PID automation; mọi lượt cuối chạy tuần tự và PASS, không ghi lại nguồn bằng Word.

## SHA-256

| Tệp | Trước | Sau |
| --- | --- | --- |
| DOCX | `a8d225253a83965050a0efd5843b20b0ebecea5df3954d9ecad12d9274e48d71` | `cc314001a1770f9c3e87f05a170c2913511956b8ee2732ff88184587e79f81cf` |
| PDF | `8c36df58cd16c85ad0c1ea9697603d7db370c98410d8d82fe95e8435b185508c` | `0df209c1d95037e18b97a52e4c278bb0442693d8322114861d645323505e1f85` |

JSON đi kèm ghi candidate, thay đổi, cache trang, QA cấu trúc, Word COM, bố cục và provenance. Repo xuất xưởng chỉ nhận DOCX/PDF và báo cáo phát hành cần thiết; không nhận script hoặc ảnh rà/tệp tạm.

## Kiểm tra trực tiếp bản xuất xưởng

- Microsoft Word mở chính DOCX tại `D:\chuyen-de-chuyen-sau` với OpenAndRepair=False; 14 REF / 30 SEQ / 83 PAGEREF resolve PASS.
- QA ZIP/XML, bullet, 861 OMML, 186 citation và hash chạy lại trên chính gói xuất xưởng PASS.
- Word xuất lại PDF từ chính DOCX xuất xưởng: render **128/128 trang trùng pixel** với PDF đã rà và bàn giao. Không thay PDF đã nghiệm thu bằng tệp xuất lại chỉ khác metadata.
- DOCX/PDF xuất xưởng trùng byte với sản phẩm xưởng. Không đồng bộ script, ảnh rà, tệp tạm hoặc log nội bộ.
- Commit xưởng đã push: `ed85545bc8ade93283d0e13861e4a5482cacecc1`.
