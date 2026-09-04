"""Page Blueprint — canonical pipeline stage 4 (decision C8).

Consumes ONE ClusterStrategy that Cluster Strategy itself recommended for this
stage (``recommendation.target_next_stage == PAGE_BLUEPRINT``) and produces
ONE Page Blueprint: page identity, visual identity + tone of voice (grounded
in business-dna §9), the carried asset link, and a shallow page-level content
framing. It stops before Content Strategy (stage 5).

Contract: docs/PAGE-BLUEPRINT-V1.md (owner-authorized 2026-09-04, D-PB-1..4).
Autonomy Level 1 — recommend only.

Non-negotiable, carried from the V1 contract:
  * NO composite 0-100 score (C6). Qualitative confidence only, capped by the
    input ClusterStrategy's own confidence (never raised by this stage).
  * NEVER re-decide the asset (page/playlist/artist) — carried verbatim from
    ClusterStrategy.asset_strategy (I5, D-PB-3).
  * NEVER produce a content system (formats/hooks/structures/CTA copy/a
    posting calendar) — that is Content Strategy's job (stage 5, D-PB-2).
  * NEVER invent an artist / playlist / page (I1). Every id resolves in the
    inventory or is dropped to UNKNOWN.
  * NEVER write to knowledge/ — Page Blueprint has no registry or taxonomy
    write path (unlike Cluster Strategy's D-CS-7 registry append).
"""

SCHEMA_VERSION = "1.0.0"
