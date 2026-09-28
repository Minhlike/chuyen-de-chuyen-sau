# Nghiệm thu sao chép ký hiệu theo đúng đối tượng trong Word gốc

## Nguồn và phạm vi

- Chuẩn duy nhất cho ký hiệu: Word cũ tại commit `d7578872c9b101450ce1b1fcaa73f52dd1c97309`, giữ nguyên trong Downloads. DOCX SHA-256 `9bb11639807081f6ee3dafa8907f5293913ffec5697b945993b905ad93a67033`; PDF SHA-256 `087f1a69721b063fad07362ea184974143c4822d293d67db4ade6906754ce302`.
- STARTING_HEAD xưởng: `73949750e112e03ef81c045729652c2ba06ffba0`; branch mới: `codex/omml-object-bound-symbols`.
- STARTING_HEAD xuất xưởng: `2dd5099ef8cfab0f6e37af7b2280d7ce19d08ce5`; branch phát hành: `codex/omml-object-bound-release`.
- DOCX/PDF xuất xưởng trước đợt này: `4e9b4f00b9c424dbdfa991d0c58b2538f8928e4826c0de8d164e8991994c672c` và `a1cd62ac6e15a6d507add775241b7a473a9e8a04c5ce92b39e4e97eefb05ea1c`.
- Chỉ sửa chú giải Chương 1–2. Văn bản và công thức Chương 3 giữ nguyên so với bản nền. Công việc có sẵn tại checkout chính D:\Research được giữ nguyên.

## Nguyên nhân và cách sửa

Cách chọn mẫu trước đây tìm ký hiệu theo chữ cái và khoảng cách tới công thức, nên có thể lấy kiểu chữ của đối tượng khác. Đợt này bỏ cách chọn đó: mỗi ký hiệu được gắn với công thức định nghĩa đúng đối tượng, vị trí XML và hash của OMML nguồn trong Word gốc. Chú giải sao chép cấu trúc OMML đã chỉ định, gồm font, kiểu chữ, chỉ số trên/dưới và ký tự gốc. Không coi hai glyph cùng chữ cái là tương đương.

- Hồ sơ cố định `OMML-OBJECT-SYMBOL-BINDINGS.json` có 239 biểu thức trong 45 chú giải. `OMML-TYPOGRAPHY-SOURCE-MAP.json` ghi 285 lần sao chép từ nguồn.
- Biểu thức có nhiều đối tượng được tách đoạn chữ toán để giữ kiểu chữ của từng thành phần. Chỉ số số trong ví dụ được lấy từ họ ký hiệu gốc, chỉ thay giá trị chỉ số cần thiết.
- Tên hàm trong chú giải cũng dùng OMML nguồn. Update của trạng thái dòng và Update của nút đồ thị được lấy từ công thức riêng của từng đối tượng.
- Nhãn là **“Ví dụ”**. Giá trị giả định được mô tả là phép tính phục vụ giải thích, không viết như kết quả nghiên cứu.
- Những biến thể tồn tại trong bản gốc được giữ theo đúng công thức tương ứng; không áp đặt một kiểu chữ chung lên toàn tài liệu.
- Giữ hai sửa toán học từ đợt trước: mẫu số `L_MPP` đếm khe tham số hợp lệ; đầu hồi quy `L_time` nhận cặp trạng thái phù hợp chiều đầu vào đã công bố. Chứng cứ: `OMML-CLARITY-REPAIR-MATH-CORRECTIONS.json`. Đợt này có **0 sửa toán học gốc mới**.

## Trước → sau tiêu biểu

1. Ma trận A và ma trận đơn vị I bị mượn kiểu script của tập hành động/giao diện → A và I đúng kiểu công thức Invariant Mining/PCA gốc.
2. x trong Retain(x), Normalize(x) bị lấy kiểu đậm của vector nhúng → x đúng kiểu trường tham số gốc; vector nhúng x có chỉ số ở phần khác vẫn đậm theo nguồn của chính nó.
3. S trong chú giải trạng thái dòng → đúng kiểu script và chỉ số gốc; S ở ràng buộc thông tin lối tắt giữ kiểu riêng theo nguồn.
4. Ký hiệu không trong Ax=0 → đúng vector không đậm của phương trình gốc, kể cả khi đứng riêng trong lời giải.
5. Chỉ số cửa sổ lịch sử l thường → L hoa như nguồn; T của phép biến đổi được phân biệt với tập mẫu T kiểu script.

## Kiểm kê và số lượng

