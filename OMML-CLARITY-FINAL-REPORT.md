# Nghiệm thu sửa chú giải công thức Chương 1–2

## Nguồn và phạm vi

- Bản nền là DOCX trước đợt sửa OMML lỗi, lấy từ commit `d7578872c9b101450ce1b1fcaa73f52dd1c97309` của repo xuất xưởng. SHA-256: `9bb11639807081f6ee3dafa8907f5293913ffec5697b945993b905ad93a67033`.
- Bản nền PDF SHA-256: `087f1a69721b063fad07362ea184974143c4822d293d67db4ade6906754ce302`.
- Branch xưởng: `codex/omml-clarity-repair`, bắt đầu từ `cb6b30028501690c8b7dc70f8e72f78a68ce38f0`.
- Chỉ chú giải công thức Chương 1–2. Nội dung và thứ tự Chương 3, biểu thức gốc còn lại, citation fields, bookmarks, hình và các thành phần ZIP khác được đối chiếu với bản nền.

## Kết quả sửa

- Kiểm kê 555 vùng OMML ở Chương 1–2, kể cả biểu thức inline và trong bảng; 30 ở Chương 1, 525 ở Chương 2. Mỗi bản ghi có vị trí, biểu thức, ký hiệu, độ khó, nguy cơ diễn giải sai và văn cảnh. Nhiều vùng là ký hiệu lặp lại trong đoạn/bảng/hình; 45 chú giải theo nhóm được đặt gần các cụm công thức thay vì lặp 555 lần.
- Thêm 45 đoạn chú giải, 31 phép tính minh họa được kiểm tra số học, và 77 vùng OMML mới. Trong 77 vùng này, 69 có cấu trúc phân số/chỉ số/căn/tổng hoặc cấu trúc toán học khác; 8 vùng ngắn là đẳng thức/bất đẳng thức đơn giản trong `m:oMath`. Không có phép thay số nào chuyển thành ảnh hoặc LaTeX dạng chữ.
- Hai công thức gốc được sửa có ghi lý do và chứng cứ riêng trong `OMML-CLARITY-REPAIR-MATH-CORRECTIONS.json`: mẫu số `L_MPP` đếm khe tham số hợp lệ, và đầu hồi quy `L_time` nhận cặp trạng thái có kích thước đã công bố. Không thay đổi kết quả thực nghiệm hoặc claim an ninh.
- Bỏ duy nhất ngắt trang cứng trước chú thích Bảng 2.4 vì sau khi thêm chú giải nó tạo một trang gần trống. Bảng còn tiêu đề lặp ở trang kế tiếp.

## Mẫu trước → sau

1. **Entropy:** trước chỉ có công thức và diễn giải ngắn; sau định nghĩa cửa sổ, tỷ lệ, trường hợp `0 log 0`, thay số `A,A,B,B → 1 bit`, đối chiếu trường hợp một loại `→ 0`, và nói rõ entropy không tự xác nhận tấn công.
2. **TF-IDF:** sau phân biệt số cửa sổ tham chiếu `N` với số cửa sổ chứa một loại `n(eᵢ)`, thay `N=10`, `n(A)=2`, `n(B)=10`, rồi giải thích loại hiếm chỉ tăng trọng số thống kê.
3. **PCA:** sau nêu các cột trực chuẩn của `P`, vector đã tâm hóa, phép chiếu còn dư, thay vector hai chiều để có `‖xₐ‖²=4` và đối chiếu ngưỡng minh họa 3; cờ lệch không xác nhận nguyên nhân độc hại.
4. **VICReg:** sau nêu kích thước ma trận, điều kiện `B≥2`, tính phương sai và hiệp phương sai trên lô hai mẫu, và giới hạn rằng giảm tương quan tuyến tính không chứng minh độc lập thống kê.
5. **PCGrad:** sau thay hai gradient `(1,−1)` và `(−1,0)`, chỉ ra phép chiếu cho `(0,−1)` và tích mới bằng 0; một bước chiếu không bảo đảm cả hai mục tiêu cùng cải thiện.

## Cổng QA tại xưởng

| Cổng | Kết quả | Chứng cứ |
|---|---|---|
| Phép tính ví dụ | PASS, 31 kiểm tra | `OMML-CLARITY-REPAIR-NUMERIC-QA.json` |
| OMML/OOXML trước Word | PASS, 622 → 699 vùng; 620 công thức gốc giữ nguyên thứ tự và XML | `OMML-CLARITY-REPAIR-QA-PREWORD.json` |
| Word COM | PASS, mở/lưu/xuất PDF/A/đóng/mở lại không repair | `OMML-CLARITY-REPAIR-WORD-COM-QA.json` |
| DOCX/PDF cuối | PASS, 699 vùng OMML, ZIP/XML/relationships/fields/bookmarks/fonts/PDF/A | `OMML-CLARITY-REPAIR-QA-RELEASE.json` |
| Bố cục | PASS, rà 84 trang Chương 1–2; 45 chú giải không cắt trang | `OMML-CLARITY-REPAIR-LAYOUT-QA.json`, `OMML-CLARITY-REPAIR-PAGINATION-QA.json` |
| Hồi quy Chương 3 | PASS, văn bản và công thức trùng bản nền | `OMML-CLARITY-REPAIR-QA-RELEASE.json` |

DOCX cuối SHA-256: `f9d212a5d957cbc0e6eeca019894d991e7141bbb0860ab28fda343e2e4b85c7e`. PDF cuối SHA-256: `e783de4bbb53a9c69a7b9aa0d9f4522482c7d29e480a9a67fa1ddfaf61da7356` (129 trang).

## Kiểm tra trên bản xuất xưởng

- Repo xuất xưởng bắt đầu đợt sửa này tại `360d85733ac38b63b629f3eaa275e8ab8c7ccad0`, branch phát hành `codex/omml-clarity-repair-release`.
- DOCX/PDF sau đồng bộ có SHA-256 trùng chính xác bản đã nghiệm thu trong repo xưởng. Kiểm tra trực tiếp `OMML-CLARITY-RELEASE-QA.json` đạt PASS cho OMML, OOXML, citations, bookmarks, font nhúng, PDF/A và Chương 3.
- Mở lại chính DOCX trong repo xuất xưởng bằng Microsoft Word ở chế độ chỉ đọc, không dùng chế độ repair. Word nhận 665 đối tượng toán và 386 fields; xuất lại PDF/A 129 trang. Văn bản trích xuất của cả 129 trang trùng PDF phát hành; byte PDF khác do dữ liệu phát sinh khi xuất.

Giới hạn của QA: kiểm kê 555 vùng theo ngữ cảnh nhóm, không tạo 555 chú giải riêng; các vùng lặp lại và chú thích trong bảng/hình dùng định nghĩa gần đó. Bộ kết xuất `render_docx.py` không chạy vì môi trường Windows này thiếu `soffice.exe`; đã dùng Microsoft Word COM và PDFium để kiểm tra trực quan.
