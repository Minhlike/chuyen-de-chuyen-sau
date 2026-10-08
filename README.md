# Chuyên đề chuyên sâu — gói phát hành tối giản

Nguồn nội dung khoa học là [Word Master](Chuyên%20đề%20chuyên%20sâu.docx); [PDF chuyên đề](Chuyên%20đề%20chuyên%20sâu.pdf) dùng để đọc. [PowerPoint 10 slide](bao-ve/Bao-cao-chuyen-de-10-slide-v4.pptx) giữ phương trình dưới dạng OMML native; [PDF slide](bao-ve/Bao-cao-chuyen-de-10-slide-v4.pdf) dùng để trình chiếu ổn định. [Lời thuyết trình dạng Word](bao-ve/LOI-THUYET-TRINH-15-PHUT.docx) dùng khi tập nói. Tài liệu Markdown này gom hướng dẫn, bản nói, bản đồ chứng cứ, kết quả chạy lại và câu trả lời phản biện vào một nơi.

## Bắt đầu từ một bản clone

```powershell
git clone https://github.com/Minhlike/chuyen-de-chuyen-sau.git
cd chuyen-de-chuyen-sau
code .
```

Mở Word Master và slide từ thư mục gốc. Nếu cần chỉ số, mở `experiments/nineplus/evaluation_v3/V3_SIX_BACKBONE_EVALUATION_SUMMARY.json` cạnh Bảng 3.6 trong Word. Khi được hỏi về phép chia, mở `datasets/manifests/SPL-HDFS-001.json` và `datasets/manifests/SUBSET-MANIFEST-HDFS.json` cạnh Bảng 3.2. Tất cả đường dẫn ở đây là tương đối từ thư mục vừa clone, không phụ thuộc ổ D:.

**Giới hạn của gói này:** đây là gói đọc, trình bày và kiểm toán số liệu đã lưu. Theo yêu cầu dọn gọn, cây làm việc phát hành không có script Python, mã nguồn huấn luyện, dữ liệu HDFS thô, môi trường CUDA hay checkpoint. Git history vẫn chứa mã Python đúng phiên bản `cecd89a`; cách xem ghi bên dưới. Dữ liệu và checkpoint chỉ có tên, dung lượng, SHA-256 trong `experiments/nineplus/ARTIFACT-MANIFEST.json`, không có payload để nạp. Vì thế clone sạch không thể chạy lại thí nghiệm V3 hoặc huấn luyện Stage A2. Đừng nói với hội đồng rằng bản clone vừa chạy lại kết quả; sáu lượt GPU trong biên nhận là bằng chứng lịch sử ngày 02–03/10/2026.

## Nguồn gốc và cách đọc kết quả

- Ngữ liệu HDFS được báo cáo: 11.175.629 dòng log, 575.061 phiên khối. Phép đánh giá V3 dùng 35.000 phiên Train và 7.500 phiên Validation. Test giữ niêm phong trong phạm vi chiến dịch được mô tả; chỉ số trong gói này là trên Validation.
- Ba AP Sequence-Only: 1,0000; 1,0000; 1,0000. Ba AP Multi-View: 0,7604; 0,6309; 0,5911. Multi-View trung bình 0,6608 ± 0,0885 (độ lệch chuẩn mẫu). Độ lệch AP Multi-View trừ Sequence trung bình −0,3392, thấp hơn biên không thua kém −0,02 ở cả ba seed. H2 không được hỗ trợ **trong đối chứng HDFS Validation đã thực hiện**.
- H1 chưa đo trực tiếp ngữ nghĩa ở cấp khe/token. H3–H5, Graph-Only V3, độ trễ toàn trình và Test chưa có kết quả xác nhận trong gói này. Loss tự giám sát không thay cho AP; bất thường không tự động là tấn công.
- Các tệp JSON/CSV trong `datasets/manifests/`, `experiments/` và `evidence/` là chứng cứ máy đọc được. Hai log Stage A2 Multi-View seed 7/999 và biên bản tạm dừng nằm trong `evidence/STAGE-A2-LOGS.zip`; sáu log chạy lại V3 nằm trong `evidence/V3-GPU-LOGS.zip`. Tệp ZIP chỉ gom các bản gốc, không thay đổi nội dung.

## Bản đồ chứng cứ khi trình bày

| Câu hỏi | Word Master | Tệp nên mở trong bản clone | Mã lịch sử nếu cần |
|---|---|---|---|
| Chia dữ liệu, chống rò rỉ | Mục 3.1.2, Bảng 3.2 | `datasets/manifests/SPL-HDFS-001.json`, `SUBSET-MANIFEST-HDFS.json` | `src/research_agent/experiments/data/hdfs_split_authority.py` |
| Cấu trúc hai nhánh | Mục 2.3–2.4 | Word và slide 4 | `extractor/sequence_view.py`, `models/temporal_graph_view_encoder.py`, `extractor/multi_view.py` |
| Stage A2 và ba loss | Mục 3.1.3, Bảng 3.3–3.4 | `experiments/plans/`, `experiments/nineplus/confirmatory/` | `src/research_agent/experiments/training/stage_a2_trainer.py` dòng 261–286 |
| Đầu dò V3 | Mục 3.1.3, 3.2.2, Bảng 3.6 | `experiments/nineplus/evaluation_v3/V3_SIX_BACKBONE_EVALUATION_SUMMARY.json` | `scripts/evaluate_nineplus_v3.py` dòng 187–327 |
| H2 và bỏ tham số | Mục 3.2.3, Bảng 3.7, 3.10 | `experiments/nineplus/evaluation_v3/H2_SEQUENCE_NOPARAM_SENSITIVITY.json` | `scripts/run_h2_sequence_noparam_sensitivity.py` |
| H1 và che tham số | Mục 3.2.3, Bảng 3.9 | `experiments/nineplus/evaluation_v3/h1_ablation/H1_FROZEN_MASKING_ABLATION_SUMMARY.json` | `scripts/run_h1_masking_ablation.py` |
| Lượt thủ công seed 42 | Mục 3.2.2–3.2.3, Bảng 3.8 | `evidence/MANUAL_RUN_SUMMARY.txt`, `evidence/03_training_epochs_loss.png` | `scripts/run_nineplus_confirmatory.py` |

Để xem mã đúng phiên bản mà không khôi phục các file Python vào cây làm việc:

