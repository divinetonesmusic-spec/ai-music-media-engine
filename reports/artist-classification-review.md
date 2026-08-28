---
title: Artist Classification Review — Suggested Pre-classification (V1)
status: suggestion_only
created: 2026-08-27
revised: 2026-08-27
revision_note: recalculated after three owner decisions (see "Owner Decisions Applied")
scope: 37 own artists
sources:
  - knowledge/inventories/artists.yaml
  - knowledge/inventories/catalog.yaml
  - knowledge/inventories/playlists.yaml
  - knowledge/inventories/classification-input.yaml
writes_to_inventories: false
---

# Artist Classification Review — Suggested Pre-classification

**This is a SUGGESTION, not a decision.** Nothing here was written to any inventory or to
`classification-input.yaml`. The owner remains the source of the strategic classification
(`primary_cluster`, `secondary_clusters`, `language`, `market`, `positioning`,
`hero_artist`).

---

## Owner Decisions Applied

Three strategic decisions from the owner were incorporated into this revised analysis:

1. **`Anjos / Espiritualidade Religiosa` is now an official business cluster.**
   It stopped being a "(proposto)" label. Artists whose only blocker was *"does this
   cluster exist?"* now receive it as a concrete `suggested_primary_cluster`, and their
   confidence was re-evaluated accordingly.

2. **English-language artists use the market `English-speaking markets`, when the evidence
   supports it.** "Evidence" = the dominant language of the track titles. Artists with
   predominantly English titles get `market: English-speaking markets`; an English *name*
   with pt/es titles does **not** trigger it (the title language wins).

3. **`Divine Tones` is the flagship / primary hero artist of the operation.**
   `suggested_hero_artist` for Divine Tones is now **`true`** (an owner decision, not an
   inference). Its brand/sound `positioning` and target `market` remain `NEEDS_INPUT`.

No other inference was promoted to a decision. Everything not supported by evidence or an
owner decision stays `NEEDS_INPUT`.

---

## Method

Each of the 37 own artists was analysed **only** from evidence present in the sources:
artist name, releases and track titles (`catalog.yaml`), distributors, and any explicit
artist↔playlist relationship.

- **Artist↔playlist relationship:** `playlists.yaml` has `owner_artists: UNKNOWN` for all 8
  playlists — **no factual artist↔playlist link exists**; none was inferred.
- **`suggested_language`** — inferred from the dominant language of the track titles.
- **`suggested_market`** — follows the owner's approved mapping: `pt → Brasil`,
  `es → Mercados hispanohablantes`, and now `en → English-speaking markets` (Decision 2).
- **`suggested_positioning`** — `NEEDS_INPUT` for all 37 (no positioning evidence in any
  source). For Divine Tones the flagship *role* is set (Decision 3) but the brand/sound
  positioning is still `NEEDS_INPUT`.
- **`suggested_hero_artist`** — `NEEDS_INPUT` for 36 artists; `true` for Divine Tones only
  (Decision 3).
- **Clusters:** official labels are those the owner has applied (playlists, pages) plus
  `Anjos / Espiritualidade Religiosa` (Decision 1). Labels marked **(a formalizar)** appear
  in CLAUDE.md §2 as examples but are not yet formalized (`Cura / Bem-estar`,
  `Ansiedade / Relaxamento`, `Foco / Estudo`).

## Confidence definition

| Level | Meaning |
|---|---|
| `HIGH` | Name and/or catalogue point clearly and consistently to one cluster; single consistent title language; market resolved. |
| `MEDIUM` | Dominant theme with real spread, or name↔catalogue tension, or language mix, or a small-but-consistent catalogue (2–3 releases), or the primary cluster is a strategic choice between two clear themes. |
| `LOW` | 1–2 releases only, or 3+ themes with no dominant one, or mixed languages, or an undefined market — evidence insufficient to suggest reliably. |

---

## Suggested classification — all 37 artists (revised)

