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


def get_color_block_chars(percentage: float) -> tuple[str, str]:
    if percentage >= 70.0:
        return "🟩", "⬜"
    elif percentage >= 30.0:
        return "🟨", "⬜"
    else:
        return "🟥", "⬜"


def get_color_dot_chars(percentage: float) -> tuple[str, str]:
    if percentage >= 70.0:
        return "🟢", "⚪"
    elif percentage >= 30.0:
        return "🟡", "⚪"
    else:
        return "🔴", "⚪"


def get_status_badge(percentage: float) -> str:
    if percentage >= 70.0:
        return "🟢"
    elif percentage >= 30.0:
        return "🟡"
    else:
        return "🔴"


def get_heart_icon(percentage: float) -> str:
    if percentage >= 70.0:
        return "💚"
    elif percentage >= 30.0:
        return "💛"
    else:
        return "❤️"


def get_diamond_char(percentage: float) -> str:
    if percentage >= 70.0:
        return "🔹"
    elif percentage >= 30.0:
        return "🔸"
    else:
        return "🔺"


def get_dot_char(percentage: float) -> str:
    if percentage >= 70.0:
        return "🟢"
    elif percentage >= 30.0:
        return "🟡"
    else:
        return "🔴"


def shorten_model_name(name: str) -> str:
    """Shortens verbose model names for compact Top Bar display."""
    clean = (
        name.replace("(Thinking)", "")
        .replace("(High)", "")
        .replace("(Medium)", "")
        .replace("(Low)", "")
        .replace("(Extra Low)", "")
        .strip()
    )
    if "Claude Opus" in clean:
        return "Claude Opus"
    if "Claude Sonnet" in clean:
        return "Claude Sonnet"
    if "Claude Haiku" in clean:
        return "Claude Haiku"
    if "GPT-OSS" in clean:
        return "GPT-OSS"
    if "Gemini" in clean:
        return clean.replace("Google ", "").strip()
    return clean[:16]


def render_bar(percentage: float, width: int = 4, style: str = "diamonds") -> str:
    """Generates a compact progress bar with configurable style.

    Styles:
    - 'diamonds': 🔹/🔸/🔺 and ▫ (Kim cương nhỏ có màu bên trong)
    - 'color_dots': 🟢/🟡/🔴 and ⚪ (Chấm tròn màu bên trong)
    - 'small_squares': ▪ and ▫ (Khối vuông nhỏ trắng đen)
    - 'medium_squares': ◾ and ◽ (Khối vuông vừa)
    - 'rect': ▰ and ▱ (Thanh chữ nhật)
    - 'dots': ● and ○ (Chấm tròn)
    - 'bullets': • and ◦ (Chấm nhỏ)
    - 'lines': ▮ and ▯ (Vạch đứng)
    - 'block': █ and ░ (Khối đặc)
    - 'color_blocks': 🟩/🟨/🟥 and ⬜ (Khối màu emoji lớn)
    """
    pct = max(0.0, min(100.0, float(percentage)))
    filled = int(round((pct / 100.0) * width))
    empty = width - filled

    if style == "diamonds":
        f_char = get_diamond_char(pct)
        return f_char * filled + "▫" * empty
    elif style == "diamonds_orange":
        return "🔸" * filled + "▫" * empty
    elif style == "color_dots":
        f_char = get_dot_char(pct)
        return f_char * filled + "⚪" * empty
    elif style == "small_squares":
        return "▪" * filled + "▫" * empty
    elif style == "medium_squares":
        return "◾" * filled + "◽" * empty
    elif style == "color_blocks":
        f_char, e_char = get_color_block_chars(pct)
        return f_char * filled + e_char * empty
    elif style == "dots":
        return "●" * filled + "○" * empty
    elif style == "bullets":
        return "•" * filled + "◦" * empty
    elif style == "lines":
        return "▮" * filled + "▯" * empty
    elif style == "block":
        return "█" * filled + "░" * empty
    return "▰" * filled + "▱" * empty


