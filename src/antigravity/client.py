"""HTTP client for Google CloudCode PA / Antigravity prediction service."""

import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional
from ..core.logger import logger
from ..core.config import (
    API_FETCH_MODELS_URL,
    API_QUOTA_SUMMARY_URL,
    API_FALLBACK_FETCH_MODELS_URL,
    API_FALLBACK_QUOTA_SUMMARY_URL,
)
from .auth import AntigravityAuthProvider, AuthError


class ClientError(Exception):
    """Base error for API communication."""
    pass


class ClientAuthError(ClientError):
    """Authentication required or token expired."""
    pass


class ClientRateLimitError(ClientError):
    """Endpoint throttled."""
    pass


class ClientNetworkError(ClientError):
    """Network connection or DNS failure."""
    pass


class AntigravityClient:
    """Sends authenticated requests to CloudCode PA prediction service endpoints."""

    def __init__(self, auth_provider: Optional[AntigravityAuthProvider] = None, timeout_sec: int = 10):
        self.auth_provider = auth_provider or AntigravityAuthProvider()
        self.timeout_sec = timeout_sec

    def fetch_available_models(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Queries :fetchAvailableModels endpoint with fallback and auto-refresh on 401."""
        try:
            token = self.auth_provider.get_access_token(force_refresh=force_refresh)
            return self._fetch_with_fallback(API_FETCH_MODELS_URL, API_FALLBACK_FETCH_MODELS_URL, token)
        except ClientAuthError:
            logger.info("Access token rejected (401), reloading from GNOME Keyring...")
            token = self.auth_provider.get_access_token(force_refresh=True)
            return self._fetch_with_fallback(API_FETCH_MODELS_URL, API_FALLBACK_FETCH_MODELS_URL, token)

    def fetch_quota_summary(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Queries :retrieveUserQuotaSummary endpoint with fallback and auto-refresh on 401."""
        try:
            token = self.auth_provider.get_access_token(force_refresh=force_refresh)
            return self._fetch_with_fallback(API_QUOTA_SUMMARY_URL, API_FALLBACK_QUOTA_SUMMARY_URL, token)
        except ClientAuthError:
            logger.info("Access token rejected (401), reloading from GNOME Keyring...")
            token = self.auth_provider.get_access_token(force_refresh=True)
            return self._fetch_with_fallback(API_QUOTA_SUMMARY_URL, API_FALLBACK_QUOTA_SUMMARY_URL, token)

    def _fetch_with_fallback(self, primary_url: str, fallback_url: str, token: str) -> Dict[str, Any]:
        try:
            return self._post_json(primary_url, token)
        except (ClientNetworkError, ClientError) as e:
            if isinstance(e, (ClientAuthError, ClientRateLimitError)):
                raise
            logger.debug("Primary endpoint failed (%s), trying fallback: %s", e, fallback_url)
            return self._post_json(fallback_url, token)

    def _post_json(self, url: str, token: str, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        req_data = json.dumps(body or {}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "User-Agent": "antigravity-cli/1.0",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                raw = resp.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as e:
            if e.code == 401 or e.code == 403:
                self.auth_provider.invalidate_cache()
                raise ClientAuthError(f"HTTP {e.code}: Authentication token rejected or expired.")
            elif e.code == 429:
                raise ClientRateLimitError(f"HTTP 429: Quota endpoint rate limited.")
            raise ClientError(f"HTTP {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise ClientNetworkError(f"Network error: {e.reason}")
        except json.JSONDecodeError as e:
            raise ClientError(f"Invalid JSON response from server: {e}")
        except Exception as e:
            raise ClientError(f"Unexpected error: {e}")
