"""SupremeAI Scout: Policy-Driven Web Crawler, Deduplication & Summarization Package."""

from __future__ import annotations

from scout.cache import CrawlerCache
from scout.crawler import CrawlerService
from scout.dedup import ContentDeduplicator
from scout.extractor import ExtractiveSummarizer
from scout.models import (
    CrawlEventType,
    CrawlHistoryRecord,
    CrawlPageResult,
    CrawlPolicy,
    CrawlRequest,
    CrawlResponse,
    DomainRule,
    TrustLevel,
)
from scout.policy import PolicyEngine
from scout.telemetry import CrawlerTelemetry
from scout.web_crawler_agent import APPROVED_DOMAINS, CrawlResult, crawl

__all__ = [
    "APPROVED_DOMAINS",
    "ContentDeduplicator",
    "CrawlEventType",
    "CrawlHistoryRecord",
    "CrawlPageResult",
    "CrawlPolicy",
    "CrawlRequest",
    "CrawlResponse",
    "CrawlResult",
    "CrawlerCache",
    "CrawlerService",
    "CrawlerTelemetry",
    "DomainRule",
    "ExtractiveSummarizer",
    "PolicyEngine",
    "TrustLevel",
    "crawl",
]