def render_mini_bar(percentage: float, width: int = 4) -> str:
    """Generates a compact mini progress bar e.g. ▰▰▰▱."""
    return render_bar(percentage, width=width, style="rect")


class DisplayMode(str, Enum):
    STATUS_BADGE = "status_badge"              # 🟢 5h: [▪▪▪▪] 92% | 🟢 7d: [▪▪▪▫] 75% (Đèn màu thông minh + Khối nhỏ - Khuyến nghị)
    SMALL_COLOR_EMBED = "small_color_embed"    # 5h: 🟢[▪▪▪▪] 92% | 7d: 🟢[▪▪▪▫] 75% (Khối nhỏ có đèn màu đính kèm)
    SMALL_DIAMONDS = "small_diamonds"          # 5h: [🔹🔹🔹▫] 92% | 7d: [🔹🔹🔹▫] 75% (Kim cương nhỏ xanh)
    SMALL_DIAMONDS_WARM = "small_diamonds_warm"# 5h: [🔸🔸🔸▫] 92% | 7d: [🔸🔸🔸▫] 75% (Kim cương nhỏ cam)
    SMALL_SQUARES = "small_squares"            # 5h: [▪▪▪▪] 92% | 7d: [▪▪▪▫] 75% (Khối vuông nhỏ trắng đen)
    MEDIUM_SQUARES = "medium_squares"          # 5h: [◾◾◾◾] 92% | 7d: [◾◾◾◽] 75% (Khối vuông vừa)
    MINI_BARS = "mini_bars"                    # 5h: [▰▰▰▰] 92% | 7d: [▰▰▰▱] 75% (Thanh chữ nhật ▰▱)
    CIRCLE_DOTS = "circle_dots"                # 5h: [●●●●] 92% | 7d: [●●●○] 75% (Chấm tròn ●○)
    BULLETS = "bullets"                        # 5h: [••••] 92% | 7d: [•••◦] 75% (Chấm nhỏ •◦)
    VERTICAL_LINES = "vertical_lines"          # 5h: [▮▮▮▮] 92% | 7d: [▮▮▮▯] 75% (Vạch đứng ▮▯)
    SOLID_BLOCKS = "solid_blocks"              # 5h: [████] 92% | 7d: [███░] 75% (Khối đặc █░)
    COLOR_BLOCKS = "color_blocks"              # 5h: [🟩🟩🟩🟩] 92% | 7d: [🟩🟩🟩⬜] 75% (Khối màu Emoji lớn)
    COLOR_DOTS = "color_dots"                  # 5h: [🟢🟢🟢🟢] 92% | 7d: [🟢🟢🟢⚪] 75% (Chấm màu Emoji)
    COLOR_HEARTS = "color_hearts"              # 5h: 💚 92% | 7d: 💚 75% (Trái tim màu)
    BARS_ONLY = "bars_only"                    # 5h: [▪▪▪▪] | 7d: [▪▪▪▫] (Chỉ khối, ẩn %)
    COMBINED_5H_WEEKLY = "combined_5h_weekly"  # 5h: 70% | 7d: 78% (Dạng số rút gọn)
    MINIMAL_LOWEST = "minimal_lowest"          # [▪▪▪▫] 70% (Tối giản)
    LOWEST = "lowest"                          # 70% (Chỉ số % thấp nhất)
    ACTIVE = "active"                          # Model mặc định / đang active
    GEMINI_ALL = "gemini_all"                  # Gemini: Cả 5h & 7d
    CLAUDE_ALL = "claude_all"                  # Claude/GPT: Cả 5h & 7d
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

    def get_target_model(self, selected_model_id: Optional[str] = None) -> Optional[QuotaInfo]:
        """Resolves target model based on ID or fallback to active/lowest."""
        if not selected_model_id or selected_model_id in ("auto", "none", ""):
            return None
        if selected_model_id == "active":
            return self.active_model
        if selected_model_id == "lowest":
            return self.lowest_model
        if selected_model_id in self.models:
            return self.models[selected_model_id]
        # Search by partial match / model_name
        for mid, m in self.models.items():
            if selected_model_id.lower() in mid.lower() or selected_model_id.lower() in m.model_name.lower():
                return m
        return None

    def get_display_percentage(
        self,
        mode: DisplayMode = DisplayMode.MINI_BARS,
        selected_model_id: Optional[str] = None,
    ) -> float:
        target_m = self.get_target_model(selected_model_id)
        if target_m is not None:
            return target_m.percentage

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
        elif mode in (
            DisplayMode.STATUS_BADGE,
            DisplayMode.SMALL_COLOR_EMBED,
            DisplayMode.SMALL_DIAMONDS,
            DisplayMode.SMALL_DIAMONDS_WARM,
            DisplayMode.SMALL_SQUARES,
            DisplayMode.MEDIUM_SQUARES,
            DisplayMode.MINI_BARS,
            DisplayMode.CIRCLE_DOTS,
            DisplayMode.BULLETS,
            DisplayMode.VERTICAL_LINES,
            DisplayMode.SOLID_BLOCKS,
            DisplayMode.COLOR_BLOCKS,
            DisplayMode.COLOR_DOTS,
            DisplayMode.COLOR_HEARTS,
            DisplayMode.BARS_ONLY,
            DisplayMode.COMBINED_5H_WEEKLY,
        ):
            p_5h, p_wk = self.get_5h_and_weekly()
            vals = [v for v in (p_5h, p_wk) if v is not None]
            return min(vals) if vals else (self.lowest_model.percentage if self.lowest_model else 0.0)
        # Default LOWEST
        low = self.lowest_model
        return low.percentage if low else 0.0

    def get_display_label(
        self,
        mode: DisplayMode = DisplayMode.STATUS_BADGE,
        selected_model_id: Optional[str] = None,
    ) -> str:
        target_m = self.get_target_model(selected_model_id)

        # Style map for rendering bars
        style_map = {
            DisplayMode.SMALL_SQUARES: "small_squares",
            DisplayMode.MEDIUM_SQUARES: "medium_squares",
            DisplayMode.SMALL_DIAMONDS: "diamonds",
            DisplayMode.SMALL_DIAMONDS_WARM: "diamonds_orange",
            DisplayMode.MINI_BARS: "rect",
            DisplayMode.CIRCLE_DOTS: "dots",
            DisplayMode.BULLETS: "bullets",
            DisplayMode.VERTICAL_LINES: "lines",
            DisplayMode.SOLID_BLOCKS: "block",
            DisplayMode.COLOR_BLOCKS: "color_blocks",
            DisplayMode.COLOR_DOTS: "color_dots",
            DisplayMode.BARS_ONLY: "small_squares",
        }
        style = style_map.get(mode, "small_squares")
        show_pct = (mode != DisplayMode.BARS_ONLY)

        # Case 1: Specific Model Override is Selected
        if target_m is not None:
            m_name = shorten_model_name(target_m.model_name)
            pct = target_m.percentage
            bar = render_bar(pct, width=4, style=style)

            if mode == DisplayMode.STATUS_BADGE:
                badge = get_status_badge(pct)
                return f"{badge} {m_name}: [{bar}] {pct:.0f}%" if show_pct else f"{badge} {m_name}: [{bar}]"
            elif mode == DisplayMode.SMALL_COLOR_EMBED:
                badge = get_status_badge(pct)
                return f"{m_name}: {badge}[{bar}] {pct:.0f}%" if show_pct else f"{m_name}: {badge}[{bar}]"
            elif mode == DisplayMode.COLOR_HEARTS:
                heart = get_heart_icon(pct)
                return f"{m_name}: {heart} {pct:.0f}%"
            elif mode == DisplayMode.COMBINED_5H_WEEKLY:
                return f"{m_name}: {pct:.0f}%"
            elif mode == DisplayMode.MINIMAL_LOWEST:
                return f"[{bar}] {pct:.0f}%"
            elif mode == DisplayMode.LOWEST:
                return f"{pct:.0f}%"
            else:
                return f"{m_name}: [{bar}] {pct:.0f}%" if show_pct else f"{m_name}: [{bar}]"

        # Case 2: Group / Auto / 5h & 7d display modes
        if mode in (
            DisplayMode.SMALL_SQUARES,
            DisplayMode.MEDIUM_SQUARES,
            DisplayMode.SMALL_DIAMONDS,
            DisplayMode.SMALL_DIAMONDS_WARM,
            DisplayMode.MINI_BARS,
            DisplayMode.CIRCLE_DOTS,
            DisplayMode.BULLETS,
            DisplayMode.VERTICAL_LINES,
            DisplayMode.SOLID_BLOCKS,
            DisplayMode.COLOR_BLOCKS,
            DisplayMode.COLOR_DOTS,
            DisplayMode.BARS_ONLY,
        ):
            l_5h, l_wk = self.get_5h_and_weekly()
            if l_5h is not None and l_wk is not None:
                b_5h = render_bar(l_5h, width=4, style=style)
                b_wk = render_bar(l_wk, width=4, style=style)
                if show_pct:
                    return f"5h: [{b_5h}] {l_5h:.0f}% | 7d: [{b_wk}] {l_wk:.0f}%"
                else:
                    return f"5h: [{b_5h}] | 7d: [{b_wk}]"
            elif l_5h is not None:
                b_5h = render_bar(l_5h, width=4, style=style)
                return f"5h: [{b_5h}] {l_5h:.0f}%" if show_pct else f"5h: [{b_5h}]"
            elif l_wk is not None:
                b_wk = render_bar(l_wk, width=4, style=style)
                return f"7d: [{b_wk}] {l_wk:.0f}%" if show_pct else f"7d: [{b_wk}]"
            low = self.lowest_model
            if low:
                b_low = render_bar(low.percentage, width=4, style=style)
                return f"[{b_low}] {low.percentage:.0f}%" if show_pct else f"[{b_low}]"
            return "100%"

        elif mode == DisplayMode.STATUS_BADGE:
            l_5h, l_wk = self.get_5h_and_weekly()
            if l_5h is not None and l_wk is not None:
                b_5h = render_bar(l_5h, width=4, style="small_squares")
                b_wk = render_bar(l_wk, width=4, style="small_squares")
                s_5h = get_status_badge(l_5h)
                s_wk = get_status_badge(l_wk)
                return f"{s_5h} 5h: [{b_5h}] {l_5h:.0f}% | {s_wk} 7d: [{b_wk}] {l_wk:.0f}%"
            elif l_5h is not None:
                b_5h = render_bar(l_5h, width=4, style="small_squares")
                return f"{get_status_badge(l_5h)} 5h: [{b_5h}] {l_5h:.0f}%"
            elif l_wk is not None:
                b_wk = render_bar(l_wk, width=4, style="small_squares")
                return f"{get_status_badge(l_wk)} 7d: [{b_wk}] {l_wk:.0f}%"
            low = self.lowest_model
            return f"{get_status_badge(low.percentage if low else 100.0)} {low.percentage:.0f}%" if low else "🟢 100%"

        elif mode == DisplayMode.SMALL_COLOR_EMBED:
            l_5h, l_wk = self.get_5h_and_weekly()
            if l_5h is not None and l_wk is not None:
                b_5h = render_bar(l_5h, width=4, style="small_squares")
                b_wk = render_bar(l_wk, width=4, style="small_squares")
                s_5h = get_status_badge(l_5h)
                s_wk = get_status_badge(l_wk)
                return f"5h: {s_5h}[{b_5h}] {l_5h:.0f}% | 7d: {s_wk}[{b_wk}] {l_wk:.0f}%"
            elif l_5h is not None:
                b_5h = render_bar(l_5h, width=4, style="small_squares")
                return f"5h: {get_status_badge(l_5h)}[{b_5h}] {l_5h:.0f}%"
            elif l_wk is not None:
                b_wk = render_bar(l_wk, width=4, style="small_squares")
                return f"7d: {get_status_badge(l_wk)}[{b_wk}] {l_wk:.0f}%"
            low = self.lowest_model
            return f"{get_status_badge(low.percentage if low else 100.0)} {low.percentage:.0f}%" if low else "🟢 100%"

        elif mode == DisplayMode.COLOR_HEARTS:
            l_5h, l_wk = self.get_5h_and_weekly()
            if l_5h is not None and l_wk is not None:
                return f"5h: {get_heart_icon(l_5h)} {l_5h:.0f}% | 7d: {get_heart_icon(l_wk)} {l_wk:.0f}%"
            elif l_5h is not None:
                return f"5h: {get_heart_icon(l_5h)} {l_5h:.0f}%"
            elif l_wk is not None:
                return f"7d: {get_heart_icon(l_wk)} {l_wk:.0f}%"
            low = self.lowest_model
            return f"{get_heart_icon(low.percentage if low else 100.0)} {low.percentage:.0f}%" if low else "💚 100%"

        elif mode == DisplayMode.MINIMAL_LOWEST:
            low = self.lowest_model
            if low:
                b_low = render_bar(low.percentage, width=4, style="small_squares")
                return f"[{b_low}] {low.percentage:.0f}%"
            return "100%"

        elif mode == DisplayMode.COMBINED_5H_WEEKLY:
            l_5h, l_wk = self.get_5h_and_weekly()
            if l_5h is not None and l_wk is not None:
                return f"5h: {l_5h:.0f}% | 7d: {l_wk:.0f}%"
            elif l_5h is not None:
                return f"5h: {l_5h:.0f}%"
            elif l_wk is not None:
                return f"7d: {l_wk:.0f}%"
            low = self.lowest_model
            return f"{low.percentage:.0f}%" if low else "100%"

        elif mode == DisplayMode.LOWEST:
            low = self.lowest_model
            return f"{low.percentage:.0f}%" if low else "100%"

        elif mode == DisplayMode.ACTIVE:
            act = self.active_model
            if act:
                m_name = shorten_model_name(act.model_name)
                b = render_bar(act.percentage, width=4, style=style)
                return f"{m_name}: [{b}] {act.percentage:.0f}%" if show_pct else f"{m_name}: [{b}]"
            return "100%"

        elif mode == DisplayMode.GEMINI_ALL:
            p_5h, p_wk = self.get_group_5h_and_weekly("gemini")
            if p_5h is not None and p_wk is not None:
                b_5h = render_bar(p_5h, width=4, style=style)
                b_wk = render_bar(p_wk, width=4, style=style)
                return f"Gemini 5h: [{b_5h}] {p_5h:.0f}% | 7d: [{b_wk}] {p_wk:.0f}%"
            elif p_5h is not None:
                b_5h = render_bar(p_5h, width=4, style=style)
                return f"Gemini 5h: [{b_5h}] {p_5h:.0f}%"
            return "100%"

        elif mode == DisplayMode.CLAUDE_ALL:
            p_5h, p_wk = self.get_group_5h_and_weekly("claude")
            if p_5h is not None and p_wk is not None:
                b_5h = render_bar(p_5h, width=4, style=style)
                b_wk = render_bar(p_wk, width=4, style=style)
                return f"Claude 5h: [{b_5h}] {p_5h:.0f}% | 7d: [{b_wk}] {p_wk:.0f}%"
            elif p_5h is not None:
                b_5h = render_bar(p_5h, width=4, style=style)
                return f"Claude 5h: [{b_5h}] {p_5h:.0f}%"
            return "100%"

        elif mode == DisplayMode.GEMINI_5H:
            p_5h, _ = self.get_group_5h_and_weekly("gemini")
            if p_5h is not None:
                b_5h = render_bar(p_5h, width=4, style=style)
                return f"Gemini 5h: [{b_5h}] {p_5h:.0f}%"
            return "100%"

        elif mode == DisplayMode.CLAUDE_5H:
            p_5h, _ = self.get_group_5h_and_weekly("claude")
            if p_5h is not None:
                b_5h = render_bar(p_5h, width=4, style=style)
                return f"Claude 5h: [{b_5h}] {p_5h:.0f}%"
            return "100%"

        return "100%"

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
    display_mode: DisplayMode = DisplayMode.MINI_BARS
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
