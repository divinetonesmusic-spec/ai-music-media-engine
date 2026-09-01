---
run_id: run_2026-09-01_02
run_date: '2026-09-01'
schema_version: 1.0.0
generated_at: '2026-09-01T14:33:17Z'
replay: false
model: claude-sonnet-5
prompt_version: mi-v1-live-01
config_snapshot:
  run_id: run_2026-09-01_02
  run_date: '2026-09-01'
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
  signals: 25
  opportunities_total: 11
  presented: 10
  parked: 1
  excluded: 0
  technical_failures: 0
  framing_candidates_dropped: 3
  asset_match_warnings: 0
timings_seconds:
  collection: 175.7948
  normalization: 26.5998
  framing: 77.099
  matching: 531.9821
  evaluation: 584.3071
  ranking: 0.0004
---

# Run digest — run_2026-09-01_02

## Presented opportunities

| rank | opportunity_id | title | market/language | target_state | overall_confidence | top dimensions | key red flags | report |
|---|---|---|---|---|---|---|---|---|
| 1 | `opp_2026-09-01_f724e341ad` | Fusión de frecuencias (432Hz+528Hz) con abundancia/prosperidade en pt | Brasil / pt | TEST | LOW | audience_potential, content_potential, asset_fit | evidence_gap/MEDIUM; market/LOW; compliance/MEDIUM | [opp_2026-09-01_f724e341ad.md](./opp_2026-09-01_f724e341ad.md) |
| 2 | `opp_2026-09-01_640ed9519d` | Alivio de ansiedad basado en tendencia de búsqueda sostenida (en) | English-speaking markets / en | EXPLORE | LOW | audience_potential, durability_opportunity_window, content_potential | evidence_gap/MEDIUM; asset_gap/MEDIUM; market/LOW | [opp_2026-09-01_640ed9519d.md](./opp_2026-09-01_640ed9519d.md) |
| 3 | `opp_2026-09-01_3fc0e61565` | Frecuencia 432Hz como categoría masiva cross-cutting en TikTok | English-speaking markets / en | TEST | LOW | audience_potential, durability_opportunity_window, content_potential | asset_gap/MEDIUM; market/MEDIUM; evidence_gap/MEDIUM | [opp_2026-09-01_3fc0e61565.md](./opp_2026-09-01_3fc0e61565.md) |
| 4 | `opp_2026-09-01_4e5f3a677c` | Escala solfeggio ampliada con propósitos narrativos específicos (es) | Mercados hispanohablantes / es | TEST | LOW | durability_opportunity_window, content_potential, asset_fit | evidence_gap/MEDIUM; market/LOW | [opp_2026-09-01_4e5f3a677c.md](./opp_2026-09-01_4e5f3a677c.md) |
| 5 | `opp_2026-09-01_97c0d0ee30` | Música de foco/estudio madura dominada por competidor flagship (en) | English-speaking markets / en | EXPLORE | LOW | audience_potential, durability_opportunity_window | asset_gap/MEDIUM; evidence_gap/MEDIUM; market/MEDIUM | [opp_2026-09-01_97c0d0ee30.md](./opp_2026-09-01_97c0d0ee30.md) |
| 6 | `opp_2026-09-01_0b5dbe1e33` | Recuperación tras crisis emocional/ruptura vía frecuencias y sonido (es) | Mercados hispanohablantes / es | TEST | LOW | audience_potential | evidence_gap/MEDIUM; asset_gap/MEDIUM | [opp_2026-09-01_0b5dbe1e33.md](./opp_2026-09-01_0b5dbe1e33.md) |
| 7 | `opp_2026-09-01_084609db5a` | Alivio de ansiedad ligado a limpieza energética/frecuencias en es | Mercados hispanohablantes / es | EXPLORE | LOW | — | evidence_gap/MEDIUM; asset_gap/MEDIUM | [opp_2026-09-01_084609db5a.md](./opp_2026-09-01_084609db5a.md) |
| 8 | `opp_2026-09-01_c6249fcde5` | Resistencia 'No AI' en comunidades de música de estudio (en) | English-speaking markets / en | EXPLORE | LOW | — | evidence_gap/MEDIUM; asset_gap/MEDIUM | [opp_2026-09-01_c6249fcde5.md](./opp_2026-09-01_c6249fcde5.md) |
| 9 | `opp_2026-09-01_cb76cacc52` | Sueño combinado con meditación y ansiedad en un solo contenido (es) | Mercados hispanohablantes / es | TEST | LOW | — | evidence_gap/MEDIUM; asset_gap/MEDIUM; market/LOW | [opp_2026-09-01_cb76cacc52.md](./opp_2026-09-01_cb76cacc52.md) |
| 10 | `opp_2026-09-01_92016b7992` | Limpieza energética esotérica/folclórica ligada a mudanza de casa (es) | Mercados hispanohablantes / es | EXPLORE | LOW | — | evidence_gap/MEDIUM; asset_gap/MEDIUM; market/LOW | [opp_2026-09-01_92016b7992.md](./opp_2026-09-01_92016b7992.md) |

## Parked opportunities

- `opp_2026-09-01_2a789f4101` — Glándula pineal + energía divina/equilíbrio em pt (status: PARK)

## Excluded opportunities

_None._

## Technical failures

> Evaluation could not complete for these opportunities (infrastructure / API error). This is NOT a business decision — they carry no status and are not in the opportunity registry. Re-run once the cause is fixed.

_None._

## NEEDS_INPUT encountered

_None recorded this run._
