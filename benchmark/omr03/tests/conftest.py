"""Makes ``benchmark/omr03`` importable as ``omr03`` for this test suite only.

Isolated on purpose: this does not touch ``pyproject.toml``, ``tests/conftest.py``,
or anything under ``src/`` — the main project test suite (``pytest -q`` from the
repo root) is completely unaffected by this file.
"""
from __future__ import annotations

import sys
from pathlib import Path

_BENCHMARK_DIR = Path(__file__).resolve().parents[2]  # .../benchmark
if str(_BENCHMARK_DIR) not in sys.path:
    sys.path.insert(0, str(_BENCHMARK_DIR))
