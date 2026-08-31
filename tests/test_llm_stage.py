"""Shared Claude-stage plumbing (spec §19, §22). No network anywhere in this file."""

from __future__ import annotations

import json
import types

import anthropic
import pytest

from market_intelligence import llm_stage as ls
from market_intelligence.llm_stage import (
    AnthropicStageClient,
    MissingFixtureError,
    RecordedStageClient,
    ResponseRejected,
    StageError,
    call_stage,
    enum_str,
    obj_schema,
    redact,
    select_stage_client,
    stage_key,
)
from market_intelligence.schema.codec import decode
from market_intelligence.schema.models import RunConfig


def _cfg(**over) -> RunConfig:
    raw = {
        "schema_version": "1.0.0",
        "run_id": "run_stage",
        "run_date": "2026-08-28",
        "model": "claude-sonnet-5",
        "prompt_version": "p1",
        "signal_sources": ["web_search"],
    }
    raw.update(over)
    return decode(RunConfig, raw)


# --- redaction ------------------------------------------------------

def test_redact_strips_anthropic_keys_from_text():
    dirty = "call failed with key sk-ant-api03-AbC123_def-XYZ and retried"
    assert "sk-ant-api03" not in redact(dirty)
    assert "sk-ant-REDACTED" in redact(dirty)


def test_redact_is_a_noop_for_clean_text():
    assert redact("nothing secret here") == "nothing secret here"


# --- RecordedStageClient ------------------------------------------

def test_recorded_client_reads_a_fixture(tmp_path):
    (tmp_path / "framing").mkdir()
    (tmp_path / "framing" / "abc.json").write_text('{"ok": true}', encoding="utf-8")
    client = RecordedStageClient(tmp_path)
    out = client.complete(stage="framing", key="abc", prompt="x", schema={}, model="m")
    assert out == {"ok": True}


def test_recorded_client_raises_missing_fixture_and_never_hits_network(tmp_path):
    client = RecordedStageClient(tmp_path)
    with pytest.raises(MissingFixtureError):
        client.complete(stage="framing", key="nope", prompt="x", schema={}, model="m")


def test_recorded_client_rejects_malformed_fixture(tmp_path):
    (tmp_path / "evaluation").mkdir()
    (tmp_path / "evaluation" / "bad.json").write_text("{not json", encoding="utf-8")
    client = RecordedStageClient(tmp_path)
    with pytest.raises(ResponseRejected):
        client.complete(stage="evaluation", key="bad", prompt="x", schema={}, model="m")


# --- select_stage_client -----------------------------------------

def test_selector_returns_recorded_client_in_replay(tmp_path):
    fixtures = tmp_path / "fx"
    (fixtures / "llm" / "framing").mkdir(parents=True)
    (fixtures / "llm" / "framing" / "k.json").write_text('{"v": 1}', encoding="utf-8")
    cfg = _cfg(replay={"enabled": True, "fixture_path": str(fixtures)})
    client, mode = select_stage_client(cfg, tmp_path)
    assert mode == "recorded"
    assert isinstance(client, RecordedStageClient)
    assert client.complete(stage="framing", key="k", prompt="", schema={}, model="m") == {"v": 1}


def test_selector_returns_live_client_when_replay_llm_is_live(tmp_path):
    cfg = _cfg(replay={"enabled": True, "fixture_path": str(tmp_path), "llm": "live"})
    client, mode = select_stage_client(cfg, tmp_path)
    assert mode == "live"
    assert isinstance(client, AnthropicStageClient)


def test_selector_returns_injected_client_untouched(tmp_path):
    sentinel = object()
    cfg = _cfg()
    client, mode = select_stage_client(cfg, tmp_path, client=sentinel)
    assert client is sentinel and mode == "live"


def test_selector_needs_a_fixture_path_in_replay(tmp_path):
    cfg = _cfg(replay={"enabled": True})
    with pytest.raises(StageError):
        select_stage_client(cfg, tmp_path)


# --- live client: no network without credentials -----------------

