import csv
import hashlib
import json
import re
from pathlib import Path

from ..domain.models import Evidence, Source
from ..infrastructure.text import stable_id, tokens
from .semantic_retriever import SemanticRetriever

# Source markdown puts one sentence/list-item per paragraph (e.g. each numbered
# admission criterion on its own line), so a naive per-sentence split yields
# fragments too small to carry enough of a query's keywords to rank well.
# Both the semantic_chunkers path and the fallback merge consecutive small
# fragments up to this target size so a full criterion/section stays together.
MIN_CHUNK_CHARS = 420

# Local docs that were copied from an official web page often say so ("Link
# chính thức: https://..."). When present, cite that real URL instead of the
# local file path so "mở nguồn" in the UI actually opens something.
OFFICIAL_LINK_PATTERN = re.compile(r"link chính thức\s*:\s*(https?://\S+)", re.IGNORECASE)

_chunker = None
_chunker_unavailable = False


def _get_semantic_chunker():
    """Lazily instantiate semantic_chunkers.RegexChunker.

    semantic_chunkers currently only supports Python <3.14, so this must not
    be a hard import-time dependency: on a newer interpreter (or if the
    package is simply missing) indexing has to keep working via the local
    fallback below instead of crashing the whole app at import time.
    """
    global _chunker, _chunker_unavailable
    if _chunker_unavailable:
        return None
    if _chunker is None:
        try:
            from semantic_chunkers import RegexChunker
            _chunker = RegexChunker()
        except Exception:
            _chunker_unavailable = True
            return None
    return _chunker


def regex_chunks(text: str, *, min_chars: int = 40, max_chars: int = 2500) -> list[str]:
    """Split documents into retrievable chunks for RAG indexing."""
    chunker = _get_semantic_chunker()
    if chunker is not None:
        try:
            chunks = _chunks_from_semantic_chunkers(chunker, text, min_chars=min_chars, max_chars=max_chars)
            if chunks:
                return chunks
        except Exception:
            pass
    return _fallback_chunks(text, min_chars=min_chars, max_chars=max_chars)


def _chunks_from_semantic_chunkers(chunker, text: str, *, min_chars: int, max_chars: int) -> list[str]:
    raw_chunks = chunker([text])
    chunks: list[str] = []
    for chunk in _flatten_chunks(raw_chunks):
        splits = getattr(chunk, "splits", None)
        raw_text = " ".join(splits) if splits else str(chunk)
        clean = re.sub(r"\s+", " ", raw_text).strip()
        if len(clean) > min_chars:
            chunks.append(clean[:max_chars])
    return chunks


def _fallback_chunks(text: str, *, min_chars: int, max_chars: int) -> list[str]:
    """Paragraph/sentence split with small-fragment merging (no external chunker needed)."""
    pieces = re.split(r"\n\s*\n|(?<=[.!?])\s+(?=[A-ZÀ-ỴĐ])", text)
    chunks: list[str] = []
    buffer_parts: list[str] = []
    for piece in pieces:
        if not piece.strip():
            continue
        buffer_parts.append(piece)
        if sum(len(part) for part in buffer_parts) >= MIN_CHUNK_CHARS:
            _flush_chunk(buffer_parts, chunks, min_chars, max_chars)
            buffer_parts = []
    if buffer_parts:
        _flush_chunk(buffer_parts, chunks, min_chars, max_chars)
    return chunks


def _flush_chunk(parts: list[str], chunks: list[str], min_chars: int, max_chars: int) -> None:
    clean = re.sub(r"\s+", " ", "\n\n".join(parts)).strip()
    if len(clean) > min_chars:
        chunks.append(clean[:max_chars])


def _flatten_chunks(items):
    for item in items:
        if isinstance(item, list):
            yield from _flatten_chunks(item)
        else:
            yield item


class KnowledgeBase:
    """Indexes local documents while preserving source metadata per chunk."""

    def __init__(self, repo_root: Path):
        self.repo_root = repo_root
        self.sources: dict[str, Source] = {}
        self.documents: list[dict[str, str]] = []
        self._load()
        self.semantic = SemanticRetriever(self)

    def _register(self, title: str, path: Path, source_type: str, trust: float, uri: str | None = None) -> Source:
        source = Source(stable_id("src", str(path.resolve())), title, uri or str(path), source_type, trust)
        self.sources[source.source_id] = source
        return source

    def _document(self, source: Source, locator: str, text: str) -> dict[str, str]:
        return {
            "source_id": source.source_id,
            "locator": locator,
            "text": text[:2500],
            "source_title": source.title,
            "source_uri": source.uri,
        }

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
                        locator = f"{row.get('conversation_id', 'conversation')}/{row.get('message_id', 'message')}"
                        self.documents.append(self._document(source, locator, re.sub(r"\s+", " ", content)))

        # The current repository stores the approved admissions corpus here.
        # Keeping this discovery explicit prevents a silently empty knowledge base.
        for path in sorted((self.repo_root / "Tailieutubtc").glob("*.md")):
            text = path.read_text(encoding="utf-8")
            link_match = OFFICIAL_LINK_PATTERN.search(text)
            # A local absolute path (e.g. /home/user/.../file.md) can never be
            # opened from a browser — neither on a demo machine nor, worse, a
            # deployed one. server.py serves this same folder at /docs/<name>,
            # so "mở nguồn" always resolves to something a user can actually click.
            uri = link_match.group(1) if link_match else f"/docs/{path.name}"
            source = self._register(path.stem, path, "official_admissions_document", 0.92, uri=uri)
            self._index_markdown(path, source)

        for path in sorted((self.repo_root / "data").glob("*.json")):
            self._index_community_json(path)

    def _index_markdown(self, path: Path, source: Source) -> None:
        for index, clean in enumerate(regex_chunks(path.read_text(encoding="utf-8")), 1):
            marker = re.search(r"\[(T\d+-\d+)\]", clean)
            locator = marker.group(1) if marker else f"paragraph-{index}"
            self.documents.append(self._document(source, locator, clean))

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
                self.documents.append(self._document(source, f"post-{index}", re.sub(r"\s+", " ", text)))

    def search(self, query: str, limit: int = 8) -> list[Evidence]:
        if self.semantic.configured:
            try:
                hybrid_results = self.semantic.search(query, limit=limit)
                if hybrid_results:
                    return hybrid_results
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
                source_id=source.source_id,
                quote=document["text"],
                locator=document["locator"],
                relevance_score=round(score, 3),
                source_trust_score=source.trust_score,
                query=query,
                source_check_passed=source.authority == "approved_local" and source.trust_score >= 0.7,
                source_title=source.title,
                source_uri=source.uri,
            ))
            if len(results) >= limit:
                break
        return results

    def index_semantic_documents(self) -> int:
        """Embed and upsert the current regex-chunked corpus into Weaviate."""
        return self.semantic.index(self.documents)
