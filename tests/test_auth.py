from utils import validate_password

def test_validate_password_valid():
    """Test that a valid password returns None."""
    assert validate_password("ValidPass123") is None

def test_validate_password_short():
    """Test that a password shorter than 8 characters returns an error."""
    assert validate_password("Short1!") == "Password must be at least 8 characters"

def test_validate_password_no_lowercase():
    """Test that a password without lowercase letters returns an error."""
    assert validate_password("UPPERCASE123") == "Password must include a lowercase letter"

def test_validate_password_no_uppercase():
    """Test that a password without uppercase letters returns an error."""
    assert validate_password("lowercase123") == "Password must include an uppercase letter"

def test_validate_password_no_number():
    """Test that a password without a number returns an error."""
    assert validate_password("NoNumberPass") == "Password must include a number"

def test_validate_password_none():
    """Test that a None input returns an error."""
    assert validate_password(None) == "Password must be at least 8 characters"

def test_validate_password_empty():
    """Test that an empty string returns an error."""
    assert validate_password("") == "Password must be at least 8 characters"
