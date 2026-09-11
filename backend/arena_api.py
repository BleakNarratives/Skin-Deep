"""
arena_api.py — REST + WebSocket endpoints for the Skin-Deep LOUGH Arena.

Contract lives in ../CONNECTED_BUILD.md. The Mikey engine (~/MikeySwarm) is
imported read-only; nothing here ever writes to persona_runs.db.
"""

from __future__ import annotations

import asyncio
import json
import random
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

import arena_db
import telemetry

# Canonical MikeySwarm Multi-Agent Orchestrator (~/MikeySwarm/orchestrator.py,
# merged from multi_agent_overseer_fixed + unified_orchestrator 2026-08-26).
# Imported for the clone registry + clone experiment endpoints. Its module
# level has no side effects; load_agent_state() is called explicitly below.
import orchestrator as orch

# ── Mikey engine (imported read-only via sys.path in app.py) ────────────
from run_round2 import (
    PERSONA,
    TASKS,
    compute_mike_delta,
    simulate_response_a,
    simulate_response_b,
    simulate_response_c,
)
from swarm_overseer import DB_PATH as MIKEY_DB

router = APIRouter()

# group → simulator (canonical, mirrors swarm_overseer.GROUP_RUNNERS)
SIMULATORS: dict[str, Any] = {
    "A": simulate_response_a,
    "B": simulate_response_b,
    "C": simulate_response_c,
}

arena_db.init_db()

# live websocket subscribers: round_id -> set[WebSocket]
RUN_SUBSCRIBERS: dict[str, set[WebSocket]] = {}

# Strong references to background tasks — asyncio only holds weak refs, so
# an unreferenced task gets GC'd mid-run. Registry prevents that.
_BACKGROUND_TASKS: set[asyncio.Task] = set()


def _spawn(coro: Any) -> asyncio.Task:
    task = asyncio.create_task(coro)
    _BACKGROUND_TASKS.add(task)
    task.add_done_callback(_BACKGROUND_TASKS.discard)
    return task


# ── REST ────────────────────────────────────────────────────────────────


class ScoreRequest(BaseModel):
    task_id: str
    response_text: str = ""
    traits: dict[str, float] = Field(
        default_factory=dict,
        description="Optional explicit 5-dim traits (0-1). Empty = simulated group A traits.",
    )


class ArenaRunRequest(BaseModel):
    groups: list[str] = Field(default_factory=lambda: ["A", "B", "C"])
    task_ids: list[str] = Field(default_factory=list)  # empty = all tasks


class BattleRequest(BaseModel):
    duress_level: str = "none"  # none | pressure | critical
    contradiction_seed: str | None = None
    identity_shift: str | None = None
    turns: int = Field(default=3, ge=1, le=10)


class PersonaUpdate(BaseModel):
    seed: dict[str, Any]


class AgentRegisterRequest(BaseModel):
    agent_id: str = Field(min_length=1, max_length=64)
    template: str = "variant"


class AgentRunRequest(BaseModel):
    task_id: str
    group: str = "A"
    persist: bool = False  # False = dry run (no corpus/state/comms writes)


@router.get("/health")
async def health() -> dict:
    snap = telemetry.snapshot()
    return {
        "status": "ok",
        "engine": "MikeySwarm",
        "memgate": snap["memgate"],
        "db_runs": _count_mikey_runs(),
        "inference": orch.inference_pool_status(),
    }


@router.get("/inference/pool")
async def inference_pool() -> dict:
    """Groq key rotation pool health: pool size, per-key quarantine state
    (hints only — never full keys), and provider fallback chain."""
    return orch.inference_pool_status()


@router.get("/tasks")
async def tasks() -> list[dict]:
    return TASKS


@router.post("/score")
async def score(req: ScoreRequest) -> dict:
    task = next((t for t in TASKS if t["task_id"] == req.task_id), None)
    if task is None:
        raise HTTPException(status_code=404, detail=f"unknown task: {req.task_id}")

    if req.traits:
        response = {"alignment_traits": req.traits}
    else:
        # Human benchmark mode: simulate a group-A-style response and score it.
        response = simulate_response_a(task)
        if req.response_text:
            response["response_text"] = req.response_text

    mike_delta, outcome = compute_mike_delta(response, "A", task)
    traits = response.get("alignment_traits", {})

    row_id = arena_db.insert_human_score(
        req.task_id, req.response_text, mike_delta, outcome, traits
    )
    return {
        "id": row_id,
        "task_id": req.task_id,
        "task_description": task["description"],
        "mike_delta": mike_delta,
        "outcome": outcome,
        "traits": traits,
        "baselines": {
            "A_persona": 0.925,
            "B_contradictory": 0.228,
            "C_bare": 0.503,
        },
    }


