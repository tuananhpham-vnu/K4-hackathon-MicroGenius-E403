import csv
import hashlib
import json
import re
from pathlib import Path

from ..domain.models import Evidence, Source
from ..infrastructure.text import stable_id, tokens
from .semantic_retriever import SemanticRetriever


class KnowledgeBase:
    """Indexes local documents while preserving source metadata per chunk."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.sources: dict[str, Source] = {}
        self.documents: list[dict[str, str]] = []
        self._load()
        self.semantic = SemanticRetriever(self)

    def _register(self, title: str, path: Path, source_type: str, trust: float) -> Source:
        source = Source(stable_id("src", str(path.resolve())), title, str(path), source_type, trust)
        self.sources[source.source_id] = source
        return source

    def _load(self) -> None:
        legacy_root = self.repo_root / "data" / "vlearn-pack"
        for path in sorted((legacy_root / "transcript").glob("*.md")):
            source = self._register(path.stem, path, "official_training_transcript", 0.86)
            self._index_markdown(path, source)

        csv_path = legacy_root / "chatlog" / "chat_history_anonymized_for_hackathon.csv"
        if csv_path.exists():
            source = self._register(csv_path.stem, csv_path, "anonymized_chatlog", 0.72)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    content = (row.get("content") or "").strip()
                    if len(content) > 25:
                        self.documents.append({"source_id": source.source_id, "locator": f"{row.get('conversation_id', 'conversation')}/{row.get('message_id', 'message')}", "text": re.sub(r"\s+", " ", content)[:2500]})

        # The current repository stores the approved admissions corpus here.
        # Keeping this discovery explicit prevents a silently empty knowledge base.
        for path in sorted((self.repo_root / "Tailieutubtc").glob("*.md")):
            source = self._register(path.stem, path, "official_admissions_document", 0.92)
            self._index_markdown(path, source)

        for path in sorted((self.repo_root / "data").glob("*.json")):
            self._index_community_json(path)

    def _index_markdown(self, path: Path, source: Source) -> None:
        chunks = re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-ZÀ-ỴĐ])", path.read_text(encoding="utf-8"))
        for index, chunk in enumerate(chunks, 1):
            clean = re.sub(r"\s+", " ", chunk).strip()
            if len(clean) <= 40:
                continue
            marker = re.search(r"\[(T\d+-\d+)\]", chunk)
            self.documents.append({
                "source_id": source.source_id,
                "locator": marker.group(1) if marker else f"paragraph-{index}",
                "text": clean[:2500],
            })

    def _index_community_json(self, path: Path) -> None:
        try:
            records = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return
        if not isinstance(records, list):
            return
        source = self._register(path.stem, path, "community_observation", 0.62)
        for index, record in enumerate(records, 1):
            if not isinstance(record, dict):
                continue
            text = str(record.get("text") or "").strip()
            if len(text) > 25:
                self.documents.append({
                    "source_id": source.source_id,
                    "locator": f"post-{index}",
                    "text": re.sub(r"\s+", " ", text)[:2500],
                })

    def search(self, query: str, limit: int = 8) -> list[Evidence]:
        if self.semantic.configured:
            try:
                semantic_results = self.semantic.search(query, limit=limit)
                if semantic_results:
                    return semantic_results
            except Exception:
                # Cloud/model failures must not take down the local fallback.
                pass
        query_tokens = tokens(query)
        ranked: list[tuple[float, dict[str, str]]] = []
        for document in self.documents:
            overlap = query_tokens & tokens(document["text"])
            if not overlap:
                continue
            phrase_bonus = 0.12 if query.lower() in document["text"].lower() else 0
            score = min(1.0, len(overlap) / max(1, len(query_tokens)) * 0.88 + phrase_bonus)
            ranked.append((score, document))
        ranked.sort(key=lambda item: item[0], reverse=True)
        results = []
        seen_text: set[str] = set()
        for score, document in ranked:
            fingerprint = hashlib.sha1(document["text"].casefold().encode()).hexdigest()
            if fingerprint in seen_text:
                continue
            seen_text.add(fingerprint)
            source = self.sources[document["source_id"]]
            key = f"{source.source_id}:{document['locator']}:{query}"
            results.append(Evidence(
                evidence_id=f"ev_{len(results) + 1:03d}_{hashlib.sha1(key.encode()).hexdigest()[:8]}",
                source_id=source.source_id, quote=document["text"], locator=document["locator"],
                relevance_score=round(score, 3), source_trust_score=source.trust_score,
                query=query, source_check_passed=source.authority == "approved_local" and source.trust_score >= 0.7,
            ))
            if len(results) >= limit:
                break
        return results

    def index_semantic_documents(self) -> int:
        """Embed and upsert the current regex-chunked corpus into Weaviate."""
        return self.semantic.index(self.documents)
