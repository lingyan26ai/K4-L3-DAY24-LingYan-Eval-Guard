# Đánh giá LLM Judge Phase B

Nhóm: Ling yan

Người phụ trách: Võ Công Danh - 2A202602739

Nguồn: `artifacts/judge_results.json`; run timestamp: 2026-10-12T18:58:13.138850+00:00 (01:58 ngày 13/10/2026 giờ Việt Nam).
Models generation/judge: generation `gpt-6-luna`; judge `gpt-6-luna`. Hai vai trò dùng cùng một model, xem phần giới hạn.

## Năm cặp A/B và hai lượt

Nguồn cố định: A từ artifacts/answers_50q.json:answer; B từ
fixtures/human_labels_10q.json:model_answer; reference từ fixtures/test_set_50q.json:ground_truth.
Ids: 1, 5, 12, 21, 41. Không đổi nguồn sau khi xem kết quả judge.

| ID | Answer A (pipeline) | Answer B (supplied model_answer) | winner_pass1 | winner_pass2 (đã quy về A/B gốc) | final_winner | position_consistent | scores pass 1 (A / B) | scores pass 2 (A / B, đã quy về gốc) |
|---|---|---|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ **3 ngày làm việc** khi kết hôn. | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | B | B | B | True | 0.85 / 0.95 | 0.75 / 0.90 |
| 5 | Tổng Giám đốc (CEO) phê duyệt đơn hàng 55 triệu đồng, vì giá trị trên 50.000.000 VNĐ. | Cần Giám đốc phòng ban phê duyệt. | A | A | A | True | 1.00 / 0.00 | 1.00 / 0.00 |
| 12 | Thưởng Tết tối thiểu là **1 tháng lương**. | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | A | tie | tie | False | 0.95 / 0.82 | 0.95 / 0.95 |
| 21 | Nhân viên có 9 năm thâm niên được **18 ngày phép năm** theo ví dụ. **Khoảng lương không tìm thấy.** | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | B | B | B | True | 0.70 / 1.00 | 0.55 / 1.00 |
| 41 | Không tìm thấy. | Nhân viên được nghỉ 12 ngày phép năm. | A | A | A | True | 0.40 / 0.10 | 0.20 / 0.00 |

Lý do và điểm của từng cặp. Ở lượt 2 hai answer bị hoán đổi vị trí, nên chữ "A" và "B" trong lý do lượt 2 là nhãn của lượt đó (A của lượt 2 là answer B gốc). Chỉ `winner_pass2` và `scores_pass2` đã được quy về A/B gốc.

- **Câu 1** (Nhân viên được nghỉ bao nhiêu ngày khi kết hôn?)
  - Lượt 1: Cả hai nêu đúng 3 ngày làm việc, nhưng B cũng nêu rõ ngày nghỉ có lương. Cả hai đều bỏ sót việc không trừ vào phép năm.
  - Lượt 2 (nhãn đã hoán đổi): A nêu đúng 3 ngày làm việc và bổ sung điều kiện được hưởng lương. Cả hai đều chưa nói rõ thời gian nghỉ không trừ vào phép năm, nhưng A đầy đủ hơn.
- **Câu 5** (Muốn mua thiết bị trị giá 55 triệu cần ai phê duyệt?)
  - Lượt 1: A đúng với chính sách: đơn hàng trên 50.000.000 VNĐ cần CEO phê duyệt; 55 triệu vượt ngưỡng. B nêu sai người phê duyệt.
  - Lượt 2 (nhãn đã hoán đổi): B xác định đúng Tổng Giám đốc (CEO) và điều kiện đơn hàng trên 50.000.000 VNĐ. A nêu sai người phê duyệt.
- **Câu 12** (Thưởng Tết tối thiểu cho nhân viên chính thức có từ 6 tháng trở lên là bao nhiêu?)
  - Lượt 1: A nêu đúng mức tối thiểu 1 tháng lương và phù hợp với nhóm nhân viên được hỏi. B khái quát thành mọi nhân viên, bỏ điều kiện từ 6 tháng trở lên.
  - Lượt 2 (nhãn đã hoán đổi): Cả hai đều nêu đúng mức thưởng tối thiểu là 1 tháng lương và đều súc tích. Không nhắc điều kiện từ 6 tháng trở lên, nhưng câu hỏi đã giới hạn đối tượng này.
- **Câu 21** (Một nhân viên Senior có 9 năm thâm niên được nghỉ bao nhiêu ngày phép năm và lương trong khoảng nào?)
  - Lượt 1: B nêu đúng 18 ngày phép và đầy đủ khoảng lương Senior 20–35 triệu VNĐ/tháng. A đúng số ngày phép nhưng bỏ sót khoảng lương và nói không tìm thấy.
  - Lượt 2 (nhãn đã hoán đổi): A nêu đúng 18 ngày phép và khoảng lương Senior 20–35 triệu VNĐ/tháng theo tham chiếu. B đúng về ngày phép nhưng sai khi nói không tìm thấy khoảng lương, nên thiếu thông tin quan trọng.
