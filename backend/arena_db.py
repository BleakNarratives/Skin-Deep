"""
arena_db.py — persistence for the Skin-Deep LOUGH Arena.

Deliberately SEPARATE from ~/MikeySwarm/persona_runs.db (the sacred 77-run
experiment corpus). Human benchmark scores and role-reversal battles land
here. Schema is additive — ALTERs are safe; drops are not.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

ARENA_DB: Path = Path(__file__).resolve().parent / "arena.db"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(ARENA_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS human_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                task_id TEXT NOT NULL,
                response_text TEXT,
                mike_delta REAL NOT NULL,
                outcome TEXT NOT NULL,
                directness REAL,
                investigation REAL,
                systems_thinking REAL,
                anti_larp REAL,
                no_hedging REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS battles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                params TEXT NOT NULL,
                turns INTEGER DEFAULT 0,
                status TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS rounds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                round_id TEXT UNIQUE NOT NULL,
                started TEXT NOT NULL,
                groups TEXT NOT NULL,
                status TEXT NOT NULL,
                events TEXT DEFAULT '[]'
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS persona_custom (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created TEXT NOT NULL,
                seed TEXT NOT NULL
            )
            """
        )


def insert_human_score(
    task_id: str,
    response_text: str,
    score: float,
    outcome: str,
    traits: dict,
) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO human_scores
                (timestamp, task_id, response_text, mike_delta, outcome,
                 directness, investigation, systems_thinking, anti_larp, no_hedging)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                _now(),
                task_id,
                response_text,
                score,
                outcome,
                traits.get("directness"),
                traits.get("investigation"),
                traits.get("systems_thinking"),
                traits.get("anti_larp"),
                traits.get("no_hedging"),
            ),
        )
        return cur.lastrowid


def create_round(round_id: str, groups: list[str]) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO rounds (round_id, started, groups, status)
            VALUES (?, ?, ?, ?)
            """,
            (round_id, _now(), json.dumps(groups), "running"),
        )


def append_round_event(round_id: str, event: dict) -> None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT events FROM rounds WHERE round_id = ?", (round_id,)
        ).fetchone()
        events = json.loads(row["events"]) if row else []
        events.append(event)
        conn.execute(
            "UPDATE rounds SET events = ? WHERE round_id = ?",
            (json.dumps(events, default=str), round_id),
        )


def finish_round(round_id: str, status: str = "complete") -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE rounds SET status = ? WHERE round_id = ?", (status, round_id)
        )


def get_round(round_id: str) -> dict | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM rounds WHERE round_id = ?", (round_id,)
        ).fetchone()
    return dict(row) if row else None


def insert_battle(params: dict, status: str = "running") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO battles (timestamp, params, status) VALUES (?, ?, ?)",
            (_now(), json.dumps(params), status),
        )
        return cur.lastrowid


def update_battle(battle_id: int, turns: int, status: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "UPDATE battles SET turns = ?, status = ? WHERE id = ?",
            (turns, status, battle_id),
        )
