# Phân tích lỗi Phase A

Nhóm: Ling yan

Người phụ trách: Võ Công Danh - 2A202602739

Nguồn: `artifacts/ragas_50q.json`; run timestamp: 2026-10-12T18:47:01.667607+00:00 (01:47 ngày 13/10/2026 giờ Việt Nam).
Generation mode/fallback và điều kiện chạy: 50/50 answers có `generation_mode = llm`, không dùng extractive fallback. Lần sinh answers đầu tiên đã bị loại bỏ vì cả 50 câu rơi vào fallback (proxy trả `model_not_found` cho `gpt-4o-mini`); nhóm đổi sang model có sẵn trên proxy, xóa file cũ và sinh lại. Qdrant v1.9.7 và BGE-M3 chạy trên máy nhóm, mỗi câu lấy 3 contexts sau rerank (`RERANK_TOP_K = 3`).
Models generation/evaluator: generation `gpt-6-luna`; evaluator `BAAI/bge-m3, gpt-6-luna` (LLM của RAGAS và embedding). Generator và evaluator cùng một LLM, xem phần giới hạn.

## Điểm theo distribution

| Metric | factual (20) | multi_hop (20) | adversarial (10) |
|---|---|---|---|
| faithfulness | 0.925 | 0.727 | 0.725 |
| answer_relevancy | 0.827 | 0.458 | 0.614 |
| context_precision | 0.867 | 0.725 | 0.733 |
| context_recall | 0.733 | 0.512 | 0.425 |
| avg_score | 0.838 | 0.605 | 0.624 |

multi_hop thấp nhất (0.605), adversarial thấp thứ hai (0.624), factual cao nhất (0.838). Khoảng cách lớn nhất nằm ở `answer_relevancy` (factual 0.827 so với multi_hop 0.458) và `context_recall` (factual 0.733, adversarial 0.425).

## Bottom 10 và nguyên nhân

| Rank | ID | Distribution | avg_score | worst_metric | Câu hỏi | Diagnosis (Task 3) | Suggested fix (Task 3) |
|---|---|---|---|---|---|---|---|
| 1 | 41 | adversarial | 0.125 | faithfulness | Nhân viên được nghỉ bao nhiêu ngày phép năm? | LLM hallucinating (faithfulness=0.00); câu bẫy (policy cũ/mới, điều kiện phủ định) — dễ lấy nhầm phiên bản cũ | Tighten system prompt, lower temperature |
| 2 | 27 | multi_hop | 0.150 | answer_relevancy | Nhân viên có thâm niên 7 năm theo v2024 được nghỉ bao nhiêu ngày phép? Nếu bị trừ thêm 4 ngày ốm không có giấy y tế thì còn lại bao nhiêu? | Answer doesn't match question (answer_relevancy=0.00); câu multi-hop cần ghép nhiều tài liệu — top_k nhỏ dễ thiếu một vế | Improve prompt template |
| 3 | 33 | multi_hop | 0.250 | faithfulness | Nhân viên Manager có thâm niên 12 năm: tổng phụ cấp hàng tháng và số ngày phép năm theo v2024 là bao nhiêu? | LLM hallucinating (faithfulness=0.00); câu multi-hop cần ghép nhiều tài liệu — top_k nhỏ dễ thiếu một vế | Tighten system prompt, lower temperature |
| 4 | 42 | adversarial | 0.250 | faithfulness | Thâm niên bao nhiêu năm thì được cộng thêm ngày phép? | LLM hallucinating (faithfulness=0.00); câu bẫy (policy cũ/mới, điều kiện phủ định) — dễ lấy nhầm phiên bản cũ | Tighten system prompt, lower temperature |
| 5 | 2 | factual | 0.250 | faithfulness | Bảo hiểm sức khỏe PVI có hạn mức bao nhiêu cho nhân viên? | LLM hallucinating (faithfulness=0.00); câu factual một nguồn — lỗi thường do chunk chứa con số bị cắt hoặc rerank sai | Tighten system prompt, lower temperature |
| 6 | 25 | multi_hop | 0.333 | faithfulness | Lương thử việc của nhân viên Junior mức cao nhất là bao nhiêu? | LLM hallucinating (faithfulness=0.00); câu multi-hop cần ghép nhiều tài liệu — top_k nhỏ dễ thiếu một vế | Tighten system prompt, lower temperature |
| 7 | 46 | adversarial | 0.333 | answer_relevancy | Nhân viên thử việc có được nghỉ phép năm không? | Answer doesn't match question (answer_relevancy=0.00); câu bẫy (policy cũ/mới, điều kiện phủ định) — dễ lấy nhầm phiên bản cũ | Improve prompt template |
| 8 | 40 | multi_hop | 0.400 | answer_relevancy | Nhân viên cấp Manager có thời hạn thử việc 90 ngày, đang trong tháng thứ 3, phát hiện vi phạm bảo mật. Họ nên và không nên làm gì theo chính sách? | Answer doesn't match question (answer_relevancy=0.00); câu multi-hop cần ghép nhiều tài liệu — top_k nhỏ dễ thiếu một vế | Improve prompt template |
| 9 | 39 | multi_hop | 0.452 | context_precision | So sánh yêu cầu mật khẩu giữa policy v1.0 và v2.0 về độ dài tối thiểu, thời hạn đổi và MFA. | Too many irrelevant chunks (context_precision=0.00); câu multi-hop cần ghép nhiều tài liệu — top_k nhỏ dễ thiếu một vế | Add reranking or metadata filter |
| 10 | 38 | multi_hop | 0.457 | faithfulness | Nhân viên đi công tác nước ngoài 4 ngày tại thành phố lớn, ở khách sạn 200 USD/đêm (3 đêm). Công ty thanh toán bao nhiêu tiền khách sạn? | LLM hallucinating (faithfulness=0.00); câu multi-hop cần ghép nhiều tài liệu — top_k nhỏ dễ thiếu một vế | Tighten system prompt, lower temperature |

