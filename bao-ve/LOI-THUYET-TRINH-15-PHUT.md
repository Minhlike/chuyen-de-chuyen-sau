# Lời trình bày chuyên đề — 15 phút

Đọc như đang giải thích công việc mình làm, không đọc nguyên bảng số. Mốc thời gian đã tính cả lúc chuyển slide và dừng ngắn để hội đồng nhìn sơ đồ. Các câu in đậm là chỗ cần nhấn giọng, không phải để đọc to hơn.

## Slide 1 — Câu hỏi nghiên cứu (0:00–0:40)

Kính thưa cô và các thầy cô, em là Đoàn Ngọc Hoàng Minh. Chuyên đề của em nghiên cứu cách tạo đặc trưng từ log để phục vụ phát hiện tấn công. Vấn đề em theo đuổi không chỉ là đổi log thành vector. Em muốn biết khi gom nhiều sự kiện vào một vector thì thông tin an ninh nào còn lại, thông tin nào mất đi, và mình có cách nào kiểm tra điều đó mà không tự đánh lừa bằng một điểm số đẹp. Em xin đi từ câu hỏi ấy đến phương pháp, rồi trình bày kết quả thực nghiệm, kể cả kết quả chưa ủng hộ giả thuyết ban đầu.

## Slide 2 — Vì sao biểu diễn log khó (0:40–2:05)

Một dòng log thường kể được rất ít. Nó cho biết một sự kiện đã xảy ra, nhưng ý nghĩa an ninh của sự kiện ấy còn phụ thuộc vào cái gì xảy ra trước đó, thực thể nào liên quan và tham số cụ thể là gì. Vì vậy, nếu chỉ đếm mẫu hoặc tần suất, ta dễ bỏ sót quan hệ và tham số. Nếu chỉ đọc chuỗi, ta giữ được diễn biến nhưng chưa chắc nhìn rõ các phụ thuộc giữa nhiều thực thể. Nếu dựng đồ thị, quan hệ hiện ra rõ hơn, đổi lại chi phí xử lý tăng lên.

Từ khảo sát ở Chương 1, em rút ra năm khoảng trống. Trên slide em đã đặt chúng ở phía bên phải; trong 15 phút này em tập trung vào ba khoảng trống chi phối cách làm: giữ ngữ nghĩa tham số, kết hợp chuỗi với đồ thị mà không làm hỏng biểu diễn tốt sẵn có, và kiểm soát rò rỉ khi đánh giá. Hai khoảng trống còn lại — nhãn an ninh mức thô và quyền riêng tư — được đưa vào khung thiết kế nhưng chưa có thực nghiệm đầy đủ.

**Một mô hình phức tạp hơn không mặc nhiên học được tín hiệu an ninh tốt hơn.** Muốn nói nó tốt hơn, trước hết phải chỉ rõ tín hiệu cần giữ là gì, rồi đo dưới cùng một cách chia dữ liệu và cùng một giao thức.

## Slide 3 — Hợp đồng Biểu diễn là tiêu chí, không phải lời hứa (2:05–3:25)

Em gọi bộ tiêu chí đó là Hợp đồng Biểu diễn. Nó có ba nhóm điều kiện. Bảo toàn là giữ những thứ có thể mang ý nghĩa an ninh, như tham số lệnh, thứ tự thời gian và quan hệ phụ thuộc. Bất biến là không để những thay đổi vô hại — chẳng hạn một PID ngẫu nhiên hoặc cách ghi thời gian — làm đổi kết luận một cách vô lý. Triệt tiêu là hạn chế dấu vết rò rỉ, dấu vết môi trường thí nghiệm và định danh nhạy cảm mà mô hình có thể lợi dụng để học đường tắt.

Ba từ này dễ nghe như cam kết rằng mô hình đã đạt cả ba. Em không dùng chúng theo nghĩa đó. Đây là **đặc tả những gì cần kiểm tra**. Một phép kiểm tra có thể thất bại, và thất bại ấy vẫn cho ta thông tin. Ví dụ, muốn nói vector giữ tham số, phải có phép đo phù hợp với tham số; chỉ nhìn AP phát hiện bất thường ở cấp phiên thì chưa đủ.

