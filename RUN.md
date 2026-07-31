# Traceable Admissions MAS

Prototype được triển khai theo `docs/framework_plan_techstack.md` với LangGraph làm agent orchestration layer.

## Cấu trúc mã nguồn

```text
src/
├── server.py                       # HTTP entrypoint
├── admissions_system.py            # compatibility facade
└── admissions_mas/
    ├── agents/                     # LangGraph graph và Agent Harness
    ├── domain/                     # domain models: Source, Evidence
    ├── infrastructure/             # text/id helpers
    ├── prompts/                    # XML prompt và prompt registry
    ├── retrieval/                  # local KB, embeddings, Weaviate, web search
    ├── services/                   # workflow và observability
    └── presentation/               # backend-served UI helper
frontend/                           # HTML/CSS/JS client
scripts/                            # indexing và vận hành
tests/                              # unit tests
```

Convention: Python module/file dùng `snake_case`, class dùng `PascalCase`, constant dùng `UPPER_SNAKE_CASE`, package dùng tên ngắn lowercase.

## Môi trường

```powershell
python -m venv venv
.\venv\Scripts\activate #window
pip install -r requirements.txt
```


## Chạy web app

```powershell
python scripts/upload_weaviate_documents.py # upload tài liệu
python src/server.py
```

Mở `http://127.0.0.1:8765`.

Nếu chạy FE riêng bằng Live Server/Vite, mở `frontend/index.html` qua frontend dev server; FE tự gọi backend `http://127.0.0.1:8765` và backend đã bật CORS. Nếu dùng domain khác, đặt `window.__API_BASE__` trước `app.js`.

API `POST /api/query` nhận JSON gồm `query`, `context`, `history`, `profile`, `request_id`. Kết quả trả về `response`, `evidence`, `sources`, `validation`, `orchestration` và `prompt_xml`. API `GET /api/audit` trả audit trail của các agent trong tiến trình hiện tại.

Mỗi request được trace thành JSONL tại `logs/mas.jsonl`. Có thể xem trace trong runtime bằng `GET /api/logs`. Console cũng in từng bước theo format `[MAS] step | component | request_id`. Có thể đổi file log bằng biến môi trường `MAS_LOG_FILE`.

Synthesis dùng Gemini nếu có API key; nếu thiếu key hoặc Gemini lỗi, hệ thống tự fallback sang câu trả lời grounded theo evidence:

```powershell
$env:GEMINI_API_KEY="..."
$env:GEMINI_MODEL_NAME="gemini-3.5-flash-lite"
python src/server.py
```

Web search dùng Firecrawl và được gọi qua `AgentHarness` bằng tool `web.search`. Cấu hình trước khi chạy:

```powershell
$env:FIRECRAWL_API_KEY="fc-..."
$env:WEB_ALLOWED_DOMAINS="vinai.io,vinuni.edu.vn"
python src/server.py
```

Nếu chưa có `FIRECRAWL_API_KEY`, hệ thống vẫn chạy local retrieval; health endpoint sẽ báo `web_search_available: false`. Web result ngoài allowlist chỉ là candidate evidence và không được Validator dùng làm nguồn chính thức.

Hybrid retrieval với Weaviate:

```powershell
python scripts/index_documents.py
python src/server.py
```

Script đọc tài liệu trong `Tailieutubtc/`, chunk bằng regex, encode bằng `EMBEDDING_MODEL_NAME` và upsert vector vào collection `WEAVIATE_COLLECTION`. Khi query, Searcher dùng Weaviate `hybrid` search: BM25 query + embedding vector, không dùng reranker model. Khi collection chưa có dữ liệu hoặc cloud/model lỗi, Searcher tự fallback về local lexical retrieval.

Upload thêm tài liệu RAG vào Weaviate:

```powershell
python scripts/upload_weaviate_documents.py --path .\Tailieutubtc
python scripts/upload_weaviate_documents.py --path .\docs\new-info.md --title "Tên tài liệu" --source-uri "https://example.com/source"
python src/server.py
```

Mỗi chunk upload giữ `source_id`, `source_title`, `source_uri`, `locator`, `trust_score` và `text`. Vì vậy kết quả RAG luôn kèm tên tài liệu; kết quả web luôn kèm URL/source.

Web search dùng Firecrawl và được gọi qua `AgentHarness` bằng tool `web.search`. Cấu hình trước khi chạy:

```powershell
$env:FIRECRAWL_API_KEY="fc-..."
$env:WEB_ALLOWED_DOMAINS="vinai.io,vinuni.edu.vn"
python src/server.py
```

Nếu chưa có `FIRECRAWL_API_KEY`, hệ thống vẫn chạy local retrieval; health endpoint sẽ báo `web_search_available: false`. Web result ngoài allowlist chỉ là candidate evidence và không được Validator dùng làm nguồn chính thức.

## Chạy kiểm thử

```powershell
python -m unittest discover -s tests -v
```

Chạy bộ use case trong `data/test.json` và xuất dashboard:

```powershell
python scripts/run_use_case_dashboard.py --disable-gemini # mock test, không dùng model gen final response
python scripts/run_use_case_dashboard.py # 
```

Kết quả được in ra console và lưu tại `eval/use_case_dashboard/results.json` cùng `eval/use_case_dashboard/dashboard.html`. Bỏ `--disable-gemini` nếu muốn chấm với synthesis Gemini thật.

Knowledge base hiện đọc transcript và chatlog local trong `data/vlearn-pack`; mỗi evidence giữ `source_id`, đường dẫn nguồn, locator, quote, relevance score và source trust score. Graph gồm các node Orchestrator, Analyst, Searcher, Validator, HITL Gate và Synthesis; Validator có conditional edge retry một lần khi evidence chưa đạt ngưỡng. Prompt được tách thành `system_prompt` và `user_prompt`; user prompt chứa XML envelope để trace request, history, profile và source.

Agent Harness nằm ở `src/admissions_mas/agents/harness.py`. Harness quyết định `allowed_tools`, `memory_scopes`, `guardrails` và `reasoning_mode` cho từng agent. LLM không được tự gọi tool; mọi tool call phải đi qua `AgentHarness.invoke_tool()` và được audit.
