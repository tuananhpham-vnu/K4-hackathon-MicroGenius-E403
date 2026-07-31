"""Upload regex-chunked admissions documents into Weaviate hybrid-search storage."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))
load_dotenv(REPO_ROOT / ".env", override=True)

from admissions_mas.domain.models import Source  # noqa: E402
from admissions_mas.infrastructure.text import stable_id  # noqa: E402
from admissions_mas.retrieval.knowledge_base import regex_chunks  # noqa: E402
from admissions_mas.services.workflow import create_workflow  # noqa: E402


def iter_markdown_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(item for item in path.rglob("*") if item.is_file() and item.suffix.lower() in {".md", ".txt"})


def add_upload_documents(workflow, path: Path, title: str, source_uri: str, source_type: str, trust_score: float) -> int:
    files = iter_markdown_files(path)
    for file_path in files:
        uri = source_uri or str(file_path)
        source_title = title or file_path.stem
        source = Source(
            source_id=stable_id("src_upload", f"{uri}:{source_title}"),
            title=source_title,
            uri=uri,
            source_type=source_type,
            trust_score=trust_score,
            authority="approved_local",
        )
        workflow.kb.sources[source.source_id] = source
        for index, chunk in enumerate(regex_chunks(file_path.read_text(encoding="utf-8")), 1):
            workflow.kb.documents.append({
                "source_id": source.source_id,
                "source_title": source.title,
                "source_uri": source.uri,
                "locator": f"{file_path.name}#chunk-{index}",
                "text": chunk,
            })
    return len(files)


def main() -> int:
    parser = argparse.ArgumentParser(description="Upload regex chunks to Weaviate for hybrid_search retrieval.")
    parser.add_argument("--path", type=Path, help="Optional .md/.txt file or directory to upload. Default uploads the repo corpus.")
    parser.add_argument("--title", default="", help="Source title for a single uploaded file.")
    parser.add_argument("--source-uri", default="", help="Original URL/link for the uploaded source.")
    parser.add_argument("--source-type", default="official_admissions_document")
    parser.add_argument("--trust-score", type=float, default=0.92)
    args = parser.parse_args()

    workflow = create_workflow(REPO_ROOT)
    if not workflow.kb.semantic.configured:
        raise SystemExit("WEAVIATE_URL and WEAVIATE_API_KEY are required")
    if args.path:
        uploaded_files = add_upload_documents(
            workflow,
            args.path.resolve(),
            args.title,
            args.source_uri,
            args.source_type,
            args.trust_score,
        )
        print(f"Prepared {uploaded_files} uploaded file(s)")
    count = workflow.kb.index_semantic_documents()
    print(f"Uploaded {count} regex chunks to {workflow.kb.semantic.collection_name} using hybrid_search embeddings")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
