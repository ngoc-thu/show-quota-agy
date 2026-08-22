"""Adw.Application lifecycle and GUI entrypoint."""

import sys
import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio
from typing import Optional
from ..core.service import QuotaService
from ..core.config import APP_ID, APP_NAME
from ..core.logger import logger
from .window import MainWindow


class QuotaMonitorApp(Adw.Application):
    """Libadwaita application instance."""

    def __init__(self, service: Optional[QuotaService] = None, initial_tab: Optional[str] = None):
        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.NON_UNIQUE,
        )
        self.service = service or QuotaService()
        self.initial_tab = initial_tab
        self.window = None

    def do_activate(self):
        if not self.window:
            self.window = MainWindow(
                app=self,
                service=self.service,
                initial_tab=self.initial_tab,
            )
        self.window.present()


def run_gui(service: Optional[QuotaService] = None, initial_tab: Optional[str] = None) -> int:
    """Entrypoint to launch the GTK4 GUI window."""
    app = QuotaMonitorApp(service=service, initial_tab=initial_tab)
    return app.run([])
