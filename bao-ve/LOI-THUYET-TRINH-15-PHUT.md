# Lời trình bày chuyên đề — 15 phút

Bản nói theo 10 slide. Các mốc để tập bấm giờ; nếu cần rút ngắn, chỉ lược câu chuyển ý, không lược phạm vi của kết quả. Khi chỉ mã trong VS Code, dùng kịch bản riêng `KICH-BAN-DEMO-VSCODE.md` sau phần trình bày.

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

Trước khi nói đến điểm AP, em xin chỉ nguồn của các con số. Ngữ liệu HDFS gốc có 11.175.629 dòng log, gom thành 575.061 phiên khối có nhãn. Đây là quy mô **toàn ngữ liệu**. Phép thử V3 dùng một tập con theo ngân sách: 35.000 phiên Train và 7.500 phiên Validation; không được lấy 11 triệu dòng để gọi là số mẫu huấn luyện của đầu dò.

Trong mã và manifest, phiên được xếp theo thời điểm bắt đầu. Những phiên bắc qua ranh giới Train–Validation hoặc Validation–Test bị loại, rồi mới chọn tập con. Từ vựng được khớp trên Train. Các tệp `SPL-HDFS-001.json` và `SUBSET-MANIFEST-HDFS.json` ghi số lượng, thời gian và mã băm của phép chia; mã thực hiện nằm ở `hdfs_split_authority.py`. Khi cô hỏi có thể mở đúng ba tệp ấy để đối chiếu.

Manifest ghi Test ở trạng thái `SEALED`, chưa vật hóa đặc trưng Test cho người huấn luyện. Phần báo cáo này chỉ dùng kết quả trên Validation. Một tệp manifest không tự chứng minh mọi lần chạy trong lịch sử không bao giờ truy cập Test; điều em có thể trình ra là giao thức, chỉ mục và trạng thái artifact của chiến dịch đang báo cáo.

## Slide 6 — Stage A2: công thức và mã huấn luyện (4:30–6:35)

Bây giờ đến phần mã huấn luyện. Trên slide là công thức đang dùng cho mất mát đồ thị Stage A2: **L_graph bằng L_rel cộng L_node cộng 0,1 lần L_time**. Ba số hạng lần lượt là sai số dự đoán quan hệ bị che, tái tạo thuộc tính nút bị che và dự đoán khoảng thời gian. Trước khi cộng, mã chia tổng sai số từng loại cho số mục tiêu hợp lệ của loại ấy. Thành ra hệ số 0,1 là trọng số trong mục tiêu tối ưu; không thể đọc nó thành “thời gian chỉ đóng góp 10% vào AP”.

Ngay dưới công thức là đoạn từ `stage_a2_trainer.py`, khoảng dòng 261 đến 286: mã tạo `L_graph_group`, gọi `backward()`, kiểm tra gradient, chặn chuẩn gradient nếu cấu hình bật, rồi `optimizer.step()`. Nếu cô hỏi mô hình thực sự học ở đâu, em mở đoạn này và runner `run_nineplus_confirmatory.py`, thay vì chỉ trỏ vào sơ đồ trong Word.

Bảng bên phải là năm lượt chạy Stage A2 được chuyên đề báo cáo. Em không dùng bảng này để xếp hạng mô hình bằng loss, bởi các mục tiêu và điều kiện chạy chưa đồng nhất hoàn toàn. Seed 999 có giai đoạn khởi động khác kế hoạch; seed 42 dùng lịch cũ và dừng ở epoch 4; các lượt còn lại có vấn đề về mốc xác lập giao thức, hồ sơ thực thi hoặc commit. Khi đối chiếu giao thức đã khóa, không lượt nào trong năm lượt đáp ứng đầy đủ điều kiện chuẩn. Vì vậy kết luận đúng là: có năm hồ sơ và năm số loss quan sát được, nhưng không thể gom chúng thành năm phép lặp chuẩn để tuyên bố chất lượng phát hiện. Muốn trả lời bài toán hạ nguồn, em phải sang bước đánh giá vector V3.

## Slide 7 — V3: chỉ đầu dò được cập nhật (6:35–9:20)

Slide này là trọng tâm của phép so. Em lấy sáu checkpoint đã huấn luyện: Sequence-Only và Multi-View, mỗi nhánh ba seed 42, 7, 999. Với từng checkpoint, mã gọi `model.eval()` và trích xuất trong `torch.no_grad()`. Nó tạo ma trận vector Train kích thước 35.000 nhân 128, và Validation 7.500 nhân 128. Hai ma trận này là đầu vào của một lớp tuyến tính `nn.Linear(128,1)`.

Chỗ cần chỉ thật rõ trong mã là `optimizer = AdamW(probe.parameters())`. Bộ tối ưu chỉ nhận tham số của đầu dò, rồi vòng lặp 50 epoch gọi `loss.backward()` và `optimizer.step()` cho đầu dò ấy. Tệp kết quả ghi số bước tối ưu của backbone bằng không. Đây là căn cứ để em nói bộ tạo vector **không được cập nhật trong bước V3**; em không viện ra một dòng `requires_grad_(False)` vì mã không có dòng đó. Điểm đầu dò về mặt toán học là sigmoid của `w` chuyển vị nhân `z` cộng `b`. Sau khi fit trên nhãn Train, mã lấy điểm trên toàn bộ Validation để tính AP và ROC-AUC.

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

Kết quả hiện có không cho phép gọi mô hình đa góc nhìn tốt hơn. Em xin dừng ở điều đã đo được và sẵn sàng mở mã, manifest, bảng kết quả để trả lời câu hỏi của cô.
