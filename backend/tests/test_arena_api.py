"""
test_arena_api.py — REST + WebSocket contract tests for the LOUGH Arena.

Run:  python3 -m pytest tests/   (inside backend/, with .venv)
"""

from __future__ import annotations

import socket
import threading
import time

import httpx
import pytest
import uvicorn
from fastapi.testclient import TestClient
from websockets.sync.client import connect as ws_connect

from app import app

client = TestClient(app)


# ── Real-server fixture ─────────────────────────────────────────────────
# TestClient freezes asyncio background tasks between requests (its portal
# only pumps the loop while a request is in flight). The arena round/battle
# runners are background tasks, so those paths are tested against a real
# uvicorn server — which is also the documented deployment mode.

@pytest.fixture(scope="module")
def server_url():
    sock = socket.socket()
    sock.bind(("127.0.0.1", 0))
    port = sock.getsockname()[1]
    sock.close()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    for _ in range(100):
        if server.started:
            break
        time.sleep(0.1)
    yield f"http://127.0.0.1:{port}"
    server.should_exit = True
    thread.join(timeout=5)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["engine"] == "MikeySwarm"
    assert body["db_runs"] >= 77
    assert body["memgate"]["verdict"] in ("PASS", "WARN", "BLOCK")


def _inference_available() -> bool:
    """True when a live Groq key is configured. In CI (no secrets) the
    pool degrades to unavailable — these tests skip rather than fail so
    the suite still gates the engine on keyless runners."""
    r = client.get("/api/v1/inference/pool")
    return r.status_code == 200 and r.json().get("available") is True


def test_health_includes_inference_pool():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    inf = r.json()["inference"]
    if not inf["available"]:
        pytest.skip("no Groq key — live inference unavailable in this environment")
    assert inf["groq_pool"]["pool_size"] >= 1
    assert inf["providers"]["groq"] is True


def test_inference_pool_endpoint():
    r = client.get("/api/v1/inference/pool")
    assert r.status_code == 200
    body = r.json()
    if not body["available"]:
        pytest.skip("no Groq key — live inference unavailable in this environment")
    pool = body["groq_pool"]
    assert pool["pool_size"] == len(pool["keys"])
    for entry in pool["keys"]:
        # hints only — never leak full keys over the wire
        assert not entry["hint"].startswith("gsk_")
        assert set(entry) >= {"hint", "dead", "cooldown", "failures"}


def test_tasks():
    r = client.get("/api/v1/tasks")
    assert r.status_code == 200
    tasks = r.json()
    assert len(tasks) >= 5
    assert tasks[0]["task_id"] == "task_001_legal_analysis"


def test_score_simulated():
    r = client.post(
        "/api/v1/score",
        json={"task_id": "task_001_legal_analysis", "response_text": "test submission"},
    )
    assert r.status_code == 200
    body = r.json()
    assert 0.0 <= body["mike_delta"] <= 1.0
    assert body["outcome"] in ("pass", "drift", "fail")
    assert set(body["traits"]) >= {
        "directness",
        "investigation",
        "systems_thinking",
        "anti_larp",
        "no_hedging",
    }
    assert body["baselines"]["A_persona"] == 0.925


def test_score_explicit_traits():
    r = client.post(
        "/api/v1/score",
        json={
            "task_id": "task_003_code_review",
            "traits": {
                "directness": 1.0,
                "investigation": 1.0,
                "systems_thinking": 1.0,
                "anti_larp": 1.0,
                "no_hedging": 1.0,
            },
        },
    )
    assert r.status_code == 200
    assert r.json()["mike_delta"] == 1.0
    assert r.json()["outcome"] == "pass"


def test_score_unknown_task():
    r = client.post("/api/v1/score", json={"task_id": "nope"})
    assert r.status_code == 404


def test_runs_corpus():
    r = client.get("/api/v1/runs?group=A&limit=5")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) <= 5
    assert all(row["group_type"] == "A" for row in rows)


def test_runs_corpus_db_error_handling(monkeypatch):
    """Verify database exceptions return generic 500 detail without leaking filesystem paths or DB errors."""
    import sqlite3

    def mock_connect(*args, **kwargs):
        raise sqlite3.Error("sqlite error exposing /home/jules/secret_path/persona_runs.db")

    monkeypatch.setattr(sqlite3, "connect", mock_connect)
    r = client.get("/api/v1/runs")
    assert r.status_code == 500
    assert r.json()["detail"] == "corpus read failed"


def test_groups():
    r = client.get("/api/v1/groups")
    assert r.status_code == 200
    groups = r.json()
    ids = [g["group_type"] for g in groups]
    assert "A" in ids and "B" in ids and "C" in ids
    assert all(0.0 <= g["avg_score"] <= 1.0 for g in groups)


def test_persona_get():
    r = client.get("/api/v1/persona")
    assert r.status_code == 200
    assert r.json()["identifier"] == "mikey-seed-v1"


