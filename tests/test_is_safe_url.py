import pytest
from app import is_safe_url

def test_is_safe_url_empty():
    """Test that empty or None targets are considered safe."""
    assert is_safe_url(None) is True
    assert is_safe_url("") is True

def test_is_safe_url_relative():
    """Test that relative URLs are considered safe."""
    assert is_safe_url("/") is True
    assert is_safe_url("/path") is True
    assert is_safe_url("/path/to/resource") is True
    assert is_safe_url("/path?query=1") is True
    assert is_safe_url("/path#fragment") is True

def test_is_safe_url_absolute_http():
    """Test that absolute HTTP(S) URLs are considered unsafe."""
    assert is_safe_url("http://example.com") is False
    assert is_safe_url("https://example.com") is False
    assert is_safe_url("http://example.com/path") is False

def test_is_safe_url_protocol_relative():
    """Test that protocol-relative URLs (starting with // or \\\\) are considered unsafe."""
    assert is_safe_url("//example.com") is False
    assert is_safe_url("\\\\example.com") is False

def test_is_safe_url_other_schemes():
    """Test that other schemes (like javascript, file, ftp, mailto) are considered unsafe."""
    assert is_safe_url("javascript:alert(1)") is False
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("ftp://example.com") is False
    assert is_safe_url("mailto:test@example.com") is False
    assert is_safe_url("data:text/html,<script>alert(1)</script>") is False

def test_is_safe_url_sneaky():
    """Test sneaky URLs that might try to bypass checks."""
    assert is_safe_url("///example.com") is False
    assert is_safe_url("////example.com") is False
    assert is_safe_url("\\\\\\example.com") is False
    assert is_safe_url(" /") is True
