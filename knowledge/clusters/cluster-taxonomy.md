---
title: Cluster Taxonomy — Canonical V1
status: CANONICAL_V1
created: "2026-08-27"
owner: Nicolas Alves (divinetonesmusic@gmail.com)
decision: owner-defined canonical taxonomy (2026-08-27)
canonical_cluster_count: 11
open_taxonomy: true
related:
  - knowledge/business-dna/business-dna.md (§2, §10–§11)
  - CLAUDE.md (§14 — C4 guardrails; §2 — clusters as examples)
  - knowledge/DECISIONS-NEEDED.md (C1 — OPPORTUNITY ≠ CLUSTER; P6 — cluster governance, DEFERRED)
  - docs/TECHNICAL-SPEC-V1.md (§10.2a — artist eligibility)
---

# Cluster Taxonomy — Canonical V1

## Purpose

This document defines the **canonical set of content clusters** for V1 — the closed list
of editorial categories that Market Intelligence, Opportunity Analysis, Asset Matching and
asset classification must use. It replaces ad-hoc / divergent labels (e.g. `Sono` vs
`Sono Restaurador`) with a single reference.

The canonical clusters are an **owner decision** (2026-08-27). There are exactly **11**.

## Cluster vs subcluster vs angle

| Level | What it is | Official in V1? |
|---|---|---|
| **Cluster (canonical)** | One of the 11 root editorial categories in this document. The level at which assets and opportunities are officially classified (`primary_cluster`, playlist/page `cluster`). | **Yes** — closed list. |
| **Subcluster** | A named, recurring subdivision inside a cluster (e.g. `Sono Restaurador`, `Sono Profundo` inside `Sono`). May be formalized later. | No — internal structure; can evolve freely. |
| **Angle (editorial)** | A specific content framing inside a cluster/subcluster (e.g. "dormir em 528 Hz", "o Sono do Pastor"). Tactical. | No — tactical; changes per campaign. |

Only **clusters** are official categories in V1. Subclusters and angles are internal
organization.

## Open-taxonomy rule

- The taxonomy is **open**: Market Intelligence may discover demand for a theme outside the
  11 clusters.
- In V1, a newly discovered cluster appears as a **hypothesis** inside an Opportunity Report
  (`potential_cluster`), **never** as an official category automatically.
- Formalizing a new canonical cluster is an **explicit owner decision**, recorded here (and,
  when applicable, in `DECISIONS-NEEDED.md`). Formal cluster governance is `DEFERRED` (P6).

## Cluster does NOT restrict artist eligibility

- A cluster is **editorial context**, not a restriction on which artists may participate.
- **Any artist can serve any cluster / playlist** per business strategy
  (`business-dna.md` §10; `docs/TECHNICAL-SPEC-V1.md` §10.2a).
- An artist's `primary_cluster` = **catalog affinity** (predominant observed theme), not an
  eligibility filter. `hero_artist` status is **independent** of cluster.

## Guardrails

- An editorial cluster implies **no medical claim and no promised outcome**.
- Labels such as "Cura", "Ansiedade", "Bem-estar" are **editorial positioning of subjective
  experience** (relaxation, environment, ritual, intention, comfort) — not treatment,
  diagnosis or disease prevention.
- The **C4 guardrails** (`CLAUDE.md` §14) always prevail over any cluster label.

---

## Canonical clusters (machine-readable)

```yaml
canonical_clusters:
  - id: sono
    name: "Sono"
  - id: abundancia-prosperidade
    name: "Abundância / Prosperidade"
  - id: limpeza-energetica
    name: "Limpeza Energética"
  - id: frequencia-divina-espiritualidade
    name: "Frequência Divina / Espiritualidade"
  - id: glandula-pineal-frequencias
    name: "Glândula Pineal / Frequências"
  - id: anjos-espiritualidade-religiosa
    name: "Anjos / Espiritualidade Religiosa"
  - id: meditacao-relaxamento
    name: "Meditação / Relaxamento"
  - id: ansiedade-relaxamento
    name: "Ansiedade / Relaxamento"
  - id: cura-bem-estar
    name: "Cura / Bem-estar"
  - id: foco-estudo
    name: "Foco / Estudo"
  - id: sonho-lucido
    name: "Sonho Lúcido"
```

---

## 1. Sono

