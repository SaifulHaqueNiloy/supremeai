from services.scraper.security import (
    _BLOCKED_HOSTS,
    _BLOCKED_SCHEMES,
    _is_private_ip,
    is_safe_url,
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
