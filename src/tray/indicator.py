"""GNOME Top Bar indicator implementation using AppIndicator3."""

import os
import sys
import subprocess
from pathlib import Path
from typing import Optional
from ..core.models import QuotaSnapshot, ConnectionState
from ..core.service import QuotaService
from ..core.config import APP_NAME
from ..core.logger import logger
from .menu import TrayMenuBuilder


class TopBarIndicator:
    """Manages the GNOME Top Bar indicator and menu lifecycle."""

    def __init__(self, service: QuotaService):
        self.service = service
        self.indicator = None
        self.Gtk = None
        self.GLib = None

    def run(self):
        """Initializes GTK3 and AppIndicator loop."""
        import gi
        gi.require_version("Gtk", "3.0")
        try:
            gi.require_version("AppIndicator3", "0.1")
            from gi.repository import AppIndicator3
        except Exception:
            gi.require_version("AyatanaAppIndicator3", "0.1")
            from gi.repository import AyatanaAppIndicator3 as AppIndicator3

        from gi.repository import Gtk, GLib
        self.Gtk = Gtk
        self.GLib = GLib

        # Create Indicator
        icon_theme_path = str(Path(__file__).resolve().parent.parent.parent / "assets" / "icons")
        self.indicator = AppIndicator3.Indicator.new_with_path(
            "antigravity-quota-monitor",
            "antigravity-quota-monitor",
            AppIndicator3.IndicatorCategory.APPLICATION_STATUS,
            icon_theme_path,
        )
        self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        self.indicator.set_label("...", "5h: [▰▰▰▰] 100% | Tuần: [▰▰▰▰] 100%")

        # Subscribe to service snapshot updates
        self.service.add_listener(self._on_snapshot_updated)

        # Build initial menu
        self._update_ui(self.service.current_snapshot)

        # Start auto refresh in background
        self.service.start_auto_refresh()

        logger.info("GNOME Top Bar Indicator started.")
        Gtk.main()

    def _on_snapshot_updated(self, snapshot: QuotaSnapshot):
        """Thread-safe dispatch to GTK main loop."""
        if self.GLib:
            self.GLib.idle_add(self._update_ui, snapshot)

    def _update_ui(self, snapshot: Optional[QuotaSnapshot]):
        if not self.indicator or not self.Gtk:
            return

        # 1. Update Top Bar Label
        if snapshot and snapshot.connection_state == ConnectionState.CONNECTED:
            label = snapshot.get_display_label(self.service.settings.display_mode)
        elif snapshot and snapshot.connection_state == ConnectionState.AUTH_REQUIRED:
            label = "🔐"
        elif snapshot and snapshot.connection_state == ConnectionState.OFFLINE:
            label = "⚪"
        else:
            label = "..."

        self.indicator.set_label(label, "5h: [▰▰▰▰] 100% | Tuần: [▰▰▰▰] 100%")

        # 2. Update Popup Menu
        menu = TrayMenuBuilder.build_menu(
            Gtk=self.Gtk,
            snapshot=snapshot,
            on_refresh=self._handle_refresh,
            on_open_dashboard=self._handle_open_dashboard,
            on_open_settings=self._handle_open_settings,
            on_quit=self._handle_quit,
        )
        self.indicator.set_menu(menu)

    def _handle_refresh(self):
        logger.info("Manual refresh triggered from Top Bar menu.")
        # Trigger background refresh
        import threading
        threading.Thread(target=lambda: self.service.refresh(force=True), daemon=True).start()

    def _handle_open_dashboard(self):
        logger.info("Opening dashboard GUI...")
        launcher = str(Path(__file__).resolve().parent.parent.parent / "antigravity-quota")
        subprocess.Popen([launcher, "--gui"])

    def _handle_open_settings(self):
        logger.info("Opening settings GUI...")
        launcher = str(Path(__file__).resolve().parent.parent.parent / "antigravity-quota")
        subprocess.Popen([launcher, "--gui", "--tab=settings"])

    def _handle_quit(self):
        logger.info("Quitting Top Bar indicator...")
        self.service.stop_auto_refresh()
        if self.Gtk:
            self.Gtk.main_quit()
