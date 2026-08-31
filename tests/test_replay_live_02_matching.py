"""The real Asset-Matching responses captured live (2026-08-31) over 3 of the 13
live_02 FramedOpportunities, into ``tests/fixtures/replay/live_02/llm/matching/``.

3 live Matching calls produced these fixtures — no Web Search / Normalization /
Framing were re-run, and Evaluation / Ranking / Reporting / Registry were not run.
The 3 opportunities are the first 3 of the 13 sorted by ``opportunity_id``
(deterministic selection). Every test here is fully offline.

Evaluation could NOT be captured in the same run: every Evaluation call returned
``400 "The compiled grammar is too large"`` — the structured-output schema is
still over the Anthropic grammar-size limit even after the ``5d9781f`` flatten.
That fix is pending an owner decision; no evaluation fixtures exist yet.
"""

from __future__ import annotations

import json
import re

from tests.conftest import PROJECT_ROOT

from market_intelligence.framing import frame_signals
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.matching import _candidates, match_assets
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.models import RunConfig, RunPaths, Signal
from market_intelligence.schema.validate import validate_asset_match

FIXTURE = PROJECT_ROOT / "tests" / "fixtures" / "replay" / "live_02"
_SECRET = re.compile(r"sk-ant-|x-api-key|authorization|bearer |api[_-]?key|/Users/|/home/", re.I)
_N_PICK = 3


def _knowledge():
    return load_knowledge(RunPaths(), project_root=PROJECT_ROOT)


def _replay_cfg() -> RunConfig:
    return decode(RunConfig, {
        "schema_version": "1.0.0", "run_id": "run_live_02_replay", "run_date": "2026-08-30",
        "model": "claude-sonnet-5", "prompt_version": "p", "signal_sources": ["web_search"],
        "max_candidates": 15,
        "replay": {"enabled": True, "fixture_path": str(FIXTURE)},
    })


def _signals():
    return [decode(Signal, d) for d in json.loads((FIXTURE / "signals.json").read_text())]


def _picked():
    kn = _knowledge()
    opps = frame_signals(
        _signals(), knowledge=kn, config=_replay_cfg(),
        project_root=PROJECT_ROOT, now="2026-08-30T00:00:00Z",
    ).opportunities
    return kn, sorted(opps, key=lambda o: o.opportunity_id)[:_N_PICK]


def _match(kn, picked):
    return match_assets(picked, knowledge=kn, config=_replay_cfg(), project_root=PROJECT_ROOT)


# --- fixtures present + clean --------------------------------------


def test_matching_fixtures_exist_for_the_3_picked():
    kn, picked = _picked()
    assert len(picked) == _N_PICK
    for o in picked:
        assert (FIXTURE / "llm" / "matching" / f"matching__{o.opportunity_id}.json").is_file()


def test_captured_matching_fixtures_carry_no_secrets_or_local_paths():
    for p in (FIXTURE / "llm" / "matching").glob("*.json"):
        assert not _SECRET.search(p.read_text(encoding="utf-8")), p.name


# --- §10.2a — every artist is a candidate, live-confirmed --------


def test_candidate_generation_sends_every_artist_for_each_picked_opportunity():
    kn, picked = _picked()
    artist_ids = {a["artist_id"] for a in kn.artists}
    for o in picked:
        gen = {c.asset_id for c in _candidates(o, kn) if c.asset_type == "artist"}
        assert gen == artist_ids, f"{o.opportunity_id}: not every artist was a candidate (§10.2a)"


# --- Asset Matching replays the real responses --------------------


def test_matching_replay_produces_a_valid_assetmatch_per_opportunity():
    kn, picked = _picked()
    res = _match(kn, picked)
    assert res.llm_mode == "recorded"
    playlist_ids = {p["playlist_id"] for p in kn.playlists}
    page_ids = {p["page_id"] for p in kn.pages}
    artist_ids = {a["artist_id"] for a in kn.artists}
    for o in picked:
        am = res.matches[o.opportunity_id]
        # a technical failure would have poisoned the reason with this prefix
        assert not (am.unmatched_reason or "").startswith("asset matching could not run")
        # every referenced asset id exists in the inventory (§10.4) — no invention
        for c in am.matching_playlists:
            assert c.asset_id in playlist_ids
        for c in am.matching_pages:
            assert c.asset_id in page_ids
        for c in am.matching_artists:
            assert c.asset_id in artist_ids
        assert am.best_playlist in playlist_ids | {"UNKNOWN"}
        assert am.best_page in page_ids | {"UNKNOWN", "NEW_ASSET"}
        assert am.best_artist in artist_ids | {"UNKNOWN"}
        # §13 asset-fit validation passes (only warnings, if any)
        assert validate_asset_match(am, inventory=kn.inventory) == []


def test_matching_replay_is_deterministic():
    kn, picked = _picked()
    a = {k: encode(v) for k, v in _match(kn, picked).matches.items()}
    b = {k: encode(v) for k, v in _match(kn, picked).matches.items()}
    assert a == b


def test_matching_new_asset_recommendation_has_all_four_i5_conditions():
    kn, picked = _picked()
    for am in _match(kn, picked).matches.values():
        rec = am.new_asset_recommendation
        if rec is None:
            continue
        c = rec.i5_conditions_met
        assert {c.no_adequate_fit, c.relevant_potential,
                c.differentiation_potential, c.sufficient_window} <= {True, False}
        assert rec.rationale
