"""Logging facility for Antigravity Quota Monitor with sensitive credential scrubbing."""

import logging
import os
import re
from pathlib import Path

# Regular expressions to scrub tokens and credentials
TOKEN_PATTERNS = [
    re.compile(r"ya29\.[a-zA-Z0-9_\-]+"),
    re.compile(r"Bearer\s+[a-zA-Z0-9_\.\-]+", re.IGNORECASE),
    re.compile(r"1//[a-zA-Z0-9_\-]+"),
    re.compile(r'"access_token"\s*:\s*"[^"]+"'),
    re.compile(r'"refresh_token"\s*:\s*"[^"]+"'),
    re.compile(r'"client_secret"\s*:\s*"[^"]+"'),
]


class SanitizingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.sanitize(record.msg)
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self.sanitize(v) if isinstance(v, str) else v for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self.sanitize(a) if isinstance(a, str) else a for a in record.args)
        return True

    @staticmethod
    def sanitize(text: str) -> str:
        res = text
        for pat in TOKEN_PATTERNS:
            res = pat.sub("[REDACTED_TOKEN]", res)
        return res


def setup_logger(debug: bool = False) -> logging.Logger:
    logger = logging.getLogger("antigravity_quota")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)

    if not logger.handlers:
        # Determine log directory
        log_dir = Path.home() / ".local" / "share" / "antigravity-quota-monitor" / "logs"
        try:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "app.log"
            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_formatter = logging.Formatter(
                "[%(asctime)s] [%(levelname)s] [%(name)s:%(filename)s:%(lineno)d] %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            file_handler.addFilter(SanitizingFilter())
            logger.addHandler(file_handler)
        except Exception:
            pass  # Fallback gracefully if directory is read-only

        # Stream handler for CLI / console
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("[%(levelname)s] %(message)s")
        console_handler.setFormatter(console_formatter)
        console_handler.addFilter(SanitizingFilter())
        logger.addHandler(console_handler)

    return logger


logger = setup_logger()
