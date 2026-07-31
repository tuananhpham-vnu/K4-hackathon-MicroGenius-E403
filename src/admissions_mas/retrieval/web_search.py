"""Optional Firecrawl web discovery tool for the Searcher agent."""

from __future__ import annotations

import os
from urllib.parse import urlparse

from ..domain.models import Evidence, Source
from ..infrastructure.text import stable_id, tokens

# The program's canonical admissions page (also referenced as the "Link
# chính thức" inside Tailieutubtc/TaiLieuTongHop.md). Always checked first and
# cited ahead of generic web search results so answers stay anchored to the
# one page VinUni actually publishes as authoritative.
PRIORITY_SOURCE_URL = "https://vinuni.edu.vn/vi/thong-tin-tuyen-sinh-chuong-trinh-dao-tao-nhan-tai-ai-thuc-chien-khoa-co-ban/"
PRIORITY_SOURCE_TITLE = "Thông tin tuyển sinh AI Thực Chiến (VinUni chính thức)"


class WebSearchService:
    def __init__(self, knowledge_base):
        self.knowledge_base = knowledge_base
        self.api_key = os.getenv("FIRECRAWL_API_KEY", "")
        self.allowed_domains = {item.strip().lower() for item in os.getenv("WEB_ALLOWED_DOMAINS", "").split(",") if item.strip()}
        # Cached across calls so the priority page is scraped once per process,
        # not once per query. None = not fetched yet, "" = fetch failed.
        self._priority_content: str | None = None

    @property
    def available(self) -> bool:
        return bool(self.api_key)

    def search(self, query: str, limit: int = 5) -> list[Evidence]:
        if not self.available:
            return []
        results: list[Evidence] = []
        priority = self._priority_evidence(query)
        if priority:
            results.append(priority)
        results.extend(self._general_search(query, limit=max(0, limit - len(results))))
        return results

    def _priority_evidence(self, query: str) -> Evidence | None:
        content = self._fetch_priority_content()
        if not content:
            return None
        query_terms = tokens(query)
        overlap = len(query_terms & tokens(content))
        if not overlap:
            return None
        relevance = min(1.0, 0.5 + overlap / max(1, len(query_terms)) * 0.5)
        source_id = stable_id("src_web", PRIORITY_SOURCE_URL)
        source = Source(source_id, PRIORITY_SOURCE_TITLE, PRIORITY_SOURCE_URL, "official_website", 0.9, "approved_external")
        self.knowledge_base.sources[source_id] = source
        return Evidence(
            evidence_id=f"web_priority_{source_id[-8:]}", source_id=source_id,
            quote=content[:2500], locator=PRIORITY_SOURCE_URL, relevance_score=round(relevance, 3),
            source_trust_score=source.trust_score, query=query, retrieval_method="firecrawl_scrape_priority",
            source_check_passed=True, source_title=source.title, source_uri=source.uri,
        )

    def _fetch_priority_content(self) -> str:
        if self._priority_content is None:
            try:
                from firecrawl import Firecrawl
                client = Firecrawl(api_key=self.api_key, api_url=os.getenv("FIRECRAWL_API_URL", "https://api.firecrawl.dev"))
                document = client.scrape(PRIORITY_SOURCE_URL, formats=["markdown"])
                self._priority_content = str(getattr(document, "markdown", "") or "")
            except Exception:
                # Cloud/network failures must not take down the rest of retrieval.
                self._priority_content = ""
        return self._priority_content

    def _general_search(self, query: str, limit: int) -> list[Evidence]:
        if limit <= 0:
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
            if not url or url == PRIORITY_SOURCE_URL:
                continue  # already covered by _priority_evidence, don't cite it twice
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
