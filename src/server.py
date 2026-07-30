"""Minimal HTTP API for the traceable admissions workflow."""

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from langgraph_mas import LangGraphAdmissionsMAS
from mas.ui import html_page
from mas.workflow import create_workflow


WORKFLOW = create_workflow(Path(__file__).resolve().parents[1])
MAS = LangGraphAdmissionsMAS(WORKFLOW)


class Handler(BaseHTTPRequestHandler):
    def _send(self, body: str, status: int = 200, content_type: str = "text/html; charset=utf-8") -> None:
        encoded = body.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_GET(self) -> None:
        if self.path == "/" or self.path.startswith("/?"):
            self._send(html_page())
        elif self.path == "/api/health":
            self._send(json.dumps({"status": "ok", "sources": len(WORKFLOW.kb.sources), "documents": len(WORKFLOW.kb.documents)}), content_type="application/json")
        elif self.path == "/api/audit":
            self._send(json.dumps(WORKFLOW.audit_log, ensure_ascii=False), content_type="application/json")
        elif self.path == "/api/logs":
            self._send(json.dumps(WORKFLOW.logger.read(), ensure_ascii=False), content_type="application/json")
        else:
            self._send("Not found", 404, "text/plain; charset=utf-8")

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
            state = MAS.invoke(query, request_id=payload.get("request_id") or "req_http", context=payload.get("context"), history=payload.get("history"), profile=payload.get("profile"))
            result = {"request_id": state["request_id"], "response": state.get("response", ""), "evidence": state.get("evidence", []), "validation": state.get("validation", {}), "orchestration": state.get("orchestration", {}), "prompt_xml": state.get("prompt_xml", ""), "system_prompt": state.get("system_prompt", ""), "user_prompt": state.get("user_prompt", ""), "sources": [WORKFLOW.kb.sources[item["source_id"]].__dict__ for item in state.get("evidence", [])]}
            self._send(json.dumps(result, ensure_ascii=False), content_type="application/json")
        except (ValueError, json.JSONDecodeError) as error:
            self._send(json.dumps({"error": str(error)}), 400, "application/json")


if __name__ == "__main__":
    print("Traceable Admissions MAS: http://127.0.0.1:8765")
    ThreadingHTTPServer(("127.0.0.1", 8765), Handler).serve_forever()
