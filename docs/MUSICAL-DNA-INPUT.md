---
title: Musical DNA — Owner Input Worksheet (COMPLETED)
status: OWNER-APPROVED
created: 2026-09-03
completed: 2026-09-03
owner: Nicolas Alves (divinetonesmusic@gmail.com)
purpose: >
  The worksheet used to define the house sound ("Musical DNA"). Originally a question
  set; now a completed record. On 2026-09-03 the business owner reviewed Musical DNA V1
  in full and explicitly approved it as correct. The approved answers are recorded inline
  below (verbatim) and, in paste-ready form for knowledge/business-dna/business-dna.md §9,
  in docs/MUSICAL-DNA-V1-FINAL.md.
authoritative_requirement: knowledge/business-dna/business-dna.md §9 ("Music DNA")
canonical_final_content: docs/MUSICAL-DNA-V1-FINAL.md
knowledge_transfer_status: >
  knowledge/business-dna/business-dna.md §9 has NOT been updated by tooling — knowledge/
  is human-owned and the guard-knowledge hook blocks it (fail-closed; not bypassed). The
  owner transfers docs/MUSICAL-DNA-V1-FINAL.md into §9 manually.
provenance: >
  All values below were reviewed in full and explicitly approved by the business owner on
  2026-09-03. Nothing was inferred, expanded, weakened, or reinterpreted by the system.
---

# Musical DNA — Owner Input Worksheet (COMPLETED)

> **STATUS: OWNER-APPROVED (2026-09-03).** The eight sonic dimensions are defined. The
> canonical, paste-ready §9 content is `docs/MUSICAL-DNA-V1-FINAL.md`. This file keeps the
> full approved answers inline alongside the original "what must not be inferred" framing,
> as the working record of how the house sound was established.

## Core positioning (owner-approved 2026-09-03)

Create instrumental relaxing experiences that feel like opening an inner space — ethereal,
deep, transcendental and contemplative, with expressions that may become angelic, cosmic,
luminous or abundant without losing softness, beauty and a sense of peace.

**North-star principle:** *"The music should transport, not pressure."*

## History

