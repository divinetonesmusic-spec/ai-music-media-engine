---
title: Business DNA — AI Music Media Engine
status: provisional
created: 2026-08-27
owner: Nicolas Alves (divinetonesmusic@gmail.com)
source: Informações fornecidas pelo proprietário do negócio em 2026-08-27 (conversa de arquitetura)
decision: DECISIONS-NEEDED.md — C3
---

# Business DNA — AI Music Media Engine

Este documento registra a identidade e a estratégia do negócio conforme informadas pelo
**proprietário do negócio (Nicolas Alves)** em 2026-08-27.

- Nada aqui foi inventado pelo sistema.
- Onde a informação ainda não existe, o item está marcado **`NEEDS INPUT`**.
- Aspirações e intenções estratégicas estão registradas como tais — **não** como garantias
  nem como claims de resultado.
- Documento **provisório**: deve ser completado conforme os `NEEDS INPUT` forem respondidos.

---

## 1. Identidade do negócio

- O negócio é um **sistema de artistas musicais instrumentais de músicas relaxantes**,
  organizados em diferentes clusters.
- Opera como uma **franquia / portfólio de artistas e playlists** distribuídos em
  diferentes clusters.
- Aquisição de audiência acontece através de:
  - tráfego pago no Meta;
  - conteúdo orgânico em páginas temáticas;
  - o conteúdo leva as pessoas ao link na bio;
  - o link direciona para playlists;
  - as playlists crescem ao longo do tempo;
  - os artistas também crescem;
  - o negócio monetiza através dos **royalties musicais**.

---

## 2. Missão e visão

- **Missão:** construir uma franquia de artistas ouvida por milhões de pessoas no mundo
  inteiro e impactar positivamente a vida dessas pessoas através da música.
- **Filosofia do fundador:** construir um negócio que proporcione algo positivo à
  humanidade através da música.
- **Visão financeira:** construir uma **fonte de renda de longo prazo** através do
  crescimento desse ecossistema.
- **Ressalva obrigatória:** "fonte de renda de longo prazo" é uma intenção estratégica.
  Não deve ser transformada em promessa ou garantia operacional — em particular, o sistema
  não deve tratar a receita futura como certa nem apresentar "fonte de renda ilimitada"
  como um resultado assegurado.

---

## 3. Experiência desejada

Experiências associadas ao universo musical do negócio:

- paz;
- harmonia;
- alegria;
- elevação da consciência;
- relaxamento;
- experiências positivas em geral.

---

## 4. Modelo de receita

- **Principal modelo econômico:** royalties musicais.
- **Ecossistemas atualmente relevantes:**
  - Spotify;
  - TikTok;
  - YouTube Music.
- Existe uma **segunda oportunidade de negócio no YouTube como plataforma de vídeo**,
  através da criação e monetização de conteúdo audiovisual próprio (ver seção 7).
- **`NEEDS INPUT`:** peso relativo entre os royalties dos diferentes ecossistemas;
  participação esperada do YouTube Video na receita; existência e peso de outras fontes
  (ex.: sync, Content ID, brand deals).

---

## 5. Music Trend Engine

- Conteúdos sociais **não servem apenas** para levar pessoas ao Spotify.
- Uma segunda função estratégica é **aumentar a exposição das músicas**.
- Conteúdos que alcançam milhões de visualizações **podem aumentar as chances** de uma
  música ser utilizada por outras pessoas como áudio, transformando a música em uma
  tendência e gerando royalties relacionados ao uso da música (UGC).
- Portanto, conteúdos sociais **podem possuir objetivos diferentes** entre si.
- Nota: trata-se de um mecanismo probabilístico ("podem aumentar as chances"), não de um
  resultado garantido.

---

## 6. Content Objectives

O sistema deve considerar pelo menos estes objetivos potenciais de conteúdo:

- Playlist Growth;
- Music Discovery;
- Music Trend / UGC;
- Page Growth;
- YouTube Media.

Regras:

- Uma oportunidade deve poder ser avaliada em **múltiplos objetivos simultaneamente**.
- Não assumir que uma oportunidade com baixo potencial em um objetivo é necessariamente
  ruim.

