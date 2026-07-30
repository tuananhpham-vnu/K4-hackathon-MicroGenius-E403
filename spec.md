# AI SPEC — Tư vấn tuyển sinh có căn cứ · Nhóm MicroGenius E403

Hướng: **C — Làn mở**  
Loại: **Tính năng mới**  
Mức hiện tại: **Working prototype**

> Chốt phạm vi: trợ lý chỉ tư vấn thông tin Chương trình AI Thực Chiến từ tài liệu cục bộ đã phê duyệt; không ra quyết định tuyển sinh và không sửa hồ sơ.

## §1. User & Job

### Job executor và workflow

Người thực hiện job là ứng viên đang cân nhắc hoặc chuẩn bị đăng ký Chương trình AI Thực Chiến.

1. Ứng viên phát sinh câu hỏi về điều kiện, lịch, quyền lợi, lộ trình hoặc hồ sơ.
2. Ứng viên tìm trong website, bài đăng cộng đồng hoặc hỏi người quen.
3. Ứng viên phải tự đánh giá thông tin nào chính thức, còn hiệu lực và đúng với khóa mình quan tâm.
4. Nếu chưa chắc chắn, ứng viên liên hệ cán bộ tuyển sinh và chờ xác nhận.
5. Ứng viên dùng câu trả lời để quyết định chuẩn bị/nộp hồ sơ hoặc hỏi tiếp.

### Core JTBD

Khi chuẩn bị tham gia một chương trình đào tạo, tôi muốn nhận được câu trả lời tuyển sinh có căn cứ và biết rõ khi nào cần hỏi người phụ trách, để có thể thực hiện bước tiếp theo mà không bỏ lỡ mốc hoặc chuẩn bị sai.

### Problem statement

Ứng viên phải ghép thông tin tuyển sinh phân tán giữa tài liệu chính thức và cộng đồng; câu trả lời thiếu nguồn, hết hiệu lực hoặc quá chắc chắn có thể làm họ chuẩn bị sai hồ sơ, bỏ lỡ thời hạn hoặc hình thành kỳ vọng sai.

### Evidence

Phương pháp mining có thể kiểm lại:

- Corpus cộng đồng tại thời điểm đo: 4 file JSON trong `data/`, tổng **750 bài ghi**.
- Đếm không phân biệt hoa/thường trên trường `text`; mỗi nhóm dùng regex công khai dưới đây. Một bài có thể nằm ở nhiều nhóm, vì vậy không cộng các nhóm thành tổng.
- Kết quả: lịch/hạn/trạng thái **136**; điều kiện/đăng ký/hồ sơ **93**; địa điểm/hình thức học **47**; test/phỏng vấn **24**; học phí/phụ cấp/học bổng **7**.
- Lệnh kiểm lại được mô tả trong changelog và có thể chạy bằng PowerShell `ConvertFrom-Json` + `Where-Object`.

Năm ví dụ nguyên văn ngắn, đã ẩn danh:

1. `dataset.../post-1`: “Cho em hỏi chương trình AI thực chiến này dự kiến có tổ chức dạy ở Hồ Chí Minh không ạ?”
2. `dataset.../post-2`: “Mình ở HCM... chưa có bằng và nên ôn thêm kiến thức hay chứng chỉ gì để có thể vượt qua phỏng vấn?”
3. `dataset.../post-3`: “Ai học xong khoá 1 rồi cho mình xin ít review lịch học và cách học với ạ”
4. `dataset.../post-4`: “Khi nào sẽ có kết quả vòng hồ sơ khóa 5... và ngày thi dự kiến là ngày nào?”
5. `dataset.../post-6`: “Lịch học khá dày, kéo dài gần như full-time... các bạn thường sắp xếp việc học trên trường như thế nào?”

Nguồn cộng đồng chỉ dùng để chứng minh pain, có trust score `0.62` và **không được dùng làm căn cứ kết luận tuyển sinh**. Sáu file Markdown trong `Tailieutubtc/` là corpus trả lời chính thức, trust score `0.92`.

## §2. Impact & quyết định chọn

