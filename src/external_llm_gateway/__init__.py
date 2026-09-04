"""External LLM Gateway — isolated, optional adapter for OmniRoute.

Decision **OMR-01** (``knowledge/DECISIONS-NEEDED.md``, status ``DECIDED`` —
implementation approved for this isolated adapter only, 2026-09-04). See
``docs/EXTERNAL-LLM-GATEWAY.md`` for the full design note.

Claude/Anthropic remains the default and only path used by the pipeline. This
package is not imported by ``market_intelligence`` or ``cluster_strategy``, and
no ``select_*_client()`` in those packages references it. The dependency runs
one way only:

    external_llm_gateway  ->  market_intelligence.llm_stage.StageClient

never the reverse. The only supported use in this milestone is explicit
instantiation from an isolated test or script — no pipeline stage uses this
package by default, and connecting one to it is a separate, future decision.
"""

from .config import OmniRouteConfig
from .omniroute_client import OmniRouteStageClient

__all__ = ["OmniRouteConfig", "OmniRouteStageClient"]
