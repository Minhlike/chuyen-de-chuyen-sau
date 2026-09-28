# Bổ sung hạn chế cách đọc kết quả Chương 3

Ngày nghiệm thu: 2026-09-29. Các cổng kiểm tra trong phạm vi yêu cầu: PASS.

## Nguồn chuẩn và phạm vi

- Nguồn chuẩn là bản Word hiện tại do người dùng đã chỉnh bullet, lấy từ `D:\chuyen-de-chuyen-sau`, không phục hồi về bản trong Git.
- HEAD ban đầu repo xuất xưởng: `7c6847a17c24a419a6e58d8d6ffc21ab3f459f94`; remote main trùng HEAD này.
- HEAD ban đầu worktree xưởng: `eaf58836ccf363c4bec3ced8444b2253b8408a07`; branch mới `codex/ch3-limited-clarifications`.
- Remote main repo xưởng khi kiểm tra: `a99d5dc0e1499f8454293a2931a4962ad214d4af`. Worktree tiếp tục trên phiên bản tài liệu đã được kiểm toán trước, nhưng DOCX baseline được thay bằng chính bản hiện tại của người dùng.
- Backup nguyên trạng: `C:\Users\Acer\Downloads\chuyen-de-chuyen-sau-before-ch3-2026-09-28\Chuyên đề chuyên sâu.docx`.
- Chỉ bổ sung 8 đoạn có sẵn và 1 đoạn mới. Không tạo chú giải hàng loạt, công thức mới hay ví dụ toán học.

## Đúng các vị trí bổ sung

| Vị trí | Bổ sung | Trang PDF vật lý |
| --- | --- | --- |
| 3.1.3, đoạn đầu dò tuyến tính | Phân biệt trọng số W với cửa sổ ngữ cảnh; giải thích ngắn AP và ROC-AUC ở lần đầu nêu | 103 |
| 3.1.3, trước ba mất mát Stage A2 | Dẫn chiếu ký hiệu và định nghĩa chi tiết về Mục 2.3.3 | 105 |
| 3.1.3, sau mất mát tổng hợp | Ý nghĩa hai hệ số đầu và hệ số thời gian; phân biệt hệ số với đóng góp thực tế khi thang mất mát khác nhau | 106 |
| 3.2.3, lần đầu nêu Var(z) | Mức phân tán biểu diễn; riêng giá trị này chưa chứng minh tránh sụp đổ | 110 |
| 3.2.3, đoạn chênh lệch cặp đôi | Chênh lệch âm nghĩa là Multi-View kém Sequence; biên không thua kém đã đặt trước | 111 |
| 3.2.3, hai đoạn tổng hợp kết quả | Độ lệch chuẩn mẫu qua các seed, không phải khoảng tin cậy | 112 |
| 3.3.2, mục tiêu tham số của H1 | Chiều đầu là số sự kiện trong phiên; chiều sau là tối đa bốn khe tham số mỗi sự kiện | 117 |
| 3.3.2, ngay sau Bảng 3.8 | Cách đọc độ tương đồng cosine và khoảng cách Euclid | 118 |

Kích thước mục tiêu tham số đã được đối chiếu với `hdfs_adapter.py:429–454` và cache thật `hdfs_ssl_train.pt`: 35.000 phiên, tất cả chiều đầu khớp số sự kiện, chiều sau bằng 4; cấu hình `max_param_slots=4`. Đây không phải bốn loại tham số cố định. SHA cache và chứng cứ chi tiết nằm trong `CH3-LIMITED-RELEASE-PROVENANCE.json`.

Giữ nguyên các định nghĩa H1–H5, ER1, VICReg, Frozen Linear Probe, Representation Contract và các ký hiệu h, E, V, thời gian đã định nghĩa tại Chương 1–2. Không diễn giải lại dài; các trạng thái bằng chứng và kết luận gốc được giữ nguyên.

## Bảo toàn và kiểm tra

