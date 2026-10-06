# Lời trình bày chuyên đề — 15 phút

Bản luyện nói theo 10 slide. Mốc thời gian dùng để tập thử; khi luyện nên bấm giờ và nghỉ ngắn ở chỗ xuống đoạn. Chữ in đậm là ý cần nhấn.

## Slide 1 — Câu hỏi nghiên cứu (0:00–0:45)

Kính thưa cô và các thầy cô, em là Đoàn Ngọc Hoàng Minh. Hôm nay em xin trình bày chuyên đề về cách tạo đặc trưng từ log để phục vụ phát hiện tấn công. Thoạt nhìn, việc này giống như chuyển các dòng log thành vector. Nhưng điều em thực sự muốn hỏi là: sau khi gộp nhiều sự kiện vào một vector, những thông tin có ích cho an ninh còn giữ được đến đâu? Và mình kiểm tra việc ấy bằng cách nào, thay vì chỉ thấy điểm đánh giá cao rồi cho rằng mô hình đã học đúng? Em sẽ đi từ câu hỏi đó đến cách làm, sau đó nói thẳng về kết quả thực nghiệm, kể cả chỗ kết quả không đúng với dự kiến ban đầu.

## Slide 2 — Vì sao biểu diễn log khó (0:45–2:15)

Trước hết, vì sao phải nghĩ lại cách biểu diễn log? Một dòng log đứng riêng thường chưa nói được nhiều. Cùng một sự kiện, nhưng xảy ra sau chuỗi nào, gắn với thực thể nào, mang tham số gì, thì ý nghĩa an ninh có thể khác. Nếu chỉ đếm mẫu log, ta thấy tần suất nhưng dễ mất các quan hệ ấy. Nếu đọc theo chuỗi, ta giữ được diễn biến, còn mối phụ thuộc giữa nhiều thực thể thì chưa chắc đã rõ. Đồ thị có thể giúp nhìn quan hệ, nhưng lại tốn thêm chi phí xử lý. Thành ra, chọn cách biểu diễn nào cũng là chọn thứ mình giữ và thứ mình có thể bỏ sót.

Từ phần khảo sát ở Chương 1, em rút ra năm khoảng trống. Trên slide có đủ cả năm; ở đây em xin tập trung vào ba việc dẫn trực tiếp đến thiết kế thực nghiệm: giữ ngữ nghĩa tham số, thử kết hợp chuỗi với đồ thị mà không làm hỏng phần biểu diễn đã tốt, và ngăn rò rỉ dữ liệu khi đánh giá. Hai việc còn lại là nhãn an ninh ở mức thô và quyền riêng tư. Chúng có mặt trong khung thiết kế, nhưng chuyên đề này chưa có thực nghiệm đầy đủ để kết luận về chúng.

**Ý chính của slide này là: thêm một mô hình phức tạp chưa chắc đã tốt hơn.** Trước khi so điểm, mình phải nói rõ muốn vector giữ thông tin gì, rồi đặt các mô hình vào cùng một cách chia dữ liệu và một cách đo.

## Slide 3 — Hợp đồng Biểu diễn là tiêu chí, không phải lời hứa (2:15–4:00)

Từ câu hỏi vừa rồi, em đặt ra Hợp đồng Biểu diễn. Có thể hiểu đây là bộ tiêu chí để hỏi một vector log cần làm được gì. Nhóm thứ nhất là **bảo toàn**: giữ những dấu hiệu có thể mang ý nghĩa an ninh, như tham số lệnh, thứ tự thời gian và quan hệ phụ thuộc. Nhóm thứ hai là **bất biến**: nếu một chi tiết vô hại thay đổi, chẳng hạn PID ngẫu nhiên hoặc cách ghi thời gian, thì kết luận không nên thay đổi một cách vô lý. Nhóm cuối là **triệt tiêu**: hạn chế dấu vết rò rỉ, dấu vết riêng của môi trường thí nghiệm và định danh nhạy cảm mà mô hình có thể bám vào để học đường tắt.

Đến đây em muốn nói rõ một điểm. Ba nhóm ấy là **điều kiện cần đem ra kiểm tra**, chứ không phải lời khẳng định rằng mô hình của em đã đạt cả ba. Chẳng hạn, muốn nói vector giữ được ý nghĩa của tham số, mình phải đo đúng ở cấp tham số. Một điểm AP phát hiện bất thường ở cấp phiên, dù cao, cũng chưa trả lời được câu hỏi đó.