- Bản nền có 555 OMML Chương 1–2: Chương 1 có 30, Chương 2 có 525; gồm inline và trong bảng. Hồ sơ: `OMML-CLARITY-BASELINE-INVENTORY.json`.
- Có 45 chú giải theo nhóm, trực tiếp đặt gần 304 vùng công thức; ký hiệu lặp khác dùng định nghĩa sẵn ở văn cảnh gần đó. Không phải 555 chú giải riêng.
- Thêm 239 OMML: 141 vùng cấu trúc toán và 98 vùng ký hiệu/đẳng thức ngắn. Tổng DOCX: 622 → 861; Chương 1 có 109, Chương 2 có 685, Chương 3 vẫn 67.
- Kiểm tra 239 OMML mới và 599 đoạn chữ toán sau Word lưu. Có 31 phép tính ví dụ được kiểm tra số học. Không chuyển phương trình thành ảnh hoặc chữ giả phương trình.

## Cổng QA tại xưởng

| Cổng | Kết quả | Chứng cứ |
|---|---|---|
| Phép tính ví dụ | PASS, 31 kiểm tra | `OMML-CLARITY-REPAIR-NUMERIC-QA.json` |
| Đối tượng, font và chỉ số | PASS, 45 chú giải / 239 vùng / 599 đoạn chữ toán | `OMML-TYPOGRAPHY-REPAIR-QA.json`, hồ sơ cố định và bản đồ sao chép |
| OMML/OOXML trước Word | PASS, 620 vùng gốc ngoài hai sửa đã ghi nhận giữ XML/thứ tự | `OMML-TYPOGRAPHY-REPAIR-QA-PREWORD.json` |
| Word COM | PASS, mở không dùng sửa file, cập nhật trường, phân trang, lưu, xuất PDF/A, đóng/mở lại | `OMML-CLARITY-REPAIR-WORD-COM-QA.json` |
| DOCX/PDF cuối | PASS, 861 OMML; ZIP/XML/relationships/fields/bookmarks/font nhúng | `OMML-CLARITY-REPAIR-QA-RELEASE.json` |
| Bố cục | PASS, rà 84 trang Chương 1–2; 45 chú giải không cắt trang | `OMML-CLARITY-REPAIR-LAYOUT-QA.json`, `OMML-CLARITY-REPAIR-PAGINATION-QA.json` |
| Chương 3 | PASS, văn bản và công thức trùng bản nền | `OMML-CLARITY-REPAIR-QA-RELEASE.json` |

DOCX cuối SHA-256: `4f4f2b55f8e4cb632d358fc695a0bb72e0a628a3b3402fbd7cbca167acd97054`.

PDF cuối SHA-256: `684c59e99246be3dfb1e49de71c5b2911ef4c3d38471daafa5afee05ef1ad643` (129 trang).

Giữ 186 citation fields, 114 bookmarks, 11 hình, 9 thành phần font nhúng DOCX. TOC, danh mục hình/bảng và bibliography còn nguyên; metadata gốc được giữ. Chương 3 có hash văn bản `ddf20d1f4927a6f39ebd33804e80d891178a2df5a02e40ccd549519e7465c96b` ở cả bản nền và bản cuối.

Giới hạn kiểm chứng: chưa chạy bộ kiểm chứng chuẩn PDF/A độc lập; đã kiểm tra cấu hình xuất Word, metadata PDF/A-1a, output intent và font nhúng. `render_docx.py` thiếu soffice.exe trong Windows này; kết xuất/mở lại bằng Word COM và kiểm tra hình bằng PDFium. Thống kê trang Word ngay sau mở lại có thể sai; số trang nghiệm thu lấy từ PDF thực tế, 129 trang. Chỉ nghiệm thu xuất xưởng sau kiểm tra trực tiếp file đã đồng bộ.

## Nghiệm thu trực tiếp bản xuất xưởng

- DOCX/PDF tại D:\chuyen-de-chuyen-sau trùng hash bản xưởng đã nghiệm thu. QA OMML/OOXML, kiểu chữ và nguồn theo đối tượng: PASS.
- Microsoft Word mở trực tiếp DOCX xuất xưởng không dùng sửa file; 827 vùng toán theo phạm vi Word COM, 386 trường. Xuất lại PDF 129 trang; văn bản cả 129 trang trùng PDF phát hành.
- Bản Word/PDF gốc trong Downloads giữ nguyên SHA-256. Chương 3 giữ nội dung và công thức.
- FINAL_HEAD xưởng đã push: `4e401094044824facd6fa9740c813b32b6e5acea`. Commit phát hành xuất xưởng là commit chứa báo cáo này; SHA được ghi trong kết quả bàn giao và lịch sử Git.
- Chứng cứ trực tiếp: `OMML-CLARITY-RELEASE-QA.json`; nguồn, hash và danh sách file: `OMML-CLARITY-RELEASE-PROVENANCE.json`.
