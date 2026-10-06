# Kịch bản trình diễn trong VS Code (khoảng 5 phút)

Mở thư mục `D:\chuyen-de-chuyen-sau` bằng VS Code. Giữ sẵn `bao-ve/Bao-cao-chuyen-de-10-slide-v4.pptx` và Word master ngoài VS Code. Các slide 5–10 đã có bảng số và địa chỉ tệp; phần mở mã chỉ cần chứng minh đường đi **dữ liệu → hàm mất mát → đầu dò → kết quả → giới hạn**. Không chạy lại sáu lượt `--force-extract` trước hội đồng: các lượt Multi-View đã mất nhiều phút và có thể ghi lại artifact.

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

1. `datasets/manifests/SPL-HDFS-001.json`: giao thức chia theo thời gian và số bản ghi/phiên toàn ngữ liệu. Mở tiếp `datasets/manifests/SUBSET-MANIFEST-HDFS.json` để chỉ đúng ngân sách chọn 35.000 Train, 7.500 Validation, ranh giới thời gian và trạng thái Test `SEALED`. Mã phân chia: `src/research_agent/experiments/data/hdfs_split_authority.py`.
2. `src/research_agent/experiments/training/stage_a2_trainer.py`: mở dòng 261–286 để thấy từng loss được chia cho số mục tiêu hợp lệ, tổng `1,0 / 1,0 / 0,1`, rồi `backward()` và `self.optimizer.step()` khi huấn luyện. Runner là `scripts/run_nineplus_confirmatory.py`. Với Multi-View, `src/research_agent/experiments/extractor/multi_view.py` dòng 329–340 tính VICReg trong đường huấn luyện; dòng 215–249 cho thấy đường trích xuất dùng `self.fusion(z_seq, z_graph_batch)`.
3. `scripts/evaluate_nineplus_v3.py`: mở dòng 187–191 hoặc 247–251 để thấy `model.eval()` và `torch.no_grad()` khi trích xuất; dòng 277–279 xác nhận kích thước `[35000,128]`/`[7500,128]`; dòng 306–327 cho thấy `nn.Linear(128,1)`, `AdamW(probe.parameters())` và bước cập nhật đầu dò. Mã **không có** lệnh `requires_grad_(False)` cho backbone; phát biểu chính xác là backbone không có bước cập nhật trong V3. Seed đầu dò `10007`, 50 epoch. Đây là **đánh giá lại checkpoint**, không phải huấn luyện lại Stage A2.
4. `experiments/nineplus/evaluation_v3/V3_SIX_BACKBONE_EVALUATION_SUMMARY.json` cùng Bảng 3.6 trong Word: đối chiếu AP/ROC-AUC của sáu hàng ở bốn chữ số thập phân. Biên nhận chạy trực tiếp: `bao-ve/V3-ALL-BACKBONES-RERUN-20261003.md`; log đầy đủ nằm ngoài Git tại `C:\Users\Acer\Downloads\ChuyenDe-backup-truoc-bao-ve-20261002\`.
5. `experiments/nineplus/evaluation_v3/H2_SEQUENCE_NOPARAM_SENSITIVITY.json` cùng Bảng 3.7/3.10: ba chênh lệch AP Multi-View trừ Sequence đều âm (`−0,2396`, `−0,3691`, `−0,4089`) và đều thấp hơn biên `−0,02`. Nếu hỏi H1, mở `experiments/nineplus/evaluation_v3/h1_ablation/H1_FROZEN_MASKING_ABLATION_SUMMARY.json` cùng Bảng 3.9: vector thay đổi khi che tham số, còn AP cấp phiên không đổi.

## 3. Nếu được yêu cầu xem dữ liệu gốc

Tệp gốc nằm ngoài Git tại `D:\Research\datasets\raw\hdfs\`. Trên máy này, mã băm SHA-256 của `HDFS_1.tar.gz` là `6ca6c5bc2671c66afecee9369a2fdac606bf33997a2494ac66aa411fe3e95169`, của `anomaly_label.csv` là `1c711ed6c8848fc3243fb4d092f172f31d128c8a6ec7f26ebba72ab931885ed8`; cả hai khớp `SPL-HDFS-001.json`. Không mở tệp nén trong editor. Để cho xem ba dòng log và vài nhãn bằng terminal:

```powershell
Get-Content 'D:\Research\datasets\raw\hdfs\anomaly_label.csv' -TotalCount 5
python -c "import tarfile; t=tarfile.open(r'D:\Research\datasets\raw\hdfs\HDFS_1.tar.gz','r:gz'); f=t.extractfile('HDFS.log'); [print(f.readline().decode('utf-8',errors='replace').rstrip()) for _ in range(3)]; t.close()"
```

Một dòng log là một sự kiện; nhãn gắn với `BlockId`/phiên khối. Không đồng nhất 11.175.629 dòng log với 575.061 phiên khối hoặc với tập con 35.000/7.500 phiên dùng trong V3. Nếu sang máy khác, các đường dẫn cục bộ trên không tồn tại cho đến khi cấp phát tệp đúng hash.

## 4. Câu nói ngắn khi chỉ mã và kết quả

“Em tách phiên HDFS thành Train, Validation và Test theo manifest này. Mỗi checkpoint được dùng để trích xuất vector 128 chiều; đầu dò tuyến tính chỉ học trên 35.000 phiên Train, rồi đo trên 7.500 phiên Validation. Em đã chạy lại bước trích xuất và đầu dò cho cả sáu checkpoint trên GPU; các chỉ số in ra khớp số đã báo cáo ở độ chính xác trình bày. Ba seed Sequence đều đạt AP 1,0000; Multi-View là 0,7604, 0,6309 và 0,5911. Vì vậy H2 không được hỗ trợ trong đối chứng HDFS Validation này. Em không suy từ kết quả ấy sang Test hay bộ dữ liệu khác.”

## 5. Nếu bị hỏi sâu

- **“Dữ liệu thô ở đâu?”** Kho lưu gốc ở `D:\Research\datasets\raw\hdfs\`; hash của hai tệp gốc nằm trong `SPL-HDFS-001.json`. Cache, nhãn đầu dò và checkpoint cục bộ được kiểm kê trong `experiments/nineplus/ARTIFACT-MANIFEST.json`. Clone sạch cần cấp phát đủ artifact theo hash mới chạy được V3.
- **“Mã huấn luyện ở đâu?”** Mở `src/research_agent/experiments/training/stage_a2_trainer.py`, rồi `scripts/run_nineplus_confirmatory.py` và manifest của một run trong `experiments/nineplus/confirmatory/`. Chỉ ra ba tác vụ tự giám sát và trọng số 1,0 / 1,0 / 0,1; nói rõ năm run có sai khác thủ tục, không nhận là năm lần lặp chuẩn đồng nhất.
- **“Em huấn luyện lại từ đầu chưa?”** Chưa. Sáu lượt ngày 02–03/10 trích xuất từ checkpoint đã huấn luyện và fit lại đầu dò; Stage A2 chưa được huấn luyện lại.
- **“Sao Multi-View kém hơn?”** Kết quả cho thấy kém ở phép đo này; chưa đủ thí nghiệm để quy kết một nguyên nhân duy nhất. Chỉ ra các sai khác thủ tục Stage A2 và seed 999 trong Word nếu được hỏi.
- **“AP 1,0 có chứng minh mô hình hoàn hảo?”** Không. Đây là HDFS Validation theo cách chia hiện tại; Test chưa được mở để đánh giá trong phạm vi chuyên đề.
- **“Graph-Only đâu?”** Chưa có ba run Graph-Only xác nhận theo cùng giao thức V3; không xếp hạng probe lịch sử với sáu kết quả này.

Lúc trình diễn, ưu tiên mở **đúng tệp chứng cứ** mà câu hỏi cần. Không chạy `evaluate_nineplus_v3.py --force-extract` trực tiếp trên cây artifact gốc trong buổi bảo vệ: lệnh có thể kéo dài và ghi lại cache/JSON.
