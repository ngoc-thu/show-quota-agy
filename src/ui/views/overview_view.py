"""Overview tab view presenting active quota cards, progress bars, and countdowns."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib
from typing import Optional, Callable
from ...core.models import QuotaSnapshot, QuotaInfo, QuotaStatus, ConnectionState
from ...core.logger import logger


class OverviewView(Gtk.Box):
    """Overview tab content container."""

    def __init__(self, on_refresh_clicked: Optional[Callable[[], None]] = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        self.set_margin_top(16)
        self.set_margin_bottom(16)
        self.set_margin_start(20)
        self.set_margin_end(20)
        self.on_refresh_clicked = on_refresh_clicked

        self._build_ui()

    def _build_ui(self):
        # 1. Header Toolbar Box
        header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_lbl = Gtk.Label(label="Tổng quan Quota", xalign=0)
        title_lbl.add_css_class("title-2")
        subtitle_lbl = Gtk.Label(label="Theo dõi mức sử dụng và thời gian reset của các model Antigravity", xalign=0)
        subtitle_lbl.add_css_class("caption")
        subtitle_lbl.add_css_class("dim-label")
        title_box.append(title_lbl)
        title_box.append(subtitle_lbl)
        header_box.append(title_box)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        header_box.append(spacer)

        # Refresh button & spinner
        self.spinner = Gtk.Spinner()
        header_box.append(self.spinner)

        self.refresh_btn = Gtk.Button(label="↻ Làm mới")
        self.refresh_btn.add_css_class("quota-accent-button")
        if self.on_refresh_clicked:
            self.refresh_btn.connect("clicked", lambda _: self.on_refresh_clicked())
        header_box.append(self.refresh_btn)

        self.append(header_box)

        # 2. Status Banner (if offline/stale)
        self.banner = Adw.Banner()
        self.banner.set_button_label("Thử lại")
        if self.on_refresh_clicked:
            self.banner.connect("button-clicked", lambda _: self.on_refresh_clicked())
        self.append(self.banner)

        # 3. Scrollable Content Area
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self.content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        scrolled.set_child(self.content_box)
        self.append(scrolled)

        # 4. Footer Metadata Box
        self.footer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.footer_box.set_margin_top(8)

        self.conn_pill = Gtk.Label(label="🟢 Đã kết nối")
        self.conn_pill.add_css_class("status-pill")
        self.conn_pill.add_css_class("status-pill-connected")
        self.footer_box.append(self.conn_pill)

        self.updated_lbl = Gtk.Label(label="Cập nhật lần cuối: --:--:--", xalign=0)
        self.updated_lbl.add_css_class("caption")
        self.updated_lbl.add_css_class("dim-label")
        self.footer_box.append(self.updated_lbl)

        self.append(self.footer_box)

    def update_snapshot(self, snapshot: Optional[QuotaSnapshot]):
        """Renders new snapshot data onto widgets."""
        # Clear previous dynamic cards
        while child := self.content_box.get_first_child():
            self.content_box.remove(child)

        if not snapshot:
            empty_lbl = Gtk.Label(label="Đang tải thông tin quota...")
            empty_lbl.add_css_class("dim-label")
            self.content_box.append(empty_lbl)
            return

        # 1. Update Connection State & Banner
        if snapshot.connection_state == ConnectionState.CONNECTED:
            self.conn_pill.set_label("🟢 Đã kết nối")
            self.conn_pill.set_css_classes(["status-pill", "status-pill-connected"])
            self.banner.set_revealed(False)
        elif snapshot.connection_state == ConnectionState.AUTH_REQUIRED:
            self.conn_pill.set_label("🔐 Cần xác thực")
            self.conn_pill.set_css_classes(["status-pill", "status-pill-auth"])
            self.banner.set_title("Cần đăng nhập vào Antigravity (chạy 'agy') để tải quota.")
            self.banner.set_revealed(True)
        else:
            self.conn_pill.set_label("⚪ Ngoại tuyến")
            self.conn_pill.set_css_classes(["status-pill", "status-pill-offline"])
            self.banner.set_title("Không thể kết nối với Antigravity. Đang hiển thị dữ liệu lưu tạm.")
            self.banner.set_revealed(True)

        self.updated_lbl.set_label(f"Cập nhật lần cuối: {snapshot.last_updated_str or '--:--:--'}")

        # 2. Render Rate Limit Groups if present
        if snapshot.groups:
            groups_header = Gtk.Label(label="Hạn mức nhóm (Rate Limit Groups)", xalign=0)
            groups_header.add_css_class("heading")
            self.content_box.append(groups_header)

            group_flow = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            group_flow.set_homogeneous(True)

            for g in snapshot.groups:
                g_card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
                g_card.add_css_class("quota-card")

                g_title = Gtk.Label(label=g.display_name, xalign=0)
                g_title.add_css_class("quota-card-header")
                g_card.append(g_title)

                for b in g.buckets:
                    b_row = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
                    
                    b_head = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
                    b_name = Gtk.Label(label=b.display_name, xalign=0)
                    b_name.add_css_class("caption")
                    b_head.append(b_name)

                    b_spacer = Gtk.Box()
                    b_spacer.set_hexpand(True)
                    b_head.append(b_spacer)

                    b_pct = Gtk.Label(label=f"{b.percentage:.1f}%", xalign=1)
                    b_pct.add_css_class("caption")
                    b_pct.add_css_class("bold")
                    b_head.append(b_pct)

                    b_row.append(b_head)

                    # Progress bar
                    pbar = Gtk.ProgressBar()
                    pbar.set_fraction(b.remaining_fraction)
                    if b.percentage >= 70:
                        pbar.add_css_class("healthy")
                    elif b.percentage >= 30:
                        pbar.add_css_class("warning")
                    else:
                        pbar.add_css_class("critical")
                    b_row.append(pbar)

                    # Countdown
                    cd_lbl = Gtk.Label(label=f"Reset sau: {b.formatted_countdown()}", xalign=0)
                    cd_lbl.add_css_class("quota-meta-label")
                    b_row.append(cd_lbl)

                    g_card.append(b_row)

                group_flow.append(g_card)

            self.content_box.append(group_flow)

        # 3. Render Individual Models
        models_header = Gtk.Label(label="Chi tiết từng Model", xalign=0)
        models_header.add_css_class("heading")
        models_header.set_margin_top(8)
        self.content_box.append(models_header)

        # Sort models: default / recommended first, then by name
        sorted_models = sorted(
            snapshot.models.values(),
            key=lambda m: (not m.recommended, m.model_name),
        )

        for minfo in sorted_models:
            card = self._create_model_card(minfo, is_active=(minfo.model_id == snapshot.default_model_id))
            self.content_box.append(card)

    def _create_model_card(self, minfo: QuotaInfo, is_active: bool) -> Gtk.Box:
        card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        card.add_css_class("quota-card")

        # Top row: Name, badges, percentage
        top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        name_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        name_lbl = Gtk.Label(label=minfo.model_name, xalign=0)
        name_lbl.add_css_class("quota-model-title")
        name_box.append(name_lbl)

        if is_active:
            active_badge = Gtk.Label(label="Đang dùng")
            active_badge.add_css_class("quota-badge")
            active_badge.add_css_class("quota-badge-recommended")
            name_box.append(active_badge)

        if minfo.recommended:
            rec_badge = Gtk.Label(label="Recommended")
            rec_badge.add_css_class("quota-badge")
            rec_badge.add_css_class("quota-badge-recommended")
            name_box.append(rec_badge)

        if minfo.supports_thinking:
            think_badge = Gtk.Label(label="Thinking")
            think_badge.add_css_class("quota-badge")
            name_box.append(think_badge)

        info_box.append(name_box)

        id_lbl = Gtk.Label(label=minfo.model_id, xalign=0)
        id_lbl.add_css_class("quota-model-id")
        info_box.append(id_lbl)

        top_row.append(info_box)

        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        top_row.append(spacer)

        # Status badge & percentage
        status_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        pct_lbl = Gtk.Label(label=f"{minfo.percentage:.1f}%")
        pct_lbl.add_css_class("quota-pct-label")
        status_box.append(pct_lbl)

        badge_lbl = Gtk.Label(label=minfo.status.emoji)
        status_box.append(badge_lbl)
        top_row.append(status_box)

        card.append(top_row)

        # Progress bar
        pbar = Gtk.ProgressBar()
        pbar.set_fraction(minfo.remaining_fraction)
        if minfo.status == QuotaStatus.HEALTHY:
            pbar.add_css_class("healthy")
        elif minfo.status == QuotaStatus.WARNING:
            pbar.add_css_class("warning")
        else:
            pbar.add_css_class("critical")
        card.append(pbar)

        # Bottom row: Countdown / info
        bottom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        countdown_str = minfo.formatted_countdown()
        cd_lbl = Gtk.Label(
            label=f"Thời gian reset: {countdown_str}" if countdown_str != "N/A" else "Reset: Theo chu kỳ",
            xalign=0,
        )
        cd_lbl.add_css_class("quota-meta-label")
        bottom_row.append(cd_lbl)

        card.append(bottom_row)
        return card

    def set_loading(self, loading: bool):
        if loading:
            self.spinner.start()
            self.refresh_btn.set_sensitive(False)
        else:
            self.spinner.stop()
            self.refresh_btn.set_sensitive(True)
