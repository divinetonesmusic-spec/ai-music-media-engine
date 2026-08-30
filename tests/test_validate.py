"""Deterministic validators — one valid + one invalid case per rule in spec §13.

Each test names the §13 rule it pins. A validator returns a list of
``ValidationError``; ``[]`` means the entity is valid. Rules that the codec
already enforces at decode time (bad enum, missing required field) are pinned in
``test_models.py`` / ``test_codec.py`` and cross-referenced here.
"""

from __future__ import annotations

import copy

import yaml

from market_intelligence.schema import models as M
from market_intelligence.schema.codec import decode
from market_intelligence.schema.validate import (
    InventoryIndex,
    ValidationError,
    blocking,
    validate_asset_match,
    validate_business_outcome_profile,
    validate_canonical_clusters,
    validate_evaluation,
    validate_guardrails,
    validate_opportunity,
    validate_presented_count,
    validate_run_config,
    validate_signal,
    validate_signals,
)

CANONICAL_CLUSTER_IDS = frozenset(
    {
        "sono",
        "abundancia-prosperidade",
        "limpeza-energetica",
        "frequencia-divina-espiritualidade",
        "glandula-pineal-frequencias",
        "anjos-espiritualidade-religiosa",
        "meditacao-relaxamento",
        "ansiedade-relaxamento",
        "cura-bem-estar",
        "foco-estudo",
        "sonho-lucido",
    }
)

INVENTORY = InventoryIndex(
    artist_ids=frozenset({"art_5NJXbvpRnlTAqZ5neNTWGT"}),
    playlist_ids=frozenset({"pl_5Wz1PL0H0t7f1qCuY989ZE"}),
    page_ids=frozenset({"page_tiktok_mandalameditationss", "page_ref_competitor_x"}),
    catalog_ids=frozenset({"cat_5NJXbvpRnlTAqZ5neNTWGT_r2"}),
    own_page_ids=frozenset({"page_tiktok_mandalameditationss"}),
    reference_page_ids=frozenset({"page_ref_competitor_x"}),
)

KNOWN_SIGNAL_IDS = frozenset({"sig_run_2026-08-28_01_0001", "sig_run_2026-08-28_01_0002"})


def run_opp_validator(d):
    return validate_opportunity(
        decode(M.Opportunity, d),
        known_signal_ids=KNOWN_SIGNAL_IDS,
        canonical_cluster_ids=CANONICAL_CLUSTER_IDS,
        inventory=INVENTORY,
    )


# --- the canonical fixture is fully valid ------------------------------------

def test_fixture_opportunity_has_zero_validation_errors(valid_opportunity_dict):
    assert run_opp_validator(valid_opportunity_dict) == []


def test_fixture_signals_have_zero_validation_errors(valid_signal_dicts):
    for raw in valid_signal_dicts:
        assert validate_signal(decode(M.Signal, raw)) == []
    assert validate_signals([decode(M.Signal, r) for r in valid_signal_dicts]) == []


def test_validation_error_is_hashable_and_carries_a_code():
    e = ValidationError(code="x.y", path="a.b", message="nope")
    assert e.severity == "ERROR"
    assert {e, e} == {e}


# --- §13 Signal -----------------------------------------------------------

def test_signal_observed_at_after_collected_at_is_rejected(valid_signal_dicts):
    # §6.3: observed_at MUST NOT be in the future relative to collected_at
    d = valid_signal_dicts[0]
    d["observed_at"] = "2027-01-01"
    d["provenance"]["observed_at"] = "2027-01-01"
    errs = validate_signal(decode(M.Signal, d))
    assert any(e.code == "signal.observed_at_in_future" for e in errs)


def test_signal_market_outside_v1_taxonomy_is_rejected(valid_signal_dicts):
    # §6.3: market MUST be one of the three V1 markets or UNKNOWN
    d = valid_signal_dicts[0]
    d["market"] = "Germany"
    errs = validate_signal(decode(M.Signal, d))
    assert any(e.code == "signal.market_not_in_taxonomy" for e in errs)


def test_signal_language_outside_v1_set_is_rejected(valid_signal_dicts):
    d = valid_signal_dicts[0]
    d["language"] = "de"
    errs = validate_signal(decode(M.Signal, d))
    assert any(e.code == "signal.language_not_in_taxonomy" for e in errs)


