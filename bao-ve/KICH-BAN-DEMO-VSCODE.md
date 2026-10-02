# Kịch bản trình diễn trong VS Code (khoảng 5 phút)

Mở thư mục `D:\chuyen-de-chuyen-sau` bằng VS Code. Giữ sẵn PowerPoint và Word master ngoài VS Code; buổi trình diễn mã nguồn chỉ cần chứng minh đường đi **dữ liệu → mô hình → đầu dò → kết quả → giới hạn**. Không chạy lại sáu lượt `--force-extract` trước hội đồng: các lượt Multi-View đã mất nhiều phút và có thể ghi lại artifact.

## 1. Trước giờ báo cáo

Trong terminal PowerShell của VS Code:

```powershell
cd D:\chuyen-de-chuyen-sau
git status --short --branch
python scripts/validate_experiment_index.py
python scripts/verify_reported_results.py
```

Kiểm tra branch, cây làm việc sạch và hai lệnh hiện PASS. Lệnh đầu đối chiếu chỉ mục cùng mã băm artifact cục bộ; lệnh sau đối chiếu các số trong Word với kết quả đã lưu. **Cả hai là kiểm tra tĩnh**, không chạy mô hình và không chứng minh mọi hoạt động trước đây với tập Test. Nếu cần xác nhận GPU, dùng môi trường CUDA đúng trên máy này:

```powershell
$env:CUBLAS_WORKSPACE_CONFIG = ':4096:8'
& 'D:\Research\.venv-stage-a2-cuda\Scripts\python.exe' scripts/gpu_smoke_test.py
```

Nếu một lệnh không PASS, dừng phần trình diễn đó và nói đúng lỗi; không dùng ảnh chụp hoặc báo cáo cũ để thay kết quả hiện tại.

## 2. Các tab nên ghim sẵn

1. `datasets/manifests/SPL-HDFS-001.json`: chỉ Train 35.000 và Validation 7.500 phiên, Test niêm phong trong phạm vi giao thức. Mã phân chia: `src/research_agent/experiments/data/hdfs_split_authority.py`.
2. `src/research_agent/experiments/extractor/sequence_view.py`, `src/research_agent/experiments/models/temporal_graph_view_encoder.py`, `src/research_agent/experiments/extractor/multi_view.py`: chỉ đường đi từ chuỗi log sang vector; mở sâu một nhánh đúng câu hỏi của cô, không cuộn cả ba tệp.
3. `scripts/evaluate_nineplus_v3.py`: chỉ cấu hình sáu checkpoint (cuối tệp), biểu diễn Train/Validation `[35000,128]`/`[7500,128]`, seed đầu dò `10007`, 50 epoch; backbone ở chế độ đánh giá, chỉ đầu dò được fit. Nói rõ đây là **đánh giá lại checkpoint**, không phải huấn luyện lại Stage A2.
4. `experiments/nineplus/evaluation_v3/V3_SIX_BACKBONE_EVALUATION_SUMMARY.json` cùng Bảng 3.6 trong Word: đối chiếu AP/ROC-AUC của sáu hàng ở bốn chữ số thập phân. Biên nhận chạy trực tiếp: `bao-ve/V3-ALL-BACKBONES-RERUN-20261003.md`; log đầy đủ nằm ngoài Git tại `C:\Users\Acer\Downloads\ChuyenDe-backup-truoc-bao-ve-20261002\`.
5. `experiments/nineplus/evaluation_v3/H2_SEQUENCE_NOPARAM_SENSITIVITY.json` cùng Bảng 3.7/3.10: ba chênh lệch AP Multi-View trừ Sequence đều âm (`−0,2396`, `−0,3691`, `−0,4089`) và đều thấp hơn biên `−0,02`.

## 3. Câu nói ngắn khi chỉ mã và kết quả

“Em tách phiên HDFS thành Train, Validation và Test theo manifest này. Mỗi checkpoint được dùng để trích xuất vector 128 chiều; đầu dò tuyến tính chỉ học trên 35.000 phiên Train, rồi đo trên 7.500 phiên Validation. Em đã chạy lại bước trích xuất và đầu dò cho cả sáu checkpoint trên GPU; các chỉ số in ra khớp số đã báo cáo ở độ chính xác trình bày. Ba seed Sequence đều đạt AP 1,0000; Multi-View là 0,7604, 0,6309 và 0,5911. Vì vậy H2 không được hỗ trợ trong đối chứng HDFS Validation này. Em không suy từ kết quả ấy sang Test hay bộ dữ liệu khác.”

## 4. Nếu bị hỏi sâu

- **“Dữ liệu thô ở đâu?”** Tệp lớn và checkpoint không nằm trong Git; chỉ có trên máy này và được kiểm kê bằng `experiments/nineplus/ARTIFACT-MANIFEST.json`. Clone sạch cần cấp phát đủ artifact theo hash mới chạy được V3.
- **“Em huấn luyện lại từ đầu chưa?”** Chưa. Sáu lượt ngày 02–03/10 trích xuất từ checkpoint đã huấn luyện và fit lại đầu dò; Stage A2 chưa được huấn luyện lại.
- **“Sao Multi-View kém hơn?”** Kết quả cho thấy kém ở phép đo này; chưa đủ thí nghiệm để quy kết một nguyên nhân duy nhất. Chỉ ra các sai khác thủ tục Stage A2 và seed 999 trong Word nếu được hỏi.
- **“AP 1,0 có chứng minh mô hình hoàn hảo?”** Không. Đây là HDFS Validation theo cách chia hiện tại; Test chưa được mở để đánh giá trong phạm vi chuyên đề.
- **“Graph-Only đâu?”** Chưa có ba run Graph-Only xác nhận theo cùng giao thức V3; không xếp hạng probe lịch sử với sáu kết quả này.

Lúc trình diễn, ưu tiên mở **đúng tệp chứng cứ** mà câu hỏi cần. Không chạy `evaluate_nineplus_v3.py --force-extract` trực tiếp trên cây artifact gốc trong buổi bảo vệ: lệnh có thể kéo dài và ghi lại cache/JSON.
