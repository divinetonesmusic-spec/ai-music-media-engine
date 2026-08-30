"""Signal Collection — common infrastructure (spec §6.7, §18 component 1)."""

from __future__ import annotations

import datetime as dt
import json

import pytest

from market_intelligence.collect.base import (
    RawCapture,
    RawCaptureStore,
    SignalIdAllocator,
    raw_ref_for,
)
from market_intelligence.schema.enums import CaptureMethod, SourceType

FIXED = dt.datetime(2026, 8, 28, 14, 3, 11, tzinfo=dt.timezone.utc)


def test_signal_id_allocator_counts_from_one_and_is_zero_padded():
    alloc = SignalIdAllocator("run_2026-08-28_01")
    assert alloc.allocate() == "sig_run_2026-08-28_01_0001"
    assert alloc.allocate() == "sig_run_2026-08-28_01_0002"
    assert alloc.count == 2


def test_raw_ref_for_is_the_spec_literal_path():
    # spec §6.1 / §6.3 — always the literal "data/" prefix
    assert (
        raw_ref_for("run_2026-08-28_01", "sig_run_2026-08-28_01_0007")
        == "data/run_2026-08-28_01/signals/raw/sig_run_2026-08-28_01_0007.json"
    )


def test_raw_capture_store_writes_the_spec_6_7_shape(tmp_path):
    store = RawCaptureStore(tmp_path / "raw")
    cap = RawCapture(
        signal_id="sig_run_2026-08-28_01_0001",
        source_type=SourceType.INTERNAL_DATA,
        capture_method=CaptureMethod.INTERNAL_DATA,
        query_or_reference="data/inputs/internal.yaml [record 0]",
        captured_at="2026-08-28T14:03:11Z",
        raw_content={"observed_at": "2026-08-20", "evidence": "…"},
        url=None,
    )
    path = store.write(cap)
    assert path == tmp_path / "raw" / "sig_run_2026-08-28_01_0001.json"

    on_disk = json.loads(path.read_text())
    assert on_disk == {
        "signal_id": "sig_run_2026-08-28_01_0001",
        "source_type": "internal_data",
        "capture_method": "internal_data",
        "query_or_reference": "data/inputs/internal.yaml [record 0]",
        "url": None,
        "captured_at": "2026-08-28T14:03:11Z",
        "raw_content": {"observed_at": "2026-08-20", "evidence": "…"},
    }


def test_raw_capture_store_read_all_returns_every_capture(tmp_path):
    store = RawCaptureStore(tmp_path / "raw")
    for i in (1, 2):
        store.write(
            RawCapture(
                signal_id=f"sig_r_{i:04d}",
                source_type=SourceType.INTERNAL_DATA,
                capture_method=CaptureMethod.INTERNAL_DATA,
                query_or_reference="ref",
                captured_at="2026-08-28T14:03:11Z",
                raw_content={"n": i},
            )
        )
    got = sorted(store.read_all(), key=lambda d: d["signal_id"])
    assert [d["raw_content"]["n"] for d in got] == [1, 2]


def test_raw_capture_store_copy_from_preserves_content(tmp_path):
    src_dir = tmp_path / "fixture"
    src_dir.mkdir()
    src = src_dir / "sig_x_0001.json"
    src.write_text(json.dumps({"signal_id": "sig_x_0001", "raw_content": {"k": 1}}))

    store = RawCaptureStore(tmp_path / "run" / "raw")
    dst = store.copy_from(src)
    assert dst == tmp_path / "run" / "raw" / "sig_x_0001.json"
    assert json.loads(dst.read_text())["raw_content"] == {"k": 1}


def test_raw_capture_rejects_non_json_serialisable_content(tmp_path):
    store = RawCaptureStore(tmp_path / "raw")
    with pytest.raises(TypeError):
        store.write(
            RawCapture(
                signal_id="sig_r_0001",
                source_type=SourceType.INTERNAL_DATA,
                capture_method=CaptureMethod.INTERNAL_DATA,
                query_or_reference="ref",
                captured_at="2026-08-28T14:03:11Z",
                raw_content={"bad": {1, 2, 3}},  # a set is not JSON
            )
        )
