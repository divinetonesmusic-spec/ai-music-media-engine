"""Signal deduplication — the config-driven §6.6 key and rules. No network."""

from __future__ import annotations

import pytest
from tests.conftest import PROJECT_ROOT, load_fixture

from market_intelligence.config.loader import load_dedup_config
from market_intelligence.normalize.dedup import (
    NormalizationError,
    dedup_key,
    deduplicate,
)
from market_intelligence.schema.codec import decode
from market_intelligence.schema.models import Signal

DEDUP = load_dedup_config(project_root=PROJECT_ROOT)
_PARTS = DEDUP["dedup_key_parts"]


def _sigs(name):
    return [decode(Signal, d) for d in load_fixture(f"normalize/{name}.json")]


def _part(sig, part_name):
    return dedup_key(sig, dedup_config=DEDUP)[_PARTS.index(part_name)]


# --- the key ---------------------------------------------------------

def test_dedup_key_is_a_deterministic_tuple_of_the_configured_parts():
    a = _sigs("dup_exact")[0]
    assert isinstance(dedup_key(a, dedup_config=DEDUP), tuple)
    assert len(dedup_key(a, dedup_config=DEDUP)) == len(_PARTS)
    assert dedup_key(a, dedup_config=DEDUP) == dedup_key(a, dedup_config=DEDUP)


def test_config_is_actually_respected_unknown_part_raises():
    bad = dict(DEDUP)
    bad["dedup_key_parts"] = list(_PARTS) + ["bogus"]
    with pytest.raises(NormalizationError):
        dedup_key(_sigs("dup_exact")[0], dedup_config=bad)


def test_tracking_params_stripped_from_canonical_url():
    a, b = _sigs("dup_exact")  # b's url carries &utm_source=newsletter
    assert _part(a, "canonical_url") == _part(b, "canonical_url")
    assert "utm_source" not in _part(b, "canonical_url")


def test_missing_url_contributes_the_missing_part_token():
    a = _sigs("dup_confidence")[0]  # no url
    assert _part(a, "canonical_url") == DEDUP["missing_part_token"]


def test_normalized_subject_drops_stopwords_and_kebab_cases():
    subj = _part(_sigs("dup_exact")[0], "normalized_subject")
    assert " " not in subj and "-" in subj
    assert "in" not in subj.split("-") and "the" not in subj.split("-")
    assert "do" not in subj.split("-")  # 'do' is a pt stopword in the config


def test_different_source_gives_a_different_key():
    a, b = _sigs("same_theme_diff_source")
    assert dedup_key(a, dedup_config=DEDUP) != dedup_key(b, dedup_config=DEDUP)
    assert _part(a, "normalized_source") != _part(b, "normalized_source")
    assert _part(a, "normalized_subject") == _part(b, "normalized_subject")  # same theme


# --- the algorithm -------------------------------------------------

def test_exact_duplicates_are_collapsed_with_a_reason():
    kept, discarded, reasons = deduplicate(_sigs("dup_exact"), DEDUP)
    assert [s.signal_id for s in kept] == ["sig_run_norm_0001"]
    assert discarded == ["sig_run_norm_0002"]
    assert (reasons[0].kept, reasons[0].dropped) == ("sig_run_norm_0001", "sig_run_norm_0002")


def test_tie_on_confidence_keeps_the_lower_signal_id():
    kept, _, _ = deduplicate(_sigs("dup_exact"), DEDUP)  # both MEDIUM
    assert kept[0].signal_id == "sig_run_norm_0001"


def test_higher_confidence_wins():
    kept, discarded, _ = deduplicate(_sigs("dup_confidence"), DEDUP)
    assert [s.signal_id for s in kept] == ["sig_run_norm_0011"]  # HIGH beats LOW
    assert discarded == ["sig_run_norm_0010"]


def test_absent_metrics_are_merged_conflicts_are_not_overwritten():
    kept, _, reasons = deduplicate(_sigs("dup_metrics_partial"), DEDUP)
    assert kept[0].signal_id == "sig_run_norm_0020"  # HIGH
    assert kept[0].metrics == {"view_count": "10", "like_count": "500"}
    assert reasons[0].merged_metric_keys == ["like_count"]


def test_exact_dup_merges_only_the_absent_metric_key():
    kept, _, reasons = deduplicate(_sigs("dup_exact"), DEDUP)
    assert kept[0].metrics == {"related_queries": "7"}
    assert reasons[0].merged_metric_keys == ["related_queries"]


def test_same_theme_different_source_stays_separate():
    kept, discarded, reasons = deduplicate(_sigs("same_theme_diff_source"), DEDUP)
    assert len(kept) == 2 and discarded == [] and reasons == []


def test_temporally_distinct_observations_stay_separate():
    kept, discarded, _ = deduplicate(_sigs("temporally_distinct"), DEDUP)
    assert sorted(s.signal_id for s in kept) == ["sig_run_norm_0040", "sig_run_norm_0041"]
    assert discarded == []


def test_dedup_is_input_order_independent():
    sigs = _sigs("dup_metrics_partial")
    fwd = deduplicate(sigs, DEDUP)
    rev = deduplicate(list(reversed(sigs)), DEDUP)
    assert [s.signal_id for s in fwd[0]] == [s.signal_id for s in rev[0]]
    assert fwd[1] == rev[1]
    assert fwd[0][0].metrics == rev[0][0].metrics
    assert fwd[2] == rev[2]


def test_original_signals_are_not_mutated():
    sigs = _sigs("dup_exact")
    kept_metrics_before = sigs[0].metrics  # None
    kept_signal_before = sigs[1].metrics  # {"related_queries": "7"}
    deduplicate(sigs, DEDUP)
    assert sigs[0].metrics is kept_metrics_before  # still None
    assert sigs[1].metrics == kept_signal_before


def test_no_metric_value_is_invented():
    sigs = _sigs("dup_metrics_partial")
    kept, _, _ = deduplicate(sigs, DEDUP)
    for k, v in (kept[0].metrics or {}).items():
        assert any((s.metrics or {}).get(k) == v for s in sigs)
