# AI Music Media Engine

An intelligent content-growth system for a wellness instrumental-music business.
See [`CLAUDE.md`](CLAUDE.md) for the operational specification and
[`docs/TECHNICAL-SPEC-V1.md`](docs/TECHNICAL-SPEC-V1.md) for the V1 implementation spec.

**Current phase: V1 — Market Intelligence + Opportunity Analysis** (canonical
pipeline stages 1–2). Everything downstream (Cluster Strategy → Learning) is
future architecture and is not built yet.

## Status

Foundation layer is implemented and test-covered:

| Piece | Module |
|---|---|
| Controlled vocabularies (spec §6.2, §7.1a, §8.1, §9) | `market_intelligence.schema.enums` |
| Dataclass models for every entity (§6–§10, §12, §16, §20) | `market_intelligence.schema.models` |
| Dataclass ⇄ plain-dict codec (YAML/JSON round-trip) | `market_intelligence.schema.codec` |
| Deterministic id derivation (§6.1, §7.1) | `market_intelligence.schema.ids` |
| Validators — one rule per §13 line | `market_intelligence.schema.validate` |
| Config loading (§20) + `config/{run.example,ranking,dedup}.yaml` | `market_intelligence.config.loader` |
| Knowledge Loader (§18) — hard-fails on missing required files | `market_intelligence.knowledge_loader` |
| Preflight: `load & validate config → Knowledge Loader` (§5) | `market_intelligence.preflight` |

Signal Collection and everything after it are **not** implemented yet.

## Development setup

Python 3.12 (`requires-python = ">=3.12,<3.13"`). Only stdlib + `PyYAML` at runtime;
`pytest` + `ruff` for dev.

```bash
python3.12 -m venv .venv            # e.g. Homebrew: brew install python@3.12
./.venv/bin/python -m pip install -e ".[dev]"

./.venv/bin/python -m pytest          # run the test suite
./.venv/bin/ruff check src tests      # lint
```

### Preflight check

Loads and validates a run config, then loads the knowledge base:

```bash
./.venv/bin/python -m market_intelligence preflight config/run.example.yaml
```

## Layout

```
config/       run config template + ranking / dedup constants (data, not code)
knowledge/    human-owned source of truth — read-only to the pipeline
              (except knowledge/market/opportunity-registry.yaml, append-only)
src/market_intelligence/   the pipeline
tests/        pytest suite (TDD); tests/fixtures/ holds canonical valid entities
data/         generated, regenerable — git-ignored
reports/      generated, durable, versioned
```

## Engineering notes

- Deterministic code decides *whether output is well-formed, traceable and within
  V1 rules*; Claude decides *what is true and how strong it is* (spec §19). This
  Foundation layer is entirely deterministic.
- No database, queue or server (I10). Persistence is YAML + Markdown + JSON.
- Autonomy Level 1: the system only recommends (CLAUDE.md §13).