Vì thế, em tách bộ trích xuất khỏi bộ phát hiện. Bộ trích xuất học vector từ log; khi đánh giá thì khóa trọng số của nó, huấn luyện riêng một đầu dò tuyến tính. Cách này đo được thông tin có thể đọc ra bằng một bộ phân loại tuyến tính, chứ không tuyên bố đã khai thác hết mọi thông tin phi tuyến trong vector.

## Slide 4 — Vì sao thử kết hợp chuỗi và đồ thị (3:25–5:00)

Kiến trúc em đề xuất có hai nhánh. Nhánh chuỗi dùng Transformer để giữ thứ tự và ngữ cảnh sự kiện. Nhánh đồ thị dùng Temporal GNN để biểu diễn các quan hệ thực thể biến đổi theo thời gian. Sau đó, hai nhánh được gióng hàng trong không gian chiếu và kết hợp thành vector cho đánh giá hạ nguồn. Trong thiết kế, đầu chiếu và các hàm mất mát phục vụ huấn luyện không phải là toàn bộ chi phí suy luận khi triển khai.

Lý do ghép hai nhánh là hợp lý về mặt bài toán: chuỗi thấy diễn biến, đồ thị thấy phụ thuộc. Nhưng có một giả định cần kiểm tra: **hai nguồn thông tin có thực sự bổ sung cho nhau trên dữ liệu đang xét không?** Nếu nhánh đồ thị nhiễu, hoặc bước gióng hàng ép hai biểu diễn khác bản chất thành quá giống nhau, kết quả có thể giảm. Em không coi sơ đồ kiến trúc là bằng chứng rằng Multi-View sẽ thắng.

Phần suy luận theo dòng ở cuối slide là hướng thiết kế: sự kiện mới đến, trạng thái hữu hạn được cập nhật, rồi tạo vector hiện tại. Trong thực nghiệm HDFS hiện nay em chưa đo toàn trình thông lượng hay độ trễ. Do đó, em chỉ bảo vệ đây là cấu trúc dự kiến cho vận hành, chưa bảo vệ được yêu cầu thời gian thực.

## Slide 5 — Chặn rò rỉ từ khâu chia dữ liệu (5:00–6:15)

Dữ liệu HDFS có hơn 11 triệu bản ghi log, gắn với hơn 575 nghìn phiên khối. Chiến dịch này dùng 35 nghìn phiên Train và 7 nghìn 500 phiên Validation, với cửa sổ ngữ cảnh dài 256 sự kiện. Điểm cần chú ý không chỉ là quy mô, mà là **thứ tự phân chia**: Train ở trước, Validation ở sau theo thời gian; phiên giữa các phân vùng không chồng lấn, và vùng giáp ranh được loại bỏ.

Nếu trộn ngẫu nhiên những phiên có liên hệ thời gian rồi mới chia, ta có nguy cơ cho mô hình nhìn thấy ở Train những dấu vết rất gần với mẫu Validation. Khi ấy điểm số có thể đẹp nhưng câu hỏi nghiên cứu lại bị trả lời sai. Quy trình ở đây cố gắng chặn con đường đó bằng manifest, mã băm danh sách phiên và những bất biến phân chia trong mã nguồn.

Tập Test vẫn niêm phong. Em sẽ nhắc lại giới hạn này ở phần kết quả: những số AP và ROC-AUC sắp trình bày là trên Validation. Chúng có ích để so sánh các nhánh trong cùng phép thử, nhưng chưa phải điểm số cuối cùng trên Test.

## Slide 6 — Huấn luyện tự giám sát và kiểm toán thủ tục (6:15–7:50)

Stage A2 học từ ba bài tập: đoán quan hệ bị che, đoán thuộc tính nút bị che và xử lý khoảng thời gian. Trọng số trong hàm mất mát lần lượt là một, một và không phẩy một. Đây là hệ số thiết kế của mục tiêu, **không phải tỷ lệ đóng góp thực tế** của từng loại thông tin vào khả năng phát hiện tấn công.