def test_live_client_without_credentials_raises_stage_error(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    client = AnthropicStageClient()
    with pytest.raises(StageError):
        client.complete(stage="framing", key="k", prompt="p", schema={}, model="m")


def test_live_client_uses_an_injected_sdk_client_and_redacts_errors(monkeypatch):
    class BoomError(Exception):
        pass

    class FakeMessages:
        def create(self, **kw):
            raise BoomError("bad key sk-ant-api03-SECRET here")

    class FakeSDK:
        messages = FakeMessages()

    import market_intelligence.llm_stage as mod

    class FakeAnthropicModule:
        APIError = BoomError

        class APITimeoutError(Exception):
            pass

    monkeypatch.setitem(__import__("sys").modules, "anthropic", FakeAnthropicModule())
    client = AnthropicStageClient(client=FakeSDK())
    with pytest.raises(StageError) as ei:
        client.complete(stage="framing", key="k", prompt="p", schema={}, model="m")
    assert "sk-ant-api03-SECRET" not in str(ei.value)
    assert "sk-ant-REDACTED" in str(ei.value)
    assert mod  # module import sanity


def test_live_client_parses_json_text_block(monkeypatch):
    class Block:
        type = "text"
        text = json.dumps({"answer": 42})

    class Msg:
        content = [Block()]

    class FakeMessages:
        def create(self, **kw):
            return Msg()

    class FakeSDK:
        messages = FakeMessages()

    class FakeAnthropicModule:
        class APIError(Exception):
            pass

    monkeypatch.setitem(__import__("sys").modules, "anthropic", FakeAnthropicModule())
    client = AnthropicStageClient(client=FakeSDK())
    out = client.complete(stage="framing", key="k", prompt="p", schema={}, model="m")
    assert out == {"answer": 42}


# --- helpers -----------------------------------------------------

def test_stage_key_is_filesystem_safe():
    assert stage_key("a b", "c/d", "") == "a_b__c_d"
    assert stage_key() == "default"


def test_obj_schema_is_closed():
    s = obj_schema({"a": {"type": "string"}}, ["a"])
    assert s["additionalProperties"] is False
    assert s["required"] == ["a"]


def test_enum_str_sorts_and_dedupes():
    assert enum_str(["b", "a", "a"]) == {"type": "string", "enum": ["a", "b"]}


def test_call_stage_passes_response_to_validate(tmp_path):
    (tmp_path / "framing").mkdir()
    (tmp_path / "framing" / "k.json").write_text('{"n": 3}', encoding="utf-8")
    client = RecordedStageClient(tmp_path)
    seen = {}

    def validate(raw):
        seen.update(raw)
        return "validated"

    result = call_stage(
        client, stage="framing", key="k", prompt="", schema={}, model="m", validate=validate
    )
    assert result == "validated" and seen == {"n": 3}


# --- timeout / retry policy (spec §14) -----------------------------------


class _CapturingAnthropic:
    last_kwargs: dict = {}

    def __init__(self, **kwargs):
        type(self).last_kwargs = kwargs
        self.messages = None


def test_live_client_is_built_with_a_bounded_timeout_and_retry(monkeypatch):
    monkeypatch.setattr(anthropic, "Anthropic", _CapturingAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-placeholder")
    AnthropicStageClient()._build_client()

    kw = _CapturingAnthropic.last_kwargs
    assert kw.get("max_retries") is not None and kw["max_retries"] <= 1   # SDK default is 2
    read = float(getattr(kw.get("timeout"), "read", kw.get("timeout")))
    assert 30.0 <= read <= 900.0        # explicit and bounded (SDK default retries to ~30 min)


def test_live_client_timeout_becomes_a_stage_error_without_leaking_the_key():
    req = types.SimpleNamespace(
        method="POST", url="https://api.anthropic.com/v1/messages",
        headers={"x-api-key": "sk-ant-api03-MUST-NOT-LEAK"},
    )

    class _Messages:
        def create(self, **kw):
            raise anthropic.APITimeoutError(request=req)

    class _SDK:
        messages = _Messages()

    client = AnthropicStageClient(client=_SDK())
    with pytest.raises(StageError) as ei:
        client.complete(stage="framing", key="k", prompt="p", schema={}, model="m")
    msg = str(ei.value)
    assert "framing" in msg
    assert "did not return" in msg or "timed out" in msg.lower()
    assert "sk-ant-api03-MUST-NOT-LEAK" not in msg
    assert ls._READ_TIMEOUT >= 60


# --- per-stage output budget + effort (spec §19; the live Framing failure) ---


def _block(kind: str, **kw):
    return types.SimpleNamespace(type=kind, **kw)


class _RecordingSDK:
    """Captures each messages.create call and returns a preset response."""

    def __init__(self, response):
        self._response = response
        self.calls: list = []
        outer = self

        class _Messages:
            def create(self, **kw):
                outer.calls.append(kw)
                if isinstance(outer._response, BaseException):
                    raise outer._response
                return outer._response

        self.messages = _Messages()


def _ok_msg():
    return types.SimpleNamespace(
        stop_reason="end_turn", content=[_block("text", text='{"opportunities": []}')]
    )


def _capture_output_config(stage: str) -> dict:
    sdk = _RecordingSDK(_ok_msg())
    AnthropicStageClient(client=sdk).complete(
        stage=stage, key="k", prompt="p", schema={"type": "object"}, model="claude-sonnet-5"
    )
    return sdk.calls[0]


def test_framing_call_uses_medium_effort_as_a_sibling_of_format():
    kw = _capture_output_config("framing")
    oc = kw["output_config"]
    assert oc["effort"] == "medium"               # thinking step-down from the default high
    assert "effort" not in oc["format"]           # sibling of `format`, not nested in it
    assert oc["format"]["type"] == "json_schema"  # structured output preserved


def test_framing_call_max_tokens_is_the_chosen_value():
    assert ls._STAGE_OUTPUT["framing"]["max_tokens"] == 32000
    assert _capture_output_config("framing")["max_tokens"] == 32000


@pytest.mark.parametrize("stage", ["matching", "evaluation"])
def test_other_stages_do_not_get_the_framing_override(stage):
    kw = _capture_output_config(stage)
    assert "effort" not in kw["output_config"]           # no effort override
    assert kw["max_tokens"] == ls._DEFAULT_MAX_TOKENS     # 8000 — unchanged
    assert kw["output_config"]["format"]["type"] == "json_schema"


def test_a_truncated_max_tokens_response_is_a_diagnostic_ResponseRejected():
    cut_off = '{"opportunities": [{"title": "Rotina de sono'  # JSON truncated mid-string
    truncated = types.SimpleNamespace(
        stop_reason="max_tokens",
        content=[_block("text", text=cut_off)],
    )
    client = AnthropicStageClient(client=_RecordingSDK(truncated))
    with pytest.raises(ResponseRejected) as ei:
        client.complete(stage="framing", key="k", prompt="p", schema={}, model="m")
    msg = str(ei.value)
    assert "framing" in msg
    assert "max_tokens" in msg
    assert "truncated" in msg.lower()
    assert "line 1 column 1" not in msg    # not the opaque json.loads("") message


def test_an_empty_response_names_the_stop_reason_not_json_loads_empty():
    empty = types.SimpleNamespace(stop_reason="max_tokens", content=[_block("thinking")])
    client = AnthropicStageClient(client=_RecordingSDK(empty))
    with pytest.raises(ResponseRejected) as ei:
        client.complete(stage="framing", key="k", prompt="p", schema={}, model="m")
    assert "stop_reason='max_tokens'" in str(ei.value)
    assert "thinking" in str(ei.value)


def test_a_complete_json_response_is_still_accepted():
    full = types.SimpleNamespace(
        stop_reason="end_turn",
        content=[
            _block("thinking"),  # thinking block precedes the JSON — must be skipped
            _block("text", text='{"opportunities": [{"title": "X"}]}'),
        ],
    )
    out = AnthropicStageClient(client=_RecordingSDK(full)).complete(
        stage="framing", key="k", prompt="p", schema={}, model="m"
    )
    assert out == {"opportunities": [{"title": "X"}]}


def test_a_json_array_at_top_level_is_rejected():
    arr = types.SimpleNamespace(
        stop_reason="end_turn", content=[_block("text", text="[1, 2, 3]")]
    )
    with pytest.raises(ResponseRejected):
        AnthropicStageClient(client=_RecordingSDK(arr)).complete(
            stage="framing", key="k", prompt="p", schema={}, model="m"
        )
