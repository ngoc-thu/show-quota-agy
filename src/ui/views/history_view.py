"""History tab view with responsive Cairo-based quota timeline analytics."""

import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk, GLib
import cairo
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from ...storage.history_repo import HistoryRepository
from ...core.logger import logger

TIME_RANGES = [
    (1.0, "1 Giờ"),
    (6.0, "6 Giờ"),
    (24.0, "24 Giờ"),
    (168.0, "7 Ngày"),
    (720.0, "30 Ngày"),
]

MODEL_COLORS = {
    "gemini": (0.486, 0.227, 0.929),   # Purple / Violet
    "claude": (0.850, 0.450, 0.150),   # Orange
    "gpt": (0.063, 0.725, 0.506),      # Green
    "default": (0.380, 0.560, 0.950),  # Blue
}


class HistoryView(Gtk.Box):
    """Historical timeline analytics and chart container."""

    def __init__(self, history_repo: HistoryRepository):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.history_repo = history_repo
        self.selected_hours = 24.0
        self.selected_model: Optional[str] = None
        self.history_data: List[Dict[str, Any]] = []

        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(20)
        self.set_margin_end(20)

        self._build_ui()

    def _build_ui(self):
        # 1. Header Toolbar Box
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label="Lịch sử Quota", xalign=0)
        title_lbl.add_css_class("title-2")
        sub_lbl = Gtk.Label(label="Biểu đồ biến động quota theo thời gian", xalign=0)
        sub_lbl.add_css_class("caption")
        sub_lbl.add_css_class("dim-label")
        title_box.append(title_lbl)
        title_box.append(sub_lbl)
        header_box.append(title_box)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header_box.append(spacer)

        # Range Selector Dropdown
        range_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        range_lbl = Gtk.Label(label="Khoảng thời gian:")
        range_lbl.add_css_class("caption")
        range_box.append(range_lbl)

        self.range_combo = Gtk.DropDown.new_from_strings([label for _, label in TIME_RANGES])
        self.range_combo.set_selected(2)  # Default 24h
        self.range_combo.connect("notify::selected", self._on_range_changed)
        range_box.append(self.range_combo)
        header_box.append(range_box)

        self.append(header_box)

        # 2. Cairo Drawing Area for Chart
        chart_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        chart_card.add_css_class("quota-card")
        chart_card.set_vexpand(True)

        self.drawing_area = Gtk.DrawingArea()
        self.drawing_area.set_content_height(240)
        self.drawing_area.set_vexpand(True)
        self.drawing_area.set_hexpand(True)
        self.drawing_area.set_draw_func(self._draw_chart)
        chart_card.append(self.drawing_area)

        self.append(chart_card)

        # 3. Recent History List Table
        table_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        table_card.add_css_class("quota-card")
        table_card.set_vexpand(True)

        t_title = Gtk.Label(label="Dữ liệu gần đây", xalign=0)
        t_title.add_css_class("heading")
        table_card.append(t_title)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.log_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        scrolled.set_child(self.log_box)
        table_card.append(scrolled)

        self.append(table_card)

    def load_data(self):
        """Fetches history from SQLite and refreshes chart and table."""
        self.history_data = self.history_repo.get_history(hours=self.selected_hours)
        self.drawing_area.queue_draw()
        self._update_table()

    def _on_range_changed(self, dropdown, param):
        idx = dropdown.get_selected()
        if 0 <= idx < len(TIME_RANGES):
            self.selected_hours = TIME_RANGES[idx][0]
            self.load_data()

    def _update_table(self):
        while child := self.log_box.get_first_child():
            self.log_box.remove(child)

        if not self.history_data:
            empty = Gtk.Label(label="Chưa có dữ liệu lịch sử.")
            empty.add_css_class("dim-label")
            self.log_box.append(empty)
            return

        # Show latest 25 entries in reverse order
        for row in reversed(self.history_data[-25:]):
            row_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

            ts_str = row.get("timestamp", "").split("T")[-1].split(".")[0]
            ts_lbl = Gtk.Label(label=ts_str, xalign=0)
            ts_lbl.add_css_class("caption")
            ts_lbl.add_css_class("dim-label")
            row_box.append(ts_lbl)

            name_lbl = Gtk.Label(label=row.get("model_name", "Model"), xalign=0)
            name_lbl.add_css_class("body")
            row_box.append(name_lbl)

            spacer = Gtk.Box()
            spacer.set_hexpand(True)
            row_box.append(spacer)

            pct = row.get("percentage", 0.0)
            pct_lbl = Gtk.Label(label=f"{pct:.1f}%", xalign=1)
            pct_lbl.add_css_class("bold")
            if pct >= 70:
                pct_lbl.add_css_class("quota-badge-healthy")
            elif pct >= 30:
                pct_lbl.add_css_class("quota-badge-warning")
            else:
                pct_lbl.add_css_class("quota-badge-critical")
            row_box.append(pct_lbl)

            self.log_box.append(row_box)

    def _draw_chart(self, area, cr, width, height):
        """Renders timeline axes, grid, and quota percentage lines using Cairo."""
        # Background
        cr.set_source_rgb(0.12, 0.12, 0.14)
        cr.paint()

        margin_left = 45
        margin_right = 20
        margin_top = 20
        margin_bottom = 35

        plot_w = width - margin_left - margin_right
        plot_h = height - margin_top - margin_bottom

        if plot_w <= 0 or plot_h <= 0:
            return

        # Draw Grid lines for 0%, 25%, 50%, 75%, 100%
        cr.set_line_width(0.7)
        for pct in [0, 25, 50, 75, 100]:
            y = margin_top + plot_h - (pct / 100.0) * plot_h
            cr.set_source_rgba(0.3, 0.3, 0.35, 0.4)
            cr.move_to(margin_left, y)
            cr.line_to(margin_left + plot_w, y)
            cr.stroke()

            # Axis label
            cr.set_source_rgba(0.7, 0.7, 0.75, 0.8)
            cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(10)
            cr.move_to(5, y + 3)
            cr.show_text(f"{pct}%")

        if not self.history_data:
            cr.set_source_rgba(0.6, 0.6, 0.6, 0.7)
            cr.set_font_size(13)
            cr.move_to(width / 2 - 80, height / 2)
            cr.show_text("Chưa có đủ dữ liệu lịch sử")
            return

        # Group data points by model_id
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for d in self.history_data:
            mid = d["model_id"]
            grouped.setdefault(mid, []).append(d)

        # Plot each model curve
        for mid, points in grouped.items():
            if len(points) < 1:
                continue

            # Determine color
            mid_lower = mid.lower()
            if "gemini" in mid_lower:
                color = MODEL_COLORS["gemini"]
            elif "claude" in mid_lower:
                color = MODEL_COLORS["claude"]
            elif "gpt" in mid_lower:
                color = MODEL_COLORS["gpt"]
            else:
                color = MODEL_COLORS["default"]

            cr.set_source_rgb(*color)
            cr.set_line_width(2.2)

            for i, p in enumerate(points):
                pct = max(0.0, min(100.0, p.get("percentage", 0.0)))
                x = margin_left + (i / max(1, len(points) - 1)) * plot_w
                y = margin_top + plot_h - (pct / 100.0) * plot_h

                if i == 0:
                    cr.move_to(x, y)
                else:
                    cr.line_to(x, y)

            cr.stroke()

            # Draw dots
            for i, p in enumerate(points):
                pct = max(0.0, min(100.0, p.get("percentage", 0.0)))
                x = margin_left + (i / max(1, len(points) - 1)) * plot_w
                y = margin_top + plot_h - (pct / 100.0) * plot_h
                cr.arc(x, y, 3.0, 0, 2 * 3.14159)
                cr.fill()
