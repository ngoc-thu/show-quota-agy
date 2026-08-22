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
    COMBINED_5H_WEEKLY = "combined_5h_weekly"  # 5h: XX% | Tuần: YY% (Khuyến nghị)
    LOWEST = "lowest"                          # Model thấp nhất
    ACTIVE = "active"                          # Model mặc định / đang active
    GEMINI_ALL = "gemini_all"                  # Gemini: Cả 5h & Tuần
    CLAUDE_ALL = "claude_all"                  # Claude/GPT: Cả 5h & Tuần
    GEMINI_5H = "gemini_5h"                    # Hạn mức 5h của Gemini
    CLAUDE_5H = "claude_5h"                    # Hạn mức 5h của Claude/GPT


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

    def get_5h_and_weekly(self) -> tuple[Optional[float], Optional[float]]:
        """Returns (lowest_5h_pct, lowest_weekly_pct) across all groups."""
        p_5h = []
        p_weekly = []
        for g in self.groups:
            for b in g.buckets:
                if b.window == "5h":
                    p_5h.append(b.percentage)
                elif b.window == "weekly":
                    p_weekly.append(b.percentage)
        lowest_5h = min(p_5h) if p_5h else None
        lowest_weekly = min(p_weekly) if p_weekly else None
        return lowest_5h, lowest_weekly

    def get_group_5h_and_weekly(self, group_keyword: str) -> tuple[Optional[float], Optional[float]]:
        p_5h = None
        p_weekly = None
        for g in self.groups:
            if group_keyword.lower() in g.group_id.lower() or group_keyword.lower() in g.display_name.lower():
                for b in g.buckets:
                    if b.window == "5h":
                        p_5h = b.percentage
                    elif b.window == "weekly":
                        p_weekly = b.percentage
        return p_5h, p_weekly

    def get_display_percentage(self, mode: DisplayMode = DisplayMode.COMBINED_5H_WEEKLY) -> float:
        if mode == DisplayMode.ACTIVE:
            act = self.active_model
            return act.percentage if act else 0.0
        elif mode == DisplayMode.GEMINI_5H:
            p_5h, _ = self.get_group_5h_and_weekly("gemini")
            return p_5h if p_5h is not None else (self.lowest_model.percentage if self.lowest_model else 0.0)
        elif mode == DisplayMode.CLAUDE_5H:
            p_5h, _ = self.get_group_5h_and_weekly("claude")
            return p_5h if p_5h is not None else (self.lowest_model.percentage if self.lowest_model else 0.0)
        elif mode == DisplayMode.GEMINI_ALL:
            p_5h, p_wk = self.get_group_5h_and_weekly("gemini")
            vals = [v for v in (p_5h, p_wk) if v is not None]
            return min(vals) if vals else (self.lowest_model.percentage if self.lowest_model else 0.0)
        elif mode == DisplayMode.CLAUDE_ALL:
            p_5h, p_wk = self.get_group_5h_and_weekly("claude")
            vals = [v for v in (p_5h, p_wk) if v is not None]
            return min(vals) if vals else (self.lowest_model.percentage if self.lowest_model else 0.0)
        elif mode == DisplayMode.COMBINED_5H_WEEKLY:
            p_5h, p_wk = self.get_5h_and_weekly()
            vals = [v for v in (p_5h, p_wk) if v is not None]
            return min(vals) if vals else (self.lowest_model.percentage if self.lowest_model else 0.0)
        # Default LOWEST
        low = self.lowest_model
        return low.percentage if low else 0.0

    def get_display_label(self, mode: DisplayMode = DisplayMode.COMBINED_5H_WEEKLY) -> str:
        if mode == DisplayMode.COMBINED_5H_WEEKLY:
            l_5h, l_wk = self.get_5h_and_weekly()
            if l_5h is not None and l_wk is not None:
                return f"5h: {l_5h:.0f}% | Tuần: {l_wk:.0f}%"
            elif l_5h is not None:
                return f"5h: {l_5h:.0f}%"
            elif l_wk is not None:
                return f"Tuần: {l_wk:.0f}%"
            low = self.lowest_model
            return f"{low.percentage:.0f}%" if low else "100%"

        elif mode == DisplayMode.GEMINI_ALL:
            g_5h, g_wk = self.get_group_5h_and_weekly("gemini")
            if g_5h is not None and g_wk is not None:
                return f"G: 5h {g_5h:.0f}% | Tuần {g_wk:.0f}%"
            elif g_5h is not None:
                return f"Gemini 5h: {g_5h:.0f}%"
            return f"{self.get_display_percentage(mode):.0f}%"

        elif mode == DisplayMode.CLAUDE_ALL:
            c_5h, c_wk = self.get_group_5h_and_weekly("claude")
            if c_5h is not None and c_wk is not None:
                return f"C: 5h {c_5h:.0f}% | Tuần {c_wk:.0f}%"
            elif c_5h is not None:
                return f"Claude 5h: {c_5h:.0f}%"
            return f"{self.get_display_percentage(mode):.0f}%"

        elif mode == DisplayMode.GEMINI_5H:
            pct = self.get_display_percentage(mode)
            return f"Gemini 5h: {pct:.0f}%"

        elif mode == DisplayMode.CLAUDE_5H:
            pct = self.get_display_percentage(mode)
            return f"Claude 5h: {pct:.0f}%"

        elif mode == DisplayMode.ACTIVE:
            act = self.active_model
            return f"{act.percentage:.0f}%" if act else "100%"

        # Default or LOWEST
        pct = self.get_display_percentage(mode)
        return f"{pct:.0f}%"

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
    display_mode: DisplayMode = DisplayMode.COMBINED_5H_WEEKLY
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
