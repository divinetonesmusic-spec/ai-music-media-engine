"""Cluster Strategy V1 — recorded-replay end-to-end (contract §12, §14).

Runs the whole stage offline (recorded LLM fixture, no network) on Run 1's
owner-advanced opportunity `opp_2026-08-31_1bca4af972` and asserts the transform:
MAP_TO_EXISTING limpeza-energetica, no invented asset, no 0–100 score, the
compliance flag carried, the opportunity lifecycle untouched, all 8 sections
rendered, nothing written under knowledge/.
"""

from __future__ import annotations

import json

import pytest
from tests.conftest import PROJECT_ROOT

from cluster_strategy.config import ClusterStrategyConfig, CSReplayConfig
from cluster_strategy.orchestrator import ClusterStrategyError, run_cluster_strategy
from market_intelligence.schema.codec import decode
from market_intelligence.schema.models import RunPaths

_RUN = "run_2026-08-31_01"
_OID = "opp_2026-08-31_1bca4af972"
_SIDECAR = PROJECT_ROOT / "reports" / _RUN / f"{_OID}.json"
_FIXTURES = "tests/fixtures/cluster_strategy"


def _config(tmp_path, *, write_registry_link=False, replay_llm="recorded") -> ClusterStrategyConfig:
    return ClusterStrategyConfig(
        run_id="cs_run_2026-09-01_01",
        model="claude-sonnet-5",
        prompt_version="cs-v1-test",
        run_date="2026-09-01",
        reports_subdir=str(tmp_path / "cluster-strategy"),
        write_registry_link=write_registry_link,
        paths=RunPaths(),
        replay=CSReplayConfig(enabled=True, fixture_path=_FIXTURES, llm=replay_llm),
    )


@pytest.fixture
def result(tmp_path):
    return run_cluster_strategy(
        _SIDECAR, config=_config(tmp_path), project_root=PROJECT_ROOT,
        now="2026-09-01T18:00:00Z",
    )


def test_maps_to_the_existing_canonical_cluster(result):
    cs = result.cluster_strategy
    assert cs.cluster_decision.decision.value == "MAP_TO_EXISTING"
    assert cs.cluster_decision.cluster_id == "limpeza-energetica"
    assert cs.cluster_decision.cluster_name == "Limpeza Energética"
    assert cs.cluster_decision.is_new_subcluster is True
    assert "moving" in (cs.cluster_decision.subcluster_or_angle or "").lower()


def test_asset_strategy_reuses_only_real_inventory_assets(result):
    a = result.cluster_strategy.asset_strategy
    assert a.playlist_strategy.primary_playlist_id == "pl_4oV5F1W2E6azZePnmqBanN"
    assert a.artist_strategy.best_artist_id == "art_7bnKOg3GDWAbLFtNhyn8Gw"
    # a new page is recommended (carried); its design is NOT here
    assert a.page_strategy.new_page_recommendation is not None
    assert a.page_strategy.primary_page_id == "UNKNOWN"


def test_no_0_to_100_score_anywhere(result):
    from market_intelligence.schema.codec import encode
    from market_intelligence.schema.validate import scan_json_for_numeric_score
    assert scan_json_for_numeric_score(encode(result.cluster_strategy)) == []


def test_the_compliance_flag_is_carried_forward(result):
    flags = result.cluster_strategy.evaluation.red_flags
    assert any(f.kind.value == "compliance" for f in flags)


def test_the_opportunity_lifecycle_is_carried_not_transitioned(result):
    cs = result.cluster_strategy
    # opportunity_lifecycle_state carries the opportunity's ACTUAL registry status
    # (EXPLORE), NOT the Market Intelligence recommendation to advance to TEST.
    assert cs.opportunity.status.value == "EXPLORE"
    assert cs.recommendation.opportunity_lifecycle_state.value == "EXPLORE"
    # the MI recommendation (advance to TEST) is kept as context, clearly distinct
    assert cs.opportunity.target_state.value == "TEST"
    # no LAUNCH/SCALE/KILL in the recommendation vocabulary
    assert cs.recommendation.target_next_stage.value == "PAGE_BLUEPRINT"


def test_overall_confidence_capped_at_the_opportunitys(result):
    # the opportunity is LOW; the model draft may say more, but it is clamped
    assert result.cluster_strategy.evaluation.overall_confidence.value == "LOW"


def test_report_has_all_eight_sections_and_a_round_tripping_sidecar(result, tmp_path):
    md = result.report_path.read_text()
    for h in ["## 1. Identity", "## 2. Cluster Decision", "## 3. Strategic Definition",
              "## 4. Asset Strategy", "## 5. Content Direction",
              "## 6. Evaluation & Confidence", "## 7. Recommendation", "## 8. Provenance"]:
        assert h in md
    assert md.startswith("---\n")  # front matter
    # observed / derived / hypothesis are visually separated
    assert "HYPOTHESIS" in md and "Derived decisions" in md
    from cluster_strategy.schema.models import ClusterStrategy
    raw = json.loads(result.sidecar_path.read_text())
    assert decode(ClusterStrategy, raw) == result.cluster_strategy


def test_replay_run_is_stamped(result):
    assert result.cluster_strategy.provenance.replay is True
    assert result.llm_mode in ("recorded", "injected")


def test_nothing_is_written_under_knowledge(result, tmp_path):
    # write_registry_link is False for this run
    assert result.registry_updated is False
    assert not (tmp_path / "knowledge").exists()


def test_a_missing_llm_fixture_is_a_hard_failure(tmp_path):
    cfg = _config(tmp_path)
    cfg.replay.fixture_path = str(tmp_path / "no_fixtures_here")
    with pytest.raises(ClusterStrategyError):
        run_cluster_strategy(_SIDECAR, config=cfg, project_root=PROJECT_ROOT)
