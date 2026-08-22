"""Settings tab view using Libadwaita Preferences components."""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw
from typing import Callable, Optional
from ...core.models import AppSettings, DisplayMode
from ...core.config import INTERVAL_OPTIONS
from ...autostart.manager import AutostartManager
from ...antigravity.detector import AntigravityDetector
from ...core.logger import logger


class SettingsView(Adw.PreferencesPage):
    """Settings preferences page for configuring application behavior."""

    def __init__(self, settings: AppSettings, on_save_callback: Optional[Callable[[AppSettings], None]] = None):
        super().__init__()
        self.settings = settings
        self.on_save_callback = on_save_callback

        self._build_ui()

    def _build_ui(self):
        # 1. General Preferences Group
        general_group = Adw.PreferencesGroup(title="Chung (General)")

        # Autostart Row
        self.autostart_row = Adw.SwitchRow(
            title="Khởi động cùng hệ thống",
            subtitle="Tự động chạy Antigravity Quota Monitor khi đăng nhập Ubuntu",
        )
        self.autostart_row.set_active(AutostartManager.is_enabled())
        self.autostart_row.connect("notify::active", self._on_autostart_toggled)
        general_group.add(self.autostart_row)

        # Show on Top Bar Row
        self.tray_row = Adw.SwitchRow(
            title="Hiển thị trên GNOME Top Bar",
            subtitle="Hiển thị icon và % quota trực tiếp trên thanh tác vụ trên cùng",
        )
        self.tray_row.set_active(self.settings.show_tray)
        self.tray_row.connect("notify::active", self._on_setting_changed)
        general_group.add(self.tray_row)

        # Refresh Interval Row
        self.interval_row = Adw.ComboRow(
            title="Chu kỳ làm mới (Refresh interval)",
            subtitle="Khoảng thời gian tự động lấy quota mới từ Antigravity",
        )
        interval_model = Gtk.StringList.new([label for _, label in INTERVAL_OPTIONS])
        self.interval_row.set_model(interval_model)
        
        # Select current interval
        curr_idx = 2  # default 60s
        for idx, (sec, _) in enumerate(INTERVAL_OPTIONS):
            if sec == self.settings.refresh_interval_sec:
                curr_idx = idx
                break
        self.interval_row.set_selected(curr_idx)
        self.interval_row.connect("notify::selected", self._on_interval_changed)
        general_group.add(self.interval_row)

        # Display Mode Row
        self.display_row = Adw.ComboRow(
            title="Hiển thị trên Top Bar",
            subtitle="Giá trị hiển thị trên thanh tác vụ",
        )
        display_options = [
            ("lowest", "Model có quota thấp nhất (Khuyến nghị)"),
            ("active", "Model mặc định / đang active"),
            ("gemini_5h", "Hạn mức 5h của Gemini"),
            ("claude_5h", "Hạn mức 5h của Claude/GPT"),
        ]
        display_model = Gtk.StringList.new([opt[1] for opt in display_options])
        self.display_row.set_model(display_model)
        for idx, (val, _) in enumerate(display_options):
            if val == self.settings.display_mode.value:
                self.display_row.set_selected(idx)
                break
        self.display_row.connect("notify::selected", self._on_display_mode_changed)
        general_group.add(self.display_row)

        self.add(general_group)

        # 2. Thresholds Group
        threshold_group = Adw.PreferencesGroup(title="Ngưỡng cảnh báo (Thresholds)")

        # Healthy Threshold
        self.healthy_row = Adw.SpinRow.new_with_range(1, 100, 5)
        self.healthy_row.set_title("Mức Tốt / Xanh (Healthy %)")
        self.healthy_row.set_subtitle("Quota lớn hơn hoặc bằng mức này sẽ hiển thị màu xanh")
        self.healthy_row.set_value(self.settings.healthy_threshold)
        self.healthy_row.connect("notify::value", self._on_setting_changed)
        threshold_group.add(self.healthy_row)

        # Warning Threshold
        self.warning_row = Adw.SpinRow.new_with_range(1, 100, 5)
        self.warning_row.set_title("Mức Cảnh báo / Vàng (Warning %)")
        self.warning_row.set_subtitle("Quota nằm giữa mức này và mức tốt sẽ hiển thị màu vàng")
        self.warning_row.set_value(self.settings.warning_threshold)
        self.warning_row.connect("notify::value", self._on_setting_changed)
        threshold_group.add(self.warning_row)

        self.add(threshold_group)

        # 3. Notification Group
        notif_group = Adw.PreferencesGroup(title="Thông báo Desktop (Notifications)")

        self.notif_low_row = Adw.SwitchRow(
            title="Cảnh báo quota thấp",
            subtitle="Gửi thông báo khi quota model giảm xuống dưới mức cảnh báo",
        )
        self.notif_low_row.set_active(self.settings.notify_low_quota)
        self.notif_low_row.connect("notify::active", self._on_setting_changed)
        notif_group.add(self.notif_low_row)

        self.notif_reset_row = Adw.SwitchRow(
            title="Thông báo khi quota reset",
            subtitle="Gửi thông báo khi quota hồi phục về mức tốt",
        )
        self.notif_reset_row.set_active(self.settings.notify_reset)
        self.notif_reset_row.connect("notify::active", self._on_setting_changed)
        notif_group.add(self.notif_reset_row)

        self.add(notif_group)

        # 4. Connection & Diagnostics Group
        conn_group = Adw.PreferencesGroup(title="Kết nối &amp; Chẩn đoán (Diagnostics)")

        detection = AntigravityDetector.detect()
        self.status_row = Adw.ActionRow(
            title="Trạng thái Antigravity",
            subtitle=detection.details,
        )
        conn_group.add(self.status_row)

        auth_row = Adw.ActionRow(
            title="Cơ chế xác thực (Authentication)",
            subtitle="Tự động qua GNOME Keyring / Secret Service (không yêu cầu nhập API key)",
        )
        conn_group.add(auth_row)

        self.add(conn_group)

    def _on_autostart_toggled(self, row, param):
        enabled = row.get_active()
        AutostartManager.set_enabled(enabled)
        self.settings.autostart = enabled
        self._save()

    def _on_interval_changed(self, row, param):
        idx = row.get_selected()
        if 0 <= idx < len(INTERVAL_OPTIONS):
            self.settings.refresh_interval_sec = INTERVAL_OPTIONS[idx][0]
            self._save()

    def _on_display_mode_changed(self, row, param):
        modes = [DisplayMode.LOWEST, DisplayMode.ACTIVE, DisplayMode.GEMINI_5H, DisplayMode.CLAUDE_5H]
        idx = row.get_selected()
        if 0 <= idx < len(modes):
            self.settings.display_mode = modes[idx]
            self._save()

    def _on_setting_changed(self, *args):
        self.settings.show_tray = self.tray_row.get_active()
        self.settings.healthy_threshold = int(self.healthy_row.get_value())
        self.settings.warning_threshold = int(self.warning_row.get_value())
        self.settings.notify_low_quota = self.notif_low_row.get_active()
        self.settings.notify_reset = self.notif_reset_row.get_active()
        self._save()

    def _save(self):
        if self.on_save_callback:
            self.on_save_callback(self.settings)
