"""Top Bar popup menu construction using GTK3 menu widgets for AppIndicator."""

from datetime import datetime, timezone
from typing import Optional, Callable
from ..core.models import QuotaSnapshot, ConnectionState
from ..core.config import APP_NAME
from ..core.logger import logger


def create_progress_bar_str(pct: float, width: int = 6) -> str:
    """Generates ASCII block progress representation e.g. ████░░."""
    pct = max(0.0, min(100.0, pct))
    filled = int(round((pct / 100.0) * width))
    empty = width - filled
    return "█" * filled + "░" * empty


def format_reset_time(reset_dt: Optional[datetime], now: Optional[datetime] = None) -> str:
    """Formats reset datetime into a user-friendly countdown and clock time."""
    if not reset_dt:
        return "N/A"
    if now is None:
        now = datetime.now(timezone.utc)
    diff = reset_dt - now
    total_seconds = int(diff.total_seconds())
    if total_seconds <= 0:
        return "Sẵn sàng reset"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        countdown = f"{days}d {hours}h"
    elif hours > 0:
        countdown = f"{hours}h {minutes}m"
    else:
        countdown = f"{minutes}m {total_seconds % 60}s"

    try:
        local_dt = reset_dt.astimezone()
        now_local = now.astimezone()
        if local_dt.date() == now_local.date():
            time_str = local_dt.strftime("%H:%M")
        else:
            time_str = local_dt.strftime("%H:%M %d/%m")
        return f"{countdown} ({time_str})"
    except Exception:
        return countdown


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
                header_text += "  🟢 Đang hoạt động"
            elif snapshot.connection_state == ConnectionState.AUTH_REQUIRED:
                header_text += "  🔐 Yêu cầu đăng nhập"
            elif snapshot.connection_state == ConnectionState.OFFLINE:
                header_text += "  ⚪ Ngoại tuyến"
            else:
                header_text += "  ⚠ Lỗi kết nối"

        header_item = Gtk.MenuItem(label=header_text)
        header_item.set_sensitive(False)
        menu.append(header_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 2. Group Buckets (5h & 7d limits with clear reset times)
        if snapshot and snapshot.groups:
            for g in snapshot.groups:
                g_header = Gtk.MenuItem(label=f"📊 {g.display_name}:")
                g_header.set_sensitive(False)
                menu.append(g_header)

                for b in g.buckets:
                    bar = create_progress_bar_str(b.percentage, width=6)
                    reset_str = format_reset_time(b.reset_time)
                    w_name = "5h (5 Giờ)" if "5h" in b.window.lower() else ("7d (Tuần)" if "week" in b.window.lower() else b.window)
                    b_label = f"   • {w_name:<11} [{bar}] {b.percentage:4.1f}%  ⏳ Reset: {reset_str}"
                    b_item = Gtk.MenuItem(label=b_label)
                    b_item.set_sensitive(False)
                    menu.append(b_item)

            menu.append(Gtk.SeparatorMenuItem())

        # 3. Model Quotas
        if snapshot and snapshot.models:
            models_header = Gtk.MenuItem(label="🤖 Chi tiết các Model:")
            models_header.set_sensitive(False)
            menu.append(models_header)

            # Filter out internal backend slot names
            visible_models = [
                m for m in snapshot.models.values()
                if not m.model_id.startswith("chat_") and not m.model_id.startswith("tab_")
            ]
            # Sort models: recommended first, then lowest percentage, then name
            sorted_models = sorted(
                visible_models,
                key=lambda m: (not m.recommended, m.percentage, m.model_name),
            )

            # Limit top models to keep popup clean and readable
            for minfo in sorted_models[:6]:
                bar = create_progress_bar_str(minfo.percentage, width=5)
                reset_str = format_reset_time(minfo.reset_time)
                label = f"   • {minfo.model_name:<24} [{bar}] {minfo.percentage:4.1f}% {minfo.status.emoji}"
                if reset_str != "N/A":
                    label += f"  ⏳ {reset_str}"

                item = Gtk.MenuItem(label=label)
                item.set_sensitive(False)
                menu.append(item)

            menu.append(Gtk.SeparatorMenuItem())

            # Timestamp
            up_text = f"🕒 Cập nhật: {snapshot.last_updated_str}"
            if snapshot.is_stale:
                up_text += " (dữ liệu cũ)"
            up_item = Gtk.MenuItem(label=up_text)
            up_item.set_sensitive(False)
            menu.append(up_item)

        elif not (snapshot and snapshot.groups):
            empty_item = Gtk.MenuItem(label="Không có dữ liệu hạn mức")
            empty_item.set_sensitive(False)
            menu.append(empty_item)

        menu.append(Gtk.SeparatorMenuItem())

        # 4. Actions
        refresh_item = Gtk.MenuItem(label="↻ Làm mới ngay (Refresh)")
        refresh_item.connect("activate", lambda _: on_refresh())
        menu.append(refresh_item)

        dash_item = Gtk.MenuItem(label="🏠 Mở bảng điều khiển (Dashboard)")
        dash_item.connect("activate", lambda _: on_open_dashboard())
        menu.append(dash_item)

        settings_item = Gtk.MenuItem(label="⚙ Cài đặt (Settings)")
        settings_item.connect("activate", lambda _: on_open_settings())
        menu.append(settings_item)

        menu.append(Gtk.SeparatorMenuItem())

        quit_item = Gtk.MenuItem(label="✕ Thoát (Quit)")
        quit_item.connect("activate", lambda _: on_quit())
        menu.append(quit_item)

        menu.show_all()
        return menu
