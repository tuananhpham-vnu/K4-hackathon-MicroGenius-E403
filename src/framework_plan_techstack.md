# Framework MAS tư vấn tuyển sinh dựa trên ViSecChat

Dựa trên framework ViSecChat, có thể xây dựng một hệ thống multi-agent hỗ trợ tư vấn tuyển sinh theo luồng:

```text
Phân tích câu hỏi
-> Chia nhỏ truy vấn
-> Tìm kiếm dữ liệu
-> Kiểm tra nguồn và chấm điểm liên quan với user query
-> Kiểm tra bằng chứng
-> Tinh chỉnh khi thiếu/sai dữ liệu
-> Tổng hợp câu trả lời
-> Chuyển người phụ trách khi rủi ro cao
```

Điểm cốt lõi của thiết kế là tách rõ vai trò giữa các agent: Orchestrator điều phối, Analyst làm rõ ý định, Searcher truy xuất thông tin, Validator kiểm tra bằng chứng, Program Matcher tư vấn mức độ phù hợp, Synthesis tổng hợp câu trả lời, còn HITL Gate đảm bảo con người tham gia ở các tình huống nhạy cảm hoặc không chắc chắn.

Hệ thống không tự đưa ra quyết định trúng tuyển, không tự phê duyệt ngoại lệ, không cam kết học bổng và không thay đổi hồ sơ ứng viên nếu chưa có xác nhận của cán bộ tuyển sinh.

---

## 1. Mục tiêu hệ thống

Xây dựng chatbot hỗ trợ ứng viên:

- Tra cứu thông tin các chương trình AI Thực chiến VinAI.
- Tìm hiểu đối tượng phù hợp, điều kiện đầu vào, lịch tuyển sinh, học phí, học bổng và nội dung đào tạo.
- So sánh các chương trình.
- Đề xuất chương trình phù hợp dựa trên hồ sơ ứng viên.
- Hướng dẫn chuẩn bị và nộp hồ sơ.
- Chuyển câu hỏi cho cán bộ tuyển sinh khi AI không đủ thông tin, dữ liệu mâu thuẫn hoặc câu hỏi cần quyết định của con người.

Các nguyên tắc vận hành:

- Chỉ trả lời dựa trên nguồn chính thức hoặc nguồn đã được phê duyệt.
- Mọi thông tin truy xuất phải đi kèm kiểm tra nguồn và điểm liên quan với user query trước khi được dùng để tổng hợp câu trả lời.
- Luôn phân biệt giữa tư vấn tham khảo và quyết định tuyển sinh.
- Với thông tin không chắc chắn, phải nêu rõ giới hạn thay vì suy đoán.
- Với trường hợp rủi ro cao, bắt buộc kích hoạt Human-in-the-Loop.

---

## 2. Kiến trúc MAS đề xuất

### Sơ đồ tổng quát

```text
Ứng viên
   |
   v
Orchestrator Agent
   |
   +-- Chit-chat -----------------------> Synthesis Agent
   |
   +-- Thiếu thông tin ------------------> Hỏi lại ứng viên
   |
   v
Admissions Analyst Agent
   |
   v
Searcher Agent
   |
   +-- Knowledge Base Tool
   +-- Program Database Tool
   +-- Official Website Tool
   +-- Deadline Tool
   +-- CRM Read Tool
   |
   v
Program Matching Agent
   |
   v
Validator Agent
   |
   +-- Thiếu dữ liệu --------------------> Searcher Agent
   +-- Hiểu sai câu hỏi -----------------> Admissions Analyst Agent
   +-- Rủi ro thấp ----------------------> Synthesis Agent
   +-- Rủi ro cao / không chắc ----------> HITL Gate
                                               |
                                               v
                                      Cán bộ tuyển sinh
                                               |
                         +---------------------+---------------------+
                         v                     v                     v
                      Phê duyệt             Chỉnh sửa          Yêu cầu tìm thêm
                         |                     |                     |
                         +---------------------+---------------------+
                                               |
                                               v
                                      Synthesis Agent
                                               |
                                               v
                                      Trả lời ứng viên
```