```powershell
git show cecd89a:src/research_agent/experiments/training/stage_a2_trainer.py
git show cecd89a:scripts/evaluate_nineplus_v3.py
git show cecd89a:src/research_agent/experiments/extractor/multi_view.py
```

Những đường dẫn `.py` in trên slide là đường dẫn của commit `cecd89a`. Trong VS Code có thể dùng Git Timeline/History để mở commit này; nếu chỉ xem trong terminal, dùng `git show` như trên. Ở V3, mã gọi `model.eval()` và `torch.no_grad()` lúc trích xuất; optimizer nhận `probe.parameters()`. Mã không có lệnh `requires_grad_(False)` cho backbone. Phát biểu được chứng cứ hỗ trợ là **backbone không có bước cập nhật trong giai đoạn đánh giá V3**, không phải một khẳng định về thuộc tính `requires_grad` của từng tensor.

Trước hội đồng, đi theo thứ tự: Bảng 3.2 và hai manifest → công thức/đoạn mã Stage A2 trên slide 6 và mã lịch sử → Bảng 3.6 và JSON sáu backbone → H2/H1 cùng JSON đối chứng → giới hạn. Các số đã lưu có thể đối chiếu bằng mắt hoặc công cụ đọc JSON; gói phát hành tối giản không có lệnh kiểm thử/huấn luyện đang hoạt động.

## Dữ liệu và khả năng tái lập

`experiments/nineplus/ARTIFACT-MANIFEST.json` ghi mã băm của cache, nhãn probe và checkpoint gốc. Trước đợt dọn dẹp, các payload này chỉ có trên máy, không có trong GitHub. Nếu về sau cần chạy lại, phải tải lại dữ liệu thô từ nguồn hợp pháp, phục hồi đúng mã ở commit lịch sử, tái tạo môi trường và nạp đúng artifact có SHA-256 khớp manifest; checkpoint đã huấn luyện không thể tái tạo chỉ từ Markdown. Khi thiếu một thành phần, chỉ dùng các JSON kết quả như chứng cứ **đã lưu**, không gọi là kết quả tái chạy.

Với Multi-View seed 999, biên bản tạm dừng cũ ghi epoch 4 có Validation loss 48,7659 (tốt nhất), epoch 5 có Validation loss 49,3850 và bộ đếm chờ 1/3. Cả hai mốc đều được tạm dừng an toàn theo thủ tục quản trị, không phải kết luận về chất lượng mô hình. Log từng epoch và `ADMINISTRATIVE_PAUSE.json` được giữ nguyên byte trong `evidence/STAGE-A2-LOGS.zip`.

---

## Lời trình bày 15 phút

Bản nói theo 10 slide. Các mốc để tập bấm giờ; nếu cần rút ngắn, chỉ lược câu chuyển ý, không lược phạm vi của kết quả. Khi chỉ mã trong VS Code, dùng mục “Xem mã trong lịch sử Git” bên dưới. Đường dẫn `.py` trong lời nói và trên slide trỏ đến commit nguồn `cecd89a`, không phải tệp đang nằm ở gốc bản phát hành tối giản.

## Slide 1 — Câu hỏi nghiên cứu (0:00–0:30)

Kính thưa cô và các thầy cô, em là Đoàn Ngọc Hoàng Minh. Chuyên đề của em tìm cách biến log thành vector để phục vụ phát hiện bất thường. Câu hỏi chính là: vector ấy giữ được thông tin gì, và mình kiểm tra bằng cách nào? Em xin nói ngắn phần đặt vấn đề để dành thời gian cho dữ liệu, mã và kết quả, kể cả kết quả không thuận với giả thuyết ban đầu.

## Slide 2 — Log cần ngữ cảnh (0:30–1:20)

Một dòng log đứng riêng thường chưa đủ để hiểu hành vi. Cùng là thao tác đọc tệp, nhưng do tiến trình nào thực hiện và xảy ra sau lệnh nào thì cách đánh giá sẽ khác. Ba cách biểu diễn giữ các phần khác nhau: đếm sự kiện giữ tần suất, chuỗi giữ thứ tự, đồ thị giữ quan hệ thực thể. Cách nào cũng có phần dễ bỏ sót.

Từ khảo sát ở Chương 1, em rút ra năm khoảng trống. Ở đây em tập trung vào ba điểm: giữ tín hiệu tham số, thử kết hợp chuỗi với đồ thị, và chống rò rỉ khi chia dữ liệu. Nhãn thô và quyền riêng tư vẫn có trong thiết kế nhưng chưa có phép thử đủ để kết luận. Việc thêm nhánh đồ thị mới là giả thuyết cần đối chứng.

## Slide 3 — Hợp đồng Biểu diễn (1:20–2:15)

Để tránh nói chung chung rằng vector “tốt”, em đặt ra Hợp đồng Biểu diễn. **PRESERVE** hỏi tín hiệu cần cho an ninh, như tham số và quan hệ, còn đọc ra được không. **INVARIANT** hỏi thay đổi vô hại như PID ngẫu nhiên có làm vector lệch vô lý không. **EXCLUDE** hỏi mô hình có bám vào dấu vết môi trường hoặc định danh nhạy cảm để học đường tắt không.

Đây là tiêu chí để đặt phép đo, chưa phải thành tích đã đạt. Muốn chứng minh ngữ nghĩa một khe tham số được giữ, cần đo đúng cấp khe ấy; điểm bất thường của cả phiên chưa trả lời được. Khi đánh giá, em dùng checkpoint để tạo vector mà không cập nhật bộ tạo vector; chỉ đầu dò tuyến tính được học. Lát nữa em sẽ chỉ đúng đoạn mã.

## Slide 4 — Thiết kế hai nhánh (2:15–3:15)

Thiết kế em khảo sát có một nhánh đọc chuỗi bằng Transformer và một nhánh đọc quan hệ theo thời gian bằng Temporal GNN. Trong đường huấn luyện, hai đầu chiếu đưa vector nhánh vào mất mát gióng hàng VICReg. Nhưng khi lấy vector để đánh giá V3, mã đưa hai biểu diễn gốc vào cổng dung hợp; nó không chạy lại hai đầu chiếu ấy. Đây là chỗ rất dễ nói sai nếu chỉ nhìn sơ đồ kiến trúc.

Chuỗi giúp nhìn diễn biến, đồ thị giúp nhìn phụ thuộc giữa thực thể. Hai nguồn nghe có vẻ bổ sung cho nhau, nhưng dữ liệu và cách học quyết định nó có bổ sung thật hay không. Vì thế em không coi Multi-View chắc chắn tốt hơn. Thiết kế còn mô tả cập nhật theo dòng; chuyên đề chưa đo thông lượng và độ trễ toàn trình, nên em cũng chưa nhận là đã chứng minh khả năng thời gian thực.