Cột Diagnosis và Suggested fix là đầu ra Task 3 giữ nguyên từ JSON. Đối chiếu từng câu với answer, contexts và reference cho thấy diagnosis theo `worst_metric` chỉ mô tả metric, chưa phải nguyên nhân thật. Nguyên nhân quan sát được chia thành bốn nhóm.

**1. Pipeline từ chối trả lời dù context có đáp án.** Có 10/50 answers bắt đầu bằng "Không tìm thấy" (6 multi_hop, 3 adversarial, 1 factual), điểm trung bình của nhóm này là 0.334 so với 0.794 của 40 câu còn lại, và chúng chiếm 7/10 câu bottom 10. Trong đó:
- Câu 42 ("Thâm niên bao nhiêu năm thì được cộng thêm ngày phép?"): context 1 ghi rõ nhân viên "có thâm niên từ **3 năm trở lên** được cộng thêm **1 ngày phép** cho mỗi 3 năm", đúng reference, nhưng answer là "Không tìm thấy."
- Câu 41 ("Nhân viên được nghỉ bao nhiêu ngày phép năm?"): contexts lấy về cả chính sách v2023 lẫn v2024; context 2 (v2024) ghi "15 ngày phép năm, tăng từ 12 ngày so với chính sách năm 2023". Model không chọn v2024 mà từ chối. Đây là bẫy version conflict và pipeline chưa xử lý được.
- Câu 25 (lương thử việc Junior cao nhất): contexts có khung lương Junior 12.000.000 đến 20.000.000 và mức thử việc 85%, đủ để tính 17.000.000, nhưng answer từ chối. Câu này cần ghép hai dữ kiện rồi nhân, và model không làm.
- Với các câu từ chối hoàn toàn, RAGAS cho `faithfulness` và `answer_relevancy` bằng 0 (câu 41, 42, 33, 2, 25). Vì vậy diagnosis "LLM hallucinating" của `faithfulness` ở các hàng này không đúng: model không bịa, nó không đưa ra phát biểu nào. Cần đọc answer trước khi tin nhãn worst_metric.

