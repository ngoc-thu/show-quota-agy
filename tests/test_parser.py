"""Unit tests for API response parsing and normalization."""

import unittest
from src.antigravity.parser import parse_quota_response, categorize_model
from src.core.models import QuotaStatus, AppSettings
from tests.mock_data import MOCK_FETCH_MODELS_RESPONSE, MOCK_QUOTA_SUMMARY_RESPONSE


class TestParser(unittest.TestCase):
    def setUp(self):
        self.settings = AppSettings()

    def test_categorize_model(self):
        self.assertEqual(categorize_model("claude-sonnet-4-6", "Claude Sonnet"), "Claude")
        self.assertEqual(categorize_model("gpt-oss-120b", "GPT-OSS"), "GPT")
        self.assertEqual(categorize_model("gemini-3.6-flash", "Gemini 3.6 Flash"), "Gemini")
        self.assertEqual(categorize_model("custom-agent", "Custom Agent"), "Other")

    def test_parse_quota_response(self):
        snapshot = parse_quota_response(
            models_json=MOCK_FETCH_MODELS_RESPONSE,
            summary_json=MOCK_QUOTA_SUMMARY_RESPONSE,
            settings=self.settings,
        )

        # Check default model
        self.assertEqual(snapshot.default_model_id, "gemini-3.6-flash-high")

        # Check models count
        self.assertEqual(len(snapshot.models), 5)

        # Check Gemini Flash values
        g_flash = snapshot.models["gemini-3.6-flash-high"]
        self.assertEqual(g_flash.percentage, 88.8)
        self.assertEqual(g_flash.status, QuotaStatus.HEALTHY)
        self.assertTrue(g_flash.recommended)

        # Check Claude Opus values
        c_opus = snapshot.models["claude-opus-4-6-thinking"]
        self.assertEqual(c_opus.percentage, 42.5)
        self.assertEqual(c_opus.status, QuotaStatus.WARNING)

        # Check GPT values (0.08 -> 8.0% -> CRITICAL)
        gpt = snapshot.models["gpt-oss-120b-medium"]
        self.assertEqual(gpt.percentage, 8.0)
        self.assertEqual(gpt.status, QuotaStatus.CRITICAL)

        # Check Groups
        self.assertEqual(len(snapshot.groups), 2)
        g1 = snapshot.groups[0]
        self.assertEqual(g1.display_name, "Gemini Models")
        self.assertEqual(len(g1.buckets), 2)
        self.assertEqual(g1.buckets[0].percentage, 82.2)

    def test_parse_empty_response(self):
        snapshot = parse_quota_response({}, None, self.settings)
        self.assertEqual(len(snapshot.models), 0)
        self.assertEqual(len(snapshot.groups), 0)


if __name__ == "__main__":
    unittest.main()
