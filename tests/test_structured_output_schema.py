"""Every JSON Schema the pipeline sends in ``output_config.format`` must stay
inside the subset the Anthropic structured-outputs validator accepts.

Two subset rules have each produced a live 400 (docs verified 2026-08-30,
platform.claude.com/docs/en/build-with-claude/structured-outputs):

1. ``"type"`` is a single string, never a union array. ``["string", "null"]``
   is rejected — the validator stringifies the array and fails every enum value
   against it (``Enum value 'EPHEMERAL' does not match declared type
   '['string', 'null']'``). Nullable = ``anyOf`` + an explicit ``{"type":
   "null"}`` branch.
2. Every object must set ``additionalProperties: false``. An open / dynamic-key
   map cannot be expressed (``additionalProperties`` other than ``false`` is
   unsupported, ``patternProperties`` is not supported) — encode it as an array
   of ``{key, value}`` pairs. ``messages.create`` sends the schema verbatim;
   only ``messages.parse`` transforms it.

No network and no real key: the live clients are exercised with a fake SDK
client that only captures the ``output_config`` it is handed.
"""

from __future__ import annotations

import json
import types

import pytest

from market_intelligence.collect.web_search import AnthropicWebSearch, _findings_schema
from market_intelligence.evaluation import _response_schema as evaluation_response_schema
from market_intelligence.framing import _response_schema as framing_response_schema
from market_intelligence.llm_stage import AnthropicStageClient
from market_intelligence.matching import _response_schema as matching_response_schema
from market_intelligence.normalize.llm import AnthropicNormalization
from market_intelligence.normalize.llm import _response_schema as normalization_response_schema
from market_intelligence.schema.enums import Durability

CANONICAL_DURABILITIES = {"EPHEMERAL", "EMERGING", "STRUCTURAL", "EVERGREEN"}


# --- the subset rules that have each caused a live 400 --------------------


def assert_within_anthropic_subset(schema: object, *, path: str = "$") -> None:
    """Fail if any node uses a construct ``output_config.format`` rejects."""
    assert isinstance(schema, dict), f"{path}: schema node is not an object"

    declared_type = schema.get("type")
    assert not isinstance(declared_type, list), (
        f"{path}: `type` is the union array {declared_type!r} — the json_schema "
        f"validator rejects this (\"Enum value '…' does not match declared type\"). "
        f'Use anyOf + {{"type": "null"}}.'
    )
    if declared_type == "object":
        assert schema.get("additionalProperties") is False, (
            f"{path}: object without `additionalProperties: false` — the subset "
            f"requires it on every object and has no open-map form."
        )

    for name, sub in (schema.get("properties") or {}).items():
        assert_within_anthropic_subset(sub, path=f"{path}.{name}")
    if isinstance(schema.get("items"), dict):
        assert_within_anthropic_subset(schema["items"], path=f"{path}[]")
    for keyword in ("anyOf", "allOf", "oneOf"):
        for i, sub in enumerate(schema.get(keyword, [])):
            assert_within_anthropic_subset(sub, path=f"{path}/{keyword}[{i}]")


def schema_accepts(schema: dict, instance: object) -> bool:
    """A tiny instance checker for the keywords these schemas actually use."""
    if "anyOf" in schema:
        return any(schema_accepts(branch, instance) for branch in schema["anyOf"])
    if "enum" in schema:
        return instance in schema["enum"]
    declared_type = schema.get("type")
    if declared_type == "null":
        return instance is None
    if declared_type == "string":
        return isinstance(instance, str)
    if declared_type == "object":
        if not isinstance(instance, dict):
            return False
        if any(req not in instance for req in schema.get("required", [])):
            return False
        props = schema.get("properties", {})
        return all(k not in props or schema_accepts(props[k], v) for k, v in instance.items())
    if declared_type == "array":
        return isinstance(instance, list) and all(
            schema_accepts(schema.get("items", {}), item) for item in instance
        )
    return True


