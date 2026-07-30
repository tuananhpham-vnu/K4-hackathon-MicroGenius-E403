"""Structured runtime tracing for MAS requests."""

from __future__ import annotations

import json
import os
from pathlib import Path
from threading import Lock
from typing import Any

from ..infrastructure.text import now_iso


class TraceLogger:
    """Writes one JSON object per event to console and a JSONL file."""

    def __init__(self, log_path: Path | None = None, console: bool = True):
        configured_path = os.getenv("MAS_LOG_FILE")
        if configured_path:
            # dotenv interprets sequences such as ``\r`` in Windows paths.
            # Normalize escaped/control separators before constructing Path.
            configured_path = configured_path.replace("\r", "/").replace("\n", "/").replace("\\", "/")
        self.log_path = Path(configured_path) if configured_path else (log_path or Path("logs") / "mas.jsonl")
        self.console = console
        self._lock = Lock()

    def event(self, *, request_id: str, step: str, component: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        record = {"timestamp": now_iso(), "request_id": request_id, "step": step, "component": component, "payload": payload or {}}
        line = json.dumps(record, ensure_ascii=False, default=str)
        with self._lock:
            self.log_path.parent.mkdir(parents=True, exist_ok=True)
            with self.log_path.open("a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        if self.console:
            print(f"[MAS] {record['step']} | {record['component']} | {request_id}")
        return record

    def read(self) -> list[dict[str, Any]]:
        if not self.log_path.exists():
            return []
        return [json.loads(line) for line in self.log_path.read_text(encoding="utf-8").splitlines() if line.strip()]