| # | Artist | suggested_primary_cluster | suggested_secondary_clusters | suggested_language | suggested_market | suggested_positioning | suggested_hero_artist | confidence | evidence_summary |
|---|---|---|---|---|---|---|---|---|---|
| 1 | Meditação Sonora | Abundância / Prosperidade | 888 Hz; Manifestação; Limpeza Energética | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | Catálogo 100% financeiro ("Financial Expansion 888+963", "Éter Financeiro", "Kundalini da Fortuna", "Geometria da Abundância") — nome sugere meditação genérica (tensão nome×catálogo); 1 título em inglês. |
| 2 | Sinta-se Próspero | Abundância / Prosperidade | Sono Restaurador; 963 Hz; Manifestação | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome + catálogo alinhados ("Campo Magnético do Dinheiro 528", "Ordem Divina de Multiplicação", "Prosperidade do Espírito 963"); 1 faixa cruza com sono. |
| 3 | Opulentia Divina | Abundância / Prosperidade | Sono Restaurador; 888 Hz; 963 Hz | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | Nome + catálogo de prosperidade ("Sacred Money Frequency", "Linha Temporal da Prosperidade"); forte cruzamento com sono ("Prosperidade Enquanto Dorme"); mistura pt/en. |
| 4 | Sonia Amor Divino | Sono Restaurador | Limpeza Energética; Delta; Theta; 528 Hz | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | HIGH | 4/4 faixas de sono ("Sono Restaurador", "Sono Profundo Neuromodulado – Delta & Theta", "Sono Inabalável 528"); 100% pt. |
| 5 | Divine Tones | Sono Restaurador | Abundância / Prosperidade; Consciência; 963 Hz | pt (misto) | NEEDS_INPUT | Flagship da operação (decisão do proprietário); identidade sonora / ângulo de marca ainda NEEDS_INPUT | **true** *(owner decision)* | MEDIUM | **Dec. 3:** artista flagship/herói principal → hero_artist = true. Catálogo cruza sono, consciência ("963Hz Sono Elevado – Integração da Consciência") e purificação financeira; títulos pt+en; mercado do flagship ainda a definir pelo proprietário. |
| 6 | Nimbus Sleep Sanctuary | Sono Restaurador | Theta; Purificação; 528 Hz; 432 Hz | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome inglês declara "Sleep Sanctuary" + 5/5 faixas de sono, títulos 100% pt. **Dec. 2:** a evidência (idioma dos títulos) resolve o mercado como Brasil; nome inglês tratado como branding. |
| 7 | Divine Tones by Nikolai | Sono Restaurador | NEEDS_INPUT | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | LOW | Apenas 1 lançamento ("Frecuencia del Sueño Restaurador 852 Hz"); evidência insuficiente. |
| 8 | Nathaniel Lior Grace | Sono Restaurador | NEEDS_INPUT | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | LOW | Apenas 1 lançamento ("Portales del Sueño"); evidência insuficiente. |
| 9 | Templo Theta | NEEDS_INPUT (Meditação / Relaxamento?) | Sono Restaurador; Limpeza Energética; Ansiedade / Relaxamento (a formalizar); Theta | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | LOW | 5 faixas divididas em 3 temas sem dominante: limpeza de chakras (1), sono (2), aquietamento mental / "Colapso do Pensamento" (2). |
| 10 | Dormesia | Sono Restaurador | Delta; Theta; 528 Hz; Purificação | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome ~ "dormir"; 5/5 faixas de sono ("Sueño Delta Reparador", "Frecuencia de Inducción al Sueño"); 100% es. |
| 11 | Diviniia | Sono Restaurador | Ansiedade / Relaxamento (a formalizar); 528 Hz; 963 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | HIGH | Sono dominante ("Sueño Reparador y Purificación", "Señal Cerebral de Sueño") + ansiedade ("Dormir sin Ansiedad 417", "Protocolo Anti Pensamientos"); es. |
| 12 | Aura de los Sueños | Sono Restaurador | Purificação; Descanso mental | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome + 4/4 faixas de sono ("Respira y Duerme", "Dormir Bien Hoy", "Reinicio Mental Nocturno"); es. |
| 13 | Seraphim Frequencies | Anjos / Espiritualidade Religiosa | Sono Restaurador; Cura / Bem-estar (a formalizar); 528 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome = serafins; 4/4 faixas combinam "Ángeles" + "Sueño". **Dec. 1** formaliza o cluster → primário claro; es consistente. |
| 14 | Coro dos Anjos | Anjos / Espiritualidade Religiosa | Sono Restaurador; Glândula Pineal; 528 Hz | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome = "coro dos anjos"; 4/4 faixas de arcanjos/pineal + sono. **Dec. 1** formaliza o cluster; pt consistente. |
| 15 | Abundor | Abundância / Prosperidade | Sono / Sonhos; Manifestação; 528 Hz | en | English-speaking markets | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome + catálogo 100% abundância ("Money Answering You", "Manifesting While Dreaming", "Assinatura Vibracional da Fortuna"); 4/5 títulos em inglês → **Dec. 2** resolve mercado como English-speaking markets. |
| 16 | Proverbia | Anjos / Espiritualidade Religiosa | Sono Restaurador; Salmos; Anjos | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | HIGH | 4/4 faixas religiosas ("Salmos sagrados del sueño", "El Sueño del Pastor", "El sueño tranquilo de Sión", "Frecuencia de los Ángeles") + sono. **Dec. 1** formaliza o cluster (subtema mais bíblico/Salmos que anjos); es consistente. |
| 17 | Cortiq | NEEDS_INPUT — Sono Restaurador **ou** Meditação / Relaxamento | Alpha; Theta | en | English-speaking markets | NEEDS_INPUT | NEEDS_INPUT | LOW | 2 lançamentos em inglês ("Nervous Quiet – Alpha Waves for Relaxation", "Dream Harbor – Theta-Delta Waves for Sleep"). **Dec. 2** resolve mercado; primário ainda dividido entre relaxamento e sono, catálogo pequeno. |
| 18 | David's Harp Meditation | Anjos / Espiritualidade Religiosa | Sono Restaurador; Salmos | NEEDS_INPUT | NEEDS_INPUT | NEEDS_INPUT | NEEDS_INPUT | LOW | Nome = harpa de Davi (bíblico); **Dec. 1** dá o cluster. Mas só 2 lançamentos, idiomas misturados ("O Sono do Pastor 963" pt, "Frecuencia de Unidad" es) → idioma/mercado seguem NEEDS_INPUT. |
| 19 | Salmo Sonoro | Anjos / Espiritualidade Religiosa | Sono Restaurador; Salmos; 963 Hz | NEEDS_INPUT | NEEDS_INPUT | NEEDS_INPUT | NEEDS_INPUT | LOW | Nome = "Salmo Sonoro"; **Dec. 1** dá o cluster. 2 lançamentos, idiomas misturados ("O Sono do Pastor" pt, "Resonancia de Dios" es). |
| 20 | Brainhertz | Anjos / Espiritualidade Religiosa *(sugerido)* | Sono Restaurador; Frequência Divina; 963 Hz | es (misto) | NEEDS_INPUT | NEEDS_INPUT | NEEDS_INPUT | LOW | Nome techy neutro; faixas "O Sono do Pastor" (bíblico) + "La Frecuencia de lo Divino" inclinam para religioso — **Dec. 1** permite sugerir o cluster, mas 3 lançamentos, idiomas misturados → confiança baixa. |
| 21 | Synaptica | Sono Restaurador | Delta; 528 Hz; 963 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | 2 faixas, ambas de sono ("Sueño Delta Reparador 528", "Vibración de Sueño Profundo 963"); es consistente; catálogo pequeno limita a MEDIUM. |
| 22 | Hypnozzert | NEEDS_INPUT — Sono Restaurador | Cura / Perdão; 528 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | LOW | 2 lançamentos com temas distintos ("Frecuencia del Sueño Restaurador 528" vs "Frecuencia del Perdón"); catálogo pequeno e disperso. |
| 23 | Hipnocortex | Sono Restaurador | Chakras / Espiritualidade; Metafísico; 432 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | 2 faixas, ambas sono-primário ("Sueño y Activación de Chakras", "Sueño metafísico reparador 432"); es; catálogo pequeno. |
| 24 | Thetara | Sono Restaurador | Kundalini / Espiritualidade; Metafísico; Frequência Divina; 963 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | 4/5 faixas de sono ("Sueño Curativo 528+963", "Sueño Regenerativo", "Sueño Metafísico Restaurador"); 1 outlier de kundalini; es. |
| 25 | Arcturian Healing Codes | NEEDS_INPUT — Sono Restaurador **ou** Cura / Bem-estar (a formalizar) | Espiritualidade / Starseed; Abundância; 528 Hz; 963 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | Nome enfatiza "Healing"; faixas cruzam sono + "Sanación"/"Curación interna" + 1 de abundância (pt "Magnetismo da Abundância") + espiritualidade arcturiana (starseed, não religiosa → Dec. 1 não se aplica). Sono vs. cura como primário. |
| 26 | Hertzia | NEEDS_INPUT — Limpeza Energética **ou** Sono Restaurador | Purificação; 528 Hz; 741 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | Divisão par: purificação/limpeza ("Purificación Total 741", "Espíritu Purificado", "Limpieza del Subconsciente") 2 faixas × sono 2 faixas; sem primário claro. |
| 27 | Sonoriium | Sono Restaurador | Delta; Theta; 528 Hz; 963 Hz; Manifestação | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | HIGH | 5/5 faixas de sono ("Sueño Delta Reparador", "Cura del Sueño 432", "Pulso de Sueño Theta"); es consistente. |
| 28 | Frequenzia | Sono Restaurador | Limpeza Espiritual; Anti-insônia; Theta | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | 3 faixas: limpeza espiritual (1), anti-insônia (1), sono theta (1); sono/insônia = 2/3; es. |
| 29 | Binauric | Sono Restaurador | Chakras / Espiritualidade; Purificação; Anti-insônia; 528 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | HIGH | 5/5 faixas de sono ("Código Theta del Sueño", "Señal Theta Anti Insomnio", "Sueño Sagrado y Purificación"); es. |
| 30 | Meditara | Sono Restaurador | Ansiedade / Estresse (a formalizar); Anti-insônia; Frequência Divina; REM | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | 5/5 faixas de sono ("Protocolo Sueño Reparador", "Anti Insomnio 1111", "Sueño sin Estrés Mental", "Sueño REM"); nome sugere meditação — tensão nome×catálogo. |
| 31 | Prospperus | Abundância / Prosperidade | Sono Restaurador; Limpeza Energética; Sonho Lúcido; 777 Hz; 888 Hz | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome + 5/5 faixas de prosperidade ("Sucesso Material 777", "Limpeza Energética do Campo Financeiro 888", "Noite Próspera", "Sonho Lúcido da Prosperidade"); pt. |
| 32 | The Seven Archangels | Anjos / Espiritualidade Religiosa | Sono Restaurador; Prosperidade; Purificação; 528 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | HIGH | Nome = os sete arcanjos; 4/4 faixas combinam arcanjos + sono. **Dec. 1** formaliza o cluster. Títulos 100% es → mercado hispanohablante (nome inglês = branding, não sinal de mercado; **Dec. 2** não se aplica). |
| 33 | Raphael's Healing Choir | Anjos / Espiritualidade Religiosa | Sono Restaurador; Cura / Bem-estar (a formalizar); Purificação / Limpeza; 528 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | MEDIUM | Nome = Rafael (arcanjo da cura) + faixa "de los Ángeles"; **Dec. 1** dá âncora de primário. Ainda há dispersão (cura, purificação, sono) → MEDIUM. |
| 34 | Brainora | NEEDS_INPUT — multi-cluster | Sono Restaurador; Foco / Estudo (a formalizar); Ansiedade / Relaxamento (a formalizar); Ondas cerebrais | en | English-speaking markets | NEEDS_INPUT | NEEDS_INPUT | LOW | 4 faixas em inglês em 3 clusters funcionais: sono profundo (2), equilíbrio emocional (1), foco/concentração ("Focus Spine – Alpha-Beta Waves for Concentration") (1). **Dec. 2** resolve mercado; primário segue indefinido. |
| 35 | Psalms Frequencies | Anjos / Espiritualidade Religiosa | Sono Restaurador; Anjos / Celestial; 528 Hz | NEEDS_INPUT | NEEDS_INPUT | NEEDS_INPUT | NEEDS_INPUT | LOW | Nome = salmos; **Dec. 1** dá o cluster ("Acalanto de Sião", "Arpa del Sueño Celestial"). 3 lançamentos, idiomas misturados (1 pt, 2 es) → idioma/mercado NEEDS_INPUT; nome inglês não sustentado por evidência de títulos (**Dec. 2** não se aplica). |
| 36 | Silenciium | Sono Restaurador | Frequência Divina; 852 Hz | es | Mercados hispanohablantes | NEEDS_INPUT | NEEDS_INPUT | LOW | Apenas 1 lançamento ("Frecuencia del Sueño Divino 852 Hz"); evidência insuficiente. |
| 37 | Vibração Consciente | Frequência Divina / Espiritualidade | Consciência; 963 Hz | pt | Brasil | NEEDS_INPUT | NEEDS_INPUT | LOW | Apenas 1 lançamento ("Frequência Suprema da Consciência 963 Hz"); evidência insuficiente. |

