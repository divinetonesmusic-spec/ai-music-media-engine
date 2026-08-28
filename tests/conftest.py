"""Shared fixture helpers.

``FIXTURES`` points at ``tests/fixtures/``. ``load_fixture`` reads a JSON fixture;
``PROJECT_ROOT`` is the repo root (used by Knowledge Loader tests that read the
real ``knowledge/`` tree).
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    with (FIXTURES / name).open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def valid_opportunity_dict():
    """A fresh deep copy of the canonical spec-§13-valid Opportunity fixture."""
    return copy.deepcopy(load_fixture("opportunity_valid.json"))


@pytest.fixture
def valid_signal_dicts():
    return copy.deepcopy(load_fixture("signals_valid.json"))
