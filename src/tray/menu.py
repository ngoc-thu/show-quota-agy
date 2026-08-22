"""Top Bar popup menu construction using GTK3 menu widgets for AppIndicator."""

import subprocess
import sys
from typing import Optional, Callable
from ..core.models import QuotaSnapshot, ConnectionState, QuotaStatus
from ..core.config import APP_NAME
from ..core.logger import logger


def create_progress_bar_str(pct: float, width: int = 8) -> str:
    """Generates ASCII block progress representation e.g. ██████░░."""
    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100.0) * width))
    empty = width - filled
    return "█" * filled + "░" * empty


class TrayMenuBuilder:
    """Constructs dynamic GTK3 menu for AppIndicator."""

    @staticmethod
    def build_menu(
        Gtk,
        snapshot: Optional[QuotaSnapshot],
        on_refresh: Callable[[], None],
        on_open_dashboard: Callable[[], None],
        on_open_settings: Callable[[], None],
        on_quit: Callable[[], None],
    ):
        menu = Gtk.Menu()

        # 1. Header item
        header_text = f"🚀 {APP_NAME}"
        if snapshot:
            if snapshot.connection_state == ConnectionState.CONNECTED:
                header_text += "  🟢"
            elif snapshot.connection_state == ConnectionState.AUTH_REQUIRED:
                header_text += "  🔐 Auth Required"
            elif snapshot.connection_state == ConnectionState.OFFLINE:
                header_text += "  ⚪ Offline"
            else:
                header_text += "  ⚠ Error"

        header_item = Gtk.MenuItem(label=header_text)
        header_item.set_sensitive(False)
        menu.append(header_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 2. Model Quotas
        if snapshot and snapshot.models:
            # Sort models: default / recommended first, then by name
            sorted_models = sorted(
                snapshot.models.values(),
                key=lambda m: (not m.recommended, m.model_name),
            )

            # Limit top models to keep popup clean
            for minfo in sorted_models[:8]:
                bar = create_progress_bar_str(minfo.percentage, width=8)
                countdown = minfo.formatted_countdown()
                label = f"{minfo.model_name:<20} {bar} {minfo.percentage:4.1f}% {minfo.status.emoji}"
                if countdown != "N/A":
                    label += f" ({countdown})"

                item = Gtk.MenuItem(label=label)
                item.set_sensitive(False)
                menu.append(item)

            # Group buckets summary if available
            if snapshot.groups:
                menu.append(Gtk.SeparatorMenuItem())
                for g in snapshot.groups:
                    g_label = f"• {g.display_name}:"
                    for b in g.buckets:
                        g_label += f" [{b.window}: {b.percentage:.1f}%]"
                    g_item = Gtk.MenuItem(label=g_label)
                    g_item.set_sensitive(False)
                    menu.append(g_item)

            menu.append(Gtk.SeparatorMenuItem())

            # Timestamp
            up_text = f"Updated: {snapshot.last_updated_str}"
            if snapshot.is_stale:
                up_text += " (stale)"
            up_item = Gtk.MenuItem(label=up_text)
            up_item.set_sensitive(False)
            menu.append(up_item)

        else:
            empty_item = Gtk.MenuItem(label="No quota data available")
            empty_item.set_sensitive(False)
            menu.append(empty_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 3. Actions
        refresh_item = Gtk.MenuItem(label="↻ Refresh Now")
        refresh_item.connect("activate", lambda _: on_refresh())
        menu.append(refresh_item)

        dash_item = Gtk.MenuItem(label="🏠 Open Dashboard")
        dash_item.connect("activate", lambda _: on_open_dashboard())
        menu.append(dash_item)

        settings_item = Gtk.MenuItem(label="⚙ Settings")
        settings_item.connect("activate", lambda _: on_open_settings())
        menu.append(settings_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="✕ Quit")
        quit_item.connect("activate", lambda _: on_quit())
        menu.append(quit_item)

        menu.show_all()
        return menu
