# CONNECTED_BUILD — Mikey Arena × Skin-Deep LOUGH

**Date:** 2026-08-26
**Status:** APPROVED — both repositories, one system
**Operators:** Mike (BleakNarratives) + Buffy (Codebuff) + Google Jules
**Repos:** `~/MikeySwarm` (engine, source of truth) + `~/Skin-Deep` (frontend, LOUGH)

---

## The Vision

The Mikey behavioral experiment platform is the **assessment engine** for the
Lancy-Lough Digital Apprenticeship. An apprentice submits work; the engine
scores it across the 5 Mikey dimensions; the LOUGH React app renders the
results, streams live telemetry, and persists every session to SQLite.

One system, two repos:

```
~/MikeySwarm  (EXISTING, VERIFIED)          ~/Skin-Deep  (EXISTING, PROMOTED)
├── persona_runs.db   — 77 runs, A–H       ├── Lancy-Lough-Digital-Apprenticeship/
├── run_round2.py     — TASKS + PERSONA    │   └── React 19 + Vite + recharts app
│                      + 5-dim scoring     ├── code/*.py — ink/skin sims (heavy native
├── swarm_overseer.py — coordinator        │               deps, NOT web-servable as-is)
├── memgate.py        — memory gate        └── backend/  ← NEW FastAPI service
├── landing/          — design system
└── WHITE_PAPER.md    — v1.4 + release kit
```

## Architecture

### Layer 1 — Engine (unchanged, imported read-only)
`backend/arena_api.py` imports from `~/MikeySwarm` via `sys.path`:

- `run_round2.PERSONA`, `TASKS`, `simulate_response_a/b/c`, `compute_mike_delta`
- `memgate.check()` / `memgate.guard()` — pre-flight gate
- `swarm_overseer.Overseer` — live experiment runner
- `persona_runs.db` — read-only historical corpus

**NEVER write to `persona_runs.db` from the arena.** Historical corpus is
sacred (77 runs, provenance-verified). Human benchmark + battle results go to
`~/Skin-Deep/backend/arena.db`.

### Layer 1.5 — Multi-Agent Orchestrator (CANONICAL, MERGED 2026-08-26)

`~/MikeySwarm/orchestrator.py` — the SINGLE canonical orchestrator, merged
from `multi_agent_overseer_fixed.py` + `unified_orchestrator.py` (both
deleted). One state file (`agent_state.json`), one CLI, one import surface
for the arena. The merge keeps all fixes:

1. **Clone configs actually matter.** `AgentSpecificOverseer` builds the
   response from the clone's own weights (same trait formulas as Group-A
   simulation) and scores with the canonical `compute_mike_delta`.
2. **dry_run has zero side effects.** No DB writes, no agent_state
   mutation, no comms, no integration log. Verified: corpus stayed at 94
   rows through dry runs.
3. **Bardildo mode is REAL (2026-08-26).** The fake `bardildo.Bardildo`
   import (the on-disk bardildo.py is a repo scanner, not a creative AI)
   was replaced with `GroqBardildoClient` — live `openai/gpt-oss-120b`
   inference via the Boardroom router. Enhanced experiments now generate
   actual creative insights (DNA-strand metaphor for legal analysis),
   judge them on 5 creative dimensions, and fold the bonus into the
   composite with the factor. Verified: base 0.895 + 0.176 bonus = 1.000
   at 1.5x. If the router is ever down, init fails loudly — no fake
   enhancement.
4. **Run-time flags applied at EXPERIMENT time** — `--dry-run`,
   `--bardildo-mode`, `--creative-factor` are folded into the loaded
   config, fixing the dry-run-corruption bug.
5. **Frozen dataclasses handled with `replace()`.**
6. **Groq key rotation pool (2026-08-26).** The Boardroom router now
   runs a health-aware key pool: 401/403 quarantines a key dead (5-min
   TTL), 429 cooldowns it 15s while other keys serve, rotation skips
   dead keys, and a success releases a recovered key. Pool health is
   exposed via `groq_pool_status()` (hints only — never full keys) and
   surfaced through the arena at `GET /api/v1/inference/pool` + the
   `inference` field on `/api/v1/health`. Failover PROVEN by test:
   injected fake key 401s → quarantined → live key serves the call
   (test_key_pool.py, 3/3). Add a second key: comma-separate it in
   `~/Official-Vertical-AI-Boardroom/.env` (`GROQ_API_KEY=k1,k2`).

The arena exposes the clone registry via REST (below). Clone runs default
`dry_run=true`; `persist=true` opts into the canonical corpus write.

### Layer 2 — API (NEW: `~/Skin-Deep/backend/`)

```
backend/
├── app.py            — FastAPI app, CORS, mounts arena_api router
├── arena_api.py      — REST + WebSocket endpoints (below)
├── arena_db.py       — arena.db schema + persistence (human_scores, battles)
├── telemetry.py      — meminfo/PSI/memguard_state readers (memgate + /proc)
├── requirements.txt  — fastapi, uvicorn[standard], websockets
└── tests/
    └── test_arena_api.py — httpx TestClient suite
```

### Layer 3 — UI (extend existing React app)

