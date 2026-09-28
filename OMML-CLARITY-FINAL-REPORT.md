# Nghiệm thu sửa kiểu chữ và chỉ số công thức Chương 1–2

## Nguồn và phạm vi

- Chuẩn công thức: bản Word cũ tại commit `d7578872c9b101450ce1b1fcaa73f52dd1c97309`, giữ trong Downloads. DOCX SHA-256 `9bb11639807081f6ee3dafa8907f5293913ffec5697b945993b905ad93a67033`; PDF SHA-256 `087f1a69721b063fad07362ea184974143c4822d293d67db4ade6906754ce302`.
- HEAD xưởng khi bắt đầu sửa kiểu chữ: `b881f7cba1bd65680ac332982f1b10784c780cad`. Branch: `codex/omml-typography-exact-repair`. HEAD xuất xưởng trước đồng bộ: `302a6a80c2b4c656d97c032808975b5bc6c7456d`.
- DOCX/PDF xuất xưởng trước đợt này: `f9d212a5d957cbc0e6eeca019894d991e7141bbb0860ab28fda343e2e4b85c7e` và `e783de4bbb53a9c69a7b9aa0d9f4522482c7d29e480a9a67fa1ddfaf61da7356`.
- Chỉ sửa chú giải Chương 1–2. Văn bản và công thức Chương 3 giữ nguyên so với bản nền.

## Sửa nguyên nhân

Trước đây, một số ký hiệu trong chú giải là chữ thường kèm ký tự Unicode giả chỉ số; một số biểu thức OMML mới chưa dùng đúng kiểu chữ toán và vị trí chỉ số của công thức gốc. Đợt này lấy trực tiếp cấu trúc ký hiệu từ OMML của bản Word cũ, gồm font, chữ toán dạng script, đậm/nghiêng/đứng và chỉ số trên/dưới. Ký hiệu trong lời giải và phép thay số dùng OMML native, vẫn chỉnh sửa được trong Equation Editor.

- Rà toàn bộ 45 đoạn chú giải. Kiểm tra 225 vùng OMML mới và 566 đoạn chữ toán sau khi Word lưu; không còn ký hiệu giả chỉ số trong lời giải mới.
- Nhãn trong tài liệu là **“Ví dụ”**. Các giá trị ví dụ là giả định phục vụ giải thích, không phải kết quả thực nghiệm.
- Hai sửa toán học gốc từ đợt trước vẫn giữ: mẫu số `L_MPP` đếm khe tham số hợp lệ; đầu hồi quy `L_time` nhận cặp trạng thái phù hợp kích thước đã công bố. Chứng cứ: `OMML-CLARITY-REPAIR-MATH-CORRECTIONS.json`. Đợt kiểu chữ không sửa thêm công thức gốc.
- Giữ sửa bố cục từ đợt trước: bỏ ngắt trang cứng trước chú thích Bảng 2.4; tiêu đề bảng vẫn lặp khi sang trang. Các chú giải không bị cắt trang.

## Trước → sau tiêu biểu

1. Trạng thái bộ nhớ: chữ S với chỉ số Unicode trong chú giải → đúng chữ toán dạng script và chỉ số dưới như `S_t`, `S_{t-1}` trong công thức gốc.
2. Hàm biểu diễn: chữ `fθ` trong câu → OMML với θ ở chỉ số dưới, đúng ký hiệu `f_θ` gốc.
3. Trọng số dung hợp: `rel,seq` cùng nằm dưới → `rel` nằm dưới và `seq` nằm trên như công thức gốc.
4. PCGrad: `align,proj` cùng nằm dưới → `align` nằm dưới, `proj` nằm trên; kiểu chữ vector đậm lấy từ biểu thức gốc.
5. Nhãn ví dụ dài → **“Ví dụ”**; các phép thay số vẫn là OMML và được kiểm tra số học.

## Kiểm kê và số lượng

- Bản nền có 555 vùng OMML Chương 1–2: 30 ở Chương 1, 525 ở Chương 2; gồm vùng inline và trong bảng. Hồ sơ: `OMML-CLARITY-BASELINE-INVENTORY.json`.
- Có 45 chú giải theo nhóm, trực tiếp đặt gần 304 vùng công thức; các ký hiệu lặp còn lại dùng định nghĩa sẵn ở văn cảnh gần đó. Không phải 555 chú giải riêng.
- So với bản nền, thêm 225 vùng OMML: 121 vùng có cấu trúc toán và 104 vùng ký hiệu/đẳng thức ngắn. Tổng DOCX: 622 → 847; Chương 1 có 106, Chương 2 có 674, Chương 3 vẫn 67.
- 31 phép tính ví dụ đã kiểm tra. Có 2 sửa toán học gốc từ đợt trước, 0 sửa toán học gốc mới trong đợt kiểu chữ.