Vì vậy, khi đánh giá, em tách bộ tạo vector ra khỏi bộ phân loại. Em đóng băng trọng số bộ tạo vector, rồi chỉ huấn luyện một đầu dò tuyến tính trên các vector đã có. Nếu đầu dò làm tốt, ta biết thông tin hữu ích có thể đọc ra theo cách tuyến tính. Còn những thông tin phi tuyến khác có hay không, phép đo này tự nó chưa kết luận được. Cách tách ấy cũng giúp em nói đúng phạm vi của mỗi kết quả ở các slide sau.

## Slide 4 — Vì sao thử kết hợp chuỗi và đồ thị (4:00–5:30)

Vậy em thử tạo vector bằng cách nào? Kiến trúc có hai nhánh. Nhánh chuỗi dùng Transformer để đọc thứ tự và ngữ cảnh của sự kiện. Nhánh đồ thị dùng Temporal GNN để biểu diễn quan hệ giữa các thực thể theo thời gian. Sau đó, hai nhánh được gióng hàng trong không gian chiếu và kết hợp thành một vector để đánh giá ở bài toán hạ nguồn. Ở đây cũng cần phân biệt: đầu chiếu và các hàm mất mát là phần dùng khi huấn luyện; chi phí suy luận khi triển khai phải được tính theo đường chạy thực tế, chứ không bê nguyên sơ đồ huấn luyện sang.

Lý do ghép hai nhánh khá dễ hiểu: chuỗi cho ta diễn biến, còn đồ thị cho ta quan hệ. Nhưng “có lý về mặt thiết kế” chưa có nghĩa là chắc chắn hiệu quả. **Câu hỏi thực nghiệm là: trên dữ liệu này, hai nguồn thông tin có bổ sung cho nhau thật không?** Nếu quan hệ đồ thị chứa nhiều nhiễu, hoặc bước gióng hàng làm mất những khác biệt vốn có ích, Multi-View có thể còn kém đi. Vì thế, em đưa nó vào phép so sánh, chứ không mặc định nó sẽ thắng.

Ở cuối slide là hướng suy luận theo dòng: sự kiện mới đi vào, trạng thái hữu hạn được cập nhật, rồi tạo vector tại thời điểm đó. Phần này mới là thiết kế. Với HDFS, em chưa đo toàn trình thông lượng và độ trễ, nên chưa thể nói hệ thống đã đáp ứng yêu cầu thời gian thực.

## Slide 5 — Chặn rò rỉ từ khâu chia dữ liệu (5:30–6:50)

Trước khi xem mô hình học được gì, phải chắc rằng cách chia dữ liệu không làm sai câu trả lời. Bộ HDFS có hơn 11 triệu bản ghi log, tương ứng hơn 575 nghìn phiên khối. Trong chiến dịch này, em dùng 35 nghìn phiên Train, 7 nghìn 500 phiên Validation và cửa sổ ngữ cảnh dài 256 sự kiện. Con số quy mô là một chuyện; **thứ tự chia mới là chỗ cần để ý**. Train nằm trước Validation theo thời gian, các phiên không chồng lấn giữa hai phần, và vùng giáp ranh được loại bỏ.

Nếu trộn ngẫu nhiên những phiên gần nhau rồi mới chia, mô hình có thể đã gặp ở Train dấu vết rất giống những gì nó sẽ thấy ở Validation. Khi đó điểm cao chưa chắc là năng lực khái quát. Để kiểm tra việc chia này, em lưu danh sách phiên trong manifest, mã băm danh sách ấy và các điều kiện bất biến trong mã nguồn. Như vậy, người khác có thể đối chiếu lại thay vì chỉ tin vào mô tả trong báo cáo.

Tập Test vẫn được niêm phong. Vì thế, từ đây đến hết phần kết quả, khi em nói AP hay ROC-AUC thì đó là số trên **HDFS Validation**. Nó dùng để so các nhánh trong cùng phép thử; chưa phải điểm cuối cùng trên Test.

## Slide 6 — Huấn luyện tự giám sát và kiểm toán thủ tục (6:50–8:20)

Sang phần huấn luyện, Stage A2 cho mô hình học từ ba bài tập: dự đoán quan hệ bị che, dự đoán thuộc tính nút bị che và xử lý khoảng thời gian. Trọng số của ba phần trong hàm mất mát lần lượt là 1,0; 1,0; và 0,1. Đây là cách em đặt trọng số cho mục tiêu học, **không phải số đo xem mỗi loại thông tin đóng góp bao nhiêu vào việc phát hiện tấn công**.