## Slide 5 — Dữ liệu và phép chia (3:15–4:30)

Trước khi xem điểm đánh giá, em xin chỉ nguồn của các con số. Ngữ liệu HDFS gốc có 11.175.629 dòng log, gom thành 575.061 phiên khối có nhãn. Đây là quy mô **toàn ngữ liệu**. Phép thử V3 dùng một tập con theo ngân sách: 35.000 phiên Train và 7.500 phiên Validation; không được lấy 11 triệu dòng để gọi là số mẫu huấn luyện của đầu dò.

Trong mã và manifest, phiên được xếp theo thời điểm bắt đầu. Những phiên bắc qua ranh giới Train–Validation hoặc Validation–Test bị loại, rồi mới chọn tập con. Từ vựng được khớp trên Train. Các tệp `SPL-HDFS-001.json` và `SUBSET-MANIFEST-HDFS.json` ghi số lượng, thời gian và mã băm của phép chia; mã thực hiện nằm ở `hdfs_split_authority.py`. Khi cô hỏi, mở hai manifest trong bản phát hành; xem mã phân chia từ commit `cecd89a` theo hướng dẫn bên dưới.

Manifest ghi Test ở trạng thái `SEALED`, chưa vật hóa đặc trưng Test cho người huấn luyện. Phần báo cáo này chỉ dùng kết quả trên Validation. Một tệp manifest không tự chứng minh mọi lần chạy trong lịch sử không bao giờ truy cập Test; điều em có thể trình ra là giao thức, chỉ mục và trạng thái artifact của chiến dịch đang báo cáo.

## Slide 6 — Stage A2: công thức và mã huấn luyện (4:30–6:35)

Bây giờ đến phần mã huấn luyện. Trên slide là công thức đang dùng cho mất mát đồ thị Stage A2: **L_graph bằng L_rel cộng L_node cộng 0,1 lần L_time**. Ba số hạng lần lượt là sai số dự đoán quan hệ bị che, tái tạo thuộc tính nút bị che và dự đoán khoảng thời gian. Trước khi cộng, mã chia tổng sai số từng loại cho số mục tiêu hợp lệ của loại ấy. Thành ra hệ số 0,1 là trọng số trong mục tiêu tối ưu; không thể đọc nó thành “thời gian chỉ đóng góp 10% vào kết quả phát hiện”.

Ngay dưới công thức là đoạn từ `stage_a2_trainer.py`, khoảng dòng 261 đến 286: mã tạo `L_graph_group`, gọi `backward()`, kiểm tra gradient, chặn chuẩn gradient nếu cấu hình bật, rồi `optimizer.step()`. Nếu cô hỏi mô hình thực sự học ở đâu, em chỉ đoạn mã đã lưu ở commit `cecd89a` và runner `run_nineplus_confirmatory.py`, cùng manifest kết quả; em không chỉ trỏ vào sơ đồ trong Word.

Bảng bên phải là năm lượt chạy Stage A2 được chuyên đề báo cáo. Em không dùng bảng này để xếp hạng mô hình bằng loss, bởi các mục tiêu và điều kiện chạy chưa đồng nhất hoàn toàn. Seed 999 có giai đoạn khởi động khác kế hoạch; seed 42 dùng lịch cũ và dừng ở epoch 4; các lượt còn lại có vấn đề về mốc xác lập giao thức, hồ sơ thực thi hoặc commit. Khi đối chiếu giao thức đã khóa, không lượt nào trong năm lượt đáp ứng đầy đủ điều kiện chuẩn. Vì vậy kết luận đúng là: có năm hồ sơ và năm số loss quan sát được, nhưng không thể gom chúng thành năm phép lặp chuẩn để tuyên bố chất lượng phát hiện. Muốn trả lời bài toán hạ nguồn, em phải sang bước đánh giá vector V3.

## Slide 7 — V3: chỉ đầu dò được cập nhật (6:35–9:20)

Slide này là trọng tâm của phép so. Em lấy sáu checkpoint đã huấn luyện: Sequence-Only và Multi-View, mỗi nhánh ba seed 42, 7, 999. Với từng checkpoint, mã gọi `model.eval()` và trích xuất trong `torch.no_grad()`. Nó tạo ma trận vector Train kích thước 35.000 nhân 128, và Validation 7.500 nhân 128. Hai ma trận này là đầu vào của một lớp tuyến tính `nn.Linear(128,1)`.

Chỗ cần chỉ thật rõ trong mã là `optimizer = AdamW(probe.parameters())`. Bộ tối ưu chỉ nhận tham số của đầu dò, rồi vòng lặp 50 epoch gọi `loss.backward()` và `optimizer.step()` cho đầu dò ấy. Tệp kết quả ghi số bước tối ưu của backbone bằng không. Đây là căn cứ để em nói bộ tạo vector **không được cập nhật trong bước V3**; em không viện ra một dòng `requires_grad_(False)` vì mã không có dòng đó. Điểm đầu dò là sigmoid của `w` chuyển vị nhân `z` cộng `b`. Sau khi học trên Train, mã chấm điểm toàn bộ Validation. **AP là Average Precision, tức độ chính xác trung bình**: khi xếp các phiên theo điểm, các phiên thật sự bất thường càng ở phía đầu danh sách thì AP càng cao. Nó không phải tỷ lệ dự đoán đúng của toàn bộ phiên. Còn ROC-AUC là diện tích dưới đường ROC, đo khả năng phân biệt hai lớp khi thay đổi ngưỡng.

Giờ ta đọc bảng sáu hàng. Ba seed Sequence đều có AP và ROC-AUC là 1,0000. Ba AP của Multi-View là 0,7604; 0,6309; 0,5911, với ROC-AUC tương ứng 0,9946; 0,8081; 0,7693. AP trung bình Multi-View là 0,6608, độ lệch chuẩn mẫu 0,0885. Cột Var(z) chỉ là độ phân tán trung bình của biểu diễn ẩn; từ một giá trị dương nhỏ không thể tự suy rằng mô hình tránh được sụp đổ biểu diễn theo mọi tiêu chí.

