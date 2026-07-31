# Kịch bản Pitching — AI Tư Vấn Tuyển Sinh "AI Thực Chiến"

> Thời lượng gợi ý: ~6 phút nói + 2-3 phút demo trực tiếp + Q&A.
> Có time-marker (⏱) để tự canh giờ, có thể cắt bớt phần [có thể lược] nếu bị giới hạn thời gian.

---

## 0. Hook mở đầu (⏱ 0:00 – 0:30)

> "Các bạn thử tưởng tượng: bạn đang quan tâm một chương trình đào tạo, vào Facebook Group để hỏi, và phải **chờ 10 đến 60 phút** mới có admin hoặc học viên cũ trả lời — trong khi câu trả lời đó đã có sẵn trên website, chỉ là không ai tìm ra. Tệ hơn, tuần sau có người khác hỏi **y hệt câu đó**.
>
> Đó chính là điều đang xảy ra thật, mỗi ngày, trong Facebook Group của chương trình **AI Thực Chiến** — chương trình đào tạo AI hợp tác giữa Vingroup và VinUni. Và đó là bài toán nhóm mình giải quyết."

---

## 1. Lý do chọn đề tài (⏱ 0:30 – 1:30)

**Không đoán mò — mình đào dữ liệu thật trước khi chọn bài toán:**

- Mining **100 bài đăng** trong Facebook Group AI Thực Chiến, từ 12/07 đến 30/07/2026.
- Phân loại theo 8 nhóm nội dung: điều kiện tham gia, hồ sơ đăng ký, kết quả xét tuyển, phỏng vấn, học phí, lịch khai giảng, địa điểm học, khóa đang tuyển.
- Kết quả: **59/100 bài (59%) liên quan trực tiếp đến tư vấn tuyển sinh** — nhóm câu hỏi lớn nhất, lặp lại hằng ngày.

**Hai ứng viên khác từng cân nhắc rồi loại:**
| Ứng viên | Vì sao loại |
|---|---|
| Hỗ trợ tìm tài liệu học | Chỉ phục vụ học viên đã nhập học, đã có Discord/Zalo hỗ trợ, tần suất thấp hơn nhiều (~15%) |
| Hỗ trợ lỗi Discord/VLearn | Ít xuất hiện (~10%), không phải pain point lớn, giải quyết được bằng FAQ có sẵn |

**→ Chọn "Tư vấn tuyển sinh" vì:** tần suất cao nhất, tính lặp lại cao nhất, câu trả lời phần lớn *đã tồn tại* (không cần tạo tri thức mới, chỉ cần tổ chức và truy xuất đúng lúc), và **khả thi xây trong khuôn khổ hackathon** bằng một Knowledge Base + chatbot.

---

## 2. Giải pháp & tính ứng dụng (⏱ 1:30 – 2:30)

**Một câu duy nhất mô tả lát cắt:**

> Một ứng viên hỏi *"Em có đủ điều kiện tham gia chương trình AI không?"* → hệ thống đối chiếu với nguồn tuyển sinh hiện hành → trả lời có **trích dẫn nguồn (citation)**, hoặc chuyển thẳng cho cán bộ tuyển sinh nếu vượt thẩm quyền AI.

**Tính ứng dụng thực tế:**
- **Giảm tải cho đội ngũ tuyển sinh:** không phải trả lời tay hàng chục câu hỏi lặp lại mỗi ngày.
- **Ứng viên nhận phản hồi tức thì** thay vì chờ 10–60 phút, 24/7, không phụ thuộc admin online hay không.
- **Không "ảo giác" (hallucination) về chính sách nhạy cảm:** hệ thống **chủ động từ chối quyết định** những việc rủi ro cao — xác nhận trúng tuyển, cam kết học bổng/học phí, ngoại lệ chính sách — và bắt buộc chuyển người thật (HITL). Đây là lựa chọn thiết kế có chủ đích, không phải giới hạn kỹ thuật.
- **Có thể tái sử dụng** cho bất kỳ chương trình tuyển sinh/đào tạo nào khác chỉ bằng cách đổi Knowledge Base — kiến trúc không gắn cứng vào domain AI Thực Chiến.

---

## 3. Cách tiếp cận — vì sao không làm RAG đơn giản hay 1 agent duy nhất (⏱ 2:30 – 3:30)

Mình có nghiên cứu 2 hệ thống tương tự trước khi quyết định kiến trúc:

