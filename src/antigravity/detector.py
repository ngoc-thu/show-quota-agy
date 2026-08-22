"""Process and environment detector for Google Antigravity."""

import os
import subprocess
from dataclasses import dataclass
from typing import List, Optional
from ..core.logger import logger


@dataclass
class AntigravityProcessInfo:
    pid: int
    name: str
    cmdline: str
    process_type: str  # 'cli', 'bridge', 'proxy', 'ide'


@dataclass
class DetectionResult:
    is_running: bool
    processes: List[AntigravityProcessInfo]
    has_keyring_token: bool = False
    details: str = ""


class AntigravityDetector:
    """Scans running processes and environment to detect Antigravity components."""

    @staticmethod
    def detect() -> DetectionResult:
        processes: List[AntigravityProcessInfo] = []

        try:
            # Inspect /proc or use ps
            cmd = ["ps", "-eo", "pid,comm,args"]
            out = subprocess.check_output(cmd, text=True, errors="replace")

            for line in out.splitlines()[1:]:
                parts = line.strip().split(None, 2)
                if len(parts) < 3:
                    continue
                pid_str, comm, args = parts
                try:
                    pid = int(pid_str)
                except ValueError:
                    continue

                if pid == os.getpid():
                    continue

                # Check process signatures
                if comm == "agy" or "bin/agy" in args:
                    processes.append(
                        AntigravityProcessInfo(
                            pid=pid,
                            name="agy",
                            cmdline=args,
                            process_type="cli",
                        )
                    )
                elif "dev.matasar.antigravity.bridge.StdioBridge" in args:
                    processes.append(
                        AntigravityProcessInfo(
                            pid=pid,
                            name="antigravity-bridge",
                            cmdline=args,
                            process_type="bridge",
                        )
                    )
                elif "antigravity_proxy.py" in args:
                    processes.append(
                        AntigravityProcessInfo(
                            pid=pid,
                            name="antigravity-proxy",
                            cmdline=args,
                            process_type="proxy",
                        )
                    )
                elif "antigravity" in args.lower() and "quota-monitor" not in args:
                    processes.append(
                        AntigravityProcessInfo(
                            pid=pid,
                            name=comm,
                            cmdline=args,
                            process_type="ide",
                        )
                    )

        except Exception as e:
            logger.debug("Error detecting processes: %s", e)

        is_running = len(processes) > 0
        details = (
            f"Found {len(processes)} Antigravity process(es)"
            if is_running
            else "No active Antigravity process found"
        )

        return DetectionResult(
            is_running=is_running,
            processes=processes,
            details=details,
        )
