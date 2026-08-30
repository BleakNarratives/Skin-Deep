"""
storyboard_gen.py — AI generation engine for the Skin Deep storyboard.

Text backbone: the Boardroom router (call_model) — Groq key pool with
429 backoff, OpenRouter/Gemini/Ollama failover. Same inference path as
vertical_ai.py, zero new text-gen infra.

Images: pluggable provider chain (openrouter → novita → gemini-stub →
placeholder). See DESIGN.md §5. Nothing blocks on image providers.

All LLM stages demand strict JSON and parse defensively; validation
failures raise GenerationError with the raw text attached (fail loud).
"""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Callable

# ── Boardroom router (imported read-only, like app.py does for MikeySwarm) ──
BOARDROOM_ROOT = Path.home() / "Official-Vertical-AI-Boardroom"
if str(BOARDROOM_ROOT) not in sys.path:
    sys.path.insert(0, str(BOARDROOM_ROOT))

import requests  # noqa: E402  (router depends on it; kept adjacent)

SB_DIR = Path(__file__).parent
IMAGES_DIR = SB_DIR / "images"
EXPORTS_DIR = SB_DIR / "exports"
EPISODES_DIR = SB_DIR / "episodes"

MAX_SCENES = 12
MAX_PANELS_PER_SCENE = 8

_STYLE_SUFFIX = os.environ.get(
    "STORYBOARD_IMAGE_STYLE",
    "cinematic documentary still, available light, warm tungsten practicals,"
    " neon spill, gritty realism, subtle film grain, 16:9 widescreen",
)

OPENROUTER_URL = "https://openrouter.ai/api/v1"
OPENROUTER_IMAGE_FALLBACKS = [
    os.environ.get("STORYBOARD_IMAGE_MODEL", ""),
    "google/gemini-2.5-flash-image",   # paid, pennies — attempt then fall through
]
NOVITA_URL = "https://api.novita.ai/v3/text2img"


class GenerationError(RuntimeError):
    """LLM stage failed validation. Carries raw output for debugging."""

    def __init__(self, stage: str, raw: str, cause: str):
        super().__init__(f"[{stage}] {cause}")
        self.stage = stage
        self.raw = raw
        self.cause = cause


# ── defensive JSON extraction (same spirit as the Boardroom's parsers) ────

def extract_json(raw: str) -> Any:
    text = raw.strip()
    if "```" in text:
        for chunk in text.split("```"):
            chunk = chunk.strip()
            if chunk.startswith(("json", "{", "[")):
                chunk = chunk.removeprefix("json").strip()
                if chunk.startswith(("{", "[")):
                    text = chunk
                    break
    for start_ch, end_ch in (("[", "]"), ("{", "}")):
        i = text.find(start_ch)
        if i == -1:
            continue
        j = text.rfind(end_ch)
        if j > i:
            text = text[i:j + 1]
            break
    return json.loads(text)


def _call_llm(stage: str, system: str, prompt: str) -> Any:
    """call_model → defensive parse → structural assert. Fail loud."""
    from router import call_model, ModelTier  # lazy: keeps import graph light

    raw, provider = call_model(prompt, system=system, tier=ModelTier.FAST)
    try:
        data = extract_json(raw)
    except (ValueError, TypeError) as e:
        raise GenerationError(stage, raw, f"unparseable JSON: {e}") from e
    if not isinstance(data, list) or not data:
        raise GenerationError(stage, raw, "expected a non-empty JSON array")
    return data, provider


# ── show bible / prompts ─────────────────────────────────────────────────

BIBLE = """SHOW: SKIN DEEP (Season 1) — docuseries verite about preserving a
master tattoo artist's technique through salvaged sensors and stubborn code.

CHARACTERS:
- MIKE (Operator): the engineer. Builds rigs from dumpster parts and duct
  tape. Speaks in specs and short sentences. Desperate but never pitiful.
- LANCY: master artist, Iron & Ink tattoo. Decades in the craft. Grunts
  before he agrees. Tests people without telling them they are being tested.
- SARAH (VO): narrator. Dry, warm, mythic. Reads data like scripture.
- THE REP: local arts council. $10K preservation grant. Polite, skeptical.
- JET: Lancy's apprentice (ep3+; background presence in ep1 only).

REGISTER: available-light documentary. Real gear, real prices, real stakes.
Cold opens, escalating demos, human moments, cliffhanger endings. On-screen
text may carry AI-roast interstitials. No score until the human moment."""

SCENE_SYSTEM = BIBLE + """

TASK: Expand the episode outline into a scene beat sheet.
Return STRICT JSON ONLY (no markdown fences, no commentary): a single array
of at most 12 scene objects, each:
{"slug": "INT. IRON & INK - DAY", "synopsis": "2-4 sentences of what happens
and why it matters", "location": "Iron & Ink tattoo shop, front room",
"time_of_day": "DAY" | "NIGHT" | "DUSK", "characters": ["LANCY", "MIKE"]}

Rules: preserve the outline's beats and order. Keep the voice. Never invent
new named characters. Slug lines are screenplay-style and ALL CAPS."""

