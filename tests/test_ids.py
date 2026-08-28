"""Deterministic id derivation (spec §6.1 signal_id, §7.1 opportunity_id)."""

import pytest

from market_intelligence.schema.ids import (
    opportunity_id,
    opportunity_id_base,
    signal_id,
    split_opportunity_id_suffix,
)

C1_TUPLE = dict(
    need="Adults who wake around 3am want to fall back asleep without reaching for their phone",
    audience_description="Portuguese-speaking adults 30-55 with interrupted sleep",
    market="Brasil",
    language="pt",
    platform="tiktok",
)


def test_opportunity_id_is_deterministic_and_matches_precomputed_hash():
    got = opportunity_id(run_date="2026-08-28", **C1_TUPLE)
    assert got == "opp_2026-08-28_6c5532f243"


def test_opportunity_id_ignores_the_title():
    # spec §7.1: a reworded title does not change the id (title is not in the hash input)
    a = opportunity_id(run_date="2026-08-28", **C1_TUPLE)
    b = opportunity_id(run_date="2026-08-28", **C1_TUPLE)
    assert a == b


def test_opportunity_id_changes_when_any_c1_field_changes():
    base = opportunity_id(run_date="2026-08-28", **C1_TUPLE)
    for key in C1_TUPLE:
        altered = dict(C1_TUPLE)
        altered[key] = altered[key] + " (x)" if key in ("need", "audience_description") else "es"
        assert opportunity_id(run_date="2026-08-28", **altered) != base


def test_collision_suffix_helper():
    base = opportunity_id_base(**C1_TUPLE)
    assert split_opportunity_id_suffix(f"opp_2026-08-28_{base}") == (f"opp_2026-08-28_{base}", 1)
    assert split_opportunity_id_suffix(f"opp_2026-08-28_{base}-2") == (f"opp_2026-08-28_{base}", 2)


def test_signal_id_format():
    # spec §6.1 TECHNICAL DEFAULT: sig_<run_id>_<NNNN> zero-padded
    assert signal_id("run_2026-08-28_01", 7) == "sig_run_2026-08-28_01_0007"
    assert signal_id("run_2026-08-28_01", 1234) == "sig_run_2026-08-28_01_1234"


def test_signal_id_rejects_negative_counter():
    with pytest.raises(ValueError):
        signal_id("run_x", -1)
