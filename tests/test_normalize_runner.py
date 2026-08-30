"""Signal Normalization runner — SN-3 (spec §18 component 2, §6.7). No network."""

from __future__ import annotations

import json
import shutil

from tests.conftest import PROJECT_ROOT, load_fixture

from market_intelligence.cli import main
from market_intelligence.collect.runner import run_collection
from market_intelligence.config.loader import load_dedup_config
from market_intelligence.normalize.llm import NormalizationClient
from market_intelligence.normalize.runner import (
    NormalizationRunResult,
    normalized_path,
    run_normalization,
)
from market_intelligence.schema.codec import decode, encode
from market_intelligence.schema.models import RunConfig, Signal
from market_intelligence.schema.validate import validate_signal

DEDUP = load_dedup_config(project_root=PROJECT_ROOT)


class NoopClient(NormalizationClient):
    """Model declines to fill anything — signals keep their conservative values."""

    def __init__(self):
        self.calls: list[str] = []

    def classify(self, signal_id, *, context, ambiguous_fields, model):
        self.calls.append(signal_id)
        return {"signal_id": signal_id, "suggestions": {}, "rationale": "no adequate basis"}


def _sigs(name):
    return [decode(Signal, d) for d in load_fixture(f"normalize/{name}.json")]


def _cfg(**over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_sn3",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["web_search"],
    }
    raw.update(over)
    return decode(RunConfig, raw)


def _norm(signals, cfg, root, **kw):
    kw.setdefault("dedup_config", DEDUP)
    kw.setdefault("client", NoopClient())
    return run_normalization(signals, config=cfg, project_root=root, **kw)


def test_runner_chains_sn1_sn2_and_writes_normalized_json(tmp_path):
    cfg = _cfg()
    r = _norm(_sigs("distinct_valid_set"), cfg, tmp_path)
    assert isinstance(r, NormalizationRunResult)
    assert [s.signal_id for s in r.signals] == [
        "sig_run_norm_0100", "sig_run_norm_0101", "sig_run_norm_0102", "sig_run_norm_0103",
    ]
    out = normalized_path(cfg, tmp_path)
    assert out.is_file()
    manifest = json.loads(out.read_text())
    assert manifest["run_id"] == "run_sn3"
    assert manifest["signal_count"] == 4
    assert manifest["signal_ids"] == [s.signal_id for s in r.signals]
    assert len(manifest["signals"]) == 4
    assert manifest["llm_changes"][0]["signal_id"] == "sig_run_norm_0100"


def test_invalid_signals_are_recorded_in_the_manifest_not_dropped_silently(tmp_path):
    r = _norm(_sigs("invalid_signal"), _cfg(), tmp_path)
    manifest = json.loads(r.manifest_path.read_text())
    assert [iv["signal_id"] for iv in manifest["invalid_signals"]] == ["sig_run_norm_0051"]
    assert "sig_run_norm_0051" not in manifest["signal_ids"]


def test_dedup_decisions_are_recorded(tmp_path):
    r = _norm(_sigs("dup_exact"), _cfg(), tmp_path)
    manifest = json.loads(r.manifest_path.read_text())
    assert manifest["discarded_signal_ids"] == ["sig_run_norm_0002"]
    assert manifest["dedup_reasons"][0]["kept"] == "sig_run_norm_0001"


def test_manifest_is_byte_reproducible_for_the_same_input(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    _norm(_sigs("distinct_valid_set"), _cfg(), a)
    _norm(_sigs("distinct_valid_set"), _cfg(), b)
    assert normalized_path(_cfg(), a).read_text() == normalized_path(_cfg(), b).read_text()


def test_every_output_signal_is_valid(tmp_path):
    r = _norm(_sigs("distinct_valid_set"), _cfg(), tmp_path)
    assert all(validate_signal(s) == [] for s in r.signals)


def test_runner_accepts_a_collected_json_manifest_path(tmp_path):
    cfg = decode(RunConfig, {
        "schema_version": "1.0.0",
        "run_id": "run_sn3_from_manifest",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["internal_data"],
        "replay": {
            "enabled": True,
            "fixture_path": str(PROJECT_ROOT / "tests/fixtures/replay/collect_demo"),
        },
    })
    run_collection(cfg, project_root=tmp_path)
    collected = tmp_path / "data" / "run_sn3_from_manifest" / "signals" / "collected.json"

    r = _norm(collected, cfg, tmp_path)
    assert [s.signal_id for s in r.signals] == [
        "sig_run_replay_demo_0001", "sig_run_replay_demo_0002",
    ]
    manifest = json.loads(r.manifest_path.read_text())
    assert manifest["replay"] is True


def test_inputs_are_not_mutated(tmp_path):
    sigs = _sigs("distinct_valid_set")
    snapshot = [encode(s) for s in sigs]
    _norm(sigs, _cfg(), tmp_path)
    assert [encode(s) for s in sigs] == snapshot


def test_dedup_config_defaults_to_the_repo_config_when_project_root_has_one():
    # project_root == the real repo → config/dedup.yaml resolves; still offline.
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        cfg = _cfg(paths={"data_dir": d})
        r = run_normalization(
            _sigs("distinct_valid_set"), config=cfg, project_root=PROJECT_ROOT,
            client=NoopClient(),
        )
        assert len(r.signals) == 4


# --- the `normalize` CLI command --------------------------------

def _project_with_config(tmp_path):
    shutil.copytree(PROJECT_ROOT / "config", tmp_path / "config")
    return tmp_path


def _replay_cfg_file(tmp_path):
    cfg = {
        "schema_version": "1.0.0",
        "run_id": "run_cli_norm",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["internal_data"],
        "replay": {
            "enabled": True,
            "llm": "recorded",
            "fixture_path": str(PROJECT_ROOT / "tests/fixtures/replay/collect_demo"),
        },
    }
    path = tmp_path / "run.yaml"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_cli_normalize_success(tmp_path, capsys):
    _project_with_config(tmp_path)
    cfg_path = _replay_cfg_file(tmp_path)
    rc = main(["normalize", str(cfg_path), "--project-root", str(tmp_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "NORMALIZE OK" in out
    assert "Analysis not run" in out
    assert (tmp_path / "data" / "run_cli_norm" / "signals" / "normalized.json").is_file()


def test_cli_normalize_config_failure_returns_1(tmp_path, capsys):
    _project_with_config(tmp_path)
    (tmp_path / "bad.yaml").write_text(
        'schema_version: "1.0.0"\nrun_id: "bad id!"\nmodel: m\nprompt_version: p\n'
        'signal_sources: ["internal_data"]\n',
        encoding="utf-8",
    )
    rc = main(["normalize", str(tmp_path / "bad.yaml"), "--project-root", str(tmp_path)])
    assert rc == 1
    assert "NORMALIZE FAILED" in capsys.readouterr().out