@router.get("/runs")
async def runs(group: str | None = None, limit: int = 50) -> list[dict]:
    """Read-only analytics over the persona_runs.db corpus."""
    q = "SELECT * FROM persona_runs"
    args: list[Any] = []
    if group:
        q += " WHERE group_type = ?"
        args.append(group)
    q += " ORDER BY id DESC LIMIT ?"
    args.append(min(max(limit, 1), 500))
    try:
        with sqlite3.connect(MIKEY_DB) as conn:
            conn.row_factory = sqlite3.Row
            rows = [dict(r) for r in conn.execute(q, args).fetchall()]
    except sqlite3.Error:
        # Security: Do not expose raw SQLite exception strings to callers (prevents leakage of server filesystem paths/DB details).
        raise HTTPException(status_code=500, detail="corpus read failed")
    for r in rows:
        r.pop("response_summary", None)
        r.pop("response_text", None)
    return rows


@router.get("/groups")
async def groups() -> list[dict]:
    with sqlite3.connect(MIKEY_DB) as conn:
        conn.row_factory = sqlite3.Row
        rows = [
            dict(r)
            for r in conn.execute(
                """
                SELECT group_type, COUNT(*) AS runs,
                       ROUND(AVG(mike_delta_score), 3) AS avg_score,
                       SUM(CASE WHEN outcome='pass' THEN 1 ELSE 0 END) AS passes,
                       SUM(CASE WHEN outcome='fail' THEN 1 ELSE 0 END) AS fails
                FROM persona_runs GROUP BY group_type ORDER BY group_type
                """
            ).fetchall()
        ]
    return rows


@router.get("/persona")
async def persona() -> dict:
    return PERSONA


@router.put("/persona")
async def persona_update(req: PersonaUpdate) -> dict:
    """Persist a customized seed to arena.db. NEVER touches the canonical seed."""
    arena_db.get_conn().execute(
        "INSERT INTO persona_custom (created, seed) VALUES (?, ?)",
        (arena_db._now(), json.dumps(req.seed)),
    )
    return {"status": "stored", "identifier": req.seed.get("identifier", "custom")}


# ── Multi-Agent Clone Registry (orchestrator integration) ─────────────


def _orch_state_loaded() -> None:
    """Ensure the orchestrator has loaded agent_state.json before reads."""
    if not orch.AGENT_STATE:
        orch.load_agent_state()


@router.get("/agents")
async def agents_list() -> list[dict]:
    _orch_state_loaded()
    out = []
    for agent_id in orch.list_registered_agents():
        info = orch.AGENT_STATE[agent_id]
        cfg = info["config"]
        out.append(
            {
                "agent_id": agent_id,
                "status": info.get("status"),
                "experiments_run": info.get("experiments_run", 0),
                "last_activity": info.get("last_activity"),
                "weights": getattr(cfg, "weights", None),
                "temperature": getattr(cfg, "temperature", None),
            }
        )
    return out


@router.post("/agents/register")
async def agents_register(req: AgentRegisterRequest) -> dict:
    _orch_state_loaded()
    if req.agent_id in orch.AGENT_STATE:
        raise HTTPException(status_code=409, detail=f"agent already registered: {req.agent_id}")
    try:
        cfg = orch.AgentClone.create_from_template(req.agent_id, req.template)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    ok = orch.register_agent_clone(cfg)
    if not ok:
        raise HTTPException(status_code=500, detail="orchestrator failed to register agent")
    return {"agent_id": req.agent_id, "status": "registered", "weights": cfg.weights}


@router.get("/agents/{agent_id}")
async def agents_status(agent_id: str) -> dict:
    _orch_state_loaded()
    if agent_id not in orch.AGENT_STATE:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    info = orch.AGENT_STATE[agent_id]
    return {
        "agent_id": agent_id,
        "status": info.get("status"),
        "experiments_run": info.get("experiments_run", 0),
        "last_activity": info.get("last_activity"),
        "results": info.get("results", []),
        "config": getattr(info.get("config"), "to_dict", lambda: {})() if info.get("config") else {},
    }


@router.post("/agents/{agent_id}/run")
async def agents_run(agent_id: str, req: AgentRunRequest) -> dict:
    _orch_state_loaded()
    if agent_id not in orch.AGENT_STATE:
        raise HTTPException(status_code=404, detail=f"unknown agent: {agent_id}")
    if req.group not in orch.GROUP_RUNNERS:
        raise HTTPException(status_code=400, detail=f"unknown group: {req.group}")
    if not any(t["task_id"] == req.task_id for t in orch.TASKS):
        raise HTTPException(status_code=404, detail=f"unknown task: {req.task_id}")

    cfg = orch.AGENT_STATE[agent_id]["config"]
    # dry_run by default — the arena never writes the corpus silently.
    # persist=True opts into the canonical overseer persistence path.
    result = orch.run_experiment_for_clone(
        agent_id, req.task_id, req.group, cfg, dry_run=not req.persist
    )
    if not result.get("success"):
        raise HTTPException(status_code=500, detail=result.get("error", "clone run failed"))
    return {
        "agent_id": agent_id,
        "task_id": result["task_id"],
        "group": result["group"],
        "score": result["score"],
        "outcome": result["outcome"],
        "dry_run": not req.persist,
    }