def _optional_field_paths(schema: object, path: str = "$") -> list:
    """Every property declared but NOT listed in its object's ``required``.

    An optional field roughly doubles the constrained-decoding grammar's state
    space; 15 optional fields (~2^15) is what blew Evaluation's compiled grammar
    past the API limit ("The compiled grammar is too large", HTTP 400).
    """
    out: list = []
    if not isinstance(schema, dict):
        return out
    if schema.get("type") == "object":
        required = set(schema.get("required") or [])
        for name, sub in (schema.get("properties") or {}).items():
            if name not in required:
                out.append(f"{path}.{name}")
            out += _optional_field_paths(sub, f"{path}.{name}")
    if isinstance(schema.get("items"), dict):
        out += _optional_field_paths(schema["items"], f"{path}[]")
    for keyword in ("anyOf", "allOf", "oneOf"):
        for i, sub in enumerate(schema.get(keyword, [])):
            out += _optional_field_paths(sub, f"{path}/{keyword}[{i}]")
    return out


def _finding_props() -> dict:
    return _findings_schema()["properties"]["findings"]["items"]["properties"]


def _enum_branch(nullable_schema: dict) -> list:
    for branch in nullable_schema["anyOf"]:
        if "enum" in branch:
            return branch["enum"]
    raise AssertionError(f"no enum branch in {nullable_schema!r}")


# --- fake SDK client -------------------------------------------------------


def _fake_sdk(capture: dict, *, text: str):
    def create(**kwargs):
        capture.update(kwargs)
        block = types.SimpleNamespace(type="text", text=text)
        return types.SimpleNamespace(content=[block], stop_reason="end_turn")

    return types.SimpleNamespace(messages=types.SimpleNamespace(create=create))


ALL_STAGE_SCHEMAS = {
    "web_search.findings": _findings_schema(),
    "normalization.suggestions": normalization_response_schema(),
    "framing": framing_response_schema(),
    "matching": matching_response_schema(["pl_demo", "ar_demo"]),
    "evaluation": evaluation_response_schema(),
}


# --- the regression --------------------------------------------------------


@pytest.mark.parametrize("name", sorted(ALL_STAGE_SCHEMAS))
def test_every_stage_schema_is_within_the_anthropic_subset(name):
    assert_within_anthropic_subset(ALL_STAGE_SCHEMAS[name])


@pytest.mark.parametrize("name", sorted(ALL_STAGE_SCHEMAS))
def test_every_stage_schema_serialises_for_the_sdk(name):
    dumped = json.dumps(ALL_STAGE_SCHEMAS[name])
    assert json.loads(dumped) == ALL_STAGE_SCHEMAS[name]


# --- evaluation: the schema must compile to a bounded grammar (7th live bug) --
#
# The first full live run failed Evaluation with HTTP 400 "The compiled grammar
# is too large". Root cause: 15 OPTIONAL ``blocked_by`` fields (10 dimensions +
# 5 Business Outcome axes). The fix makes every field required — an empty
# ``blocked_by: []`` is the "no blocker" signal — and drops ``blocked_by`` from
# the axes entirely (``_axis`` never read it). No dimension / axis / rating /
# confidence / red_flag / recommendation semantics change.


def test_evaluation_schema_has_no_optional_fields():
    assert _optional_field_paths(evaluation_response_schema()) == []


def test_evaluation_dimension_rating_requires_blocked_by_as_an_array():
    dims = evaluation_response_schema()["properties"]["dimensions"]["properties"]
    assert set(dims) and len(dims) == 10
    for key, rated in dims.items():
        assert "blocked_by" in rated["required"], key
        assert rated["properties"]["blocked_by"] == {
            "type": "array", "items": {"type": "string"}
        }, key
    # an empty list is a valid "no blocker" value the model can emit
    assert schema_accepts(dims["signal_strength"]["properties"]["blocked_by"], [])
    assert schema_accepts(dims["signal_strength"]["properties"]["blocked_by"], ["x"])


def test_evaluation_bop_axis_drops_the_dead_blocked_by_field():
    axes = evaluation_response_schema()["properties"]["business_outcome_profile"]["properties"]
    assert set(axes) and len(axes) == 5
    for key, rated in axes.items():
        assert "blocked_by" not in rated["properties"], key
        assert set(rated["required"]) == {"rating", "confidence", "justification"}, key


def test_evaluation_still_covers_10_dims_5_axes_red_flags_and_recommendation():
    schema = evaluation_response_schema()["properties"]
    assert len(schema["dimensions"]["properties"]) == 10
    assert len(schema["business_outcome_profile"]["properties"]) == 5
    assert schema["red_flags"]["type"] == "array"
    rec = schema["recommendation"]["properties"]
    assert set(rec) == {"target_state", "suggested_next_step", "justification", "confidence"}
    # rating and confidence stay separate keys on every rated node
    a_dim = evaluation_response_schema()["properties"]["dimensions"]["properties"]["music_fit"]
    assert "rating" in a_dim["properties"] and "confidence" in a_dim["properties"]


