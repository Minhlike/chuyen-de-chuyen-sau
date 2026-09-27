# Hiệu chỉnh chú giải công thức OMML Chương 1–2

## Nguồn và phạm vi

- Repo xuất xưởng bắt đầu tại `d7578872c9b101450ce1b1fcaa73f52dd1c97309`; repo xưởng bắt đầu tại `cb6b30028501690c8b7dc70f8e72f78a68ce38f0`.
- Nhánh xưởng: `codex/omml-ch1-ch2-clarity`, commit đã push `77e4869f4d4cfad4950444ad02cb22d33c16e991`. Nhánh phát hành: `codex/omml-ch1-ch2-clarity-release`.
- Master DOCX gốc được lấy trực tiếp từ repo xuất xưởng, SHA-256 `9bb11639807081f6ee3dafa8907f5293913ffec5697b945993b905ad93a67033`; PDF gốc `087f1a69721b063fad07362ea184974143c4822d293d67db4ade6906754ce302`.
- DOCX cuối SHA-256 `93b8df9d8485b153b97cacb9025aeeca475d28c454299852131b7db06e0937c7`; PDF cuối `307154e3d4cdabf35f73dbd7e95666baa6dbffd3d70da74c2a2ffc0989b3883b`.

## Kết quả

Đã kiểm kê 555 vùng công thức OMML gốc trong Chương 1–2, gồm cả công thức inline và 52 vùng trong bảng: Chương 1 có 30, Chương 2 có 525. Hồ sơ chi tiết từng công thức và toàn bộ QA nằm trong repo xưởng. Đã thêm 45 đoạn chú giải theo ngữ cảnh, trực tiếp hỗ trợ 304 vùng công thức; 251 vùng còn lại được rà soát với lời giải thích vốn có. Có 31 ví dụ thay số đã kiểm tra độc lập và 33 vùng OMML native mới cho ví dụ. Không chuyển phương trình thành ảnh hay văn bản giả công thức.

Hai công thức gốc được sửa về toán học, với lý do và bằng chứng ở repo xưởng:

1. `L_MPP`: mẫu số cũ đếm sự kiện dù tử số cộng trên các khe tham số bị che. Mẫu số mới đếm đúng các khe hợp lệ, khớp phép lấy trung bình trong Đoạn mã 2.2.
2. `L_time`: đầu hồi quy được định nghĩa nhận vector ghép kích thước `2d_model`, trong khi công thức cũ chỉ truyền một vector `d_model`. Công thức mới truyền `[h_i; h_(i+1)]`.

Hai sửa đổi này không đổi mục tiêu mất mát, claim an ninh hay số liệu thực nghiệm. Nội dung khoa học Chương 3 và phần tài liệu tham khảo không đổi.

| Nhóm | Trước → sau |
|---|---|
| Entropy | Từ xác suất trừu tượng → cửa sổ A,A,B,B cho 1 bit; A,A,A,A cho 0; entropy không tự xác nhận tấn công. |
| PCA | Từ phần dư trừu tượng → vector (3,2), trục (1,0), phần dư (0,2), bình phương chuẩn 4; vượt ngưỡng không tự chỉ ra nguyên nhân độc hại. |
| MPP | Từ trung bình sai theo số sự kiện → trung bình đúng theo khe tham số; xác suất minh họa 0,8 và 0,5 cho mất mát khoảng 0,458. |
| VICReg | Từ phương sai/hiệp phương sai khó hình dung → ví dụ lô vector nhỏ tính từng thành phần; không suy ra độc lập thống kê hoặc ngữ nghĩa an ninh. |
| PCGrad | Từ phép chiếu hình thức → gradient (1,−1) và (−1,0) cho kết quả (0,−1); không bảo đảm cả hai mục tiêu cùng cải thiện. |

## Nghiệm thu

- Toán học và khoa học: 31 ví dụ số PASS; hai công thức sửa có ledger, nguồn đối chiếu và phạm vi claim; không có ký hiệu mới vô nguồn trong các đoạn bổ sung.
- OMML/OOXML: toàn tài liệu từ 622 lên 655 vùng toán, gồm 620 vùng gốc giữ nội dung/thứ tự và đúng hai vùng sửa; không công thức rỗng, quan hệ gói/rId treo hoặc XML hỏng. Chương 3 giữ 67 vùng toán.
- Word thật: mở, cập nhật trường, phân trang, lưu, đóng/mở lại, xuất PDF/A trong repo xưởng; sau đồng bộ, mở lại trực tiếp DOCX xuất xưởng không repair và xuất PDF/A 129 trang. Văn bản cả 129 trang khớp PDF phát hành.
- Bố cục: đã soát trang PDF 15–98 của Chương 1–2, không thấy công thức tràn lề, chú giải mồ côi, trang trắng hoặc bảng/hình vỡ. Bảng 2.4 qua trang 88–89 với hàng tiêu đề lặp.
- Trường và phông: 186 CITATION, 82 PAGEREF, 24 SEQ, 8 REF, 3 TOC, 1 BIBLIOGRAPHY, 114 bookmark và 11 drawing được giữ; danh mục bảng còn Bảng 3.7b. PDF có PDF/A-1a XMP, output intent và 11/11 phông nhúng.
- Hồi quy: băm văn bản và toán Chương 3 trước/sau giống nhau; metadata DOCX được giữ. Kết quả máy đọc được: `OMML-CLARITY-RELEASE-QA.json`.

Giới hạn của thiết kế gốc: `Cov_event`, `Cov_graph`, `Density_edge` mới là chỉ báo dự kiến, chưa khóa công thức đo. Phần chú giải ghi rõ giới hạn này và không dùng số giả như kết quả thực nghiệm.
