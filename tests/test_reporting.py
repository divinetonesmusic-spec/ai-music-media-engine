"""Report Generation — spec §12, §16, §18 component 7. Deterministic, no network."""

from __future__ import annotations

import json

from tests.conftest import FIXTURES, PROJECT_ROOT, load_fixture

from market_intelligence.config.loader import load_ranking_config
from market_intelligence.evaluation import evaluate_opportunities
from market_intelligence.framing import frame_signals
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.matching import match_assets
from market_intelligence.ranking import rank_opportunities
from market_intelligence.reporting import generate_reports
from market_intelligence.schema.codec import decode
from market_intelligence.schema.models import RunConfig, RunPaths, Signal
from market_intelligence.schema.validate import blocking, validate_opportunity

_FIXTURE_ROOT = FIXTURES / "pipeline"
_OPP_ID = "opp_2026-08-28_e1a48ddf1c"
RANKING = load_ranking_config(project_root=PROJECT_ROOT)

_SECTIONS = [
    "## 1. Identity",
    "## 2. Market Context",
    "## 3. Evidence",
    "## 4. Evaluation",
    "## 5. Business Outcome Profile",
    "## 6. Asset Fit",
    "## 7. Hypotheses",
    "## 8. Recommendation",
    "## 9. Provenance",
]


def _cfg(**over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_pipe",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["web_search"],
        "replay": {"enabled": True, "llm": "recorded", "fixture_path": str(_FIXTURE_ROOT)},
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _pipeline(tmp_path, cfg=None):
    cfg = cfg or _cfg()
    kn = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)
    signals = [decode(Signal, d) for d in load_fixture("pipeline/signals.json")]
    framed = frame_signals(
        signals, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).opportunities
    matches = match_assets(
        framed, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).matches
    bundles = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles
    ranking = rank_opportunities(
        framed, bundles, ranking_config=RANKING,
        max_presented=cfg.max_opportunities_presented,
    )
    result = generate_reports(
        ranking, {o.opportunity_id: o for o in framed}, matches, bundles,
        signals=signals, knowledge=kn, run_config=cfg, project_root=tmp_path,
        collection_summary={"sources_used": ["web_search"], "sources_failed": []},
        generated_at="2026-08-28T12:00:00Z", replay=True,
    )
    return result, signals, kn


def test_writes_report_sidecar_digest_and_review(tmp_path):
    result, _, _ = _pipeline(tmp_path)
    base = tmp_path / "reports" / "run_pipe"
    assert (base / f"{_OPP_ID}.md").is_file()
    assert (base / f"{_OPP_ID}.json").is_file()
    assert (base / "digest.md").is_file()
    assert (base / "review.md").is_file()


def test_report_has_all_nine_sections_in_order(tmp_path):
    result, signals, _ = _pipeline(tmp_path)
    md = (tmp_path / "reports" / "run_pipe" / f"{_OPP_ID}.md").read_text()
    positions = [md.index(s) for s in _SECTIONS]
    assert positions == sorted(positions)
    assert md.startswith("---\n")  # YAML front matter


def test_front_matter_is_complete_and_target_state_is_a_v1_state(tmp_path):
    result, _, _ = _pipeline(tmp_path)
    md = (tmp_path / "reports" / "run_pipe" / f"{_OPP_ID}.md").read_text()
    fm = md.split("---\n")[1]
    import yaml

    data = yaml.safe_load(fm)
    for key in ("opportunity_id", "run_id", "schema_version", "created_at", "rank", "title",
                "market", "language", "platforms", "durability", "urgency",
                "potential_cluster", "overall_confidence", "target_state"):
        assert key in data
    assert data["target_state"] in ("EXPLORE", "TEST", "PARK")
    assert data["rank"] == 1


def test_assembled_opportunity_passes_the_section_13_validator(tmp_path):
    result, signals, kn = _pipeline(tmp_path)
    opp = result.opportunities[_OPP_ID]
    errs = blocking(validate_opportunity(
        opp,
        known_signal_ids={s.signal_id for s in signals},
        canonical_cluster_ids=kn.canonical_cluster_ids,
        inventory=kn.inventory,
        musical_dna_needs_input=True,
    ))
    assert errs == []


def test_sidecar_json_round_trips_to_the_same_opportunity(tmp_path):
    result, _, _ = _pipeline(tmp_path)
    from market_intelligence.schema.codec import decode as _decode
    from market_intelligence.schema.models import Opportunity

    data = json.loads((tmp_path / "reports" / "run_pipe" / f"{_OPP_ID}.json").read_text())
    restored = _decode(Opportunity, data)
    assert restored.opportunity_id == _OPP_ID
    assert restored.recommendation.execution_note.startswith("V1 does not execute")


def test_evidence_section_separates_observed_inferred_hypothesis(tmp_path):
    result, _, _ = _pipeline(tmp_path)
    md = (tmp_path / "reports" / "run_pipe" / f"{_OPP_ID}.md").read_text()
    ev = md.split("## 3. Evidence")[1].split("## 4.")[0]
    assert "### Observed facts" in ev
    assert "### Inferences" in ev
    assert "### Hypotheses" in ev
    assert "[OBSERVED]" in ev and "observed_at:" in ev