PANEL_SYSTEM = BIBLE + """

TASK: Cut the given scene into shot panels for a documentary storyboard.
Return STRICT JSON ONLY (no markdown fences, no commentary): a single array
of 4 to 8 panel objects, each:
{"shot_type": "WS"|"MS"|"MCU"|"CU"|"ECU"|"OTS"|"POV"|"INSERT"|"AERIAL"|"TWO_SHOT",
 "camera_move": "static"|"handheld"|"push in"|"pull out"|"pan"|"tilt"|"whip",
 "action": "what we SEE, 1-3 concrete sentences, present tense",
 "vo_speaker": "" or "SARAH" or a character name for on-camera dialogue",
 "vo_line": "the exact spoken line or VO sentence; empty if none",
 "on_screen_text": "lower-third / UI overlay / AI-roast interstitial; empty if none",
 "duration_sec": 1.5 to 8.0,
 "visual_prompt": "one dense sentence for an image generator: framing,
 subjects, lighting, texture. Documentary realism. No text in frame."}

Rules: alternate coverage like a real doc crew (establish, then insert, then
reaction). Every dialogue line must belong to a character in the bible.
duration_sec must be a number. Do not merge the scene's whole action into
one panel; cut it."""

REGEN_SYSTEM = BIBLE + """

TASK: Re-cut ONE storyboard panel. Same JSON schema as the panel stage
(single object, not an array). Keep continuity with the neighboring panels
given as context, but make this panel earn its slot."""


# ── stage 1: outline → scenes ────────────────────────────────────────────

def generate_scenes(outline_text: str) -> tuple[list[dict], str]:
    data, provider = _call_llm(
        "scenes", SCENE_SYSTEM, f"EPISODE OUTLINE:\n\n{outline_text}",
    )
    scenes = []
    for s in data[:MAX_SCENES]:
        if not isinstance(s, dict) or not s.get("slug"):
            raise GenerationError("scenes", json.dumps(data)[:2000],
                                  "scene object missing slug")
        scenes.append(s)
    return scenes, provider


# ── stage 2: scene → panels ──────────────────────────────────────────────

def generate_panels(scene: dict, episode_title: str) -> tuple[list[dict], str]:
    prompt = (
        f"EPISODE: {episode_title}\n\nSCENE:\n"
        f"{json.dumps(scene, ensure_ascii=False, indent=2)}\n\n"
        "Cut this scene into panels now."
    )
    data, provider = _call_llm("panels", PANEL_SYSTEM, prompt)
    panels = []
    for p in data[:MAX_PANELS_PER_SCENE]:
        if not isinstance(p, dict) or not p.get("action"):
            raise GenerationError("panels", json.dumps(data)[:2000],
                                  "panel object missing action")
        panels.append(p)
    return panels, provider


# ── stage 2b: single panel regeneration ──────────────────────────────────

def regenerate_panel(panel: dict, neighbors: list[dict], scene: dict,
                     episode_title: str) -> tuple[dict, str]:
    prompt = (
        f"EPISODE: {episode_title}\n\nSCENE:\n{json.dumps(scene, ensure_ascii=False)}\n\n"
        f"NEIGHBOR PANELS (context, do not rewrite):\n"
        f"{json.dumps(neighbors, ensure_ascii=False)}\n\n"
        f"PANEL TO RE-CUT:\n{json.dumps(panel, ensure_ascii=False)}\n\n"
        "Return the replacement panel as a single JSON object."
    )
    from router import call_model

    raw, provider = call_model(prompt, system=REGEN_SYSTEM, tier="fast")
    try:
        obj = extract_json(raw)
    except (ValueError, TypeError) as e:
        raise GenerationError("regen", raw, f"unparseable JSON: {e}") from e
    if isinstance(obj, list):
        if not obj:
            raise GenerationError("regen", raw, "empty array")
        obj = obj[0]
    if not isinstance(obj, dict) or not obj.get("action"):
        raise GenerationError("regen", raw, "panel object missing action")
    return obj, provider


# ── stage 3: image providers ─────────────────────────────────────────────

def _openrouter_key() -> str:
    return os.environ.get("OPENROUTER_API_KEY", "")


def _or_pick_model() -> str | None:
    """Prefer env slug, then any :free image model, then the paid Gemini
    flash image as last real attempt. Discovery beats hardcoded slugs."""
    try:
        r = requests.get(f"{OPENROUTER_URL}/images/models", timeout=30)
        r.raise_for_status()
        ids = [m.get("id", "") for m in r.json().get("data", [])]
    except Exception:
        ids = []
    for slug in OPENROUTER_IMAGE_FALLBACKS:
        if slug and (not ids or slug in ids):
            return slug
    for slug in ids:
        if ":free" in slug:
            return slug
    return ids[0] if ids else None