| Ứng viên pain | Số tín hiệu / 750 | Tần suất xảy ra | Tổn thất mỗi lần | Khả thi trong hackathon |
|---|---:|---|---|---|
| Lịch, hạn, trạng thái vòng tuyển sinh | 136 (18,1%) | Theo từng mốc/khóa | Có thể lỡ hạn hoặc phải hỏi lại | Cao — có tài liệu lịch chính thức |
| Điều kiện, đăng ký, hồ sơ | 93 (12,4%) | Trước mỗi lần ứng tuyển | Chuẩn bị sai/thiếu hồ sơ | Cao — có tài liệu tổng hợp |
| Địa điểm và hình thức học | 47 (6,3%) | Trước khi cam kết tham gia | Quyết định sai về thời gian/di chuyển | Trung bình — thông tin có thể thay đổi |
| Test và phỏng vấn | 24 (3,2%) | Trước vòng đánh giá | Ôn sai trọng tâm, tăng lo lắng | Trung bình — tài liệu chưa phủ toàn bộ |
| Học phí, phụ cấp, học bổng | 7 (0,9%) | Khi cân nhắc chi phí | Kỳ vọng tài chính sai | Cao về impact, thấp hơn về số tín hiệu |

Đã loại:

- Chatbot trả lời mọi nội dung cộng đồng: nguồn không đủ thẩm quyền.
- AI chấm CV hoặc quyết định trúng tuyển: cost-of-error cao, vượt quyền.
- Tự động nộp/sửa hồ sơ: cần xác thực, CRM và phê duyệt mà prototype chưa có.

Đã chọn: **một lớp tư vấn có truy xuất nguồn, validation và handoff**, vì nó phủ ba pain lớn nhất bằng cùng một quyết định cốt lõi: “evidence hiện có có đủ để trả lời hay phải hỏi lại/chuyển người?”.