Em báo cáo năm lượt chạy với các seed khác nhau. Cột loss cho biết mức tối ưu đối với bài tập tự giám sát của từng lượt. Nhưng khi rà hồ sơ, không lượt nào khớp trọn vẹn mọi điều kiện của giao thức chuẩn: có trường hợp lịch học cũ, dừng sớm, thiếu hồ sơ hoặc mốc commit không đúng kế hoạch đã khóa. Nói như vậy không có nghĩa cả năm lượt “hỏng”; nó có nghĩa em không được phép gọi chúng là năm lần lặp hoàn toàn tương đương rồi lấy trung bình như thể điều kiện giống nhau.

Quan trọng hơn, loss thấp chưa chứng minh biểu diễn có ích cho an ninh. Mô hình có thể giải tốt bài tập che quan hệ nhưng không giúp tách lớp bất thường. Vì vậy, muốn kiểm tra giả thuyết về chất lượng biểu diễn, em chuyển sang đầu dò hạ nguồn với trọng số backbone đã đóng băng.

## Slide 7 — Kết quả V3 và cách đọc AP bằng một (7:50–9:15)

Giao thức V3 dùng sáu bộ trích xuất cố định: ba Sequence-Only và ba Multi-View theo các seed ghép cặp. Với mỗi bộ, đầu dò tuyến tính học trên toàn bộ 35 nghìn vector Train và được đo trên 7 nghìn 500 vector Validation. Trong bước này không có cập nhật trọng số backbone.

Sequence-Only đạt AP bằng một trên cả ba seed. Multi-View đạt khoảng 0,76; 0,63; và 0,59, trung bình 0,6608. AP cho biết thứ hạng của lớp dương trong bài toán này; ROC-AUC nhìn khả năng phân biệt hai lớp trên toàn dải ngưỡng. Kết quả AP bằng một là rất cao, nhưng em chỉ phát biểu đúng phạm vi: **đó là kết quả quan sát trên HDFS Validation theo giao thức V3**. Nó không phải chứng cứ rằng mô hình sẽ không mắc lỗi ở một tập dữ liệu khác.

Điều có thể rút ra ngay từ bảng là Multi-View thấp hơn Sequence-Only ở cả ba seed. Đây là điểm trái với kỳ vọng khi thiết kế kiến trúc. Em không bỏ qua nó; em dùng nó để kiểm tra trực tiếp giả thuyết H2 ở slide sau.

## Slide 8 — H2: kiểm tra bằng biên đã đặt trước (9:15–11:10)

H2 hỏi liệu Multi-View có ít nhất không thua kém Sequence-Only hay không. “Không thua kém” phải có ngưỡng cụ thể, chứ không thể nhìn bảng rồi mới đặt ngưỡng. Trong chuyên đề, biên AP được đặt trước là âm 0,02. Em lấy AP Multi-View trừ AP Sequence theo từng seed. Ba độ lệch là âm 0,2396; âm 0,3691; và âm 0,4089. Cả ba đều vượt xa biên theo chiều bất lợi. Trung bình là âm 0,3392; số cộng trừ đi kèm là độ lệch chuẩn mẫu qua ba seed, không phải khoảng tin cậy.

Có một cách bắt bẻ hợp lý: Sequence thắng vì được nhìn trực tiếp các khe tham số, còn Multi-View thì không. Em đã kiểm tra đúng điểm này bằng cách che tham số của Sequence trên cả Train và Validation, lấy lại biểu diễn rồi huấn luyện một đầu dò mới. Trong phép kiểm tra ấy, AP của Sequence vẫn bằng một ở cả ba seed. Như vậy, lời giải thích “chỉ vì Sequence thấy tham số đầu vào” không phù hợp với kết quả của phép kiểm tra cụ thể này.