**2. Chunk cắt ngang số liệu và câu phủ định.** Chunk con bị cắt đúng giữa thông tin quan trọng:
- Câu 2 (hạn mức PVI): context 1 kết thúc ở "Hạn mức bảo hiểm: **200.000." còn context 3 bắt đầu ở "000 VNĐ/năm** bao gồm nội trú, ngoại trú và nha khoa". Số 200.000.000 bị tách đôi nên answer là "Không tìm thấy." dù `context_recall` = 1.0.
- Câu 38 (khách sạn công tác nước ngoài): context 3 dừng ở "Khách sạn tối đa 150 U", phần "SD/đêm (thành phố lớn: 200 USD/đêm)" nằm ở context 1. Answer dùng 150 USD/đêm và kết luận 450 USD, trong khi reference là 200 USD/đêm và 600 USD. Đây là lỗi bịa/ghép sai thật (`faithfulness` = 0.0), khác với nhóm 1.
- Câu 46 (thử việc có nghỉ phép năm không): câu phủ định "KHÔNG được nghỉ phép năm" bị cắt giữa chữ, phần "KHÔNG được ng" ở cuối một chunk (xuất hiện trong contexts của câu 25) và "hỉ phép năm**" ở đầu chunk trong contexts câu 46. Answer vì vậy là "Không tìm thấy." (`faithfulness` = 1.0, `answer_relevancy` = 0.0).

**3. Multi-hop thiếu tài liệu thứ hai, `top_k = 3` quá ít.**
- Câu 27 (thâm niên 7 năm, trừ 4 ngày ốm): contexts gồm ngày phép 2024, nghỉ ốm và chính sách 2023, không có đoạn thâm niên (`context_recall` = 0). Answer nói rõ "không có quy định tăng phép theo thâm niên".
- Câu 33 (Manager 12 năm, phụ cấp và ngày phép): cả ba contexts đều thuộc chính sách nghỉ phép, không có chunk phụ cấp (`context_recall` = 0).
- Câu 40 (vi phạm bảo mật khi đang thử việc): chỉ có một chunk quy trình sự cố (nêu "phải báo cáo trong vòng 1 giờ") nhưng thiếu phần "không được làm"; hai slot còn lại bị chiếm bởi chunk lương thử việc và thời gian thử việc. Answer trả lời được vế "nên" và thừa nhận thiếu vế "không nên".
- Câu 39 (so sánh mật khẩu v1.0 và v2.0): ba slot gồm v1.0, v2.0 và một thông báo "đã được thay thế bởi v2.0", nên thiếu thời hạn đổi và MFA (`context_precision` = 0.0, `context_recall` = 0.0). Answer đúng ở độ dài tối thiểu (8 và 12 ký tự), phần còn lại "Không tìm thấy".

**4. Chunk đã enrichment chứa văn bản thừa.** Contexts có thêm câu mô tả đầu chunk và các đoạn "Tóm tắt / Câu hỏi" ở cuối. Một số tóm tắt tự ghi "hạn mức được nêu chưa đầy đủ" hoặc "đoạn trích bị thiếu", tức chính bước enrichment đã đánh dấu chunk bị cắt. Phần văn bản này làm context dài hơn nhưng không cứu được thông tin đã bị cắt. Chưa có phép đo nào tách ảnh hưởng của enrichment lên `context_precision`, nên đây là quan sát, chưa phải kết luận.

## Matrix và nhóm yếu nhất

| worst_metric | factual | multi_hop | adversarial | Tổng |
|---|---|---|---|---|
| faithfulness | 2 | 5 | 3 | 10 |
| answer_relevancy | 9 | 7 | 2 | 18 |
| context_precision | 4 | 4 | 1 | 9 |
| context_recall | 5 | 4 | 4 | 13 |
| Tổng số câu | 20 | 20 | 10 | 50 |

