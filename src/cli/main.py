"""Command line interface (antigravity-quota) for terminal and desktop launch."""

import argparse
import json
import sys
import os
from datetime import datetime, timezone
from typing import Optional

from ..core.config import APP_NAME, VERSION
from ..core.models import QuotaSnapshot, ConnectionState, QuotaStatus
from ..core.service import QuotaService
from ..core.logger import logger, setup_logger
from ..antigravity.detector import AntigravityDetector
from ..antigravity.auth import AntigravityAuthProvider, AuthError

# ANSI Colors
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_DIM = "\033[2m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_PURPLE = "\033[35m"
COLOR_CYAN = "\033[36m"


def render_progress_bar(percentage: float, width: int = 18) -> str:
    """Renders a colored Unicode progress bar."""
    pct = max(0.0, min(100.0, percentage))
    filled = int(round((pct / 100.0) * width))
    empty = width - filled

    if pct >= 70.0:
        color = COLOR_GREEN
    elif pct >= 30.0:
        color = COLOR_YELLOW
    else:
        color = COLOR_RED

    bar = "█" * filled + "░" * empty
    return f"{color}{bar}{COLOR_RESET}"


def print_quota_terminal(snapshot: QuotaSnapshot):
    """Formats and prints quota information to the terminal."""
    print(f"\n{COLOR_BOLD}{COLOR_PURPLE}🚀 {APP_NAME}{COLOR_RESET}")
    print(f"{COLOR_DIM}────────────────────────────────────────────────────────────{COLOR_RESET}")

    if snapshot.connection_state == ConnectionState.AUTH_REQUIRED:
        print(f"{COLOR_YELLOW}🔐 Authentication Required{COLOR_RESET}")
        print("Please log into Antigravity (run 'agy') to initialize credentials.\n")
        return

    if not snapshot.models:
        print(f"{COLOR_RED}⚪ Không có dữ liệu quota ({snapshot.error_message or 'Offline'}){COLOR_RESET}\n")
        return

    # 1. Models List
    sorted_models = sorted(
        snapshot.models.values(),
        key=lambda m: (not m.recommended, m.model_name),
    )

    for minfo in sorted_models:
        bar = render_progress_bar(minfo.percentage, width=16)
        countdown = minfo.formatted_countdown()
        cd_str = f" {COLOR_DIM}(Reset: {countdown}){COLOR_RESET}" if countdown != "N/A" else ""

        rec_tag = f" {COLOR_CYAN}[★]{COLOR_RESET}" if minfo.recommended else ""
        print(f"  {minfo.model_name:<26}{rec_tag}")
        print(f"  {bar} {COLOR_BOLD}{minfo.percentage:5.1f}%{COLOR_RESET}{cd_str}")
        print()

    # 2. Rate Limit Groups
    if snapshot.groups:
        print(f"{COLOR_BOLD}Hạn mức nhóm (Rate Limit Groups):{COLOR_RESET}")
        for g in snapshot.groups:
            b_texts = []
            for b in g.buckets:
                b_texts.append(f"{b.window}: {b.percentage:.1f}% (reset: {b.formatted_countdown()})")
            print(f"  • {COLOR_BOLD}{g.display_name}{COLOR_RESET}: {' | '.join(b_texts)}")
        print()

    # 3. Status Footer
    status_label = "🟢 Live" if not snapshot.is_stale else "⚠ Stale (Offline)"
    print(f"{COLOR_DIM}────────────────────────────────────────────────────────────{COLOR_RESET}")
    print(f"Trạng thái: {status_label}  |  Cập nhật: {snapshot.last_updated_str or 'N/A'}\n")


def run_debug_diagnostics(service: QuotaService):
    """Runs detailed environment and connectivity diagnostics without printing secrets."""
    print(f"\n{COLOR_BOLD}🔍 Antigravity Quota Monitor — Diagnostic Report{COLOR_RESET}")
    print("=" * 60)

    # 1. Process Detection
    detection = AntigravityDetector.detect()
    print(f"Antigravity Detected:  {'YES' if detection.is_running else 'NO'}")
    print(f"Details:               {detection.details}")
    for p in detection.processes:
        print(f"  - PID {p.pid:<7} Type: {p.process_type:<10} Command: {p.cmdline[:60]}...")
    print()

    # 2. Keyring Authentication Test
    print(f"GNOME Keyring Test:    Service='gemini', Username='antigravity'")
    try:
        token = service.auth_provider.get_access_token(force_refresh=True)
        print(f"Authentication Token:  VALID (Length: {len(token)} chars, Type: {service.auth_provider.auth_method})")
    except Exception as e:
        print(f"Authentication Token:  FAILED ({e})")
    print()

    # 3. API Connectivity Test
    print("Testing Live API Endpoints:")
    try:
        models_data = service.client.fetch_available_models(force_refresh=True)
        models_count = len(models_data.get("models", {}))
        print(f"  • :fetchAvailableModels:      SUCCESS ({models_count} models found)")
    except Exception as e:
        print(f"  • :fetchAvailableModels:      FAILED ({e})")

    try:
        summary_data = service.client.fetch_quota_summary(force_refresh=True)
        groups_count = len(summary_data.get("groups", []))
        print(f"  • :retrieveUserQuotaSummary:  SUCCESS ({groups_count} groups found)")
    except Exception as e:
        print(f"  • :retrieveUserQuotaSummary:  FAILED ({e})")

    print("=" * 60)
    print("Diagnostics complete.\n")


def main():
    parser = argparse.ArgumentParser(
        prog="antigravity-quota",
        description="Monitor Google Antigravity remaining quota natively on Ubuntu.",
    )
    parser.add_argument("--json", action="store_true", help="Output current quota snapshot as JSON")
    parser.add_argument("--refresh", action="store_true", help="Force immediate refresh from API")
    parser.add_argument("--version", "-v", action="store_true", help="Display version information")
    parser.add_argument("--debug", action="store_true", help="Run diagnostics without leaking credentials")
    parser.add_argument("--gui", "--dashboard", action="store_true", help="Launch the GTK4 / Libadwaita dashboard window")
    parser.add_argument("--tray", "--indicator", action="store_true", help="Launch the GNOME Top Bar indicator daemon")
    parser.add_argument("--tab", type=str, default="overview", help="Initial tab for GUI (overview, history, settings, about)")

    args = parser.parse_args()

    if args.version:
        print(f"{APP_NAME} v{VERSION}")
        sys.exit(0)

    service = QuotaService()

    if args.debug:
        setup_logger(debug=True)
        run_debug_diagnostics(service)
        sys.exit(0)

    if args.gui:
        from ..ui.app import run_gui
        sys.exit(run_gui(service=service, initial_tab=args.tab))

    if args.tray:
        from ..tray.indicator import TopBarIndicator
        indicator = TopBarIndicator(service)
        indicator.run()
        sys.exit(0)

    # CLI Output mode
    snapshot = service.refresh(force=args.refresh)

    if args.json:
        print(json.dumps(snapshot.to_dict(), indent=2))
    else:
        print_quota_terminal(snapshot)


if __name__ == "__main__":
    main()
