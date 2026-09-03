---
title: Musical DNA — Owner Input Worksheet
status: NEEDS_INPUT
created: 2026-09-03
owner: Nicolas Alves (divinetonesmusic@gmail.com)
purpose: >
  A structured worksheet for the business owner to define the house sound
  ("Musical DNA"). This file is the QUESTION set; it does not contain answers.
  Nothing here may be filled in by the system — see "Rules" below.
authoritative_requirement: knowledge/business-dna/business-dna.md §9 ("Music DNA")
destination_when_filled: >
  The owner transfers the completed answers into
  knowledge/business-dna/business-dna.md §9 (or a new
  knowledge/business-dna/music-dna.md), as a manual owner edit — knowledge/ is
  human-owned and the guard-knowledge hook blocks tooling from writing it.
---

# Musical DNA — Owner Input Worksheet

## Why this exists

`knowledge/business-dna/business-dna.md` §9 records the musical positioning as
**WELLNESS** — *"músicas instrumentais relaxantes"* and *"experiências positivas"* —
and then lists **eight sonic dimensions as `NEEDS INPUT`**:

> instrumentação · energia · duração · textura · BPM · uso de frequências ·
> vocal / instrumental · critérios mais detalhados de sonoridade

Those eight items are still `NEEDS_INPUT` today. This worksheet is the audit of
exactly what §9 asks for and a place for the owner to answer it. It changes no
behaviour and asserts no musical identity.

## Where this is consumed today (and where it will be)

| Consumer | Status | How it uses Musical DNA |
|---|---|---|
| **MI Evaluation — `music_fit` dimension (spec §8.1 dim 5)** | live | While §9 is `NEEDS_INPUT`, `music_fit` **confidence is structurally capped at ≤ `MEDIUM`** (`evaluation.py` `_apply_music_fit_cap`, gated by `orchestrator._musical_dna_needs_input`). Evidence: 23 of 26 opportunities across the 3 C10 runs rated `music_fit: MEDIUM/LOW` — the dimension currently cannot discriminate. |
| **MI Evaluation — `music_fit` rating anchor (spec Appendix B.6)** | live | The anchor's `HIGH` / `VERY_HIGH` levels lean on cluster + asset match today because there is no sound spec to check a track against. Filling §9 lets the anchor test *actual sonic fit*. |
| **Cluster Strategy V1 — `market_language_fit` + `music_relationship` confidence** | live (frozen) | Both are capped at ≤ `MEDIUM` while §9 is `NEEDS_INPUT` (decision **D-CS-9**; `src/cluster_strategy/asset_strategy.py`). The cap also cites the strategic-classification backlog, so it does not lift on §9 alone. |
| **Run digest — `NEEDS_INPUT encountered`** | live (has a gap) | Should surface "musical DNA" every run; currently does not, because `reporting.py` `_collect_needs_input` only matches the literal token `NEEDS_INPUT`/`UNKNOWN` in `blocked_by`, which the model writes as prose ("business musical DNA / catalog detail"). Minor wiring fix, tracked separately. |
| **Stage 4 — Page Blueprint** | deferred (P4) | Visual identity and tone of voice are partly derived from the sound's character (energy, texture, instrumentation). This is the stage that most needs §9 defined. |
| **Stage 5 — Content Strategy** | deferred (P4) | Hook/format choices that pair with the music. |
| **Stage 8 — Audio Engine** | deferred (P4) | BPM, instrumentation, texture, frequency use, duration become concrete **production parameters** here. |

## Rules (apply to every field below)

1. **The system must not fill any of these.** Not from track titles, artist names,
   cluster names, competitor catalogues, playlist descriptions, or genre
   heuristics ("wellness music is usually ~60 BPM"). All of that is inference, and
   inference here is fabrication of a business identity (guardrails **G05**, **G10**;
   spec §15).
2. **`NEEDS_INPUT` stays until the owner writes a real answer.** A partial answer is
   fine and better than none — mark the rest `NEEDS_INPUT`.
3. **Ranges and "it depends per cluster" are valid answers.** The house sound may
   legitimately differ between Sono and Abundância; say so explicitly.