Exemplo conceitual (ilustrativo — não é uma oportunidade real):

```
Playlist Growth: HIGH
Music Trend:     VERY HIGH
Streaming:       HIGH
Page Growth:     HIGH
YouTube Media:   LOW
```

---

## 7. YouTube — dois papéis distintos

YouTube deve ser tratado de forma **diferente** de plataformas de vídeos curtos. Existem
dois papéis, que não devem ser misturados:

- **YouTube Music:** distribuição / consumo do catálogo musical e geração de royalties.
- **YouTube Video:** operação de mídia audiovisual própria, com estratégia, conteúdo,
  retenção, audiência e monetização **diferentes** de short-form.

A estratégia de **YouTube Video** deve ser desenvolvida posteriormente, em um estágio
próprio. Está **fora do escopo do V1**.

---

## 8. Mercados e idiomas

- **Mercados linguísticos prioritários:**
  - Português;
  - Espanhol;
  - Inglês.
- Não assumir ainda países específicos além dessa definição linguística.
- **`NEEDS INPUT`:** países-alvo dentro de cada idioma; prioridade entre os três idiomas;
  mercados explicitamente fora de escopo.

---

## 9. Music DNA

- **Posicionamento musical informado:** WELLNESS.
- A operação deve contemplar **músicas instrumentais relaxantes** e **experiências
  positivas**.
- **`NEEDS INPUT`** (não inventar — especificar posteriormente):
  - instrumentação;
  - energia;
  - duração;
  - textura;
  - BPM;
  - uso de frequências;
  - vocal / instrumental;
  - critérios mais detalhados de sonoridade.

---

## 10. Artist Architecture

Cada artista tem uma **afinidade de catálogo** — o tema predominante ou o contexto
editorial observado no seu catálogo (ex.: sono, abundância, limpeza energética,
frequências / espiritualidade). Essa afinidade é **contexto, não uma restrição**.

Regra estratégica (decisão do proprietário, 2026-08-27):

- **Qualquer artista pode participar de qualquer cluster e de qualquer playlist** quando
  isso fizer parte da estratégia do negócio. A afinidade de catálogo **não limita** a
  participação, independentemente do nome da faixa ou do tema predominante.
- Três conceitos que o sistema deve manter **distintos** e nunca colapsar:
  - **catalog affinity** — tema predominante observado no catálogo do artista;
  - **playlist placement** — em quais playlists o artista está de fato posicionado
    (decisão estratégica / operacional);
  - **strategic hero status** — se o artista é um artista herói (ver §11); classificação
    estratégica **independente** da afinidade de catálogo.
- O sistema **não deve** concluir que um artista "não serve" para uma oportunidade apenas
  porque o catálogo dele tem afinidade predominante com outro cluster.
- Os exemplos de afinidade acima são ilustrativos — não são a lista oficial de artistas
  nem de clusters.

**`NEEDS INPUT`:** consolidação da afinidade de catálogo (`primary_cluster` / clusters
secundários) dos 37 artistas — em andamento em
`knowledge/inventories/classification-input.yaml` (ver I1).

---

## 11. Playlist Strategy

- As playlists são **ativos centrais** do negócio. A estratégia do negócio é **crescer os
  artistas dentro das playlists**.
- O conteúdo social pode direcionar tráfego para as playlists.
- **Artistas heróis** são selecionados **estrategicamente** e posicionados **em todas as
  playlists predefinidas**, para receber maior exposição e gerar **sinais reais de consumo
  e engajamento**:
  - saves;
  - retorno;
  - repetição;
  - visitas ao perfil;
  - baixa taxa de skip;
  - outros sinais relevantes de comportamento.
- O status de artista herói é uma **classificação estratégica independente** da afinidade
  de catálogo do artista (ver §10).
- **Roster de heróis (decisão do proprietário, 2026-08-27):** Nimbus Sleep Sanctuary;
  Divine Tones; Sonia Amor Divino; Thetara; Meditação Sonora; Hertzia; Brainhertz;
  Arcturian Healing Codes; Dormesia; Frequenzia. Fonte operacional:
  `knowledge/inventories/classification-input.yaml` (`hero_artist: true`).
