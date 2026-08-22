"""About tab view presenting application metadata and credits."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from ...core.config import APP_NAME, VERSION


class AboutView(Gtk.Box):
    """About tab container with project metadata."""

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(32)
        self.set_margin_bottom(32)
        self.set_margin_start(32)
        self.set_margin_end(32)
        self.set_valign(Gtk.Align.CENTER)
        self.set_halign(Gtk.Align.CENTER)

        self._build_ui()

    def _build_ui(self):
        # Rocket Icon Label
        icon_lbl = Gtk.Label(label="🚀")
        icon_lbl.add_css_class("title-1")
        self.append(icon_lbl)

        # Title
        title_lbl = Gtk.Label(label=APP_NAME)
        title_lbl.add_css_class("title-1")
        title_lbl.add_css_class("bold")
        self.append(title_lbl)

        # Version
        ver_lbl = Gtk.Label(label=f"Phiên bản {VERSION}")
        ver_lbl.add_css_class("dim-label")
        ver_lbl.add_css_class("caption")
        self.append(ver_lbl)

        # Description
        desc_lbl = Gtk.Label(
            label="Phần mềm Desktop native cho Ubuntu theo dõi quota và hạn mức sử dụng của Google Antigravity trong thời gian thực.",
            wrap=True,
            max_width_chars=40,
            justify=Gtk.Justification.CENTER,
        )
        desc_lbl.set_margin_top(12)
        desc_lbl.add_css_class("body")
        self.append(desc_lbl)

        # Feature badges list
        badge_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        badge_box.set_halign(Gtk.Align.CENTER)
        badge_box.set_margin_top(16)

        b1 = Gtk.Label(label="GTK4 & Libadwaita")
        b1.add_css_class("quota-badge")
        b1.add_css_class("quota-badge-recommended")
        badge_box.append(b1)

        b2 = Gtk.Label(label="GNOME Top Bar")
        b2.add_css_class("quota-badge")
        b2.add_css_class("quota-badge-healthy")
        badge_box.append(b2)

        b3 = Gtk.Label(label="SQLite Analytics")
        b3.add_css_class("quota-badge")
        b3.add_css_class("quota-badge-warning")
        badge_box.append(b3)

        self.append(badge_box)