4. **Examples/reference tracks help more than adjectives.** A link to two existing
   releases that "sound right" is worth more than a paragraph.
5. When filled, the owner moves the answers into `knowledge/business-dna/` (see the
   front matter). This worksheet then stays as the question record.

---

## 1. Instrumentation

**Decision the owner must make:** which instrument families and sound sources are
in-bounds for the house sound, which are signature, and which are off-limits.

**Information / examples that would help:**
- A short in-bounds list (e.g. pads, felt/prepared piano, ambient guitar, hand
  percussion, nature textures, choir/vocal-pad *without lyrics*, synth drones).
- A "signature" subset — the 1–3 sounds a listener should associate with the brand.
- An out-of-bounds list (e.g. drum kits, distorted guitar, brass sections, spoken
  word, recognisable pop synths).
- Whether it varies by cluster (Sono vs Abundância vs Frequência Divina).
- 2–3 reference releases from the existing catalogue that exemplify it.

**Downstream consumers:** Audio Engine (stage 8 — instrument selection), Page
Blueprint (stage 4 — visual identity cues from timbre), MI `music_fit` anchor.

**Must NOT be inferred:** from artist names, track titles, or the cluster label.
"Coro dos Anjos" does not imply choir instrumentation as a house rule.

---

## 2. Energy

**Decision the owner must make:** the intensity / arousal band the music should sit
in, and how much it may move within a track.

