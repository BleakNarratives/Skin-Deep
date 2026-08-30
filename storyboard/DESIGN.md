# SKIN DEEP STORYBOARD ENGINE — DESIGN

DNA_TAG: ORIGIN=BleakNarratives/Skin-Deep | PILLAR=storyboard | CREATED=2026-08-28

AI-driven storyboarding for Skin Deep Season 1, Episode 1: "The Handshake"
(and any later episode — schema is season/episode generic).

---

## 1. WHAT IT IS

A module inside `~/Skin-Deep` (mounted into the existing LOUGH Arena FastAPI
service — ONE uvicorn process, RAM discipline). Pipeline:

    episode outline (markdown, human-editable)
        → AI scene beat sheet (LLM, strict JSON)
        → AI shot panels per scene (LLM, strict JSON)
        → AI visual prompts per panel
        → AI panel images (pluggable image provider)
        → editable in browser → exports (contact sheet HTML / CSV / JSON)

Inference backbone: `Official-Vertical-AI-Boardroom/router.py`
(`call_model(prompt, system, tier)`) — Groq key pool, 429 backoff,
OpenRouter/Gemini/Ollama failover. Zero new text-gen infrastructure.

BOARDROOM MODE (opt-in): runs the full vertical_ai conductor
(`boardroom.run_boardroom`) on the episode outline and stores the champion
thesis as director's notes on the episode — the board argues structure before
a single panel is cut.

## 2. TARGET EPISODE

Ep1 "The Handshake" (canonical outline: `episodes/ep1_the_handshake.md`,
seeded from `bluesky/deepseek_Lough_s_skin_deep.txt` — the 5-episode season
arc is the spine; the TikTok short-form format is derivable later from the
same panels, not boarded separately).

Show bible (generation system prompt): MIKE (operator, duffel-bag rig),
LANCY (master, Iron & Ink, antiseptic + Marlboros), JET (apprentice, ep3+),
SARAH (VO), THE REP (arts council). Docuseries verite. Cold opens,
cliffhanger endings, real gear with real prices, roast interstitials.

## 3. DATA MODEL (SQLite: storyboard.db)

    episodes:  id, season, number, slug, title, logline, outline_path,
               director_notes, status, created_at, updated_at
    scenes:    id, episode_id, ord, slug ("INT. IRON & INK - DAY"), synopsis,
               location, time_of_day, characters(json), ai_meta(json)
    panels:    id, scene_id, ord, shot_type, camera_move, action,
               vo_speaker, vo_line, on_screen_text, duration_sec,
               visual_prompt, image_path, image_status, ai_meta(json)

Panel JSON export = the canonical artifact (git-diffable, per episode:
`exports/ep1_the_handshake.json`).

## 4. GENERATION CONTRACTS (strict JSON, validated, fail-loud)

Stage 1  outline  → scenes[]   {slug, synopsis, location, time_of_day,
                                characters[]}
Stage 2  scene    → panels[]   {shot_type, camera_move, action, vo_speaker,
                                vo_line, on_screen_text, duration_sec,
                                visual_prompt}
Stage 3  panel    → image      (pluggable provider)

JSON repaired defensively (strip ```fences, first-brace slice) exactly like
the Boardroom's own parsers. Validation errors raise HTTP 502 with the raw
text attached — never silently re-generated into mush.

## 5. IMAGE PROVIDERS (pluggable, priority order)

| Priority | Provider | Status | Notes |
|----------|----------|--------|-------|
| 1 | openrouter | KEY IN HAND | `POST /api/v1/images`, model via
  `STORYBOARD_IMAGE_MODEL` env or auto-pick cheapest discovered endpoint
  (`GET /api/v1/images/models` + endpoints pricing). Free-tier models exist;
  catalog churns, so discovery > hardcoded slug. |
| 2 | novita | optional key | Purpose-built SDXL/flux, pennies per image.
  Recommended upgrade if OpenRouter free models vanish. |
| 3 | gemini | REQUIRES BILLING | image gen left the free tier (Aug 2026).
  Stub present, off by default. |
| 4 | placeholder | always | No provider call — panel renders text-only,
  visual_prompt saved, image_status="placeholder". NOTHING blocks. |

Images land in `storyboard/images/ep{N}/s{scene}p{panel}.png`. Regenerating
a panel regenerates its image only on explicit request.

## 6. API (mounted at /api/v1/storyboard in backend/app.py)

    GET    /episodes                     list
    POST   /episodes                     create (from outline markdown)
    GET    /episodes/{id}                full tree (scenes+panels)
    POST   /episodes/{id}/scenes         AI: outline → scene beat sheet
    POST   /episodes/{id}/panels         AI: all scenes → panels
    POST   /episodes/{id}/boardroom      AI: full conductor → director notes
    PATCH  /panels/{id}                  human edit (any field)
    POST   /panels/{id}/regenerate       AI: re-cut this one panel
    POST   /panels/{id}/image            AI: render image for this panel
    GET    /episodes/{id}/export/json    canonical JSON
    GET    /episodes/{id}/export/csv     shot list CSV
    GET    /episodes/{id}/export/sheet   contact sheet HTML (print→PDF)
    GET    /health                       provider status (router.check_providers)

## 7. UI (storyboard/static/index.html)

Vanilla JS, no build step, no node_modules. Design system: dark #0e0c09,
cream/gold/crimson/tan/silver, Playfair Display + Bebas Neue + Courier Prime,
NO emojis. Episode header, scene rail, panel grid (shot type badge, action,
VO, duration, image thumb), inline edit, per-panel/scene/episode generate
buttons, export links, provider health strip.

## 8. NON-GOALS (v1)

- No timeline/drag editor (panels have ordinals; reorder = edit ord)
- No video/image rendering of animatics
- No multi-user auth (localhost service)
- No reuse of backend/.venv python changes beyond the mount — module imports
  nothing from arena code, so it can split out later without surgery.

## 9. TESTS

`tests/test_storyboard.py` — mocked `call_model` (fake JSON responses), fake
image provider: schema validation, db round-trip, CSV/JSON export integrity.
No network in tests. Live generation is operator-triggered via the UI/curl.

<!-- DNA_TAG: ORIGIN=BleakNarratives/Skin-Deep | PILLAR=storyboard | LAST_SYNC=2026-08-28 -->
