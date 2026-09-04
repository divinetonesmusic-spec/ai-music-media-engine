"""Page Blueprint V1 — the compliance-driven forced-HOLD / strip branches
(contract §6, §14 "technical failure != business state"). Same real
Cluster-Strategy-recommended sidecar, different recorded model responses.
"""

from __future__ import annotations

from tests.conftest import PROJECT_ROOT

from market_intelligence.schema.models import RunPaths
from page_blueprint.config import PageBlueprintConfig, PBReplayConfig
from page_blueprint.orchestrator import run_page_blueprint

_OID = "opp_2026-08-31_1bca4af972"
_SIDECAR = PROJECT_ROOT / "reports" / "cluster-strategy" / f"{_OID}.json"


def _run(tmp_path, fixtures: str):
    cfg = PageBlueprintConfig(
        run_id="pb_run_test_01", model="claude-sonnet-5", prompt_version="pb-v1-test",
        run_date="2026-09-04", reports_subdir=str(tmp_path / "out"), paths=RunPaths(),
        replay=PBReplayConfig(enabled=True, fixture_path=fixtures, llm="recorded"),
    )
    return run_page_blueprint(_SIDECAR, config=cfg, project_root=PROJECT_ROOT,
                               generated_at="2026-09-04T12:00:00Z")


def test_a_high_compliance_claim_in_core_content_forces_hold(tmp_path):
    pb = _run(tmp_path, "tests/fixtures/page_blueprint_reject").page_blueprint
    assert pb.recommendation.target_next_stage.value == "HOLD"
    assert "compliance" in pb.recommendation.justification.lower()
    assert any(f.kind.value == "compliance" and f.severity.value == "HIGH"
               for f in pb.evaluation.red_flags)
    # the identity/bio itself is untouched (forced HOLD, not a silent rewrite)
    assert "cura tu trastorno" in pb.identity.bio


def test_a_high_compliance_claim_in_content_pillars_is_stripped_not_rejected(tmp_path):
    result = _run(tmp_path, "tests/fixtures/page_blueprint_strip")
    pb = result.page_blueprint
    # NOT forced to HOLD — the page design stands
    assert pb.recommendation.target_next_stage.value == "CONTENT_STRATEGY"
    assert pb.content_framing.content_pillars == [
        "[removed — a HIGH-severity compliance guardrail flagged the drafted content "
        "pillars; Content Strategy (stage 5) must supply compliant ones]"
    ]
    assert any(f.kind.value == "compliance" and f.severity.value == "HIGH"
               for f in pb.evaluation.red_flags)
    # the stripped pillar's full original claim does not survive in the report
    # (the red-flag list may still quote the short matched fragment as evidence)
    assert "para siempre" not in result.report_path.read_text()
