"""
app.py — Skin-Deep LOUGH Arena FastAPI entrypoint.

Runs the Mikey experiment engine as the assessment backend for the
Lancy-Lough Digital Apprenticeship. Engine lives in ~/MikeySwarm and is
imported read-only; this service owns the human-benchmark / battle arena.

Boot:  uvicorn app:app --port 8765   (from backend/, inside .venv)
"""

from __future__ import annotations

from pathlib import Path
import sys

# The Mikey engine is pure-python (json/random/sqlite3/hashlib) and safe to
# import. Source of truth: ~/MikeySwarm. Never write to its DB from here.
MIKEY_ROOT: Path = Path.home() / "MikeySwarm"
if str(MIKEY_ROOT) not in sys.path:
    sys.path.insert(0, str(MIKEY_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from arena_api import router as arena_router

# Storyboard engine (Skin Deep production tooling) lives in its own dir;
# mount its router + static UI/images/exports alongside the arena.
STORYBOARD_ROOT: Path = Path(__file__).resolve().parent.parent / "storyboard"
if str(STORYBOARD_ROOT) not in sys.path:
    sys.path.insert(0, str(STORYBOARD_ROOT))

from storyboard_api import router as storyboard_router  # noqa: E402

for _d in ("static", "images", "exports", "episodes"):
    (STORYBOARD_ROOT / _d).mkdir(exist_ok=True)

app = FastAPI(
    title="Skin-Deep LOUGH Arena",
    description=(
        "Mikey behavioral engine as the Lough Digital Apprenticeship "
        "assessment layer — 5-dimension scoring, live swarm runs, telemetry."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # local dev; tighten for deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(arena_router, prefix="/api/v1")
app.include_router(storyboard_router, prefix="/api/v1/storyboard")

app.mount("/storyboard", StaticFiles(directory=STORYBOARD_ROOT / "static", html=True), name="storyboard-ui")
app.mount("/storyboard/images", StaticFiles(directory=STORYBOARD_ROOT / "images", html=False), name="storyboard-images")
app.mount("/storyboard/exports", StaticFiles(directory=STORYBOARD_ROOT / "exports", html=False), name="storyboard-exports")
app.mount("/storyboard/episodes", StaticFiles(directory=STORYBOARD_ROOT / "episodes", html=False), name="storyboard-episodes")


@app.get("/", include_in_schema=False)
async def root() -> dict:
    return {"service": "Skin-Deep LOUGH Arena", "docs": "/docs", "storyboard": "/storyboard/"}
