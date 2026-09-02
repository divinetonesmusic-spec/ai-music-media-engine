"""Cluster Strategy V1 — the DEFER / PROPOSE_NEW_CLUSTER / forced-REJECT branches
(contract §3.2, §3.4, §9). Same advanced opportunity, different recorded model
responses.
"""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from cluster_strategy.config import ClusterStrategyConfig, CSReplayConfig
from cluster_strategy.orchestrator import run_cluster_strategy
from market_intelligence.schema.models import RunPaths

_OID = "opp_2026-08-31_1bca4af972"
_SIDECAR = PROJECT_ROOT / "reports" / "run_2026-08-31_01" / f"{_OID}.json"


def _run(tmp_path, fixtures: str):
    cfg = ClusterStrategyConfig(
        run_id="cs_run_test_01", model="claude-sonnet-5", prompt_version="cs-v1-test",
        run_date="2026-09-01", reports_subdir=str(tmp_path / "out"),
        write_registry_link=False, paths=RunPaths(),
        replay=CSReplayConfig(enabled=True, fixture_path=fixtures, llm="recorded"),
    )
    return run_cluster_strategy(_SIDECAR, config=cfg, project_root=PROJECT_ROOT,
                                now="2026-09-01T18:00:00Z")


def test_defer_omits_the_strategy_sections_and_recommends_formalize(tmp_path):
    cs = _run(tmp_path, "tests/fixtures/cluster_strategy_defer").cluster_strategy
    assert cs.cluster_decision.decision.value == "DEFER"
    assert cs.cluster_decision.deferral_reason
    assert cs.strategic_definition is None
    assert cs.asset_strategy is None
    assert cs.content_direction is None
    assert cs.recommendation.target_next_stage.value == "FORMALIZE_CLUSTER"
    assert cs.recommendation.opportunity_lifecycle_state.value == "EXPLORE"  # opp's real status


def test_propose_new_cluster_carries_the_boundary_map_and_never_writes_the_taxonomy(tmp_path):
    result = _run(tmp_path, "tests/fixtures/cluster_strategy_propose")
    cs = result.cluster_strategy
    p = cs.cluster_decision.new_cluster_proposal
    assert cs.cluster_decision.decision.value == "PROPOSE_NEW_CLUSTER"
    assert cs.cluster_decision.cluster_id is None
    assert p is not None and set(p.boundary_vs_adjacent) <= {c.id for c in _canon()}
    assert "does not modify cluster-taxonomy.md" in p.governance_note
    assert cs.recommendation.target_next_stage.value == "FORMALIZE_CLUSTER"
    # the taxonomy file on disk is byte-identical
    tax = PROJECT_ROOT / "knowledge" / "clusters" / "cluster-taxonomy.md"
    assert "mudanza-hogar-ritual" not in tax.read_text()
    md = result.report_path.read_text()
    assert "Proposed new cluster (HYPOTHESIS" in md


def test_a_high_compliance_claim_in_core_content_forces_reject(tmp_path):
    cs = _run(tmp_path, "tests/fixtures/cluster_strategy_reject").cluster_strategy
    assert cs.cluster_decision.decision.value == "REJECT"
    assert "compliance" in (cs.cluster_decision.rejection_reason or "").lower()
    assert cs.recommendation.target_next_stage.value == "HOLD"
    assert cs.recommendation.opportunity_lifecycle_state.value == "EXPLORE"  # NOT transitioned
    assert any(f.kind.value == "compliance" for f in cs.evaluation.red_flags)


def test_a_high_compliance_claim_in_a_hypothesis_scope_is_stripped_not_rejected(tmp_path):
    # The drafted first_content_direction contains a HIGH-severity G03 claim
    # ("treatment for depression"). That scope is NOT core content, so MI guardrail
    # semantics say: strip the offending hypothesis text, keep the strategy.
    result = _run(tmp_path, "tests/fixtures/cluster_strategy_strip")
    cs = result.cluster_strategy
    cd = cs.content_direction
    # NOT rejected — the strategy stands
    assert cs.cluster_decision.decision.value == "MAP_TO_EXISTING"
    assert cs.recommendation.target_next_stage.value == "PAGE_BLUEPRINT"
    # the offending direction text is removed (strip_scopes applied)
    assert "treatment for depression" not in cd.first_content_direction
    assert cd.first_content_direction.startswith("[removed")
    assert cd.editorial_angles == []
    # music_relationship (a different, clean field) survives
    assert "ambient bed" in cd.music_relationship
    # a HIGH compliance red flag is still surfaced
    assert any(f.kind.value == "compliance" and f.severity.value == "HIGH"
               for f in cs.evaluation.red_flags)
    # and the report does not carry the stripped claim
    assert "treatment for depression" not in result.report_path.read_text()


def test_needs_uncertainty_note_scopes_become_open_questions(tmp_path, monkeypatch):
    # No current scanner emits `require_uncertainty_statement` (same as MI), so
    # inject a ComplianceResult to prove the orchestrator honours the branch.
    import cluster_strategy.orchestrator as orch
    from market_intelligence.guardrails import ComplianceResult

    real = orch.check_cluster_strategy_prose

    def _patched(prose, *, guardrails):
        r = real(prose, guardrails=guardrails)
        r.needs_uncertainty_note.add("report_prose")
        return r

    monkeypatch.setattr(orch, "check_cluster_strategy_prose", _patched)
    assert ComplianceResult().needs_uncertainty_note == set()  # sanity
    cs = _run(tmp_path, "tests/fixtures/cluster_strategy").cluster_strategy
    assert any("uncertainty" in q.lower() and "report_prose" in q
               for q in cs.evaluation.open_questions)


def test_a_verbatim_restated_red_flag_is_deduped_but_a_distinct_one_survives(tmp_path):
    # The model restates the opportunity's carried compliance flag word-for-word;
    # the orchestrator also carries it. It must appear exactly once — and the
    # model's genuinely distinct feasibility flag must NOT be dropped.
    cs = _run(tmp_path, "tests/fixtures/cluster_strategy_dupflag").cluster_strategy
    flags = cs.evaluation.red_flags
    cleansing = [f for f in flags if "energetic cleansing" in f.description.lower()]
    assert len(cleansing) == 1
    assert any(f.kind.value == "feasibility" and "follower data" in f.description
               for f in flags)


def _canon():
    from market_intelligence.knowledge_loader import load_knowledge
    return load_knowledge(RunPaths(), project_root=PROJECT_ROOT).clusters
