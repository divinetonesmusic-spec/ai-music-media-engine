"""Connection configuration for the OmniRoute adapter (decision OMR-01).

Kept deliberately separate from ``market_intelligence.schema.models.RunConfig`` /
``ReplayConfig`` — OMR-01 (``knowledge/DECISIONS-NEEDED.md``) is explicit that
those must not be touched. This dataclass is only meaningful to
``external_llm_gateway.omniroute_client.OmniRouteStageClient``; nothing in
``market_intelligence`` or ``cluster_strategy`` reads it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class OmniRouteConfig:
    """Where and how to reach an OmniRoute OpenAI-compatible gateway.

    The API key is never stored on this object, never hardcoded and never read
    from OmniRoute's own local credential store (``~/.omniroute/storage.sqlite``)
    — only the *name* of the environment variable to read it from, resolved at
    call time by :meth:`resolve_api_key`.
    """

    base_url: str = "http://localhost:20128/v1"
    model: str = ""
    api_key_env_var: str = "OMNIROUTE_API_KEY"
    connect_timeout: float = 10.0
    read_timeout: float = 60.0

    def resolve_api_key(self) -> Optional[str]:
        """The API key from the environment, or ``None``.

        A missing key is not an error — a local OmniRoute instance may run with
        ``REQUIRE_API_KEY=false`` (the default for a loopback-bound instance);
        the request is then simply sent unauthenticated.
        """
        return os.environ.get(self.api_key_env_var) or None