---

## Confidence distribution (revised)

| Confidence | Count (was) | Artists |
|---|---|---|
| `HIGH` | **14** (was 8) | Sinta-se Próspero; Sonia Amor Divino; Nimbus Sleep Sanctuary; Dormesia; Diviniia; Aura de los Sueños; Seraphim Frequencies; Coro dos Anjos; Abundor; Proverbia; Sonoriium; Binauric; Prospperus; The Seven Archangels |
| `MEDIUM` | **11** (was 16) | Meditação Sonora; Opulentia Divina; Divine Tones; Synaptica; Hipnocortex; Thetara; Arcturian Healing Codes; Hertzia; Frequenzia; Meditara; Raphael's Healing Choir |
| `LOW` | **12** (was 13) | Divine Tones by Nikolai; Nathaniel Lior Grace; Templo Theta; Cortiq; David's Harp Meditation; Salmo Sonoro; Brainhertz; Hypnozzert; Brainora; Psalms Frequencies; Silenciium; Vibração Consciente |

The three decisions moved **7 confidence levels up**: 6 into `HIGH` (Nimbus, Seraphim
Frequencies, Coro dos Anjos, Abundor, Proverbia, The Seven Archangels) and 1 from `LOW`
into `MEDIUM` (Raphael's Healing Choir).

---

## Artists that still require a human decision

### A. Evidence insufficient — cannot be suggested reliably (the 12 `LOW`)

- **1 release only:** Divine Tones by Nikolai · Nathaniel Lior Grace · Silenciium · Vibração Consciente.
- **3+ themes, no dominant cluster:** Templo Theta · Brainora.
- **Small catalogue + theme spread:** Cortiq · Hypnozzert.
- **Religious cluster now assigned, but language/market unresolved (mixed pt/es, small catalogue):** David's Harp Meditation · Salmo Sonoro · Brainhertz · Psalms Frequencies.

### B. Primary cluster is a choice between two clear themes (the owner picks)

- **Hertzia** — `Limpeza Energética` vs `Sono Restaurador` (even 2×2 split).
- **Arcturian Healing Codes** — `Sono Restaurador` vs `Cura / Bem-estar` (a formalizar).
- **Raphael's Healing Choir** — `Anjos / Espiritualidade Religiosa` anchored, but healing/purification/sleep spread remains.

### C. Name ↔ catalogue tension (confirm the intended cluster)

- **Meditação Sonora** — name = "sound meditation", catalogue = 100% abundance.
- **Meditara** — name = meditation, catalogue = 100% sleep.
- **Templo Theta** — name = Theta/meditation, catalogue = sleep + cleansing + mind-quieting.

### D. Still open after the three decisions

- **Roster consolidation vs differentiation:** ~20 artists share the `Sono Restaurador`
  primary. The owner needs to decide which artists *lead* a sub-cluster and which are
  interchangeable, and whether some `es` sleep artists with 1–2 releases (Divine Tones by
  Nikolai, Nathaniel Lior Grace, Synaptica, Hypnozzert, Hipnocortex) should be consolidated.
- **`Divine Tones` (flagship):** `hero_artist = true` is set; `positioning` (sound identity,
  brand angle) and target `market` still `NEEDS_INPUT`.
- **`English-speaking markets` label:** confirm the wording and whether country granularity
  is needed (Abundor, Brainora, Cortiq).
- **`(a formalizar)` clusters:** `Cura / Bem-estar`, `Ansiedade / Relaxamento`,
  `Foco / Estudo` — appear in CLAUDE.md §2 examples and in several artists' secondary
  clusters; not yet formal.
- **`positioning` for all 37** and **`hero_artist` for the other 36** remain `NEEDS_INPUT`.

---

## Not decided here (by design)

- Nothing was written to `knowledge/inventories/*` or to
  `knowledge/inventories/classification-input.yaml`. The owner applies decisions there.
- All values above are **suggestions** derived from catalogue/name evidence plus the three
  owner decisions — not classifications.