Kết luận em bảo vệ là H2 **không được hỗ trợ trong đối chứng HDFS Validation đã thực hiện**. Em không nói mọi mô hình đa góc nhìn đều kém. Ba seed cũng không đủ để tuyên bố ý nghĩa thống kê rộng hoặc quan hệ nhân quả. Nhưng với biên đặt trước và ba cặp quan sát hiện có, em không thể gọi Multi-View là không thua kém.

## Slide 9 — H1: quan sát được phản ứng, chưa chứng minh được ngữ nghĩa (11:10–13:10)

H1 hỏi liệu tham số động có được giữ lại với ý nghĩa an ninh hay không. Trở ngại là nhãn tham số nằm ở cấp token hoặc khe tham số, còn vector mang đi đánh giá là một vector gộp 128 chiều cho cả phiên. Đây là lệch cấp độ mục tiêu. Nếu em dùng điểm phát hiện bất thường cấp phiên để xác nhận H1, em đã trả lời một câu hỏi khác.

Vì chưa đo trực tiếp được, em làm phép thử gián tiếp: giữ nguyên mô hình Sequence, che các khe tham số đầu vào rồi so vector với trường hợp không che. Cosine từ 0,8201 đến 0,9581 và khoảng cách Euclid khác không cho thấy vector đã thay đổi. Nhưng AP phát hiện bất thường vẫn bằng một. Cách đọc đúng là: **vector nhạy với thao tác che tham số; phép thử này chưa cho biết nó hiểu hoặc giữ đúng ngữ nghĩa tham số đến mức nào**. Cũng chưa thể kết luận tham số là vô ích: bài toán hạ nguồn HDFS này có thể được giải bằng những tín hiệu khác.

Ở nửa còn lại là lượt chạy lại thủ công Sequence seed 42. Mô hình chạy sáu epoch; checkpoint tốt nhất ở epoch ba; loss Validation tốt nhất là 0,009218; bộ nhớ GPU đỉnh khoảng 170,45 MB. Hai số AP 0,899385 và 1,0000 nằm cạnh nhau nhưng thuộc hai giao thức khác nhau: một đầu dò nội bộ chia Validation 80/20, và một đầu dò V3 học trên Train rồi đánh giá trên Validation. Em giữ cả hai để người đọc thấy quá trình, đồng thời ghi rõ không được so chúng như hai phép đo đồng nhất.

## Slide 10 — Đóng góp, kết quả âm tính và việc cần làm tiếp (13:10–15:00)

Đóng góp của chuyên đề có ba phần. Thứ nhất là Hợp đồng Biểu diễn: một cách đặt tiêu chí cụ thể cho vector log. Thứ hai là tích hợp kiến trúc chuỗi và đồ thị theo thời gian; em không tuyên bố các khối nguyên thủy như Transformer hay VICReg là thuật toán do em phát minh. Thứ ba là hạ tầng thực nghiệm và đối soát: từ phân chia dữ liệu, đầu dò đóng băng, đến việc công khai các sai lệch thủ tục và kết quả âm tính.

Trạng thái bằng chứng hiện nay cũng phải tách rõ. H1 chưa được kiểm tra trực tiếp; H2 không được hỗ trợ trong đối chứng HDFS Validation; H3 đến H5 chưa có thực nghiệm xác nhận. ER1 mới có quan sát bộ nhớ, chưa có số đo thông lượng và độ trễ. Graph-Only xác nhận mới chưa được huấn luyện theo V3, còn Test vẫn niêm phong.

Theo em, kết quả âm tính ở H2 không làm chuyên đề mất giá trị. Nó chỉ ra đúng chỗ giả định kiến trúc chưa đứng vững: thêm góc nhìn đồ thị đã không tạo ra lợi ích trên phép thử này. Hướng tiếp theo không phải chỉnh cách kể để biến kết quả thành tích cực, mà là đo H1 ở đúng cấp token, tìm nguyên nhân Multi-View giảm hiệu năng, thử trên dữ liệu có cấu trúc quan hệ phong phú hơn, rồi mới mở Test theo giao thức khóa trước. Đó là phạm vi em có thể bảo vệ bằng dữ liệu đang có. Em xin cảm ơn cô và các thầy cô.