Em đã chạy lại bước trích xuất và fit đầu dò từ đủ sáu checkpoint trên GPU; kết quả khớp số trong Word ở độ chính xác báo cáo. Đây là **chạy lại đánh giá**, không phải huấn luyện lại Stage A2 từ đầu. AP bằng một là quan sát đáng chú ý nhưng chỉ trên HDFS Validation theo cách chia này. Nó không phải điểm Test, cũng không chứng minh mô hình hiểu mọi loại tấn công. Điều bảng này cho thấy rõ nhất là, dưới cùng giao thức đầu dò, Multi-View thấp hơn Sequence ở cả ba seed.

## Slide 8 — H2: tính từng cặp và kiểm tra ngờ vực (9:20–11:20)

H2 đầy đủ có thêm các đối chứng khác; phần hoàn tất và so được cùng giao thức ở đây là Multi-View với Sequence-Only. Trước khi nhìn kết quả, chuyên đề dùng biên không thua kém của AP là âm 0,02. Em tính **Delta AP bằng AP Multi-View trừ AP Sequence** cho cùng seed. Nếu Delta nhỏ hơn âm 0,02, cặp đó không đạt biên.

Ta có thể thay ngay hàng đầu trên bảng: 0,7604 trừ 1,0000 cho khoảng âm 0,2396. Hai seed còn lại lần lượt âm 0,3691 và âm 0,4089. Cả ba thấp hơn biên khá xa; trung bình là âm 0,3392, cộng trừ 0,0885 là độ lệch chuẩn mẫu qua ba seed, không phải khoảng tin cậy. Vì vậy, trong đối chứng này, **H2 không được hỗ trợ**. Với ba seed, em không suy rộng thành mọi dữ liệu và mọi kiến trúc đa góc nhìn.

Một cách phản biện rất hợp lý là: Sequence thắng chỉ vì nó được nhìn trực tiếp khe tham số, trong khi Multi-View bị thiệt. Em đã thử đúng nghi vấn ấy: che khe tham số của Sequence ở cả Train và Validation, trích xuất lại vector rồi fit đầu dò mới. AP của Sequence vẫn 1,0000 ở cả ba seed. Tệp `H2_SEQUENCE_NOPARAM_SENSITIVITY.json` ghi riêng từng hàng và chênh lệch. Phép thử này làm yếu cách giải thích “chỉ do khe tham số”, nhưng không chứng minh tham số vô ích hay tìm ra nguyên nhân duy nhất khiến Multi-View kém. Đó là việc phải làm tiếp.

## Slide 9 — H1: phản ứng của vector và giới hạn cấp đo (11:20–13:35)

H1 hỏi thông tin của tham số động có được giữ với đúng ý nghĩa an ninh hay không. Nhãn cần kiểm tra nằm ở cấp token hoặc khe tham số, trong khi vector V3 đang đo là một vector 128 chiều gộp cho cả phiên. Nếu lấy AP cấp phiên để tuyên bố H1 đã được chứng minh thì mình đã lẫn cấp độ đo.

Phép thử hiện có mang tính gián tiếp. Em giữ nguyên từng checkpoint Sequence, tạo một vector khi có tham số và một vector khi che các khe tham số, rồi đo cosine và khoảng cách Euclid L2. Cosine gần một nghĩa là hai vector gần cùng hướng hơn; L2 càng lớn thì chúng càng xa nhau. Ba giá trị cosine trung bình là 0,9581; 0,8201; 0,9546. Các khoảng cách L2 đều khác không. Như vậy vector có phản ứng với thao tác che. Nhưng AP cấp phiên trước và sau che đều 1,0000 ở cả ba seed. Ta có thể nói vector đổi mà phép đo AP này không đổi; không thể nói mô hình đã giữ đúng ngữ nghĩa từng khe, cũng không thể nói tham số hoàn toàn vô ích.

Ở góc dưới slide em để một lượt tái lập thủ công seed 42: sáu epoch, tốt nhất ở epoch ba, loss Validation 0,009218 và VRAM đỉnh khoảng 170,45 MB. Số AP nội bộ 0,899385 và AP V3 1,0000 dễ bị so sai. Hai run ID của checkpoint khác nhau nhưng tệp trọng số có cùng SHA-256; điều làm hai AP không cùng thước so là giao thức đầu dò. Đầu dò nội bộ chia Validation 80/20 để học và đo, còn V3 học trên Train và đo trên toàn bộ Validation. Em không gọi chênh lệch đó là mức cải thiện. Để trả lời H1 đúng nghĩa, cần một phép đo với biểu diễn và nhãn ở cùng cấp token hoặc khe.

## Slide 10 — Kết luận gắn với tệp chứng cứ (13:35–15:00)

Slide cuối là bản đồ chứng cứ. Dữ liệu và phép chia nằm ở hai manifest HDFS; loss huấn luyện ở `stage_a2_trainer.py`; đường trích xuất và gióng hàng ở `multi_view.py`. Trong `evaluate_nineplus_v3.py`, trích xuất dùng `eval()` và `no_grad()`, còn bộ tối ưu chỉ nhận `probe.parameters()`. Sáu hàng kết quả nằm ở `V3_SIX_BACKBONE_EVALUATION_SUMMARY.json`.

Em nhận ba phần đóng góp: đặc tả Hợp đồng Biểu diễn, tích hợp kiến trúc chuỗi–đồ thị, và hiện thực cùng kiểm toán. Em không nhận Transformer, Temporal GNN hay VICReg là thuật toán mình phát minh. Bằng chứng hiện có không hỗ trợ H2 trên HDFS Validation; H1 chưa đo trực tiếp ở cấp tham số. H3 đến H5, Graph-Only V3, độ trễ toàn trình và Test còn thiếu.

Kết quả hiện có không cho phép gọi mô hình đa góc nhìn tốt hơn. Em xin dừng ở điều đã đo được và sẵn sàng mở mã trong lịch sử Git, manifest và bảng kết quả để trả lời câu hỏi của cô.

---

## Từ điển trả lời phản biện

Đây là tài liệu ôn tập, không phải lời để đọc nguyên văn. Mỗi câu trả lời đi theo ba bước: **khẳng định đúng phạm vi → chỉ bằng chứng → nêu giới hạn**. Nếu không biết, dùng bản đồ chứng cứ ở đầu tài liệu này để mở đúng mã lịch sử hoặc tệp kết quả; không suy đoán thay cho dữ liệu.

## A. Câu hỏi gốc về đề tài

### 1. Đề tài này thực sự giải quyết bài toán gì?

