"""Backward-compatible facade for the refactored MAS package."""

import json
import sys

from mas.models import Evidence, Source
from mas.prompts import XmlPrompt
from mas.retrieval import KnowledgeBase
from mas.ui import html_page
from mas.utils import now_iso, stable_id, tokens
from mas.workflow import AdmissionsWorkflow, create_workflow

__all__ = ["AdmissionsWorkflow", "Evidence", "KnowledgeBase", "Source", "XmlPrompt", "create_workflow", "html_page"]


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(create_workflow().answer("Điều kiện tham gia chương trình AI là gì?"), ensure_ascii=False, indent=2))
