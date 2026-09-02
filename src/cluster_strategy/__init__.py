"""Cluster Strategy — canonical pipeline stage 3 (decision C8).

Consumes ONE owner-advanced Opportunity Report (canonical stages 1–2 output) and
produces ONE Cluster Strategy: the cluster decision + a strategic cluster
definition + a cluster-level asset strategy + a non-binding first content
direction. It stops before Page Blueprint (stage 4) and Content Strategy
(stage 5).

Contract: docs/CLUSTER-STRATEGY-V1.md (approved by the owner 2026-09-01, with
D-CS-1..D-CS-12 at their recommended answers). Autonomy Level 1 — recommend only.

Non-negotiable, carried from the V1 contract:
  * NO composite 0–100 score (C6). Qualitative rating + separate confidence.
  * NO operational LAUNCH/SCALE/KILL (I2); the opportunity lifecycle
    (EXPLORE/TEST/PARK) is carried forward, never transitioned by this stage.
  * NEVER invent an artist / playlist / page / asset (I1). Every id resolves in
    the inventory or is dropped to UNKNOWN.
  * NEVER write cluster-taxonomy.md or any knowledge/ file except (D-CS-7) an
    append to opportunity-registry.yaml.
  * A new canonical cluster is a PROPOSAL only (P6, deferred).
"""

SCHEMA_VERSION = "1.0.0"
