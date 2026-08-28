from unittest.mock import MagicMock, patch

import httpx

from services.scraper.web_scraper import WebScraper


def test_fetch_page_blocks_ssrf():
    scraper = WebScraper()
    with patch("services.scraper.web_scraper.is_safe_url", return_value=False):
        result = scraper.fetch_page("http://127.0.0.1:8080/secret")
    assert result["success"] is False
    assert "SSRF" in result["error"]
    assert result["url"] == "http://127.0.0.1:8080/secret"


def test_fetch_page_parses_html_successfully():
    class _FakeResponse:
        status_code = 200
        text = (
            "<html><head><title>Hello Title</title></head>"
            "<body><script>ignore()</script><p>Main content here</p>"
            "<a href='/page-a'>A</a><a href='/page-b'>B</a></body></html>"
        )

        def raise_for_status(self):
            return None

    with (
        patch("services.scraper.web_scraper.is_safe_url", return_value=True),
        patch("services.scraper.web_scraper.httpx.get", return_value=_FakeResponse()),
    ):
        result = WebScraper().fetch_page("https://example.com")

    assert result["success"] is True
    assert result["title"] == "Hello Title"
    assert "Main content here" in result["content"]
    assert result["links"] == ["/page-a", "/page-b"]
    assert result["status_code"] == 200


def test_fetch_page_handles_request_error():
    with (
        patch("services.scraper.web_scraper.is_safe_url", return_value=True),
        patch(
            "services.scraper.web_scraper.httpx.get",
            side_effect=httpx.RequestError("connection refused"),
        ),
    ):
        result = WebScraper().fetch_page("https://example.com")

    assert result["success"] is False
    assert "connection refused" in result["error"]
