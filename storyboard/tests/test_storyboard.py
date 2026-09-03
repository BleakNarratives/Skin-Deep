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


# ── db round-trip ────────────────────────────────────────────────────────

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


def test_outline_text_path_traversal_prevention(api, tmp_db):
    ep = tmp_db.create_episode(1, 100, "test_traversal", "Traversal", "log", outline_path="../backend/app.py")
    with pytest.raises(HTTPException) as ei:
        api._outline_text(ep)
    assert ei.value.status_code == 400
    assert ei.value.detail == "invalid outline path"


def test_panels_require_scenes(api):
    ep = api.create_episode(api.EpisodeCreate(
        season=1, number=3, slug="test_no_scenes", title="NoScenes"))
    with pytest.raises(HTTPException) as ei:
        api.generate_panels(ep["id"])
    assert ei.value.status_code == 400


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
