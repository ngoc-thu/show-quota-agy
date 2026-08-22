"""Repository for persisting user settings and preferences in SQLite."""

import json
from typing import Optional
from .db import DatabaseManager
from ..core.models import AppSettings, DisplayMode
from ..core.logger import logger


class SettingsRepository:
    """Stores and loads user preferences."""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager

    def load_settings(self) -> AppSettings:
        """Loads settings from SQLite or returns defaults."""
        settings = AppSettings()
        try:
            with self.db_manager.get_connection() as conn:
                cursor = conn.execute("SELECT key, value FROM settings;")
                rows = {row["key"]: row["value"] for row in cursor.fetchall()}

            if not rows:
                return settings

            if "refresh_interval_sec" in rows:
                settings.refresh_interval_sec = int(rows["refresh_interval_sec"])
            if "display_mode" in rows:
                try:
                    settings.display_mode = DisplayMode(rows["display_mode"])
                except ValueError:
                    settings.display_mode = DisplayMode.COMBINED_5H_WEEKLY
            if "healthy_threshold" in rows:
                settings.healthy_threshold = int(rows["healthy_threshold"])
            if "warning_threshold" in rows:
                settings.warning_threshold = int(rows["warning_threshold"])
            if "critical_threshold" in rows:
                settings.critical_threshold = int(rows["critical_threshold"])
            if "autostart" in rows:
                settings.autostart = rows["autostart"].lower() in ("true", "1")
            if "show_tray" in rows:
                settings.show_tray = rows["show_tray"].lower() in ("true", "1")
            if "notify_low_quota" in rows:
                settings.notify_low_quota = rows["notify_low_quota"].lower() in ("true", "1")
            if "notify_reset" in rows:
                settings.notify_reset = rows["notify_reset"].lower() in ("true", "1")
            if "selected_model_override" in rows:
                settings.selected_model_override = rows["selected_model_override"] or None

        except Exception as e:
            logger.debug("Failed to load settings from DB: %s, using defaults", e)

        return settings

    def save_settings(self, settings: AppSettings):
        """Saves current settings object into SQLite."""
        items = [
            ("refresh_interval_sec", str(settings.refresh_interval_sec)),
            ("display_mode", settings.display_mode.value),
            ("healthy_threshold", str(settings.healthy_threshold)),
            ("warning_threshold", str(settings.warning_threshold)),
            ("critical_threshold", str(settings.critical_threshold)),
            ("autostart", "true" if settings.autostart else "false"),
            ("show_tray", "true" if settings.show_tray else "false"),
            ("notify_low_quota", "true" if settings.notify_low_quota else "false"),
            ("notify_reset", "true" if settings.notify_reset else "false"),
            ("selected_model_override", settings.selected_model_override or ""),
        ]

        with self.db_manager.get_connection() as conn:
            conn.executemany(
                """
                INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?);
                """,
                items,
            )
            conn.commit()