- **Nome canônico:** `Sono`
- **Definição:** música instrumental para relaxar, adormecer e manter o sono ao longo da
  noite. É o cluster raiz para tudo relacionado a dormir e ao descanso noturno.
- **Subclusters / ângulos:** `Sono Restaurador`, `Sono Profundo`, `Sono + frequência`
  (ex.: 432 Hz, 528 Hz), indução ao sono, ondas delta/theta, anti-insônia — e outros a
  formalizar posteriormente.
- **Fronteira conceitual:** foco em **descanso passivo e continuidade do sono**. Não é
  relaxamento diurno (→ Meditação / Relaxamento), não é atividade consciente no sonho
  (→ Sonho Lúcido), não é alívio de ansiedade como objetivo primário
  (→ Ansiedade / Relaxamento).
- **Relação com outros clusters:** adjacente a Sonho Lúcido (mesma janela — o sono —
  intenção diferente); combinado editorialmente com frequência (Frequência Divina, Glândula
  Pineal), Cura / Bem-estar e Anjos / Espiritualidade Religiosa.
- **Regra:** `Sono Restaurador` **não** é cluster raiz — é subcluster / ângulo dentro de
  `Sono`. Rótulos `Sono Restaurador` em ativos devem ser normalizados para o cluster
  canônico `Sono` na consolidação.
- **status:** `CANONICAL_V1`

## 2. Abundância / Prosperidade

- **Nome canônico:** `Abundância / Prosperidade`
- **Definição:** música associada à intenção de prosperidade, dinheiro, sucesso material e
  manifestação.
- **Subclusters / ângulos:** manifestação, frequências de abundância (888 Hz, 777 Hz),
  "prosperar enquanto dorme", campo magnético do dinheiro, geometria da abundância.
- **Fronteira conceitual:** o tema é **prosperidade material/financeira e manifestação**.
  Não é espiritualidade genérica (→ Frequência Divina / Espiritualidade) nem cura
  (→ Cura / Bem-estar).
- **Relação com outros clusters:** cruza com Sono ("prosperidade enquanto dorme") e com
  Limpeza Energética ("limpeza do campo financeiro").
- **status:** `CANONICAL_V1`

## 3. Limpeza Energética

- **Nome canônico:** `Limpeza Energética`
- **Definição:** música associada à limpeza / purificação energética de pessoas, ambientes
  e do lar, proteção espiritual e remoção de energias densas.
- **Subclusters / ângulos:** proteção do lar, purificação do campo áurico, limpeza do
  subconsciente, corte de energias, 741 Hz.
- **Fronteira conceitual:** foco em **limpar / proteger**. Não é ativação espiritual
  (→ Frequência Divina / Glândula Pineal) nem recuperação/bem-estar (→ Cura / Bem-estar).
- **Relação com outros clusters:** cruza com Abundância / Prosperidade (limpeza do campo
  financeiro) e com Anjos / Espiritualidade Religiosa (proteção angélica).
- **status:** `CANONICAL_V1`

## 4. Frequência Divina / Espiritualidade

- **Nome canônico:** `Frequência Divina / Espiritualidade`
- **Definição:** música voltada à conexão espiritual, elevação de consciência e frequências
  "divinas" (963 Hz, terceiro olho, unidade), num registro **espiritual amplo / new age**,
  **não** vinculado a uma religião específica.
- **Subclusters / ângulos:** ativação do terceiro olho, expansão de consciência, 963 Hz,
  unidade / oneness, frequência do divino.
- **Fronteira conceitual:** espiritualidade **genérica e não-confessional**. Distinta de
  Anjos / Espiritualidade Religiosa (tradição judaico-cristã explícita) e de Glândula
  Pineal / Frequências (foco fisiológico/simbólico na pineal).
- **Relação com outros clusters:** sobreposição temática com Glândula Pineal / Frequências
  (963 Hz, terceiro olho — ver *Ambiguidades*); adjacente a Meditação / Relaxamento.
- **status:** `CANONICAL_V1`

## 5. Glândula Pineal / Frequências

- **Nome canônico:** `Glândula Pineal / Frequências`
- **Definição:** música centrada **especificamente na glândula pineal** — "ativação",
  "descalcificação", "limpeza" — e nas frequências a ela associadas.
