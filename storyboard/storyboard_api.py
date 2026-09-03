"""
storyboard_api.py — REST endpoints for the Skin Deep storyboard engine.

Mounted by backend/app.py at /api/v1/storyboard. Generation endpoints are
synchronous on purpose: localhost, one operator, and the Boardroom router
already owns backoff/retry. Slow calls are expected; fast failures are not.
"""

from __future__ import annotations

import csv
import html
import io
import json
import sys
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel, Field

SB_DIR = Path(__file__).parent
if str(SB_DIR) not in sys.path:
    sys.path.insert(0, str(SB_DIR))

import storyboard_db as db  # noqa: E402
import storyboard_gen as gen  # noqa: E402

router = APIRouter()

db.init_db()

EXPORTS_DIR = gen.EXPORTS_DIR
EPISODES_DIR = gen.EPISODES_DIR


# ── request bodies ───────────────────────────────────────────────────────

class EpisodeCreate(BaseModel):
    season: int = 1
    number: int = 1
    # Security: Restrict slug to safe alphanumeric characters, hyphens, and underscores.
    # Prevents directory traversal attacks when writing markdown outlines to filesystem (episodes/{slug}.md).
    slug: str = Field(min_length=2, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    title: str = Field(min_length=1, max_length=200)
    logline: str = ""
    outline: str = ""  # markdown; written to episodes/{slug}.md


class PanelPatch(BaseModel):
    shot_type: str | None = None
    camera_move: str | None = None
    action: str | None = None
    vo_speaker: str | None = None
    vo_line: str | None = None
    on_screen_text: str | None = None
    duration_sec: float | None = Field(default=None, gt=0.1, le=60)
    visual_prompt: str | None = None
    ord: int | None = None


def _episode_or_404(episode_id: int) -> dict:
    ep = db.get_episode(episode_id)
    if ep is None:
        raise HTTPException(404, f"episode {episode_id} not found")
    return dict(ep)


def _panel_or_404(panel_id: int) -> dict:
    p = db.get_panel(panel_id)
    if p is None:
        raise HTTPException(404, f"panel {panel_id} not found")
    return dict(p)


def _outline_text(ep: dict, override: str = "") -> str:
    if override.strip():
        return override
    if not ep.get("outline_path"):
        raise HTTPException(400, f"episode '{ep['slug']}' has no outline file")
    # Security: Ensure path remains inside SB_DIR to prevent directory traversal attacks
    path = (SB_DIR / ep["outline_path"]).resolve()
    if not path.is_relative_to(SB_DIR.resolve()):
        raise HTTPException(400, "invalid outline path")
    if path.exists():
        return path.read_text(errors="replace")
    raise HTTPException(400, f"episode '{ep['slug']}' has no outline file")


def _gen_fail(e: gen.GenerationError) -> HTTPException:
    return HTTPException(
        502,
        detail={
            "stage": e.stage,
            "cause": e.cause,
            "raw_excerpt": e.raw[:1200],
        },
    )


# ── episodes ─────────────────────────────────────────────────────────────

@router.get("/episodes")
def list_episodes() -> list[dict]:
    return db.list_episodes()


@router.post("/episodes", status_code=201)
def create_episode(body: EpisodeCreate) -> dict:
    if db.get_episode_by_slug(body.slug):
        raise HTTPException(409, f"slug '{body.slug}' already exists")
    outline_rel = ""
    if body.outline.strip():
        EPISODES_DIR.mkdir(parents=True, exist_ok=True)
        f = EPISODES_DIR / f"{body.slug}.md"
        f.write_text(body.outline, encoding="utf-8")
        outline_rel = str(f.relative_to(SB_DIR))
    ep = db.create_episode(body.season, body.number, body.slug, body.title,
                           body.logline, outline_rel)
    return ep


@router.get("/episodes/{episode_id}")
def get_episode(episode_id: int) -> dict:
    tree = db.episode_tree(episode_id)
    if tree is None:
        raise HTTPException(404, f"episode {episode_id} not found")
    return tree


@router.delete("/episodes/{episode_id}")
def delete_episode(episode_id: int) -> dict:
    _episode_or_404(episode_id)
    db.delete_episode(episode_id)
    return {"deleted": episode_id}


# ── AI generation stages ─────────────────────────────────────────────────

@router.post("/episodes/{episode_id}/scenes")
def generate_scenes(episode_id: int, body: dict | None = None) -> dict:
    ep = _episode_or_404(episode_id)
    outline = _outline_text(ep, (body or {}).get("outline", ""))
    try:
        scenes, provider = gen.generate_scenes(outline)
    except gen.GenerationError as e:
        raise _gen_fail(e)
    db.replace_scenes(episode_id, scenes, {"provider": provider})
    return {"scenes": len(scenes), "provider": provider}


@router.post("/episodes/{episode_id}/panels")
def generate_panels(episode_id: int) -> dict:
    ep = _episode_or_404(episode_id)
    scenes = db.list_scenes(episode_id)
    if not scenes:
        raise HTTPException(400, "no scenes yet — POST /scenes first")
    made, provider = 0, "unknown"
    for scene in scenes:
        try:
            panels, provider = gen.generate_panels(scene, ep["title"])
        except gen.GenerationError as e:
            raise _gen_fail(e)
        db.replace_panels(scene["id"], panels, {"provider": provider})
        made += len(panels)
    return {"scenes": len(scenes), "panels": made, "provider": provider}


@router.post("/episodes/{episode_id}/boardroom")
def boardroom_mode(episode_id: int, body: dict | None = None) -> dict:
    ep = _episode_or_404(episode_id)
    outline = _outline_text(ep, (body or {}).get("outline", ""))
    rounds = int((body or {}).get("rounds", 2))
    try:
        notes = gen.boardroom_notes(outline, rounds=rounds)
    except gen.GenerationError as e:
        raise _gen_fail(e)
    except Exception as e:  # conductor runtime failure — fail loud, stay specific
        raise HTTPException(502, f"boardroom conductor failed: {e}")
    db.update_episode(episode_id, director_notes=json.dumps(notes, ensure_ascii=False))
    return notes


# ── panel edits / regeneration / images ──────────────────────────────────

@router.patch("/panels/{panel_id}")
def patch_panel(panel_id: int, body: PanelPatch) -> dict:
    _panel_or_404(panel_id)
    fields = {k: v for k, v in body.model_dump().items() if v is not None}
    row = db.update_panel(panel_id, **fields)
    return dict(row) if row else {}


@router.post("/panels/{panel_id}/regenerate")
def regenerate_panel(panel_id: int) -> dict:
    p = _panel_or_404(panel_id)
    scene_row = db.get_scene(p["scene_id"])
    if scene_row is None:
        raise HTTPException(404, "parent scene missing")
    ep = db.get_episode(scene_row["episode_id"])
    neighbors = [x for x in db.list_panels(p["scene_id"]) if x["id"] != panel_id]
    try:
        fresh, provider = gen.regenerate_panel(
            dict(p), neighbors[:4], dict(scene_row), ep["title"]
        )
    except gen.GenerationError as e:
        raise _gen_fail(e)
    try:
        dur = max(0.5, float(fresh.get("duration_sec", 3.0)))
    except (TypeError, ValueError):
        dur = 3.0
    fields = {
        "shot_type": str(fresh.get("shot_type", p["shot_type"])).strip(),
        "camera_move": str(fresh.get("camera_move", p["camera_move"])).strip(),
        "action": str(fresh.get("action", p["action"])).strip(),
        "vo_speaker": str(fresh.get("vo_speaker", "")).strip(),
        "vo_line": str(fresh.get("vo_line", "")).strip(),
        "on_screen_text": str(fresh.get("on_screen_text", "")).strip(),
        "duration_sec": dur,
        "visual_prompt": str(fresh.get("visual_prompt", "")).strip(),
        "ai_meta": {"provider": provider, "regenerated_from": panel_id},
    }
    row = db.update_panel(panel_id, **fields)
    return dict(row) if row else {}


@router.post("/panels/{panel_id}/image")
def panel_image(panel_id: int) -> dict:
    p = _panel_or_404(panel_id)
    scene = db.get_scene(p["scene_id"])
    if scene is None:
        raise HTTPException(404, "parent scene missing")
    ep = _episode_or_404(scene["episode_id"])
    p = dict(p)
    p["scene_ord"] = scene["ord"]
    return gen.generate_image_for_panel(p, ep)


# ── exports ──────────────────────────────────────────────────────────────

def _flatten(tree: dict) -> list[dict]:
    rows = []
    for scene in tree["scenes"]:
        for panel in scene["panels"]:
            rows.append({
                "scene_ord": scene["ord"], "scene_slug": scene["slug"],
                "location": scene["location"], "time_of_day": scene["time_of_day"],
                "panel_ord": panel["ord"], **{
                    k: panel[k] for k in (
                        "shot_type", "camera_move", "action", "vo_speaker",
                        "vo_line", "on_screen_text", "duration_sec",
                        "visual_prompt", "image_status",
                    )
                },
            })
    return rows


@router.get("/episodes/{episode_id}/export/json")
def export_json(episode_id: int) -> Response:
    tree = db.episode_tree(episode_id)
    if tree is None:
        raise HTTPException(404, "episode not found")
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = EXPORTS_DIR / f"{tree['slug']}.json"
    path.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
    return Response(
        path.read_text(encoding="utf-8"),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename={path.name}"},
    )


@router.get("/episodes/{episode_id}/export/csv")
def export_csv(episode_id: int) -> Response:
    tree = db.episode_tree(episode_id)
    if tree is None:
        raise HTTPException(404, "episode not found")
    rows = _flatten(tree)
    buf = io.StringIO()
    cols = ["scene_ord", "scene_slug", "location", "time_of_day", "panel_ord",
            "shot_type", "camera_move", "action", "vo_speaker", "vo_line",
            "on_screen_text", "duration_sec", "image_status"]
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    w.writerows(rows)
    name = f"{tree['slug']}_shotlist.csv"
    return Response(
        buf.getvalue(), media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={name}"},
    )


@router.get("/episodes/{episode_id}/export/sheet")
def export_sheet(episode_id: int) -> HTMLResponse:
    tree = db.episode_tree(episode_id)
    if tree is None:
        raise HTTPException(404, "episode not found")
    EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
    html = _render_sheet(tree)
    path = EXPORTS_DIR / f"{tree['slug']}_contact_sheet.html"
    path.write_text(html, encoding="utf-8")
    return HTMLResponse(html)


# Security: Use standard library html.escape with quote=True to escape quotes
# and prevent HTML/attribute-injection XSS in contact sheet exports.
def _esc(s: Any) -> str:
    return html.escape(str(s), quote=True)


def _render_sheet(tree: dict) -> str:
    parts = [
        "<!doctype html><html><head><meta charset='utf-8'>",
        f"<title>{_esc(tree['title'])} — contact sheet</title>",
        "<style>",
        "body{background:#0e0c09;color:#e8dcc3;font-family:'Courier Prime',monospace;margin:2em}",
        "h1{font-family:'Bebas Neue',sans-serif;letter-spacing:.08em;color:#d4af37;margin:0}",
        ".log{color:#b0a58c;font-style:italic;margin:.4em 0 1.5em}",
        ".scene{border-top:1px solid #3a3226;margin-top:2em;padding-top:1em}",
        ".slug{font-family:'Bebas Neue',sans-serif;font-size:1.2em;color:#c0392b;letter-spacing:.06em}",
        ".grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:1em;margin-top:1em}",
        ".panel{border:1px solid #3a3226;padding:.6em;background:#14110c}",
        ".shot{color:#d4af37;font-weight:bold}.dur{color:#8a7f68;float:right}",
        ".act{margin:.5em 0;font-size:.85em;line-height:1.4}",
        ".vo{color:#c0b493;font-style:italic;font-size:.8em}",
        ".ost{color:#c0392b;font-size:.75em}",
        "img{width:100%;aspect-ratio:16/9;object-fit:cover;border:1px solid #3a3226}",
        ".ph{display:flex;align-items:center;justify-content:center;aspect-ratio:16/9;"
        "border:1px dashed #3a3226;color:#5a5142;font-size:.75em}",
        "@media print{body{background:#fff;color:#111}}",
        "</style></head><body>",
        f"<h1>SKIN DEEP — {_esc(tree['title'])}</h1>",
        f"<div class='log'>S{tree['season']}E{tree['number']} · {_esc(tree['logline'])}</div>",
    ]
    for scene in tree["scenes"]:
        parts.append(
            f"<div class='scene'><div class='slug'>{_esc(scene['slug'])}</div>"
            f"<div>{_esc(scene['synopsis'])}</div><div class='grid'>"
        )
        for p in scene["panels"]:
            img = ""
            if p["image_status"] == "ready" and p["image_path"]:
                img = f"<img src='../{_esc(p['image_path'])}' alt='panel'>"
            else:
                img = "<div class='ph'>no image — visual prompt on file</div>"
            vo = ""
            if p["vo_line"]:
                who = p["vo_speaker"] or "VO"
                vo = f"<div class='vo'>{_esc(who)}: {_esc(p['vo_line'])}</div>"
            ost = (f"<div class='ost'>[ {_esc(p['on_screen_text'])} ]</div>"
                   if p["on_screen_text"] else "")
            parts.append(
                f"<div class='panel'><span class='shot'>{_esc(p['shot_type'])}"
                f" · {_esc(p['camera_move'])}</span><span class='dur'>"
                f"{p['duration_sec']:.1f}s</span>{img}"
                f"<div class='act'>{_esc(p['action'])}</div>{vo}{ost}</div>"
            )
        parts.append("</div></div>")
    parts.append("</body></html>")
    return "".join(parts)


# ── health ───────────────────────────────────────────────────────────────

@router.get("/health")
def health() -> dict:
    try:
        from router import check_providers
        text_providers = check_providers()
    except ImportError:
        text_providers = []

    out: dict[str, Any] = {"text_providers": text_providers}
    out["image_chain"] = [
        {"provider": "openrouter", "key": bool(gen._openrouter_key())},
        {"provider": "novita", "key": bool(gen.os.environ.get("NOVITA_API_KEY"))},
        {"provider": "gemini", "enabled": gen.os.environ.get("STORYBOARD_ALLOW_GEMINI") == "1"},
    ]
    return out
