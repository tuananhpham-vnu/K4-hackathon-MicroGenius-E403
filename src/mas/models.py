from dataclasses import dataclass, field

from .utils import now_iso


@dataclass
class Source:
    source_id: str
    title: str
    uri: str
    source_type: str
    trust_score: float
    authority: str = "approved_local"
    captured_at: str = field(default_factory=now_iso)


@dataclass
class Evidence:
    evidence_id: str
    source_id: str
    quote: str
    locator: str
    relevance_score: float
    source_trust_score: float
    query: str
    retrieval_method: str = "lexical_overlap"
    source_check_passed: bool = False