- **Intenção estratégica:** aumentar a relevância dos artistas e playlists dentro do
  ecossistema do Spotify e ampliar as possibilidades de crescimento e descoberta, inclusive
  oportunidades relacionadas ao **Spotify Radio**.
- **Ressalva obrigatória:** nenhum resultado futuro (crescimento, descoberta, inclusão em
  Radio) deve ser tratado como garantido.
- **`NEEDS INPUT`:** regras detalhadas de posicionamento; consolidação nos inventários (ver
  I1).

---

## 12. Growth Model

Modelo atual:

```
Conteúdo
→ Página temática
→ Link na bio
→ Playlist
→ Consumo
→ Engajamento
→ Crescimento da playlist / artistas
→ Royalties
```

E também, em paralelo:

```
Conteúdo viral
→ descoberta da música
→ utilização da música por terceiros
→ expansão do áudio
→ royalties relacionados ao uso da música
```

Os dois caminhos coexistem e podem ter objetivos de conteúdo diferentes (ver seção 6).

---

## 13. Brand Innegotiable

O proprietário informou explicitamente:

> "O sistema não deve virar uma ferramenta de spam."

Portanto, o sistema deve **evitar**:

- produção indiscriminada sem estratégia;
- publicação repetitiva sem propósito;
- conteúdo feito apenas para volume;
- comportamento que degrade a qualidade da audiência;
- automações que transformem a operação em spam.

(Relaciona-se com C4 — guardrails de compliance — e I12 — controle de volume / gargalo do
operador.)

---

## 14. Strategic Horizon

- O negócio pretende trabalhar **simultaneamente** com:
  - tendências rápidas;
  - oportunidades evergreen.
- O Market Intelligence **deve diferenciar** esses tipos de oportunidade (ver C2 e I9).

---

## 15. Múltiplos motores de valor (eixos de avaliação)

Toda oportunidade poderá ser avaliada **individualmente** em:

- Playlist Growth Potential;
- Music Trend / UGC Potential;
- Streaming Royalty Potential;
- Page Growth Potential;
- YouTube Media Potential.

Esses são **eixos de avaliação do ecossistema**, não necessariamente fontes de receita
independentes.

Nota de arquitetura: como esses eixos entram no modelo de avaliação depende das decisões
C5, C6 e C9, ainda em aberto.

---

## Distinções que o sistema deve preservar

- **Oportunidade ≠ Cluster** (C1). A oportunidade é a oportunidade de mercado; o cluster é
  a estrutura editorial que poderá ser criada para explorá-la numa etapa posterior.
- **YouTube Music ≠ YouTube Video** (seção 7).
- **Playlist Growth ≠ Music Trend / UGC** (seções 5 e 6).

---

## Itens `NEEDS INPUT` (consolidado)

| Área | O que falta |
|------|-------------|
| Music DNA (seção 9) | instrumentação, energia, duração, textura, BPM, uso de frequências, vocal/instrumental, critérios de sonoridade |
| Mercados (seção 8) | países-alvo por idioma, prioridade entre idiomas, mercados fora de escopo |
| Receita (seção 4) | pesos entre ecossistemas de royalties, participação esperada do YouTube Video, outras fontes |
| Artistas (seção 10) | consolidação da afinidade de catálogo dos 37 (em andamento em classification-input.yaml) |
| Playlists (seção 11) | regras detalhadas de posicionamento (roster de heróis já definido — ver §11) |
| Inventários | playlists, páginas, catálogo (ver I1) |
| Metodologia de conteúdo | material existente do negócio (ver I11) |

---

## Referências

- `knowledge/DECISIONS-NEEDED.md` — C1 (unidade de oportunidade), C3 (esta captura), C4
  (compliance), C5/C6/C9 (modelo de avaliação), I1 (inventários), I9 (durabilidade da
  tendência), I11 (metodologia de conteúdo).
- `CLAUDE.md` — §2 (business context), §3 (existing assets), §4 (strategic objective).