- Toàn bộ XML Chương 1 và Chương 2 khớp baseline; mọi bullet trong các khoảng trống nghiên cứu, glyph, thụt lề, numbering và paragraph style không đổi.
- SHA XML Chương 1: `205f56de4723b630b85b00e31171b65e8261eec13df9e40f4bebc07d86cb5985`.
- SHA XML Chương 2: `e83e0cb7bf1382524a3a3ce17f8aa17f288bb596f67bd2842fb8d73d77809ba7`.
- Cả 861 vùng OMML giữ nguyên XML và thứ tự; không thêm hoặc sửa công thức. Tất cả bảng, hình, section, bookmark, field code giữ nguyên. 186 citation và kết quả hiển thị CITATION/BIBLIOGRAPHY/REF/SEQ không đổi.
- Không thay số liệu thực nghiệm, kết quả hoặc claim gốc. Số mới trong văn bản chỉ là dẫn chiếu Chương 2 và Mục 2.3.3.
- DOCX ZIP/XML và relationships PASS; không dangling rId hoặc vùng toán rỗng. Các ZIP part khác `word/document.xml` giữ nguyên byte, gồm numbering, styles, header/footer, metadata và font.
- Word COM mở bằng `OpenAndRepair=False`, phân trang, xuất PDF rồi đóng; mở lại bản cuối PASS. Word được dùng chỉ đọc, không lưu lại DOCX để tránh Word tự viết lại cấu trúc bullet của người dùng.
- Cập nhật 3 kết quả số trang PAGEREF từ bookmark thực tế do Word phân trang; giữ nguyên field code và cách ghi số La Mã của phần đầu.
- PDF có 129 trang, tất cả font nhúng, không trang trắng mới, không glyph vượt trang hoặc clipping được phát hiện. Bảng 3.8 nằm trọn trên trang PDF 117, không tách dòng trung bình.
- Đã rà trực quan các trang từ Chương 3 đến hết tài liệu và các vị trí bổ sung. Đối chiếu 84 trang Chương 1–2: chữ và ngắt dòng giữ nguyên; 82 trang khớp pixel. Hai trang PDF 15–16 có sai khác vị trí glyph do Word xuất lại, tối đa 0,277 pt, không đổi nội dung hoặc cấu trúc danh sách.
- Word `ComputeStatistics` trả 157 nhưng PDF thực tế 129 trang; số trang nghiệm thu lấy từ PDF. Xuất bằng cấu hình PDF/A của Word; kiểm tra nhúng font đã PASS, không tuyên bố có kiểm định PDF/A độc lập.

## SHA-256

| Tệp | SHA-256 |
| --- | --- |
| DOCX baseline hiện tại | `cb6a9f9691d21c98af6c0381049412ed90ad7da268e13cae5ce25dc9c76ca57b` |
| PDF cũ trong repo, chưa phản ánh sửa bullet của người dùng | `684c59e99246be3dfb1e49de71c5b2911ef4c3d38471daafa5afee05ef1ad643` |
| DOCX cuối | `d29077dbecb3fff58b417734e0b19e49d271c34750b361c89f534b6d6d15c319` |
| PDF cuối | `649b63d107276d8b1123397d2d2e01c2c7fa6cce010ee5e2fe7e222244d903f1` |

Định nghĩa thước đo được đối chiếu với tài liệu chính thức [AP](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html), [ROC-AUC](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.roc_auc_score.html), và [precision–recall khi mất cân bằng](https://scikit-learn.org/stable/auto_examples/model_selection/plot_precision_recall.html). Không thêm citation vào Word.

Các JSON đi kèm lưu từng bổ sung, QA cấu trúc, Word COM, phân trang và bố cục. Repo xuất xưởng chỉ nhận DOCX/PDF và báo cáo nghiệm thu cần thiết, không nhận script hoặc tệp tạm.

## Nghiệm thu trực tiếp bản xuất xưởng

Word COM mở lại chính DOCX tại `D:\chuyen-de-chuyen-sau` PASS, xuất lại PDF kiểm tra; nội dung và ngắt dòng toàn bộ 129 trang khớp PDF phát hành. Hash DOCX sau mở Word không đổi. Kiểm tra cấu trúc và bảo toàn Chương 1–2 chạy lại trực tiếp tại repo xuất xưởng PASS.

Commit xưởng đã push: `52447775a12bf1497425606cb5bfca773dd98723`. Branch xuất xưởng: `codex/ch3-limited-clarifications-release`. Commit xuất xưởng là commit chứa báo cáo này; tra bằng lịch sử Git của báo cáo.