Em có báo cáo năm lượt chạy với các seed khác nhau. Nhìn vào cột loss, ta biết mỗi lượt tối ưu bài tập tự giám sát đến đâu. Nhưng khi rà lại hồ sơ chạy, cả năm lượt đều có ít nhất một điểm chưa khớp trọn vẹn với giao thức chuẩn đã khóa: có lượt dùng lịch học cũ, có lượt dừng sớm, có lượt thiếu hồ sơ hoặc mốc commit không đúng kế hoạch. Điều này không có nghĩa là phải bỏ hết số liệu. Nó có nghĩa là em phải ghi đúng hoàn cảnh của từng lượt, không gom chúng thành năm phép lặp hoàn toàn tương đương rồi rút ra một kết luận quá tay.

Thêm một việc nữa: loss thấp chỉ cho thấy mô hình làm tốt các bài tập tự giám sát ấy. Nó chưa chứng minh vector giúp phát hiện bất thường tốt hơn. Muốn biết điều đó, em lấy các backbone đã đóng băng, trích xuất vector và kiểm tra bằng đầu dò tuyến tính. Kết quả của phép kiểm tra này là phần tiếp theo.

## Slide 7 — Kết quả V3 và cách đọc AP bằng một (8:20–9:45)

Ở giao thức V3, em so sáu bộ trích xuất cố định: ba Sequence-Only và ba Multi-View, ghép theo cùng ba seed. Với từng bộ, em tạo 35 nghìn vector Train để học đầu dò tuyến tính, rồi đo trên 7 nghìn 500 vector Validation. Trong suốt bước ấy, backbone không được cập nhật. Em cũng đã chạy lại việc trích xuất và huấn luyện đầu dò từ đủ sáu checkpoint trên GPU; các số thu được khớp với Word ở độ chính xác báo cáo. **Đây là đánh giá lại checkpoint, không phải huấn luyện lại Stage A2.**

Nhìn vào bảng, Sequence-Only đạt AP bằng 1,0000 ở cả ba seed. Multi-View lần lượt khoảng 0,76; 0,63; và 0,59, trung bình là 0,6608. AP phản ánh chất lượng xếp hạng lớp dương; còn ROC-AUC nhìn khả năng phân biệt hai lớp trên nhiều ngưỡng. AP bằng một là kết quả rất cao, nên càng phải nói cho chặt: đây là quan sát trên HDFS Validation theo đúng giao thức V3. Nó không bảo đảm kết quả tương tự trên tập khác, và cũng không tự chứng minh vector đã hiểu mọi tín hiệu an ninh.

Điều rõ nhất ở bảng này là Multi-View thấp hơn Sequence-Only ở cả ba cặp seed. Kết quả ấy ngược với kỳ vọng ban đầu khi em ghép thêm nhánh đồ thị. Vậy thay vì giải thích cho qua, em đem chính sự chênh lệch này kiểm tra giả thuyết H2.

## Slide 8 — H2: kiểm tra bằng biên đã đặt trước (9:45–11:25)

H2 đặt câu hỏi: Multi-View có ít nhất là không thua kém Sequence-Only không? Muốn trả lời thì phải có biên đặt trước, không thể thấy số rồi mới chọn một ngưỡng thuận lợi. Ở đây, biên không thua kém của AP là âm 0,02. Em lấy AP của Multi-View trừ AP của Sequence theo từng seed. Ba độ lệch thu được là âm 0,2396; âm 0,3691; và âm 0,4089. Cả ba đều thấp hơn biên khá xa. Độ lệch trung bình là âm 0,3392; phần cộng trừ đi kèm biểu thị độ lệch chuẩn mẫu qua ba seed, không phải khoảng tin cậy.

Đến đây có một câu hỏi rất đáng đặt ra: liệu Sequence thắng chỉ vì nó nhìn trực tiếp các khe tham số, còn Multi-View thì không? Em đã làm thêm một phép kiểm tra cho đúng nghi vấn ấy. Em che tham số đầu vào của Sequence ở cả Train lẫn Validation, trích xuất lại vector, rồi học một đầu dò mới. AP của Sequence trong phép kiểm tra này vẫn bằng một ở cả ba seed. Như vậy, trong phạm vi phép thử đã làm, cách giải thích “thắng chỉ vì nhìn thấy tham số” không đứng vững. Phép thử này cũng không nói rằng tham số chẳng có ích; hai câu hỏi đó khác nhau.

