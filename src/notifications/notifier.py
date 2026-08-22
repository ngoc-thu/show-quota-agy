"""Desktop notifications manager using DBus org.freedesktop.Notifications."""

import time
import subprocess
from typing import Optional, Dict
from ..core.logger import logger
from ..core.config import APP_NAME


class DesktopNotifier:
    """Sends native desktop notifications via DBus with debounce control."""

    def __init__(self):
        self._last_notified: Dict[str, float] = {}
        self._cooldown_seconds = 180.0  # 3 minutes cooldown per notification key

    def notify_low_quota(self, model_name: str, percentage: float, reset_countdown: str):
        key = f"low_{model_name}"
        if not self._can_notify(key):
            return

        title = f"🚀 {APP_NAME}"
        body = f"<b>{model_name}</b> quota is low: <b>{percentage:.1f}%</b> remaining.\nReset in {reset_countdown}."
        self._send_notification(title, body, urgency=1)  # Normal/Warning
        self._mark_notified(key)

    def notify_quota_reset(self, model_name: str, percentage: float):
        key = f"reset_{model_name}"
        if not self._can_notify(key):
            return

        title = f"🚀 {APP_NAME}"
        body = f"<b>{model_name}</b> quota has replenished: <b>{percentage:.1f}%</b> available."
        self._send_notification(title, body, urgency=0)  # Low/Normal
        self._mark_notified(key)

    def _can_notify(self, key: str) -> bool:
        now = time.time()
        last = self._last_notified.get(key, 0.0)
        return (now - last) >= self._cooldown_seconds

    def _mark_notified(self, key: str):
        self._last_notified[key] = time.time()

    def _send_notification(self, title: str, body: str, urgency: int = 1):
        try:
            import dbus
            bus = dbus.SessionBus()
            notify_obj = bus.get_object("org.freedesktop.Notifications", "/org/freedesktop/Notifications")
            notify_iface = dbus.Interface(notify_obj, "org.freedesktop.Notifications")

            # Notify method signature:
            # (app_name, replaces_id, app_icon, summary, body, actions, hints, expire_timeout)
            notify_iface.Notify(
                APP_NAME,
                0,
                "dialog-information",
                title,
                body,
                [],
                {"urgency": dbus.Byte(urgency)},
                5000,  # 5 seconds
            )
            logger.debug("Sent desktop notification: %s - %s", title, body)
        except Exception as e:
            # Fallback to notify-send CLI
            try:
                subprocess.run(["notify-send", "-a", APP_NAME, title, body], check=False)
            except Exception:
                logger.debug("Could not send desktop notification: %s", e)