def test_signal_raw_ref_must_match_the_canonical_path_shape(valid_signal_dicts):
    # §6.1 / §6.3: raw_ref -> data/<run_id>/signals/raw/<signal_id>.json
    d = valid_signal_dicts[0]
    d["raw_ref"] = "somewhere/else.json"
    errs = validate_signal(decode(M.Signal, d))
    assert any(e.code == "signal.raw_ref_shape" for e in errs)


def test_signal_capture_method_must_agree_with_source_type(valid_signal_dicts):
    # §6.5: web_search <-> claude_web_search, etc.
    d = valid_signal_dicts[0]
    d["provenance"]["capture_method"] = "analyst_capture"
    errs = validate_signal(decode(M.Signal, d))
    assert any(e.code == "signal.capture_method_mismatch" for e in errs)


def test_signal_provenance_mirror_fields_must_match(valid_signal_dicts):
    # §6.1: top-level source_type / observed_at / collected_at mirror provenance
    d = valid_signal_dicts[0]
    d["provenance"]["source"] = "A different source string"
    errs = validate_signal(decode(M.Signal, d))
    assert any(e.code == "signal.provenance_mirror_mismatch" for e in errs)


def test_signal_raw_ref_file_existence_check_when_raw_root_given(valid_signal_dicts, tmp_path):
    # §6.3: raw_ref MUST resolve to an existing file
    sig = decode(M.Signal, valid_signal_dicts[0])
    assert any(
        e.code == "signal.raw_ref_missing_file"
        for e in validate_signal(sig, raw_root=tmp_path)
    )
    (tmp_path / f"{sig.signal_id}.json").write_text("{}", encoding="utf-8")
    assert [
        e for e in validate_signal(sig, raw_root=tmp_path)
        if e.code == "signal.raw_ref_missing_file"
    ] == []


def test_signal_set_rejects_duplicate_ids(valid_signal_dicts):
    # §6.3: signal_id unique within a run
    a = decode(M.Signal, valid_signal_dicts[0])
    b = decode(M.Signal, valid_signal_dicts[1])
    b.signal_id = a.signal_id  # force a within-run collision
    errs = validate_signals([a, b])
    assert any(e.code == "signal.duplicate_id" for e in errs)


# --- §13 Opportunity ----------------------------------------------------

def test_opportunity_missing_a_c1_field_is_rejected(valid_opportunity_dict):
    # §13: all six C1 mandatory fields present and non-empty
    valid_opportunity_dict["consumption_context"] = "   "
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "opportunity.c1_field_empty" for e in errs)


def test_opportunity_market_language_inconsistent_is_rejected(valid_opportunity_dict):
    # §7.1a: language and market must be consistent
    valid_opportunity_dict["language"] = "es"  # market stays "Brasil"
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "opportunity.market_language_mismatch" for e in errs)


def test_opportunity_id_not_matching_the_c1_hash_is_rejected(valid_opportunity_dict):
    # §13 / §7.1: opportunity_id MUST be the deterministic hash of the C1 tuple
    valid_opportunity_dict["opportunity_id"] = "opp_2026-08-28_deadbeef00"
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "opportunity.id_hash_mismatch" for e in errs)


def test_opportunity_id_reworded_title_still_validates(valid_opportunity_dict):
    valid_opportunity_dict["title"] = "Completely different wording of the same opportunity"
    assert run_opp_validator(valid_opportunity_dict) == []


def test_opportunity_platform_outside_opportunity_set_is_rejected(valid_opportunity_dict):
    # §7.1: Opportunity.platform excludes 'web' and 'UNKNOWN'
    valid_opportunity_dict["platform"] = "web"
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "opportunity.platform_not_allowed" for e in errs)


def test_opportunity_with_no_observed_evidence_is_not_presentable(valid_opportunity_dict):
    # §13: >= 1 OBSERVED item to be eligible for the presented set
    for item in valid_opportunity_dict["evidence"]:
        if item["type"] == "OBSERVED":
            item["type"] = "INFERRED"
            item["derived_from"] = ["sig_run_2026-08-28_01_0001"]
            item["rationale"] = "downgraded for the test"
            item.pop("signal_ids", None)
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "opportunity.no_observed_evidence" for e in errs)


def test_opportunity_with_zero_evidence_items_is_rejected(valid_opportunity_dict):
    valid_opportunity_dict["evidence"] = []
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "opportunity.no_evidence" for e in errs)


