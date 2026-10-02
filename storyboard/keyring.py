"""
keyring.py — Concierge-style key pool for the Skin Deep storyboard.

Port of the valet_concierge_system KeyPool idea (round-robin over a vault
of API keys, rotate on 429) adapted to this repo's needs:

  * Vault location: $SKINDEEP_KEYRING_DIR, default ~/.concierge/vault/
    — same directory `python3 valet_concierge_system/concierge.py add ...`
    writes labels into if you point it at the shared vault. Keys live as
    plain files named `<service>+<label>.key` (one key per file), so you
    can also just `echo sk-... > ~/.concierge/vault/openrouter+work.key`.
  * Rotation is keyed PER SERVICE: a 429 on openrouter only burns
    openrouter keys; gemini/novita pools are untouched.
  * Thread-safe (the FastAPI gen endpoints can fire concurrent panels).
  * Zero dependencies; falls back silently to os.environ when the vault
    has nothing for a service, so current behavior is unchanged if no
    vault is configured.

Env var precedence for single-key setups stays intact: callers check
OPENROUTER_API_KEY / GEMINI_API_KEY etc. first via get_key().
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

VAULT_DIR = Path(os.environ.get("SKINDEEP_KEYRING_DIR",
                                Path.home() / ".concierge" / "vault"))


class KeyPool:
    """Round-robin pool of API keys for one service, backed by
    `<service>+<label>.key` files in the vault dir plus an optional
    primary env var."""

    _pools: dict[str, "KeyPool"] = {}
    _registry_lock = threading.Lock()

    def __init__(self, service: str, env_vars: tuple[str, ...] = (),
                 vault_dir: Path | None = None):
        self.service = service
        self.env_vars = env_vars
        self.vault_dir = vault_dir or VAULT_DIR
        self._lock = threading.Lock()
        self._index = 0
        self._exhausted_reported = False

    # -- registry ----------------------------------------------------------

    @classmethod
    def for_service(cls, service: str, env_vars: tuple[str, ...] = ()):
        with cls._registry_lock:
            pool = cls._pools.get(service)
            if pool is None:
                pool = cls(service, env_vars)
                cls._pools[service] = pool
            return pool

    # -- vault discovery -----------------------------------------------------

    def _vault_keys(self) -> list[str]:
        if not self.vault_dir.is_dir():
            return []
        keys = []
        for f in sorted(self.vault_dir.glob(f"{self.service}+*.key")):
            try:
                val = f.read_text(encoding="utf-8").strip()
            except OSError:
                continue
            if val:
                keys.append(val)
        return keys

    def all_keys(self) -> list[str]:
        """Env var first (primary), then vault keys, deduped."""
        seen: set[str] = set()
        out: list[str] = []
        for var in self.env_vars:
            v = os.environ.get(var, "").strip()
            if v and v not in seen:
                seen.add(v)
                out.append(v)
        for v in self._vault_keys():
            if v not in seen:
                seen.add(v)
                out.append(v)
        return out

    # -- rotation ------------------------------------------------------------

    def get_key(self) -> str | None:
        """Current key without advancing the pool (env fallback included)."""
        keys = self.all_keys()
        if not keys:
            return None
        with self._lock:
            return keys[self._index % len(keys)]

    def rotate(self) -> str | None:
        """Advance past the current key (call on 429/quota error), return
        the next key or None if the pool is empty."""
        keys = self.all_keys()
        if not keys:
            return None
        with self._lock:
            self._index = (self._index + 1) % len(keys)
            return keys[self._index]

    def status(self) -> dict:
        # Security: Mask absolute filesystem path (vault_dir) to prevent leaking
        # host directory layout and usernames in public health API endpoints.
        keys = self.all_keys()
        active = keys[self._index % len(keys)] if keys else None
        return {
            "service": self.service,
            "pool_size": len(keys),
            "vault_configured": self.vault_dir.is_dir(),
            "vault_keys": len(self._vault_keys()),
            "active_fingerprint": (active[-4:] if active else None),
        }


# ── module-level convenience for storyboard_gen providers ────────────────

def openrouter_pool() -> KeyPool:
    return KeyPool.for_service("openrouter", ("OPENROUTER_API_KEY",))


def novita_pool() -> KeyPool:
    return KeyPool.for_service("novita", ("NOVITA_API_KEY",))


def gemini_pool() -> KeyPool:
    return KeyPool.for_service("gemini",
                               ("GEMINI_API_KEY", "GOOGLE_API_KEY"))
