"""Index Tailieutubtc regex chunks into Weaviate Cloud."""

import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
load_dotenv(REPO_ROOT / ".env")

from admissions_mas.services.workflow import create_workflow  # noqa: E402


if __name__ == "__main__":
    workflow = create_workflow(REPO_ROOT)
    if not workflow.kb.semantic.configured:
        raise SystemExit("WEAVIATE_URL and WEAVIATE_API_KEY are required")
    count = workflow.kb.index_semantic_documents()
    print(f"Indexed {count} chunks with {workflow.kb.semantic.model_name}")
