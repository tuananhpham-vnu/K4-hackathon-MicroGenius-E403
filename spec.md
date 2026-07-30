

# AI SPEC — [Tên lát cắt] · Nhóm [XX] · Zone [X]
Hướng: C — Làn mở
Loại: Tính năng mới

### §1. User & Job

### Job executor + workflow

**Job executor:** Người đang quan tâm và chuẩn bị đăng ký chương trình AI Thực chiến.

**Workflow hiện tại:**

```text
Quan tâm chương trình
        ↓
Tham gia Facebook Group
        ↓
Tìm bài cũ hoặc đọc website
        ↓
Không tìm thấy thông tin
        ↓
Đăng bài hỏi
        ↓
Chờ Admin/Học viên trả lời
        ↓
Tiếp tục hỏi thêm nếu còn thắc mắc
```

---

### Core JTBD

> Khi chuẩn bị đăng ký một chương trình đào tạo, tôi muốn nhanh chóng tìm được câu trả lời chính xác cho các thắc mắc của mình để quyết định có nên đăng ký và chuẩn bị hồ sơ đúng hạn.

---

### Problem statement

Người quan tâm đến chương trình phải đăng bài hoặc hỏi nhiều lần trong group vì thông tin tuyển sinh phân tán giữa website, Facebook và các bài đăng cũ. Việc chờ phản hồi từ admin hoặc học viên khiến quá trình tìm hiểu mất thời gian và nhiều câu hỏi bị lặp lại.

---

### Evidence (Chuẩn B - Data Mining)

#### Phương pháp mining

- **Nguồn dữ liệu:** Facebook Group AI Thực chiến.
- **Số lượng mẫu:** 100 bài đăng.
- **Khoảng thời gian:** 12/07/2026 – 30/07/2026.
- **Tiêu chí phân loại:** Một bài được xem là liên quan đến tuyển sinh nếu chứa các nội dung:
  - Điều kiện tham gia
  - Hồ sơ đăng ký
  - Kết quả xét tuyển
  - Phỏng vấn
  - Học phí
  - Lịch khai giảng
  - Địa điểm học
  - Khóa đang tuyển sinh

#### Kết quả

- **Tổng số bài phân tích:** 100
- **Số bài liên quan đến tuyển sinh:** 59
- **Tỷ lệ:** **59%**

Các chủ đề được hỏi nhiều nhất:

- Điều kiện tham gia chương trình
- Hồ sơ và kết quả xét tuyển
- Lịch khai giảng
- Khóa đang tuyển sinh
- Địa điểm học (Hà Nội/HCM)
- Chuẩn bị thi

#### Ví dụ nguyên văn

> "Dạ chào mọi người, mình ở HCM... chương trình có mở tại HCM không?"

> "Cho em hỏi ngày 10/9 là khai giảng khóa 5 đúng không ạ?"

> "Khi nào sẽ có kết quả vòng hồ sơ khóa 5?"

> "Giờ đang tuyển sinh khóa mấy vậy ạ?"

> "Em cần ôn những gì để thi đầu vào?"

---

## §2. Impact & quyết định chọn

### Bảng Impact

| Ứng viên | Bao nhiêu người gặp | Tần suất | Mỗi lần tốn gì | Khả thi trong hackathon |
|-----------|--------------------:|----------|----------------|-------------------------|
| **Hỏi thông tin tuyển sinh** | **59/100 bài (59%)** | Hàng ngày | Chờ admin/học viên phản hồi từ 10–60 phút | Cao |
| Hỏi tài liệu học | ~15/100 bài | Theo tuần | Mất thời gian tìm link tài liệu | Trung bình |
| Hỏi lỗi Discord/VLearn | ~10/100 bài | Không thường xuyên | 5–10 phút xử lý | Cao |

---

### Ứng viên đã loại

#### 1. Hỗ trợ tìm tài liệu học

**Lý do:**

- Chủ yếu phục vụ học viên đã nhập học.
- Đã có kênh discord và các nhóm zalo hỗ trợ
- Tần suất xuất hiện thấp hơn.

#### 2. Hỗ trợ lỗi Discord/VLearn

**Lý do:**

- Ít xuất hiện trong dữ liệu.
- Có thể giải quyết bằng FAQ hoặc hướng dẫn có sẵn.
- Không phải pain point lớn nhất.

---

### Ứng viên được chọn

#### Hỗ trợ tư vấn tuyển sinh

**Lý do lựa chọn:**

- Chiếm **59%** tổng số bài đăng trong dataset.
- Là nhóm câu hỏi xuất hiện thường xuyên nhất.
- Nội dung có tính lặp lại cao.
- Phần lớn câu trả lời đã tồn tại trên website hoặc FAQ.
- Có thể xây dựng chatbot sử dụng Knowledge Base trong phạm vi hackathon.
- Giảm tải cho đội ngũ tuyển sinh và giúp người quan tâm nhận phản hồi nhanh hơn.

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

## §5. Kiểu lỗi — 4 lớp chỗ khó + kịch bản (≥8) [bảng theo guide §2.5]

## §6. Bốn đường đi của trải nghiệm
- Happy path: · Low-confidence (②): · Failure/không căn cứ (①): · Correction (user sửa):
- Khi bị đòi ngoài phạm vi (③): · Case đặc thù domain (④):

## §7. Kiểm thử
- Chiều chất lượng + định nghĩa kiểm chứng được:
- Golden set (≥20 case theo cơ cấu trong guide §2.6, file trong eval/):
- Quality bar (chốt từ 23:59, giữ nguyên sau đó): "Đạt khi ≥ ___% qua bộ, và ___"
- Kết quả các lượt chạy (bảng % — cập nhật đến trước CP6):

## §8. Phân công & kế hoạch
- Phân công có tên: spec / evidence / prompt / code / demo
- Willing users (≥3 tên) + kế hoạch vòng validation CP5 (3 câu hỏi, ai log):
- Multi-prototype (nếu làm): trục khác biệt của ≥2 phương án + lý do chọn:

## §9. Changelog
| Thời điểm | Đổi gì | Vì sao (trỏ về feedback/case nào) |