def openrouter_image(prompt: str) -> tuple[bytes | None, dict]:
    key = _openrouter_key()
    if not key:
        return None, {"provider": "openrouter", "error": "no OPENROUTER_API_KEY"}
    model = _or_pick_model()
    if not model:
        return None, {"provider": "openrouter", "error": "no image models discovered"}
    try:
        r = requests.post(
            f"{OPENROUTER_URL}/images",
            headers={"Authorization": f"Bearer {key}"},
            json={"model": model, "prompt": prompt, "aspect_ratio": "16:9"},
            timeout=180,
        )
        r.raise_for_status()
        item = r.json().get("data", [{}])[0]
        b64 = item.get("b64_json", "")
        if not b64:
            return None, {"provider": "openrouter", "error": "empty image payload"}
        return base64.b64decode(b64), {
            "provider": "openrouter", "model": model,
            "media_type": item.get("media_type", "image/png"),
            "cost_usd": r.json().get("usage", {}).get("cost"),
        }
    except Exception as e:
        return None, {"provider": "openrouter", "model": model, "error": str(e)[:300]}


def novita_image(prompt: str) -> tuple[bytes | None, dict]:
    key = os.environ.get("NOVITA_API_KEY", "")
    if not key:
        return None, {"provider": "novita", "error": "no NOVITA_API_KEY"}
    try:
        r = requests.post(
            NOVITA_URL,
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model_name": "stable-diffusion-xl-v1-0",
                "prompt": f"{prompt}, {_STYLE_SUFFIX}",
                "negative_prompt": "text, watermark, low quality, blurry, deformed hands",
                "width": 1024, "height": 576, "samples": 1, "guidance_scale": 7.5,
            },
            timeout=180,
        )
        r.raise_for_status()
        images = r.json().get("images") or []
        if not images:
            return None, {"provider": "novita", "error": "no images in response"}
        url = images[0].get("image_url", "")
        img = requests.get(url, timeout=60)
        img.raise_for_status()
        return img.content, {"provider": "novita", "model": "sdxl-v1"}
    except Exception as e:
        return None, {"provider": "novita", "error": str(e)[:300]}


def gemini_image(prompt: str) -> tuple[bytes | None, dict]:
    # Image gen left Gemini's free tier (Aug 2026). Kept as an explicit
    # billing-required stub so the chain documents itself.
    return None, {
        "provider": "gemini",
        "error": "requires paid tier (billing) — enable via STORYBOARD_ALLOW_GEMINI=1",
    }


PROVIDER_CHAIN: list[Callable[[str], tuple[bytes | None, dict]]] = [
    openrouter_image, novita_image, gemini_image,
]


def generate_image_for_panel(panel: dict, episode: dict) -> dict:
    """Try the provider chain; write the PNG; update the panel row.
    Returns the ai_meta dict that was stored (provider attempts trail)."""
    import storyboard_db as db

    prompt = panel.get("visual_prompt") or panel.get("action") or "storyboard panel"
    styled = f"{prompt}. {_STYLE_SUFFIX}"
    attempts: list[dict] = []
    image_bytes: bytes | None = None

    allow_gemini = os.environ.get("STORYBOARD_ALLOW_GEMINI") == "1"
    for fn in PROVIDER_CHAIN:
        if fn is gemini_image and not allow_gemini:
            continue
        data, meta = fn(styled)
        attempts.append(meta)
        if data:
            image_bytes = data
            break

    ep_slug = episode["slug"]
    out_dir = IMAGES_DIR / ep_slug
    out_dir.mkdir(parents=True, exist_ok=True)

    if image_bytes:
        fname = f"s{panel.get('scene_ord', 0):02d}p{panel.get('ord', 0):02d}_{panel['id']}.png"
        path = out_dir / fname
        path.write_bytes(image_bytes)
        # stored relative to IMAGES_DIR: the UI mounts /storyboard/images ->
        # IMAGES_DIR, and the path stays valid wherever the dir lives
        rel = f"{ep_slug}/{fname}"
        db.update_panel(panel["id"], image_path=rel, image_status="ready",
                        ai_meta={"attempts": attempts})
        return {"status": "ready", "image_path": rel, "attempts": attempts}

    db.update_panel(panel["id"], image_status="placeholder",
                    ai_meta={"attempts": attempts})
    return {"status": "placeholder", "attempts": attempts}


# ── boardroom mode: the full conductor weighs in on structure ────────────

def boardroom_notes(outline_text: str, rounds: int = 2) -> dict:
    """Run the vertical_ai conductor (boardroom → fractal sim → genetic
    arena → champion) on the episode outline. Returns the champion payload
    to store as director_notes metadata. Fails loud — no fake champion."""
    from boardroom import run_boardroom

    context = {
        "timestamp": __import__("datetime").datetime.now().isoformat(),
        "type": "document",
        "label": "SKIN DEEP S1E1 outline",
        "raw": outline_text,
        "data": {"content": outline_text},
    }
    result = run_boardroom(context, rounds=rounds)
    champion = result.get("champion") if isinstance(result, dict) else result
    if not champion:
        raise GenerationError("boardroom", json.dumps(result)[:2000],
                              "conductor returned no champion")
    return {"champion": champion, "rounds": rounds}