| Tham khảo | Học được gì | Vì sao không bê nguyên |
|---|---|---|
| **Salesforce Agentforce** | Tách rõ subagent/action/reasoning, có audit trail | Kiến trúc enterprise, quá nặng cho prototype hackathon |
| **Intercom Fin AI Agent** | Quản lý knowledge source tập trung, kiểm soát nguồn nào được dùng | Phụ thuộc knowledge platform riêng, không linh hoạt |

**Hai hướng cũng cân nhắc rồi loại:**
- *Traditional RAG (retrieval tĩnh → LLM trả lời thẳng):* dễ làm nhưng không tự biết khi nào cần tra thêm nguồn hay khi nào cần chuyển người thật.
- *Single-agent (1 prompt to rule them all):* dễ demo nhưng prompt phình to, không phân quyền được tool/memory, không trace được ai làm gì khi sai.

**→ Lựa chọn:** *Conditional tool-using Multi-Agent System* trên **LangGraph**, có **Agent Harness** (mỗi agent chỉ được dùng tool được cấp phép) + **Validator kiểm tra độ tin cậy nguồn** + **HITL gate** rõ ràng — nhẹ hơn Agentforce, kiểm soát nguồn chặt hơn RAG thường, và trace được từng bước quyết định.

---

## 4. Workflow — Người dùng TRƯỚC và SAU (⏱ 3:30 – 4:30)

### Trước khi có giải pháp
```
Quan tâm chương trình
    ↓
Tham gia Facebook Group
    ↓
Tìm bài cũ / đọc website (thông tin phân tán)
    ↓
Không tìm thấy thông tin
    ↓
Đăng bài hỏi
    ↓
Chờ Admin/Học viên trả lời (10–60 phút, có thể cả ngày)
    ↓
Hỏi lại nếu còn thắc mắc → lặp lại chu trình
```
**Nỗi đau:** thông tin phân tán, chờ đợi, câu hỏi lặp lại, đội ngũ tuyển sinh quá tải.

### Sau khi có giải pháp
```
Quan tâm chương trình
    ↓
Mở chatbot tư vấn tuyển sinh (trên web)
    ↓
Hỏi trực tiếp bằng ngôn ngữ tự nhiên
    ↓
   ┌─── Câu hỏi rõ, có nguồn tin cậy ───→ Trả lời NGAY, kèm trích dẫn nguồn (vài giây)
   ├─── Câu hỏi mơ hồ / thiếu hồ sơ ────→ Hệ thống hỏi lại 1-3 thông tin còn thiếu
   └─── Vượt thẩm quyền AI (rủi ro cao) ─→ Chuyển thẳng cán bộ tuyển sinh, không đoán mò
```
**Thay đổi cho người dùng:** từ "đăng bài rồi chờ" → "hỏi và có câu trả lời có căn cứ ngay lập tức"; luôn biết rõ *vì sao* AI trả lời vậy (evidence + source card có thể bấm vào xem gốc); và biết chắc AI không tự ý quyết định thay cán bộ tuyển sinh trong các case nhạy cảm.

---

## 5. Kiến trúc kỹ thuật — luồng code & agent (⏱ 4:30 – 5:30)

**6 agent nối thành state graph (LangGraph), mỗi agent có phạm vi tool/quyền riêng (Agent Harness):**

```
User query
   ↓
[Orchestrator] → phân loại: chitchat / out-of-scope / capability-question / risk / intent
   ↓
[Analyst] → dựng truy vấn tìm kiếm, kiểm tra thiếu thông tin hồ sơ (nếu hỏi mức độ phù hợp)
   ↓
[Searcher] → chỉ agent này được gọi knowledge_base.search + web.search
   ↓
[Validator] → chấm relevance/trust từng evidence; đạt ngưỡng → đi tiếp;
              chưa đạt → retry Searcher (tối đa 2 lần) hoặc chuyển HITL nếu rủi ro cao
   ↓
[HITL gate] → các case nhạy cảm (xác nhận trúng tuyển, ngoại lệ, khiếu nại) LUÔN
              chuyển người thật, không bao giờ để AI tự quyết
   ↓
[Synthesis] → LLM (Gemini) tổng hợp câu trả lời CHỈ từ evidence đã được Validator duyệt,
              bắt buộc có citation
```