Mỗi câu được đếm theo `worst_metric` của chính nó, nên tổng cột là kích thước nhóm 20/20/10 và không đo chất lượng.

Nhóm yếu theo mean thấp nhất: multi_hop; mean: 0.605.
Worst metric xuất hiện nhiều nhất: answer_relevancy; số câu: 18.

multi_hop yếu nhất vì mỗi câu cần ghép từ hai tài liệu trở lên (ngày phép cộng thâm niên, lương cộng phụ cấp, hai phiên bản chính sách) trong khi chỉ có 3 slot context, và model từ chối khi thiếu một vế. `answer_relevancy` là worst metric của 18/50 câu, nhưng con số này bị kéo bởi câu từ chối vì RAGAS cho 0 với những answer không trả lời câu hỏi (6 câu trong bottom 10 trả đúng "Không tìm thấy." đều có `answer_relevancy` = 0). Vì vậy `answer_relevancy` ở đây phản ánh một phần hành vi từ chối của generation, không chỉ chất lượng câu chữ. `context_recall` đứng thứ hai (13 câu) và là metric thấp nhất của nhóm adversarial (0.425).

Đề xuất sửa, mỗi lần đổi một yếu tố rồi chạy lại cùng 50 câu để so sánh:
1. Sửa prompt generation: yêu cầu ưu tiên chính sách hiện hành khi có nhiều phiên bản, cho phép tính toán nhiều bước từ context, và chỉ trả "Không tìm thấy" khi context thật sự thiếu. Chạy lại `setup_answers.py --live` rồi Phase A, theo dõi số câu từ chối (hiện 10/50) và mean của multi_hop.
2. Sửa chunking: cắt theo câu hoặc heading, thêm overlap để số liệu và câu phủ định không bị tách (các câu 2, 38, 46). Cần index lại Qdrant rồi chạy lại cả hai bước trên.
3. Tăng `RERANK_TOP_K` từ 3 lên 5 và loại chunk chỉ là thông báo "đã được thay thế" (câu 39); theo dõi `context_recall` của multi_hop.
4. Lọc theo metadata trạng thái hiệu lực để ưu tiên v2024/v2.0 (câu 41, 27, 33). Không xóa tài liệu bản cũ khỏi corpus để eval dễ hơn.

## Bẫy adversarial và giới hạn

Mean adversarial (0.624) thấp hơn factual (0.838), nhưng multi_hop (0.605) còn thấp hơn adversarial. Trong 10 câu adversarial: 3 câu từ chối (41, 42, 46) là các câu dính bẫy phiên bản hoặc phủ định; câu 49 hỏi thẳng chính sách v2023 và trả 12 ngày, khớp phiên bản được hỏi nhưng `context_recall` = 0.0; các câu 43, 44 và 45 trả giá trị của mật khẩu v2.0 hiện hành (12 ký tự, đổi mỗi 120 ngày, MFA bắt buộc) và các câu 47, 48, 50 trả đúng phủ định ("Không"). Điểm thấp hơn của nhóm này chủ yếu đến từ 3 câu từ chối. Dữ liệu này chưa chứng minh pipeline nhận ra bẫy version conflict: trong câu 41 nó lấy được cả hai phiên bản nhưng không chọn được phiên bản hiện hành, và chúng tôi chưa kiểm tra contexts của các câu 43 đến 45 để biết có lấy cả v1.0 hay không.

Giới hạn:
- Chỉ một lần chạy RAGAS, chưa lặp lại nên chưa đo độ dao động giữa các lần (chưa đo).
- Nhóm adversarial chỉ có 10 câu, mỗi câu lệch có thể làm mean đổi đáng kể.
- Generator và evaluator cùng là `gpt-6-luna`, có thể làm điểm thiên lệch; chưa đối chiếu với evaluator khác.
- RAGAS chấm 0 cho câu từ chối, nên điểm thấp không phân biệt được "model bịa" với "model từ chối".
- Phân tích nguyên nhân dựa trên đọc thủ công 10 câu bottom 10, chưa kiểm tra toàn bộ 50 câu.
