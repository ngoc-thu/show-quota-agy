"""Central QuotaService orchestrating detection, fetching, caching, notifications, and persistence."""

import threading
import time
from datetime import datetime, timezone
from typing import Optional, Callable, List
from .models import (
    QuotaSnapshot,
    ConnectionState,
    AppSettings,
    QuotaStatus,
)
from .logger import logger
from ..antigravity.detector import AntigravityDetector
from ..antigravity.auth import AntigravityAuthProvider, AuthError
from ..antigravity.client import AntigravityClient, ClientError, ClientAuthError
from ..antigravity.parser import parse_quota_response
from ..storage.db import DatabaseManager
from ..storage.history_repo import HistoryRepository
from ..storage.settings_repo import SettingsRepository
from ..notifications.notifier import DesktopNotifier


class QuotaService:
    """Manages periodic quota updates, notifications, caching, and state listeners."""

    def __init__(
        self,
        db_manager: Optional[DatabaseManager] = None,
        auth_provider: Optional[AntigravityAuthProvider] = None,
        client: Optional[AntigravityClient] = None,
    ):
        self.db_manager = db_manager or DatabaseManager()
        self.history_repo = HistoryRepository(self.db_manager)
        self.settings_repo = SettingsRepository(self.db_manager)
        self.settings: AppSettings = self.settings_repo.load_settings()

        self.auth_provider = auth_provider or AntigravityAuthProvider()
        self.client = client or AntigravityClient(self.auth_provider)
        self.notifier = DesktopNotifier()

        self.current_snapshot: Optional[QuotaSnapshot] = None
        self._listeners: List[Callable[[QuotaSnapshot], None]] = []

        self._refresh_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    def add_listener(self, callback: Callable[[QuotaSnapshot], None]):
        """Registers a UI or daemon callback to be invoked upon snapshot update."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[QuotaSnapshot], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, snapshot: QuotaSnapshot):
        for cb in list(self._listeners):
            try:
                cb(snapshot)
            except Exception as e:
                logger.debug("Error in listener callback: %s", e)

    def refresh(self, force: bool = False) -> QuotaSnapshot:
        """Fetches live quota from Antigravity API and updates local state & history."""
        with self._lock:
            # Sync settings from SQLite DB
            try:
                self.settings = self.settings_repo.load_settings()
            except Exception as e:
                logger.debug("Failed to reload settings in refresh: %s", e)

            detection = AntigravityDetector.detect()
            logger.debug("Antigravity process detection: %s", detection.details)

            now = datetime.now(timezone.utc)
            try:
                # 1. Fetch live models and quotas
                models_json = self.client.fetch_available_models(force_refresh=force)

                # 2. Fetch quota summary groups
                summary_json = None
                try:
                    summary_json = self.client.fetch_quota_summary(force_refresh=force)
                except Exception as e:
                    logger.debug("Optional quota summary fetch failed: %s", e)

                # 3. Parse snapshot
                snapshot = parse_quota_response(
                    models_json=models_json,
                    summary_json=summary_json,
                    settings=self.settings,
                )
                snapshot.connection_state = ConnectionState.CONNECTED
                snapshot.is_stale = False
                snapshot.last_updated_str = now.strftime("%H:%M:%S")

                # Check for notification events
                if self.current_snapshot:
                    self._check_notifications(self.current_snapshot, snapshot)

                self.current_snapshot = snapshot

                # 4. Save to history
                try:
                    self.history_repo.record_snapshot(snapshot)
                except Exception as e:
                    logger.debug("Failed to record snapshot in SQLite: %s", e)

                logger.info(
                    "Quota refreshed successfully. Lowest: %.1f%%",
                    snapshot.get_display_percentage(
                        mode=self.settings.display_mode,
                        selected_model_id=self.settings.selected_model_override,
                    ),
                )

            except ClientAuthError as e:
                logger.warn("Authentication error: %s", e)
                snapshot = self._handle_fetch_error(
                    error_msg="Authentication required. Please log into Antigravity.",
                    state=ConnectionState.AUTH_REQUIRED,
                )
            except AuthError as e:
                logger.warn("Keyring Auth error: %s", e)
                snapshot = self._handle_fetch_error(
                    error_msg=str(e),
                    state=ConnectionState.AUTH_REQUIRED,
                )
            except ClientError as e:
                logger.warn("Client error: %s", e)
                state = ConnectionState.OFFLINE if not detection.is_running else ConnectionState.ERROR
                snapshot = self._handle_fetch_error(
                    error_msg=f"Failed to communicate with Antigravity: {e}",
                    state=state,
                )
            except Exception as e:
                logger.error("Unexpected error fetching quota: %s", e)
                snapshot = self._handle_fetch_error(
                    error_msg=f"Unexpected error: {e}",
                    state=ConnectionState.ERROR,
                )

            self._notify_listeners(snapshot)
            return snapshot

    def _handle_fetch_error(self, error_msg: str, state: ConnectionState) -> QuotaSnapshot:
        """Preserves cached snapshot if available while flagging it as stale."""
        now = datetime.now(timezone.utc)
        if self.current_snapshot:
            # Preserve last known data, mark stale
            self.current_snapshot.is_stale = True
            self.current_snapshot.connection_state = state
            self.current_snapshot.error_message = error_msg
            return self.current_snapshot

        # Create an empty initial snapshot
        snapshot = QuotaSnapshot(
            timestamp=now,
            connection_state=state,
            is_stale=True,
            last_updated_str="N/A",
            error_message=error_msg,
        )
        self.current_snapshot = snapshot
        return snapshot

    def _check_notifications(self, previous: QuotaSnapshot, current: QuotaSnapshot):
        """Dispatches desktop notifications if quota crossed critical/warning thresholds or reset."""
        if not self.settings.notify_low_quota and not self.settings.notify_reset:
            return

        for mid, curr_m in current.models.items():
            prev_m = previous.models.get(mid)
            if not prev_m:
                continue

            # Low quota notification (e.g. dropped into WARNING or CRITICAL)
            if self.settings.notify_low_quota:
                if prev_m.status == QuotaStatus.HEALTHY and curr_m.status in (QuotaStatus.WARNING, QuotaStatus.CRITICAL):
                    self.notifier.notify_low_quota(
                        model_name=curr_m.model_name,
                        percentage=curr_m.percentage,
                        reset_countdown=curr_m.formatted_countdown(),
                    )

            # Quota reset notification (e.g. quota increased significantly or went back to HEALTHY)
            if self.settings.notify_reset:
                if prev_m.percentage < self.settings.healthy_threshold and curr_m.percentage >= self.settings.healthy_threshold:
                    if curr_m.percentage - prev_m.percentage >= 15.0:
                        self.notifier.notify_quota_reset(
                            model_name=curr_m.model_name,
                            percentage=curr_m.percentage,
                        )

    def update_settings(self, new_settings: AppSettings):
        """Updates settings in memory and persists to database."""
        self.settings = new_settings
        self.settings_repo.save_settings(new_settings)
        if self.current_snapshot:
            self._notify_listeners(self.current_snapshot)
        logger.info("Application settings updated.")

    def start_auto_refresh(self):
        """Starts the background polling thread."""
        if self._refresh_thread and self._refresh_thread.is_alive():
            return

        self._stop_event.clear()
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True, name="QuotaAutoRefresh")
        self._refresh_thread.start()
        logger.info("Auto-refresh background worker started.")

    def stop_auto_refresh(self):
        """Signals the background polling thread to stop."""
        self._stop_event.set()
        if self._refresh_thread:
            self._refresh_thread.join(timeout=2.0)
            self._refresh_thread = None
        logger.info("Auto-refresh background worker stopped.")

    def _refresh_loop(self):
        # Initial immediate fetch
        self.refresh()

        while not self._stop_event.is_set():
            interval = self.settings.refresh_interval_sec
            if interval <= 0:
                # Manual mode: sleep and check again
                self._stop_event.wait(5.0)
                continue

            # Sleep in chunks to allow fast responsiveness to stop_event
            elapsed = 0
            while elapsed < interval and not self._stop_event.is_set():
                time.sleep(1.0)
                elapsed += 1

            if not self._stop_event.is_set():
                try:
                    self.refresh()
                except Exception as e:
                    logger.debug("Error in auto-refresh worker loop: %s", e)
