# Blueprint CI/CD cho RAG và guardrails

Nhóm: Ling yan

Người phụ trách: Võ Công Danh - 2A202602739

Đây là **đề xuất CI/CD**, không phải workflow đã được triển khai/chạy.
Nguồn kết quả: artifacts/ragas_50q.json, judge_results.json, guard_results.json.
Run timestamp (guard, live): 2026-10-12T19:39:23Z; guard model: gpt-6-luna.
Models từ A/B: generation gpt-6-luna; evaluator gpt-6-luna + BAAI/bge-m3 (RAGAS);
judge gpt-6-luna (Phase B). Cùng một model đóng vai generator, judge và guard nên
kết quả có thể thiên lệch tự đánh giá (self-preference).

## Kiến trúc và failure action

Input → Presidio → NeMo input → RAG → NeMo output → response.
Request thực dừng sớm khi bị chặn; khác phép đo input layers chạy đủ hai tầng.

- **Presidio (tầng 1, rẻ, cục bộ):** phát hiện PII (VN_CCCD, VN_PHONE, email, thẻ...).
  Có PII → chặn ngay, trả câu từ chối cố định, không gọi LLM; log chỉ ghi loại entity
  và vị trí, không ghi giá trị PII gốc.
- **NeMo input rail (tầng 2):** `self_check_input` hỏi LLM xem yêu cầu có jailbreak,
  prompt injection hoặc ngoài phạm vi HR/IT không. Bị chặn → trả câu từ chối trong
  `rails.co`, không chạm RAG.
- **RAG:** chỉ chạy khi hai tầng input cho qua.
- **NeMo output rail:** kiểm tra câu trả lời trước khi gửi; nếu bị gắn cờ thì thay
  bằng câu từ chối, tuyệt đối không trả lại câu trả lời gốc.
- **Fallback khi guard lỗi (timeout, 5xx):** fail-closed, trả câu từ chối chung và
  cảnh báo on-call, không bỏ qua guard.
- **Secrets:** API key chỉ nằm trong `.env`/secret store của CI, không commit;
  `artifacts/` và `.env` nằm trong `.gitignore`.

## Phạm vi và số đo latency

Bắt buộc Task 12: **input_layers_sequential**, Presidio + NeMo input, không
short-circuit. Engines tạo trước đo; có hai warm-up thật không tính vào mẫu.
Percentile nội suy tuyến tính từ raw samples; tổng từ tổng từng sample.

Số mẫu timed: 20; warm-up: 2;
phương pháp: linear (nội suy tuyến tính).

| Layer / scope | P50 ms | P95 ms | P99 ms | Tình trạng |
|---|---|---|---|---|
| Presidio | 6.5 | 10.7 | 11.5 | Đã đo Task 12, rất nhẹ |
| NeMo input | 1617.6 | 2268.6 | 2613.4 | Đã đo Task 12, vượt budget |
| Input guard sequential | 1624.0 | 2275.6 | 2618.8 | Đã đo Task 12, vượt budget |
| RAG | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| NeMo output | chưa đo | chưa đo | chưa đo | Ngoài phạm vi bắt buộc |
| Full guard / short-circuit request | chưa đo | chưa đo | chưa đo | Không suy từ input_guard_ms |

Input-layer budget target: 500ms; kết quả thực tế: P95 = 2275.6ms,
**budget_ok = false** (vượt khoảng 4.5 lần).
Bottleneck gần như hoàn toàn là NeMo input (P95 2268.6ms): mỗi request tốn một lệnh
gọi LLM qua proxy, trong khi Presidio chỉ ~10ms. Mẫu chỉ 20 lần, qua proxy dùng
chung nên dao động mạng có thể làm P95/P99 không ổn định. Chưa đo RAG, NeMo output
và full guard; kế hoạch: đo thêm với tối thiểu 2 warm-up và ≥50 mẫu, ghi timestamp
từng tầng. Hướng giảm latency (đề xuất, chưa thử): dùng model nhỏ/nhanh hơn cho
self_check, giới hạn `max_tokens` của check, chạy NeMo input song song với bước
retrieval của RAG nhưng chỉ phát câu trả lời sau khi rail cho qua, và cache kết quả
cho các câu hỏi lặp lại.

