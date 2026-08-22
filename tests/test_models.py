"""Unit tests for core data models and calculations."""

import unittest
from datetime import datetime, timezone, timedelta
from src.core.models import (
    QuotaInfo,
    QuotaStatus,
    AppSettings,
    DisplayMode,
    QuotaSnapshot,
    ConnectionState,
)


class TestModels(unittest.TestCase):
    def setUp(self):
        self.settings = AppSettings(
            healthy_threshold=70,
            warning_threshold=30,
            critical_threshold=10,
        )

    def test_compute_status(self):
        self.assertEqual(self.settings.compute_status(90.0), QuotaStatus.HEALTHY)
        self.assertEqual(self.settings.compute_status(70.0), QuotaStatus.HEALTHY)
        self.assertEqual(self.settings.compute_status(69.9), QuotaStatus.WARNING)
        self.assertEqual(self.settings.compute_status(30.0), QuotaStatus.WARNING)
        self.assertEqual(self.settings.compute_status(29.9), QuotaStatus.CRITICAL)
        self.assertEqual(self.settings.compute_status(0.0), QuotaStatus.CRITICAL)

    def test_formatted_countdown(self):
        now = datetime(2026, 8, 22, 12, 0, 0, tzinfo=timezone.utc)
        reset_time = now + timedelta(hours=2, minutes=17, seconds=30)
        q = QuotaInfo(
            model_id="test",
            model_name="Test Model",
            remaining_fraction=0.72,
            percentage=72.0,
            reset_time=reset_time,
        )
        self.assertEqual(q.formatted_countdown(now=now), "2h 17m")

        # Test days countdown
        reset_time_days = now + timedelta(days=3, hours=5)
        q.reset_time = reset_time_days
        self.assertEqual(q.formatted_countdown(now=now), "3d 5h")

        # Test minutes / seconds countdown
        reset_time_min = now + timedelta(minutes=4, seconds=15)
        q.reset_time = reset_time_min
        self.assertEqual(q.formatted_countdown(now=now), "4m 15s")

        # Test expired countdown
        reset_past = now - timedelta(minutes=5)
        q.reset_time = reset_past
        self.assertEqual(q.formatted_countdown(now=now), "Ready to reset")

    def test_snapshot_display_percentage(self):
        m1 = QuotaInfo(model_id="gemini-pro", model_name="Gemini Pro", remaining_fraction=0.88, percentage=88.0)
        m2 = QuotaInfo(model_id="claude", model_name="Claude", remaining_fraction=0.43, percentage=43.0)
        snapshot = QuotaSnapshot(
            models={"gemini-pro": m1, "claude": m2},
            default_model_id="gemini-pro",
        )

        # Lowest mode
        self.assertEqual(snapshot.get_display_percentage(DisplayMode.LOWEST), 43.0)

        # Active mode
        self.assertEqual(snapshot.get_display_percentage(DisplayMode.ACTIVE), 88.0)


if __name__ == "__main__":
    unittest.main()
