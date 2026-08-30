"""
telemetry.py — live system state for the arena WebSocket feeds.

Reads /proc/meminfo, cgroup PSI, and the memguard daemon heartbeat
(~/MikeySwarm/logs/memguard/memguard_state.json). Uses the Mikey engine's
memgate for the verdict so the arena and the runners speak the same dialect.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import memgate  # from ~/MikeySwarm via sys.path in app.py

MIKEY_ROOT: Path = Path.home() / "MikeySwarm"
STATE_FILE: Path = MIKEY_ROOT / "logs" / "memguard" / "memguard_state.json"


def _read_meminfo() -> dict:
    d: dict[str, int] = {}
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                key, _, rest = line.partition(":")
                parts = rest.split()
                if parts:
                    d[f"{key.strip()}_mb"] = int(parts[0]) // 1024
    except (OSError, ValueError):
        pass
    return d


def _read_psi() -> dict:
    psi: dict[str, float] = {}
    try:
        with open("/sys/fs/cgroup/memory.pressure") as f:
            for line in f:
                kind, _, rest = line.partition(" ")
                fields = dict(p.split("=") for p in rest.split() if "=" in p)
                if kind == "some":
                    psi["some_avg10"] = float(fields.get("avg10", 0))
    except OSError:
        pass
    return psi


def _read_memguard_state() -> dict:
    try:
        age = time.time() - STATE_FILE.stat().st_mtime
        with open(STATE_FILE) as f:
            state = json.load(f)
        state["age_s"] = round(age, 1)
        return state
    except (OSError, ValueError, KeyError):
        return {"state": "unknown", "age_s": None}


def snapshot() -> dict:
    """One telemetry frame. Lightweight — safe on a 2.6GB VM."""
    mi = _read_meminfo()
    psi = _read_psi()
    verdict, reasons = memgate.check()
    return {
        "ts": time.time(),
        "mem": {
            "total_mb": mi.get("MemTotal_mb"),
            "available_mb": mi.get("MemAvailable_mb"),
            "free_mb": mi.get("MemFree_mb"),
        },
        "psi": psi,
        "memgate": {"verdict": verdict, "reasons": reasons},
        "memguard": _read_memguard_state(),
    }
