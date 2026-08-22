"""Antigravity authentication and credential provider using GNOME Secret Service and DBus."""

import json
import time
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Optional, Dict, Any, Tuple
from ..core.logger import logger
from ..core.config import KEYRING_SERVICE, KEYRING_USERNAME


class AuthError(Exception):
    """Raised when authentication credentials cannot be loaded or refreshed."""
    pass


class AntigravityAuthProvider:
    """Manages token extraction from GNOME Keyring and handles token lifecycle."""

    def __init__(self, service_name: str = KEYRING_SERVICE, username: str = KEYRING_USERNAME):
        self.service_name = service_name
        self.username = username
        self._cached_token: Optional[str] = None
        self._cached_expiry: Optional[datetime] = None
        self._auth_method: Optional[str] = None

    def get_access_token(self, force_refresh: bool = False) -> str:
        """Retrieves a valid access token, extracting from Secret Service or refreshing if needed."""
        # Check cache if not forcing refresh
        if not force_refresh and self._cached_token and self._cached_expiry:
            now = datetime.now(timezone.utc)
            # If token has at least 60 seconds of validity remaining
            if (self._cached_expiry - now).total_seconds() > 60:
                return self._cached_token

        # Load from GNOME Keyring
        token_data, auth_method = self._load_from_secret_service()
        self._auth_method = auth_method

        access_token = token_data.get("access_token")
        if not access_token:
            raise AuthError("No access_token found in Antigravity keyring credentials.")

        expiry_str = token_data.get("expiry")
        if expiry_str:
            try:
                # Format: 2026-08-21T17:39:28.948475876+07:00 or ISO format
                # Python 3.11+ fromisoformat handles fractional seconds and offsets
                clean_expiry = expiry_str.split("+")[0].split("Z")[0]
                if "." in clean_expiry and len(clean_expiry.split(".")[1]) > 6:
                    # Truncate nanoseconds to microseconds
                    base, nano = clean_expiry.split(".")
                    clean_expiry = f"{base}.{nano[:6]}"
                self._cached_expiry = datetime.fromisoformat(clean_expiry).replace(tzinfo=timezone.utc)
            except Exception as e:
                logger.debug("Could not parse token expiry timestamp %s: %s", expiry_str, e)
                self._cached_expiry = None

        self._cached_token = access_token
        logger.debug("Successfully loaded Antigravity token from Keyring.")
        return access_token

    def _load_from_secret_service(self) -> Tuple[Dict[str, Any], str]:
        """Loads the credential JSON directly from org.freedesktop.secrets via DBus."""
        try:
            import dbus
        except ImportError:
            raise AuthError("Python 'dbus' library is not installed.")

        try:
            bus = dbus.SessionBus()
            service = bus.get_object("org.freedesktop.secrets", "/org/freedesktop/secrets")
            iface = dbus.Interface(service, "org.freedesktop.Secret.Service")

            # Open a plain unencrypted session on session bus
            session_path = iface.OpenSession("plain", "")[1]

            search_query = {"service": self.service_name, "username": self.username}
            search_res, locked = iface.SearchItems(search_query)

            if not search_res:
                raise AuthError(
                    f"No credentials found in GNOME Keyring for service='{self.service_name}', username='{self.username}'. "
                    "Make sure you are logged into Antigravity ('agy')."
                )

            item_path = search_res[0]
            item_obj = bus.get_object("org.freedesktop.secrets", item_path)
            item_iface = dbus.Interface(item_obj, "org.freedesktop.Secret.Item")

            secret_tuple = item_iface.GetSecret(session_path)
            # Secret tuple format: (session_path, parameters, secret_bytes, content_type)
            secret_bytes = bytes(secret_tuple[2])
            secret_str = secret_bytes.decode("utf-8")
            payload = json.loads(secret_str)

            token_data = payload.get("token", {})
            auth_method = payload.get("auth_method", "consumer")
            return token_data, auth_method

        except dbus.DBusException as e:
            raise AuthError(f"DBus Secret Service error: {e.get_dbus_message()}")
        except Exception as e:
            raise AuthError(f"Failed to load Antigravity token: {e}")

    @property
    def auth_method(self) -> Optional[str]:
        return self._auth_method
