"""Unit tests for token sanitization filter."""

import unittest
from src.core.logger import SanitizingFilter


class TestLogger(unittest.TestCase):
    def test_token_sanitization(self):
        text_with_token = "User authenticated with Bearer ya29.a0AfH6SMDI8823hjdks8237 and refresh 1//04kjdsf83427"
        sanitized = SanitizingFilter.sanitize(text_with_token)
        self.assertNotIn("ya29.a0AfH6SMDI8823hjdks8237", sanitized)
        self.assertNotIn("1//04kjdsf83427", sanitized)
        self.assertIn("[REDACTED_TOKEN]", sanitized)

    def test_json_token_sanitization(self):
        json_str = '{"access_token": "ya29.secret123", "refresh_token": "1//refresh456"}'
        sanitized = SanitizingFilter.sanitize(json_str)
        self.assertNotIn("ya29.secret123", sanitized)
        self.assertNotIn("1//refresh456", sanitized)


if __name__ == "__main__":
    unittest.main()
