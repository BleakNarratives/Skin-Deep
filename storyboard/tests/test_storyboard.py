"""
test_storyboard.py — offline suite for the storyboard engine.

No network, no Boardroom import at test time (router imports are lazy and
generation is monkeypatched). DB and image dirs are redirected to tmp_path
BEFORE the api module is imported, since it runs db.init_db() at import.

NOTE: endpoints are tested as plain functions, NOT via TestClient — the
installed fastapi/starlette pair has a broken middleware astack under
TestClient (fastapi_middleware_astack assertion). Direct calls hit the same
handlers and skip the broken middleware layer entirely.
"""

from __future__ import annotations

import base64
import json
import sys
from pathlib import Path

import pytest

SB_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(SB_DIR))

import storyboard_db as db  # noqa: E402
import storyboard_gen as gen  # noqa: E402

from fastapi import HTTPException  # noqa: E402
from pydantic import ValidationError  # noqa: E402


@pytest.fixture(scope="module")
def tmp_db(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("sb")
    db.DB_PATH = tmp / "test_storyboard.db"
    db.init_db()
    return db


@pytest.fixture(scope="module")
def api(tmp_db, tmp_path_factory):
    tmp = tmp_path_factory.mktemp("media")
    gen.IMAGES_DIR = tmp / "images"
    gen.EXPORTS_DIR = tmp / "exports"
    # kill any real provider chain: tests must never touch the network
    gen.PROVIDER_CHAIN = []

    import storyboard_api

    return storyboard_api


# ── extract_json ─────────────────────────────────────────────────────────

def test_extract_plain():
    assert gen.extract_json('[{"a":1}]') == [{"a": 1}]


def test_extract_fenced():
    assert gen.extract_json('```json\n{"a": 2}\n```') == {"a": 2}


def test_extract_with_commentary():
    raw = ("Here is the beat sheet you asked for:\n"
           '[{"slug": "INT. X - DAY"}]\nHope this helps!')
    assert gen.extract_json(raw)[0]["slug"] == "INT. X - DAY"


def test_extract_garbage_raises():
    with pytest.raises(json.JSONDecodeError):
        gen.extract_json("no json here at all")


def test_esc_quotes_and_html(api):
    raw = '<script>alert("xss")</script> & \'quote\''
    escaped = api._esc(raw)
    assert "&lt;script&gt;" in escaped
    assert "&quot;xss&quot;" in escaped
    assert "&#x27;quote&#x27;" in escaped or "&#39;quote&#39;" in escaped


# ── db round-trip ────────────────────────────────────────────────────────

def test_update_episode_sanitizes_columns(tmp_db):
    ep = tmp_db.create_episode(1, 98, "test_update_episode", "Update Episode Title", "log", "")
    # Updating valid field
    tmp_db.update_episode(ep["id"], title="Updated Title", logline="Updated Logline")
    updated = tmp_db.get_episode(ep["id"])
    assert updated["title"] == "Updated Title"
    assert updated["logline"] == "Updated Logline"

    # Attempting SQL injection / unallowed column injection via kwargs
    malicious_kwargs = {"title": "New Title", "malicious_col; DROP TABLE episodes;--": "value"}
    tmp_db.update_episode(ep["id"], **malicious_kwargs)
    after_attack = tmp_db.get_episode(ep["id"])
    assert after_attack is not None
    assert after_attack["title"] == "New Title"


def test_db_roundtrip(tmp_db):
    ep = tmp_db.create_episode(1, 99, "test_ep_roundtrip", "Roundtrip", "log", "")
    scenes = [{"slug": "INT. SHOP - DAY", "synopsis": "s", "location": "shop",
               "time_of_day": "DAY", "characters": ["LANCY"]}]
    tmp_db.replace_scenes(ep["id"], scenes, {"provider": "test"})
    got = tmp_db.list_scenes(ep["id"])
    assert len(got) == 1 and got[0]["characters"] == ["LANCY"]

    tmp_db.replace_panels(got[0]["id"], [{
        "shot_type": "CU", "action": "needle meets skin",
        "duration_sec": 4, "visual_prompt": "macro of needle",
    }], {"provider": "test"})
    tree = tmp_db.episode_tree(ep["id"])
    panel = tree["scenes"][0]["panels"][0]
    assert panel["shot_type"] == "CU"

    row = tmp_db.update_panel(panel["id"], action="needle lifts", duration_sec=5.5)
    assert row is not None, "update_panel lost the row"
    assert row["action"] == "needle lifts"
    assert row["duration_sec"] == pytest.approx(5.5)


# ── API: episodes + exports (no AI) ─────────────────────────────────────

def test_episode_create_and_tree(api):
    ep = api.create_episode(api.EpisodeCreate(
        season=1, number=1, slug="test_api_ep", title="API Ep",
        logline="test", outline="# OUTLINE\n\nsome beats here"))
    assert ep["id"] > 0

    tree = api.get_episode(ep["id"])
    assert tree["title"] == "API Ep"
    assert "some beats here" in (SB_DIR / tree["outline_path"]).read_text()

    with pytest.raises(HTTPException) as ei:
        api.create_episode(api.EpisodeCreate(
            season=1, number=2, slug="test_api_ep", title="dup"))
    assert ei.value.status_code == 409

    with pytest.raises(HTTPException) as ei:
        api.get_episode(424242)
    assert ei.value.status_code == 404


def test_episode_create_slug_path_traversal_prevention(api):

    for invalid_slug in ["../evil", "../../etc/passwd", "sub/dir", "slug with space", "slug!"]:
        with pytest.raises(ValidationError):
            api.EpisodeCreate(
                season=1,
                number=1,
                slug=invalid_slug,
                title="Invalid Slug Ep",
                outline="some outline",
            )


def test_create_episode_oserror_sanitizes_500(api, monkeypatch):
    def fake_write_text(*args, **kwargs):
        raise OSError("[Errno 13] Permission denied: '/var/secret/path/episodes/test.md'")

    monkeypatch.setattr(Path, "write_text", fake_write_text)

    with pytest.raises(HTTPException) as ei:
        api.create_episode(api.EpisodeCreate(
            season=1, number=99, slug="test_oserror_sanitized",
            title="OSError Test", outline="some outline content",
        ))
    assert ei.value.status_code == 500
    assert ei.value.detail == "failed to write outline file"


def test_esc_quotes_escaping(api):
    assert api._esc('test "double" & \'single\' <tag>') == 'test &quot;double&quot; &amp; &#x27;single&#x27; &lt;tag&gt;'


def test_csv_formula_injection_sanitization(api, tmp_db):
    assert api._sanitize_csv_cell("=1+1") == "'=1+1"
    assert api._sanitize_csv_cell("+cmd") == "'+cmd"
    assert api._sanitize_csv_cell("-cmd") == "'-cmd"
    assert api._sanitize_csv_cell("@cmd") == "'@cmd"
    assert api._sanitize_csv_cell("normal text") == "normal text"

    ep = tmp_db.create_episode(1, 101, "test_csv_inj", "CSV Inj", "log", "")
    scenes = [{"slug": "INT. SHOP - DAY", "synopsis": "s", "location": "=DANGEROUS()",
               "time_of_day": "DAY", "characters": ["LANCY"]}]
    tmp_db.replace_scenes(ep["id"], scenes, {"provider": "test"})
    scenes_db = tmp_db.list_scenes(ep["id"])
    tmp_db.replace_panels(scenes_db[0]["id"], [{
        "shot_type": "CU", "action": "+cmd|' /C calc'!A0",
        "duration_sec": 4, "visual_prompt": "prompt",
    }], {"provider": "test"})

    res = api.export_csv(ep["id"])
    csv_text = bytes(res.body).decode("utf-8")
    assert "'=DANGEROUS()" in csv_text
    assert "'+cmd|' /C calc'!A0" in csv_text


def test_outline_text_path_traversal_prevention(api, tmp_db):
    ep = tmp_db.create_episode(1, 100, "test_traversal", "Traversal", "log", outline_path="../backend/app.py")
    with pytest.raises(HTTPException) as ei:
        api._outline_text(ep)
    assert ei.value.status_code == 400
    assert ei.value.detail == "invalid outline path"


def test_export_path_traversal_prevention(api, tmp_db):
    ep = tmp_db.create_episode(1, 102, "../evil_export_slug", "Evil Slug Ep", "log", "")
    with pytest.raises(HTTPException) as ei_json:
        api.export_json(ep["id"])
    assert ei_json.value.status_code == 400
    assert ei_json.value.detail == "invalid episode slug"

    with pytest.raises(HTTPException) as ei_sheet:
        api.export_sheet(ep["id"])
    assert ei_sheet.value.status_code == 400
    assert ei_sheet.value.detail == "invalid episode slug"


def test_export_oserror_sanitizes_500(api, tmp_db, monkeypatch):
    ep = tmp_db.create_episode(1, 103, "test_export_oserror", "Export OSError Ep", "log", "")

    def fake_write_text(*args, **kwargs):
        raise OSError("[Errno 13] Permission denied: '/exports/test_export_oserror.json'")

    monkeypatch.setattr(Path, "write_text", fake_write_text)

    with pytest.raises(HTTPException) as ei_json:
        api.export_json(ep["id"])
    assert ei_json.value.status_code == 500
    assert ei_json.value.detail == "failed to write export file"

    with pytest.raises(HTTPException) as ei_sheet:
        api.export_sheet(ep["id"])
    assert ei_sheet.value.status_code == 500
    assert ei_sheet.value.detail == "failed to write export file"


def test_panels_require_scenes(api):
    ep = api.create_episode(api.EpisodeCreate(
        season=1, number=3, slug="test_no_scenes", title="NoScenes"))
    with pytest.raises(HTTPException) as ei:
        api.generate_panels(ep["id"])
    assert ei.value.status_code == 400


def test_scene_generate_request_validation(api):
    req = api.SceneGenerateRequest(outline="short outline")
    assert req.outline == "short outline"

    with pytest.raises(ValidationError):
        api.SceneGenerateRequest(outline="x" * 50001)


def test_boardroom_request_validation(api):
    req = api.BoardroomRequest(outline="outline", rounds=3)
    assert req.rounds == 3

    with pytest.raises(ValidationError):
        api.BoardroomRequest(rounds=0)


# ── gemini image provider (wired up post-CLI; offline via fake client) ───

class _FakePart:
    def __init__(self, data: bytes, mime: str):
        self.inline_data = type("D", (), {"data": data, "mime_type": mime})()


class _FakeResp:
    def __init__(self, data: bytes):
        content = type("C", (), {"parts": [_FakePart(data, "image/png")]})()
        self.candidates = [type("Cand", (), {"content": content})()]


class _FakeModels:
    last = {}

    def generate_content(self, model, contents, config):
        _FakeModels.last = {"model": model, "prompt": contents, "config": config}
        return _FakeResp(b"\x89PNG-fake")


class _FakeClient:
    models = _FakeModels()


def test_gemini_gated_off_by_default(monkeypatch):
    monkeypatch.delenv("STORYBOARD_ALLOW_GEMINI", raising=False)
    data, meta = gen.gemini_image("a panel prompt")
    assert data is None
    assert meta["provider"] == "gemini"
    assert "STORYBOARD_ALLOW_GEMINI" in meta["error"]


def test_gemini_api_key_path(monkeypatch):
    monkeypatch.setenv("STORYBOARD_ALLOW_GEMINI", "1")
    monkeypatch.setenv("GEMINI_API_KEY", "test-key-not-real")
    monkeypatch.setattr(gen, "_gemini_client",
                        lambda key=None: (_FakeClient(), "api_key"))
    data, meta = gen.gemini_image("ECU gloved hand on tattoo machine")
    assert data == b"\x89PNG-fake"
    assert meta["provider"] == "gemini"
    assert meta["auth"] == "api_key"
    cfg = _FakeModels.last["config"]
    assert cfg["response_modalities"] == ["IMAGE"]
    assert cfg["image_config"]["aspect_ratio"] == "16:9"


def test_gemini_error_is_swallowed_into_meta(monkeypatch):
    monkeypatch.setenv("STORYBOARD_ALLOW_GEMINI", "1")

    def boom(key=None):
        raise RuntimeError("no GEMINI_API_KEY/vault keys and no application-default credentials")

    monkeypatch.setattr(gen, "_gemini_client", boom)
    data, meta = gen.gemini_image("anything")
    assert data is None
    assert "application-default" in meta["error"]


def test_gemini_in_panel_image_chain(tmp_db, monkeypatch, tmp_path):
    """generate_image_for_panel must write the PNG and mark ready when
    gemini is the enabled provider that returns bytes."""
    ep = tmp_db.create_episode(1, 9, "test_gem_chain", "GemChain", "", "")
    ep = tmp_db.get_episode(ep["id"])  # idempotent re-runs against a dirty DB
    tmp_db.replace_scenes(ep["id"], [{"slug": "INT. TEST - DAY",
                                      "synopsis": "s", "location": "l",
                                      "time_of_day": "DAY",
                                      "characters": []}], {})
    tree = tmp_db.episode_tree(ep["id"])
    panel = tree["scenes"][0]["panels"][0] if tree["scenes"][0]["panels"] else None
    if panel is None:
        tmp_db.replace_panels(tree["scenes"][0]["id"],
                              [{"shot_type": "CU", "camera_move": "static",
                                "action": "hand", "vo_speaker": "",
                                "vo_line": "", "on_screen_text": "",
                                "duration_sec": 2.0, "visual_prompt": "vp"}], {})
        tree = tmp_db.episode_tree(ep["id"])
        panel = tree["scenes"][0]["panels"][0]

    monkeypatch.setattr(gen, "PROVIDER_CHAIN", [gen.gemini_image])
    monkeypatch.setenv("STORYBOARD_ALLOW_GEMINI", "1")
    monkeypatch.setattr(gen, "_gemini_client", lambda key=None: (_FakeClient(), "api_key"))
    monkeypatch.setattr(gen, "IMAGES_DIR", tmp_path)
    # hermetic: dummy vault key (never used — _gemini_client is patched) so
    # the pool path runs and meta carries provider="gemini"
    import keyring as kring
    (tmp_path / "gemini+test.key").write_text("dummy-key-for-tests")
    monkeypatch.setattr(gen, "gemini_pool",
                        lambda: kring.KeyPool("gemini", (), vault_dir=tmp_path))

    result = gen.generate_image_for_panel(panel, tmp_db.get_episode(ep["id"]))
    assert result["status"] == "ready"
    out_file = (tmp_path / result["image_path"]).resolve()
    assert out_file.read_bytes() == b"\x89PNG-fake"
    assert result["attempts"][0]["provider"] == "gemini"


# ── API: generation stages (mocked LLM) ──────────────────────────────────

def test_generation_pipeline_mocked(api, monkeypatch):
    ep = api.create_episode(api.EpisodeCreate(
        season=1, number=4, slug="test_gen_ep", title="Gen Ep", outline="beats"))

    fake_scenes = [{
        "slug": "INT. IRON & INK - DAY", "synopsis": "the rig goes up",
        "location": "Iron & Ink", "time_of_day": "DAY",
        "characters": ["LANCY", "MIKE"],
    }]
    monkeypatch.setattr(gen, "generate_scenes",
                        lambda outline: (fake_scenes, "fake-llm"))

    fake_panels = [{
        "shot_type": "ECU", "camera_move": "static", "action": "EMG spikes",
        "vo_speaker": "SARAH", "vo_line": "0.78 millivolts.",
        "on_screen_text": "", "duration_sec": 2.5,
        "visual_prompt": "macro of waveform",
    }]
    monkeypatch.setattr(gen, "generate_panels",
                        lambda scene, title: (fake_panels, "fake-llm"))

    r = api.generate_scenes(ep["id"])
    assert r["scenes"] == 1 and r["provider"] == "fake-llm"

    r = api.generate_panels(ep["id"])
    assert r["panels"] == 1, r

    tree = api.get_episode(ep["id"])
    panel = tree["scenes"][0]["panels"][0]
    assert panel["vo_line"] == "0.78 millivolts."

    patched = api.patch_panel(panel["id"], api.PanelPatch(action="edited action"))
    assert patched["action"] == "edited action"

    # exports
    j = api.export_json(ep["id"])
    assert json.loads(bytes(j.body))["scenes"][0]["panels"]

    c = api.export_csv(ep["id"])
    # the PATCH above flowed through: the export must carry the edited action
    assert "edited action" in bytes(c.body).decode()

    s = api.export_sheet(ep["id"])
    body = bytes(s.body).decode()
    assert "IRON &amp; INK" in body and "SARAH" in body

    api.delete_episode(ep["id"])


def test_export_csv_formula_injection_sanitization(api, monkeypatch):
    ep = api.create_episode(api.EpisodeCreate(
        season=1, number=7, slug="test_csv_injection", title="CSV Injection Ep", outline="beats"))

    fake_scenes = [{
        "slug": "=cmd|' /C calc'!A0", "synopsis": "formula in synopsis",
        "location": "@LOCATION", "time_of_day": "+DAY",
        "characters": ["LANCY"],
    }]
    monkeypatch.setattr(gen, "generate_scenes", lambda outline: (fake_scenes, "fake"))

    fake_panels = [{
        "shot_type": "-ECU", "camera_move": "static", "action": "=SUM(1+1)",
        "vo_speaker": "@SARAH", "vo_line": "+0.78mV",
        "on_screen_text": "@INTERSTITIAL", "duration_sec": 2.5,
        "visual_prompt": "prompt",
    }]
    monkeypatch.setattr(gen, "generate_panels", lambda scene, title: (fake_panels, "fake"))

    api.generate_scenes(ep["id"])
    api.generate_panels(ep["id"])

    res = api.export_csv(ep["id"])
    content = bytes(res.body).decode("utf-8")

    assert "'=cmd|' /C calc'!A0" in content
    assert "'@LOCATION" in content
    assert "'+DAY" in content
    assert "'-ECU" in content
    assert "'=SUM(1+1)" in content
    assert "'@SARAH" in content
    assert "'+0.78mV" in content
    assert "'@INTERSTITIAL" in content

    api.delete_episode(ep["id"])


def test_generation_fail_loud(api, monkeypatch):
    ep = api.create_episode(api.EpisodeCreate(
        season=1, number=5, slug="test_badllm", title="Bad LLM", outline="beats"))

    def bad(outline):
        raise gen.GenerationError("scenes", "i refuse to emit json",
                                  "unparseable JSON: nonsense")
    monkeypatch.setattr(gen, "generate_scenes", bad)
    with pytest.raises(HTTPException) as ei:
        api.generate_scenes(ep["id"])
    assert ei.value.status_code == 502
    assert ei.value.detail["stage"] == "scenes"


# ── image provider chain (fake provider) ─────────────────────────────────

def _seed_one_panel(api, monkeypatch, slug):
    ep = api.create_episode(api.EpisodeCreate(
        season=1, number=6, slug=slug, title="Img Ep", outline="beats"))
    monkeypatch.setattr(gen, "generate_scenes",
                        lambda o: ([{"slug": "INT. X - DAY", "synopsis": "s",
                                     "location": "x", "time_of_day": "DAY",
                                     "characters": []}], "fake"))
    monkeypatch.setattr(gen, "generate_panels",
                        lambda s, t: ([{"shot_type": "MS", "action": "a",
                                        "visual_prompt": "vp",
                                        "duration_sec": 2}], "fake"))
    api.generate_scenes(ep["id"])
    api.generate_panels(ep["id"])
    panel = api.get_episode(ep["id"])["scenes"][0]["panels"][0]
    return panel


def test_image_chain_placeholder(api, monkeypatch):
    panel = _seed_one_panel(api, monkeypatch, "test_img_ep")

    # empty chain -> placeholder, no crash
    r = api.panel_image(panel["id"])
    assert r["status"] == "placeholder", r


def test_image_chain_ready(api, monkeypatch):
    panel = _seed_one_panel(api, monkeypatch, "test_img_ep2")

    def fake_provider(prompt):
        assert "vp" in prompt  # visual prompt flows through
        return b"\x89PNG-fake", {"provider": "fake", "model": "test"}
    monkeypatch.setattr(gen, "PROVIDER_CHAIN", [fake_provider])
    r = api.panel_image(panel["id"])
    assert r["status"] == "ready", r
    f = gen.IMAGES_DIR / r["image_path"]
    assert f.read_bytes() == b"\x89PNG-fake"

    row = db.get_panel(panel["id"])
    assert row["image_status"] == "ready" and row["image_path"] == r["image_path"]


def test_health_offline(api):
    h = api.health()
    assert "image_chain" in h
    assert "text_providers" in h


def test_generate_image_for_panel_path_traversal_prevention(api):
    panel = {"id": 1, "action": "test action", "visual_prompt": "test prompt"}
    malicious_ep = {"slug": "../evil_dir"}
    with pytest.raises(ValueError) as excinfo:
        gen.generate_image_for_panel(panel, malicious_ep)
    assert "invalid episode slug" in str(excinfo.value)


def test_arena_db_insert_persona_custom(tmp_path):
    backend_dir = SB_DIR.parent / "backend"
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    import arena_db

    arena_db.ARENA_DB = tmp_path / "test_arena.db"
    arena_db.init_db()

    seed_data = {"identifier": "test-security-seed", "weights": {"dim1": 0.9}}
    row_id = arena_db.insert_persona_custom(seed_data)
    assert row_id > 0

    with arena_db.get_conn() as conn:
        row = conn.execute("SELECT * FROM persona_custom WHERE id = ?", (row_id,)).fetchone()
        assert row is not None
        assert "test-security-seed" in row["seed"]


def test_boardroom_request_validation(api):
    # Valid bounds: 1 <= rounds <= 10
    req_valid = api.BoardroomRequest(rounds=3)
    assert req_valid.rounds == 3

    # Default value
    req_default = api.BoardroomRequest()
    assert req_default.rounds == 2

    # Out of bounds: rounds < 1 or rounds > 10
    with pytest.raises(ValidationError):
        api.BoardroomRequest(rounds=0)

    with pytest.raises(ValidationError):
        api.BoardroomRequest(rounds=11)


# ── keyring: Concierge-style vault + rotation ────────────────────────────

def test_keyring_vault_files_and_rotation(tmp_path, monkeypatch):
    import keyring as kring

    (tmp_path / "openrouter+b.key").write_text("sk-vault-key-b\n")
    (tmp_path / "openrouter+a.key").write_text("sk-vault-key-a")
    (tmp_path / "gemini+work.key").write_text("gk-vault-1")
    (tmp_path / "unrelated.key").write_text("nope")

    for var in ("OPENROUTER_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"):
        monkeypatch.delenv(var, raising=False)

    or_pool = kring.KeyPool("openrouter", ("OPENROUTER_API_KEY",),
                            vault_dir=tmp_path)
    assert or_pool.all_keys() == ["sk-vault-key-a", "sk-vault-key-b"]
    assert or_pool.get_key() == "sk-vault-key-a"
    assert or_pool.rotate() == "sk-vault-key-b"
    assert or_pool.rotate() == "sk-vault-key-a"  # wraps round-robin

    g_pool = kring.KeyPool("gemini", ("GEMINI_API_KEY", "GOOGLE_API_KEY"),
                           vault_dir=tmp_path)
    assert g_pool.all_keys() == ["gk-vault-1"]
    st = g_pool.status()
    assert st["pool_size"] == 1
    assert st["active_fingerprint"] == "lt-1"  # last 4 chars of gk-vault-1
    assert st["vault_keys"] == 1
    # never leak raw keys through status
    assert "gk-vault-1" not in str(st)


def test_keyring_env_precedence_and_dedup(tmp_path, monkeypatch):
    import keyring as kring
    monkeypatch.setenv("NOVITA_API_KEY", "nv-primary")
    (tmp_path / "novita+backup.key").write_text("nv-backup")
    (tmp_path / "novita+dupe.key").write_text("nv-primary")
    pool = kring.KeyPool("novita", ("NOVITA_API_KEY",), vault_dir=tmp_path)
    assert pool.all_keys() == ["nv-primary", "nv-backup"]


def test_gen_rotates_pool_on_429(monkeypatch, tmp_path):
    """A rate-limited key must trigger rotation to the next vault key."""
    import requests as req

    calls = []

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append(headers["Authorization"])
        r = type("R", (), {})()
        if headers["Authorization"].endswith("key-one"):
            def boom():
                raise req.HTTPError("429 Too Many Requests")
            r.raise_for_status = boom
        else:
            r.raise_for_status = lambda: None
            r.json = lambda: {"data": [{"b64_json": base64.b64encode(b"img").decode()}]}
        return r

    monkeypatch.setattr(gen.requests, "post", fake_post)
    monkeypatch.setattr(gen, "_or_pick_model", lambda: "fake/model")
    monkeypatch.setenv("OPENROUTER_API_KEY", "or-key-one")
    (tmp_path / "openrouter+second.key").write_text("or-key-two")
    pool = gen.kring.KeyPool("openrouter", ("OPENROUTER_API_KEY",),
                             vault_dir=tmp_path)
    monkeypatch.setattr(gen, "openrouter_pool", lambda: pool)

    data, meta = gen.openrouter_image("prompt")
    assert data == b"img"
    assert meta["key"] == "...-two"          # rotated off the 429'd key
    assert calls[0].endswith("or-key-one")  # first attempt used key one
    assert calls[-1].endswith("or-key-two")  # second attempt used key two