Tạo biểu diễn đặc trưng từ log và kiểm tra biểu diễn đó có ích cho phát hiện bất thường hay không. Chuyên đề **không** xây dựng một hệ thống SOC hoàn chỉnh hay chứng minh mọi bất thường là tấn công. Bản Word: Mục 1.1.3, 2.1 và Chương 3.

### 2. Khác nhau giữa log, sự kiện, phiên và vector là gì?

Log là bản ghi nguồn. Sự kiện là nội dung đã được phân tích và chuẩn hóa từ log. Phiên khối HDFS gom các sự kiện cùng block ID. Vector 128 chiều là biểu diễn học được của một phiên trong phép đánh giá hạ nguồn. Không lấy một chiều vector riêng lẻ làm nhãn tấn công. Mã: `src/research_agent/experiments/data/hdfs_adapter.py`, `scripts/evaluate_nineplus_v3.py`.

### 3. Bất thường có đồng nghĩa với tấn công không?

Không. Bất thường là lệch khỏi mẫu tham chiếu hoặc là lớp dương của bộ dữ liệu theo giao thức đang xét. Muốn kết luận tấn công cần thêm ngữ cảnh và bằng chứng an ninh. Vì vậy, khi nói về HDFS, dùng đúng cụm “phát hiện bất thường” cho AP/ROC-AUC; không đổi thành tỷ lệ phát hiện tấn công ngoài thực địa.

### 4. Cái gì là đóng góp của sinh viên, cái gì là phương pháp có sẵn?

C1 là khung Hợp đồng Biểu diễn, C2 là cách tích hợp các khối chuỗi–đồ thị và ràng buộc vận hành, C3 là thực hiện và kiểm toán giao thức thực nghiệm. Transformer, Temporal GNN, VICReg và đầu dò tuyến tính là các khối kỹ thuật kế thừa; chuyên đề không nhận là đã phát minh chúng. Bản Word: đoạn mở đầu Mục 2.1 và Kết luận Chương 3.

### 5. Vì sao không chỉ dùng Sequence-Only khi kết quả của nó tốt hơn?

Sau thực nghiệm, Sequence-Only đúng là đối chứng mạnh hơn trên HDFS Validation. Việc nghiên cứu Multi-View vẫn trả lời câu hỏi khoa học: thêm quan hệ đồ thị có giúp trong giao thức này không? Kết quả hiện tại là chưa giúp. Nếu triển khai cho đúng bộ dữ liệu và chi phí hiện thấy, Sequence-Only là lựa chọn cần được ưu tiên xem xét; không ép dùng Multi-View chỉ vì thiết kế phức tạp hơn.

### 6. “Hợp đồng Biểu diễn” có phải hợp đồng hình thức hay định lý không?

Không. Đây là đặc tả yêu cầu và phép thử cho biểu diễn. PRESERVE, INVARIANT, EXCLUDE không tự chứng minh mô hình thỏa mãn. Mỗi điều kiện phải được thao tác hóa và đo riêng. Bản Word nêu rõ ranh giới này ở phần đóng góp C1.

## B. Khái niệm và thuật toán

### 7. PRESERVE, INVARIANT, EXCLUDE phân biệt thế nào?

PRESERVE hỏi thông tin an ninh cần thiết có còn đọc được từ vector không. INVARIANT hỏi vector có ổn định trước biến đổi vô hại không. EXCLUDE hỏi thông tin gây rò rỉ, đường tắt hoặc lộ định danh có bị hạn chế không. Một đặc trưng có thể hữu ích cho một phép đo nhưng vẫn vi phạm quyền riêng tư; ba điều kiện không thay thế nhau. Bản Word: Bảng 1.2.

### 8. Vì sao vector 128 chiều không giải thích được từng tham số?

128 là kích thước vector gộp cấp phiên trong giao thức đang xét, không phải 128 nhãn có nghĩa cố định. Nhãn tham số gốc ở cấp token/khe, nên muốn kiểm tra trung thực ngữ nghĩa tham số phải có biểu diễn và mục tiêu cùng cấp. Đây là lý do H1 chưa đo trực tiếp. Bản Word: Mục 3.2.3.

### 9. Transformer làm gì ở nhánh chuỗi?

Nó biến dãy sự kiện thành biểu diễn có xét ngữ cảnh và thứ tự. Cơ chế chú ý dùng Query, Key, Value để tính mức liên hệ giữa các vị trí; thông tin vị trí/thời gian giúp mô hình phân biệt thứ tự. Attention là trọng số tính toán trong mô hình, **không phải bằng chứng nhân quả** rằng một sự kiện gây ra sự kiện khác. Mã: `src/research_agent/experiments/extractor/sequence_view.py`.

### 10. Temporal GNN khác một đồ thị tĩnh ở đâu?

Quan hệ thực thể và thời điểm tương tác được đưa vào cập nhật thông điệp/trạng thái. Nó nhằm mô hình hóa phụ thuộc thay đổi theo thời gian, thay vì chỉ xem có cạnh hay không. Thiết kế suy luận theo dòng có trạng thái hữu hạn, nhưng thông lượng và độ trễ toàn trình chưa đo. Mã: `src/research_agent/experiments/models/temporal_graph_view_encoder.py` và `src/research_agent/experiments/extractor/graph_view.py`.

### 11. Vì sao cần cả nhánh chuỗi lẫn nhánh đồ thị?

Đây là giả thuyết thiết kế: chuỗi diễn tả thứ tự sự kiện, đồ thị diễn tả phụ thuộc giữa thực thể. Hai nguồn có thể bổ sung nhau, nhưng cũng có thể tạo nhiễu hoặc làm giảm tín hiệu khi gióng hàng. Kết quả H2 trên HDFS cho thấy giả thuyết lợi ích chưa thành công trong phép thử hiện tại.

### 12. VICReg gồm những gì?

Ba phần: kéo các biểu diễn tương ứng lại gần nhau (invariance), khuyến khích độ phân tán theo chiều để tránh nghiệm hằng (variance), và giảm sự phụ thuộc dư thừa giữa các chiều (covariance). Đây là mục tiêu tối ưu, không phải chứng nhận mô hình “hiểu an ninh” hay chắc chắn không sụp đổ. Mã: `src/research_agent/experiments/extractor/multi_view.py`.

### 13. Var(z) nhỏ có chứng minh sụp đổ biểu diễn không?