`Lancy-Lough-Digital-Apprenticeship/` gains 4 surfaces (all in the existing
design system: dark #0e0c09, cream/gold/crimson, Playfair/Bebas/Courier):

| Surface | Purpose | Existing assets |
|---|---|---|
| Human Benchmark Arena | Apprentice completes task → 5-dim score → radar chart | `DataChart.tsx` (recharts), `ChatInterface.tsx` |
| Role-Reversal Playground | Adversarial controls: duress, contradiction seeds, identity shifts | `HapticFeedbackSimulator.tsx`, `VideoDataOverlay.tsx` |
| Live Swarm Orchestrator | Memory gauges, live run logs, group comparison | `VideoDataOverlay.tsx` + WebSocket |
| Scorecard + Easter Eggs | Consistency/variance vs Mikey baselines (A 0.925, B 0.228, C 0.503…) | `DataChart.tsx` |

### Layer 4 — Telemetry & WebSockets

- `WS /ws/telemetry` — 2s cadence: MemAvailable MB, PSI avg10, memguard state
  (reads `~/MikeySwarm/logs/memguard/memguard_state.json` + `/proc/meminfo`)
- `WS /ws/run/{round_id}` — live task-by-task output + scoring events
- `WS /ws/arena/{battle_id}` — role-reversal battle turns

## Endpoint Contract

```
GET  /api/v1/health               → {status, memgate: {verdict, reasons}}
GET  /api/v1/tasks                → TASKS from run_round2
POST /api/v1/score                → {task_id, response_text} → {mike_delta, outcome, traits}
                                     (wraps compute_mike_delta; human benchmark mode)
GET  /api/v1/runs?group=A         → read-only persona_runs.db analytics
GET  /api/v1/groups               → group averages/outcomes (A–H corpus)
GET  /api/v1/persona              → persona_seed.json
PUT  /api/v1/persona              → customized seed (validated, written to arena.db, NOT canonical seed)
GET  /api/v1/agents               → registered clone roster (agent_state.json)
POST /api/v1/agents/register      → {agent_id, template} → registered clone
GET  /api/v1/agents/{agent_id}    → clone config, results, run count
POST /api/v1/agents/{id}/run      → {task_id, group, persist=false} → score/outcome
                                     (dry-run default — arena never writes the corpus silently)
POST /api/v1/arena/run            → {groups: ["A","B","C"]} → round_id, streams on /ws/run/{id}
POST /api/v1/battle               → role-reversal battle start (adversarial params in body)
WS   /ws/telemetry                → live system state
WS   /ws/run/{round_id}           → live run events (with catch-up replay)
WS   /ws/arena/{battle_id}        → battle turns
```

## Execution Order (for Jules / Copilot)

1. **Scaffold** `~/Skin-Deep/backend/` per layout above. `requirements.txt`:
   `fastapi>=0.115`, `uvicorn[standard]>=0.32`, `websockets>=12`.
   Venv: `~/Skin-Deep/.venv` (per-project convention).
2. **Verify engine import** early: `from run_round2 import TASKS, PERSONA,
   compute_mike_delta` via `sys.path.insert(0, str(Path.home()/"MikeySwarm"))`.
   Engine is pure-python (json/random/sqlite3/hashlib only) — imports clean.
3. **Implement REST** endpoints in `arena_api.py` (contract above). Read-only
   DB access via `sqlite3` (already a dependency — do NOT pull SQLAlchemy).
4. **Implement WebSockets** with the telemetry + run streaming contracts.
   Reuse the memgate/memguard readers (`memgate.check()`, state JSON).
5. **Extend the React app**: add the 4 surfaces. Keep the existing design
   tokens. Add `fetch`/`WebSocket` client in `services/` (geminiService.ts is
   the model for a new `arenaService.ts`).
6. **Tests**: `tests/test_arena_api.py` with httpx TestClient — health,
   tasks, score, runs, persona, arena run (dry-run mode), WS connect.
7. **Boot verification**: `uvicorn app:app --port 8765`, curl every REST
   endpoint, `python3 -m pytest tests/`. Overseer suite stays green
   (`python3 ~/MikeySwarm/test_swarm_overseer.py`).
8. **Pre-commit**: compile-check all py, run both test suites, keep
   persona_runs.db untouched (verify byte-identical before commit).

## Constraints (non-negotiable)

- `persona_runs.db` is **read-only** from the arena. Back it up before first boot.
- Do NOT install into global python; per-project venv only.
- The heavy sims (`code/*.py`: cv2, mediapipe, open3d, pyrealsense2) are NOT
  part of this build — they stay CLI tools. The arena serves the *scoring
  engine*, not the simulations.
- No new UI framework — extend the existing React 19 + Vite app and its
  design tokens. Landing page at `~/MikeySwarm/landing/` is the style bible.
- No emojis in UI output. Dark #0e0c09 / cream / gold / crimson / tan / silver.
- memgate guard runs before any live arena round; MEMGATE_FORCE=1 for tests.
- This VM has 2.6GB RAM and a swapfile. Long WS broadcasts must be
  lightweight (2s cadence, small payloads). Do not stream full model output.

## Success Criteria

- [x] `uvicorn app:app` boots, all REST endpoints curl 200 (verified 2026-08-26)
- [x] Human benchmark POST /score returns mike_delta + traits + outcome
- [x] WS /ws/telemetry streams meminfo/PSI/memguard state
- [x] WS /ws/run/{id} replays full history for late subscribers
- [x] Arena round runs Groups A–C live, events stream over WS, results land
      in arena.db (not persona_runs.db)
- [x] Clone registry: register/list/run/status via /api/v1/agents; dry-run
      default keeps the corpus untouched (verified: corpus stayed 78 rows)
- [x] Clone configs affect scores (legal-heavy 0.63 vs systems-heavy 0.556,
      variant clone 0.895 vs base 0.92)
- [x] multi_agent_overseer_fixed.py + unified_orchestrator.py merged into
      one canonical orchestrator.py (single state file agent_state.json,
      one CLI); dry-run side-effect-free, Bardildo fails loudly, frozen
      dataclass replace(), arena imports orchestrator as orch
- [ ] React app renders radar chart of a scored apprentice session
- [x] Test suite green (21/21); persona_runs.db byte-identical before/after
