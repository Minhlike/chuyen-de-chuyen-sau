# Từ điển bảo vệ và trả lời phản biện

Đây là tài liệu ôn tập, không phải lời để đọc nguyên văn. Mỗi câu trả lời đi theo ba bước: **khẳng định đúng phạm vi → chỉ bằng chứng → nêu giới hạn**. Nếu không biết, mở đúng mã nguồn hoặc tệp kết quả trong `BAN-DO-CHUNG-CU.md`; không suy đoán thay cho dữ liệu.

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

Repo Git chỉ lưu manifest và mã nguồn; tệp HDFS thô và các tensor/checkpoint lớn không nằm trong Git. Trên máy hiện tại có các artifact cục bộ đã được liệt kê và kiểm mã băm. Một bản clone sạch từ Internet **chưa tự chạy được V3** nếu chưa nạp các artifact đó. Mở `experiments/nineplus/ARTIFACT-MANIFEST.json` để chỉ từng tệp, dung lượng và SHA-256.

### 20. Tại sao Train chỉ 35.000 phiên khi bộ dữ liệu có 575.061 phiên?

575.061 là quy mô toàn ngữ liệu. 35.000 Train và 7.500 Validation là ngân sách phiên của chiến dịch được báo cáo, lấy theo thứ tự thời gian sau khi áp dụng quy tắc phân chia. Không đồng nhất “toàn ngữ liệu” với “toàn bộ phiên dùng để fit probe”. Bản Word: Mục 3.1.2, Bảng 3.2.

### 21. Chặn rò rỉ dữ liệu bằng cách nào?

Các phiên được sắp theo thời gian; Train đi trước Validation; phiên qua ranh giới bị loại; danh tính phiên không chồng lấn. Manifest và cache split lưu mã băm danh sách, còn mã nguồn kiểm các bất biến này khi chạy. Điều đó giảm các đường rò rỉ đã nhận diện, không phải bằng chứng tuyệt đối rằng mọi kiểu rò rỉ đều không thể xảy ra. Mã: `src/research_agent/experiments/data/hdfs_split_authority.py`.

### 22. Test niêm phong nghĩa là gì?

Các biến kiểm soát chiến dịch ghi `test_opened=false`, `test_reads=0`, và mã đánh giá V3 chỉ làm việc với Train/Validation. Đây là trạng thái được ghi nhận trong giao thức và artifact; không phải lời bảo đảm vượt quá chứng cứ. Nếu hội đồng yêu cầu điểm Test, câu trả lời đúng là chưa có trong chuyên đề này.

### 23. Frozen Linear Probe kiểm tra cái gì?

Nó khóa backbone, lấy vector cố định, chỉ huấn luyện một bộ phân loại tuyến tính bằng nhãn Train và đo trên Validation. Nó kiểm tra tín hiệu **có thể phân tách tuyến tính** từ vector theo giao thức đó. Nó không đo mọi tương quan phi tuyến và không chứng minh bộ trích xuất tự nó là một bộ phát hiện hoàn chỉnh. Mã: `scripts/evaluate_nineplus_v3.py`.

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

Mở `README.md` và `BAN-DO-CHUNG-CU.md`. Chạy `python scripts/validate_experiment_index.py` để đối soát JSON/CSV; lệnh này không cần GPU. Sau đó xác nhận Python đang dùng là môi trường CUDA, chạy `gpu_smoke_test.py`, kiểm mã băm artifact và chỉ khi tất cả điều kiện đạt mới chạy đánh giá V3. Nếu dùng Python mặc định bản CPU, lệnh GPU sẽ thất bại đúng thiết kế; không đổi câu chuyện thành “mã nguồn hỏng”.
