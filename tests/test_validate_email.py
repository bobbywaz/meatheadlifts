import pytest
from app import validate_email

def test_validate_email_valid():
    """Test valid email formatting and cleanup."""
    assert validate_email("test@example.com") == ("test@example.com", None)

    # Test whitespace stripping
    assert validate_email("  test@example.com  ") == ("test@example.com", None)

    # Test lowercase conversion
    assert validate_email("TEST@EXAMPLE.COM") == ("test@example.com", None)
    assert validate_email("  Test@Example.Com  ") == ("test@example.com", None)

    # Valid complex formats based on the regex
    assert validate_email("user.name+tag@example.co.uk") == ("user.name+tag@example.co.uk", None)


def test_validate_email_empty():
    """Test empty, missing, or whitespace-only emails."""
    assert validate_email(None) == (None, "Email is required")
    assert validate_email("") == (None, "Email is required")
    assert validate_email("   ") == (None, "Email is required")


def test_validate_email_invalid_format():
    """Test strings that do not match the EMAIL_RE."""
    # Missing @
    assert validate_email("testexample.com") == (None, "Invalid email format")

    # Missing domain
    assert validate_email("test@") == (None, "Invalid email format")

    # Missing username
    assert validate_email("@example.com") == (None, "Invalid email format")

    # Spaces in email
    assert validate_email("test user@example.com") == (None, "Invalid email format")
    assert validate_email("test@example com") == (None, "Invalid email format")

    # Invalid characters or no domain extension
    # EMAIL_RE = r"^[^@\s]+@[^@\s]+\.[^@\s]+$" requires at least one dot in domain part
    assert validate_email("test@example") == (None, "Invalid email format")
