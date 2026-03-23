import unittest
from app import validate_email

class TestValidateEmail(unittest.TestCase):
    def test_valid_email(self):
        """Test valid standard email address."""
        val, err = validate_email("test@example.com")
        self.assertEqual(val, "test@example.com")
        self.assertIsNone(err)

    def test_email_cleaning(self):
        """Test email is stripped and converted to lower case."""
        val, err = validate_email("  Test@Example.com  ")
        self.assertEqual(val, "test@example.com")
        self.assertIsNone(err)

    def test_missing_input_none(self):
        """Test None input."""
        val, err = validate_email(None)
        self.assertIsNone(val)
        self.assertEqual(err, "Email is required")

    def test_missing_input_empty(self):
        """Test empty string."""
        val, err = validate_email("")
        self.assertIsNone(val)
        self.assertEqual(err, "Email is required")

    def test_missing_input_whitespace(self):
        """Test whitespace-only string."""
        val, err = validate_email("   ")
        self.assertIsNone(val)
        self.assertEqual(err, "Email is required")

    def test_invalid_format_no_at(self):
        """Test missing @ symbol."""
        val, err = validate_email("testexample.com")
        self.assertIsNone(val)
        self.assertEqual(err, "Invalid email format")

    def test_invalid_format_no_domain(self):
        """Test missing domain part."""
        val, err = validate_email("test@")
        self.assertIsNone(val)
        self.assertEqual(err, "Invalid email format")

    def test_invalid_format_no_dot(self):
        """Test missing dot in domain."""
        val, err = validate_email("test@example")
        self.assertIsNone(val)
        self.assertEqual(err, "Invalid email format")

    def test_invalid_format_spaces_inside(self):
        """Test spaces inside email."""
        val, err = validate_email("test @example.com")
        self.assertIsNone(val)
        self.assertEqual(err, "Invalid email format")

if __name__ == '__main__':
    unittest.main()