- **Subclusters / ângulos:** descalcificação da pineal, ativação da pineal, 936 / 963 Hz,
  "abertura do terceiro olho" com foco pineal.
- **Fronteira conceitual:** o **foco explícito na glândula pineal** é o critério que o
  separa de Frequência Divina / Espiritualidade (espiritualidade ampla). São **clusters
  distintos** por decisão do proprietário, mesmo com temas que se tocam.
- **Relação com outros clusters:** sobreposição temática com Frequência Divina /
  Espiritualidade (963 Hz, terceiro olho); combinado com Sono ("ativação da pineal durante
  o sono").
- **status:** `CANONICAL_V1`

## 6. Anjos / Espiritualidade Religiosa

- **Nome canônico:** `Anjos / Espiritualidade Religiosa`
- **Definição:** música com referência **explícita a anjos, arcanjos e tradição religiosa**
  (predominantemente judaico-cristã na prática do catálogo atual) — salmos, "o Sono do
  Pastor", Sião, coros angélicos, arcanjos.
- **Subclusters / ângulos:** arcanjos (Miguel, Rafael), salmos / conteúdo bíblico, coros
  angélicos, cura angélica, "harpa de Davi".
- **Fronteira conceitual:** **referência religiosa / bíblica explícita**. Distinto de
  Frequência Divina / Espiritualidade (espiritualidade não-confessional).
- **Relação com outros clusters:** cruza fortemente com Sono (a maioria das faixas do
  catálogo combina anjos + sono) e com Cura / Bem-estar (cura angélica).
- **status:** `CANONICAL_V1`

## 7. Meditação / Relaxamento

- **Nome canônico:** `Meditação / Relaxamento`
- **Definição:** música para **prática de meditação e relaxamento diurno / geral** —
  aquietamento, presença, mindfulness — não necessariamente ligada a dormir.
- **Subclusters / ângulos:** trilha para meditação guiada, relaxamento profundo,
  mindfulness, sons ambientes, respiração.
- **Fronteira conceitual:** relaxamento e meditação **acordado**. Distinto de Sono
  (descanso noturno) e de Ansiedade / Relaxamento (onde o gatilho declarado é ansiedade /
  estresse).
- **Relação com outros clusters:** adjacente a Sono, Ansiedade / Relaxamento e
  Cura / Bem-estar. Compartilha a palavra "Relaxamento" com o cluster 8 — a fronteira é a
  **intenção** (ver *Ambiguidades*).
- **status:** `CANONICAL_V1`

## 8. Ansiedade / Relaxamento

- **Nome canônico:** `Ansiedade / Relaxamento`
- **Definição:** música posicionada em torno do **alívio de ansiedade, estresse e
  sobrecarga mental** — acalmar a mente, "anti-pensamentos", "sem estresse".
- **Subclusters / ângulos:** alívio de estresse, aquietamento mental, "dormir sem
  ansiedade" (cruzamento com Sono), ondas alfa, protocolo anti-pensamentos.
- **Fronteira conceitual:** o **gatilho emocional é ansiedade / estresse**. É posicionamento
  editorial de experiência subjetiva — **não** alegação de tratamento (C4). Distinto de
  Meditação / Relaxamento (prática ampla) e de Cura / Bem-estar (recuperação /
  restauração).
- **Relação com outros clusters:** cruza com Sono ("dormir sem ansiedade") e com
  Meditação / Relaxamento.
- **status:** `CANONICAL_V1` (formalizado na taxonomia V1)

## 9. Cura / Bem-estar

- **Nome canônico:** `Cura / Bem-estar`
- **Definição:** música associada a **bem-estar geral, recuperação, restauração e "cura" no
  sentido de conforto e experiência subjetiva** — regeneração, harmonia corpo-mente,
  recuperação do sistema nervoso. **Não** é medicina.
- **Subclusters / ângulos:** recuperação / restauração, harmonia corpo-mente, sistema
  nervoso, sono regenerativo (cruzamento com Sono), "cura" simbólica.
- **Fronteira conceitual:** a linguagem de "cura" é **editorial / simbólica**; nenhuma
  alegação de tratamento, diagnóstico ou prevenção de doença (C4). Distinto de
  Ansiedade / Relaxamento (gatilho específico) e de Limpeza Energética (limpar / proteger).
- **Relação com outros clusters:** cruza com Sono, Anjos / Espiritualidade Religiosa (cura
  angélica) e Meditação / Relaxamento.
- **status:** `CANONICAL_V1` (formalizado na taxonomia V1)

## 10. Foco / Estudo

- **Nome canônico:** `Foco / Estudo`
- **Definição:** música para **concentração, produtividade e sessões de estudo / trabalho**
  — sustentar a atenção, fluxo, "deep work".
- **Subclusters / ângulos:** estudo / leitura, deep work, ondas beta / alfa para
  concentração, fluxo / flow.
- **Fronteira conceitual:** o objetivo é **desempenho cognitivo acordado**. Distinto de
  Meditação / Relaxamento (aquietamento) e de Sono.
- **Relação com outros clusters:** baixa sobreposição com o restante da taxonomia; é o
  cluster mais **diurno / funcional**.
- **status:** `CANONICAL_V1` (formalizado na taxonomia V1)

## 11. Sonho Lúcido

- **Nome canônico:** `Sonho Lúcido`
- **Definição:** música voltada à **consciência e ao controle durante o sonho** — indução
  de sonho lúcido, ondas theta para lucidez onírica, exploração do estado onírico.
- **Subclusters / ângulos:** indução de sonho lúcido, ondas theta (8 Hz), sonhos vívidos,
  projeção / viagem astral, "ativar a intuição".
- **Fronteira conceitual:** ocorre **durante o sono**, mas a intenção é **atividade
  consciente no sonho**, não descanso passivo — por isso é cluster canônico próprio e
  **não** subcluster de Sono.
- **Relação com outros clusters:** adjacente a Sono (mesma janela) e a Frequência Divina /
  Espiritualidade (theta, expansão de consciência).
- **status:** `CANONICAL_V1`

---

## Ambiguidades registradas (decisão humana quando indicado)

1. **Sono ↔ Sonho Lúcido.** A lista do proprietário citou "Sonho Lúcido" **tanto** como
   ângulo dentro de Sono (#1) **quanto** como cluster #11. A taxonomia V1 resolve a favor
   de **cluster autônomo (#11)** — coerente com a classificação já aprovada da playlist
   "Sueño Lúcido – Ondas Theta…" como cluster `Sonho Lúcido`. Confirmar se essa é a leitura
   pretendida.
2. **"Relaxamento" em dois clusters.** Aparece em `Meditação / Relaxamento` (#7) e
   `Ansiedade / Relaxamento` (#8). A fronteira é a **intenção**: prática / aquietamento (7)
   vs. gatilho declarado de ansiedade / estresse (8). Uma oportunidade genérica de
   "relaxamento" pode ser enquadrada em qualquer um — escolha por oportunidade.
3. **Frequência Divina / Espiritualidade ↔ Glândula Pineal / Frequências.** Temas se
   sobrepõem (963 Hz, terceiro olho). Mantidos **distintos** por decisão do proprietário; o
   critério é o **foco explícito na glândula pineal**.
4. **Anjos / Espiritualidade Religiosa** é, na prática do catálogo atual, judaico-cristã
   (salmos, arcanjos). Se surgir conteúdo de outras tradições religiosas, confirmar se
   entra neste cluster ou gera um novo (via hipótese — regra de abertura).
5. **Reconciliação pendente com `classification-input.yaml`.** A página "Frequências de
   Sono Profundo" está classificada como `Sono`; as playlists de sono como
   `Sono Restaurador`. Na consolidação, `Sono Restaurador` → cluster canônico `Sono`
   (subcluster). Não alterado nesta etapa.

---

## Referências

- `knowledge/business-dna/business-dna.md` — §2 (clusters de exemplo), §10 (afinidade de
  catálogo ≠ restrição), §11 (playlist strategy, artistas heróis).
- `CLAUDE.md` — §2 (clusters como exemplos, taxonomia extensível), §14 (guardrails C4),
  §6 (definição de oportunidade — `OPPORTUNITY ≠ CLUSTER`).
- `knowledge/DECISIONS-NEEDED.md` — C1 (unidade de oportunidade), P6 (governança de cluster
  novo — `DEFERRED`).
- `docs/TECHNICAL-SPEC-V1.md` — §7 (Opportunity Model, `hypotheses.potential_cluster`),
  §10.2a (elegibilidade de artista).
