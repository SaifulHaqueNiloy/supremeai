"""ResourceCatalog (tools/resource_catalog.py) এর ইউনিট টেস্ট।

বাংলা: নেটওয়ার্ক-ফ্রি লজিক কভার করা হয়েছে — _build_headers (GitHub টোকেন ইনজেকশন)
এবং _parse_awesome_markdown (কিওয়ার্ড ম্যাচ ও লিমিট)। settings মক করা হয়েছে।
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from tools.resource_catalog import ResourceCatalog


@pytest.fixture
def fake_settings():
    s = MagicMock()
    s.github_api_token = ""
    return s


def test_build_headers_no_token(fake_settings):
    with patch("tools.resource_catalog.settings", fake_settings):
        catalog = ResourceCatalog(http_client=MagicMock())
        headers = catalog._build_headers()
        assert headers["Accept"] == "application/vnd.github.v3+json"
        assert "Authorization" not in headers


def test_build_headers_with_token(fake_settings):
    fake_settings.github_api_token = "ghp_test123"
    with patch("tools.resource_catalog.settings", fake_settings):
        catalog = ResourceCatalog(http_client=MagicMock())
        headers = catalog._build_headers()
        assert headers["Authorization"] == "token ghp_test123"


def test_parse_awesome_markdown_matches_query(fake_settings):
    markdown = (
        "- [Gitea](https://gitea.io) - Self-hosted git service\n"
        "- [Nextcloud](https://nextcloud.com) - git file sync and share\n"
        "- [NotMatching](https://x.com) - unrelated tool\n"
    )
    with patch("tools.resource_catalog.settings", fake_settings):
        catalog = ResourceCatalog(http_client=MagicMock())
        results = catalog._parse_awesome_markdown(markdown, "git", limit=5, source_name="test")
        names = {r["name"] for r in results}
        assert "Gitea" in names
        assert "Nextcloud" in names
        assert "NotMatching" not in names
        assert all(r["source"] == "test" for r in results)


def test_parse_awesome_markdown_respects_limit(fake_settings):
    markdown = "\n".join(f"- [Tool{i}](https://t{i}.com) - git hosting tool" for i in range(10))
    with patch("tools.resource_catalog.settings", fake_settings):
        catalog = ResourceCatalog(http_client=MagicMock())
        results = catalog._parse_awesome_markdown(markdown, "git", limit=3, source_name="test")
        assert len(results) == 3


def test_parse_awesome_markdown_skips_non_entry_lines(fake_settings):
    markdown = "# Heading\n\nSome paragraph text\n\n- [Real](https://r.com) - git tool\n"
    with patch("tools.resource_catalog.settings", fake_settings):
        catalog = ResourceCatalog(http_client=MagicMock())
        results = catalog._parse_awesome_markdown(markdown, "git", limit=5, source_name="test")
        assert len(results) == 1
        assert results[0]["name"] == "Real"