- **Nguồn dữ liệu 3 tầng, mỗi tầng có `trust_score` riêng:** tài liệu tuyển sinh chính thức (0.92) > VLearn nội bộ (0.72–0.86) > quan sát cộng đồng/Facebook (0.62). Evidence chỉ được dùng để kết luận khi `relevance_score ≥ 0.30` và trung bình `trust_score ≥ 0.70` — câu trả lời không bao giờ dựa "chính" vào nguồn cộng đồng chưa kiểm chứng.
- **Retrieval:** lexical token-overlap (mặc định) hoặc hybrid BM25 + vector search trên Weaviate (embedding tiếng Việt `bkai-foundation-models/vietnamese-bi-encoder`) khi cấu hình.
- **Web search (Firecrawl)** bổ sung, chỉ tin domain chính thức (`vinuni.edu.vn`, `vinai.io`).
- **Fallback graceful:** nếu máy demo chưa cài `langgraph`, hệ thống tự rơi về workflow thường, API/UI vẫn chạy — không bao giờ "sập" hoàn toàn.

**Kiểm thử — không chỉ code chạy được mà còn đo được chất lượng:**
- Unit test: quyền hạn tool theo agent, bộ nhớ theo phiên (`test_harness.py`), logging JSONL (`test_observability.py`), giữ metadata nguồn khi chunk (`test_retrieval_sources.py`), fallback khi không có API key (`test_synthesis.py`).
- **Golden set 20 case** phủ đủ *4 đường đi trải nghiệm*: happy path, low-confidence, out-of-scope, out-of-authority — chấm theo `expected_intent`, có cần chuyển người hay không, và số evidence tối thiểu.
- **Quality bar tự đặt: ≥ 80% qua bộ.** Baseline ban đầu chỉ đạt **13/20 (65%)** — sau khi sửa lỗi định tuyến chitchat/low-confidence/out-of-scope, kết quả hiện tại là **20/20 (100%)**, vượt xa ngưỡng chất lượng.
- **8 kiểu lỗi được định danh và xử lý riêng biệt** (E01–E08): thiếu nguồn, câu hỏi mơ hồ, thiếu hồ sơ, ngoài phạm vi, ngoài thẩm quyền, thiếu package, xâm phạm bảo mật/riêng tư, lỗi hệ thống — mỗi loại có route xử lý rõ ràng, không đổ chung một cục.

---

## 6. Kết quả & demo (⏱ 5:30 – 6:00)

- **Từ 65% → 100%** trên golden set 20 case sau một vòng lặp sửa lỗi.
- **59% nhu cầu thật** trong dữ liệu được giải quyết bằng một luồng duy nhất, có kiểm soát rủi ro.
- Sẵn sàng demo trực tiếp: hỏi trực tiếp trên UI → xem câu trả lời + evidence + trace (bao nhiêu nguồn, relevance/trust trung bình, có gọi web search hay không).

> *(Chuyển sang demo trực tiếp: mở `frontend/index.html`, hỏi mẫu "Điều kiện tham gia chương trình AI Thực Chiến là gì?" và một câu rủi ro cao như "Em có chắc chắn trúng tuyển không?" để cho thấy HITL kích hoạt.)*

---

## 7. Kết luận (⏱ 6:00)

> "Nhóm mình không xây một chatbot trả lời bừa cho có. Mình xây một hệ thống **biết rõ giới hạn của chính nó** — trả lời nhanh khi có căn cứ, hỏi lại khi thiếu thông tin, và **luôn nhường lại cho con người** khi câu hỏi vượt quá thẩm quyền của AI. Đó là cách một trợ lý tuyển sinh nên hoạt động: nhanh, có căn cứ, và biết khi nào cần dừng lại."

---

## Phụ lục — câu hỏi Q&A dự kiến

| Câu hỏi ban giám khảo có thể hỏi | Gợi ý trả lời ngắn |
|---|---|
| Sao không dùng RAG đơn giản cho nhanh? | RAG tĩnh không tự quyết được khi nào cần tool/human, không phân quyền được — đã phân tích ở §3 |
| Độ chính xác đo bằng gì? | Golden set 20 case, quality bar 80%, hiện đạt 100% — xem `eval/results.json` |
| Nếu AI trả lời sai thì sao? | Cost-of-error cao nên thiết kế conditional: chỉ tự trả lời khi nguồn đạt ngưỡng trust/relevance; case nhạy cảm luôn HITL, không bao giờ để AI tự quyết định trúng tuyển/học bổng/ngoại lệ |
| Có mở rộng cho chương trình khác được không? | Có — kiến trúc tách rời khỏi Knowledge Base, chỉ cần nạp tài liệu tuyển sinh mới |
| Phần nào là mock, phần nào thật? | Thật: state graph, 6 agent, harness, source/evidence trace, retry, API. Mock: local KB thay vì DB tuyển sinh chính thức, lexical retrieval thay embedding+Qdrant khi chưa cấu hình Weaviate, mock human reviewer thay dashboard cán bộ thật |
