"""Manages user-level XDG autostart .desktop configuration."""

import os
from pathlib import Path
from ..core.config import AUTOSTART_DIR, AUTOSTART_FILE, APP_NAME
from ..core.logger import logger

DESKTOP_ENTRY_TEMPLATE = """[Desktop Entry]
Type=Application
Name={app_name}
Comment=Monitor Google Antigravity quota from GNOME Top Bar
Exec=antigravity-quota --tray
Icon=antigravity-quota-monitor
Terminal=false
Categories=Utility;Development;
StartupNotify=false
X-GNOME-Autostart-enabled=true
"""


class AutostartManager:
    """Configures automatic startup upon user login."""

    @staticmethod
    def is_enabled() -> bool:
        return AUTOSTART_FILE.exists()

    @staticmethod
    def set_enabled(enable: bool):
        try:
            if enable:
                AUTOSTART_DIR.mkdir(parents=True, exist_ok=True)
                content = DESKTOP_ENTRY_TEMPLATE.format(app_name=APP_NAME)
                AUTOSTART_FILE.write_text(content, encoding="utf-8")
                logger.info("Enabled autostart at %s", AUTOSTART_FILE)
            else:
                if AUTOSTART_FILE.exists():
                    AUTOSTART_FILE.unlink()
                    logger.info("Disabled autostart: removed %s", AUTOSTART_FILE)
        except Exception as e:
            logger.error("Failed to update autostart configuration: %s", e)
