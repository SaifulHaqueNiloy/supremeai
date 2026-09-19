from services.scraper.security import (
    _BLOCKED_HOSTS,
    _BLOCKED_SCHEMES,
    _is_blocked_ip,
    _is_private_ip,
    is_safe_url,
    is_safe_url_resolved,
)


def test_https_public_url_is_safe():
    assert is_safe_url("https://example.com/path?q=1") is True


def test_http_public_url_is_safe():
    assert is_safe_url("http://example.org") is True


def test_blocked_schemes_are_unsafe():
    for scheme in _BLOCKED_SCHEMES:
        assert is_safe_url(f"{scheme}://example.com") is False


def test_ftp_scheme_is_unsafe():
    assert is_safe_url("ftp://example.com/file") is False


def test_localhost_variants_are_unsafe():
    for host in _BLOCKED_HOSTS:
        assert is_safe_url(f"http://{host}") is False


def test_private_ip_ranges_are_unsafe():
    assert is_safe_url("http://10.0.0.1") is False
    assert is_safe_url("http://192.168.1.1") is False
    assert is_safe_url("http://172.16.0.1") is False
    assert is_safe_url("http://169.254.169.254") is False


def test_missing_hostname_is_unsafe():
    assert is_safe_url("http://") is False


def test_is_private_ip_helper():
    assert _is_private_ip("10.0.0.1") is True
    assert _is_private_ip("127.0.0.1") is True  # is_local()
    assert _is_private_ip("8.8.8.8") is False
    assert _is_private_ip("not-an-ip") is False


# ---------------------------------------------------------------------------
# Issue #511 (BE-05): request-time validation on resolved IPs
# ---------------------------------------------------------------------------


def test_metadata_hosts_are_unsafe():
    assert is_safe_url("http://metadata") is False
    assert is_safe_url("http://metadata.google.internal") is False


def test_is_blocked_ip_helper():
    assert _is_blocked_ip("10.0.0.1") is True
    assert _is_blocked_ip("127.0.0.1") is True
    assert _is_blocked_ip("169.254.169.254") is True  # cloud metadata
    assert _is_blocked_ip("100.64.0.13") is True  # CGNAT
    assert _is_blocked_ip("0.0.0.0") is True
    assert _is_blocked_ip("192.168.10.5") is True
    assert _is_blocked_ip("172.31.255.255") is True
    assert _is_blocked_ip("224.0.0.1") is True  # multicast
    assert _is_blocked_ip("240.0.0.1") is True  # reserved
    assert _is_blocked_ip("::1") is True
    assert _is_blocked_ip("fc00::1") is True  # IPv6 ULA
    assert _is_blocked_ip("fe80::1") is True  # IPv6 link-local
    assert _is_blocked_ip("::ffff:10.0.0.1") is True  # IPv4-mapped private
    assert _is_blocked_ip("not-an-ip") is True  # fail closed
    assert _is_blocked_ip("8.8.8.8") is False
    assert _is_blocked_ip("2606:4700:4700::1111") is False


def test_is_safe_url_resolved_blocks_private_resolution(monkeypatch):
    monkeypatch.setattr(
        "services.scraper.security.resolve_hostname", lambda host: ["10.1.2.3"]
    )
    assert is_safe_url_resolved("https://example.com") is False


def test_is_safe_url_resolved_blocks_when_one_record_is_private(monkeypatch):
    monkeypatch.setattr(
        "services.scraper.security.resolve_hostname",
        lambda host: ["93.184.216.34", "169.254.169.254"],
    )
    assert is_safe_url_resolved("https://example.com") is False


def test_is_safe_url_resolved_allows_public_resolution(monkeypatch):
    monkeypatch.setattr(
        "services.scraper.security.resolve_hostname", lambda host: ["93.184.216.34"]
    )
    assert is_safe_url_resolved("https://example.com") is True


def test_is_safe_url_resolved_fails_closed_on_dns_failure(monkeypatch):
    monkeypatch.setattr("services.scraper.security.resolve_hostname", lambda host: [])
    assert is_safe_url_resolved("https://example.com") is False


def test_is_safe_url_resolved_still_blocks_parse_time_urls():
    assert is_safe_url_resolved("http://127.0.0.1/admin") is False
    assert is_safe_url_resolved("ftp://example.com") is False
