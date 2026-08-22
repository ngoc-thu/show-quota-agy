"""Data models for Antigravity Quota Monitor."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Any
import json


class QuotaStatus(str, Enum):
    HEALTHY = "HEALTHY"    # >= healthy_threshold (default 70%)
    WARNING = "WARNING"    # >= warning_threshold (default 30%)
    CRITICAL = "CRITICAL"  # < warning_threshold (or <= critical_threshold)
    UNKNOWN = "UNKNOWN"

    @property
    def color_hex(self) -> str:
        if self == QuotaStatus.HEALTHY:
            return "#10B981"  # Emerald green
        elif self == QuotaStatus.WARNING:
            return "#F59E0B"  # Amber yellow
        elif self == QuotaStatus.CRITICAL:
            return "#EF4444"  # Red
        return "#6B7280"      # Gray

    @property
    def emoji(self) -> str:
        if self == QuotaStatus.HEALTHY:
            return "🟢"
        elif self == QuotaStatus.WARNING:
            return "🟡"
        elif self == QuotaStatus.CRITICAL:
            return "🔴"
        return "⚪"


class ConnectionState(str, Enum):
    CONNECTED = "CONNECTED"
    CONNECTING = "CONNECTING"
    OFFLINE = "OFFLINE"
    AUTH_REQUIRED = "AUTH_REQUIRED"
    ERROR = "ERROR"

    @property
    def label(self) -> str:
        if self == ConnectionState.CONNECTED:
            return "🟢 Connected"
        elif self == ConnectionState.CONNECTING:
            return "🔄 Connecting..."
        elif self == ConnectionState.AUTH_REQUIRED:
            return "🔐 Authentication Required"
        elif self == ConnectionState.OFFLINE:
            return "⚪ Antigravity Offline"
        return "⚠ Connection Error"


class DisplayMode(str, Enum):
    LOWEST = "lowest"       # Lowest available quota across active models
    ACTIVE = "active"       # Default agent model quota
    GEMINI_5H = "gemini_5h" # Gemini 5-hour limit
    CLAUDE_5H = "claude_5h" # Claude/GPT 5-hour limit


@dataclass
class QuotaBucket:
    bucket_id: str
    display_name: str
    window: str  # 'weekly', '5h', etc.
    remaining_fraction: float
    percentage: float
    reset_time: Optional[datetime] = None
    reset_time_iso: Optional[str] = None
    description: str = ""

    def formatted_countdown(self, now: Optional[datetime] = None) -> str:
        if not self.reset_time:
            return "N/A"
        if now is None:
            now = datetime.now(timezone.utc)
        diff = self.reset_time - now
        total_seconds = int(diff.total_seconds())
        if total_seconds <= 0:
            return "Ready to reset"
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if days > 0:
            return f"{days}d {hours}h"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m {seconds}s"


@dataclass
class QuotaGroup:
    group_id: str
    display_name: str
    description: str
    buckets: List[QuotaBucket] = field(default_factory=list)
    models_included: List[str] = field(default_factory=list)

    @property
    def lowest_fraction(self) -> float:
        if not self.buckets:
            return 1.0
        return min(b.remaining_fraction for b in self.buckets)

    @property
    def lowest_percentage(self) -> float:
        return round(self.lowest_fraction * 100, 1)


@dataclass
class QuotaInfo:
    model_id: str
    model_name: str
    remaining_fraction: float
    percentage: float
    reset_time: Optional[datetime] = None
    reset_time_iso: Optional[str] = None
    status: QuotaStatus = QuotaStatus.UNKNOWN
    supports_thinking: bool = False
    recommended: bool = False
    category: str = "General"

    def formatted_countdown(self, now: Optional[datetime] = None) -> str:
        if not self.reset_time:
            return "N/A"
        if now is None:
            now = datetime.now(timezone.utc)
        diff = self.reset_time - now
        total_seconds = int(diff.total_seconds())
        if total_seconds <= 0:
            return "Ready to reset"
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        if days > 0:
            return f"{days}d {hours}h"
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m {seconds}s"


@dataclass
class QuotaSnapshot:
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    models: Dict[str, QuotaInfo] = field(default_factory=dict)
    groups: List[QuotaGroup] = field(default_factory=list)
    default_model_id: str = "gemini-3.6-flash-high"
    connection_state: ConnectionState = ConnectionState.CONNECTED
    is_stale: bool = False
    last_updated_str: str = ""
    error_message: Optional[str] = None

    @property
    def lowest_model(self) -> Optional[QuotaInfo]:
        if not self.models:
            return None
        return min(self.models.values(), key=lambda m: m.remaining_fraction)

    @property
    def active_model(self) -> Optional[QuotaInfo]:
        if self.default_model_id in self.models:
            return self.models[self.default_model_id]
        if self.models:
            return next(iter(self.models.values()))
        return None

    def get_display_percentage(self, mode: DisplayMode = DisplayMode.LOWEST) -> float:
        if mode == DisplayMode.ACTIVE:
            act = self.active_model
            return act.percentage if act else 0.0
        elif mode == DisplayMode.GEMINI_5H:
            for g in self.groups:
                if "gemini" in g.group_id.lower() or "gemini" in g.display_name.lower():
                    for b in g.buckets:
                        if b.window == "5h":
                            return b.percentage
                    return g.lowest_percentage
        elif mode == DisplayMode.CLAUDE_5H:
            for g in self.groups:
                if "claude" in g.group_id.lower() or "claude" in g.display_name.lower() or "3p" in g.group_id.lower():
                    for b in g.buckets:
                        if b.window == "5h":
                            return b.percentage
                    return g.lowest_percentage
        # Default LOWEST
        low = self.lowest_model
        return low.percentage if low else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "connection_state": self.connection_state.value,
            "is_stale": self.is_stale,
            "default_model_id": self.default_model_id,
            "error_message": self.error_message,
            "models": {
                k: {
                    "model_id": v.model_id,
                    "model_name": v.model_name,
                    "remaining_fraction": v.remaining_fraction,
                    "percentage": v.percentage,
                    "reset_time": v.reset_time_iso,
                    "status": v.status.value,
                    "supports_thinking": v.supports_thinking,
                    "recommended": v.recommended,
                }
                for k, v in self.models.items()
            },
            "groups": [
                {
                    "group_id": g.group_id,
                    "display_name": g.display_name,
                    "description": g.description,
                    "buckets": [
                        {
                            "bucket_id": b.bucket_id,
                            "display_name": b.display_name,
                            "window": b.window,
                            "remaining_fraction": b.remaining_fraction,
                            "percentage": b.percentage,
                            "reset_time": b.reset_time_iso,
                            "description": b.description,
                        }
                        for b in g.buckets
                    ],
                }
                for g in self.groups
            ],
        }


@dataclass
class AppSettings:
    refresh_interval_sec: int = 60
    display_mode: DisplayMode = DisplayMode.LOWEST
    healthy_threshold: int = 70
    warning_threshold: int = 30
    critical_threshold: int = 10
    autostart: bool = True
    show_tray: bool = True
    notify_low_quota: bool = True
    notify_reset: bool = True
    selected_model_override: Optional[str] = None

    def compute_status(self, percentage: float) -> QuotaStatus:
        if percentage >= self.healthy_threshold:
            return QuotaStatus.HEALTHY
        elif percentage >= self.warning_threshold:
            return QuotaStatus.WARNING
        else:
            return QuotaStatus.CRITICAL