def test_observed_evidence_with_dangling_signal_id_is_rejected(valid_opportunity_dict):
    # §13: every OBSERVED item's signal_ids MUST all resolve to signals in this run
    valid_opportunity_dict["evidence"][0]["signal_ids"] = ["sig_does_not_exist"]
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "evidence.signal_id_unresolved" for e in errs)


def test_inferred_evidence_without_derived_from_is_rejected(valid_opportunity_dict):
    for item in valid_opportunity_dict["evidence"]:
        if item["type"] == "INFERRED":
            item.pop("derived_from", None)
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "evidence.inferred_without_basis" for e in errs)


def test_hypothesis_evidence_without_rationale_is_rejected(valid_opportunity_dict):
    for item in valid_opportunity_dict["evidence"]:
        if item["type"] == "HYPOTHESIS":
            item["rationale"] = ""
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "evidence.hypothesis_without_rationale" for e in errs)


def test_potential_cluster_canonical_true_but_unknown_id_is_rejected(valid_opportunity_dict):
    # §13: a canonical cluster value not in cluster-taxonomy.md is a validation failure
    valid_opportunity_dict["hypotheses"]["potential_cluster"] = {
        "value": "sleepytime",
        "canonical": True,
        "basis": "existing",
    }
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "hypotheses.cluster_not_canonical" for e in errs)


def test_potential_cluster_non_canonical_must_be_proposed_new(valid_opportunity_dict):
    valid_opportunity_dict["hypotheses"]["potential_cluster"] = {
        "value": "Lo-fi rain rooms",
        "canonical": False,
        "basis": "existing",
    }
    errs = run_opp_validator(valid_opportunity_dict)
    assert any(e.code == "hypotheses.cluster_basis_inconsistent" for e in errs)


def test_potential_cluster_proposed_new_is_accepted(valid_opportunity_dict):
    valid_opportunity_dict["hypotheses"]["potential_cluster"] = {
        "value": "Lo-fi rain rooms",
        "canonical": False,
        "basis": "proposed_new",
    }
    assert run_opp_validator(valid_opportunity_dict) == []


# --- §13 Evaluation ---------------------------------------------------

def test_evaluation_missing_a_dimension_is_rejected(valid_opportunity_dict):
    del valid_opportunity_dict["evaluation"]["dimensions"]["music_fit"]
    ev = decode(M.Evaluation, valid_opportunity_dict["evaluation"])
    errs = validate_evaluation(ev)
    assert any(e.code == "evaluation.dimension_set_mismatch" for e in errs)


def test_evaluation_extra_dimension_is_rejected(valid_opportunity_dict):
    valid_opportunity_dict["evaluation"]["dimensions"]["vibes"] = {
        "rating": "HIGH", "confidence": "LOW", "justification": "n/a",
    }
    ev = decode(M.Evaluation, valid_opportunity_dict["evaluation"])
    assert any(e.code == "evaluation.dimension_set_mismatch" for e in validate_evaluation(ev))


def test_evaluation_blank_justification_is_rejected(valid_opportunity_dict):
    valid_opportunity_dict["evaluation"]["dimensions"]["signal_strength"]["justification"] = ""
    ev = decode(M.Evaluation, valid_opportunity_dict["evaluation"])
    assert any(e.code == "evaluation.justification_empty" for e in validate_evaluation(ev))


def test_music_fit_confidence_is_capped_while_dna_needs_input(valid_opportunity_dict):
    # §8.3 / §22: music_fit.confidence in {LOW, MEDIUM} while musical DNA is NEEDS_INPUT
    valid_opportunity_dict["evaluation"]["dimensions"]["music_fit"]["confidence"] = "HIGH"
    ev = decode(M.Evaluation, valid_opportunity_dict["evaluation"])
    errs = validate_evaluation(ev, musical_dna_needs_input=True)
    assert any(e.code == "evaluation.music_fit_confidence_cap" for e in errs)


def test_evaluation_numeric_0_100_score_is_rejected(valid_opportunity_dict):
    # §13 "no score" test (C6)
    valid_opportunity_dict["evaluation"]["summary"] += " Overall score: 82/100."
    ev = decode(M.Evaluation, valid_opportunity_dict["evaluation"])
    assert any(e.code == "evaluation.numeric_score_detected" for e in validate_evaluation(ev))


def test_evaluation_score_named_key_is_rejected(valid_opportunity_dict):
    d = copy.deepcopy(valid_opportunity_dict["evaluation"])
    d["dimensions"]["signal_strength"]["justification"] += " score=90"
    ev = decode(M.Evaluation, d)
    assert any(e.code == "evaluation.numeric_score_detected" for e in validate_evaluation(ev))


