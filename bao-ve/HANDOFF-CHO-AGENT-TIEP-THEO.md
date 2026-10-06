# Handoff tại mốc kiểm chứng ngày 02-10-2026

Cập nhật ngày 06-10-2026: bản slide hiện hành là `Bao-cao-chuyen-de-10-slide-v4.pptx`/`.pdf`; kịch bản trình diễn là `KICH-BAN-DEMO-VSCODE.md`. Các tham chiếu v3 bên dưới là trạng thái ở mốc handoff cũ.

## Lệnh của người dùng và điểm dừng

Người dùng yêu cầu **dừng ở mốc gần nhất và viết handoff cho agent khác**. Mốc đã chốt là bộ bảo vệ 10 slide v3 cùng lần kiểm chứng trực tiếp V3 Sequence-Only seed 42. Không tiếp tục chỉnh slide, văn nói, mã nguồn hay chạy thêm thí nghiệm nếu chưa có yêu cầu tiếp theo của người dùng.

## Trạng thái Git và nguồn nội dung

- Repo: `D:\chuyen-de-chuyen-sau`; remote `https://github.com/Minhlike/chuyen-de-chuyen-sau.git`.
- Branch làm việc đã push: `codex/defense-deck-repo-20261002`; `main` không được cập nhật trong đợt này.
- HEAD ban đầu của `main`: `71dd197383c1e48b30288a99ca4112ed5bf3f9d4`.
- Commit lưu bản Word/PDF hiện có: `882cf6cda38a8f0fe0b800b980caae08dc8b283d`.
- Commit bộ bảo vệ và hướng dẫn kiểm chứng: `41e23ed45777a33647aaa9a15f0b8fe5f5e478cd`.
- Commit chứa handoff này và ghi chú chạy lại V3: xem `git log -1` trên branch; khi bàn giao, `git status` phải sạch.
- Word master `Chuyên đề chuyên sâu.docx`: SHA-256 `2425FFB1B8C109A410A93A30E76C99251D234FA20AB33EFBB9922BDC44F0E92F`.
- PDF master `Chuyên đề chuyên sâu.pdf`: SHA-256 `606803EF93BB3C52855EE78D6B8195E0BB263E1272A846A8CA263B025F753D2A`.

Word master mới nhất trong repo là nguồn khoa học duy nhất cho bộ trình bày. Hai tệp master không bị chỉnh nội dung trong đợt làm slide; commit đầu tiên chỉ lưu các thay đổi đang có sẵn trong working tree thành một mốc riêng.

## Sản phẩm đã bàn giao

| Tệp | Mục đích |
| --- | --- |
| `bao-ve/Bao-cao-chuyen-de-10-slide-v3.pptx` | 10 slide, SHA-256 `01E827313979F0FB18A06974C2ADCC974F65210599918CB2E0C1D7B86DE32724` |
| `bao-ve/Bao-cao-chuyen-de-10-slide-v3.pdf` | Bản xuất từ PowerPoint, 10 trang, SHA-256 `7464838DADA870DFF57C3E22FA17DFB76E5AA6589C486CA4A2209A3656523136` |
| `bao-ve/LOI-THUYET-TRINH-15-PHUT.md` | Lời nói cho 10 slide, chia mốc tổng 15 phút; chưa diễn tập bấm giờ thực tế |
| `bao-ve/TU-DIEN-PHAN-BIEN.md` | 40 câu hỏi và trả lời bảo vệ, có giới hạn bằng chứng |
| `bao-ve/BAN-DO-CHUNG-CU.md` | Đường dẫn mở Word, mã nguồn, dữ liệu và kết quả để trình diễn |
| `bao-ve/WORD-MASTER-CLAIMS.json` | Các chỉ số trích từ Word để đối chiếu tự động |
| `bao-ve/V3-SEED42-RERUN-20261002.md` | Biên nhận lần chạy trực tiếp một backbone (seed 42) |
| `bao-ve/V3-ALL-BACKBONES-RERUN-20261003.md` | Biên nhận lần chạy trực tiếp đầy đủ 06 backbone V3 |
| `bao-ve/KICH-BAN-DEMO-VSCODE.md` | Trình tự trình diễn mã nguồn và chứng cứ khoảng 5 phút trong VS Code |
| `HUONG_DAN_CHAY_VA_XAC_MINH.md` | Cách kiểm tra repo và chạy lại trong môi trường hiện tại |