### Các thành phần chính

| Thành phần | Vai trò |
|---|---|
| Orchestrator Agent | Phân loại câu hỏi, đánh giá độ rõ ràng, mức rủi ro và chọn agent tiếp theo. |
| Summarizer Agent | Tóm tắt hội thoại dài, giữ lại hồ sơ và nhu cầu quan trọng của ứng viên. |
| Admissions Analyst Agent | Hiểu ý định, trích xuất thông tin ứng viên, phát hiện thông tin còn thiếu và viết lại truy vấn. |
| Searcher Agent | Chia truy vấn thành sub-query, chọn công cụ tìm kiếm phù hợp, kiểm tra nguồn sơ bộ, chấm điểm liên quan và thu thập bằng chứng. |
| Program Matching Agent | Đánh giá mức độ phù hợp giữa hồ sơ ứng viên và từng chương trình. |
| Validator Agent | Kiểm tra độ đầy đủ, chính xác, cập nhật, nhất quán, độ tin cậy nguồn và mức liên quan của bằng chứng với user query. |
| HITL Gate | Quyết định trường hợp nào bắt buộc chuyển cho con người. |
| Human Reviewer | Cán bộ tuyển sinh phê duyệt, chỉnh sửa, yêu cầu tìm thêm hoặc từ chối câu trả lời. |
| Synthesis Agent | Tổng hợp câu trả lời cuối cùng, trích nguồn và gợi ý bước tiếp theo. |

---

## 3. Luồng xử lý chi tiết

### 3.1. Orchestrator Agent

Orchestrator nhận câu hỏi hiện tại, lịch sử hội thoại, hồ sơ ứng viên đã thu thập và trạng thái phiên tư vấn. Agent này trả về các cờ điều phối như `intent`, `clarity_score`, `risk_level`, `need_clarification`, `need_human` và `next_agent`.

Ví dụ output:

```json
{
  "intent": "program_eligibility",
  "is_chitchat": false,
  "clarity_score": 7,
  "risk_level": "medium",
  "need_summary": false,
  "need_clarification": true,
  "need_human": false,
  "next_agent": "admissions_analyst"
}
```

Các intent chính:

- `program_information`
- `admission_requirements`
- `program_comparison`
- `program_recommendation`
- `application_process`
- `deadline_information`
- `tuition_and_scholarship`
- `application_status`
- `policy_exception`
- `complaint`
- `chitchat`
- `out_of_domain`

#### 3.1.1. XML Prompt Envelope

Để dễ chuẩn hóa input, đánh số `id` và lưu nguồn, mọi agent nên nhận user prompt theo dạng XML thay vì chuỗi tự do. Mỗi lần gọi agent cần giữ nguyên các trường ngữ cảnh chính như `context`, `query`, `history`, `candidate_profile`, `retrieved_evidence` và `source_registry`.

Mẫu khung prompt:

```xml
<request>
  <request_id>req_20260730_0001</request_id>
  <agent>searcher</agent>
  <context>
    <session_id>ses_123</session_id>
    <conversation_goal>program_eligibility</conversation_goal>
  </context>
  <query>Em năm 3 ngành CNTT, mới học Python thì có vào được không?</query>
  <history>
    <turn id="1" role="user">...</turn>
    <turn id="2" role="assistant">...</turn>
  </history>
  <candidate_profile>
    <education_year>3</education_year>
    <major>Công nghệ thông tin</major>
    <python_level>basic</python_level>
  </candidate_profile>
  <retrieved_evidence>
    <item id="ev_001" source_id="src_001" />
    <item id="ev_002" source_id="src_002" />
  </retrieved_evidence>
</request>
```

Quy ước sử dụng XML:

- `request_id`, `turn id`, `evidence id` và `source_id` phải là định danh duy nhất để trace end-to-end.
- Trường nào có thể lưu thành metadata thì không nhét vào text tự do.
- Khi cần truy xuất lại nguồn, hệ thống chỉ cần bám theo `source_id` thay vì parse lại toàn bộ câu trả lời.
- Nếu có nhiều nguồn cho cùng một claim, mỗi nguồn giữ một `source_id` riêng để Validator và Human Reviewer đối chiếu.

### 3.2. Summarizer Agent

Summarizer chỉ được gọi khi hội thoại dài hoặc khi cần nén ngữ cảnh. Nội dung cần giữ lại gồm học vấn, ngành học, kinh nghiệm AI/ML, kỹ năng lập trình, chương trình quan tâm, mục tiêu nghề nghiệp, câu hỏi chưa giải quyết và thông tin đã được cán bộ tuyển sinh xác nhận.

Ví dụ output:

```json
{
  "candidate_profile": {
    "education": "Sinh viên năm 3",
    "major": "Công nghệ thông tin",
    "ai_experience": "Cơ bản",
    "programming_languages": ["Python"],
    "career_goal": "AI Engineer"
  },
  "interested_programs": ["Chương trình AI Thực chiến"],
  "confirmed_information": [],
  "unresolved_questions": [
    "Ứng viên có đủ điều kiện đăng ký hay không?"
  ]
}
```

### 3.3. Admissions Analyst Agent

Admissions Analyst thực hiện bốn việc:

1. Xác định ý định thật của câu hỏi.
2. Trích xuất entity từ hồ sơ và hội thoại.
3. Xác định thông tin còn thiếu.
4. Viết lại câu hỏi thành truy vấn rõ ràng để Searcher có thể xử lý.

Ví dụ:

> Em năm 3 ngành CNTT, mới học Python thì có vào được không?

Truy vấn đã viết lại:

> Ứng viên đang là sinh viên năm 3 ngành Công nghệ thông tin, có kiến thức Python cơ bản và chưa nêu kinh nghiệm AI/ML. Hãy kiểm tra điều kiện tuyển sinh của các chương trình AI Thực chiến VinAI và xác định thông tin cần bổ sung để đánh giá mức độ phù hợp.

Output đề xuất:

```json
{
  "rewritten_query": "Kiểm tra điều kiện tuyển sinh của các chương trình AI Thực chiến VinAI...",
  "intent": "program_eligibility",
  "entities": {
    "education_year": 3,
    "major": "Công nghệ thông tin",
    "python_level": "basic"
  },
  "missing_information": [
    "Kinh nghiệm AI/ML",
    "Thời gian có thể tham gia",
    "Mục tiêu nghề nghiệp"
  ],
  "sub_tasks": [
    "Tra cứu điều kiện tuyển sinh",
    "Tra cứu yêu cầu đầu vào",
    "Đối chiếu hồ sơ ứng viên"
  ]
}
```

### 3.4. Searcher Agent

Searcher nhận truy vấn đã viết lại, chia thành các sub-query, chọn nguồn dữ liệu phù hợp và thu thập bằng chứng. Agent này có thể được Validator gọi lại khi dữ liệu còn thiếu hoặc chưa đủ tin cậy.

Thứ tự ưu tiên nguồn:

1. Văn bản chính sách chính thức.
2. Cơ sở dữ liệu chương trình nội bộ.
3. Website chính thức của chương trình.
4. FAQ đã được cán bộ tuyển sinh phê duyệt.
5. Thông báo tuyển sinh có ngày hiệu lực rõ ràng.

Không dùng blog, bài đăng mạng xã hội hoặc nguồn không chính thức để kết luận về điều kiện tuyển sinh, học phí, học bổng hoặc ngoại lệ chính sách.

Mọi thông tin lấy từ nguồn nào phải giữ lại đúng `source_id` của nguồn đó, không được chỉ lưu câu trả lời đã rút gọn. Mỗi evidence cần giữ cả nội dung trích xuất lẫn trace gốc để về sau:

- truy ngược về tài liệu gốc;
- gắn ID cho từng claim;
- tạo citation ổn định;
- đối chiếu khi nguồn có cập nhật hoặc mâu thuẫn.