- **Câu 41** (Nhân viên được nghỉ bao nhiêu ngày phép năm?)
  - Lượt 1: Chính sách hiện hành v2024 quy định 15 ngày cơ bản, cộng 1 ngày mỗi 3 năm thâm niên. A không cung cấp câu trả lời nhưng không khẳng định sai; B nêu 12 ngày theo chính sách v2023 đã bị thay thế nên không chính xác.
  - Lượt 2 (nhãn đã hoán đổi): Chính sách hiện hành quy định 15 ngày cơ bản, cộng 1 ngày mỗi 3 năm thâm niên. A nêu 12 ngày theo chính sách cũ nên sai; B không trả lời được nhưng không cung cấp thông tin sai.

Position bias count/rate: 1/5 cặp không nhất quán, tỷ lệ 20.0%.
Verbosity win rate: 50.0% (answer dài hơn thắng 2/4); decisive cases: 4.

Cặp duy nhất không nhất quán là câu 12. Lượt 1 chọn A (0.95 so với 0.82) vì B "khái quát thành mọi nhân viên, bỏ điều kiện từ 6 tháng"; lượt 2 cho hòa (0.95 và 0.95) vì "câu hỏi đã giới hạn đối tượng này". Hai answer đều là "1 tháng lương", khác nhau chỉ ở cách diễn đạt, nên đây là cặp gần như ngang nhau và hai lượt cân nhắc điều kiện 6 tháng khác nhau. Con số 1/5 là dấu hiệu thống kê, không đủ để kết luận judge thiên vị vị trí; cần thêm nhiều cặp và nhiều lần chạy mới kết luận được. Swap-and-average đã xử lý đúng tình huống này bằng cách trả `tie`.

Về verbosity: 4 cặp có winner rõ (1, 5, 21, 41), trong đó answer dài hơn thắng ở câu 1 và 5. Ở câu 1 hai answer chỉ hơn kém 5 ký tự (52 và 57) và B thắng nhờ nêu "có lương"; câu 5 answer dài hơn thắng vì đúng (CEO) còn answer ngắn nêu sai người phê duyệt. Ở câu 21 và 41 answer ngắn hơn thắng (câu 41 thắng với chỉ "Không tìm thấy."). Đọc nội dung thì không thấy lý do coi tỷ lệ 50% là verbosity bias; kết quả đi theo tính đúng của reference.

Câu 41 cần lưu ý riêng: A là "Không tìm thấy." (chính là câu từ chối đã thấy ở Phase A) thắng B "12 ngày" ở cả hai lượt vì B dùng chính sách v2023 đã bị thay thế, còn đáp án hiện hành là 15 ngày. Judge phạt khẳng định sai nặng hơn việc không trả lời, phù hợp với tiêu chí độ chính xác, nhưng "thắng" ở đây không có nghĩa A là câu trả lời tốt.

## Calibration đúng model_answer

Helper đánh giá đúng question/model_answer đang có trong fixtures/human_labels_10q.json;
không lấy answer mới của pipeline. Prompt chỉ nhận question, answer, reference.
Không gửi human_label, human_note hoặc phân bố nhãn human vào prompt.