Không tự nó chứng minh. Bản Word báo cáo giá trị phương sai đo được, nhưng ngưỡng cũ được đặt trong đường xử lý có `<MASK>`, còn V3 đo vector sạch. Hai cách thao tác hóa khác nhau nên không dùng ngưỡng cũ làm phán quyết độc lập. Bản Word: Mục 3.2.3, đoạn kiểm toán phương sai.

### 14. Loss tự giám sát thấp nói lên điều gì?

Nó cho biết mô hình giải bài tập tự giám sát đã giao tốt đến mức nào trên dữ liệu và cách tính loss đó. Nó không trực tiếp đo AP, không chứng minh hiểu hành vi độc hại, và không đủ để so sánh các lượt có thủ tục huấn luyện khác nhau. Cần đánh giá hạ nguồn theo cùng giao thức.

### 15. Trọng số 1,0; 1,0; 0,1 ở Stage A2 là gì?

Đó là hệ số cộng ba thành phần loss: quan hệ che, thuộc tính nút che và khoảng thời gian. Hệ số 0,1 không có nghĩa thời gian chỉ đóng góp đúng 10% vào gradient hay kết quả; độ lớn thực tế còn phụ thuộc thang số của từng loss. Bản Word: Mục 3.1.3.

### 16. “Causal” trong phân chia/suy luận có nghĩa nhân quả khoa học không?

Ở đây chủ yếu nghĩa là **không nhìn trước tương lai**: dữ liệu huấn luyện ở trước dữ liệu đánh giá theo thời gian, và cập nhật trạng thái chỉ dùng sự kiện đã đến. Nó không chứng minh quan hệ nhân quả giữa các sự kiện hay giữa một đặc trưng với một vụ tấn công.

### 17. Mã giả danh theo phiên có bảo đảm ẩn danh không?

Không. HMAC với khóa ngắn hạn hỗ trợ liên kết có kiểm soát trong phạm vi được thiết kế và giảm lộ định danh thô. Nó không xóa hết nguy cơ tái nhận dạng hoặc suy luận thành viên. H5 chưa có phép kiểm nghiệm quyền riêng tư đầy đủ. Mã: `src/research_agent/experiments/extractor/tokenizer.py`.

### 18. Attention-MIL và nhãn yếu được dùng đến đâu?

Stage B được mô tả như hướng thích ứng khi chỉ có nhãn mức phiên/máy chủ, giúp phân bổ bằng chứng trong một tập sự kiện. Trong chiến dịch HDFS được báo cáo, Stage B chưa huấn luyện và H4 chưa được kiểm chứng. Không nói kết quả V3 là kết quả Attention-MIL.

## C. Dữ liệu và đánh giá

### 19. Dữ liệu thô ở đâu, có nằm trong Git không?

Bản phát hành tối giản lưu manifest, kết quả và tài liệu; mã Python chỉ còn trong lịch sử Git tại commit `cecd89a`. Tệp HDFS thô, tensor và checkpoint không nằm trong Git. Vì vậy clone sạch **không chạy lại được V3**. Mở `experiments/nineplus/ARTIFACT-MANIFEST.json` để chỉ từng tệp đã dùng, dung lượng và SHA-256; đây là danh mục nguồn gốc, không phải bản tải xuống artifact.

### 20. Tại sao Train chỉ 35.000 phiên khi bộ dữ liệu có 575.061 phiên?

575.061 là quy mô toàn ngữ liệu. 35.000 Train và 7.500 Validation là ngân sách phiên của chiến dịch được báo cáo, lấy theo thứ tự thời gian sau khi áp dụng quy tắc phân chia. Không đồng nhất “toàn ngữ liệu” với “toàn bộ phiên dùng để fit probe”. Bản Word: Mục 3.1.2, Bảng 3.2.

### 21. Chặn rò rỉ dữ liệu bằng cách nào?

Các phiên được sắp theo thời gian; Train đi trước Validation; phiên qua ranh giới bị loại; danh tính phiên không chồng lấn. Manifest và cache split lưu mã băm danh sách, còn mã nguồn kiểm các bất biến này khi chạy. Điều đó giảm các đường rò rỉ đã nhận diện, không phải bằng chứng tuyệt đối rằng mọi kiểu rò rỉ đều không thể xảy ra. Mã: `src/research_agent/experiments/data/hdfs_split_authority.py`.

### 22. Test niêm phong nghĩa là gì?

Các biến kiểm soát chiến dịch ghi `test_opened=false`, `test_reads=0`, và mã đánh giá V3 chỉ làm việc với Train/Validation. Đây là trạng thái được ghi nhận trong giao thức và artifact; không phải lời bảo đảm vượt quá chứng cứ. Nếu hội đồng yêu cầu điểm Test, câu trả lời đúng là chưa có trong chuyên đề này.

### 23. Frozen Linear Probe kiểm tra cái gì?

Trong bước V3, mã không cập nhật backbone: nó lấy vector trong `torch.no_grad()`, chỉ huấn luyện một bộ phân loại tuyến tính bằng nhãn Train và đo trên Validation. Nó kiểm tra tín hiệu **có thể phân tách tuyến tính** từ vector theo giao thức đó. Nó không đo mọi tương quan phi tuyến và không chứng minh bộ trích xuất tự nó là một bộ phát hiện hoàn chỉnh. Mã lịch sử: `scripts/evaluate_nineplus_v3.py`.

### 24. Vì sao cần khóa cùng giao thức V3 khi so mô hình?

Nếu khác dữ liệu fit, seed probe, số epoch, cách chuẩn hóa hoặc phân vùng đánh giá, chênh lệch AP có thể do giao thức chứ không do biểu diễn. V3 dùng 35.000 Train, 7.500 Validation, probe seed 10007 và 50 epoch/6.850 bước cho từng backbone. Bản Word: Mục 3.1.3; tệp `V3_SIX_BACKBONE_EVALUATION_SUMMARY.json`.

### 25. AP và ROC-AUC khác gì?

AP là **Average Precision**, tức độ chính xác trung bình. Về cách tính, nó lấy trung bình precision theo những mức tăng recall trên đường precision–recall; không phải accuracy, tức tỷ lệ đoán đúng chung. AP thường hữu ích khi lớp dương hiếm. ROC-AUC là diện tích dưới đường ROC, đo khả năng phân biệt hai lớp trên nhiều ngưỡng. Cả hai dựa trên nhãn hiện có; chúng không chỉ ra nguyên nhân và không bảo đảm vận hành tốt ở một ngưỡng cảnh báo cụ thể.

