"""Unit tests for Top Bar menu builder and reset time formatter."""

import unittest
from datetime import datetime, timezone, timedelta
from src.tray.menu import format_reset_time, create_progress_bar_str


class TestTrayMenu(unittest.TestCase):

    def test_create_progress_bar_str(self):
        self.assertEqual(create_progress_bar_str(100.0, width=6), "██████")
        self.assertEqual(create_progress_bar_str(0.0, width=6), "░░░░░░")
        self.assertEqual(create_progress_bar_str(50.0, width=6), "███░░░")

    def test_format_reset_time(self):
        now = datetime(2026, 8, 24, 8, 0, 0, tzinfo=timezone.utc)

        # None reset time
        self.assertEqual(format_reset_time(None, now=now), "N/A")

        # Expired reset time
        past = now - timedelta(minutes=5)
        self.assertEqual(format_reset_time(past, now=now), "Sẵn sàng reset")

        # Future hours
        future_hours = now + timedelta(hours=4, minutes=24)
        res = format_reset_time(future_hours, now=now)
        self.assertIn("4h 24m", res)

        # Future days
        future_days = now + timedelta(days=2, hours=5)
        res = format_reset_time(future_days, now=now)
        self.assertIn("2d 5h", res)


if __name__ == "__main__":
    unittest.main()
