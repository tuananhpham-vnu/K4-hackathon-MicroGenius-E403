# Traceable Admissions MAS

Prototype được triển khai theo `docs/framework_plan_techstack.md` với LangGraph làm agent orchestration layer.

## Môi trường

```powershell
python -m venv venv
.\venv\Scripts\activate #window
pip install -r requirements.txt
```


## Chạy web app

```powershell
pip install -r requirements.txt
python src/server.py
```

Mở `http://127.0.0.1:8765`.

API `POST /api/query` nhận JSON gồm `query`, `context`, `history`, `profile`, `request_id`. Kết quả trả về `response`, `evidence`, `sources`, `validation`, `orchestration` và `prompt_xml`. API `GET /api/audit` trả audit trail của các agent trong tiến trình hiện tại.

Mỗi request được trace thành JSONL tại `logs/mas.jsonl`. Có thể xem trace trong runtime bằng `GET /api/logs`. Console cũng in từng bước theo format `[MAS] step | component | request_id`. Có thể đổi file log bằng biến môi trường `MAS_LOG_FILE`.

## Chạy kiểm thử

```powershell
python -m unittest discover -s tests -v
```

Knowledge base hiện đọc transcript và chatlog local trong `data/vlearn-pack`; mỗi evidence giữ `source_id`, đường dẫn nguồn, locator, quote, relevance score và source trust score. Graph gồm các node Orchestrator, Analyst, Searcher, Validator, HITL Gate và Synthesis; Validator có conditional edge retry một lần khi evidence chưa đạt ngưỡng. Prompt được tách thành `system_prompt` và `user_prompt`; user prompt chứa XML envelope để trace request, history, profile và source.

Agent Harness nằm ở `src/mas/harness.py`. Harness quyết định `allowed_tools`, `memory_scopes`, `guardrails` và `reasoning_mode` cho từng agent. LLM không được tự gọi tool; mọi tool call phải đi qua `AgentHarness.invoke_tool()` và được audit.
