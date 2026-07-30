"""Minimal HTTP API for the traceable admissions workflow."""

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from mas.workflow import create_workflow

try:
    from langgraph_mas import LangGraphAdmissionsMAS
except ModuleNotFoundError:
    LangGraphAdmissionsMAS = None


WORKFLOW = create_workflow(Path(__file__).resolve().parents[1])
MAS = LangGraphAdmissionsMAS(WORKFLOW) if LangGraphAdmissionsMAS else None
WEB_ROOT = Path(__file__).resolve().parents[1] / "codebase"


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        request_path = urlparse(self.path).path
        if request_path == "/api/health":
            self._send(json.dumps({"status": "ok", "sources": len(WORKFLOW.kb.sources), "documents": len(WORKFLOW.kb.documents)}), content_type="application/json")
        elif request_path == "/api/audit":
            self._send(json.dumps(WORKFLOW.audit_log, ensure_ascii=False), content_type="application/json")
        elif request_path == "/api/logs":
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
        if self.path != "/api/query":
            self._send("Not found", 404, "text/plain; charset=utf-8")
            return
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


if __name__ == "__main__":
    print("Traceable Admissions MAS: http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