**Information / examples that would help:**
- A qualitative band (e.g. "very low to low — never activating; a track should not
  raise heart rate").
- Whether any cluster is allowed to be higher-energy (e.g. Foco/Estudo slightly
  more forward than Sono).
- Dynamic range: does a track stay flat, or is a gentle swell acceptable?
- Reference tracks for "right energy" and one for "too much".

**Downstream consumers:** Audio Engine (stage 8 — arrangement density, dynamics),
Content Strategy (stage 5 — pacing of paired content), MI `music_fit` anchor.

**Must NOT be inferred:** from a cluster's emotional theme. "Abundância" is not a
licence for triumphant, high-energy arrangements unless the owner says so.

---

## 3. Duration

**Decision the owner must make:** the target length(s) for a release and for any
content-facing cut.

**Information / examples that would help:**
- Typical full-track length (a single number or a range, e.g. "2–4 min for
  playlist tracks; 30–60 min continuous mixes for sleep").
- Whether it differs by destination (Spotify track vs a long YouTube ambience vs a
  short-form clip).
- Any hard minimums/maximums (e.g. "never under 90 seconds on Spotify").
- Loopability: should tracks be seamless loops?

**Downstream consumers:** Audio Engine (stage 8), Video Engine (stage 7 — clip
length), Publishing (stage 10 — platform fit).

**Must NOT be inferred:** from what competitors release or from platform norms
alone.

---

## 4. Texture

**Decision the owner must make:** the density, space and surface character of the
sound.

**Information / examples that would help:**
- Density: sparse / medium / lush — and whether silence and space are wanted.
- Surface: clean and digital, or warm with tape/vinyl noise, room tone, breath,
  field recording?
- Reverb / ambience: intimate and dry, or large and cathedral-like?
- Movement: static bed vs slowly evolving.
- Reference tracks for the intended texture.

**Downstream consumers:** Audio Engine (stage 8 — mix and processing), Page
Blueprint (stage 4 — visual mood), MI `music_fit` anchor.

**Must NOT be inferred:** from the word "wellness" or from cluster names.

---

## 5. BPM

**Decision the owner must make:** the tempo band, and whether tracks have a
perceptible pulse at all.

**Information / examples that would help:**
- A range (e.g. "50–75 BPM") or "no fixed tempo / ambient, no pulse".
- Whether it varies by cluster (e.g. Foco/Estudo 60–80; Sono 40–60 or beatless).
- Whether a subtle beat/heartbeat pulse is ever wanted, or never.

**Downstream consumers:** Audio Engine (stage 8 — composition), Content Strategy
(stage 5 — matching content edit rhythm), MI `music_fit` anchor.

**Must NOT be inferred:** from genre heuristics or from "relaxing music is usually
~60 BPM". State it explicitly or leave `NEEDS_INPUT`.

---

## 6. Frequency use

**Decision the owner must make:** the business's stance on "healing frequency"
framing (432 Hz, 528 Hz, solfeggio, binaural beats, isochronic tones, Schumann
resonance, etc.) — both as a *production* choice and as an *editorial* choice.

**Information / examples that would help:**
- Which, if any, tuning/frequency features are actually used in production
  (e.g. "some catalogue is tuned to 432 Hz; binaural beats are used only in the
  Glândula Pineal / Frequências cluster").
- Which clusters use frequency framing in their titles/positioning and which must
  not.
- The **compliance line**: the guardrails (G01–G04) already bar efficacy claims;
  this field records the *positioning* stance (e.g. "we may name 432 Hz as a
  feature and describe the intended experience; we never claim a physiological or
  medical effect").

**Downstream consumers:** Audio Engine (stage 8 — tuning/DSP), Cluster Strategy
(`music_relationship` — already runs with a confidence cap, D-CS-9), Content
Strategy (stage 5), the compliance self-check (spec §19).

**Must NOT be inferred:** the system must not decide the business "uses 528 Hz"
because a competitor album does, or because a cluster is named for frequencies.

---

## 7. Vocal / instrumental

**Decision the owner must make:** whether the human voice appears at all, and if so
in what non-lexical form.

**Information / examples that would help:**
- The default (business-dna §1/§9 already says "instrumental" — confirm it as a
  hard rule or a strong default).
- Allowed non-lexical voice: wordless vocal pads, humming, choir "aah", breath,
  guided-meditation narration (is narration a separate product line or never?).
- Explicitly barred: sung lyrics, rap, spoken affirmations as the main content?
- Any cluster exceptions (e.g. Anjos / Espiritualidade Religiosa).

**Downstream consumers:** Audio Engine (stage 8), Content Strategy (stage 5 — is
there ever a voiceover?), MI `music_fit` anchor (a "needs vocals" opportunity is a
`LOW` fit today — this field confirms that rule).

**Must NOT be inferred:** from artist or playlist names that mention "voz",
"coro", "mantra", etc.

---

## 8. Sonority criteria (detailed)

**Decision the owner must make:** any remaining sound-quality rules that do not fit
the seven fields above — the "we would reject a track if…" list.

**Information / examples that would help:**
- Tonality / mode preferences (major, modal, drone-based, no strong resolution).
- Melodic character: is there a lead melody, or only atmosphere and motifs?
- Production standards: loudness target / LUFS, mono compatibility, no clipping,
  no abrupt starts/stops, fade conventions.
- Mastering house style (if any).
- A short "automatic reject" checklist (e.g. "sudden dynamic jumps", "dissonant
  clusters", "anything that sounds like a ringtone", "audible artefacts").
- Reference: 1–2 releases that pass cleanly, 1 that would be rejected and why.

**Downstream consumers:** Audio Engine (stage 8), Quality Control (stage 9 — this
is the QC checklist for audio), MI `music_fit` anchor.

**Must NOT be inferred:** none of this may be back-filled from the catalogue's
current average. The owner defines the standard; the catalogue is then measured
against it, not the reverse.

---

## Completion status

| # | Dimension | Status |
|---|---|---|
| 1 | Instrumentation | `NEEDS_INPUT` |
| 2 | Energy | `NEEDS_INPUT` |
| 3 | Duration | `NEEDS_INPUT` |
| 4 | Texture | `NEEDS_INPUT` |
| 5 | BPM | `NEEDS_INPUT` |
| 6 | Frequency use | `NEEDS_INPUT` |
| 7 | Vocal / instrumental | `NEEDS_INPUT` |
| 8 | Sonority criteria | `NEEDS_INPUT` |

When any row is answered, the owner updates `knowledge/business-dna/business-dna.md`
§9 accordingly. Only then does downstream wiring (loosening the `music_fit`
confidence cap; sharpening Appendix B.6) become appropriate — and Stage 4 should
not begin until enough of this table is filled to design a page's visual identity
and tone from the sound.
