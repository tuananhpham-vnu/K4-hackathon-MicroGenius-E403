"""Minimal HTTP API for the traceable admissions workflow."""

import html
import json
import mimetypes
import os
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
DOCS_ROOT = (Path(__file__).resolve().parents[1] / "Tailieutubtc").resolve()


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

    def _serve_doc(self, name: str) -> None:
        # Backs the citation/"mở nguồn" links for local admissions docs (see
        # knowledge_base.py's Source.uri) so they resolve to a real, clickable
        # page instead of a local filesystem path the browser can't open.
        candidate = (DOCS_ROOT / name).resolve()
        if DOCS_ROOT not in candidate.parents or candidate.suffix != ".md" or not candidate.is_file():
            self._send("Not found", 404, "text/plain; charset=utf-8")
            return
        body = (
            "<!doctype html><meta charset='utf-8'>"
            f"<title>{html.escape(candidate.stem)}</title>"
            "<body style=\"max-width:820px;margin:40px auto;padding:0 20px;"
            "font:16px/1.65 system-ui,sans-serif;white-space:pre-wrap\">"
            f"{html.escape(candidate.read_text(encoding='utf-8'))}"
            "</body>"
        )
        self._send(body, content_type="text/html; charset=utf-8")

    def do_GET(self) -> None:
        request_path = urlparse(self.path).path
        if request_path == "/api/health":
            self._send(json.dumps({"status": "ok", "sources": len(WORKFLOW.kb.sources), "documents": len(WORKFLOW.kb.documents), "langgraph_available": bool(MAS), "web_search_available": bool(MAS and MAS.web_search.available)}), content_type="application/json")
        elif request_path == "/api/audit":
            if not EXPOSE_TRACE_API:
                self._send("Not found", 404, "text/plain; charset=utf-8")
                return
            self._send(json.dumps(WORKFLOW.audit_log, ensure_ascii=False), content_type="application/json")
        elif request_path == "/api/logs":
            if not EXPOSE_TRACE_API:
                self._send("Not found", 404, "text/plain; charset=utf-8")
                return
            self._send(json.dumps(WORKFLOW.logger.read(), ensure_ascii=False), content_type="application/json")
        elif request_path.startswith("/docs/"):
            self._serve_doc(request_path.removeprefix("/docs/"))
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
        if self.path != "/api/query":
            self._send("Not found", 404, "text/plain; charset=utf-8")
            return
        request_id = "unknown"
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            query = str(payload.get("query", "")).strip()
            if not query:
                raise ValueError("query is required")
            request_id = payload.get("request_id") or "req_http"
            if MAS:
                state = MAS.invoke(query, request_id=request_id, context=payload.get("context"), history=payload.get("history"), profile=payload.get("profile"))
            else:
                state = WORKFLOW.answer(query, request_id=request_id, context=payload.get("context"), history=payload.get("history"), profile=payload.get("profile"))
            result = {"request_id": state["request_id"], "response": state.get("response", ""), "evidence": state.get("evidence", []), "validation": state.get("validation", {}), "orchestration": state.get("orchestration", {}), "prompt_xml": state.get("prompt_xml", ""), "system_prompt": state.get("system_prompt", ""), "user_prompt": state.get("user_prompt", ""), "sources": [WORKFLOW.kb.sources[item["source_id"]].__dict__ for item in state.get("evidence", [])]}
            self._send(json.dumps(result, ensure_ascii=False), content_type="application/json")
        except (ValueError, json.JSONDecodeError) as error:
            self._send(json.dumps({"error": str(error)}), 400, "application/json")
        except Exception as error:
            WORKFLOW.logger.event(request_id=request_id, step="request_error", component="server", payload={"error_type": type(error).__name__, "error": str(error)})
            self._send(json.dumps({"error": "Agent request failed", "request_id": request_id, "detail": str(error)}, ensure_ascii=False), 500, "application/json")


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8765"))
    print(f"Traceable Admissions MAS: http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
