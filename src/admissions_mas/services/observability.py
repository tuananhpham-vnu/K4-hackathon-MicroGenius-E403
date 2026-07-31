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
        # An explicit dependency-injected path must win in tests/evaluation.
        self.log_path = log_path or (Path(configured_path) if configured_path else Path("logs") / "mas.jsonl")
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
        records = []
        # A process can be interrupted midway through its final append. Keep
        # earlier valid trace records usable instead of failing the whole API.
        with self._lock:
            lines = self.log_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line in lines:
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(record, dict):
                records.append(record)
        return records
