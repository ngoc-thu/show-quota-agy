"""Main GTK4 / Libadwaita application window with sidebar navigation."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib
from typing import Optional
from ..core.service import QuotaService
from ..core.models import QuotaSnapshot, AppSettings
from ..core.config import APP_NAME
from ..core.logger import logger
from .style import APPLICATION_CSS
from .views.overview_view import OverviewView
from .views.history_view import HistoryView
from .views.settings_view import SettingsView
from .views.about_view import AboutView


class MainWindow(Adw.ApplicationWindow):
    """Main application dashboard window."""

    def __init__(self, app: Adw.Application, service: QuotaService, initial_tab: Optional[str] = None):
        super().__init__(application=app, title=APP_NAME)
        self.service = service
        self.set_default_size(880, 640)
        self.set_size_request(600, 480)

        # Apply CSS style provider
        self._apply_css()

        # Build UI layout
        self._build_layout(initial_tab)

        # Connect to service updates
        self.service.add_listener(self._on_snapshot_updated)

        # Load initial snapshot and history
        if self.service.current_snapshot:
            self.overview_view.update_snapshot(self.service.current_snapshot)
        else:
            self._trigger_refresh()

        self.history_view.load_data()

    def _apply_css(self):
        display = Gtk.Widget.get_display(self)
        if display:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(APPLICATION_CSS.encode("utf-8"))
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
            )

    def _build_layout(self, initial_tab: Optional[str]):
        # Main split view: Sidebar + Content
        split_view = Adw.NavigationSplitView()
        split_view.set_min_sidebar_width(200)
        split_view.set_max_sidebar_width(240)

        # 1. Sidebar page
        sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        sidebar_box.add_css_class("quota-sidebar")
        sidebar_box.set_margin_top(12)
        sidebar_box.set_margin_bottom(12)
        sidebar_box.set_margin_start(10)
        sidebar_box.set_margin_end(10)

        # App Brand Header
        brand_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        brand_box.set_margin_start(8)
        brand_box.set_margin_bottom(8)
        
        rocket_lbl = Gtk.Label(label="🚀")
        rocket_lbl.add_css_class("title-3")
        brand_box.append(rocket_lbl)

        brand_lbl = Gtk.Label(label="Antigravity", xalign=0)
        brand_lbl.add_css_class("heading")
        brand_lbl.add_css_class("bold")
        brand_box.append(brand_lbl)
        sidebar_box.append(brand_box)

        # Navigation ListBox
        self.nav_list = Gtk.ListBox()
        self.nav_list.add_css_class("navigation-sidebar")
        self.nav_list.set_selection_mode(Gtk.SelectionMode.SINGLE)

        nav_items = [
            ("overview", "🏠  Tổng quan"),
            ("history", "📊  Lịch sử"),
            ("settings", "⚙  Cài đặt"),
            ("about", "ℹ  Giới thiệu"),
        ]

        self.row_map = {}
        for tag, title in nav_items:
            row = Gtk.ListBoxRow()
            lbl = Gtk.Label(label=title, xalign=0)
            lbl.set_margin_top(8)
            lbl.set_margin_bottom(8)
            lbl.set_margin_start(12)
            row.set_child(lbl)
            self.nav_list.append(row)
            self.row_map[tag] = row

        self.nav_list.connect("row-selected", self._on_nav_selected)
        sidebar_box.append(self.nav_list)

        # 1. Sidebar ToolbarView with HeaderBar
        sidebar_toolbar = Adw.ToolbarView()
        sidebar_header = Adw.HeaderBar()
        sidebar_header.set_show_end_title_buttons(False)
        sidebar_header.set_show_start_title_buttons(True)
        sidebar_toolbar.add_top_bar(sidebar_header)
        sidebar_toolbar.set_content(sidebar_box)

        sidebar_page = Adw.NavigationPage.new(sidebar_toolbar, "Menu")
        split_view.set_sidebar(sidebar_page)

        # 2. Content ViewStack wrapped in ToolbarView with HeaderBar
        self.view_stack = Adw.ViewStack()

        # Overview View
        self.overview_view = OverviewView(on_refresh_clicked=self._trigger_refresh)
        self.view_stack.add_named(self.overview_view, "overview")

        # History View
        self.history_view = HistoryView(self.service.history_repo)
        self.view_stack.add_named(self.history_view, "history")

        # Settings View
        self.settings_view = SettingsView(
            settings=self.service.settings,
            on_save_callback=self._on_settings_saved,
            models=self.service.current_snapshot.models if self.service.current_snapshot else None,
        )
        self.view_stack.add_named(self.settings_view, "settings")

        # About View
        self.about_view = AboutView()
        self.view_stack.add_named(self.about_view, "about")

        content_toolbar = Adw.ToolbarView()
        self.content_header = Adw.HeaderBar()
        self.content_header.set_show_end_title_buttons(True)
        self.content_header.set_show_start_title_buttons(False)

        self.window_title = Adw.WindowTitle(title=APP_NAME, subtitle="Tổng quan")
        self.content_header.set_title_widget(self.window_title)

        content_toolbar.add_top_bar(self.content_header)
        content_toolbar.set_content(self.view_stack)

        content_page = Adw.NavigationPage.new(content_toolbar, "Content")
        split_view.set_content(content_page)

        self.set_content(split_view)

        # Set default active tab
        target = initial_tab if initial_tab in self.row_map else "overview"
        self.nav_list.select_row(self.row_map[target])
        self.view_stack.set_visible_child_name(target)
        self._update_title_for_tag(target)

    def _update_title_for_tag(self, tag: str):
        subtitles = {
            "overview": "Tổng quan",
            "history": "Lịch sử",
            "settings": "Cài đặt",
            "about": "Giới thiệu",
        }
        if tag in subtitles:
            self.window_title.set_subtitle(subtitles[tag])

    def _on_nav_selected(self, listbox, row):
        if not row:
            return
        for tag, r in self.row_map.items():
            if r == row:
                self.view_stack.set_visible_child_name(tag)
                self._update_title_for_tag(tag)
                if tag == "history":
                    self.history_view.load_data()
                break

    def _on_snapshot_updated(self, snapshot: QuotaSnapshot):
        GLib.idle_add(self._apply_snapshot, snapshot)

    def _apply_snapshot(self, snapshot: QuotaSnapshot):
        self.overview_view.update_snapshot(snapshot)
        self.overview_view.set_loading(False)
        if snapshot and snapshot.models:
            self.settings_view.update_models(snapshot.models)

    def _trigger_refresh(self):
        self.overview_view.set_loading(True)
        import threading
        threading.Thread(target=lambda: self.service.refresh(force=True), daemon=True).start()

    def _on_settings_saved(self, new_settings: AppSettings):
        self.service.update_settings(new_settings)
