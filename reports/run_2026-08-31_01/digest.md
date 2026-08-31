---
run_id: run_2026-08-31_01
run_date: '2026-08-31'
schema_version: 1.0.0
generated_at: '2026-08-31T18:30:08Z'
replay: false
model: claude-sonnet-5
prompt_version: mi-v1-live-01
config_snapshot:
  run_id: run_2026-08-31_01
  run_date: '2026-08-31'
  model: claude-sonnet-5
  extraction_model: null
  prompt_version: mi-v1-live-01
  schema_version: 1.0.0
  signal_sources:
  - web_search
  scope:
    clusters: []
    markets: []
    languages:
    - pt
    - es
    - en
    discovery_platforms:
    - tiktok
    - youtube
    queries: []
    notes: 'C10 validation run — a full live V1 pipeline pass for an AI-assisted instrumental
      wellness-music business (Spotify playlists + short-form social). This is one
      of three consecutive runs used to validate the V1 Definition of Done (spec §21).
      Search the web for CURRENT, externally observable signals of audience demand,
      behaviour or growth in relaxing / wellness instrumental music across pt / es
      / en. Cover the themes the business already works with — sleep, anxiety / stress
      relief, focus and study, meditation and daytime relaxation, abundance / prosperity,
      energetic cleansing, angelic / religious spirituality, non-confessional spirituality,
      pineal-gland / frequency content, lucid dreaming, healing / well-being — and,
      just as importantly, look for anything genuinely emerging that is adjacent but
      NOT already one of those: new sub-themes, listening rituals, occasions (commute,
      postpartum, exam season, grief, shift work), formats, frequency trends, creator
      behaviours, and demand in markets or languages we may be under-serving. Report
      only what a specific search result actually shows — never the model''s own background
      knowledge. When a market or language is clearly observable, use the V1 taxonomy
      (pt/Brasil, es/Mercados hispanohablantes, en/English-speaking markets); a theme
      outside the 11 canonical clusters is a HYPOTHESIS only.

      '
  max_opportunities_presented: 10
  max_candidates: 15
  min_opportunities_target: 5
  dry_run: false
  replay:
    enabled: false
    llm: null
    fixture_path: null
sources_used:
- web_search
sources_failed: []
counts:
  signals: 21
  opportunities_total: 10
  presented: 6
  parked: 0
  excluded: 4
  technical_failures: 0
  framing_candidates_dropped: 0
  asset_match_warnings: 0
timings_seconds:
  collection: 134.721
  normalization: 20.9597
  framing: 73.0001
  matching: 487.863
  evaluation: 623.2308
  ranking: 0.0003
---

# Run digest — run_2026-08-31_01

## Presented opportunities

| rank | opportunity_id | title | market/language | target_state | overall_confidence | top dimensions | key red flags | report |
|---|---|---|---|---|---|---|---|---|
| 1 | `opp_2026-08-31_3c6c875d54` | Sleep instrumental music for Brazilian TikTok audiences | Brasil / pt | TEST | LOW | audience_potential, durability_opportunity_window, asset_fit | evidence_gap/MEDIUM | [opp_2026-08-31_3c6c875d54.md](./opp_2026-08-31_3c6c875d54.md) |
| 2 | `opp_2026-08-31_8150d850ed` | Sleep instrumental music for Spanish-speaking TikTok audiences | Mercados hispanohablantes / es | TEST | LOW | audience_potential, durability_opportunity_window, content_potential | evidence_gap/MEDIUM; asset_gap/MEDIUM; compliance/MEDIUM | [opp_2026-08-31_8150d850ed.md](./opp_2026-08-31_8150d850ed.md) |
| 3 | `opp_2026-08-31_6ab2bc7937` | Study and focus instrumental music for English-speaking TikTok students | English-speaking markets / en | TEST | LOW | durability_opportunity_window, content_potential | asset_gap/MEDIUM; evidence_gap/MEDIUM; market/LOW | [opp_2026-08-31_6ab2bc7937.md](./opp_2026-08-31_6ab2bc7937.md) |
| 4 | `opp_2026-08-31_96b1fb16fa` | Angel numbers and dream-linked spirituality content (EN TikTok) | English-speaking markets / en | EXPLORE | LOW | content_potential | evidence_gap/MEDIUM; asset_gap/MEDIUM; compliance/LOW | [opp_2026-08-31_96b1fb16fa.md](./opp_2026-08-31_96b1fb16fa.md) |
| 5 | `opp_2026-08-31_1bca4af972` | Energetic cleansing music for new-home rituals (ES market) | Mercados hispanohablantes / es | TEST | LOW | — | compliance/MEDIUM; evidence_gap/MEDIUM; asset_gap/LOW | [opp_2026-08-31_1bca4af972.md](./opp_2026-08-31_1bca4af972.md) |
| 6 | `opp_2026-08-31_fa76ab96e5` | Broader dream-content wave (DreamTok) beyond lucid dreaming for EN TikTok | English-speaking markets / en | EXPLORE | LOW | — | evidence_gap/MEDIUM; asset_gap/MEDIUM; compliance/MEDIUM | [opp_2026-08-31_fa76ab96e5.md](./opp_2026-08-31_fa76ab96e5.md) |

## Parked opportunities

_None._

## Excluded opportunities

- `opp_2026-08-31_5c5bd96e59` — TikTok-to-Spotify wellness music discovery funnel in Brazil — reason: HIGH-severity compliance red flag (spec §11.1)
- `opp_2026-08-31_86df487210` — Abundance frequency manifestation music trend (EN TikTok) — reason: HIGH-severity compliance red flag (spec §11.1)
- `opp_2026-08-31_a535b67932` — Daytime relaxation background music for Brazilian YouTube listeners — reason: HIGH-severity compliance red flag (spec §11.1)
- `opp_2026-08-31_d393a1d119` — Sleep instrumental music for English-speaking TikTok night listeners — reason: HIGH-severity compliance red flag (spec §11.1)

## Technical failures

> Evaluation could not complete for these opportunities (infrastructure / API error). This is NOT a business decision — they carry no status and are not in the opportunity registry. Re-run once the cause is fixed.

_None._

## NEEDS_INPUT encountered

_None recorded this run._
