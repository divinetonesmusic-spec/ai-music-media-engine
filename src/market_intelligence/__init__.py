"""AI Music Media Engine — Market Intelligence V1.

Canonical pipeline stages 1–2 (CLAUDE.md §16, docs/TECHNICAL-SPEC-V1.md):

    Market Intelligence -> Opportunity Analysis -> Opportunity Report

This package implements a deterministic sequential orchestrator over a modular
pipeline of specialised components (spec §18). It is Level 1 autonomy: every
output is a recommendation; the system never executes (CLAUDE.md §13).
"""

__version__ = "0.1.0"

# Schema version stamped on every structured entity (spec §6.1, §7.1, §8.2, ...).
SCHEMA_VERSION = "1.0.0"

__all__ = ["__version__", "SCHEMA_VERSION"]