Cho nên, kết luận của em là **H2 không được hỗ trợ trên đối chứng HDFS Validation đã thực hiện**. Em không suy từ ba seed ra rằng mọi mô hình đa góc nhìn đều kém, cũng không coi đây là chứng minh quan hệ nhân quả. Nhưng với biên đã chốt và ba cặp quan sát hiện có, em không thể gọi Multi-View là không thua kém.

## Slide 9 — H1: quan sát được phản ứng, chưa chứng minh được ngữ nghĩa (11:25–13:20)

Sang H1, câu hỏi lại khác: thông tin tham số động có còn trong vector với đúng ý nghĩa an ninh hay không? Chỗ khó nằm ở cấp độ đo. Nhãn của tham số ở cấp token hoặc khe tham số, còn vector em đem đánh giá là một vector 128 chiều gộp cho cả phiên. Nếu lấy điểm phát hiện bất thường cấp phiên để khẳng định H1, thực ra em đã đổi câu hỏi mà không nói ra.

Vì chưa có phép đo trực tiếp ở cấp tham số, em làm một phép thử gián tiếp. Em giữ nguyên mô hình Sequence, che các khe tham số ở đầu vào, rồi so vector trước và sau khi che. Cosine nằm từ 0,8201 đến 0,9581; khoảng cách Euclid cũng khác không. Nghĩa là vector có phản ứng với thao tác che. Nhưng AP phát hiện bất thường vẫn bằng một. **Điều phép thử cho thấy là vector có thay đổi; điều nó chưa cho thấy là mô hình đã giữ đúng ngữ nghĩa của tham số.** Cũng không thể đảo lại mà bảo tham số vô ích, vì bài toán HDFS ở cấp phiên có thể còn những tín hiệu khác để giải.

Em cũng đưa lên slide lượt chạy lại thủ công của Sequence seed 42 để người đọc thấy thêm một lát cắt của quá trình. Lượt này chạy sáu epoch, checkpoint tốt nhất ở epoch ba; loss Validation tốt nhất là 0,009218 và bộ nhớ GPU đỉnh khoảng 170,45 MB. Có hai số AP dễ bị nhìn thành một phép so: 0,899385 và 1,0000. Thực ra chúng thuộc hai giao thức khác nhau. Số thứ nhất đến từ đầu dò nội bộ chia Validation theo tỷ lệ 80/20; số thứ hai là đầu dò V3 học trên Train rồi đánh giá trên Validation. Em giữ cả hai số, nhưng không coi chênh lệch giữa chúng là mức cải thiện của cùng một thí nghiệm.

## Slide 10 — Đóng góp, kết quả âm tính và việc cần làm tiếp (13:20–15:00)

Đến đây em xin chốt lại chuyên đề đóng góp gì và bằng chứng hiện có đi được đến đâu. Phần thứ nhất là Hợp đồng Biểu diễn: đặt ra những tiêu chí cụ thể để kiểm tra một vector log. Phần thứ hai là thiết kế kết hợp chuỗi với đồ thị theo thời gian. Em dùng các khối như Transformer và VICReg trong thiết kế, chứ không nhận đó là thuật toán do mình phát minh. Phần thứ ba là quy trình thực nghiệm có thể đối soát: từ cách chia dữ liệu, đầu dò với backbone đóng băng, đến việc ghi lại cả sai lệch thủ tục lẫn kết quả không thuận với giả thuyết.

Nếu tách từng giả thuyết ra thì bức tranh hiện nay khá rõ. H1 chưa được kiểm tra trực tiếp ở đúng cấp tham số. H2 không được hỗ trợ trên HDFS Validation. H3 đến H5 chưa có thực nghiệm xác nhận. Với ER1, em mới có quan sát về bộ nhớ, chưa có số đo thông lượng và độ trễ. Graph-Only xác nhận mới chưa được huấn luyện theo V3, và tập Test vẫn niêm phong.

Theo em, kết quả âm tính của H2 không phải điều cần giấu. Nó chỉ đúng chỗ giả định thiết kế chưa được dữ liệu ủng hộ: thêm góc nhìn đồ thị vào đã không mang lại lợi ích trong phép thử này. Việc tiếp theo là đo H1 ở cấp token, tìm xem vì sao Multi-View giảm hiệu năng, thử trên dữ liệu có quan hệ phong phú hơn, rồi mới mở Test theo giao thức đã khóa trước. Em xin dừng ở những kết luận mà số liệu hiện có thực sự cho phép. Em cảm ơn cô và các thầy cô đã lắng nghe.