| ID | model_answer gốc | Judge | Reasoning của judge | Human | Agree |
|---|---|---|---|---|---|
| 1 | Nhân viên được nghỉ 3 ngày làm việc có lương khi kết hôn. | 1 | Câu trả lời nêu đúng thời lượng nghỉ 3 ngày làm việc có lương khi kết hôn; thông tin không trừ vào phép năm là chi tiết bổ sung, không thiết yếu để trả lời câu hỏi. | 1 | Yes |
| 5 | Cần Giám đốc phòng ban phê duyệt. | 0 | Thiết bị trị giá 55 triệu vượt ngưỡng 50 triệu, nên cần Tổng Giám đốc (CEO) phê duyệt, không phải Giám đốc phòng ban. | 0 | Yes |
| 12 | Nhân viên được thưởng Tết tối thiểu 1 tháng lương. | 1 | Câu trả lời nêu đúng mức thưởng tối thiểu là 1 tháng lương cho nhân viên chính thức có từ 6 tháng trở lên. | 1 | Yes |
| 21 | Được nghỉ 18 ngày phép (15 cơ bản + 3 thâm niên). Lương Senior từ 20 đến 35 triệu. | 1 | Câu trả lời nêu đúng 18 ngày phép (15 ngày cơ bản + 3 ngày thâm niên) và mức lương Senior 20–35 triệu/tháng theo reference. | 1 | Yes |
| 23 | Hoàn trả 25 triệu vì chưa đủ 1 năm cam kết. | 1 | Câu trả lời nêu đúng việc hoàn trả toàn bộ 25 triệu vì nghỉ trước khi đủ 1 năm cam kết. | 1 | Yes |
| 29 | Trưởng phòng phê duyệt. Phạt 2% tháng trên 8 triệu. | 0 | Thiếu phê duyệt của Kế toán trưởng; mức phạt 2%/tháng trên 8 triệu không tính theo 15 ngày quá hạn. Theo reference, phí là 80.000 VNĐ. | 0 | Yes |
| 33 | Phép: 19 ngày. Phụ cấp: 1.500.000 VNĐ/tháng. | 1 | Đúng theo reference: tổng phụ cấp là 1.500.000 VNĐ/tháng và phép năm với 12 năm thâm niên là 19 ngày. | 1 | Yes |
| 41 | Nhân viên được nghỉ 12 ngày phép năm. | 0 | Câu trả lời dùng mức 12 ngày của chính sách v2023 đã bị thay thế; chính sách hiện hành quy định 15 ngày cơ bản, cộng 1 ngày mỗi 3 năm thâm niên. | 0 | Yes |
| 46 | Nhân viên thử việc không được nghỉ phép năm và phải xin nghỉ không lương nếu cần. | 0 | Câu trả lời đúng khi nói nhân viên thử việc không được nghỉ phép năm và cần xin nghỉ không lương, nhưng bỏ điều kiện nghỉ không lương phải được trưởng phòng phê duyệt. | 1 | No |
| 50 | Được, miễn là đảm bảo kết nối an toàn. | 0 | Reference cấm VPN cá nhân như NordVPN và yêu cầu dùng VPN WireGuard của công ty; câu trả lời cho phép sử dụng nên trái chính sách. | 0 | Yes |

Cohen’s κ: 0.80.
Observed/chance agreement và diễn giải: judge khớp người ở 9/10 nhãn nên observed agreement p_o = 0.90. Judge gán 5 nhãn 1 và 5 nhãn 0, người gán 6 nhãn 1 và 4 nhãn 0, nên chance agreement p_e = 0.5 × 0.6 + 0.5 × 0.4 = 0.50 và κ = (0.90 − 0.50) / (1 − 0.50) = 0.80. Theo thang Landis-Koch, 0.80 nằm ở biên giữa "substantial" và "almost perfect", vượt ngưỡng bonus κ > 0.6. Với chỉ 10 nhãn, mỗi nhãn lệch làm κ đổi rất nhiều: nếu câu 46 khớp thì κ lên 1.00.

Nhãn lệch duy nhất là câu 46 ("Nhân viên thử việc có được nghỉ phép năm không?"). Model answer là "không được nghỉ phép năm và phải xin nghỉ không lương nếu cần". Người gán 1 ("Đúng hoàn toàn, bao gồm hành động thay thế"); judge gán 0 vì answer "bỏ điều kiện nghỉ không lương phải được trưởng phòng phê duyệt", điều kiện này có trong reference. Cả hai cách chấm đều có lý do: judge bám sát reference hơn, người coi ý chính (phủ định và hướng xử lý) đã đủ. Đây là điểm mơ hồ của tiêu chí "ý thiết yếu", không phải lỗi hiển nhiên của một bên. Judge cũng nhất quán giữa hai quy trình trên 5 id dùng chung: khi B bị gán nhãn 0 (câu 5 và 41), B thua ở cả hai lượt, và khi B nhãn 1 (câu 1, 12, 21), B thắng hoặc không thua. Đây chỉ là kiểm tra tính hợp lý, vì kết quả A/B không được suy ra từ nhãn 0/1.

## Giới hạn và cách dùng judge

- Một model (`gpt-6-luna`) vừa sinh answer A vừa làm judge nên có thể thiên vị answer cùng nguồn; chưa đối chiếu với judge khác.
- Chỉ có 5 cặp và 10 nhãn, một lần chạy; chưa đo độ dao động giữa các lần chạy (chưa đo). κ = 0.80 cho thấy judge phù hợp với người trên tập nhỏ này, chưa đủ chứng minh độ tin cậy tổng quát.
- Nhãn người trong fixtures được dùng làm chuẩn nhưng không phải đáp án tuyệt đối, như câu 46 cho thấy.
- Kiểm chứng: đọc lý do của judge cho từng cặp và từng nhãn, đối chiếu với reference trong test set; mọi nhãn lệch được đọc lại như phần trên.
- Nên dùng judge như một tín hiệu bổ sung bên cạnh RAGAS và kiểm tra thủ công, đặc biệt với các câu phủ định hoặc có nhiều phiên bản chính sách.
