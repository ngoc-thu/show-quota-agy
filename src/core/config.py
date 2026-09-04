"""Application configuration, constants, and paths."""

import os
from pathlib import Path

APP_NAME = "Antigravity Quota Monitor"
APP_ID = "org.google.antigravity.QuotaMonitor"
VERSION = "1.0.0"

# Directories
DATA_DIR = Path.home() / ".local" / "share" / "antigravity-quota-monitor"
CONFIG_DIR = Path.home() / ".config" / "antigravity-quota-monitor"
LOG_DIR = DATA_DIR / "logs"
DB_PATH = DATA_DIR / "quota_history.db"
AUTOSTART_DIR = Path.home() / ".config" / "autostart"
AUTOSTART_FILE = AUTOSTART_DIR / "antigravity-quota-monitor.desktop"

# Assets
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = PROJECT_ROOT / "assets"
ICON_PATH = ASSETS_DIR / "icons" / "antigravity-quota-monitor.svg"

# API Endpoints
# Antigravity CLI and IDE use daily-cloudcode-pa.googleapis.com as the active endpoint on Linux
API_BASE_URL = "https://daily-cloudcode-pa.googleapis.com/v1internal"
API_FALLBACK_BASE_URL = "https://cloudcode-pa.googleapis.com/v1internal"

API_FETCH_MODELS_URL = f"{API_BASE_URL}:fetchAvailableModels"
API_QUOTA_SUMMARY_URL = f"{API_BASE_URL}:retrieveUserQuotaSummary"
API_RETRIEVE_QUOTA_URL = f"{API_BASE_URL}:retrieveUserQuota"

API_FALLBACK_FETCH_MODELS_URL = f"{API_FALLBACK_BASE_URL}:fetchAvailableModels"
API_FALLBACK_QUOTA_SUMMARY_URL = f"{API_FALLBACK_BASE_URL}:retrieveUserQuotaSummary"
API_FALLBACK_RETRIEVE_QUOTA_URL = f"{API_FALLBACK_BASE_URL}:retrieveUserQuota"

# Secret Service Keyring constants
KEYRING_SERVICE = "gemini"
KEYRING_USERNAME = "antigravity"

# Default intervals and thresholds
DEFAULT_REFRESH_INTERVAL = 60  # seconds
INTERVAL_OPTIONS = [
    (15, "15 seconds"),
    (30, "30 seconds"),
    (60, "60 seconds (Default)"),
    (120, "2 minutes"),
    (300, "5 minutes"),
    (0, "Manual only"),
]

DEFAULT_HEALTHY_THRESHOLD = 70
DEFAULT_WARNING_THRESHOLD = 30
DEFAULT_CRITICAL_THRESHOLD = 10
