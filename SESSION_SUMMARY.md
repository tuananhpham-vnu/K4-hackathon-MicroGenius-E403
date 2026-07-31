# Tóm tắt phiên làm việc — Chatbot tư vấn tuyển sinh AI Thực Chiến

Ngày: 2026-07-31

## 1. Học cách trả lời 50 câu trong `data/test.json` + tích hợp Gemini

- **Rule-engine (`src/admissions_mas/services/workflow.py`)**: sửa/thêm
  - Mở rộng danh sách từ khóa rủi ro cao & ngoài phạm vi (thiếu "gia hạn", "xét lại", "đặt vé"...).
  - Sửa bug chitchat: `"hi "` khớp nhầm vào "**Thi** thế nào?" → chuyển sang regex có word-boundary.
  - Phát hiện câu hỏi mơ hồ (không có từ neo như khóa/hồ sơ/chương trình + câu ngắn) → hỏi lại thay vì đoán.
  - Trích tín hiệu hồ sơ tự khai (học vấn/kinh nghiệm/thời gian) từ câu hỏi tự nhiên cho ý định "đánh giá phù hợp".
  - Chống suy đoán: phát hiện khóa không có trong dữ liệu, số liệu vô căn cứ, hai nguồn mâu thuẫn, nhắc tới hội nhóm Facebook → mỗi trường hợp có phản hồi trung thực riêng, đề nghị cán bộ tuyển sinh xác nhận.
  - Gộp toàn bộ logic sinh câu trả lời vào một hàm `synthesize()` dùng chung cho pipeline cũ và LangGraph (tránh lặp code/lệch hành vi).
- **Retrieval (`retrieval/knowledge_base.py`)**: sửa lỗi nguồn cộng đồng (Facebook, trust thấp) đông về số lượng nên xếp hạng cao hơn tài liệu chính thức → tài liệu có thể trích dẫn luôn ưu tiên trước nguồn không trích dẫn được; gộp các đoạn markdown nhỏ (mỗi câu một dòng) thành chunk đủ lớn để giữ ngữ cảnh.
- **Gemini 3.5 Flash Lite**: chỉ dùng để **soạn câu trả lời từ evidence** (RAG generation) cho nhánh có bằng chứng hợp lệ; câu từ chối/HITL/hỏi lại luôn là template cố định, không bao giờ qua LLM.
- Kết quả: golden set 20/20, `eval/run_test_set.py` (sau này thay bằng `scripts/run_use_case_dashboard.py` của đồng đội) 50/50.

## 2. Sự cố mất code do merge nhánh `main` + khôi phục

- Người dùng vô tình mất các thay đổi trên khi checkout ngược từ detached HEAD — nhưng commit `c78d736` vẫn còn tồn tại (orphan, chưa bị garbage-collect) nên khôi phục được nội dung để đối chiếu.
- Trong lúc đó, đồng đội (`tanh`) đã merge một hướng song song vào `main`: `GeminiSynthesisService` (dùng SDK `google-genai` chính thức, có `source_title`/`source_uri`), Weaviate hybrid retrieval, và `scripts/run_use_case_dashboard.py` — bộ chấm tự động 50 case trong `data/test.json` (rất hữu ích, dùng lại thay vì viết mới).
- **Bug chặn cứng phát hiện được**: `knowledge_base.py` import cứng `semantic_chunkers.RegexChunker`, package này chỉ hỗ trợ Python < 3.14 nhưng máy chạy Python 3.14.4 → toàn bộ app crash khi import. Đã sửa thành lazy-import với fallback chunker nội bộ (merge fragment nhỏ) khi package vắng mặt/không tương thích.
- Ghép lại toàn bộ fix ở mục 1 vào `workflow.py`/`graph.py` hiện tại của đồng đội (giữ nguyên `GeminiSynthesisService`, `graph.py` mới) thay vì ghi đè.
- **Chặn an toàn quan trọng**: thêm rào cứng để câu hỏi rủi ro cao/ngoài phạm vi **không bao giờ** đi qua Gemini — chỉ trả lời template cố định.
- Sửa `_max_known_cohort()`: ban đầu quét cả bài Facebook nên bắt nhầm "Khóa 7" từ một câu hỏi bâng quơ của học viên — giới hạn chỉ quét nguồn chính thức (trust ≥ 0.7).
- Kết quả cuối: tests 7/7, eval 6/6, golden set 20/20, dashboard 50/50 (cả fallback lẫn Gemini thật) — tăng từ baseline 40/50 (80%) của đồng đội.

## 3. Nhánh "câu hỏi về khả năng" (capability question)

- Câu như "Bạn có thể làm được những gì" bị rơi vào nhánh "câu hỏi mơ hồ" (không có từ neo) → trả lời sai (template hỏi lại).
- Thêm `CAPABILITY_PATTERN` nhận diện câu hỏi meta ("làm được gì", "bạn là ai", "chức năng của bạn"...) → nhánh riêng, bỏ qua retrieval, trả lời qua `GeminiSynthesisService.answer_capability_question()` (có fallback cố định khi không có key).

