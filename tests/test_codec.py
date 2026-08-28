"""Generic dataclass <-> plain-dict codec used for YAML/JSON round-trips."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

import pytest

from market_intelligence.schema.codec import CodecError, decode, encode


class Colour(str, Enum):
    RED = "red"
    BLUE = "blue"


@dataclass
class Inner:
    label: str
    weight: float = 1.0


@dataclass
class Outer:
    name: str
    colour: Colour
    inner: Inner
    tags: List[str] = field(default_factory=list)
    children: List[Inner] = field(default_factory=list)
    note: Optional[str] = None
    extra: Optional[Dict[str, object]] = None


def test_decode_builds_nested_dataclasses_and_coerces_enums():
    obj = decode(
        Outer,
        {
            "name": "x",
            "colour": "blue",
            "inner": {"label": "a"},
            "tags": ["t1", "t2"],
            "children": [{"label": "c1", "weight": 2.0}],
            "note": None,
        },
    )
    assert obj.colour is Colour.BLUE
    assert obj.inner == Inner(label="a", weight=1.0)
    assert obj.children == [Inner(label="c1", weight=2.0)]
    assert obj.note is None


def test_encode_is_the_inverse_of_decode():
    data = {
        "name": "x",
        "colour": "red",
        "inner": {"label": "a", "weight": 1.0},
        "tags": ["t"],
        "children": [],
        "note": "hi",
        "extra": {"k": 3},
    }
    assert encode(decode(Outer, data)) == data


def test_encode_omits_none_fields_and_absence_round_trips_to_none():
    obj = Outer(name="n", colour=Colour.RED, inner=Inner("a"))
    out = encode(obj)
    assert "note" not in out and "extra" not in out
    assert decode(Outer, out).note is None


def test_encode_emits_enum_values_as_raw_strings():
    out = encode(Inner(label="a"))
    assert out == {"label": "a", "weight": 1.0}
    assert encode(Outer(name="n", colour=Colour.RED, inner=Inner("a"))) ["colour"] == "red"


def test_decode_rejects_unknown_keys():
    with pytest.raises(CodecError) as ei:
        decode(Inner, {"label": "a", "bogus": 1})
    assert "bogus" in str(ei.value)


def test_decode_rejects_missing_required_field():
    with pytest.raises(CodecError) as ei:
        decode(Inner, {"weight": 2.0})
    assert "label" in str(ei.value)


def test_decode_rejects_invalid_enum_value():
    with pytest.raises(CodecError):
        decode(Outer, {"name": "x", "colour": "green", "inner": {"label": "a"}})


def test_decode_uses_defaults_when_absent():
    obj = decode(Inner, {"label": "a"})
    assert obj.weight == 1.0


@dataclass
class Aliased:
    from_: str = field(metadata={"codec_key": "from"})
    to: str = "x"


def test_codec_key_alias_round_trips_on_the_wire_name():
    obj = decode(Aliased, {"from": "a", "to": "b"})
    assert obj.from_ == "a"
    assert encode(obj) == {"from": "a", "to": "b"}
    with pytest.raises(CodecError):
        decode(Aliased, {"from_": "a"})  # python name is not the wire key
