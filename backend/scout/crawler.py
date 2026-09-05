"""Primary policy-governed crawler service."""

from __future__ import annotations

import asyncio
import collections
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from core.logging_config import logger
from scout.cache import CrawlerCache
from scout.dedup import ContentDeduplicator
from scout.extractor import ExtractiveSummarizer
from scout.models import (
    CrawlEventType,
    CrawlPageResult,
    CrawlPolicy,
    CrawlRequest,
    CrawlResponse,
)
from scout.policy import PolicyEngine
from scout.telemetry import CrawlerTelemetry


class CrawlerService:
    """Orchestrates policy-guided crawling, deduplication, caching, and extractive summarization."""

    def __init__(
        self,
        policy: CrawlPolicy | None = None,
        deduplicator: ContentDeduplicator | None = None,
        summarizer: ExtractiveSummarizer | None = None,
        cache: CrawlerCache | None = None,
    ) -> None:
        self.policy_engine = PolicyEngine(policy)
        self.deduplicator = deduplicator or ContentDeduplicator()
        self.summarizer = summarizer or ExtractiveSummarizer()
        self.cache = cache or CrawlerCache()

    @staticmethod
    def _clean_html(html: str) -> tuple[str, str, list[str]]:
        """Strips scripts, styling, navbars and returns (title, clean_text, links)."""
        soup = BeautifulSoup(html, "html.parser")
        title = soup.title.string.strip() if soup.title and soup.title.string else "No Title"

        # Remove irrelevant noise tags
        for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
            tag.decompose()

        text = " ".join(soup.get_text(separator=" ").split())
        links = [a.get("href", "") for a in soup.find_all("a", href=True) if a.get("href")]
        return title, text, links

    async def execute_crawl(self, request: CrawlRequest) -> CrawlResponse:
        """Executes a bounded, policy-controlled crawl starting from the target URL."""
        start_url = request.query_or_url
        max_depth = request.max_depth or self.policy_engine.policy.max_depth
        max_results = request.max_results or self.policy_engine.policy.max_results
        timeout_sec = self.policy_engine.policy.request_timeout_seconds
        telemetry = CrawlerTelemetry(request.tenant_id, request.task_id)

        # 1. Check cache first
        cached = await self.cache.get_cached_response(
            request.tenant_id, start_url, max_depth=max_depth
        )
        if cached:
            telemetry.emit_event(
                CrawlEventType.CACHED_ANSWER,
                f"Returning cached crawl response for {start_url}",
            )
            return cached

        telemetry.emit_event(
            CrawlEventType.NAV_START,
            f"Starting crawl on {start_url} (depth={max_depth}, results={max_results})",
        )

        queue: collections.deque[tuple[str, int]] = collections.deque([(start_url, 0)])
        visited_urls: set[str] = set()
        pages: list[CrawlPageResult] = []
        unique_texts: list[str] = []
        total_fetched = 0
        total_duplicates = 0
        raw_char_count = 0

        # Reset deduplication tracking for this run
        self.deduplicator.reset()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 SupremeAI-Scout/2.0",
            **request.custom_headers,
        }

        async with httpx.AsyncClient(
            headers=headers, timeout=float(timeout_sec), follow_redirects=True
        ) as client:
            while queue and len(pages) < max_results:
                url, depth = queue.popleft()
                if url in visited_urls:
                    continue
                visited_urls.add(url)

                # Policy gate: SSRF, allowed domain, depth check
                allowed, reason = self.policy_engine.is_url_allowed(url, current_depth=depth)
                if not allowed:
                    logger.debug(f"Crawler skipped URL {url} (reason: {reason})")
                    continue

                domain = self.policy_engine.extract_domain(url)

                try:
                    resp = await client.get(url)
                    total_fetched += 1
                    if resp.status_code >= 400:
                        continue

                    title, text, links = self._clean_html(resp.text)
                    raw_char_count += len(text)

                    # Deduplication check
                    content_hash, is_dup = self.deduplicator.record_content(text)
                    if is_dup:
                        total_duplicates += 1
                    else:
                        unique_texts.append(text)

                    page_result = CrawlPageResult(
                        url=url,
                        domain=domain,
                        status_code=resp.status_code,
                        title=title,
                        content=text if not is_dup else "[Duplicate Content Omitted]",
                        content_hash=content_hash,
                        is_duplicate=is_dup,
                        depth=depth,
                        extracted_links=links[:25],
                    )
                    pages.append(page_result)

                    # Expand links if within depth limit
                    if depth < max_depth:
                        for raw_link in links:
                            resolved = urljoin(url, raw_link)
                            if resolved.startswith("http") and resolved not in visited_urls:
                                queue.append((resolved, depth + 1))

                except Exception as exc:
                    logger.warning(f"Failed to fetch {url}: {exc}")
                    continue

        # Zero-token extractive summarization across unique content
        merged_unique_content = " ".join(unique_texts)
        summary = self.summarizer.summarize(merged_unique_content, max_sentences=5, max_chars=2500)
        final_char_count = len(summary)

        token_reduction = 0.0
        if raw_char_count > 0 and final_char_count < raw_char_count:
            token_reduction = round((1.0 - (final_char_count / raw_char_count)) * 100, 1)

        response = CrawlResponse(
            task_id=request.task_id,
            tenant_id=request.tenant_id,
            query=request.query_or_url,
            pages=pages,
            total_fetched=total_fetched,
            total_duplicates_skipped=total_duplicates,
            token_reduction_pct=token_reduction,
            extractive_summary=summary,
        )

        telemetry.emit_event(
            CrawlEventType.NAV_COMPLETE,
            f"Crawl completed for {start_url}: {len(pages)} pages fetched, {total_duplicates} duplicates skipped, {token_reduction}% tokens saved",
            metadata={
                "pages_count": len(pages),
                "token_reduction_pct": token_reduction,
            },
        )

        # Store in cache
        await self.cache.store_response(
            request.tenant_id,
            start_url,
            max_depth=max_depth,
            response=response,
            ttl_seconds=self.policy_engine.policy.cache_ttl_hours * 3600,
        )

        return response