## 4. Đoạn văn "nguyên tắc thiết kế AI" cho form nộp bài

- Viết đoạn ≥200 ký tự mô tả 5 nguyên tắc HAX/PAIR đã áp dụng thật trong code (G10 - thu hẹp phạm vi khi nghi ngờ, G11 - giải thích vì sao, PAIR Errors & Graceful Failure, PAIR Mental Models, G1 - làm rõ hệ thống làm được gì), mỗi nguyên tắc trỏ đúng vào cơ chế/hàm cụ thể đã build.

## 5. Multi-turn hội thoại + sửa frontend + ưu tiên nguồn VinUni chính thức

- **Multi-turn**: `orchestrate()`/`analyze()` nhận `history`; câu hỏi tỉnh lược ("Còn phụ cấp thì sao?") được ghép với câu hỏi trước đó để tránh bị hỏi lại oan.
- **Frontend chat (`frontend/app.js`)**: viết lại hoàn toàn — trước đây mỗi câu hỏi mới **xóa sạch** hội thoại cũ; giờ lưu hội thoại trong `sessionStorage`, mỗi lượt chỉ append bubble mới, gửi kèm lịch sử lên backend. Có nút "Cuộc trò chuyện mới".
- **Bug các nút bấm không trả lời được**: chip/gợi ý chỉ hoạt động lần đầu điều hướng tới `#chat` (không kích hoạt lại khi đã ở sẵn trang chat). Gộp mọi điểm click (composer, chip, gợi ý, FAQ, chủ đề sidebar) qua một hàm `askQuestion()` duy nhất. FAQ từ 4 câu hỏi tĩnh chuyển thành nút "Hỏi agent câu này" gọi API thật.
- **Ưu tiên nguồn VinUni chính thức**: `Tailieutubtc/TaiLieuTongHop.md` có link chính thức → dùng đúng URL đó thay vì đường dẫn file local. `WebSearchService` thêm cơ chế fetch riêng trang này qua Firecrawl (`scrape`), luôn xếp trước kết quả tìm kiếm chung, cache trong phiên.
- Verify bằng Playwright thật (cài Chromium headless): đếm đúng số bubble qua từng bước (2→4→6→8), không lỗi console.

## 6. Format câu trả lời (Markdown-lite) + citation thành chip bấm được

- Agent trả lời có `**bold**`, danh sách, `[Tên nguồn]` nhưng frontend chỉ escape thô → hiện nguyên dấu `**` và ngoặc vuông.
- Viết `formatAgentText()`/`formatInline()` tự chủ (không thêm thư viện ngoài): escape trước, sau đó parse bold/đoạn văn/danh sách/citation → citation thành `<span class="citation">` bấm mở panel nguồn.
- Thêm CSS cho `.citation`, `ul/li`, khoảng cách đoạn văn. Chỉnh prompt Gemini (`synthesis.py`) để không dùng heading/bảng/code block ngoài khả năng của formatter.

## 7. Sửa link citation không dẫn tới đâu cả

- Vấn đề: bấm citation không tới được tài liệu — nguồn local dùng đường dẫn file máy (vô dụng trên trình duyệt), nguồn ngoài thì citation chỉ mở panel chứ không phải link thật.
- **`server.py`**: thêm route `/docs/<file>.md` phục vụ nội dung tài liệu local (chặn path traversal).
- **`knowledge_base.py`**: tài liệu local không có "Link chính thức" giờ trỏ về `/docs/<file>.md`.
- **`app.js`**: citation giờ là `<a href>` thật, khớp tên nguồn với danh sách `sources` trả về từ API (có fallback substring); lưu kèm `sources` theo từng message để lịch sử cũ vẫn bấm được sau khi tải lại trang.
- **Bug nghiêm trọng phát hiện khi test**: gọi Firecrawl không có timeout thật sự → một câu hỏi khiến request **treo vô thời hạn**. Sửa bằng cách bọc mọi lời gọi Firecrawl trong deadline cứng phía client (`ThreadPoolExecutor` + `future.result(timeout=10s)`), đảm bảo request không bao giờ treo quá ~10-20s dù mạng/API có vấn đề gì.
- Verify bằng Playwright: bấm citation nội bộ → mở đúng `/docs/...` hiện nội dung thật; bấm citation ngoài → điều hướng đúng domain `vinuni.edu.vn`.

## Trạng thái cuối phiên

- Unit tests: 7/7 · `eval/test_admissions_system.py`: 6/6 · Golden set: 20/20 (100%) · Dashboard 50 case (`scripts/run_use_case_dashboard.py`): 50/50 cả fallback lẫn Gemini thật.
- Chưa commit gì trong toàn bộ phiên này — mọi thay đổi vẫn ở working tree, cần review/commit khi sẵn sàng.
- Việc còn để ngỏ: `requirements.txt` vẫn liệt kê `semantic-chunkers` (không cài được trên Python 3.14, đã có comment giải thích) — nên báo lại cho đồng đội `tanh`.
