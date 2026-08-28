"""Deterministic identifier derivation.

``opportunity_id`` (spec §7.1) is a pure function of the C1 mandatory tuple, so a
re-run that re-discovers the same opportunity produces the same id (idempotency),
and a reworded ``title`` does not. ``signal_id`` (spec §6.1) is a per-run counter.
"""

from __future__ import annotations

import hashlib
import re
from typing import Tuple

_SHORT_HASH_LEN = 10  # first 10 hex of sha1 (spec §7.1)
_SUFFIX_RE = re.compile(r"^(?P<base>opp_\d{4}-\d{2}-\d{2}_[0-9a-f]{10})(?:-(?P<n>\d+))?$")


def opportunity_id_base(
    need: str,
    audience_description: str,
    market: str,
    language: str,
    platform: str,
) -> str:
    """The 10-hex short hash of the C1 tuple (spec §7.1) — without the ``opp_<date>_`` prefix."""
    raw = "|".join([need, audience_description, market, language, platform])
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:_SHORT_HASH_LEN]


def opportunity_id(
    *,
    run_date: str,
    need: str,
    audience_description: str,
    market: str,
    language: str,
    platform: str,
) -> str:
    """``opp_<run_date>_<short_hash>`` (spec §7.1).

    A genuine hash collision between two distinct opportunities is resolved by the
    caller (Framing) appending ``-2``; see ``split_opportunity_id_suffix``.
    """
    short = opportunity_id_base(need, audience_description, market, language, platform)
    return f"opp_{run_date}_{short}"


def split_opportunity_id_suffix(opportunity_id_value: str) -> Tuple[str, int]:
    """Return ``(base_id, ordinal)``.

    ``ordinal`` is 1 for an unsuffixed id, or N for ``<base>-N`` (collision suffix).
    Raises ``ValueError`` if the value is not a well-formed opportunity id.
    """
    m = _SUFFIX_RE.match(opportunity_id_value)
    if not m:
        raise ValueError(f"not a well-formed opportunity_id: {opportunity_id_value!r}")
    return m.group("base"), int(m.group("n")) if m.group("n") else 1


def signal_id(run_id: str, counter: int) -> str:
    """``sig_<run_id>_<NNNN>`` with a zero-padded counter (spec §6.1 TECHNICAL DEFAULT)."""
    if counter < 0:
        raise ValueError(f"signal counter must be non-negative, got {counter}")
    return f"sig_{run_id}_{counter:04d}"