### 26. AP bằng 1 có đáng nghi không?

Đó là giá trị JSON ghi nhận trên HDFS Validation theo V3 ở ba seed Sequence. Cần kiểm tra quy trình chia, nhãn, khả năng trùng lặp và đánh giá ở dữ liệu ngoài HDFS trước khi khái quát hóa. Chuyên đề đã có kiểm soát phân vùng và chưa mở Test, nhưng không có cơ sở gọi đây là hiệu năng phổ quát. Mở Bảng 3.6 và từng `V3-PROBE-RESULT.json`.

### 27. Dấu “±” trong kết quả là gì?

Là độ lệch chuẩn mẫu của ba seed, không phải khoảng tin cậy và không phải sai số của từng dự đoán. Với ba seed, không phát biểu kiểm định ý nghĩa thống kê quy mô lớn. Bản Word: Mục 3.2.3.

### 28. Vì sao AP nội bộ 0,899385 khác AP V3 1,0000?

Hai probe được fit và đo khác nhau. Probe nội bộ chia 7.500 mẫu Validation theo tỷ lệ 80/20; V3 fit trên 35.000 Train và đo trên toàn bộ 7.500 Validation. Không lấy hiệu hai con số để kết luận mô hình cải thiện qua một lần chạy. Bản Word: Bảng 3.8 và phần tái lập thủ công.

## D. Những câu hỏi dễ bị hỏi vặn về kết quả

### 29. H2 đã bị bác bỏ hoàn toàn chưa?

Không dùng chữ “hoàn toàn”. Dưới đối chứng trực tiếp với Sequence-Only trên HDFS Validation, cả ba cặp seed vi phạm biên không thua kém AP đặt trước là −0,02. Vì vậy H2 **không được hỗ trợ trong phạm vi ấy**. Chưa có bằng chứng để khái quát sang mọi tập dữ liệu hoặc mọi cấu hình Multi-View.

### 30. Biên −0,02 có phải chọn sau khi thấy kết quả không?

Theo bản Word, đó là biên thực tiễn đã tiền đăng ký trước thực nghiệm H2. Khi trả lời nên mở Mục 3.2.3 và kế hoạch trong `experiments/plans/`; không chỉ nhắc miệng. Nếu tài liệu tiền đăng ký độc lập ngoài repo không được yêu cầu trình, không tự khẳng định thêm về thời điểm ngoài hồ sơ có sẵn.

### 31. Vì sao ba cặp seed vẫn đủ để nói H2 không được hỗ trợ?

Vì phát biểu được giới hạn ở **ba cặp quan sát và biên đã đặt trước**: cả ba độ lệch đều thấp hơn −0,02 khá xa. Ba seed không đủ cho kết luận suy diễn thống kê rộng, nhưng đủ để mô tả kết quả của chính phép đối chứng đó. Không đổi mô tả thực nghiệm thành định luật chung.

### 32. Multi-View kém vì tham số của Sequence chăng?

Đó là một giả thuyết giải thích đã được thử bằng phép che tham số đầu vào Sequence trên cả Train và Validation, rồi fit probe mới. AP Sequence vẫn 1,0000 ở ba seed. Kết quả này loại trừ lời giải thích đơn giản ấy **trong phép thử cụ thể**, chưa tìm ra nguyên nhân thật của việc Multi-View giảm. Bản Word: Bảng 3.10.

### 33. H1 đã chứng minh mô hình hiểu tham số chưa?

Chưa. Che tham số làm vector thay đổi về cosine và L2, nhưng AP phát hiện bất thường không giảm; nhãn mục tiêu H1 lại ở cấp token, khác cấp phiên của vector. Đây là quan sát phụ về độ nhạy đầu vào, không phải phép đo trực tiếp ngữ nghĩa. Bản Word: Bảng 3.9, Mục 3.2.3.

### 34. Nếu che tham số mà AP không giảm, tại sao còn cần tham số?

Không thể kết luận “không cần”. HDFS Validation hiện tại có thể có những tín hiệu khác đủ để đầu dò phân tách lớp; hoặc thước đo và cấp biểu diễn chưa nhạy với giá trị an ninh của tham số. Muốn kết luận về sự cần thiết, cần bài kiểm tra với mục tiêu đúng cấp và tình huống mà tham số quyết định hành vi.

### 35. Graph-Only có nằm trong đối chứng V3 không?

Không. Những số Graph-Only cũ là tham chiếu khảo sát theo giao thức nội bộ; bộ ba Graph-Only xác nhận mới chưa được huấn luyện và đánh giá V3 do chi phí tính toán ước tính lớn. Không đặt AP nội bộ của Graph-Only cạnh AP V3 rồi xếp hạng ba kiến trúc. Bản Word: Mục giới hạn thực nghiệm Chương 3.

### 36. 0/5 lượt Stage A2 chuẩn có làm mọi kết quả vô giá trị không?

Không. Nó làm yếu khả năng coi năm lượt là các lần lặp chuẩn hoàn toàn so sánh được, nên phải công khai từng sai lệch và giới hạn kết luận. Kết quả V3 vẫn là các phép đo đã chạy và có artifact, nhưng khi diễn giải phải giữ nguồn gốc, seed và sai lệch thủ tục tương ứng. “Không chuẩn hoàn toàn” khác “không có dữ liệu”.

### 37. Seed 999 Multi-View có vấn đề gì?

Khi khôi phục huấn luyện, trọng số mô hình và trạng thái optimizer/scheduler được nạp lại; trạng thái RNG PyTorch không được tuần tự hóa toàn phần mà được tái tạo xác định. Bản Word phân loại đây là kết quả xác nhận có sai lệch thủ tục đã công bố, không gọi là full-state resume. Không giấu chi tiết ấy khi bị hỏi về tính tái lập.

### 38. ER1 đã chứng minh mô hình chạy thời gian thực chưa?

Chưa. Có quan sát VRAM cục bộ; chưa đo thông lượng sự kiện/giây, độ trễ p50/p95, RAM và trạng thái theo thực thể cho toàn hệ thống. Chi phí cục bộ của bước fusion không được đánh đồng với chi phí toàn trình xử lý log và đồ thị. Bản Word: Mục 2.4 và 3.2.3.

### 39. H3, H4, H5 đang ở trạng thái nào?