@router.post("/arena/run")
async def arena_run(req: ArenaRunRequest) -> dict:
    groups = [g.upper() for g in req.groups]
    unknown = [g for g in groups if g not in SIMULATORS]
    if unknown:
        raise HTTPException(status_code=400, detail=f"unknown groups: {unknown}")

    # memgate pre-flight — refuse to run a live round under pressure
    verdict, _ = memgate_verdict()
    if verdict == "BLOCK":
        raise HTTPException(
            status_code=503,
            detail="memgate BLOCK — memory pressure too high for live round (MEMGATE_FORCE=1 to override)",
        )

    round_id = f"round_{uuid.uuid4().hex[:8]}"
    task_ids = req.task_ids or [t["task_id"] for t in TASKS]
    arena_db.create_round(round_id, groups)
    _spawn(_run_round(round_id, groups, task_ids))
    return {"round_id": round_id, "groups": groups, "tasks": task_ids}


@router.get("/arena/round/{round_id}")
async def arena_round(round_id: str) -> dict:
    r = arena_db.get_round(round_id)
    if r is None:
        raise HTTPException(status_code=404, detail=f"unknown round: {round_id}")
    r["events"] = json.loads(r["events"]) if r.get("events") else []
    return r


@router.post("/battle")
async def battle_start(req: BattleRequest) -> dict:
    battle_id = arena_db.insert_battle(req.model_dump())
    _spawn(_run_battle(battle_id, req))
    return {"battle_id": battle_id, "status": "running", "params": req.model_dump()}


# ── WebSockets ──────────────────────────────────────────────────────────


@router.websocket("/ws/telemetry")
async def ws_telemetry(ws: WebSocket) -> None:
    await ws.accept()
    try:
        while True:
            await ws.send_json(telemetry.snapshot())
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass


@router.websocket("/ws/run/{round_id}")
async def ws_run(ws: WebSocket, round_id: str) -> None:
    """Live round feed with catch-up replay.

    Late joiners get every event persisted so far (replayed from arena.db),
    then receive live events. If the round already finished, replay ends
    with a synthetic "done" event.
    """
    await ws.accept()

    # Catch-up replay — deterministic for late subscribers
    r = arena_db.get_round(round_id)
    if r is not None:
        for event in json.loads(r.get("events") or "[]"):
            await ws.send_json(event)
        if r["status"] == "complete":
            await ws.send_json({"type": "done", "round_id": round_id})
            await ws.close()
            return

    RUN_SUBSCRIBERS.setdefault(round_id, set()).add(ws)
    try:
        while True:
            await asyncio.sleep(10)  # keepalive; events pushed via _broadcast
    except WebSocketDisconnect:
        RUN_SUBSCRIBERS.get(round_id, set()).discard(ws)


# ── Internals ───────────────────────────────────────────────────────────


def _count_mikey_runs() -> int:
    try:
        with sqlite3.connect(MIKEY_DB) as conn:
            return conn.execute("SELECT COUNT(*) FROM persona_runs").fetchone()[0]
    except sqlite3.Error:
        return -1


def memgate_verdict() -> tuple[str, list[str]]:
    snap = telemetry.snapshot()
    return snap["memgate"]["verdict"], snap["memgate"]["reasons"]


async def _broadcast(round_id: str, event: dict) -> None:
    dead: list[WebSocket] = []
    for ws in RUN_SUBSCRIBERS.get(round_id, set()):
        try:
            await ws.send_json(event)
        except Exception:
            dead.append(ws)
    for ws in dead:
        RUN_SUBSCRIBERS.get(round_id, set()).discard(ws)


async def _run_round(round_id: str, groups: list[str], task_ids: list[str]) -> None:
    tasks = [t for t in TASKS if t["task_id"] in task_ids]
    for group in groups:
        sim = SIMULATORS[group]
        for task in tasks:
            response = sim(task)
            score, outcome = compute_mike_delta(response, group, task)
            event = {
                "type": "task",
                "group": group,
                "task_id": task["task_id"],
                "mike_delta": score,
                "outcome": outcome,
                "traits": response.get("alignment_traits", {}),
            }
            arena_db.append_round_event(round_id, event)
            await _broadcast(round_id, event)
            await asyncio.sleep(0.2)  # let the stream breathe
    arena_db.finish_round(round_id)
    await _broadcast(round_id, {"type": "done", "round_id": round_id})


async def _run_battle(battle_id: int, req: BattleRequest) -> None:
    """Role-reversal: adversarial conditions applied to simulated agents."""
    turns_done = 0
    for i in range(req.turns):
        # adversary flip-flops the group identity each turn
        group = "B" if i % 2 == 0 else "C"
        task = random.choice(TASKS)
        response = SIMULATORS[group](task)
        if req.contradiction_seed:
            response["alignment_traits"] = {
                k: max(0.0, v - 0.35) for k, v in response.get("alignment_traits", {}).items()
            }
        score, outcome = compute_mike_delta(response, group, task)
        turns_done += 1
        await asyncio.sleep(0.3)
    arena_db.update_battle(battle_id, turns_done, "complete")
