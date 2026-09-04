"""Page Blueprint V1 — recorded-replay end-to-end (contract §8, §12).

Runs the whole stage offline (recorded LLM fixture, no network) on the real,
live-produced ClusterStrategy sidecar for `opp_2026-08-31_1bca4af972`
(MAP_TO_EXISTING -> limpeza-energetica, target_next_stage PAGE_BLUEPRINT) and
asserts the transform: page identity + visual identity grounded in §9.9, the
asset link carried verbatim (no re-decision), confidence clamped to the
Cluster Strategy's own LOW ceiling, no 0-100 score, all 7 sections rendered,
nothing written under knowledge/.
"""

from __future__ import annotations

import json

import pytest
from tests.conftest import PROJECT_ROOT

from market_intelligence.schema.codec import decode
from market_intelligence.schema.models import RunPaths
from page_blueprint.config import PageBlueprintConfig, PBReplayConfig
from page_blueprint.orchestrator import PageBlueprintError, run_page_blueprint

_OID = "opp_2026-08-31_1bca4af972"
_SIDECAR = PROJECT_ROOT / "reports" / "cluster-strategy" / f"{_OID}.json"
_FIXTURES = "tests/fixtures/page_blueprint"


def _config(tmp_path, *, replay_llm="recorded") -> PageBlueprintConfig:
    return PageBlueprintConfig(
        run_id="pb_run_2026-09-04_01",
        model="claude-sonnet-5",
        prompt_version="pb-v1-test",
        run_date="2026-09-04",
        reports_subdir=str(tmp_path / "page-blueprint"),
        paths=RunPaths(),
        replay=PBReplayConfig(enabled=True, fixture_path=_FIXTURES, llm=replay_llm),
    )


@pytest.fixture
def result(tmp_path):
    return run_page_blueprint(
        _SIDECAR, config=_config(tmp_path), project_root=PROJECT_ROOT,
        generated_at="2026-09-04T12:00:00Z",
    )


def test_page_identity_is_synthesized(result):
    ident = result.page_blueprint.identity
    assert ident.concept_name == "Ritual Nuevo Hogar"
    assert ident.positioning_statement
    assert ident.bio


def test_visual_identity_is_grounded_in_musical_dna_99(result):
    vis = result.page_blueprint.visual_identity
    assert "Limpeza energética" in vis.musical_dna_expression_used
    assert "medical claim" in vis.musical_dna_expression_used


def test_asset_link_is_carried_verbatim_not_redecided(result):
    a = result.page_blueprint.asset_link
    assert a.primary_playlist_id == "pl_4oV5F1W2E6azZePnmqBanN"
    assert a.primary_artist_id == "art_7bnKOg3GDWAbLFtNhyn8Gw"
    assert a.page_strategy.primary_page_id == "UNKNOWN"
    assert a.page_strategy.new_page_recommendation is not None


def test_content_pillars_stay_a_broad_outline(result):
    cf = result.page_blueprint.content_framing
    assert 1 <= len(cf.content_pillars) <= 5
    assert cf.platforms == ["tiktok"]


def test_no_0_to_100_score_anywhere(result):
    from market_intelligence.schema.codec import encode
    from market_intelligence.schema.validate import scan_json_for_numeric_score
    assert scan_json_for_numeric_score(encode(result.page_blueprint)) == []


def test_overall_confidence_is_clamped_to_the_cluster_strategys_ceiling(result):
    # the fixture model draft says MEDIUM; the Cluster Strategy's own
    # overall_confidence is LOW — Page Blueprint can never be more confident.
    assert result.page_blueprint.evaluation.overall_confidence.value == "LOW"
    assert result.page_blueprint.cluster_strategy.overall_confidence.value == "LOW"


def test_recommendation_target_next_stage(result):
    assert result.page_blueprint.recommendation.target_next_stage.value == "CONTENT_STRATEGY"


def test_report_has_all_seven_sections_and_a_round_tripping_sidecar(result):
    md = result.report_path.read_text()
    for h in ["## 1. Identity", "## 2. Page Identity", "## 3. Visual Identity",
              "## 4. Asset Link", "## 5. Content Framing",
              "## 6. Evaluation & Confidence", "## 7. Recommendation"]:
        assert h in md
    assert md.startswith("---\n")  # front matter
    from page_blueprint.schema.models import PageBlueprint
    raw = json.loads(result.sidecar_path.read_text())
    assert decode(PageBlueprint, raw) == result.page_blueprint


def test_replay_run_is_stamped(result):
    assert result.page_blueprint.provenance.replay is True
    assert result.llm_mode in ("recorded", "injected")


def test_nothing_is_written_under_knowledge(result, tmp_path):
    assert not (tmp_path / "knowledge").exists()


def test_a_missing_llm_fixture_is_a_hard_failure(tmp_path):
    cfg = _config(tmp_path)
    cfg.replay.fixture_path = str(tmp_path / "no_fixtures_here")
    with pytest.raises(PageBlueprintError):
        run_page_blueprint(_SIDECAR, config=cfg, project_root=PROJECT_ROOT)