H3 về trôi dạt và đường tắt: chưa kiểm thử. H4 về phân bổ bằng chứng từ nhãn thô: Stage B mới ở mức thiết kế, chưa huấn luyện. H5 về liên kết có kiểm soát và quyền riêng tư: có cơ chế mã giả danh, chưa đo tấn công suy luận thành viên hoặc đường biên tiện ích–riêng tư. Không trình bày chúng như kết quả thực nghiệm.

### 40. Nếu được yêu cầu chạy ngay tại chỗ, nên làm gì trước?

Mở Word Master, manifest và JSON kết quả theo bản đồ chứng cứ ở đầu tài liệu này. Bản phát hành tối giản không có script, dữ liệu thô hoặc checkpoint nên không hứa chạy lại V3 tại chỗ. Nếu cần xem mã gốc, dùng `git show cecd89a:<đường-dẫn>`; muốn chạy lại phải phục hồi đúng mã, môi trường và từng artifact theo SHA-256 trong manifest. Không gọi số liệu đã lưu là một lượt chạy mới.

---

## Biên nhận đánh giá lại sáu backbone V3

Tại mốc kiểm chứng ngày 02–03/10/2026, toàn bộ **06 backbone xác nhận của Chiến dịch Nineplus V3** đã được chạy trích xuất lại trực tiếp từ checkpoint đã huấn luyện trên GPU (`--force-extract`), huấn luyện đầu dò tuyến tính 50 epoch chỉ trên Train, và đánh giá trên 100% tập Validation. Đây là đánh giá lại từ checkpoint, không phải huấn luyện lại Stage A2.

## 1. Môi trường thực thi & Tham số tái lập
- **Phần cứng:** NVIDIA GeForce RTX 3050 Ti Laptop GPU (Compute Capability 8.6).
- **Môi trường tại thời điểm chạy:** Python 3.12.8, PyTorch 2.6.0+cu124, CUDA 12.4. Môi trường CUDA cục bộ này không thuộc gói phát hành.
- **Khóa xác định:** `$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'`.
- **Giao thức:** `TRAIN_FIT_FULL_FIXED_VALIDATION_EVALUATE`. Khóa seed probe tại `10007`.
- **Bất biến tập dữ liệu & Niêm phong Test:**
  * Train Membership SHA (35.000 phiên): `65b76694b0a3cf5c6d684a26899b1e5dca634cfd0985560149feddc12ca8ccfc` (PASS).
  * Val Membership SHA (7.500 phiên): `14cf689f9682a354e104463b9f02806629a683dfdf36d72d88daf5b407b0609a` (PASS).
  * Ordered Train Session-ID SHA: `35396a595ded6ab643c07ce03528da4b91c1d270979b2c52e3e11f0cebcc7e60` (PASS).
  * Ordered Val Session-ID SHA: `4f474991f03aab4856c2666a671bee3fc69d8e893e22e9c2d9ca1269b8bd68ae` (PASS).
  * Trạng thái Test do kịch bản ghi và kiểm tra: `TEST_OPENED=False`, `TEST_READ_COUNT=0` (PASS trong phạm vi lượt chạy này).

## 2. Bảng kết quả kiểm chứng trực tiếp đối chiếu với Word Master

| Kiến trúc | Seed | Thời gian trích xuất Train / Val | AP thực nghiệm | ROC-AUC thực nghiệm | Var(z) | Steps probe | Đối chiếu số công bố | Mã băm SHA-256 Log thực thi |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `SEQUENCE_ONLY` | 42 | 4.35s / 0.77s | **1.0000** | **1.0000** | 0.004535 | 6.850 | Khớp ở mức báo cáo | `09edddd1e1cfa28a683956f73219d9dcb97a8e312233e792c9c4704bdac8f889` |
| `SEQUENCE_ONLY` | 7 | 3.90s / 0.79s | **1.0000** | **1.0000** | 0.005755 | 6.850 | Khớp ở mức báo cáo | `09cc6eb0ebd213595ffe0e053af21877ae64cfe72f175eadc65d663d171941ce` |
| `SEQUENCE_ONLY` | 999 | 3.93s / 0.79s | **1.0000** | **1.0000** | 0.006098 | 6.850 | Khớp ở mức báo cáo | `c97ec35e212e6973fde1062cde0f9c6fef692c6ab8f3f158c4fefe5685810a5c` |
| `MULTI_VIEW_ALIGNED` | 42 | 554.86s / 112.36s | **0.7604** | **0.9946** | 0.005513 | 6.850 | Khớp ở mức báo cáo | `2bc4ddca9b672514647421a0eef2b0cf3c8cae39ed98dce5130d28516f1fc006` |
| `MULTI_VIEW_ALIGNED` | 7 | 572.02s / 116.98s | **0.6309** | **0.8081** | 0.004682 | 6.850 | Khớp ở mức báo cáo | `d8ac393122b3148a5a1b26d212c5c5d1479e2aafbaa04aa4c474c3c8cd28972f` |
| `MULTI_VIEW_ALIGNED` | 999 | 1288.26s / 205.80s | **0.5911** | **0.7693** | 0.008013 | 6.850 | Khớp ở mức báo cáo | `28f5da5868aa3c160ee3b6fd5bcf5a6ba33f8022569dd923a109c6020b09e131` |

## 3. Tổng hợp thống kê & Bất biến khoa học H2
- **Multi-View AP:** $0{,}7604$; $0{,}6309$; $0{,}5911$. Trung bình: $0{,}6608 \pm 0{,}0885$ (độ lệch chuẩn mẫu).
- **Sequence-Only AP:** $1{,}0000$; $1{,}0000$; $1{,}0000$. Trung bình: $1{,}0000 \pm 0{,}0000$.
- **Độ lệch AP (Multi-View trừ Sequence):** $-0{,}2396$; $-0{,}3691$; $-0{,}4089$. Trung bình: $-0{,}3392 \pm 0{,}0885$.
- **Kết luận H2:** Tất cả các cặp seed đều vi phạm sâu biên không thua kém ($-0{,}02$). Lần đánh giá lại từ cùng checkpoint và mã nguồn trên GPU tiếp tục cho thấy H2 **không được hỗ trợ** trên tập Validation HDFS.

## 4. Quản lý trạng thái Git và Lưu trữ bằng chứng
- Sáu log nguyên bản được lưu trong `evidence/V3-GPU-LOGS.zip`; SHA-256 từng log nằm trong bảng trên.
- Sau lần chạy kiểm chứng, các tệp kết quả JSON lịch sử được bảo toàn nguyên trạng mã băm ban đầu; Git working tree được duy trì hoàn toàn sạch.
