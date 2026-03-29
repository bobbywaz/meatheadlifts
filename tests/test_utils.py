import pytest
from app import is_safe_url

def test_is_safe_url_empty_values():
    assert is_safe_url(None) is True
    assert is_safe_url("") is True

def test_is_safe_url_valid_local_paths():
    assert is_safe_url("/index") is True
    assert is_safe_url("page.html") is True
    assert is_safe_url("/path/to/resource?query=1") is True
    assert is_safe_url("/login?next=/dashboard") is True
    assert is_safe_url("?query=1") is True
    assert is_safe_url("#section") is True

def test_is_safe_url_external_urls():
    assert is_safe_url("http://example.com") is False
    assert is_safe_url("https://example.com/page") is False
    assert is_safe_url("ftp://example.com") is False

def test_is_safe_url_edge_cases():
    assert is_safe_url("//example.com") is False
    assert is_safe_url("\\\\example.com") is False
    assert is_safe_url("javascript:alert(1)") is False
    assert is_safe_url("javascript://alert(1)") is False
    assert is_safe_url("data:text/html,<script>alert(1)</script>") is False

def test_is_safe_url_schemeless_with_netloc():
    # urlparse might handle things differently, testing specifically what we block
    assert is_safe_url("http:///example.com") is False