Với mỗi kết quả truy xuất, Searcher phải chuẩn hóa evidence và gắn metadata kiểm tra nguồn:

- `source_type`: loại nguồn, ví dụ `official_policy`, `internal_program_db`, `official_website`, `approved_faq`, `admission_notice`.
- `source_id`: định danh nguồn gốc để truy vết xuyên suốt.
- `source_url` hoặc `document_id`: định danh nguồn để truy vết.
- `source_owner`: đơn vị/cán bộ phụ trách nguồn nếu có.
- `published_at` và `effective_from/effective_to`: ngày công bố và hiệu lực nếu có.
- `approval_status`: `official`, `approved`, `unverified` hoặc `rejected`.
- `source_trust_score`: điểm tin cậy nguồn từ 0 đến 1.
- `query_relevance_score`: điểm liên quan giữa evidence và user query từ 0 đến 1.
- `matched_query_terms`: các ý chính/entity trong user query được evidence hỗ trợ.
- `unsupported_query_terms`: các ý chính/entity trong user query chưa được evidence hỗ trợ.

Quy tắc chấm điểm liên quan:

- `0.8 - 1.0`: evidence trả lời trực tiếp câu hỏi hoặc điều kiện chính trong user query.
- `0.5 - 0.79`: evidence liên quan một phần, cần thêm nguồn để kết luận.
- `0.2 - 0.49`: evidence chỉ liên quan gián tiếp, không đủ dùng làm căn cứ chính.
- `< 0.2`: evidence không phù hợp, loại khỏi phần tổng hợp.

Searcher chỉ chuyển sang Validator các evidence có `approval_status` khác `rejected`, `source_trust_score >= 0.7` và `query_relevance_score >= 0.5`. Nếu không có evidence đạt ngưỡng, Searcher phải trả trạng thái thiếu dữ liệu hoặc yêu cầu tìm nguồn chính thức hơn.

Ví dụ evidence output:

```json
{
  "evidence_id": "policy_01_chunk_03",
  "source_id": "src_001",
  "claim": "Ứng viên cần có nền tảng lập trình cơ bản để tham gia chương trình.",
  "source_type": "official_policy",
  "document_id": "vinai_ai_practical_admission_policy_2026",
  "source_url": "https://example.edu/admissions/policy-2026",
  "published_at": "2026-05-20",
  "effective_from": "2026-06-01",
  "effective_to": "2026-12-31",
  "approval_status": "official",
  "source_trust_score": 0.95,
  "query_relevance_score": 0.86,
  "matched_query_terms": ["sinh viên năm 3", "CNTT", "Python cơ bản"],
  "unsupported_query_terms": ["kinh nghiệm AI/ML"]
}
```

### 3.5. Program Matching Agent

Program Matching Agent chỉ được kích hoạt với các câu hỏi như:

- Em phù hợp chương trình nào?
- Em có đủ điều kiện không?
- Nên chọn chương trình A hay B?
- Hồ sơ của em cần bổ sung gì?

Agent này chỉ được đánh giá theo các nhãn:

- `suitable`
- `potentially_suitable`
- `insufficient_information`
- `unlikely_suitable`

Không được trả về `accepted` hoặc `rejected`.

Ví dụ output:

```json
{
  "recommendations": [
    {
      "program": "Chương trình A",
      "fit_level": "potentially_suitable",
      "matched_requirements": [
        "Đang học ngành kỹ thuật",
        "Có kiến thức Python"
      ],
      "unverified_requirements": [
        "Kiến thức toán",
        "Khả năng tham gia toàn thời gian"
      ],
      "evidence_ids": ["policy_01", "program_02"]
    }
  ],
  "final_admission_decision": false
}
```

### 3.6. Validator Agent

Validator kiểm tra:

- Bằng chứng có trả lời đủ câu hỏi không?
- Nguồn có chính thức hoặc đã được phê duyệt không?
- Nguồn có metadata truy vết rõ ràng không?
- Điểm tin cậy nguồn có đạt ngưỡng không?
- Điểm liên quan giữa evidence và user query có đạt ngưỡng không?
- Văn bản còn hiệu lực không?
- Các nguồn có mâu thuẫn không?
- Kết luận của Program Matching có được bằng chứng hỗ trợ không?
- Câu trả lời có vượt quá nội dung tài liệu không?
- Có cần con người xác nhận không?

Ngưỡng mặc định:

- `source_trust_score >= 0.7` để evidence được dùng làm căn cứ.
- `query_relevance_score >= 0.5` để evidence được giữ lại.
- `query_relevance_score >= 0.8` cho các kết luận quan trọng như điều kiện tuyển sinh, học phí, học bổng, deadline và chính sách ngoại lệ.
- Nếu evidence có nguồn chính thức nhưng điểm liên quan thấp, không được dùng để kết luận trực tiếp.
- Nếu evidence liên quan cao nhưng nguồn chưa được phê duyệt, phải `retry_search` hoặc `hitl_required`.
- Nếu cùng một claim xuất hiện từ nhiều nguồn, phải ưu tiên nguồn có `source_trust_score` cao hơn, ngày hiệu lực mới hơn và `source_id` rõ ràng hơn.

Validator có thể trả về `pass`, `retry_search`, `retry_analysis` hoặc `hitl_required`. Nên giới hạn tối đa hai vòng retry để tránh lặp vô hạn.

Ví dụ output:

```json
{
  "verdict": "hitl_required",
  "confidence": 0.71,
  "evidence_complete": true,
  "evidence_consistent": false,
  "source_check_passed": true,
  "relevance_check_passed": true,
  "minimum_source_trust_score": 0.9,
  "minimum_query_relevance_score": 0.82,
  "issues": [
    "Hai tài liệu có điều kiện kinh nghiệm khác nhau",
    "Chưa xác định tài liệu nào mới hơn"
  ],
  "route_to": "human_reviewer",
  "human_reason": "conflicting_policy"
}
```

---

## 4. Thiết kế Human-in-the-Loop

HITL được đặt sau Validator và trước Synthesis Agent. Con người không cần kiểm tra mọi câu hỏi, mà chỉ can thiệp khi có rủi ro, thiếu chắc chắn hoặc tác động đến quyền lợi/hồ sơ ứng viên.

HITL Gate nên kết hợp rule-based logic với đánh giá của LLM. Không nên chỉ dựa vào LLM tự quyết định.

### Điều kiện bắt buộc chuyển HITL

| Tình huống | Xử lý |
|---|---|
| Không tìm thấy nguồn chính thức | Chuyển cán bộ tuyển sinh |
| Hai chính sách mâu thuẫn | Chuyển cán bộ tuyển sinh |
| Chính sách không có ngày hiệu lực | Chuyển cán bộ tuyển sinh |
| Ứng viên xin ngoại lệ điều kiện | Chuyển cán bộ tuyển sinh |
| Yêu cầu xác nhận đủ điều kiện hoặc trúng tuyển | Chuyển cán bộ tuyển sinh |
| Học phí, học bổng hoặc hỗ trợ tài chính đặc biệt | Chuyển cán bộ tuyển sinh |
| Khiếu nại kết quả tuyển sinh | Chuyển cán bộ tuyển sinh |
| Trạng thái hồ sơ không khớp dữ liệu | Chuyển cán bộ tuyển sinh |
| Thay đổi hoặc xóa thông tin hồ sơ | Bắt buộc phê duyệt |
| AI có confidence dưới ngưỡng | Chuyển cán bộ tuyển sinh |
| Câu hỏi chứa dữ liệu cá nhân nhạy cảm | Chuyển hoặc yêu cầu dùng kênh bảo mật |

### Hành động của Human Reviewer

Cán bộ tuyển sinh có thể:

- `approve`: phê duyệt câu trả lời.
- `edit_and_approve`: chỉnh sửa rồi phê duyệt.
- `reject`: không cho gửi câu trả lời.
- `request_more_information`: yêu cầu ứng viên bổ sung thông tin.
- `request_new_retrieval`: yêu cầu Searcher tìm lại.
- `escalate`: chuyển cho cán bộ phụ trách chương trình.
- `update_knowledge`: đánh dấu nội dung cần cập nhật vào knowledge base.

Audit log cần lưu câu hỏi gốc, truy vấn đã viết lại, nguồn đã dùng, kết quả Validator, lý do chuyển HITL, câu trả lời AI đề xuất, nội dung con người chỉnh sửa, người phê duyệt, thời gian phê duyệt và phiên bản chính sách được sử dụng.

---

## 5. Công cụ của Searcher Agent

| Tool | Dữ liệu |
|---|---|
| Knowledge Base Search | Quy chế, chính sách, FAQ, hướng dẫn tuyển sinh. |
| Program Database Tool | Tên chương trình, nội dung, yêu cầu, thời lượng, hình thức học. |
| Official Website Search | Thông báo mới nhất trên website chính thức. |
| Deadline Tool | Ngày mở đơn, đóng đơn, phỏng vấn, công bố kết quả. |
| CRM Read Tool | Trạng thái hồ sơ của ứng viên. |
| Candidate Profile Tool | Thông tin ứng viên đã cung cấp trong hội thoại. |
| Ticket/Handoff Tool | Tạo ticket cho cán bộ tuyển sinh. |
| Notification Tool | Gửi thông báo khi cán bộ đã xử lý. |
| Audit Log Tool | Lưu quyết định, nguồn dữ liệu và lịch sử xử lý. |

Trong MVP, CRM nên ở chế độ `read-only`. Mọi hành động sửa, xóa hoặc cập nhật hồ sơ phải qua HITL.

---

## 6. Plan triển khai đề xuất

### 6.1. Roadmap 6 tuần

| Tuần | Trọng tâm | Công việc chính | Đầu ra |
|---|---|---|---|
| Tuần 1 | Chốt phạm vi và dữ liệu | Xác định nhóm câu hỏi MVP, taxonomy intent, nguồn dữ liệu, chính sách HITL, tiêu chí đánh giá. | Problem statement, intent taxonomy, knowledge inventory, HITL rulebook. |
| Tuần 2 | Xây RAG baseline | Làm sạch tài liệu, chia chunk, gắn metadata, tạo vector index, xây API truy xuất cơ bản. | Knowledge base, vector database, RAG baseline có trích nguồn. |
| Tuần 3 | Xây MAS v1 | Implement Orchestrator, Summarizer, Admissions Analyst, Searcher và tool-calling flow. | MAS v1 có routing, query rewriting và retrieval. |
| Tuần 4 | Thêm kiểm chứng | Implement Validator, Program Matching, retry loop và schema hóa evidence. | MAS v2 có validation, retry và tư vấn chương trình có điều kiện. |
| Tuần 5 | Tích hợp HITL | Xây HITL Gate, dashboard review, ticket handoff, audit log và notification. | Human review dashboard và workflow phê duyệt. |
| Tuần 6 | Đánh giá và demo | Tạo test set, chạy evaluation, sửa lỗi, tối ưu prompt, chuẩn bị demo. | Prototype hoàn chỉnh, báo cáo evaluation, demo script. |

### 6.2. Milestone theo mức độ ưu tiên

