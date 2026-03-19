import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def validate_email(email):
    value = (email or "").strip().lower()
    if not value:
        return None, "Email is required"
    if not EMAIL_RE.match(value):
        return None, "Invalid email format"
    return value, None

def validate_password(password):
    value = password or ""
    if len(value) < 8:
        return "Password must be at least 8 characters"
    if not re.search(r"[a-z]", value):
        return "Password must include a lowercase letter"
    if not re.search(r"[A-Z]", value):
        return "Password must include an uppercase letter"
    if not re.search(r"\d", value):
        return "Password must include a number"
    return None
