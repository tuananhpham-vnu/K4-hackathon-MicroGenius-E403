"""Backward-compatible facade for the refactored MAS package."""

import json
import sys

from admissions_mas.domain.models import Evidence, Source
from admissions_mas.infrastructure.text import now_iso, stable_id, tokens
from admissions_mas.presentation.ui import html_page
from admissions_mas.prompts.xml_prompt import XmlPrompt
from admissions_mas.retrieval.knowledge_base import KnowledgeBase
from admissions_mas.services.workflow import AdmissionsWorkflow, create_workflow

__all__ = ["AdmissionsWorkflow", "Evidence", "KnowledgeBase", "Source", "XmlPrompt", "create_workflow", "html_page"]


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(json.dumps(create_workflow().answer("Điều kiện tham gia chương trình AI là gì?"), ensure_ascii=False, indent=2))
