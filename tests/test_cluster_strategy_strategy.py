"""Cluster Strategy V1 — the Claude sub-step prompt (contract §3, §11).

The prompt must feed the model the opportunity's ACTUAL lifecycle status and keep
it distinct from the Market Intelligence `target_state` recommendation, so the
model never treats the recommendation as the current state (autonomy L1, I2).
"""

from __future__ import annotations

import json

from tests.conftest import PROJECT_ROOT

from cluster_strategy.input_loader import load_input
from cluster_strategy.strategy import build_prompt
from market_intelligence.knowledge_loader import load_knowledge
from market_intelligence.schema.models import RunPaths

_SIDECAR = PROJECT_ROOT / "reports" / "run_2026-08-31_01" / "opp_2026-08-31_1bca4af972.json"
_KB = load_knowledge(RunPaths(), project_root=PROJECT_ROOT)


def _prompt() -> str:
    loaded = load_input(_SIDECAR, project_root=PROJECT_ROOT)
    return build_prompt(
        loaded.snapshot, loaded.opportunity,
        taxonomy_markdown="(taxonomy)", guardrails=_KB.guardrails,
        cluster_hint="limpeza-energetica",
    )


def test_prompt_carries_the_real_lifecycle_status_distinct_from_the_mi_recommendation():
    p = _prompt()
    # the opportunity is really in EXPLORE; MI recommends advancing to TEST
    assert '"lifecycle_status": "EXPLORE"' in p
    assert '"mi_recommended_target_state": "TEST"' in p
    # the bare, ambiguous "target_state" key is gone
    assert '"target_state":' not in p
    # and the model is told which is which
    low = p.lower()
    assert "recommendation" in low and "not" in low  # "a recommendation ... not the current state"


def test_prompt_still_forbids_transitioning_the_lifecycle():
    p = _prompt()
    assert "Do NOT transition the opportunity's lifecycle" in p


def test_opportunity_block_is_valid_json():
    p = _prompt()
    block = p.split("OPPORTUNITY:\n", 1)[1].split("\n\nEVIDENCE:", 1)[0]
    obj = json.loads(block)
    assert obj["lifecycle_status"] == "EXPLORE"
    assert obj["mi_recommended_target_state"] == "TEST"
