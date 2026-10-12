# Nhóm thực hiện K4 Track 3B

Tên nhóm: LingYan

Repo chung: https://github.com/lingyan26ai/K4-Track-3B-Day24-Eval-Guard

Trưởng nhóm/người nộp: Võ Công Danh - 2A202602739

Ngày lab/deadline áp dụng: 12:00 trưa 13/10/2026 (theo thông báo của coach/giảng viên) — Asia/Ho_Chi_Minh (UTC+07:00)

Commit dùng để chấm: commit mới nhất (HEAD) của nhánh main tại thời điểm nộp link repo

Mỗi nhóm nộp một repo. Nhóm chỉ có một thành viên.

## Thành viên và phân công

| STT | Họ và tên | MSSV | Vai trò / công việc thật | Bằng chứng |
|---|---|---|---|---|
| 1 | Võ Công Danh | 2A202602739 | Toàn bộ Phase A, B, C; chạy batch; viết 3 báo cáo | Lịch sử commit trong repo, artifacts/ và doc/reports/ |

Người tích hợp/chạy batch/nộp link: Võ Công Danh, chạy các lệnh scripts/run_experiments.py và scripts/check_lab.py trên máy cá nhân.

## Môi trường và chuẩn bị trước lớp

OS/Python/compiler: Windows, Python 3.11 (venv), Microsoft C++ Build Tools (MSVC) để build annoy.
Virtualenv/dependencies/imports: .venv cài từ requirements đã pin (NumPy 1.26.4, pyarrow 17.0.0, RAGAS 0.1.22, NeMo Guardrails 0.10.0); `scripts/check_lab.py --with-tests` cho 86 test offline pass.
Models/Qdrant/50 answers đã chuẩn bị: Qdrant v1.9.7, embedding BAAI/bge-m3, 50 câu trả lời sinh live bằng model gpt-6-luna qua proxy tương thích OpenAI (gpt-4o-mini trả 503 model_not_found nên không dùng). Lần chạy đầu bị rơi vào extractive_fallback; đã sinh lại và xác nhận 50/50 là câu trả lời LLM. Phase A, B, C đều đã chạy live thành công.
Các sửa đổi môi trường: config.py thêm OPENAI_BASE_URL và biến model; m2_search tương thích qdrant-client <1.10; m4_eval import torch trước ragas (lỗi WinError 1114); NeMo dùng engine chat đăng ký riêng vì tên model gpt-6-luna khiến NeMo gọi nhầm endpoint completions.

## INDIVIDUAL

### VoCongDanh-2A202602739

- Phần được giao và phần thực tế đã làm: toàn bộ 13 hàm TODO trong src/phase_a_ragas.py, src/phase_b_judge.py, src/phase_c_guard.py; chuẩn bị môi trường; sinh 50 câu trả lời; viết failure_clusters.md, bias_report.md, blueprint.md.
- Bằng chứng: commit trong repo và artifacts/ragas_50q.json, judge_results.json, guard_results.json cùng 3 báo cáo trong doc/reports/.
- Cách kiểm tra: 86 unit test offline pass; chạy live `scripts/run_experiments.py --phase a|b|c --live`; Phase C đạt 20/20 tấn công bị chặn, 8/8 clean được cho qua, 4/4 ca output đúng; Cohen’s κ = 0.80 trên 10 câu; kiểm tra cuối bằng scripts/check_lab.py.
- Điều đã học: đánh giá RAG theo bốn metric RAGAS và phân cụm lỗi theo loại câu hỏi; LLM-as-judge cần swap-and-average để giảm position bias và cần hiệu chỉnh bằng nhãn người (κ); guardrail nhiều tầng (Presidio cho PII, NeMo cho jailbreak/ngoài phạm vi) và đánh đổi độ trễ.
- Giới hạn/cách xử lý: input guard P95 khoảng 2276 ms, vượt ngưỡng 500 ms (ghi rõ trong blueprint); judge, generator và guard dùng cùng một model nên có thể thiên lệch; các bộ test nhỏ (50/20/8/4/10 câu) nên kết luận chỉ mang tính tham khảo.
- Nguồn/AI hỗ trợ nếu có: Claude (Anthropic) hỗ trợ viết code các hàm, gỡ lỗi môi trường và soạn báo cáo. Kết quả số liệu lấy từ các lần chạy live của chính tôi trên máy; tôi tự chạy kiểm thử và đọc lại nội dung báo cáo trước khi nộp.

## Cập nhật sau khi nộp

Không có cập nhật sau khi nộp tại thời điểm viết file này. Nếu sửa sau deadline, sẽ ghi commit, thời điểm, lý do và báo coach để được phép áp dụng bản cập nhật.