| Milestone | Mục tiêu | Tiêu chí hoàn thành |
|---|---|---|
| M1 - RAG nền tảng | Chatbot trả lời được câu hỏi tuyển sinh đơn giản bằng nguồn chính thức. | Câu trả lời có citation, không trả lời ngoài nguồn, latency chấp nhận được. |
| M2 - Multi-agent routing | Hệ thống biết phân loại câu hỏi và gọi đúng agent/tool. | Ít nhất 80% intent trong test set được route đúng. |
| M3 - Validation loop | Hệ thống phát hiện thiếu dữ liệu, nguồn mâu thuẫn và gọi retry phù hợp. | Validator giảm hallucination và log được lý do retry. |
| M4 - Program matching | Hệ thống tư vấn mức độ phù hợp nhưng không ra quyết định tuyển sinh. | Output có nhãn phù hợp, điều kiện đã khớp, điều kiện chưa xác minh và evidence. |
| M5 - HITL | Câu hỏi rủi ro cao được chuyển cán bộ tuyển sinh. | Không bỏ sót các case ngoại lệ, khiếu nại, học bổng đặc biệt, cập nhật hồ sơ. |
| M6 - Demo-ready | Prototype chạy ổn định với bộ câu hỏi demo. | Có giao diện, log, báo cáo đánh giá và kịch bản thuyết trình. |

### 6.3. Backlog MVP

| Hạng mục | Ưu tiên | Ghi chú |
|---|---|---|
| Ingest tài liệu tuyển sinh | P0 | Cần metadata: nguồn, ngày hiệu lực, loại tài liệu, chương trình áp dụng. |
| Chat API | P0 | Nhận câu hỏi, session id, hồ sơ ứng viên, trả câu trả lời và citation. |
| Orchestrator | P0 | Route intent, risk, clarification, HITL. |
| Searcher + RAG | P0 | Truy xuất theo sub-query, trả evidence chuẩn hóa. |
| Validator | P0 | Kiểm tra completeness, consistency, source quality. |
| Synthesis | P0 | Trả lời ngắn gọn, đúng nguồn, có bước tiếp theo. |
| Program Matching | P1 | Chỉ tư vấn phù hợp, không quyết định trúng tuyển. |
| HITL Dashboard | P1 | Duyệt, sửa, reject, yêu cầu tìm thêm. |
| Audit log | P1 | Lưu trace phục vụ kiểm thử và cải tiến. |
| CRM read-only | P2 | Chỉ nên thêm khi có dữ liệu hồ sơ thật hoặc giả lập đủ tốt. |
| Notification | P2 | Có thể dùng email/Slack/webhook sau MVP. |

---

## 7. Tech stack đề xuất

| Lớp | Công nghệ đề xuất | Vai trò | Ghi chú |
|---|---|---|---|
| Frontend | Next.js, React, Tailwind CSS | Chat UI, dashboard HITL, màn hình audit. | Phù hợp prototype nhanh, dễ demo. |
| Backend API | FastAPI hoặc NestJS | Điều phối request, session, agent workflow, auth. | FastAPI hợp với Python/RAG; NestJS hợp nếu team mạnh TypeScript. |
| Agent orchestration | LangGraph hoặc OpenAI Agents SDK | Xây graph multi-agent, retry loop, HITL state. | LangGraph mạnh về workflow có trạng thái; Agents SDK gọn nếu dùng sâu hệ OpenAI. |
| LLM | OpenAI GPT-4.1/GPT-4o hoặc model tương đương | Orchestrator, Analyst, Validator, Synthesis. | Nên cấu hình theo vai trò để tối ưu chi phí. |
| Embedding | OpenAI text-embedding-3-large/small hoặc BGE-M3 | Vector hóa tài liệu tuyển sinh. | `small` tiết kiệm; `large` tốt hơn khi tài liệu nhiều/nhiễu. |
| Vector database | Qdrant, Weaviate hoặc pgvector | Lưu và truy xuất chunk tài liệu. | pgvector đơn giản nếu đã dùng PostgreSQL. |
| Relational database | PostgreSQL | Session, profile, audit log, ticket, metadata. | Nên là nguồn chính cho dữ liệu có cấu trúc. |
| Cache/queue | Redis, Celery/RQ | Cache retrieval, xử lý job nền, notification. | Có thể bỏ qua ở demo nhỏ. |
| Document processing | Unstructured, PyMuPDF, docling | Parse PDF/DOCX/HTML, chuẩn hóa tài liệu. | Quan trọng để RAG sạch. |
| Evaluation | Ragas, DeepEval, custom test set | Đánh giá accuracy, faithfulness, citation, HITL recall. | Nên có bộ câu hỏi thật/giả lập từ tuyển sinh. |
| Observability | LangSmith, OpenTelemetry, Grafana | Theo dõi trace agent, chi phí, latency, lỗi. | Rất hữu ích khi debug multi-agent. |
| Auth | NextAuth/Auth.js hoặc OAuth nội bộ | Phân quyền ứng viên, cán bộ tuyển sinh, admin. | MVP có thể dùng mock auth. |
| Deployment | Docker, Docker Compose, Vercel/Render/Fly.io | Đóng gói demo và triển khai nhanh. | Hackathon nên ưu tiên Docker Compose hoặc Vercel + managed DB. |

