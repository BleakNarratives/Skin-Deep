"""
storyboard_db.py — SQLite persistence for the Skin Deep storyboard engine.

Schema: episodes -> scenes -> panels. Episode JSON export is the canonical
artifact (see DESIGN.md §3). Pure stdlib; no engine code imports FastAPI.

Connection discipline: sqlite3's `with conn` only manages transactions, it
does NOT close — leaked handles stack up under uvicorn. All access goes
through _tx (write, commit/rollback + close) or _ro (read + close), and a
write-then-read happens on the SAME connection (a second connection cannot
see the first one's uncommitted row).
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

DB_PATH = Path(__file__).parent / "storyboard.db"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL DEFAULT 1,
    number INTEGER NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    logline TEXT NOT NULL DEFAULT '',
    outline_path TEXT NOT NULL DEFAULT '',
    director_notes TEXT NOT NULL DEFAULT '',
    status TEXT NOT NULL DEFAULT 'draft',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS scenes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER NOT NULL REFERENCES episodes(id) ON DELETE CASCADE,
    ord INTEGER NOT NULL,
    slug TEXT NOT NULL DEFAULT '',
    synopsis TEXT NOT NULL DEFAULT '',
    location TEXT NOT NULL DEFAULT '',
    time_of_day TEXT NOT NULL DEFAULT '',
    characters TEXT NOT NULL DEFAULT '[]',
    ai_meta TEXT NOT NULL DEFAULT '{}',
    UNIQUE(episode_id, ord)
);
CREATE TABLE IF NOT EXISTS panels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scene_id INTEGER NOT NULL REFERENCES scenes(id) ON DELETE CASCADE,
    ord INTEGER NOT NULL,
    shot_type TEXT NOT NULL DEFAULT 'MS',
    camera_move TEXT NOT NULL DEFAULT '',
    action TEXT NOT NULL DEFAULT '',
    vo_speaker TEXT NOT NULL DEFAULT '',
    vo_line TEXT NOT NULL DEFAULT '',
    on_screen_text TEXT NOT NULL DEFAULT '',
    duration_sec REAL NOT NULL DEFAULT 3.0,
    visual_prompt TEXT NOT NULL DEFAULT '',
    image_path TEXT NOT NULL DEFAULT '',
    image_status TEXT NOT NULL DEFAULT 'none',
    ai_meta TEXT NOT NULL DEFAULT '{}',
    UNIQUE(scene_id, ord)
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def _tx() -> Iterator[sqlite3.Connection]:
    """Write transaction: commit on success, rollback on error, always close."""
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def _ro() -> Iterator[sqlite3.Connection]:
    """Read-only access: no transaction, always close."""
    conn = connect()
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    conn = connect()
    try:
        conn.executescript(_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def _j(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v


# ── episodes ─────────────────────────────────────────────────────────────

def create_episode(season: int, number: int, slug: str, title: str,
                   logline: str = "", outline_path: str = "") -> dict:
    with _tx() as conn:
        cur = conn.execute(
            "INSERT INTO episodes (season, number, slug, title, logline,"
            " outline_path, created_at, updated_at)"
            " VALUES (?,?,?,?,?,?,?,?)",
            (season, number, slug, title, logline, outline_path, _now(), _now()),
        )
        row = conn.execute(
            "SELECT * FROM episodes WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return dict(row)


def get_episode(episode_id: int) -> sqlite3.Row | None:
    with _ro() as conn:
        return conn.execute(
            "SELECT * FROM episodes WHERE id = ?", (episode_id,)
        ).fetchone()


def get_episode_by_slug(slug: str) -> sqlite3.Row | None:
    with _ro() as conn:
        return conn.execute(
            "SELECT * FROM episodes WHERE slug = ?", (slug,)
        ).fetchone()


def list_episodes() -> list[dict]:
    with _ro() as conn:
        rows = conn.execute(
            "SELECT id, season, number, slug, title, logline, status,"
            " created_at, updated_at FROM episodes"
            " ORDER BY season, number"
        ).fetchall()
        return [dict(r) for r in rows]


def update_episode(episode_id: int, **fields: Any) -> None:
    # Security: Strict whitelist mapping allowed field names to actual SQL columns.
    # Discards any unallowed keys or SQL injection attempts in field names.
    allowed = {"director_notes", "status", "logline", "title"}
    sets = {k: _j(v) for k, v in fields.items() if k in allowed}
    if not sets:
        return
    sets["updated_at"] = _now()
    # Explicitly filter and validate column names against whitelist before formatting SQL string
    cols = ", ".join(f"{k} = ?" for k in sets if k in allowed or k == "updated_at")
    with _tx() as conn:
        conn.execute(
            f"UPDATE episodes SET {cols} WHERE id = ?",
            (*sets.values(), episode_id),
        )


def delete_episode(episode_id: int) -> None:
    with _tx() as conn:
        conn.execute("DELETE FROM panels WHERE scene_id IN"
                     " (SELECT id FROM scenes WHERE episode_id = ?)",
                     (episode_id,))
        conn.execute("DELETE FROM scenes WHERE episode_id = ?", (episode_id,))
        conn.execute("DELETE FROM episodes WHERE id = ?", (episode_id,))


# ── scenes ───────────────────────────────────────────────────────────────

def replace_scenes(episode_id: int, scenes: list[dict], ai_meta: dict) -> None:
    """AI beat-sheet write: replaces the episode's scenes and cascades away
    their panels. Explicit destructive regeneration, never a surprise merge."""
    with _tx() as conn:
        conn.execute("DELETE FROM panels WHERE scene_id IN"
                     " (SELECT id FROM scenes WHERE episode_id = ?)",
                     (episode_id,))
        conn.execute("DELETE FROM scenes WHERE episode_id = ?", (episode_id,))
        for i, s in enumerate(scenes, start=1):
            conn.execute(
                "INSERT INTO scenes (episode_id, ord, slug, synopsis, location,"
                " time_of_day, characters, ai_meta) VALUES (?,?,?,?,?,?,?,?)",
                (
                    episode_id, i, str(s.get("slug", "")).strip(),
                    str(s.get("synopsis", "")).strip(),
                    str(s.get("location", "")).strip(),
                    str(s.get("time_of_day", "")).strip(),
                    _j(s.get("characters", [])), _j(ai_meta),
                ),
            )
        conn.execute(
            "UPDATE episodes SET updated_at = ? WHERE id = ?",
            (_now(), episode_id),
        )


def get_scene(scene_id: int) -> sqlite3.Row | None:
    with _ro() as conn:
        return conn.execute(
            "SELECT * FROM scenes WHERE id = ?", (scene_id,)
        ).fetchone()


def list_scenes(episode_id: int) -> list[dict]:
    with _ro() as conn:
        rows = conn.execute(
            "SELECT * FROM scenes WHERE episode_id = ? ORDER BY ord",
            (episode_id,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["characters"] = json.loads(d["characters"] or "[]")
            d["ai_meta"] = json.loads(d["ai_meta"] or "{}")
            out.append(d)
        return out


# ── panels ───────────────────────────────────────────────────────────────

def replace_panels(scene_id: int, panels: list[dict], ai_meta: dict) -> None:
    with _tx() as conn:
        conn.execute("DELETE FROM panels WHERE scene_id = ?", (scene_id,))
        for i, p in enumerate(panels, start=1):
            conn.execute(
                "INSERT INTO panels (scene_id, ord, shot_type, camera_move,"
                " action, vo_speaker, vo_line, on_screen_text, duration_sec,"
                " visual_prompt, image_status, ai_meta)"
                " VALUES (?,?,?,?,?,?,?,?,?,?, 'none', ?)",
                (
                    scene_id, i,
                    str(p.get("shot_type", "MS")).strip(),
                    str(p.get("camera_move", "")).strip(),
                    str(p.get("action", "")).strip(),
                    str(p.get("vo_speaker", "")).strip(),
                    str(p.get("vo_line", "")).strip(),
                    str(p.get("on_screen_text", "")).strip(),
                    _num(p.get("duration_sec", 3.0)),
                    str(p.get("visual_prompt", "")).strip(),
                    _j(ai_meta),
                ),
            )


def get_panel(panel_id: int) -> sqlite3.Row | None:
    with _ro() as conn:
        return conn.execute(
            "SELECT * FROM panels WHERE id = ?", (panel_id,)
        ).fetchone()


def update_panel(panel_id: int, **fields: Any) -> sqlite3.Row | None:
    allowed = {
        "shot_type", "camera_move", "action", "vo_speaker", "vo_line",
        "on_screen_text", "duration_sec", "visual_prompt", "image_path",
        "image_status", "ai_meta", "ord",
    }
    sets = {k: _j(v) for k, v in fields.items() if k in allowed}
    if not sets:
        return get_panel(panel_id)
    cols = ", ".join(f"{k} = ?" for k in sets)
    with _tx() as conn:
        conn.execute(
            f"UPDATE panels SET {cols} WHERE id = ?",
            (*sets.values(), panel_id),
        )
        return conn.execute(
            "SELECT * FROM panels WHERE id = ?", (panel_id,)
        ).fetchone()


def list_panels(scene_id: int) -> list[dict]:
    with _ro() as conn:
        rows = conn.execute(
            "SELECT * FROM panels WHERE scene_id = ? ORDER BY ord",
            (scene_id,),
        ).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["ai_meta"] = json.loads(d["ai_meta"] or "{}")
            out.append(d)
        return out


def episode_tree(episode_id: int) -> dict | None:
    ep = get_episode(episode_id)
    if ep is None:
        return None
    tree = dict(ep)
    tree["scenes"] = []
    for scene in list_scenes(episode_id):
        scene["panels"] = list_panels(scene["id"])
        tree["scenes"].append(scene)
    return tree


def _num(v: Any) -> float:
    try:
        return max(0.1, float(v))
    except (TypeError, ValueError):
        return 3.0