def test_evaluation_ordinary_numbers_do_not_trip_the_score_scanner(valid_opportunity_dict):
    ev = decode(M.Evaluation, valid_opportunity_dict["evaluation"])
    score_errs = [
        e for e in validate_evaluation(ev) if e.code == "evaluation.numeric_score_detected"
    ]
    assert score_errs == []


# --- §13 Business Outcome Profile -----------------------------------

def test_bop_missing_an_axis_is_rejected(valid_opportunity_dict):
    del valid_opportunity_dict["business_outcome_profile"]["axes"]["page_growth_potential"]
    bop = decode(M.BusinessOutcomeProfile, valid_opportunity_dict["business_outcome_profile"])
    assert any(e.code == "bop.axis_set_mismatch" for e in validate_business_outcome_profile(bop))


def test_bop_blank_justification_is_rejected(valid_opportunity_dict):
    valid_opportunity_dict["business_outcome_profile"]["axes"]["playlist_growth_potential"][
        "justification"
    ] = "  "
    bop = decode(M.BusinessOutcomeProfile, valid_opportunity_dict["business_outcome_profile"])
    assert any(e.code == "bop.justification_empty" for e in validate_business_outcome_profile(bop))


# --- §13 Asset Fit --------------------------------------------------

def test_asset_match_dangling_best_id_is_rejected(valid_opportunity_dict):
    valid_opportunity_dict["asset_fit"]["best_playlist"] = "pl_does_not_exist"
    am = decode(M.AssetMatch, valid_opportunity_dict["asset_fit"])
    errs = validate_asset_match(am, inventory=INVENTORY)
    assert any(e.code == "asset_fit.best_id_unknown" for e in errs)


def test_asset_match_dangling_candidate_id_is_a_warning(valid_opportunity_dict):
    valid_opportunity_dict["asset_fit"]["matching_artists"][0]["asset_id"] = "art_ghost"
    am = decode(M.AssetMatch, valid_opportunity_dict["asset_fit"])
    errs = validate_asset_match(am, inventory=INVENTORY)
    dangling = [e for e in errs if e.code == "asset_fit.candidate_id_unknown"]
    assert dangling and all(e.severity == "WARNING" for e in dangling)


def test_asset_match_unknown_best_without_reason_is_rejected(valid_opportunity_dict):
    valid_opportunity_dict["asset_fit"]["best_page"] = "UNKNOWN"
    am = decode(M.AssetMatch, valid_opportunity_dict["asset_fit"])
    errs = validate_asset_match(am, inventory=INVENTORY)
    assert any(e.code == "asset_fit.unmatched_reason_missing" for e in errs)


def test_asset_match_reference_competitor_page_as_best_is_rejected(valid_opportunity_dict):
    valid_opportunity_dict["asset_fit"]["best_page"] = "page_ref_competitor_x"
    am = decode(M.AssetMatch, valid_opportunity_dict["asset_fit"])
    errs = validate_asset_match(am, inventory=INVENTORY)
    assert any(e.code == "asset_fit.reference_page_not_recommendable" for e in errs)


def test_asset_match_new_asset_marker_requires_a_recommendation(valid_opportunity_dict):
    valid_opportunity_dict["asset_fit"]["best_page"] = "NEW_ASSET"
    valid_opportunity_dict["asset_fit"]["unmatched_reason"] = "No own page covers this angle."
    am = decode(M.AssetMatch, valid_opportunity_dict["asset_fit"])
    errs = validate_asset_match(am, inventory=INVENTORY)
    assert any(e.code == "asset_fit.new_asset_without_recommendation" for e in errs)


def test_new_asset_recommendation_with_unmet_i5_is_downgrade_warning(valid_opportunity_dict):
    valid_opportunity_dict["asset_fit"]["best_page"] = "NEW_ASSET"
    valid_opportunity_dict["asset_fit"]["unmatched_reason"] = "No own page covers this angle."
    valid_opportunity_dict["asset_fit"]["new_asset_recommendation"] = {
        "asset_type": "page",
        "rationale": "A dedicated page could own this niche.",
        "i5_conditions_met": {
            "no_adequate_fit": True,
            "relevant_potential": True,
            "differentiation_potential": False,
            "sufficient_window": True,
        },
    }
    am = decode(M.AssetMatch, valid_opportunity_dict["asset_fit"])
    errs = validate_asset_match(am, inventory=INVENTORY)
    assert any(
        e.code == "asset_fit.i5_conditions_incomplete" and e.severity == "WARNING" for e in errs
    )