### Tech stack gọn cho hackathon

Nếu mục tiêu là prototype trong thời gian ngắn, nên chọn:

- Frontend: Next.js + Tailwind CSS.
- Backend: FastAPI.
- Agent workflow: LangGraph.
- Database: PostgreSQL + pgvector.
- Document parsing: PyMuPDF hoặc docling.
- Evaluation: bộ test set thủ công + Ragas.
- Deployment: Docker Compose hoặc Vercel frontend + Render backend.

---

## 8. Phạm vi MVP

MVP nên tập trung vào bốn nhóm câu hỏi:

1. Thông tin chương trình.
2. Điều kiện tuyển sinh.
3. Quy trình và thời hạn đăng ký.
4. Tư vấn chương trình dựa trên hồ sơ cơ bản.

HITL tập trung vào:

- Ngoại lệ điều kiện.
- Đánh giá khả năng đủ điều kiện.
- Học phí và học bổng đặc biệt.
- Thông tin mâu thuẫn.
- Khiếu nại.
- Các thao tác ảnh hưởng đến hồ sơ.

Chưa cần cho MVP:

- AI tự đánh giá CV hoàn chỉnh.
- AI tự chấm bài đầu vào.
- AI tự quyết định trúng tuyển.
- Tự động sửa hồ sơ trong CRM.
- Tự động gửi offer.

---

## 9. Bộ tiêu chí đánh giá

### Chất lượng câu trả lời

- Accuracy.
- Faithfulness.
- Relevance.
- Citation correctness.
- Completeness.
- Tỷ lệ hallucination.

Validator đặc biệt quan trọng với faithfulness vì dữ liệu thiếu hoặc nhiễu dễ khiến LLM tự bổ sung nội dung không có trong nguồn.

### Chất lượng HITL

- Tỷ lệ câu hỏi cần HITL được phát hiện đúng.
- Tỷ lệ trường hợp rủi ro bị bỏ sót.
- Tỷ lệ câu trả lời được con người phê duyệt nguyên trạng.
- Tỷ lệ câu trả lời phải chỉnh sửa.
- Thời gian chờ cán bộ xử lý.
- Số lần cùng một vấn đề phải chuyển con người.

### Hiệu quả vận hành

- Tỷ lệ câu hỏi được giải quyết tự động.
- Thời gian phản hồi trung bình.
- Chi phí trên mỗi câu hỏi.
- Số câu hỏi giảm tải cho đội tuyển sinh.
- Tỷ lệ ứng viên tiếp tục sang bước đăng ký.

---

## 10. Tên framework đề xuất

Tên đầy đủ:

**VinAI Admissions Multi-Agent Assistant with Human-in-the-Loop**

Tên ngắn:

**VinAI Admissions Assistant**

Các agent cốt lõi:

```text
Orchestrator
Summarizer
Admissions Analyst
Searcher
Program Matcher
Validator
HITL Gate
Human Reviewer
Synthesizer
```

Thông điệp thiết kế:

> AI tự động xử lý các câu hỏi rõ ràng, có nguồn chính thức và rủi ro thấp; con người chịu trách nhiệm cho ngoại lệ, quyết định tuyển sinh, dữ liệu nhạy cảm và các trường hợp AI không chắc chắn.
