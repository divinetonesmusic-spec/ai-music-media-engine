"""Generic, dependency-free codec between dataclasses and plain dicts.

The pipeline persists everything as YAML / JSON / Markdown front matter (I10, spec
§17). ``decode`` turns parsed plain data into typed dataclass instances;
``encode`` does the reverse, emitting only JSON/YAML-native values (``str``,
``int``, ``float``, ``bool``, ``None``, ``list``, ``dict``).

Scope: this is a *structural* codec. It enforces field presence, field types and
enum membership. It does NOT enforce the semantic rules of spec §13 — those live
in ``validate.py`` and run against decoded instances.

Supported field annotations: primitives, ``Enum`` subclasses, nested dataclasses,
``Optional[X]``, ``List[X]``, ``Dict[str, X]``, and ``Any`` / ``object``
(pass-through). Annotations must use ``typing`` forms (``Optional[...]``), not the
``X | Y`` syntax, for Python 3.9 support.

A field whose serialised key differs from its Python name (e.g. a reserved word)
declares the wire key via ``field(metadata={"codec_key": "from"})``.
"""

from __future__ import annotations

import dataclasses
import typing
from enum import Enum
from typing import Any, Type, TypeVar, Union, get_args, get_origin, get_type_hints

T = TypeVar("T")

_NONE_TYPE = type(None)


class CodecError(ValueError):
    """Raised when plain data does not match the target dataclass shape."""


def _is_dataclass_type(tp: Any) -> bool:
    return isinstance(tp, type) and dataclasses.is_dataclass(tp)


def _is_enum_type(tp: Any) -> bool:
    return isinstance(tp, type) and issubclass(tp, Enum)


def _unwrap_optional(tp: Any):
    """Return (inner_type, is_optional) for ``Optional[X]`` / ``Union[X, None]``."""
    if get_origin(tp) is Union:
        args = [a for a in get_args(tp) if a is not _NONE_TYPE]
        is_opt = len(args) != len(get_args(tp))
        if len(args) == 1:
            return args[0], is_opt
        # Union of several non-None types: treat as pass-through, keep optionality.
        return Any, is_opt
    return tp, False


def _decode_value(tp: Any, value: Any, path: str) -> Any:
    tp, is_optional = _unwrap_optional(tp)
    if value is None:
        if is_optional:
            return None
        raise CodecError(f"{path}: got null for non-optional {tp!r}")

    if tp is Any or tp is object:
        return value

    origin = get_origin(tp)
    if origin in (list, typing.List):
        (item_tp,) = get_args(tp) or (Any,)
        if not isinstance(value, list):
            raise CodecError(f"{path}: expected a list, got {type(value).__name__}")
        return [_decode_value(item_tp, v, f"{path}[{i}]") for i, v in enumerate(value)]
    if origin in (dict, typing.Dict):
        args = get_args(tp) or (str, Any)
        val_tp = args[1]
        if not isinstance(value, dict):
            raise CodecError(f"{path}: expected a mapping, got {type(value).__name__}")
        return {k: _decode_value(val_tp, v, f"{path}.{k}") for k, v in value.items()}

    if _is_enum_type(tp):
        try:
            return tp(value)
        except ValueError:
            allowed = ", ".join(repr(m.value) for m in tp)
            raise CodecError(
                f"{path}: {value!r} is not a valid {tp.__name__} ({allowed})"
            ) from None

    if _is_dataclass_type(tp):
        return decode(tp, value, path=path)

    # Primitive. Be lenient about int/float but reject obvious mismatches.
    if tp in (str, int, float, bool):
        if tp is bool and not isinstance(value, bool):
            raise CodecError(f"{path}: expected bool, got {type(value).__name__}")
        if tp is str and not isinstance(value, str):
            raise CodecError(f"{path}: expected str, got {type(value).__name__}")
        if tp in (int, float) and (isinstance(value, bool) or not isinstance(value, (int, float))):
            raise CodecError(f"{path}: expected {tp.__name__}, got {type(value).__name__}")
    return value


def decode(cls: Type[T], data: Any, path: str = "") -> T:
    """Build an instance of dataclass ``cls`` from plain ``data``."""
    if not _is_dataclass_type(cls):
        raise CodecError(f"{path or '<root>'}: {cls!r} is not a dataclass")
    if not isinstance(data, dict):
        raise CodecError(f"{path or '<root>'}: expected a mapping for {cls.__name__}, "
                         f"got {type(data).__name__}")

    hints = get_type_hints(cls)
    fields = {f.name: f for f in dataclasses.fields(cls)}
    wire_key = {name: f.metadata.get("codec_key", name) for name, f in fields.items()}

    unknown = set(data) - set(wire_key.values())
    if unknown:
        raise CodecError(
            f"{path or cls.__name__}: unknown field(s) {sorted(unknown)} for {cls.__name__}"
        )

    kwargs = {}
    for name, f in fields.items():
        key = wire_key[name]
        fpath = f"{path}.{key}" if path else key
        if key in data:
            kwargs[name] = _decode_value(hints[name], data[key], fpath)
        elif f.default is not dataclasses.MISSING:
            kwargs[name] = f.default
        elif f.default_factory is not dataclasses.MISSING:  # type: ignore[misc]
            kwargs[name] = f.default_factory()  # type: ignore[misc]
        else:
            raise CodecError(f"{path or cls.__name__}: missing required field {name!r}")
    return cls(**kwargs)  # type: ignore[return-value]


def encode(obj: Any) -> Any:
    """Convert a dataclass instance (or container of them) to plain data."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        # Omit fields that are None: the canonical serialised form carries no null
        # keys. Absence round-trips back to None via the field's default in decode.
        out = {}
        for f in dataclasses.fields(obj):
            value = getattr(obj, f.name)
            if value is None:
                continue
            out[f.metadata.get("codec_key", f.name)] = encode(value)
        return out
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: encode(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [encode(v) for v in obj]
    return obj