Mã dựng slide nằm ngoài repo tại `C:\Users\Acer\Documents\ChuyenDe-Slides\build\build_deck_v3.mjs`; không tự chép sang repo nếu chưa rà nhu cầu và tính phù hợp. ZIP lưu 13 tệp chỉnh Word/QA cũ đã loại khỏi repo nằm tại `C:\Users\Acer\Downloads\ChuyenDe-document-qa-archive-20261002.zip`. Bản sao DOCX/PDF trước đợt bảo vệ nằm tại `C:\Users\Acer\Downloads\ChuyenDe-backup-truoc-bao-ve-20261002\`.

## Kiểm chứng đã thực hiện

- `python -m pytest tests -q`: 31 PASS; 2 cảnh báo deprecation của PyTorch.
- `python scripts/validate_experiment_index.py`: 9 dòng chỉ mục, 10 artifact trong manifest, PASS.
- `python scripts/verify_reported_results.py`: hash Word, số lượng/split HDFS và các số liệu V3/H1/H2 nêu trong Word khớp artifact đã chỉ định, PASS. Đây là phép đối chiếu tĩnh, không phải chạy lại toàn bộ thí nghiệm.
- DOCX đọc được như ZIP/XML; PDF master 128 trang A4. PowerPoint thật mở và xuất được PDF; 10 trang slide đã xem trực quan, không thấy cắt chữ/hình; bộ finalizer báo 0 lỗi layout/integrity.
- Môi trường CUDA `D:\Research\.venv-stage-a2-cuda\Scripts\python.exe` vượt qua GPU smoke test với `CUBLAS_WORKSPACE_CONFIG=:4096:8`; Python mặc định dùng PyTorch CPU.
- Chạy V3 trực tiếp trên GPU với `--force-extract` cho toàn bộ **06 backbone xác nhận** (Sequence seeds 42, 7, 999; Multi-View seeds 42, 7, 999): trích xuất lại toàn bộ vector Train `[35000,128]` và Validation `[7500,128]`, huấn luyện đầu dò 50 epoch chỉ trên Train, kiểm tra trên 100% Validation. Kết quả AP, ROC-AUC, Var(z) và số bước probe khớp các giá trị công bố ở độ chính xác được báo cáo. Xem chi tiết tại `bao-ve/V3-ALL-BACKBONES-RERUN-20261003.md`.

## Giới hạn bằng chứng phải giữ khi bảo vệ

- Các chỉ số phát hiện thuộc **Validation HDFS**. Test còn niêm phong; không nói đã đánh giá Test hoặc khái quát sang bộ dữ liệu khác.
- Đã chạy trực tiếp lại đủ **sáu** backbone V3 xác nhận; chưa huấn luyện lại Stage A2 từ đầu (pre-training tự giám sát 12 epoch).
- Graph-Only chưa có ba seed xác nhận theo cùng giao thức V3; probe Graph-Only lịch sử không so sánh trực tiếp được với các cấu hình V3 mới.
- H2 không được hỗ trợ bởi Validation HDFS: chênh AP Multi-View trừ Sequence theo ba seed là `−0.2396`, `−0.3691`, `−0.4089`; trung bình `−0.3392 ± 0.0885` (độ lệch chuẩn mẫu), biên không thua kém `−0.02`. AP trung bình Multi-View `0.6608`, Sequence `1.0000`.
- H1 không được đánh giá trực tiếp trên đích token-level vì biểu diễn dùng để thăm dò là vector phiên 128 chiều; masking là tác vụ phụ trợ. H3–H5 chưa được kiểm nghiệm đầy đủ.
- Năm run Stage A2 có sai khác thủ tục so với giao thức chuẩn; không mô tả là 5/5 run canonical. Multi-View seed 999 có sai khác trạng thái RNG khi resume.
- ER1 chỉ có quan sát về bộ nhớ; không kết luận thông lượng/độ trễ streaming. Attention và ví dụ minh họa không chứng minh nhân quả hoặc phát hiện tấn công thực tế.
- Manifest liệt kê 10 artifact, trong đó 7 cache/dữ liệu/checkpoint chỉ có trên máy này. Một clone công khai sạch chưa đủ artifact để chạy V3; không hứa khả năng tái lập đầy đủ nếu chưa cấp phát những tệp đó.

## Việc còn lại nếu người dùng yêu cầu tiếp tục

1. Cho người báo cáo đọc thử lời nói và bấm giờ thực tế; 15 phút hiện là phân bổ biên tập, chưa được xác nhận bằng diễn tập. Chỉnh lời nói theo tốc độ của họ mà không thêm claim.
2. Xin phản hồi trực quan về mật độ 10 slide, đặc biệt slide 2–5 và 10. Nếu chỉnh, giữ nguồn Word và xuất/soát lại toàn bộ PDF.
3. Nếu cần tái lập thêm backbone hoặc Stage A2, lập phạm vi rõ trước khi chạy; dùng bản sao riêng cho artifact đầu ra, tránh ghi đè cache lịch sử. Không mở tập Test khi chưa có giao thức/ủy quyền phù hợp.
4. Nếu chuẩn bị merge/publish, kiểm tra lại diff, hash, Word/slide/source và tình trạng Git; không force-push, không ghi đè `main`, không sửa repo `D:\Research` đang có trạng thái riêng.
5. Giúp người dùng hiểu và tự giải thích thuật toán, dữ liệu, giới hạn và mã chạy; không che giấu sai khác thí nghiệm hay bịa nguồn gốc kết quả.

Không có tác vụ đang chạy cần đợi tại thời điểm handoff. Người dùng đã yêu cầu dừng, nên agent kế tiếp chỉ thực hiện thêm việc khi nhận chỉ dẫn mới.