## §3. Giải pháp tương tự đã nghiên cứu
- [Salesforce Agentforce](https://www.salesforce.com/ap/agentforce/l):
  - **Flow:** Agent phân loại yêu cầu theo subagent/topic, dùng action/tool để lấy dữ liệu hoặc thực hiện tác vụ, sau đó handoff sang người thật khi cần.
  - **Đáng học:** Tách rõ subagent, action, reasoning và human handoff; mỗi nhóm nhiệm vụ có action riêng, có audit trail cho action/output.
  - **Đáng né:** Kiến trúc enterprise phụ thuộc sâu vào hệ sinh thái Salesforce, quá nặng cho prototype hackathon.
  - **Mình khác gì:** Dùng LangGraph + Agent Harness nhỏ gọn; mỗi agent có `allowed_tools`, `memory_scopes`, `guardrails` và trace `source_id`/`evidence_id`.
- [Intercom Fin AI Agent](https://www.intercom.com/help/en/articles/9440354-knowledge-sources-to-power-ai-agents-and-self-serve-support):
  - **Flow:** Agent tìm câu trả lời từ nhiều knowledge source, tạo câu trả lời grounded, hỏi lại hoặc handoff khi không đủ chắc chắn.
  - **Đáng học:** Quản lý knowledge source tập trung, kiểm soát source nào được agent sử dụng và hỗ trợ cập nhật nội dung theo source.
  - **Đáng né:** Phụ thuộc vào knowledge platform riêng; source bên ngoài có thể có chu kỳ đồng bộ khác nhau.
  - **Mình khác gì:** Searcher giữ metadata của từng evidence; Validator kiểm tra source trust/relevance trước khi Synthesis được phép dùng.
- **Các hướng tiếp cận đã loại:**
  - **Traditional RAG:** Dễ triển khai nhưng pipeline retrieval tĩnh, khó xử lý database/source cập nhật liên tục, không tự quyết định khi nào cần tool hoặc human. Dùng làm baseline retrieval, không chọn làm kiến trúc chính.
  - **Single-agent:** Dễ demo nhưng prompt phình to, khó phân quyền tool, memory và guardrail; khó trace agent nào đã làm gì. Dùng làm baseline so sánh, không chọn làm kiến trúc chính.
- **Phương án chọn:** Conditional tool-using MAS với LangGraph + Agent Harness + source-aware Validator + HITL.

## §4. Thiết kế
- Lát cắt MỘT CÂU (1 user · 1 việc · 1 quyết định AI · 1 kết quả):
  - Một ứng viên hỏi: “Em có đủ điều kiện tham gia chương trình AI không?”; hệ thống kiểm tra hồ sơ với nguồn tuyển sinh hiện hành, trả mức độ phù hợp có citation hoặc chuyển cán bộ tuyển sinh.
  - **1 user:** ứng viên · **1 việc:** kiểm tra mức độ phù hợp · **1 quyết định AI:** `suitable`/`potentially_suitable`/`insufficient_information`/`HITL required` · **1 kết quả:** câu trả lời có source/evidence hoặc yêu cầu bổ sung/chuyển cán bộ.
- Non-goals (≥3 thứ KHÔNG build):
  - Không tự quyết định trúng tuyển hoặc từ chối ứng viên.
  - Không cam kết học bổng, học phí hoặc ngoại lệ chính sách.
  - Không tự thay đổi, xóa hoặc cập nhật hồ sơ ứng viên.
  - Không dùng nguồn chưa được phê duyệt làm căn cứ chính.
  - Không xây CRM đầy đủ trong prototype.
- Mức prototype nhắm tới: [ ] Sketch [ ] Mock [x] Working — phần nào mock, phần nào thật:
  - **Thật:** LangGraph state graph; Orchestrator/Analyst/Searcher/Validator/HITL/Synthesis; Agent Harness; XML prompt; source/evidence trace; relevance/trust scoring; retry; structured logging; API `/api/query`, `/api/audit`, `/api/logs`.
  - **Mock/thay thế production:** local knowledge base thay official admissions database; lexical retrieval thay embedding + Qdrant; in-memory memory thay PostgreSQL/Redis; rule-based reasoning thay LLM thật ở một số node; mock human reviewer thay dashboard cán bộ.
- Automation: [ ] augment [x] conditional [ ] automate — lý do theo cost-of-error:
  - Chỉ tự trả lời khi source được duyệt, relevance/trust đạt ngưỡng và risk thấp.
  - Case thiếu nguồn, mâu thuẫn, ngoại lệ, học bổng, khiếu nại hoặc xác nhận trúng tuyển phải chuyển HITL.
  - Cost-of-error cao vì câu trả lời sai có thể khiến ứng viên chuẩn bị sai hồ sơ, hiểu sai deadline/học phí hoặc coi tư vấn là quyết định tuyển sinh.
- §4b. Nguyên tắc đã áp dụng (≥4 — HAX/PAIR, xem guide):
  | Nguyên tắc | Áp cụ thể vào đâu trong prototype |
  |---|---|
  | G1 — Làm rõ hệ thống làm được gì | UI/system prompt nêu đây là tư vấn tham khảo, không quyết định trúng tuyển. |
  | G2 — Làm rõ làm tốt đến đâu | Evidence có `source_trust_score`, `relevance_score`, `source_check_passed`; output có citation và giới hạn dữ liệu. |
  | G10 — Thu hẹp phạm vi khi nghi ngờ | Validator retry Searcher một lần; nếu vẫn thiếu thì yêu cầu bổ sung hoặc chuyển HITL. |
  | G11 — Giải thích vì sao | Output giữ `evidence_id`, `source_id`, quote và locator để đối chiếu. |
  | Gạt bỏ dễ dàng | User có thể bỏ qua AI và yêu cầu cán bộ tuyển sinh; Synthesis không chặn flow. |
  | Sửa dễ dàng | Analyst trả `missing_information` để user bổ sung profile và chạy lại. |
  | PAIR — Mental Models | Không dùng nhãn `accepted`/`rejected`; chỉ dùng nhãn phù hợp có điều kiện. |
  | PAIR — Errors & Graceful Failure | Tách lỗi thiếu source, source mâu thuẫn, query mơ hồ và vượt thẩm quyền thành các route khác nhau. |

## §5. Kiểu lỗi — 4 lớp chỗ khó

| ID | Lớp | Kịch bản | Phát hiện | Xử lý mong đợi |
|---|---|---|---|---|
| E01 | Nguồn sự thật | Không có chunk khớp | 0 evidence đạt ngưỡng | Không đoán; đề nghị bổ sung chi tiết/chuyển cán bộ |
| E02 | Nguồn sự thật | Bài cộng đồng khớp cao nhưng không chính thức | trust `< 0.70` | Không dùng làm căn cứ kết luận |
| E03 | Nguồn sự thật | Hai bản tài liệu lặp nội dung | Hash nội dung trùng | Deduplicate trước khi trả top-k |
| E04 | Mơ hồ | “Học ở đâu?” không nói khóa/hình thức | Ít hơn 4 token có nghĩa | Hỏi lại khóa/mốc/nội dung |
| E05 | Mơ hồ | “Em có phù hợp không?” thiếu profile | Thiếu education/experience/availability | Không kết luận; yêu cầu bổ sung |
| E06 | Ngoài phạm vi | Xin viết hộ bài luận | Keyword + intent ngoài phạm vi | Từ chối và nêu phạm vi |
| E07 | Ngoài thẩm quyền | Yêu cầu xác nhận trúng tuyển/ngoại lệ | High-risk rules | Bắt buộc HITL, không ra quyết định |
| E08 | Đặc thù domain | Deadline thay đổi theo khóa | Intent deadline + source metadata | Chỉ dùng tài liệu chính thức; nêu giới hạn cập nhật |
| E09 | Đặc thù domain | Học phí/phụ cấp ảnh hưởng quyền lợi | Intent tài chính | Dùng threshold nguồn; case đặc biệt chuyển người |
| E10 | Vận hành | Thiếu package LangGraph tại máy demo | Import failure | Fallback domain workflow; vẫn chạy API/UI |
| E11 | Bảo mật | Xin mật khẩu/thông tin người khác | Out-of-scope rule | Từ chối, không retrieve |
| E12 | Hệ thống | API lỗi hoặc server chưa chạy | Fetch exception | UI hiển thị hướng dẫn chạy server, không giả câu trả lời |

## §6. Bốn đường đi của trải nghiệm

- **Happy path:** câu rõ → retrieve nguồn chính thức → validation pass → câu trả lời + source cards.
- **Low-confidence:** câu quá ngắn hoặc thiếu profile → hỏi lại khóa/mốc/nội dung; không biến phỏng đoán thành kết luận.
- **Failure/không căn cứ:** không có evidence đạt trust/relevance → trả “chưa tìm thấy bằng chứng đủ tin cậy” và đề nghị cán bộ xác nhận.
- **Correction:** người dùng nhập câu mới trong composer; session giữ câu hỏi mới, chạy lại toàn bộ retrieval/validation và thay evidence panel.
- **Ngoài phạm vi:** từ chối yêu cầu như thời tiết, mật khẩu, làm hộ.
- **Đặc thù domain:** ngoại lệ, khiếu nại, phê duyệt, trúng tuyển và tình trạng hồ sơ luôn có cảnh báo cần cán bộ.

## §7. Kiểm thử

### Chiều chất lượng

| Chiều | Định nghĩa kiểm chứng được |
|---|---|
| Routing | Intent thực tế bằng `expected_intent` |
| HITL | `needs_human` bằng nhãn kỳ vọng |
| Clarification | Case mơ hồ bật `need_clarification` |
| Grounding | Số evidence đạt trust/relevance không thấp hơn `min_evidence` |
| Traceability | Evidence có `source_id`, locator, relevance; source có URI và trust |
| Safety | High-risk không thiếu cảnh báo cán bộ; out-of-scope không retrieve |
| Integration | `/`, `/api/health`, `/api/query` trả HTTP 200 và UI gọi API thật |

### Golden set

- File: `eval/golden_set.json`.
- 20 case: 8 happy path, 4 low-confidence, 4 high-risk, 3 out-of-scope, 1 chitchat.
- Runner tái lập: `python eval/run_golden_set.py`.
- Kết quả chi tiết: `eval/results.json`.

### Quality bar

**Đạt khi ≥80% case qua toàn bộ check, 100% case high-risk được route đúng, và không evidence cộng đồng trust 0.62 được dùng làm căn cứ.**

### Kết quả hiện tại

| Lượt | Thay đổi | Passed | Tỷ lệ | Quality bar |
|---|---|---:|---:|---|
| Baseline đầu tiên | Sau khi nối corpus/UI | 13/20 | 65% | Không đạt |
| Lượt 2 | Sửa chitchat, clarification, out-of-scope | 20/20 | 100% | Đạt |

Ngoài golden set:

- 4/4 unit test harness/observability đạt.
- 6/6 traceability/eval test đạt.
- `node --check codebase/app.js` đạt.
- HTTP smoke test: health, trang `/` và query đều 200; query có evidence và validation pass.

Giới hạn của phép đo: golden set hiện kiểm tra contract/định tuyến/evidence tối thiểu, chưa có human grading cho semantic correctness từng câu và chưa đo latency/cost với LLM thật. Con số 100% không được diễn giải là 100% chính xác ngoài tập test.

## §8. Phân công & kế hoạch


| Thành viên | Mã học viên | Phần phụ trách |
|---|---|---|
| Nguyễn Đức Anh | 2A202601788 | Thu thập và xử lý dữ liệu cộng đồng |
| Phạm Tuấn Anh | 2A202601070 | Backend, agent workflow, harness |
| Nguyễn Thị Thương | 2A202601226 | Thu thập và chuẩn hóa tài liệu tuyển sinh |
| Mai Tiến Dũng | 2A202601838 | Frontend, dữ liệu cộng đồng, tích hợp demo, eval, validation |

### Validation CP5

Kế hoạch 15 phút/người với ít nhất 3 ứng viên thật ngoài nhóm:

1. “Bạn đang muốn ra quyết định gì sau khi hỏi câu này?”
2. “Nguồn và cảnh báo hiện tại có đủ để bạn tin/biết bước tiếp theo không?”
3. “Có đoạn nào khiến bạn hiểu rằng hệ thống đã quyết định thay cán bộ không?”

Log cần ghi: tên/người thử, câu hỏi gốc, task success, điểm tin tưởng 1–5, chỗ hiểu sai, đề xuất và thay đổi sau feedback. **Tên 3 willing users và feedback log chưa tồn tại trong repo; đây là đầu vào từ người thật, không được tạo giả bằng code.**

### Multi-prototype

Hai phương án đã cân nhắc:

- A — câu trả lời tĩnh đẹp, nhanh demo nhưng không có bằng chứng runtime;
- B — UI gọi workflow có source/validation/audit, giao diện có thể ít “mượt” hơn nhưng kiểm chứng được.

Chọn B vì rubric ưu tiên chuỗi quyết định và bằng chứng.

## §9. Changelog

| Thời điểm | Đổi gì | Vì sao |
|---|---|---|
| 2026-07-30 | Chuyển knowledge base từ đường dẫn không tồn tại sang discovery ở repo | Backend trước đó health = 0 nguồn/0 tài liệu |
| 2026-07-30 | Nạp Markdown chính thức và JSON cộng đồng với trust khác nhau | Tách pain evidence khỏi nguồn dùng để kết luận |
| 2026-07-30 | Nối `codebase/` với `/api/query`, evidence panel và trạng thái lỗi | UI trước đó trả lời hard-coded |
| 2026-07-30 | Server phục vụ trực tiếp static UI/assets | Trước đó server dùng một UI khác trong `mas/ui.py` |
| 2026-07-30 | Deduplicate chunk và query expansion theo intent | Query thời lượng từng xếp nguồn không liên quan cao hơn lộ trình |
| 2026-07-30 | Thêm 20-case golden set và runner | Repo trước đó chỉ có test contract, chưa có quality bar tái lập |
| 2026-07-30 | Sửa chitchat, low-confidence và out-of-scope | Baseline 13/20; các nhánh này định tuyến sai |
| 2026-07-30 | Thêm fallback khi máy chưa cài LangGraph | Đảm bảo demo tối thiểu vẫn chạy; cài đủ requirements sẽ dùng graph |