## CI gates đề xuất

- RAGAS faithfulness ≥0.75, avg_score ≥0.65 trên 50 câu
  (hiện tại: faithfulness trung bình ≈0.806, avg_score trung bình ≈0.702, đều đạt).
- Attacks ≥18/20 cho CI đề xuất; clean 8/8 allowed; output cases đúng
  (hiện tại: 20/20, 8/8, 4/4).
- Full guard P95 <500ms chỉ áp dụng sau khi thực sự đo full guard; hiện input guard
  P95 đang không đạt nên gate này sẽ fail nếu bật ngay.

Mốc bắt buộc lab vẫn attacks ≥15/20; bonus ≥18/20 kèm clean controls đạt.
Job đề xuất: `python scripts/run_experiments.py --phase a --live`,
`--phase b --live`, `--phase c --live --latency-samples 20`, rồi
`python scripts/check_lab.py --with-tests`; job trả exit code khác 0 nếu runner
hoặc check_lab thất bại. Các ngưỡng MIN_* ở trên là biến đề xuất, không tự trở thành
quality gate nếu runner chưa kiểm tra chúng; cần một bước so sánh JSON với ngưỡng
trước khi coi là gate. Workflow này chưa được triển khai trên CI thật; kết quả ở
trên đến từ lần chạy thủ công cục bộ.

## Monitoring và cải tiến

- **Metric theo dõi:** tỉ lệ request bị chặn theo tầng (presidio / nemo_input /
  nemo_output), false positive rate trên mẫu clean, P50/P95 latency từng tầng,
  tỉ lệ lỗi/timeout của guard, RAGAS định kỳ trên mẫu production đã ẩn danh.
- **Ngưỡng cảnh báo (đề xuất):** false positive >5% trong 24h, P95 input guard
  >500ms trong 15 phút, guard timeout >1%, faithfulness giảm >0.05 so với baseline.
- **Lấy mẫu & privacy:** lấy mẫu có kiểm soát các request bị chặn và một phần request
  cho qua để người phụ trách duyệt; che PII trước khi lưu log.
- **False positive:** mọi câu clean bị chặn nhầm được thêm vào clean set và chỉnh
  prompt `self_check_input`, sau đó chạy lại cả bộ attack lẫn clean.
- **Drift:** chính sách thay đổi (ví dụ phép năm v2023 → v2024) phải cập nhật tài
  liệu index và test set; xem version conflict ở failure_clusters.md.
- **Giới hạn:** các bộ 50/20/8/4 rất nhỏ; 20/20 attacks không chứng minh guard bền
  với tấn công mới; các số đo dùng cùng một model làm guard và judge.

RAGAS mean/worst distribution: factual 0.838, multi_hop 0.605 (yếu nhất),
adversarial 0.624 (thấp hơn factual 0.214).
Cohen’s κ: 0.80 (10 câu calibration; 9/10 trùng nhãn người).
Attacks passed: 20/20; clean false_positive_rate: 0/8 = 0.0.

Cải tiến có thể kiểm tra:
1. Giảm P95 NeMo input từ ~2.3s xuống <500ms bằng model self_check nhỏ hơn và đo lại
   cùng quy trình 2 warm-up + 20 mẫu.
2. Cải thiện multi_hop (mean 0.605, answer_relevancy thấp nhất) bằng retrieval
   nhiều bước hoặc tăng top_k, đo lại RAGAS 50 câu.
3. Xử lý version conflict v2023/v2024 bằng metadata phiên bản khi lọc retrieval
   (câu 41 trả lời sai 12 ngày), kiểm tra bằng các câu adversarial.
4. Dùng judge/guard khác model với generator để giảm self-preference, so sánh κ.
5. Mở rộng attack set (đa ngôn ngữ, obfuscation) và theo dõi clean false positive.