def test_persona_put():
    r = client.put(
        "/api/v1/persona",
        json={"seed": {"identifier": "test-seed", "weights": {}}},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "stored"


def test_arena_run_and_poll(server_url):
    with httpx.Client(base_url=server_url, timeout=10) as c:
        r = c.post("/api/v1/arena/run", json={"groups": ["A"], "task_ids": ["task_001_legal_analysis"]})
        assert r.status_code == 200
        round_id = r.json()["round_id"]

        for _ in range(50):
            rr = c.get(f"/api/v1/arena/round/{round_id}")
            assert rr.status_code == 200
            if rr.json()["status"] == "complete":
                break
            time.sleep(0.1)
        else:
            raise AssertionError("round did not complete in time")

        body = rr.json()
        events = body["events"]
        assert len(events) == 1
        assert events[0]["group"] == "A"
        assert events[0]["outcome"] in ("pass", "drift", "fail")


def test_arena_run_bad_group():
    r = client.post("/api/v1/arena/run", json={"groups": ["Z"]})
    assert r.status_code == 400


def test_battle_start():
    r = client.post(
        "/api/v1/battle",
        json={"duress_level": "pressure", "contradiction_seed": "reverse all rules", "turns": 2},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "running"
    assert r.json()["battle_id"] > 0


def test_ws_telemetry():
    with client.websocket_connect("/api/v1/ws/telemetry") as ws:
        frame = ws.receive_json()
        assert "mem" in frame
        assert "available_mb" in frame["mem"]
        assert "memgate" in frame


def test_ws_run_streams(server_url):
    # Run a round to completion, then attach late — the feed must replay
    # every persisted event and end with "done". No missed events.
    with httpx.Client(base_url=server_url, timeout=10) as c:
        r = c.post(
            "/api/v1/arena/run",
            json={"groups": ["A", "B"], "task_ids": ["task_001_legal_analysis", "task_002_file_organization"]},
        )
        round_id = r.json()["round_id"]

        for _ in range(50):
            rr = c.get(f"/api/v1/arena/round/{round_id}")
            if rr.json()["status"] == "complete":
                break
            time.sleep(0.1)
        else:
            raise AssertionError("round did not complete")

    ws_url = server_url.replace("http", "ws", 1) + f"/api/v1/ws/run/{round_id}"
    events = []
    with ws_connect(ws_url, close_timeout=5) as ws:
        while True:
            msg = ws.recv(timeout=15)
            events.append(__import__("json").loads(msg))
            if events[-1]["type"] == "done":
                break

    types = {e["type"] for e in events}
    assert "task" in types
    assert "done" in types
    # 2 groups × 2 tasks + done — full replay, no missed events
    assert len([e for e in events if e["type"] == "task"]) == 4


def test_agents_list():
    r = client.get("/api/v1/agents")
    assert r.status_code == 200
    agents = r.json()
    assert any(a["agent_id"] == "test_clone_006" for a in agents)


def test_agents_register_and_status():
    import uuid

    agent_id = f"test_arena_clone_{uuid.uuid4().hex[:8]}"
    r = client.post(
        "/api/v1/agents/register",
        json={"agent_id": agent_id, "template": "variant"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "registered"
    assert r.json()["weights"]["legal"] < 1.0  # variant template modified weights

    r = client.get(f"/api/v1/agents/{agent_id}")
    assert r.status_code == 200
    assert r.json()["agent_id"] == agent_id


def test_agents_register_duplicate():
    # test_clone_006 already exists in the persisted registry
    r = client.post(
        "/api/v1/agents/register",
        json={"agent_id": "test_clone_006", "template": "variant"},
    )
    assert r.status_code == 409


def test_agents_run_dry_run_default():
    import uuid

    agent_id = f"test_dryrun_{uuid.uuid4().hex[:8]}"
    client.post("/api/v1/agents/register", json={"agent_id": agent_id, "template": "variant"})

    # Default (no persist) must not write to the corpus or agent state.
    r = client.post(
        f"/api/v1/agents/{agent_id}/run",
        json={"task_id": "task_001_legal_analysis", "group": "A"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["dry_run"] is True
    assert 0.0 <= body["score"] <= 1.0
    assert body["outcome"] in ("pass", "drift", "fail")

    # status must show zero persisted runs
    st = client.get(f"/api/v1/agents/{agent_id}").json()
    assert st["experiments_run"] == 0
    assert st["results"] == []


def test_agents_run_unknown_agent():
    r = client.post(
        "/api/v1/agents/nope/run",
        json={"task_id": "task_001_legal_analysis", "group": "A"},
    )
    assert r.status_code == 404


def test_agents_run_unknown_task():
    r = client.post(
        "/api/v1/agents/test_clone_006/run",
        json={"task_id": "nope", "group": "A"},
    )
    assert r.status_code == 404


def test_corpus_untouched():
    """The arena must never write to persona_runs.db — verify byte-identical."""
    from pathlib import Path

    db_path = Path.home() / "MikeySwarm" / "persona_runs.db"
    before = db_path.read_bytes()
    client.get("/api/v1/groups")
    client.get("/api/v1/runs")
    after = db_path.read_bytes()
    assert before == after
