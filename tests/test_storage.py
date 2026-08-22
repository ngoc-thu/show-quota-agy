"""Unit tests for SQLite database and repositories."""

import unittest
from pathlib import Path
from src.storage.db import DatabaseManager
from src.storage.history_repo import HistoryRepository
from src.storage.settings_repo import SettingsRepository
from src.core.models import QuotaSnapshot, QuotaInfo, AppSettings, DisplayMode


class TestStorage(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager(Path(":memory:"))
        self.history_repo = HistoryRepository(self.db)
        self.settings_repo = SettingsRepository(self.db)

    def test_settings_save_and_load(self):
        s = AppSettings(
            refresh_interval_sec=30,
            display_mode=DisplayMode.ACTIVE,
            healthy_threshold=80,
            warning_threshold=40,
            autostart=False,
            notify_low_quota=True,
        )
        self.settings_repo.save_settings(s)

        loaded = self.settings_repo.load_settings()
        self.assertEqual(loaded.refresh_interval_sec, 30)
        self.assertEqual(loaded.display_mode, DisplayMode.ACTIVE)
        self.assertEqual(loaded.healthy_threshold, 80)
        self.assertEqual(loaded.warning_threshold, 40)
        self.assertFalse(loaded.autostart)
        self.assertTrue(loaded.notify_low_quota)

    def test_history_record_and_query(self):
        m1 = QuotaInfo(model_id="gemini-pro", model_name="Gemini Pro", remaining_fraction=0.75, percentage=75.0)
        m2 = QuotaInfo(model_id="claude", model_name="Claude", remaining_fraction=0.50, percentage=50.0)
        snapshot = QuotaSnapshot(models={"gemini-pro": m1, "claude": m2})

        self.history_repo.record_snapshot(snapshot)

        history = self.history_repo.get_history(hours=1.0)
        self.assertEqual(len(history), 2)
        model_ids = {row["model_id"] for row in history}
        self.assertEqual(model_ids, {"gemini-pro", "claude"})

        # Filter by model_id
        gemini_history = self.history_repo.get_history(hours=1.0, model_id="gemini-pro")
        self.assertEqual(len(gemini_history), 1)
        self.assertEqual(gemini_history[0]["percentage"], 75.0)


if __name__ == "__main__":
    unittest.main()