`knowledge/business-dna/business-dna.md` §9 previously recorded only the musical
positioning as **WELLNESS** (*"músicas instrumentais relaxantes"*, *"experiências
positivas"*) and listed eight sonic dimensions as `NEEDS INPUT`:

> instrumentação · energia · duração · textura · BPM · uso de frequências ·
> vocal / instrumental · critérios mais detalhados de sonoridade

This worksheet audited exactly what §9 asked for. The owner answered all eight on
2026-09-03. Those answers are below and in `docs/MUSICAL-DNA-V1-FINAL.md`.

## Where this is consumed

| Consumer | Status | How it uses Musical DNA |
|---|---|---|
| **MI Evaluation — `music_fit` dimension (spec §8.1 dim 5)** | live | While `business-dna.md` §9 still reads `NEEDS_INPUT` in-repo, `music_fit` **confidence stays capped ≤ `MEDIUM`** (`evaluation.py` `_apply_music_fit_cap`, gated by `orchestrator._musical_dna_needs_input`). Once the owner transfers §9, the detector flips automatically and the cap lifts. |
| **MI Evaluation — `music_fit` rating anchor (spec Appendix B.6 + `_RATING_ANCHORS`)** | live | HIGH/VERY_HIGH currently lean on cluster + asset match. Follow-up wiring (see `docs/MUSICAL-DNA-V1-FINAL.md`) sharpens the anchor to judge actual sonic fit against §9. |
| **Cluster Strategy V1 — `market_language_fit` confidence + `music_relationship` prose** | live (frozen) | Capped at ≤ `MEDIUM` (decision **D-CS-9**; `src/cluster_strategy/asset_strategy.py`). The cap's justification also cites the strategic-classification backlog, which is **still** `NEEDS_INPUT`, so it does not lift on §9 alone — a D-CS-9 revisit, out of scope for now. |
| **Run digest — `NEEDS_INPUT encountered`** | live (has a gap) | `reporting.py` `_collect_needs_input` only matches the literal token in `blocked_by`. Separate minor fix. |
| **Stage 4 — Page Blueprint** | deferred (P4) | Visual identity and tone of voice derive partly from the sound's character. This is the stage that most needs §9 — and §9 is now defined. |
| **Stage 5 — Content Strategy** | deferred (P4) | Hook/format choices that pair with the music. |
| **Stage 8 — Audio Engine** | deferred (P4) | BPM, instrumentation, texture, frequency use, duration become concrete production parameters here. |

## Rules that governed how these answers were gathered

1. **The system did not fill any of these.** No inference from track titles, artist names,
   cluster names, competitor catalogues, or genre heuristics (G05, G10; spec §15). Every
   value below came from explicit owner approval on 2026-09-03.
2. "It depends per cluster" is a valid answer and is used (see §9.5, §9.9).
3. The answers are recorded verbatim. Any translation to Portuguese for
   `knowledge/business-dna/business-dna.md` is an owner style choice, not a content change.

---

## 1. Instrumentation

**Decision the owner had to make:** which instrument families and sound sources are
in-bounds, which are signature, and which are off-limits.

**Downstream consumers:** Audio Engine (stage 8 — instrument selection), Page Blueprint
(stage 4 — visual identity cues from timbre), MI `music_fit` anchor.

**Must NOT be inferred:** from artist names, track titles, or the cluster label.

### ✅ Owner-approved answer (2026-09-03)

**Core in-bounds sound families:** soft piano · felt piano / ambient piano · atmospheric
pads · soft ambient/analog synths · harmonic drones · harp · soft sustained strings ·
ambient/textural guitar · very soft flutes and breath-like wind instruments · integrated
nature textures when musically appropriate · wordless ethereal vocal textures · wordless
angelic choirs · extremely subtle bells/chimes/crystalline elements.

**Signature sound families:** contemplative piano · atmospheric pads/drones · wordless
angelic vocal layers. *(These do not need to appear simultaneously in every track.)*

**Out-of-bounds as primary identity:** aggressive drums · dominant percussion · distorted
guitars · aggressive bass · aggressive synths · strongly commercial/pop timbres ·
cyberpunk/futuristic sonic aesthetics · elements that create urgency or tension.

---

## 2. Energy

**Decision the owner had to make:** the intensity / arousal band and how much it may move.

**Downstream consumers:** Audio Engine (stage 8 — arrangement density, dynamics), Content
Strategy (stage 5 — pacing), MI `music_fit` anchor.

**Must NOT be inferred:** from a cluster's emotional theme.

### ✅ Owner-approved answer (2026-09-03)

**Default energy:** low to moderately low · calming · non-urgent · spacious · introspective
· slowly evolving.

**Important distinction:** low physical/arousal energy does NOT mean emotionally dead.
Tracks may gradually expand emotionally and spatially through awakening · expansion ·
elevation · transcendence — especially relevant to abundance, spirituality, frequencies
and positive-experience clusters.

**Core rule:** LOW PHYSICAL ENERGY + HIGH EMOTIONAL/SPIRITUAL DEPTH.

---

## 3. Duration

**Decision the owner had to make:** target length(s) for a release and for content-facing cuts.

**Downstream consumers:** Audio Engine (stage 8), Video Engine (stage 7 — clip length),
Publishing (stage 10).

**Must NOT be inferred:** from competitor norms or platform norms alone.

### ✅ Owner-approved answer (2026-09-03)

**Default Spotify track length:** approximately 2–5 minutes.
**Long-form:** approximately 20–60+ minutes for sleep, ambience, continuous experiences
and specific YouTube formats.
**Short-form:** tracks should contain moments that can be extracted into short-form content
without destroying their atmosphere.
Do not create a rigid hard minimum/maximum at this stage.

---

## 4. Texture

**Decision the owner had to make:** density, space and surface character of the sound.

**Downstream consumers:** Audio Engine (stage 8 — mix and processing), Page Blueprint
(stage 4 — visual mood), MI `music_fit` anchor.

**Must NOT be inferred:** from the word "wellness" or from cluster names.

### ✅ Owner-approved answer (2026-09-03)

**Space:** very spacious · silence and breathing room are desirable · do not fill every
frequency continuously.
**Surface:** clean · soft · luminous · organic · digital textures allowed when they remain
ethereal rather than technological.
**Ambience:** deep and spacious · contemplative room · celestial space · cathedral-like
space when appropriate · cosmic/infinite space when appropriate.
**Movement:** slow continuous evolution · gradual transformation · slowly emerging harmonic
layers · breathing textures · no abrupt section changes as a default.
**Core textural concept:** FLOATING — the sound should feel like it floats rather than
simply plays.

---

## 5. BPM / Pulse

**Decision the owner had to make:** the tempo band, and whether tracks have a perceptible
pulse at all.

**Downstream consumers:** Audio Engine (stage 8), Content Strategy (stage 5), MI
`music_fit` anchor.

**Must NOT be inferred:** from genre heuristics.

### ✅ Owner-approved answer (2026-09-03)

Do not impose one universal BPM.
- **Sleep:** no perceptible pulse or extremely subtle pulse.
- **Meditation/relaxation:** slow, discreet pulse may be used.
- **Abundance/expansion/spirituality:** slightly more perceptible movement is allowed; must
  remain relaxing and never become dance-oriented.
- **Focus/study:** more consistent pulse may be used while remaining inside the relaxing
  identity.

**Universal rule:** THE PULSE MUST NEVER DOMINATE THE EXPERIENCE. Beatless ambient music is
fully valid.

---

## 6. Frequency use

**Decision the owner had to make:** the stance on "healing frequency" framing — as a
production choice and as an editorial choice.

**Downstream consumers:** Audio Engine (stage 8 — tuning/DSP), Cluster Strategy
(`music_relationship`, D-CS-9), Content Strategy (stage 5), the compliance self-check
(spec §19).

**Must NOT be inferred:** the system must not decide the business "uses" a frequency
because a competitor or a cluster name does.

### ✅ Owner-approved answer (2026-09-03)

Frequencies are part of the creative and commercial identity of the business.

**Potential frequency/tuning systems include:** 432 Hz · 528 Hz · Solfeggio frequencies ·
other frequency concepts used by specific clusters · binaural approaches when appropriate
for a specific product · isochronic approaches when appropriate for a specific product.

**Important distinction:** frequency as a musical/production element vs. frequency as
editorial/positioning language. Not every track must use a frequency.

**Compliance rule:** frequency positioning may describe experience, intention, atmosphere
and creative positioning. Never make medical, physiological, therapeutic,
disease-treatment or guaranteed efficacy claims.

---

## 7. Vocal / Instrumental

**Decision the owner had to make:** whether the human voice appears at all, and in what
non-lexical form.

**Downstream consumers:** Audio Engine (stage 8), Content Strategy (stage 5), MI
`music_fit` anchor.

**Must NOT be inferred:** from artist or playlist names.

### ✅ Owner-approved answer (2026-09-03)

**Primary business DNA:** INSTRUMENTAL.

Human voice may appear only as texture: ethereal vocal pads · humming · wordless
"ahh"/"ooh" · angelic choir · subtle breath textures when appropriate.

**Not part of the primary house sound:** lyrics · verses · choruses · rap · pop vocals ·
dominant spoken word.

Guided meditation/narration may eventually exist as a separate product line and must not
redefine the primary house sound.

---

## 8. Sonority criteria (detailed)

**Decision the owner had to make:** the remaining sound-quality rules — the "we would
reject a track if…" list.

**Downstream consumers:** Audio Engine (stage 8), Quality Control (stage 9), MI
`music_fit` anchor.

**Must NOT be inferred:** none of this may be back-filled from the catalogue's current
average.

### ✅ Owner-approved answer (2026-09-03)

**Reject or strongly question tracks containing:**
- *Energy problems:* aggression · urgency · sustained tension · chaos · excessive physical impact.
- *Arrangement problems:* excessive element density · abrupt changes · drops · obvious pop structures · excessively mechanical repetition.
- *Timbre problems:* aggressive sounds · distortion as a central element · cyberpunk/futuristic aesthetics · excessively artificial timbres that break the atmosphere · strongly commercial/pop sound when inconsistent with the experience.
- *Harmonic problems:* prolonged aggressive dissonance without purpose · strong conflict/tension · excessively dramatic resolution.

**The music may be:** mysterious · contemplatively melancholic · emotionally deep.
**But should not be predominantly:** frightening · anxious · chaotic · aggressive · desperate.

**Production quality requirements:** no clipping · no audible artifacts · no unpleasant
transients · no abrupt volume jumps · no excessively crushed mastering · no abrupt opening
that destroys the atmosphere · use appropriate fades/continuity when the format calls for them.

---

## House-sound principle (owner-approved 2026-09-03)

**DNA = one sonic universe. CLUSTER = a distinct expression inside that universe.**
Do NOT make every cluster sound identical.

| Cluster | Expression |
|---|---|
| Sono | deep · darker · soft · hypnotic |
| Meditação | contemplative · spacious · introspective |
| Frequências | vibrational · minimalist · harmonic |
| Espiritualidade | angelic · celestial · transcendental |
| Abundância | luminous · expansive · golden · elevated |
| Limpeza energética | light · crystalline · spacious · cleansing-oriented as an EXPERIENCE, never as a medical claim |
| Cura / bem-estar | warm · gentle · comforting |
| Foco / Estudo | stable · clean · continuous · discreet |

---

## Completion status

| # | Dimension | Status |
|---|---|---|
| 1 | Instrumentation | ✅ OWNER-APPROVED (2026-09-03) |
| 2 | Energy | ✅ OWNER-APPROVED (2026-09-03) |
| 3 | Duration | ✅ OWNER-APPROVED (2026-09-03) |
| 4 | Texture | ✅ OWNER-APPROVED (2026-09-03) |
| 5 | BPM / Pulse | ✅ OWNER-APPROVED (2026-09-03) |
| 6 | Frequency use | ✅ OWNER-APPROVED (2026-09-03) |
| 7 | Vocal / instrumental | ✅ OWNER-APPROVED (2026-09-03) |
| 8 | Sonority criteria | ✅ OWNER-APPROVED (2026-09-03) |
| — | Core positioning + North-star + House-sound principle | ✅ OWNER-APPROVED (2026-09-03) |

**Remaining:** the owner transfers `docs/MUSICAL-DNA-V1-FINAL.md` into
`knowledge/business-dna/business-dna.md` §9 (manual edit — the guard hook blocks tooling).
Downstream wiring follows the plan in `docs/MUSICAL-DNA-V1-FINAL.md`. Stage 4 may begin
once §9 is in place.
