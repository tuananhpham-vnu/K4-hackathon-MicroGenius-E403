import csv
import hashlib
import re
from pathlib import Path

from .models import Evidence, Source
from .utils import stable_id, tokens


class KnowledgeBase:
    """Indexes local documents while preserving source metadata per chunk."""

    def __init__(self, data_root: Path):
        self.data_root = data_root
        self.sources: dict[str, Source] = {}
        self.documents: list[dict[str, str]] = []
        self._load()

    def _register(self, title: str, path: Path, source_type: str, trust: float) -> Source:
        source = Source(stable_id("src", str(path.resolve())), title, str(path), source_type, trust)
        self.sources[source.source_id] = source
        return source

    def _load(self) -> None:
        for path in sorted((self.data_root / "transcript").glob("*.md")):
            source = self._register(path.stem, path, "official_training_transcript", 0.86)
            chunks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8"))
            for index, chunk in enumerate(chunks, 1):
                clean = re.sub(r"\s+", " ", chunk).strip()
                if len(clean) > 40:
                    marker = re.search(r"\[(T\d+-\d+)\]", chunk)
                    self.documents.append({"source_id": source.source_id, "locator": marker.group(1) if marker else f"paragraph-{index}", "text": clean[:2500]})

        csv_path = self.data_root / "chatlog" / "chat_history_anonymized_for_hackathon.csv"
        if csv_path.exists():
            source = self._register(csv_path.stem, csv_path, "anonymized_chatlog", 0.72)
            with csv_path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    content = (row.get("content") or "").strip()
                    if len(content) > 25:
                        self.documents.append({"source_id": source.source_id, "locator": f"{row.get('conversation_id', 'conversation')}/{row.get('message_id', 'message')}", "text": re.sub(r"\s+", " ", content)[:2500]})

    def search(self, query: str, limit: int = 8) -> list[Evidence]:
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
        for index, (score, document) in enumerate(ranked[:limit], 1):
            source = self.sources[document["source_id"]]
            key = f"{source.source_id}:{document['locator']}:{query}"
            results.append(Evidence(
                evidence_id=f"ev_{index:03d}_{hashlib.sha1(key.encode()).hexdigest()[:8]}",
                source_id=source.source_id, quote=document["text"], locator=document["locator"],
                relevance_score=round(score, 3), source_trust_score=source.trust_score,
                query=query, source_check_passed=source.authority == "approved_local" and source.trust_score >= 0.7,
            ))
        return results
