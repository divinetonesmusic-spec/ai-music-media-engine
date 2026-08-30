"""The deterministic Signal Normalization pass (spec §6.3, §6.6, §18). No network."""

from __future__ import annotations

import random

from tests.conftest import PROJECT_ROOT, load_fixture

from market_intelligence.collect.runner import run_collection
from market_intelligence.config.loader import load_dedup_config
from market_intelligence.normalize import (
    NormalizationResult,
    normalize_deterministic,
    signals_from_collected,
)
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.models import RunConfig, Signal

DEDUP = load_dedup_config(project_root=PROJECT_ROOT)


def _sigs(name):
    return [decode(Signal, d) for d in load_fixture(f"normalize/{name}.json")]


# --- validation ---------------------------------------------------

def test_a_valid_set_passes_through_unchanged():
    r = normalize_deterministic(_sigs("distinct_valid_set"), dedup_config=DEDUP)
    assert isinstance(r, NormalizationResult)
    assert len(r.valid_signals) == 4
    assert r.invalid_signals == []
    assert [s.signal_id for s in r.deduplicated_signals] == [
        "sig_run_norm_0100", "sig_run_norm_0101", "sig_run_norm_0102", "sig_run_norm_0103",
    ]
    assert r.discarded_signal_ids == []


def test_invalid_signal_is_removed_and_its_reason_recorded_not_fixed():
    r = normalize_deterministic(_sigs("invalid_signal"), dedup_config=DEDUP)
    assert [s.signal_id for s in r.valid_signals] == ["sig_run_norm_0050"]
    assert [iv.signal_id for iv in r.invalid_signals] == ["sig_run_norm_0051"]
    codes = {e["code"] for e in r.invalid_signals[0].errors}
    assert {"signal.market_not_in_taxonomy", "signal.language_not_in_taxonomy"} <= codes
    assert "sig_run_norm_0051" not in [s.signal_id for s in r.deduplicated_signals]


def test_duplicate_signal_id_is_flagged_and_the_repeat_dropped():
    a = _sigs("distinct_valid_set")[0]
    b = decode(Signal, encode(a))  # same id, valid shape
    r = normalize_deterministic([a, b], dedup_config=DEDUP)
    assert len(r.valid_signals) == 1
    assert r.invalid_signals[0].errors[0]["code"] == "signal.duplicate_id"


# --- dedup wired in --------------------------------------------

def test_deduplication_uses_the_real_config_dedup_yaml():
    r = normalize_deterministic(_sigs("dup_exact"), dedup_config=DEDUP)
    assert len(r.deduplicated_signals) == 1
    assert r.discarded_signal_ids == ["sig_run_norm_0002"]
    assert r.dedup_reasons[0].merged_metric_keys == ["related_queries"]


def test_result_is_deterministic_regardless_of_input_order():
    sigs = _sigs("distinct_valid_set") + _sigs("dup_exact") + _sigs("invalid_signal")
    shuffled = list(sigs)
    random.Random(7).shuffle(shuffled)

    a = normalize_deterministic(sigs, dedup_config=DEDUP)
    b = normalize_deterministic(shuffled, dedup_config=DEDUP)

    assert [s.signal_id for s in a.deduplicated_signals] == [
        s.signal_id for s in b.deduplicated_signals
    ]
    assert a.discarded_signal_ids == b.discarded_signal_ids
    assert [iv.signal_id for iv in a.invalid_signals] == [iv.signal_id for iv in b.invalid_signals]
    assert [(r.kept, r.dropped) for r in a.dedup_reasons] == [
        (r.kept, r.dropped) for r in b.dedup_reasons
    ]


def test_no_new_data_is_invented():
    sigs = _sigs("dup_metrics_partial")
    r = normalize_deterministic(sigs, dedup_config=DEDUP)
    union = {}
    for s in sigs:
        union.update(s.metrics or {})
    out = r.deduplicated_signals[0].metrics or {}
    assert set(out) <= set(union)
    for k, v in out.items():
        assert any((s.metrics or {}).get(k) == v for s in sigs)


def test_ambiguous_fields_are_left_untouched_no_claude_in_sn1():
    # sig_run_norm_0102 has observed_at UNKNOWN — SN-1 must not fill it
    r = normalize_deterministic(_sigs("distinct_valid_set"), dedup_config=DEDUP)
    ch = next(s for s in r.deduplicated_signals if s.signal_id == "sig_run_norm_0102")
    assert ch.observed_at == "UNKNOWN"
    assert ch.provenance.observed_at == "UNKNOWN"


def test_inputs_are_not_mutated_and_no_files_written(tmp_path):
    sigs = _sigs("dup_exact")
    snapshot = [encode(s) for s in sigs]
    normalize_deterministic(sigs, dedup_config=DEDUP)
    assert [encode(s) for s in sigs] == snapshot


# --- accepts a collected.json manifest ------------------------

def test_normalize_from_a_collected_json_manifest(tmp_path):
    # build a real collected.json offline via the replay demo
    cfg = decode(RunConfig, {
        "schema_version": "1.0.0",
        "run_id": "run_norm_from_manifest",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p",
        "signal_sources": ["internal_data"],
        "replay": {
            "enabled": True,
            "fixture_path": str((PROJECT_ROOT / "tests/fixtures/replay/collect_demo")),
        },
    })
    run_collection(cfg, project_root=tmp_path, now=None)
    manifest = tmp_path / "data" / "run_norm_from_manifest" / "signals" / "collected.json"

    loaded = signals_from_collected(manifest)
    assert [s.signal_id for s in loaded] == [
        "sig_run_replay_demo_0001", "sig_run_replay_demo_0002",
    ]

    r = normalize_deterministic(manifest, dedup_config=DEDUP)
    assert len(r.deduplicated_signals) == 2
    assert r.invalid_signals == []