# --- §13 Config ----------------------------------------------------

def base_config(**over):
    d = {
        "run_id": "run_2026-08-28_01",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "mi-v1-2026-08-28",
    }
    d.update(over)
    return d


def test_run_config_bad_run_id_is_rejected(project_root):
    cfg = decode(M.RunConfig, base_config(run_id="run 01/bad"))
    errs = validate_run_config(cfg, project_root=project_root)
    assert any(e.code == "config.run_id_pattern" for e in errs)


def test_run_config_zero_presented_cap_is_rejected(project_root):
    cfg = decode(M.RunConfig, base_config(max_opportunities_presented=0))
    errs = validate_run_config(cfg, project_root=project_root)
    assert any(e.code == "config.max_presented_too_low" for e in errs)


def test_run_config_missing_required_path_is_rejected(project_root):
    cfg = decode(M.RunConfig, base_config(paths={"guardrails_path": "knowledge/rules/nope.yaml"}))
    errs = validate_run_config(cfg, project_root=project_root)
    assert any(e.code == "config.path_missing" for e in errs)


def test_run_config_replay_enabled_without_fixture_path_is_rejected(project_root):
    cfg = decode(M.RunConfig, base_config(replay={"enabled": True}))
    errs = validate_run_config(cfg, project_root=project_root)
    assert any(e.code == "config.replay_fixture_path_missing" for e in errs)


def test_run_config_internal_data_source_without_path_is_rejected(project_root):
    cfg = decode(M.RunConfig, base_config(signal_sources=["internal_data"]))
    errs = validate_run_config(cfg, project_root=project_root)
    assert any(e.code == "config.internal_data_path_missing" for e in errs)


def test_valid_config_against_the_real_repo_has_no_errors(project_root):
    cfg = decode(M.RunConfig, base_config(signal_sources=["web_search", "youtube"]))
    assert validate_run_config(cfg, project_root=project_root) == []


# --- §13 guardrails.yaml / cluster-taxonomy.md ---------------------

def test_guardrails_loader_rejects_wrong_count():
    guards = [
        M.Guardrail(
            guardrail_id=f"G{i:02d}",
            name=f"g{i}",
            type="prohibition",
            description="x",
            severity="HIGH",
            action_on_violation="flag",
        )
        for i in range(1, 9)
    ]
    assert any(e.code == "guardrails.count" for e in validate_guardrails(guards))


def test_guardrails_loader_rejects_bad_id_sequence():
    guards = [
        M.Guardrail(
            guardrail_id=("GXX" if i == 3 else f"G{i:02d}"),
            name=f"g{i}",
            type="prohibition",
            description="x",
            severity="HIGH",
            action_on_violation="flag",
        )
        for i in range(1, 11)
    ]
    assert any(e.code == "guardrails.id_sequence" for e in validate_guardrails(guards))


def test_real_guardrails_file_passes(project_root):
    raw = yaml.safe_load((project_root / "knowledge/rules/guardrails.yaml").read_text())
    guards = [decode(M.Guardrail, g) for g in raw["guardrails"]]
    assert validate_guardrails(guards) == []


def test_canonical_clusters_rejects_wrong_count():
    assert any(
        e.code == "taxonomy.count" for e in validate_canonical_clusters(["a", "b", "c"])
    )


def test_canonical_clusters_accepts_eleven_unique_ids():
    assert validate_canonical_clusters(sorted(CANONICAL_CLUSTER_IDS)) == []


# --- §13 presented-set contract ---------------------------------

def test_presented_count_over_cap_is_rejected():
    assert any(
        e.code == "report.presented_over_cap"
        for e in validate_presented_count(presented=12, cap=10)
    )


def test_presented_count_below_target_is_a_warning():
    errs = validate_presented_count(presented=3, cap=10, target=5)
    assert any(e.code == "report.presented_below_target" and e.severity == "WARNING" for e in errs)


# --- helper ---------------------------------------------------

def test_blocking_filters_out_warnings():
    errs = [
        ValidationError("a", "p", "m", severity="ERROR"),
        ValidationError("b", "p", "m", severity="WARNING"),
    ]
    assert [e.code for e in blocking(errs)] == ["a"]
