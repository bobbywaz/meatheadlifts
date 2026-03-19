import unittest
from app import validate_password

class TestValidatePassword(unittest.TestCase):
    def test_valid_password(self):
        self.assertIsNone(validate_password("Valid1Password"))
        self.assertIsNone(validate_password("1234567aA"))

    def test_short_password(self):
        self.assertEqual(validate_password("Short1a"), "Password must be at least 8 characters")
        self.assertEqual(validate_password(""), "Password must be at least 8 characters")

    def test_missing_lowercase(self):
        self.assertEqual(validate_password("NOLOWERCASE1"), "Password must include a lowercase letter")

    def test_missing_uppercase(self):
        self.assertEqual(validate_password("nouppercase1"), "Password must include an uppercase letter")

    def test_missing_digit(self):
        self.assertEqual(validate_password("NoDigitHere"), "Password must include a number")

    def test_none_input(self):
        self.assertEqual(validate_password(None), "Password must be at least 8 characters")

if __name__ == '__main__':
    unittest.main()
