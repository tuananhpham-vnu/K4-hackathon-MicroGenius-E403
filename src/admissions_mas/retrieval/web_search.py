"""Optional Firecrawl web discovery tool for the Searcher agent."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from ..domain.models import Evidence, Source
from ..infrastructure.text import stable_id, tokens


class WebSearchService:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.api_key = os.getenv("FIRECRAWL_API_KEY", "")
        self.allowed_domains = {item.strip().lower() for item in os.getenv("WEB_ALLOWED_DOMAINS", "").split(",") if item.strip()}

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 5) -> list[Evidence]:
        if not self.available:
            return []
        try:
            from firecrawl import Firecrawl
            client = Firecrawl(api_key=self.api_key, api_url=os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev"))
            result = client.search(query, sources=["web"], limit=limit)
        except Exception:
            return []

        evidence: list[Evidence] = []
        for index, item in enumerate(getattr(result, "web", None) or [], 1):
            url = str(getattr(item, "url", "") or "")
            if not url:
                continue
            title = str(getattr(item, "title", "") or url)
            snippet = str(getattr(item, "description", "") or getattr(item, "snippet", "") or title)
            domain = urlparse(url).netloc.lower().removeprefix("www.")
            approved = domain in self.allowed_domains or any(domain.endswith("." + allowed) for allowed in self.allowed_domains)
            source_id = stable_id("src_web", url)
            source = Source(source_id, title, url, "official_website" if approved else "web_search_result", 0.82 if approved else 0.45, "approved_external" if approved else "external_unverified")
            self.knowledge_base.sources[source_id] = source
            query_terms = tokens(query)
            overlap = len(query_terms & tokens(snippet))
            relevance = min(1.0, 0.35 + overlap / max(1, len(query_terms)) * 0.65)
            evidence.append(Evidence(
                evidence_id=f"web_ev_{index:03d}_{source_id[-8:]}", source_id=source_id,
                quote=snippet[:2000], locator=url, relevance_score=round(relevance, 3),
                source_trust_score=source.trust_score, query=query,
                retrieval_method="firecrawl_search", source_check_passed=approved,
                source_title=source.title, source_uri=source.uri,
            ))
        return evidence
