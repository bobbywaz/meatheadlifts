import pytest
from app import validate_email

def test_validate_email_none():
    assert validate_email(None) == (None, "Email is required")

def test_validate_email_empty():
    assert validate_email("") == (None, "Email is required")

def test_validate_email_whitespace():
    assert validate_email("   ") == (None, "Email is required")

def test_validate_email_valid():
    assert validate_email("test@example.com") == ("test@example.com", None)

def test_validate_email_valid_with_spaces_and_uppercase():
    assert validate_email("  Test@Example.com ") == ("test@example.com", None)

def test_validate_email_invalid_missing_at():
    assert validate_email("testexample.com") == (None, "Invalid email format")

def test_validate_email_invalid_missing_domain():
    assert validate_email("test@") == (None, "Invalid email format")

def test_validate_email_invalid_spaces_inside():
    assert validate_email("te st@example.com") == (None, "Invalid email format")