# --- framing: audience.attributes is a closed pair list, not an open map --


def _framing_audience_props() -> dict:
    items = framing_response_schema()["properties"]["opportunities"]["items"]
    return items["properties"]["audience"]


def test_framing_audience_attributes_is_a_closed_key_value_pair_list():
    audience = _framing_audience_props()
    attributes = audience["properties"]["attributes"]

    assert attributes["type"] == "array"
    item = attributes["items"]
    assert item["type"] == "object"
    assert item["additionalProperties"] is False
    assert set(item["required"]) == {"key", "value"}
    assert item["properties"]["key"] == {"type": "string"}
    assert item["properties"]["value"] == {"type": "string"}

    # attributes stays optional — audience.required is description only
    assert audience["required"] == ["description"]


def test_framing_call_sends_a_subset_valid_schema():
    from market_intelligence import framing as framing_mod

    capture: dict = {}
    sdk = _fake_sdk(capture, text='{"opportunities": []}')
    AnthropicStageClient(client=sdk).complete(
        stage=framing_mod.STAGE,
        key="k",
        prompt="p",
        schema=framing_mod._response_schema(),
        model="claude-sonnet-5",
    )
    schema = capture["output_config"]["format"]["schema"]
    assert_within_anthropic_subset(schema)
    json.dumps(schema)


# --- web_search: durability_hint + the nullable strings -------------------


def test_web_search_durability_hint_keeps_the_canonical_enum_and_allows_null():
    durability_hint = _finding_props()["durability_hint"]
    assert not isinstance(durability_hint.get("type"), list)

    enum_values = _enum_branch(durability_hint)
    assert set(enum_values) == CANONICAL_DURABILITIES
    assert "EPHEMERAL" in enum_values

    assert schema_accepts(durability_hint, "EPHEMERAL")
    assert schema_accepts(durability_hint, "EVERGREEN")
    assert schema_accepts(durability_hint, None)
    assert not schema_accepts(durability_hint, "PERMANENT")
    assert not schema_accepts(durability_hint, "ephemeral")


def test_web_search_nullable_string_fields_accept_a_string_or_null():
    props = _finding_props()
    for field in ("result_page_age", "raw_excerpt"):
        assert not isinstance(props[field].get("type"), list), field
        assert schema_accepts(props[field], "September 1, 2026")
        assert schema_accepts(props[field], None)


# --- normalization: same durability_hint fix -----------------------------


def test_normalization_durability_hint_is_a_nullable_canonical_enum():
    suggestions = normalization_response_schema()["properties"]["suggestions"]
    durability_hint = suggestions["properties"]["durability_hint"]
    assert not isinstance(durability_hint.get("type"), list)

    assert set(_enum_branch(durability_hint)) == CANONICAL_DURABILITIES
    assert schema_accepts(durability_hint, "STRUCTURAL")
    assert schema_accepts(durability_hint, None)
    assert not schema_accepts(durability_hint, "forever")

    # durability_hint stays optional — it is not in suggestions.required
    assert "durability_hint" not in suggestions.get("required", [])


def test_durability_enum_matches_the_canonical_vocabulary():
    assert {d.value for d in Durability} == CANONICAL_DURABILITIES


# --- the schema actually handed to the SDK on a live call ---------------


def test_web_search_structuring_call_sends_a_subset_valid_schema():
    capture: dict = {}
    client = _fake_sdk(capture, text='{"findings": []}')
    AnthropicWebSearch(client=client)._structure(
        client, model="claude-sonnet-5", brief="b", analysis="a", results=[], queries=[]
    )
    schema = capture["output_config"]["format"]["schema"]
    assert_within_anthropic_subset(schema)
    json.dumps(schema)


def test_normalization_call_sends_a_subset_valid_schema():
    capture: dict = {}
    client = _fake_sdk(capture, text='{"signal_id": "sig_1", "suggestions": {}, "rationale": "x"}')
    AnthropicNormalization(client=client).classify(
        "sig_1", context={}, ambiguous_fields=["durability_hint"], model="claude-sonnet-5"
    )
    schema = capture["output_config"]["format"]["schema"]
    assert_within_anthropic_subset(schema)
    json.dumps(schema)