## Cổng QA tại xưởng

| Cổng | Kết quả | Chứng cứ |
|---|---|---|
| Phép tính ví dụ | PASS, 31 kiểm tra | `OMML-CLARITY-REPAIR-NUMERIC-QA.json` |
| Font, kiểu chữ toán, vị trí chỉ số | PASS, 45 chú giải / 225 vùng / 566 đoạn chữ toán | `OMML-TYPOGRAPHY-REPAIR-QA.json`, `OMML-TYPOGRAPHY-SOURCE-MAP.json` |
| OMML/OOXML trước Word | PASS, 620 vùng toán gốc không sửa giữ nguyên XML/thứ tự | `OMML-TYPOGRAPHY-REPAIR-QA-PREWORD.json` |
| Word COM | PASS, mở/lưu/cập nhật trường/xuất PDF/A/đóng/mở lại | `OMML-CLARITY-REPAIR-WORD-COM-QA.json` |
| DOCX/PDF cuối | PASS, 847 vùng OMML; ZIP/XML/relationships/fields/bookmarks/font nhúng | `OMML-CLARITY-REPAIR-QA-RELEASE.json` |
| Bố cục | PASS, rà 84 trang Chương 1–2; 45 chú giải không cắt trang | `OMML-CLARITY-REPAIR-LAYOUT-QA.json`, `OMML-CLARITY-REPAIR-PAGINATION-QA.json` |
| Chương 3 | PASS, văn bản và công thức trùng bản nền | `OMML-CLARITY-REPAIR-QA-RELEASE.json` |

DOCX cuối SHA-256: `4e9b4f00b9c424dbdfa991d0c58b2538f8928e4826c0de8d164e8991994c672c`.

PDF cuối SHA-256: `a1cd62ac6e15a6d507add775241b7a473a9e8a04c5ce92b39e4e97eefb05ea1c` (129 trang).

Citations giữ 186 trường; bookmarks giữ 114; hình giữ 11; thành phần font nhúng DOCX giữ 9. TOC, danh mục hình/bảng và bibliography còn nguyên. Metadata gốc được giữ.

Giới hạn: `render_docx.py` không chạy được vì Windows này thiếu `soffice.exe`; đã kết xuất bằng Microsoft Word COM và rà PDF qua PDFium. Kiểm tra PDF/A xác nhận cấu hình xuất Word, metadata PDF/A-1a, output intent và font nhúng; chưa chạy bộ kiểm chứng chuẩn PDF/A độc lập. Đã kiểm tra trực tiếp và nghiệm thu các file trong repo xuất xưởng như ghi ở phần dưới.

## Nghiệm thu trực tiếp bản xuất xưởng

- Branch phát hành: `codex/omml-typography-exact-release`; HEAD trước sửa `302a6a80c2b4c656d97c032808975b5bc6c7456d`.
- Commit xưởng đã push: `73949750e112e03ef81c045729652c2ba06ffba0` trên branch `codex/omml-typography-exact-repair`.
- File DOCX/PDF trong repo xuất xưởng trùng byte và SHA-256 với bản xưởng đã nghiệm thu.
- Kiểm tra trực tiếp DOCX/PDF xuất xưởng: OMML/OOXML/font/kiểu chữ toán/chỉ số/citations/Chương 3 đều PASS. Chi tiết nằm trong `OMML-CLARITY-RELEASE-QA.json`.
- Mở chính DOCX xuất xưởng bằng Microsoft Word ở chế độ chỉ đọc, không yêu cầu repair: PASS, 813 đối tượng toán theo Word và 386 fields. Số vùng XML là 847 vì Word và XML đếm phạm vi đối tượng khác nhau.
- Xuất lại bằng Word được PDF 129 trang. Văn bản trích xuất của cả 129 trang trùng PDF phát hành.
- Bản Word cũ trong Downloads vẫn giữ nguyên SHA-256. Repo xuất xưởng chỉ nhận DOCX, PDF và ba báo cáo phát hành; các script, ảnh rà trang và log nội bộ giữ ở xưởng.
- HEAD phát hành là commit chứa báo cáo này, xem lịch sử Git của repo xuất xưởng; SHA của chính commit không ghi vào file thuộc commit đó để tránh tham chiếu vòng.
