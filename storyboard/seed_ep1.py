#!/usr/bin/env python3
"""
seed_ep1.py — create the Skin Deep S1E1 episode row from the canonical
outline (episodes/ep1_the_handshake.md). Idempotent: skips if slug exists.

Run:  python3 seed_ep1.py        (from storyboard/, any python with stdlib)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import storyboard_db as db  # noqa: E402

SLUG = "ep1_the_handshake"


def main() -> None:
    db.init_db()
    if db.get_episode_by_slug(SLUG):
        print(f"[seed] episode '{SLUG}' already exists — nothing to do")
        return
    outline_path = Path(__file__).parent / "episodes" / f"{SLUG}.md"
    ep = db.create_episode(
        season=1,
        number=1,
        slug=SLUG,
        title="The Handshake",
        logline=("A broke operator walks into a master's shop with salvaged "
                 "sensors — and walks out with a handshake and a deadline."),
        outline_path=str(outline_path.relative_to(Path(__file__).parent)),
    )
    print(f"[seed] created episode id={ep['id']} S1E1 '{ep['title']}'")
    print("[seed] next: start the service and run 'outline → scenes'")


if __name__ == "__main__":
    main()
