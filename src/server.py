"""Minimal HTTP API for the traceable admissions workflow."""

import json
import mimetypes
import os
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=True)

from admissions_mas.services.workflow import create_workflow

try:
    from admissions_mas.agents.graph import LangGraphAdmissionsMAS
except ModuleNotFoundError:
    LangGraphAdmissionsMAS = None

WORKFLOW = create_workflow(Path(__file__).resolve().parents[1])
MAS = LangGraphAdmissionsMAS(WORKFLOW) if LangGraphAdmissionsMAS else None
WEB_ROOT = Path(__file__).resolve().parents[1] / "frontend"
MAX_REQUEST_BYTES = 256 * 1024
EXPOSE_TRACE_API = os.getenv("EXPOSE_TRACE_API", "").lower() in {"1", "true", "yes"}


def parse_query_payload(raw: bytes) -> dict:
    """Decode and validate the small public API contract."""
    if not raw:
        raise ValueError("request body is required")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except UnicodeDecodeError as error:
        raise ValueError("request body must be UTF-8") from error
    if not isinstance(payload, dict):
        raise ValueError("request body must be a JSON object")
    query = payload.get("query")
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query is required and must be a string")
    if len(query) > 4000:
        raise ValueError("query must not exceed 4000 characters")
    for field, expected in (("context", dict), ("profile", dict), ("history", list)):
        value = payload.get(field)
        if value is not None and not isinstance(value, expected):
            raise ValueError(f"{field} must be a {expected.__name__}")
    payload["query"] = query.strip()
    return payload


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
        encoded = body.encode("utf-8")
        if content_type == "application/json":
            content_type = "application/json; charset=utf-8"
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()
        self.wfile.write(encoded)

    def do_OPTIONS(self) -> None:
        self._send("", 204, "text/plain; charset=utf-8")

    def do_GET(self) -> None:
        request_path = urlparse(self.path).path
        if request_path == "/api/health":
            self._send(json.dumps({"status": "ok", "sources": len(WORKFLOW.kb.sources), "documents": len(WORKFLOW.kb.documents), "langgraph_available": bool(MAS), "web_search_available": bool(MAS and MAS.web_search.available)}), content_type="application/json")
        elif request_path == "/api/audit" and EXPOSE_TRACE_API:
            self._send(json.dumps(WORKFLOW.audit_log, ensure_ascii=False), content_type="application/json")
        elif request_path == "/api/logs" and EXPOSE_TRACE_API:
            self._send(json.dumps(WORKFLOW.logger.read(), ensure_ascii=False), content_type="application/json")
        else:
            relative = "index.html" if request_path == "/" else request_path.lstrip("/")
            candidate = (WEB_ROOT / relative).resolve()
            if WEB_ROOT.resolve() not in candidate.parents and candidate != WEB_ROOT.resolve():
                self._send("Not found", 404, "text/plain; charset=utf-8")
                return
            if not candidate.is_file():
                self._send("Not found", 404, "text/plain; charset=utf-8")
                return
            content_type = mimetypes.guess_type(candidate.name)[0] or "application/octet-stream"
            if content_type.startswith("text/") or content_type in {"application/javascript", "application/json"}:
                content_type += "; charset=utf-8"
            body = candidate.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/query":
            self._send("Not found", 404, "text/plain; charset=utf-8")
            return
        request_id = "unknown"
        try:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError as error:
                raise ValueError("invalid Content-Length") from error
            if length > MAX_REQUEST_BYTES:
                self._send(json.dumps({"error": "request body is too large"}), 413, "application/json")
                return
            payload = parse_query_payload(self.rfile.read(length))
            query = payload["query"]
            supplied_request_id = payload.get("request_id")
            request_id = supplied_request_id.strip()[:128] if isinstance(supplied_request_id, str) and supplied_request_id.strip() else f"req_{uuid.uuid4().hex[:12]}"
            if MAS:
                state = MAS.invoke(query, request_id=request_id, context=payload.get("context"), history=payload.get("history"), profile=payload.get("profile"))
            else:
                state = WORKFLOW.answer(query, request_id=request_id, context=payload.get("context"), history=payload.get("history"), profile=payload.get("profile"))
            sources = []
            seen_source_ids = set()
            for item in state.get("evidence", []):
                source_id = item.get("source_id")
                source = WORKFLOW.kb.sources.get(source_id)
                if source and source_id not in seen_source_ids:
                    sources.append(source.__dict__)
                    seen_source_ids.add(source_id)
            result = {"request_id": state["request_id"], "response": state.get("response", ""), "evidence": state.get("evidence", []), "validation": state.get("validation", {}), "orchestration": state.get("orchestration", {}), "prompt_xml": state.get("prompt_xml", ""), "system_prompt": state.get("system_prompt", ""), "user_prompt": state.get("user_prompt", ""), "sources": sources}
            self._send(json.dumps(result, ensure_ascii=False), content_type="application/json")
        except (ValueError, json.JSONDecodeError) as error:
            self._send(json.dumps({"error": str(error)}), 400, "application/json")
        except Exception as error:
            WORKFLOW.logger.event(request_id=request_id, step="request_error", component="server", payload={"error_type": type(error).__name__, "error": str(error)})
            self._send(json.dumps({"error": "Agent request failed", "request_id": request_id, "detail": str(error)}, ensure_ascii=False), 500, "application/json")


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8765"))
    print(f"Traceable Admissions MAS listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