def test_digest_lists_presented_and_flags_below_target(tmp_path):
    result, _, _ = _pipeline(tmp_path)
    digest = (tmp_path / "reports" / "run_pipe" / "digest.md").read_text()
    assert _OPP_ID in digest
    assert "Below C10 target" in digest  # only 1 opportunity from the fixture


def test_review_template_prefills_the_presented_rows(tmp_path):
    result, _, _ = _pipeline(tmp_path)
    review = (tmp_path / "reports" / "run_pipe" / "review.md").read_text()
    assert "owner_decision" in review
    assert _OPP_ID in review
    assert "opportunities_presented: 1" in review


def test_no_report_is_written_under_knowledge(tmp_path):
    _pipeline(tmp_path)
    assert not (tmp_path / "knowledge").exists()


def _clone_pipeline_fixtures(tmp_path):
    fx = tmp_path / "pipeline"
    for sub in ("framing", "matching", "evaluation"):
        (fx / "llm" / sub).mkdir(parents=True, exist_ok=True)
    (fx / "signals.json").write_text(
        (_FIXTURE_ROOT / "signals.json").read_text(), encoding="utf-8"
    )
    for sub in ("framing", "matching", "evaluation"):
        for f in (_FIXTURE_ROOT / "llm" / sub).glob("*.json"):
            (fx / "llm" / sub / f.name).write_text(f.read_text(), encoding="utf-8")
    return fx


def test_a_compliance_hard_exclusion_carries_its_red_flags_into_the_artifacts(tmp_path):
    # the excluded record + the digest must show WHY an opportunity was hard-excluded
    # (which guardrail, what text) — not just "HIGH-severity compliance red flag".
    fx = _clone_pipeline_fixtures(tmp_path)
    resp = load_fixture("pipeline/llm/evaluation/evaluation__" + _OPP_ID + ".json")
    resp["red_flags"].append({
        "description": "G01: frames the routine as clinically proven to cure insomnia.",
        "severity": "HIGH", "kind": "compliance",
    })
    (fx / "llm" / "evaluation" / f"evaluation__{_OPP_ID}.json").write_text(
        json.dumps(resp), encoding="utf-8"
    )
    cfg = _cfg(replay={"enabled": True, "llm": "recorded", "fixture_path": str(fx)})
    result, _signals, _kn = _pipeline(tmp_path, cfg)

    assert result.opportunities == {}                       # hard-excluded, not presented

    oj = json.loads((tmp_path / "data" / "run_pipe" / "opportunities.json").read_text())
    ex = next(r for r in oj["excluded"] if r["opportunity_id"] == _OPP_ID)
    flags = ex["red_flags"]
    assert any(f["kind"] == "compliance" and f["severity"] == "HIGH"
               and "G01" in f["description"] for f in flags)

    digest = (tmp_path / "reports" / "run_pipe" / "digest.md").read_text()
    excluded_section = digest.split("## Excluded opportunities")[1].split("## ")[0]
    assert "G01" in excluded_section and "compliance" in excluded_section.lower()
    assert "HIGH" in excluded_section


def test_report_time_exclusion_is_itemized_in_the_digest_not_just_counted(tmp_path):
    # Make the evaluation fixture emit a canonical potential_cluster that is NOT in the
    # taxonomy but the framing hypothesis already fixed it — instead, break the report
    # by making an evidence signal_id unresolvable via a tampered signals list.
    from market_intelligence.evaluation import evaluate_opportunities
    from market_intelligence.framing import frame_signals
    from market_intelligence.matching import match_assets
    from market_intelligence.ranking import rank_opportunities
    from market_intelligence.reporting import generate_reports

    cfg = _cfg()
    kn = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)
    signals = [decode(Signal, d) for d in load_fixture("pipeline/signals.json")]
    framed = frame_signals(
        signals, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).opportunities
    matches = match_assets(
        framed, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).matches
    bundles = evaluate_opportunities(
        framed, matches, knowledge=kn, config=cfg, project_root=PROJECT_ROOT
    ).bundles
    ranking = rank_opportunities(
        framed, bundles, ranking_config=RANKING, max_presented=10
    )
    # pass an EMPTY signals list to reporting → OBSERVED evidence no longer resolves →
    # validate_opportunity fails → the opportunity is excluded at report time
    result = generate_reports(
        ranking, {o.opportunity_id: o for o in framed}, matches, bundles,
        signals=[], knowledge=kn, run_config=cfg, project_root=tmp_path,
        generated_at="2026-08-28T12:00:00Z", replay=True,
    )
    assert result.opportunities == {}
    assert _OPP_ID in result.excluded_at_report
    digest = (tmp_path / "reports" / "run_pipe" / "digest.md").read_text()
    excluded_section = digest.split("## Excluded opportunities")[1]
    assert _OPP_ID in excluded_section
    review = (tmp_path / "reports" / "run_pipe" / "review.md").read_text()
    assert _OPP_ID not in review  # no phantom row for a dropped opportunity
