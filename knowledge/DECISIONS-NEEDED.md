---
title: Decisions Needed — AI Music Media Engine
status: draft
created: 2026-08-27
owner: Nicolas Alves (divinetonesmusic@gmail.com)
phase: V1 — Market Intelligence
source: Revisão crítica do CLAUDE.md (IDs C1–C10, I1–I12, P1–P10)
---

# Decisions Needed — AI Music Media Engine

Este arquivo registra **decisões que ainda precisam ser tomadas**, não decisões já tomadas.

Nenhuma decisão de negócio foi tomada aqui. As **recomendações** são propostas para o
proprietário do negócio e/ou o responsável técnico ratificarem, ajustarem ou rejeitarem.
Os IDs mantêm rastreabilidade com a revisão crítica do `CLAUDE.md`.

## Como usar

- Quando uma decisão for tomada: mudar `status` para `DECIDED`, e registrar em
  **Resultado** a escolha, a data e quem decidiu.
- Não editar o `CLAUDE.md` a partir deste arquivo sem uma revisão explícita do documento.
- Este arquivo é conhecimento-fonte (`knowledge/`), versionado e de propriedade humana.

## Legenda de status

| Status | Significado |
|---|---|
| `NEEDS INPUT` | Bloqueada: depende de informação que **somente o proprietário do negócio** pode fornecer. |
| `OPEN` | Pronta para decisão: há informação suficiente; falta ratificar uma escolha (técnica ou de processo). |
| `DEFERRED` | Pode aguardar sem bloquear o V1. Revisar quando o V1 for validado. |
| `DECIDED` | Decisão tomada. Registrar data, responsável e resultado. |

## Papéis

- **Proprietário** — proprietário do negócio: estratégia, dados do negócio, orçamento, apetite a risco, compliance.
- **Arquitetura** — responsável técnico do projeto: design, implementação, trade-offs de engenharia.

---

## Índice de status

| ID | Título | Prioridade | Status | Quem decide |
|----|--------|-----------|--------|-------------|
| C1 | Unidade de "oportunidade" | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| C2 | Estratégia de fontes de sinal do V1 | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| C3 | Business DNA mínimo | CRÍTICO | DECIDED (2026-08-27) — doc provisório | Proprietário |
| C4 | Guardrails de compliance | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| C5 | Alinhamento objetivo (§4) × avaliação (§7) | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| C6 | Formato do modelo de score no V1 | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| C7 | Fronteira de escopo do Market Intelligence | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| C8 | Pipeline canônico (§1 × §15) | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| C9 | Lista única de dimensões de avaliação | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| C10 | Critério de "pronto" do V1 | CRÍTICO | DECIDED (2026-08-27) | Proprietário |
| I1 | Inventários de ativos | IMPORTANTE | DECIDED (2026-08-27) — classificação estratégica pendente | Proprietário + Arquitetura |
| I2 | Registro e transições do ciclo de vida | IMPORTANTE | DECIDED (2026-08-27) — transições pós-TEST DEFERRED | Proprietário |
| I3 | Padronização de "recommended action" | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I4 | Schema do Opportunity Report | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I5 | Critério de "ativo novo justificado" | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I6 | Fronteira `business-dna/` × `rules/` | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I7 | Papel de `data/` × `reports/` | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I8 | Um agente monolítico × pipeline de componentes | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I9 | Dimensão de durabilidade/timing da tendência | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I10 | Stack técnico | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I11 | Metodologia de conteúdo existente | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| I12 | Controle de volume / gargalo do operador | IMPORTANTE | DECIDED (2026-08-27) | Proprietário |
| P1 | Loop de calibração do score com dados reais | POSTERGÁVEL | DEFERRED (2026-08-27) | Proprietário + Arquitetura |
| P2 | Transições automáticas / autonomia L2–L3 | POSTERGÁVEL | DEFERRED (2026-08-27) | Proprietário |
| P3 | Integrações de dados em tempo real / APIs pagas | POSTERGÁVEL | DEFERRED (2026-08-27) | Proprietário + Arquitetura |
| P4 | Estágios seguintes do pipeline | POSTERGÁVEL | DEFERRED (2026-08-27) — estágios 3 (Cluster Strategy) e 4 (Page Blueprint) abertos 2026-09-01 / 2026-09-04 (ver D-CS-1, D-PB-1); estágios 5–13 seguem DEFERRED | Proprietário |
| P5 | Orquestração multi-agente | POSTERGÁVEL | DEFERRED (2026-08-27) | Arquitetura |
| P6 | Governança de criação de cluster novo | POSTERGÁVEL | DEFERRED (2026-08-27) | Proprietário + Arquitetura |
| P7 | Dashboards / tracking entre runs | POSTERGÁVEL | DEFERRED (2026-08-27) | Arquitetura |
| P8 | Versionamento de prompts / reprodutibilidade | POSTERGÁVEL | DEFERRED (2026-08-27) | Arquitetura |
| P9 | Conjunto de referência de concorrentes por cluster | POSTERGÁVEL | DEFERRED (2026-08-27) | Arquitetura |
| P10 | Reconciliação textual completa do pipeline no CLAUDE.md | POSTERGÁVEL | DECIDED (2026-08-27) | Proprietário + Arquitetura |
| D-CS-1 | Abertura do estágio 3 (Cluster Strategy) | ESTÁGIO 3 | DECIDED (2026-09-01) | Proprietário |
| D-CS-2 | Governança de cluster novo no estágio 3 (× P6) | ESTÁGIO 3 | DECIDED (2026-09-01) | Proprietário + Arquitetura |
| D-CS-3 | Gatilho de entrada no Cluster Strategy | ESTÁGIO 3 | DECIDED (2026-09-01) | Proprietário + Arquitetura |
| D-CS-4 | Dimensões do Cluster Strategy / sem status persistente | ESTÁGIO 3 | DECIDED (2026-09-01) | Arquitetura + Proprietário |
| D-CS-5 | Profundidade da direção de conteúdo | ESTÁGIO 3 | DECIDED (2026-09-01) | Proprietário + Arquitetura |
| D-CS-6 | Local de saída / digest do estágio 3 | ESTÁGIO 3 | DECIDED (2026-09-01) | Arquitetura |
| D-CS-7 | Vínculo com `opportunity-registry.yaml` | ESTÁGIO 3 | DECIDED (2026-09-01) | Proprietário + Arquitetura |
| D-CS-8 | Fronteira do estágio 3 × Business DNA V1 §11 | ESTÁGIO 3 | DECIDED (2026-09-01) | Proprietário + Arquitetura |
| D-CS-9 | Rodar com DNA musical NEEDS_INPUT | ESTÁGIO 3 | DECIDED (2026-09-01) | Proprietário + Arquitetura |
| D-CS-10 | Ponderação de value engine no estágio 3 | ESTÁGIO 3 | DECIDED (2026-09-01) | Arquitetura + Proprietário |
| D-CS-11 | Tratamento de schema_version | ESTÁGIO 3 | DECIDED (2026-09-01) | Arquitetura |
| D-CS-12 | Reconciliação de nomes do pipeline (C8) | ESTÁGIO 3 | DECIDED (2026-09-01) | Arquitetura |
| D-PB-1 | Abertura do estágio 4 (Page Blueprint) | ESTÁGIO 4 | DECIDED (2026-09-04) | Proprietário |
| D-PB-2 | Fronteira do estágio 4 × Business DNA V1 §11–§13 | ESTÁGIO 4 | DECIDED (2026-09-04) | Proprietário + Arquitetura |
| D-PB-3 | Herança verbatim do ativo do Cluster Strategy | ESTÁGIO 4 | DECIDED (2026-09-04) | Proprietário + Arquitetura |
| D-PB-4 | Escopo de consumo do DNA musical §9 (identidade visual / tom de voz) | ESTÁGIO 4 | DECIDED (2026-09-04) | Proprietário + Arquitetura |
| D-PB-5 | Modelo de avaliação/confiança do estágio 4; sem dimensões; sem status persistente | ESTÁGIO 4 | DECIDED (2026-09-04) | Arquitetura + Proprietário |
| D-PB-6 | Profundidade do content framing (pilares de página apenas) | ESTÁGIO 4 | DECIDED (2026-09-04) | Proprietário + Arquitetura |
| D-PB-7 | Gatilho de entrada no Page Blueprint | ESTÁGIO 4 | DECIDED (2026-09-04) | Proprietário + Arquitetura |
| D-PB-8 | Local de saída / digest do estágio 4 | ESTÁGIO 4 | DECIDED (2026-09-04) | Arquitetura |
| D-PB-9 | Ausência de escrita em `knowledge/` (contraste com D-CS-7) | ESTÁGIO 4 | DECIDED (2026-09-04) | Proprietário + Arquitetura |
| D-PB-10 | Rodar com DNA musical NEEDS_INPUT (caminho de fallback) | ESTÁGIO 4 | DECIDED (2026-09-04) | Proprietário + Arquitetura |
| D-PB-11 | Tratamento de schema_version | ESTÁGIO 4 | DECIDED (2026-09-04) | Arquitetura |
| D-PB-12 | Reconciliação de nomes do pipeline (C8) | ESTÁGIO 4 | DECIDED (2026-09-04) | Arquitetura |
| OMR-01 | External LLM Gateway — isolated adapter | GATEWAY EXTERNO (OMR) | DECIDED (2026-09-04) — adapter isolado implementado; integração com o pipeline NÃO aprovada | Proprietário + Arquitetura |
| OMR-02 | External Model Use Cases & Routing Policy | GATEWAY EXTERNO (OMR) | DECIDED (2026-09-04) — política de routing aprovada; nenhuma integração de stage aprovada | Proprietário + Arquitetura |
| OMR-03 | Normalization Benchmark — Threshold Policy V1 | GATEWAY EXTERNO (OMR) | DECIDED (2026-09-04) — critérios de aprovação pré-registrados; benchmark/dataset/integração NÃO aprovados | Proprietário + Arquitetura |

---

# 1. CRÍTICO

Bloqueia começar o Market Intelligence Agent. Sem resolver, o agente inventa regra de
negócio (viola Engineering Rule #9) ou produz saída não utilizável.

---

## C1 — Unidade de "oportunidade"

- **Problema:** o `CLAUDE.md` nunca define o que é uma "oportunidade". §4 lista 10 dimensões
  de combinação; §6 fala em "temas emergentes"; §13 tem um campo literal `opportunity`
  dentro do relatório. Granularidade e forma indefinidas.
- **Por que isso importa:** sem uma unidade fixa, os relatórios não são comparáveis, o score
  não tem base consistente, o ranking é arbitrário e os estágios seguintes do pipeline não
  têm contrato de entrada estável.
- **Decisão necessária:** fixar a unidade de análise e a granularidade mínima obrigatória de
  um registro de oportunidade.
- **Opções possíveis:**
  - (a) Keyword / termo de busca — granular demais, explode em volume, perde contexto.
  - (b) Tema amplo — pouco acionável, difícil de pontuar.
  - (c) Tupla estruturada: `necessidade emocional + cluster + mercado/idioma + plataforma`,
    com hook / formato / ângulo como hipótese opcional.
  - (d) Ângulo de conteúdo específico (hook + formato + cluster) — invade Content Strategy
    (ver C7).
- **Recomendação:** (c). É acionável, comparável, pontuável e respeita a fronteira do C7.
- **Quem precisa decidir:** Arquitetura (proposta) + Proprietário (validação).
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  **Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.**
  Definição oficial **provisória para o V1** (a revisar com dados de calibração pós-V1):

  > Uma oportunidade é uma necessidade, desejo ou comportamento de uma audiência que
  > apresenta sinais de demanda ou crescimento e que pode ser transformado em um cluster
  > de conteúdo, explorado em um mercado/idioma e plataforma específicos, e conectado a um
  > ativo musical existente ou potencial nova operação de conteúdo.

  **Estrutura mínima obrigatória de uma oportunidade:**
  - necessidade / desejo / comportamento;
  - público / audiência;
  - mercado;
  - idioma;
  - plataforma;
  - contexto de consumo.

  **Campos derivados ou hipotéticos** (preenchidos como hipótese, não vinculantes — ver C7):
  - cluster potencial;
  - ângulo potencial;
  - formato;
  - hook;
  - ativos musicais compatíveis.

  **Regra estrutural:** `OPORTUNIDADE != CLUSTER`. A oportunidade é a oportunidade de
  mercado; o cluster é a estrutura editorial que poderá ser criada para explorá-la numa
  etapa posterior do pipeline.

  Esta definição substitui a opção (c) originalmente recomendada, que fica registrada
  acima como histórico.

---

## C2 — Estratégia de fontes de sinal do V1

- **Problema:** §6 lista ~17 tipos de sinal. Não há indicação de quais são acessíveis,
  autorizados ou pagos.
- **Por que isso importa:** sem fontes reais, "market intelligence" vira "LLM chutando
  tendências a partir do treino" — defasado (cutoff jan/2026), enviesado para EUA/inglês,
  não auditável. Risco arquitetural direto de escalar a oportunidade errada.
- **Decisão necessária:** lista fechada de fontes que o V1 vai usar, mais orçamento e
  limites operacionais.
- **Opções possíveis:**
  - (a) Só pesquisa web via LLM com busca ao vivo.
  - (b) Pesquisa web via LLM + input manual estruturado de analista (planilha / Markdown).
  - (c) (b) + 1–2 APIs gratuitas ou baratas (Google Trends, TikTok Creative Center,
    YouTube Data API, Spotify).
  - (d) Pipeline de dados completo com APIs pagas.
- **Recomendação:** (b) no primeiro run, evoluindo para (c). Toda fonte fica atrás de um
  schema `Signal` plugável. (d) é POSTERGÁVEL (ver P3).
- **Quem precisa decidir:** Proprietário (quais contas/acessos já existem, orçamento para
  APIs, se há analista humano) + Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Market Intelligence V1 utilizará as seguintes fontes de sinais:

  1. Web Search ao vivo
  2. TikTok Creative Center
  3. YouTube
  4. Dados internos do negócio, inicialmente fornecidos de forma manual/estruturada

  Cada evidência deverá ser normalizada em um schema `Signal` contendo, no mínimo:
  - `signal_id`
  - `source`
  - `source_type`
  - `observed_at`
  - `market`
  - `language`
  - `platform`
  - `signal_type`
  - `evidence`
  - `context`
  - `confidence`

  A arquitetura deverá permitir a adição futura de novas fontes e APIs sem necessidade de
  reconstrução do pipeline.

  O sistema deverá distinguir entre:
  - sinais efêmeros;
  - tendências emergentes;
  - demandas potencialmente evergreen.

  O Spotify não será tratado como fonte primária de descoberta de tendências sociais no V1.
  Será utilizado posteriormente principalmente para avaliar o fit da oportunidade com
  playlists, artistas e demais ativos musicais existentes.

  APIs pagas e integrações adicionais ficam fora do escopo inicial do V1 e poderão ser
  adicionadas posteriormente após validação do sistema.

---

## C3 — Business DNA mínimo

- **Problema:** `knowledge/business-dna/` está vazio. Faltam posicionamento de marca,
  voz/tom, inegociáveis, modelo de monetização, prioridade entre métricas, mercados e
  idiomas no escopo, definição de "on-brand" musical, roster de artistas.
- **Por que isso importa:** é metade do contrato de entrada do agente ("Input: Business
  context"). Sem o modelo de monetização não existe definição de "resultado de negócio
  significativo", da qual §4 e §8 dependem.
- **Decisão necessária:** produzir `knowledge/business-dna/business-dna.md` mínimo.
- **Informação que só o Proprietário pode fornecer:**
  - posicionamento de marca e o que a marca não é;
  - voz / tom / linguagem;
  - inegociáveis;
  - modelo de monetização (streams, sync, Content ID, brand deals, outros) e peso relativo;
  - prioridade entre as métricas do funil do §4;
  - mercados e idiomas dentro e fora do escopo;
  - o que torna uma faixa "on-brand" (mood, instrumentação, energia, duração);
  - artistas e o posicionamento de cada um.
- **Opções possíveis:** não é escolha entre alternativas — é captura de fato do negócio.
- **Recomendação:** criar o arquivo como template com seções e marcadores `NEEDS INPUT`;
  o Proprietário preenche; nada é inventado pelo sistema.
- **Quem precisa decidir:** Proprietário.
- **Status:** DECIDED (2026-08-27) — documento provisório
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  Criado `knowledge/business-dna/business-dna.md`, refletindo fielmente as informações
  fornecidas pelo proprietário nesta data, em 15 seções: identidade do negócio; missão e
  visão; experiência desejada; modelo de receita; Music Trend Engine; Content Objectives;
  YouTube (dois papéis); mercados e idiomas; Music DNA; Artist Architecture; Playlist
  Strategy; Growth Model; Brand Innegotiable ("o sistema não deve virar uma ferramenta de
  spam"); Strategic Horizon; múltiplos motores de valor.

  Nada foi inventado. Aspirações e intenções estratégicas foram registradas como tais, sem
  virarem garantias ou claims de resultado. As distinções obrigatórias foram preservadas:
  oportunidade ≠ cluster, YouTube Music ≠ YouTube Video, Playlist Growth ≠ Music Trend/UGC.

  Itens ainda não definidos ficam marcados `NEEDS INPUT` dentro do próprio arquivo: Music
  DNA detalhado (instrumentação, energia, duração, textura, BPM, frequências,
  vocal/instrumental); países-alvo e prioridade entre idiomas; pesos entre ecossistemas de
  royalties e participação do YouTube Video; roster real de artistas e seus clusters; lista
  de "artistas heróis" e regras de posicionamento; inventários (I1); metodologia de
  conteúdo existente (I11).

  A decisão registrada aqui é a criação e consolidação do Business DNA a partir do input do
  proprietário. O documento em si permanece **provisório** e deve ser completado conforme
  os `NEEDS INPUT` forem respondidos.

---

## C4 — Guardrails de compliance

- **Problema:** `knowledge/rules/` está vazio. Os clusters incluem "anxiety", "healing",
  "well-being", "energetic cleansing", "abundance / prosperity" — território de alegação
  médica e de política de plataforma.
- **Por que isso importa:** o V1 já produz "recommended positioning", "copy" e "first
  content direction" (§13). Sem regras, gera risco legal e de plataforma já na saída.
- **Decisão necessária:** regras mínimas de conteúdo e segurança em `knowledge/rules/`.
- **Opções possíveis:**
  - (a) Rascunho conservador padrão de indústria wellness (sem alegação de
    cura/tratamento/diagnóstico; linguagem de "apoio"/"relaxamento"; sem promessa de
    resultado), revisado pelo Proprietário.
  - (b) Proprietário define do zero com apoio jurídico.
  - (c) Sem regras no V1 — não recomendado.
- **Recomendação:** (a) como rascunho **não vinculante**, sujeito a revisão do Proprietário
  e, antes de qualquer publicação, a revisão jurídica. As regras precisam existir já no V1
  porque moldam o output, mesmo sem publicação.
- **Quem precisa decidir:** Proprietário, idealmente com apoio jurídico.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  Guardrails operacionais mínimos do V1:

  1. Não criar alegações de cura, tratamento, diagnóstico ou prevenção de doenças.
  2. Conteúdo de wellness pode abordar relaxamento, ambiente, ritual, intenção, foco,
     conforto e experiência subjetiva.
  3. Não apresentar frequências, música, meditação ou práticas relacionadas como
     tratamento médico.
  4. Não inventar evidências científicas.
  5. Não fabricar números, tendências, resultados de pesquisa ou outras evidências.
  6. Não copiar indevidamente conteúdo, identidade ou ativos de terceiros.
  7. Não produzir spam ou conteúdo em massa cujo único objetivo seja inundar plataformas.
  8. Priorizar conteúdo genuinamente relevante e útil para o público.
  9. Claims que dependam de evidência devem ser sinalizados para validação.
  10. Em caso de dúvida, o agente deve explicitar a incerteza em vez de inventar uma
      resposta.

  Esses guardrails são operacionais para o V1 e deverão ser refinados posteriormente
  conforme novos estágios do sistema forem implementados.

---

## C5 — Alinhamento entre objetivo (§4) e avaliação (§7)

- **Problema:** §4 manda otimizar por um funil que termina em Streams → Saves → Followers e
  diz explicitamente "não otimize por views". As 8 dimensões de score do §7 não têm nenhuma
  dimensão de conversão, receita ou resultado de funil.
- **Por que isso importa:** o sistema é instruído a otimizar X e avaliar Y — desalinhamento
  estrutural que faz o ranking premiar a oportunidade errada.
- **Decisão necessária:** como as dimensões de score se conectam ao funil do §4, e se uma
  dimensão de conversão/resultado deve ser adicionada.
- **Opções possíveis:**
  - (a) Adicionar dimensão "Potencial de resultado de negócio" (proxy do funil §4:
    probabilidade de gerar streams/saves/followers, não só views).
  - (b) Manter as 8 dimensões e aplicar um "ajuste por alinhamento ao funil" pós-score.
  - (c) Redefinir "audience potential" e "content potential" para incluir conversão.
- **Recomendação:** (a) — dimensão explícita e separada, mais transparente e calibrável.
- **Quem precisa decidir:** Arquitetura (proposta) + Proprietário (o funil é estratégia).
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O sistema deverá avaliar uma oportunidade em relação aos diferentes motores de valor do
  negócio sem reduzir esses motores a uma única métrica.

  O Business Outcome Potential será representado por um perfil separado contendo:

  - Playlist Growth Potential
  - Music Trend / UGC Potential
  - Streaming Royalty Potential
  - Page Growth Potential
  - YouTube Media Potential

  Esses eixos representam potenciais resultados estratégicos/econômicos da oportunidade.

  Eles não devem ser confundidos com as dimensões utilizadas para explicar por que uma
  oportunidade é considerada forte ou fraca.

  As dimensões de avaliação explicam a qualidade da oportunidade.

  O Business Outcome Profile explica em quais motores do ecossistema essa oportunidade pode
  gerar valor.

  Uma oportunidade pode apresentar alto potencial em um motor e baixo potencial em outro e
  continuar sendo considerada estratégica.

---

## C6 — Formato do modelo de score no V1

- **Problema:** §7 define score 0–100 com 8 dimensões, "provisório", sem direção por
  dimensão (ex.: "competition" alto = pouca concorrência ou boa posição?), sem âncoras de
  escala, sem pesos, sem fórmula, sem mapeamento score → estado do ciclo de vida.
- **Por que isso importa:** falsa precisão — um número 0–100 com aparência de autoridade
  construído sobre julgamentos arbitrários; o humano ancora decisão em ruído. §7 diz
  calibrar com dados reais, mas §12 proíbe publicação, então o V1 não gera dados de
  calibração.
- **Decisão necessária:** escolher o formato de avaliação do V1.
- **Opções possíveis:**
  - (a) Rubrica numérica completa 0–100 já no V1 (direção + âncoras + pesos + fórmula),
    versionada em `knowledge/`.
  - (b) Tiers qualitativos no V1 (Alto / Médio / Baixo por dimensão + nível de confiança),
    migrando para número quando houver calibração.
  - (c) Híbrido: tiers por dimensão + um score composto grosseiro, sem pretensão de precisão.
- **Recomendação:** (b). Evita falsa precisão, é honesto sobre a incerteza do V1, e a
  rubrica numérica pode ser construída depois sobre os mesmos julgamentos.
- **Quem precisa decidir:** Arquitetura (proposta) + Proprietário (validação).
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Market Intelligence V1 não utilizará um score numérico composto de 0–100.

  A avaliação será construída através de:

  1. Perfil multidimensional utilizando as 10 dimensões definidas em C9.
  2. Rating qualitativo por dimensão:
     - LOW
     - MEDIUM
     - HIGH
     - VERY HIGH
  3. Confidence separado:
     - LOW
     - MEDIUM
     - HIGH
  4. Red flags ou fatores impeditivos relevantes.
  5. Uma recomendação operacional (`target_state`), que pode representar qualquer estado do
     ciclo de vida conceitual:
     - EXPLORE
     - TEST
     - LAUNCH
     - SCALE
     - KILL
     - PARK (estado adicional de pausa/priorização)

     SCALE permanece um estado conceitual futuro do ciclo de vida (ver §9 do CLAUDE.md).
     No V1, a execução permanece limitada a EXPLORE / TEST / PARK; LAUNCH, SCALE e KILL
     permanecem conceituais/deferred até existirem dados reais de performance.

  A recomendação operacional deverá ser explicada através das evidências, avaliações,
  confiança e eventuais red flags.

  O V1 não deverá inventar pesos ou fórmulas matemáticas para produzir um score composto
  sem dados suficientes para justificar sua validade.

  Quando houver dados reais suficientes provenientes dos ciclos de teste, a metodologia de
  avaliação poderá ser recalibrada e um modelo quantitativo poderá ser considerado em uma
  etapa posterior.

  A avaliação deverá preservar a incerteza: confiança baixa não deve ser apresentada como
  certeza apenas porque determinadas dimensões receberam ratings altos.

---

## C7 — Fronteira de escopo do Market Intelligence

- **Problema:** §13 exige que o relatório entregue "recommended positioning", "recommended
  page" e "first content direction". §15 tem estágios separados e posteriores: Cluster
  Strategy → Page Blueprint → Content Strategy. O próprio spec faz o V1 invadir 3 estágios
  seguintes.
- **Por que isso importa:** escopo indefinido é escopo infinito; o V1 incha e nunca fica
  pronto.
- **Decisão necessária:** traçar a fronteira exata do Market Intelligence V1.
- **Opções possíveis:**
  - (a) Estreito: entrega oportunidade + evidência + avaliação + ação recomendada + fit com
    ativos existentes. Direção de conteúdo/página aparece apenas como hipótese marcada como
    "a validar no próximo estágio".
  - (b) Médio: acima + proposta firme de posicionamento e página (incluindo "página nova").
  - (c) Amplo: tudo do §13 literal, com "first content direction" detalhada.
- **Recomendação:** (a). Os campos "recommended positioning / recommended page / first
  content direction" do §13 são preenchidos em nível de hipótese e explicitamente marcados
  como não vinculantes.
- **Quem precisa decidir:** Arquitetura + Proprietário.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Market Intelligence V1 terá escopo deliberadamente estreito.

  Sua responsabilidade é:
  - descobrir oportunidades;
  - estruturar oportunidades;
  - registrar evidências;
  - avaliar oportunidades;
  - priorizar oportunidades;
  - avaliar o fit com os ativos existentes;
  - recomendar uma ação para a próxima etapa.

  O Market Intelligence poderá fornecer hipóteses leves sobre:
  - cluster potencial;
  - posicionamento potencial;
  - página potencial;
  - primeira direção de conteúdo.

  Essas hipóteses não são decisões finais e não substituem os estágios posteriores.

  O Market Intelligence V1 NÃO será responsável por:
  - definir o Page Blueprint completo;
  - criar a estratégia completa de conteúdo;
  - criar grandes lotes de hooks e conteúdos;
  - produzir vídeos;
  - produzir áudio;
  - publicar conteúdo;
  - executar a operação das redes sociais.

  A saída principal do Market Intelligence V1 é uma oportunidade estruturada, evidenciada,
  avaliada e priorizada, pronta para ser encaminhada ao próximo estágio do pipeline.

  Regra de separação:
  Market Intelligence responde "quais oportunidades existem e quais merecem nossa
  atenção?".
  Os estágios seguintes respondem "como devemos explorar essa oportunidade?".

  Observações e hipóteses criativas produzidas pelo Market Intelligence devem ser
  explicitamente marcadas como observação ou hipótese, e não como estratégia definitiva.

---

## C8 — Pipeline canônico (§1 × §15)

- **Problema:** §1 e §15 descrevem pipelines diferentes — número de estágios, nomes, e se
  "Opportunity" é um estágio ou dois.
- **Por que isso importa:** afeta a nomeação de componentes e diretórios, as fronteiras do
  C7 e a comunicação sobre o projeto.
- **Decisão necessária:** eleger o pipeline canônico.
- **Opções possíveis:**
  - (a) §15 como canônico (mais granular); §1 = visão resumida.
  - (b) §1 como canônico (mais simples); §15 = visão aspiracional.
  - (c) Uma terceira versão reconciliada.
- **Recomendação:** (a) — §15 já é descrito como "expected long-term architecture" e tem a
  granularidade necessária. Registrar a decisão aqui; incorporar ao `CLAUDE.md` só numa
  revisão explícita do documento (ver P10).
- **Quem precisa decidir:** Arquitetura + Proprietário.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O pipeline canônico do AI Music Media Engine será:

  1. Market Intelligence
  2. Opportunity Analysis
  3. Cluster Strategy
  4. Page Blueprint
  5. Content Strategy
  6. Content Production
  7. Video Engine
  8. Audio Engine
  9. Quality Control
  10. Publishing
  11. Analytics
  12. Optimization
  13. Learning

  Definição dos dois primeiros estágios:

  Market Intelligence:
  descobre, coleta e organiza sinais relevantes do mercado.

  Opportunity Analysis:
  estrutura, avalia, compara e prioriza oportunidades com base nas evidências, dimensões de
  avaliação, confiança, red flags e Business Outcome Profile.

  No V1, Market Intelligence e Opportunity Analysis serão implementados como um único
  workflow funcional, mas permanecerão conceitualmente separados para preservar uma
  arquitetura modular e permitir evolução futura.

  O V1 implementará somente:

  Market Intelligence
  → Opportunity Analysis
  → Opportunity Report

  Os demais estágios permanecerão fora do escopo de implementação do V1, mas fazem parte da
  arquitetura futura oficial.

---

## C9 — Lista única de dimensões de avaliação

- **Problema:** as 8 dimensões de score do §7 e os campos do relatório do §13 são listas
  diferentes. O §13 omite "differentiation", "production feasibility" e o "compatibility
  with existing assets" geral. Dimensões calculadas mas não reportadas, ou reportadas mas
  não calculadas.
- **Por que isso importa:** inconsistência entre o que é avaliado e o que é comunicado ao
  operador.
- **Decisão necessária:** uma lista única autoritativa de dimensões de avaliação, todas
  presentes no relatório com nota e justificativa.
- **Opções possíveis:**
  - (a) Adotar as 8 do §7 como autoritativas; o relatório mostra as 8; os campos do §13
    viram narrativa por cima.
  - (b) Adotar os campos do §13 e descartar diferenciação e viabilidade de produção.
  - (c) Lista unificada = 8 do §7 + "potencial de resultado de negócio" (C5) +
    "durabilidade / timing" (I9) + "confiança / qualidade da evidência".
- **Recomendação:** (c). Depende de C5, C6 e I9.
- **Quem precisa decidir:** Arquitetura (proposta) + Proprietário (validação).
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Market Intelligence V1 utilizará as seguintes dimensões de avaliação:

  1. Signal Strength
  2. Audience Potential
  3. Growth / Momentum
  4. Durability / Opportunity Window
  5. Music Fit
  6. Content Potential
  7. Competitive Position
  8. Differentiation Potential
  9. Asset Fit
  10. Business Outcome Potential

  Cada dimensão deverá utilizar, no V1, uma escala qualitativa:

  - LOW
  - MEDIUM
  - HIGH
  - VERY HIGH

  A avaliação deverá possuir separadamente um nível de confiança:

  - LOW
  - MEDIUM
  - HIGH

  O sistema não deverá utilizar um score numérico de 0–100 no V1.

  A dimensão Business Outcome Potential deverá ser detalhada através do Business Outcome
  Profile definido em C5.

  Cada dimensão deverá ser acompanhada de justificativa baseada nas evidências disponíveis
  sempre que aplicável.

---

## C10 — Critério de "pronto" do V1

- **Problema:** §12 fala em não expandir "antes de o workflow do V1 ser validado" e §14
  Rule #10 pede "validar cada estágio antes de expandir", mas validação nunca é definida.
- **Por que isso importa:** sem critério, o V1 nunca "termina" e a expansão vira palpite —
  contraria §12 e Rule #10.
- **Decisão necessária:** critérios de aceitação mensuráveis do V1.
- **Opções possíveis (a combinar):**
  - Volume: N oportunidades por run (ex.: 5–15).
  - Qualidade: o humano concorda com a priorização em ≥ X% dos casos ao longo de M runs.
  - Rastreabilidade: 100% dos relatórios com fonte + data + premissas registradas.
  - Integridade: zero playlist / página / artista inventado.
  - Utilidade: ≥ K oportunidades por trimestre efetivamente acionadas (manualmente).
- **Recomendação:** adotar os quatro primeiros como gate técnico; o quinto como métrica de
  acompanhamento pós-V1. Os números exatos dependem da capacidade real de execução do
  Proprietário.
- **Quem precisa decidir:** Proprietário (metas e números) + Arquitetura (métricas).
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  Definition of Done do Market Intelligence V1:

  O V1 será considerado validado quando, durante 3 execuções consecutivas:

  1. Produzir entre 5 e 10 oportunidades priorizadas por execução.
  2. Possuir 100% de rastreabilidade das evidências, incluindo fonte e data de observação.
  3. Distinguir explicitamente fatos/evidências observados de hipóteses.
  4. Não inventar playlists, artistas ou páginas; quando um ativo não estiver disponível no
     inventário, utilizar UNKNOWN.
  5. Pelo menos 70% das oportunidades apresentadas no Top 10 forem consideradas pelo
     proprietário suficientemente relevantes para análise ou teste.
  6. Pelo menos uma oportunidade for selecionada pelo proprietário para avançar ao próximo
     estágio durante o período de validação.

  Esses critérios são específicos do V1 e poderão ser substituídos ou complementados por
  métricas quantitativas depois que existirem dados reais de teste e performance.

  O objetivo do gate é validar funcionamento, confiabilidade, rastreabilidade e utilidade
  do sistema antes de expandir para os demais estágios do pipeline.

---

# 2. IMPORTANTE

Necessário nas primeiras semanas, não no minuto zero. É possível começar o agente com
decisões provisórias aqui, desde que registradas.

---

## I1 — Inventários de ativos

- **Problema:** §3 e §13 dependem de listas estruturadas de playlists, páginas, catálogo e
  artistas. Não existem, e §9 não define onde ficam.
- **Por que isso importa:** os campos "existing playlist fit" e "recommended page" não podem
  ser produzidos com fidelidade sem inventário — risco de o agente inventar ativos.
- **Decisão necessária:** criar `knowledge/inventories/` e definir como populá-lo.
- **Opções possíveis:**
  - (a) Inventário completo antes do primeiro run.
  - (b) Inventário parcial (playlists + páginas mais relevantes) + campos marcados
    best-effort / `UNKNOWN` quando não há dado.
  - (c) Sem inventário no V1; o agente sempre marca "a confirmar".
- **Recomendação:** (b). Não bloqueia o primeiro run e melhora a cada iteração.
- **Quem precisa decidir:** Proprietário (fornece os dados dos ativos) + Arquitetura (schema).
- **Status:** DECIDED (2026-08-27) — inventário factual criado; classificação estratégica pendente
- **Resultado:**

  Foi adotada a abordagem de **inventário factual inicial**: extrair apenas o que está
  presente nas planilhas-fonte, sem inferência estratégica.

  Criados em `knowledge/inventories/`:
  - `artists.yaml` — 37 artistas (23 da planilha "Controle Mensal 23 Artistas", 14 da
    "Controle Mensal 14 Artistas"); todos ativos próprios; com Spotify artist ID, URL,
    distribuidoras observadas, meses de lançamento e contagem de lançamentos.
  - `playlists.yaml` — 8 playlists (Spotify), com nome, ID e URL.
  - `pages.yaml` — 49 páginas (5 próprias + 44 de referência/concorrentes), todas TikTok,
    com nome, handle e URL; a distinção próprias vs. concorrentes vem explícita da fonte
    (abas separadas).
  - `catalog.yaml` — 133 lançamentos, cada um rastreável à aba e linha de origem; mês da
    fonte preservado, ano marcado como `UNKNOWN` (a fonte só traz o mês).

  Regras aplicadas:
  - os quatro arquivos são **derivados das planilhas-fonte** em
    `knowledge/inventories/source/`, com proveniência (arquivo, aba, linha) registrada em
    cada item;
  - informações não presentes na fonte ficaram como `UNKNOWN`;
  - classificações estratégicas (cluster, mercado, idioma, posicionamento, artista herói)
    ficaram como `NEEDS_INPUT` — **nada foi inferido de nome ou título**;
  - IDs estáveis e determinísticos: `art_<spotify_id>`, `pl_<spotify_id>`,
    `page_tiktok_<handle>`, `cat_<spotify_id>_r<linha>`.

  Validação executada: YAML sintaticamente válido nos 4 arquivos; sem IDs duplicados; sem
  referências quebradas entre `catalog.yaml` e `artists.yaml`; todos os campos estratégicos
  em `NEEDS_INPUT`; todos os registros com proveniência.

  As classificações estratégicas serão preenchidas posteriormente pelo proprietário. Os
  inventários deverão ser tratados como **fonte estruturada de ativos existentes** para o
  Market Intelligence (avaliação de Asset Fit, playlist/página recomendada, compatibilidade
  musical). Quando um ativo necessário não constar do inventário, o agente deve usar
  `UNKNOWN` em vez de inventar (ver C10, item 4).

---

## I2 — Registro e transições do ciclo de vida

- **Problema:** §8 define 5 estados só qualitativamente ("enough potential", "appropriate
  testing"), sem critério mensurável, sem time-box, sem registro. Não há "opportunity
  registry" no §9.
- **Por que isso importa:** sem registro e sem critério, o ciclo de vida do §8 é decorativo.
  Além disso, o V1 não publica, então na prática só EXPLORE e "recomendar ir para TEST" são
  alcançáveis.
- **Decisão necessária:** registro de oportunidades + persistência de estado + critérios de
  transição.
- **Opções possíveis:**
  - (a) Registro append-only em `reports/` com front-matter (id, estado, data, histórico).
  - (b) Índice central `knowledge/market/opportunity-registry.md` (ou `.yaml`).
  - (c) Adiar tudo — V1 só produz EXPLORE + recomendação.
- **Recomendação:** (b) para o registro, com a regra de que o V1 opera só
  EXPLORE → (recomendar TEST). Os critérios mensuráveis de TEST → LAUNCH → SCALE → KILL
  ficam DEFERRED até haver publicação (ligado a P1 e P2).
- **Quem precisa decidir:** Arquitetura + Proprietário (define "evidência suficiente").
- **Status:** DECIDED (2026-08-27) — transições pós-TEST DEFERRED
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Market Intelligence V1 utilizará um registro central persistente de oportunidades.

  O registro deverá possuir, no mínimo:
  - opportunity_id estável;
  - status;
  - created_at;
  - referência ao Opportunity Report;
  - histórico mínimo de mudanças de estado.

  No V1, os estados operacionalmente utilizados serão:

  - EXPLORE
  - TEST
  - PARK

  O Market Intelligence poderá recomendar que uma oportunidade avance de EXPLORE para TEST,
  mas não executará o teste automaticamente. A decisão de avançar continuará sob aprovação
  humana.

  Os estados:
  - LAUNCH
  - SCALE
  - KILL

  continuam fazendo parte do ciclo de vida conceitual do sistema, mas seus critérios de
  transição mensuráveis e qualquer automação dessas transições ficam DEFERRED até que
  existam dados reais de performance provenientes dos testes.

  O registro de oportunidades deve permitir evolução futura sem quebrar os Opportunity
  Reports existentes.

---

## I3 — Padronização de "recommended action"

- **Problema:** §13 tem o campo "recommended action" e §8 tem 5 estados; não se diz se a
  ação é um dos estados ou texto livre.
- **Por que isso importa:** é o campo mais consequente do relatório para o operador; sem
  padrão, cada relatório recomenda de um jeito.
- **Decisão necessária:** padronizar o campo.
- **Opções possíveis:**
  - (a) Ação = um dos 5 estados-alvo + justificativa.
  - (b) Ação = texto livre.
  - (c) Ação = estado-alvo + próximo passo concreto sugerido (ex.: "TEST: 3 vídeos no
    TikTok BR da página X").
- **Recomendação:** (c), respeitando a fronteira do C7 — o "próximo passo" é sugestão, não
  ordem.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O campo recommended_action será estruturado como:

  - target_state
  - suggested_next_step
  - justification

  O target_state deverá utilizar os estados de ciclo de vida definidos para o sistema.

  O suggested_next_step deverá ser um próximo passo concreto e acionável, mas permanecerá
  como recomendação.

  O Market Intelligence não executará automaticamente a ação recomendada no V1.

  Exemplo conceitual:

  target_state: TEST
  suggested_next_step: executar um pequeno teste de conteúdo no mercado/plataforma indicados
  justification: explicação baseada nas evidências e avaliações da oportunidade.

---

## I4 — Schema do Opportunity Report

- **Problema:** o §13 lista 13 tópicos, mas faltam mercado/idioma, plataforma explícita,
  confiança / qualidade da evidência / premissas, ID + data + snapshot das fontes, esforço
  estimado e critério de teste/kill.
- **Por que isso importa:** sem esses campos o relatório não é acionável nem auditável, e o
  aprendizado futuro (§15) fica impossível.
- **Decisão necessária:** definir o schema do relatório (campos obrigatórios + formato).
- **Opções possíveis:**
  - (a) Markdown livre seguindo os 13 tópicos do §13.
  - (b) Markdown com front-matter YAML estruturado + corpo narrativo (id, data, fontes[],
    mercado, idioma, plataforma[], cluster, confiança, premissas[], avaliação, estado
    recomendado, esforço estimado).
  - (c) JSON puro + renderer para Markdown.
- **Recomendação:** (b). Legível por humano e por máquina; o front-matter alimenta o
  ranking e o registro (I2).
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Opportunity Report do Market Intelligence V1 será estruturado em formato legível por
  humanos e máquinas, utilizando Markdown com YAML Front Matter.

  O relatório deverá conter, no mínimo:

  1. Identity
     - opportunity_id
     - created_at
     - run_id
     - schema_version

  2. Market Context
     - market
     - language
     - platforms
     - need / desire / behavior
     - audience
     - consumption context

  3. Evidence
     - sinais utilizados
     - fontes
     - URLs quando disponíveis
     - datas de observação
     - confidence
     - distinção entre OBSERVED, INFERRED e HYPOTHESIS

  4. Evaluation
     - as 10 dimensões definidas em C9
     - rating de cada dimensão
     - justificativa
     - confidence

  5. Business Outcome Profile
     - Playlist Growth Potential
     - Music Trend / UGC Potential
     - Streaming Royalty Potential
     - Page Growth Potential
     - YouTube Media Potential

  6. Asset Fit
     - matching artists
     - matching playlists
     - matching pages
     - UNKNOWN quando não houver evidência suficiente

  7. Hypotheses
     - potential cluster
     - potential positioning
     - potential page
     - first content direction

  8. Recommendation
     - EXPLORE
     - TEST
     - LAUNCH
     - PARK
     - KILL
     - justification
     - suggested next step

  9. Provenance
     - origem dos dados utilizados
     - fontes dos sinais
     - informações relevantes para reprodutibilidade

  O relatório deve separar explicitamente fatos observados, inferências e hipóteses.

  UNKNOWN deve ser utilizado quando uma informação necessária não estiver disponível ou não
  puder ser sustentada pelas fontes.

  O schema deverá ser versionado através de schema_version para permitir evolução futura sem
  quebrar relatórios anteriores.

  O formato deve permanecer compatível com leitura humana, processamento programático e
  versionamento em Git.

  Não é necessário criar banco de dados no V1 para armazenar os Opportunity Reports.

---

## I5 — Critério de "ativo novo justificado"

- **Problema:** §3 prega reuso ("identifique a melhor playlist existente", "whenever
  possible") mas §8 LAUNCH = "justificar uma nova página". Sem critério de quando criar.
- **Por que isso importa:** sem regra, o agente ou nunca propõe ativo novo (perde
  oportunidade estrutural) ou propõe demais (contraria o ethos de reuso).
- **Decisão necessária:** regra explícita de reuso vs. criação.
- **Opções possíveis:**
  - (a) Sempre reusar no V1; "ativo novo" é só uma flag de recomendação, nunca uma ação.
  - (b) Critério: propor ativo novo só quando nenhum ativo existente atinge um limiar de
    fit **e** a oportunidade tem avaliação alta **e** volume/durabilidade justificam.
  - (c) Deixar 100% a critério humano; o agente não opina.
- **Recomendação:** (b), com o limiar de fit e os thresholds definidos junto com C6. No V1
  continua sendo recomendação (L1).
- **Quem precisa decidir:** Proprietário (apetite por novos ativos) + Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O sistema deverá priorizar o reuso dos ativos existentes.

  Uma nova página ou outro ativo novo poderá ser recomendado quando, cumulativamente ou de
  forma suficientemente forte:

  - não existir ativo existente com fit adequado;
  - a oportunidade apresentar potencial relevante;
  - existir potencial plausível de diferenciação;
  - a oportunidade possuir durabilidade ou janela suficiente para justificar o investimento.

  No V1, a criação de novos ativos será apenas uma recomendação.

  O sistema não criará automaticamente novas páginas, playlists ou outros ativos durante o
  V1.

---

## I6 — Fronteira `business-dna/` × `rules/`

- **Problema:** §9 cria duas pastas para "regras" sem definir a fronteira. Pesos de score?
  Voz de marca? Vão para onde?
- **Por que isso importa:** arquivos mal-arquivados = o agente não encontra a regra, ou
  aplica a errada.
- **Decisão necessária:** definição de fronteira + convenção de formato.
- **Opções possíveis / Recomendação:**
  - `business-dna/` = identidade e estratégia: posicionamento, voz, monetização, prioridade
    de métricas, mercados-alvo, definição de "on-brand", modelo de score.
  - `rules/` = restrições operacionais e de segurança: compliance, política de plataforma,
    copyright, temas proibidos, limites de autonomia.
  - `market/` = conhecimento de mercado acumulado: aprendizados, perfis de concorrentes,
    histórico de sinais, registro de oportunidades.
  - `clusters/` = definição formal de cada cluster.
  - Formato: Markdown com front-matter YAML; um conceito por arquivo.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  A organização de conhecimento do projeto será:

  `knowledge/business-dna/`
  - identidade do negócio;
  - estratégia;
  - monetização;
  - prioridades de métricas;
  - mercados;
  - idiomas;
  - DNA musical;
  - posicionamento.

  `knowledge/rules/`
  - compliance;
  - segurança;
  - copyright;
  - limites operacionais;
  - limites de autonomia;
  - outras restrições de execução.

  `knowledge/market/`
  - conhecimento de mercado acumulado;
  - sinais históricos;
  - aprendizados;
  - concorrentes;
  - oportunidades e contexto de mercado.

  `knowledge/clusters/`
  - definições formais de clusters;
  - regras e características dos clusters formalizados.

  `knowledge/inventories/`
  - artistas;
  - playlists;
  - páginas;
  - catálogo e demais ativos estruturados.

  O formato padrão de conhecimento será Markdown com front matter YAML quando metadados
  estruturados forem necessários.

---

## I7 — Papel de `data/` × `reports/`

- **Problema:** §9 descreve `knowledge/*` e Rule #6 separa "gerado" de "fonte", mas `data/`
  vs. `reports/` nunca é definido.
- **Por que isso importa:** sem contrato, dado descartável e entregável durável se misturam.
- **Decisão necessária:** definir o papel de cada diretório de saída.
- **Opções possíveis / Recomendação:**
  - `data/` = sinais brutos coletados + cache de pesquisa por run; descartável e
    regenerável; organizado por data de run.
  - `reports/` = Opportunity Reports + digest por run; append-only, versionado, com
    timestamp.
  - `knowledge/` = fonte da verdade, de propriedade humana.
  - Alternativa rejeitada: juntar tudo em `reports/` — mistura descartável com durável.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  `data/` será utilizado para:
  - sinais brutos;
  - caches;
  - dados intermediários;
  - dados regeneráveis;
  - artefatos temporários de execução.

  `reports/` será utilizado para:
  - Opportunity Reports;
  - digests das execuções;
  - resultados duráveis do workflow;
  - artefatos de análise que precisam ser preservados e versionados.

  `knowledge/` continuará sendo a fonte de verdade do negócio e das regras.

  Dados temporários ou regeneráveis não devem ser tratados como conhecimento-fonte.

---

## I8 — Um agente monolítico × pipeline de componentes

- **Problema:** §10 pede "componentes especializados a um agente gigante", mas §13 enquadra
  tudo como um único "Market Intelligence Agent" com um input e um output.
- **Por que isso importa:** define a forma da implementação, a testabilidade e a
  manutenibilidade.
- **Decisão necessária:** confirmar a forma da implementação (sem construir agora).
- **Opções possíveis:**
  - (a) Pipeline de passos pequenos: coleta de sinais → enquadramento → matching de ativos →
    avaliação → geração de relatório → ranking.
  - (b) Um único prompt/agente grande.
  - (c) Orquestrador + sub-agentes.
- **Recomendação:** (a). Código determinístico onde dá (matching, agregação, ranking,
  render); IA onde precisa (enquadramento, avaliação, redação). (c) é POSTERGÁVEL (ver P5).
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Market Intelligence V1 será implementado como um pipeline de componentes especializados,
  e não como um único prompt/agente monolítico.

  O fluxo conceitual será:

  1. coleta de sinais;
  2. normalização de sinais;
  3. análise/enquadramento;
  4. matching com ativos;
  5. avaliação;
  6. ranking/priorização;
  7. geração do Opportunity Report.

  Código determinístico deverá ser utilizado sempre que possível para processamento,
  normalização, matching, agregação, validação e ranking.

  IA deverá ser utilizada principalmente nas etapas que exigem pesquisa, interpretação,
  enquadramento, avaliação e síntese.

  A V1 não exigirá uma arquitetura multi-agente. A divisão em subagentes/orquestração
  avançada poderá ser introduzida posteriormente quando houver necessidade real.

---

## I9 — Dimensão de durabilidade / timing da tendência

- **Problema:** "trend strength" (§7) sozinho não distingue um som de TikTok de 2 semanas
  de uma mudança estrutural na demanda por conteúdo de sono.
- **Por que isso importa:** a estratégia é baseada em playlist, um ativo de longo prazo;
  perseguir moda passageira para dentro dela é caro e improdutivo.
- **Decisão necessária:** adicionar dimensão de durabilidade / janela ao modelo de
  avaliação.
- **Opções possíveis:**
  - (a) Nova dimensão "Durabilidade / janela de oportunidade" (evergreen ↔ efêmero) +
    "Urgência / timing".
  - (b) Sub-atributo dentro de "trend strength".
  - (c) Ignorar no V1.
- **Recomendação:** (a), incorporada à lista unificada do C9.
- **Quem precisa decidir:** Arquitetura + Proprietário (validação).
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Market Intelligence V1 deverá distinguir a durabilidade das oportunidades através de:

  - EPHEMERAL — oportunidade de curtíssima duração;
  - EMERGING — sinal de crescimento atual;
  - STRUCTURAL — demanda relativamente persistente;
  - EVERGREEN — necessidade recorrente e duradoura.

  A oportunidade também deverá possuir um campo separado de urgência:

  - LOW
  - MEDIUM
  - HIGH

  Durability e Urgency serão atributos de avaliação e contexto da oportunidade, e não regras
  automáticas que determinem isoladamente se uma oportunidade é boa ou ruim.

  O objetivo é diferenciar tendências rápidas de demandas mais persistentes e permitir que o
  sistema identifique diferentes tipos de valor, incluindo oportunidades de Music Trend /
  UGC e oportunidades de Playlist Growth.

---

## I10 — Stack técnico

- **Problema:** não há `package.json` nem `pyproject.toml`; linguagem, runtime, provedor de
  LLM e formato de persistência não escolhidos.
- **Por que isso importa:** bloqueia a implementação; a escolha errada custa retrabalho
  quando o motor de vídeo/áudio entrar.
- **Decisão necessária:** linguagem, runtime, provedor de LLM, formato de persistência.
- **Opções possíveis:**
  - (a) Python — forte em dados, scripting, scraping e ecossistema de trends.
  - (b) Node / TypeScript — bom se o motor de vídeo/edição vier em JS depois.
  - (c) Híbrido — Python para o Market Intelligence, decidir o resto depois.
- **Recomendação:** o Proprietário informa a direção de longo prazo do "media engine". Se
  indiferente: Python para o V1, LLM = Claude (modelo forte para raciocínio, modelo menor
  para extração), persistência em arquivos, sem banco / fila / servidor.
- **Quem precisa decidir:** Proprietário (direção de longo prazo) + Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  Stack técnico inicial do Market Intelligence V1:

  - Runtime: Python 3
  - LLM: Claude
  - Persistência: YAML + Markdown + JSON quando necessário
  - Controle de versão: Git
  - Ambiente de desenvolvimento: Claude Code + VS Code
  - Banco de dados: não utilizar no V1
  - Fila/servidor: não utilizar no V1
  - Arquitetura: pipeline modular de componentes especializados

  Princípio:
  usar código determinístico para coleta, normalização, validação, matching, agregação e
  ranking quando apropriado, e utilizar Claude principalmente nas etapas que exigem
  pesquisa, interpretação, enquadramento, avaliação e síntese.

  A arquitetura técnica poderá evoluir posteriormente conforme os requisitos dos estágios
  de produção, vídeo, áudio, publicação e analytics forem implementados.

---

## I11 — Metodologia de conteúdo existente

- **Problema:** §3 lista "existing content methodology" como ativo, mas não aponta onde está
  nem o que é.
- **Por que isso importa:** deveria alimentar as avaliações de "content potential" e a
  hipótese de "first content direction".
- **Decisão necessária:** localizar o material e transcrever o essencial para `knowledge/`.
- **Opções possíveis:** não é escolha — é captura.
- **Recomendação:** o Proprietário fornece o material (documento, notas, exemplos); vira
  `knowledge/business-dna/content-methodology.md`.
- **Quem precisa decidir:** Proprietário.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  A metodologia de conteúdo atual foi documentada em:
  `knowledge/business-dna/content-methodology.md`

  Ela deve ser tratada como conhecimento operacional histórico do negócio, não como um
  conjunto rígido de regras. O sistema deverá preservar os princípios que já demonstraram
  valor, mas possuir autonomia para propor e testar novas formas de conteúdo.

---

## I12 — Controle de volume / gargalo do operador

- **Problema:** §11 L1 = revisão humana de tudo. Se o agente emite 40 oportunidades por run,
  o humano não processa.
- **Por que isso importa:** o valor do sistema colapsa se a saída não cabe na capacidade de
  revisão e execução.
- **Decisão necessária:** disciplina de volume + estado para oportunidades boas sem
  capacidade agora.
- **Opções possíveis:**
  - (a) Top-N fixo por run (ex.: 10) + estado `PARK` / `HOLD`.
  - (b) Sem limite; o humano filtra.
  - (c) Limite dinâmico baseado na capacidade declarada do operador.
- **Recomendação:** (a), com N e a capacidade real informados pelo Proprietário (liga a
  C10).
- **Quem precisa decidir:** Proprietário (capacidade) + Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-08-27.

  O Market Intelligence V1 apresentará no máximo 10 oportunidades priorizadas por execução.

  O pipeline poderá identificar e manter oportunidades adicionais internamente, mas somente
  o conjunto priorizado deverá ser apresentado ao proprietário como resultado principal do
  run.

  O estado PARK será utilizado para oportunidades consideradas boas, mas que não devam
  ocupar a capacidade de atenção ou execução naquele momento.

  O limite de 10 oportunidades está alinhado ao Definition of Done do V1 definido em C10.

  O V1 deverá evitar gerar volume excessivo de oportunidades que ultrapasse a capacidade
  real de revisão do operador.

---

# 3. POSTERGÁVEL

Legítimo deixar para depois da validação do V1. Registrar a intenção; não bloqueia nada
agora.

---

## P1 — Loop de calibração do score com dados reais

- **Problema:** §7 quer calibrar o score com resultados reais; não há ingestão de
  performance nem publicação no V1.
- **Por que isso importa:** o score do V1 é inerentemente não calibrado; a melhoria
  contínua depende deste loop.
- **Decisão necessária (ao sair do V1):** como ingerir performance (Spotify for Artists,
  APIs de social) e realimentar pesos e âncoras.
- **Opções possíveis:** manual (planilha) → semi-automático → API.
- **Recomendação:** começar manual quando os primeiros testes reais existirem; revisitar ao
  fim do V1.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

---

## P2 — Transições automáticas / autonomia L2–L3

- **Problema:** §11 prevê níveis de autonomia; §8 tem estados de ciclo de vida.
- **Por que isso importa:** autonomia sem confiabilidade demonstrada é risco operacional.
- **Decisão necessária:** quando e sob quais regras subir de L1.
- **Opções possíveis:** manter L1; L2 para ações reversíveis; L3 só sob regras explícitas.
- **Recomendação:** manter L1 até o V1 passar em C10 por vários runs consecutivos.
- **Quem precisa decidir:** Proprietário.
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

---

## P3 — Integrações de dados em tempo real / APIs pagas

- **Problema:** §6 lista muitas fontes; C2 define só o mínimo do V1.
- **Por que isso importa:** mais cobertura de sinal melhora a qualidade, mas adiciona custo
  e complexidade.
- **Decisão necessária:** quais APIs adicionais integrar e em que ordem.
- **Opções possíveis:** priorizar por cluster e por mercado, atrás do schema `Signal`.
- **Recomendação:** escalar só depois de o V1 provar valor com o conjunto mínimo.
- **Quem precisa decidir:** Proprietário (orçamento) + Arquitetura.
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

---

## P4 — Estágios seguintes do pipeline

- **Problema:** §15 tem Cluster Strategy, Page Blueprint, Content Strategy, Content
  Production, Video/Audio Engine, QC, Publishing.
- **Por que isso importa:** §12 proíbe explicitamente construí-los agora.
- **Decisão necessária:** sequência e escopo de cada estágio — quando o V1 estiver validado.
- **Opções possíveis:** definir na revisão pós-V1.
- **Recomendação:** não abrir antes de C10 ser atendido.
- **Quem precisa decidir:** Proprietário.
- **Status:** DEFERRED (2026-08-27) — estágios 3 (Cluster Strategy) e 4 (Page Blueprint) abertos 2026-09-01 / 2026-09-04 (ver D-CS-1, D-PB-1); estágios 5–13 seguem DEFERRED
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

  **Atualização (2026-09-01):** o gate C10 foi atendido e registrado (ver C10; 3 runs
  consecutivos com `review.md` do proprietário; commit `39fe464`). O proprietário do
  negócio (Nicolas Alves) autorizou a abertura do **estágio 3 — Cluster Strategy** do
  pipeline canônico (C8), e somente dele. Ver a seção "# 4. ESTÁGIO 3 — CLUSTER STRATEGY"
  (D-CS-1 … D-CS-12) e o contrato `docs/CLUSTER-STRATEGY-V1.md`. Os estágios 4–13 (Page
  Blueprint, Content Strategy, Content Production, Video Engine, Audio Engine, Quality
  Control, Publishing, Analytics, Optimization, Learning) permanecem DEFERRED sob esta P4 e
  serão revisitados na revisão pós-V1, quando aplicável.

  **Atualização (2026-09-04):** o proprietário do negócio (Nicolas Alves) autorizou a
  abertura do **estágio 4 — Page Blueprint** do pipeline canônico (C8), e somente dele
  ("equivalente ao padrão D-CS-1"). Ver a seção "# 6. ESTÁGIO 4 — PAGE BLUEPRINT"
  (D-PB-1 … D-PB-12) e o contrato `docs/PAGE-BLUEPRINT-V1.md`. Os estágios 5–13 (Content
  Strategy, Content Production, Video Engine, Audio Engine, Quality Control, Publishing,
  Analytics, Optimization, Learning) permanecem DEFERRED sob esta P4 e serão revisitados
  na revisão pós-V1, quando aplicável.

---

## P5 — Orquestração multi-agente

- **Problema:** com vários estágios implementados, será preciso coordená-los.
- **Por que isso importa:** complexidade de orquestração antes de haver o que orquestrar é
  desperdício (§10).
- **Decisão necessária:** modelo de orquestração entre estágios.
- **Opções possíveis:** orquestrador central; eventos; execução manual encadeada.
- **Recomendação:** decidir quando existir o segundo estágio; depende de I8.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

---

## P6 — Governança de criação de cluster novo

- **Problema:** §2 e §6 dizem que o sistema deve descobrir clusters novos, sem fluxo de
  aprovação/definição.
- **Por que isso importa:** um cluster novo é uma decisão estratégica, não um output
  automático.
- **Decisão necessária:** fluxo formal de proposta → aprovação → definição de cluster.
- **Opções possíveis:** no V1, o agente apenas propõe cluster novo como hipótese dentro de
  um relatório; a formalização vem depois.
- **Recomendação:** V1 = só proposta; governança formal DEFERRED.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

---

## P7 — Dashboards / tracking de tendências entre runs

- **Problema:** não há visão da evolução de sinais e oportunidades ao longo do tempo.
- **Por que isso importa:** útil para enxergar tração, mas não bloqueia o V1.
- **Decisão necessária:** formato de acompanhamento longitudinal.
- **Opções possíveis:** digest por run agora; dashboard depois.
- **Recomendação:** só digests append-only no V1.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

---

## P8 — Versionamento de prompts / reprodutibilidade de output do LLM

- **Problema:** um sistema que "aprende" e compara ao longo do tempo precisa saber com qual
  prompt/modelo cada relatório foi gerado.
- **Por que isso importa:** sem isso, comparações entre runs são ruído.
- **Decisão necessária:** como versionar prompts e registrar modelo/versão por run.
- **Opções possíveis:** no V1, registrar data + fontes + versão do prompt no digest do run;
  infraestrutura dedicada depois.
- **Recomendação:** registro leve no V1; infraestrutura DEFERRED.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

---

## P9 — Conjunto de referência de concorrentes por cluster

- **Problema:** as dimensões "competition" e "differentiation" precisam de um conjunto de
  concorrentes; não existe.
- **Por que isso importa:** melhora a consistência da avaliação, mas o LLM consegue
  identificar concorrentes on-the-fly no V1.
- **Decisão necessária:** consolidar perfis de concorrentes em `knowledge/market/`.
- **Opções possíveis:** identificação ad-hoc por run agora; base curada depois.
- **Recomendação:** ad-hoc com confiança marcada no V1; consolidação DEFERRED.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

---

## P10 — Reconciliação textual completa do pipeline no CLAUDE.md

- **Problema:** §1 e §15 divergem; C8 resolve só o necessário para o V1.
- **Por que isso importa:** o `CLAUDE.md` deve ficar internamente consistente, mas isso é
  uma edição de documento, não um bloqueio de engenharia.
- **Decisão necessária:** revisão editorial do `CLAUDE.md` para uma única formulação do
  pipeline e demais inconsistências (C5, C7, C9).
- **Opções possíveis:** revisão dedicada do documento após as decisões CRÍTICAS.
- **Recomendação:** agendar uma revisão do `CLAUDE.md` depois que C1–C10 estiverem
  `DECIDED`; não editar antes.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-08-27)
- **Resultado:**

  A reconciliação do CLAUDE.md foi concluída após as decisões C1–C10 e I1–I12.

  O documento foi revisado e alinhado às decisões formalizadas, incluindo:
  - pipeline canônico;
  - definição de oportunidade;
  - fontes de sinal;
  - avaliação;
  - Business Outcome Profile;
  - escopo do Market Intelligence V1;
  - inventários;
  - organização de conhecimento;
  - stack técnico;
  - guardrails;
  - Definition of Done.

  As decisões detalhadas e seu histórico permanecem registradas em
  `knowledge/DECISIONS-NEEDED.md`.

---

# 4. ESTÁGIO 3 — CLUSTER STRATEGY

As decisões **D-CS-1 a D-CS-12** foram tomadas pelo proprietário do negócio (Nicolas
Alves) em **2026-09-01**, depois que o gate C10 foi atendido e registrado (ver C10; 3 runs
consecutivos com `review.md` do proprietário; commit `39fe464`). Elas abrem e delimitam o
**estágio 3 do pipeline canônico (C8) — Cluster Strategy** — e somente ele; os estágios
4–13 permanecem DEFERRED sob a P4.

O contrato completo do estágio está em `docs/CLUSTER-STRATEGY-V1.md`. Onde este arquivo e
uma decisão DECIDED (C1–C10 / I1–I12) divergirem, a decisão prevalece.

## D-CS-1 — Abertura do estágio 3 (Cluster Strategy)

- **Problema:** a P4 mantém os estágios 3–13 como DEFERRED; construir o Cluster Strategy
  depende de uma decisão explícita do proprietário para abrir o estágio.
- **Por que isso importa:** abrir um estágio postergável sem autorização registrada quebra
  a ordem de autoridade (`DECISIONS-NEEDED.md` > spec > `CLAUDE.md`).
- **Decisão necessária:** autorizar a abertura do estágio 3 — e somente dele — agora que o
  gate C10 foi atendido.
- **Opções possíveis:**
  - (a) abrir apenas o estágio 3;
  - (b) abrir os estágios 3–5 em conjunto;
  - (c) manter tudo DEFERRED até uma revisão pós-V1 mais ampla.
- **Recomendação:** (a). Escopo restrito ao Cluster Strategy; os estágios 4–13 seguem
  DEFERRED sob a P4.
- **Quem precisa decidir:** Proprietário.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  O gate C10 foi atendido e registrado (ver C10; commit `39fe464`). O **estágio 3 (Cluster
  Strategy)** do pipeline canônico (C8) está aberto para implementação. Somente o estágio 3
  é aberto; os estágios 4–13 (Page Blueprint, Content Strategy, Content Production, Video
  Engine, Audio Engine, Quality Control, Publishing, Analytics, Optimization, Learning)
  permanecem DEFERRED sob a P4. A implementação segue o contrato `docs/CLUSTER-STRATEGY-V1.md`
  e as decisões D-CS-2 … D-CS-12 abaixo. A autonomia permanece no Nível 1 (o sistema
  recomenda; o humano aprova e executa).

## D-CS-2 — Governança de cluster novo no estágio 3 (relação com P6)

- **Problema:** o Cluster Strategy pode concluir que uma oportunidade não cabe em nenhum
  cluster canônico; a formalização de um cluster novo é decisão estratégica (P6), ainda
  DEFERRED.
- **Por que isso importa:** uma oportunidade `proposed_new` não pode avançar plenamente se
  o estágio só propuser e nunca formalizar.
- **Decisão necessária:** o estágio 3 abre a governança formal de cluster novo (P6) ou
  permanece "apenas proposta"?
- **Opções possíveis:**
  - (a) manter P6 DEFERRED; o estágio 3 apenas propõe;
  - (b) abrir P6 junto com o estágio 3.
- **Recomendação:** (a).
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  A P6 permanece DEFERRED. O Cluster Strategy apenas **propõe** um cluster novo — hipótese +
  fronteira conceitual vs. clusters adjacentes + evidência + nota fixa de governança — e
  nunca edita `knowledge/clusters/cluster-taxonomy.md`. A formalização de um cluster
  canônico continua sendo edição manual do proprietário. Oportunidades nessa situação
  recebem `cluster_decision = DEFER` e `target_next_stage = FORMALIZE_CLUSTER` até que o
  proprietário formalize.

## D-CS-3 — Gatilho de entrada no Cluster Strategy

- **Problema:** nem o spec nem o Business DNA V1 definem como uma oportunidade é encaminhada
  ao estágio 3.
- **Por que isso importa:** a autonomia L1 e o controle de volume (I12) implicam seleção
  humana; sem um gatilho explícito o estágio pode rodar em lote.
- **Decisão necessária:** quais oportunidades entram no Cluster Strategy e como o estágio é
  invocado.
- **Opções possíveis:**
  - (a) CLI explícita, por oportunidade, invocada pelo proprietário;
  - (b) execução automática sobre todo o Top-10 de um run;
  - (c) execução em lote sob regras.
- **Recomendação:** (a).
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  Gatilho explícito, por oportunidade, invocado pelo proprietário via CLI
  (`python -m cluster_strategy reports/<run_id>/<opportunity_id>.json`). O estágio recusa a
  execução se a oportunidade não for a `advanced_opportunity_id` do `review.md` daquele run.
  Não há execução automática nem em lote (autonomia L1; I12).

## D-CS-4 — Dimensões do Cluster Strategy e ausência de `status` persistente

- **Problema:** o C9 fixa as 10 dimensões de avaliação *da oportunidade*; não há lista
  decidida para uma estratégia de cluster.
- **Por que isso importa:** sem um conjunto fixo, cada run pode inventar dimensões
  diferentes.
- **Decisão necessária:** o conjunto exato de dimensões do Cluster Strategy e se o estágio
  tem um `status` persistente por estratégia.
- **Opções possíveis:** conjunto ad hoc por run; conjunto fixo de 3–4 dimensões; reaproveitar
  as 10 do C9.
- **Recomendação:** conjunto fixo de 4 dimensões qualitativas; sem `status` persistente.
- **Quem precisa decidir:** Arquitetura + Proprietário.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  As 4 dimensões do Cluster Strategy são: `cluster_fit`, `differentiation_within_cluster`,
  `asset_readiness`, `strategic_coherence`. Cada uma tem um rating qualitativo
  (`LOW`/`MEDIUM`/`HIGH`/`VERY_HIGH`) e uma **confiança separada** (`LOW`/`MEDIUM`/`HIGH`) —
  sem score 0–100 (C6). O estágio **não** tem campo `status` persistente: uma reexecução
  sobrescreve `reports/cluster-strategy/<opportunity_id>.*` (idempotente; ver I9).

## D-CS-5 — Profundidade da direção de conteúdo no estágio 3

- **Problema:** o Business DNA V1 §11 lista pilares, estética e CTA como saídas de "Cluster
  Strategy"; o C8 e o `cluster-taxonomy.md` colocam isso nos estágios 4–5.
- **Por que isso importa:** divergência direta de documento; sem fronteira, o estágio 3
  invade os estágios 4 e 5.
- **Decisão necessária:** o quanto de direção de conteúdo o estágio 3 produz.
- **Opções possíveis:** rasa (uma direção + ângulos + papel da música); média (+ pilares);
  ampla (tudo do §11 literal).
- **Recomendação:** rasa.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  O Cluster Strategy produz apenas: uma `first_content_direction` não vinculante (hipótese),
  uma lista curta de `editorial_angles` (hipóteses, táticas) e um enunciado de papel em
  `music_relationship`. Pilares, formatos, hooks, estruturas, CTAs, regras
  linguísticas/visuais, cadência, lotes e templates são Content Strategy (estágio 5) / Page
  Blueprint (estágio 4). Consistente com o C7 e com o I11.

## D-CS-6 — Local de saída e digest do estágio 3

- **Problema:** o I7 diz que `reports/` é durável; o caminho exato do estágio 3 e a
  existência de um digest por run não estavam definidos.
- **Por que isso importa:** afeta a reprodutibilidade e a organização de `reports/`.
- **Decisão necessária:** onde o Cluster Strategy escreve e se emite um digest.
- **Opções possíveis:** `reports/cluster-strategy/<opportunity_id>.*`;
  `reports/<opportunity_run_id>/cluster-strategy/`; com ou sem digest.
- **Recomendação:** `reports/cluster-strategy/<opportunity_id>.{md,json}`; sem digest no V1
  do estágio 3.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  O estágio 3 escreve `reports/cluster-strategy/<opportunity_id>.md` e `.json` (I7). Sem
  digest por run no V1 do estágio 3 (uma oportunidade por vez); o relatório é a entrega. O
  sidecar `.json` é o contrato de entrada do futuro Page Blueprint (estágio 4).

## D-CS-7 — Vínculo com `opportunity-registry.yaml`

- **Problema:** o registro é uma exceção de governança (spec §17), append-only e revisado
  por humanos; acrescentar um `cluster_strategy_ref` é uma extensão de schema.
- **Por que isso importa:** a exceção do §17 foi escrita para o pipeline do Market
  Intelligence, não para um pacote novo do estágio 3.
- **Decisão necessária:** o Cluster Strategy toca `knowledge/market/opportunity-registry.yaml`?
- **Opções possíveis:**
  - (a) opcional, desligado por padrão: quando habilitado, acrescenta `cluster_strategy_ref`
    + uma nota em `state_history`;
  - (b) sempre acrescenta;
  - (c) nunca toca o registro — tudo fica em `reports/`.
- **Recomendação:** (a).
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  Opcional e **desligado por padrão** (`write_registry_link: false` em `ClusterStrategyConfig`
  e na config de exemplo). Um run normal ou offline **não** toca `knowledge/`. Quando
  `write_registry_link: true` for explicitamente habilitado, o estágio 3 acrescenta à
  entrada da oportunidade: o campo `cluster_strategy_ref` e uma nota em `state_history`
  (`by: system`, `status` inalterado — o ciclo de vida é carregado, nunca transicionado). A
  operação usa o mesmo mecanismo append-only de `market_intelligence.registry`: entradas
  existentes mantêm a ordem, cada mudança aparece no `git diff`, a reexecução é idempotente.
  O Technical Spec V1 §17 foi reconciliado em 2026-09-01 para permitir explicitamente este
  append de estágio 3 quando o vínculo com o registro estiver habilitado.

## D-CS-8 — Fronteira do estágio 3 vs Business DNA V1 §11

- **Problema:** o Business DNA V1 §11 coloca *linguagem, estética, conteúdo e CTA* em
  "Cluster Strategy"; a arquitetura V1 estabelecida coloca isso nos estágios 4–5.
  Divergência direta de documento, não uma lacuna.
- **Por que isso importa:** determina o que o estágio 3 entrega e o que ele deixa para os
  estágios seguintes.
- **Decisão necessária:** confirmar a fronteira do estágio 3.
- **Opções possíveis:** seguir o Business DNA V1 §11 literal; confirmar a fronteira V1
  estabelecida.
- **Recomendação:** confirmar a fronteira V1 estabelecida.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  Cluster Strategy = conceito do cluster + audiência + intenção + estado emocional +
  posicionamento + relação com música/playlist + **uma** direção de conteúdo não vinculante.
  Tudo o que o Business DNA V1 §11 lista além disso (identidade visual, tom de voz, pilares,
  formatos, hooks, CTAs, cadência) é estágio 4 (Page Blueprint) ou estágio 5 (Content
  Strategy). O `AI Music Media Engine — Business DNA V1.md` é documento de visão estratégica
  e não supersede as decisões DECIDED (C6, I2, C7–C8, I4).

## D-CS-9 — Rodar o estágio 3 com DNA musical `NEEDS_INPUT`

- **Problema:** o detalhe do DNA musical (`business-dna.md` §9) está `NEEDS_INPUT`; isso
  limita estruturalmente a confiança de `music_relationship` e `market_language_fit`.
- **Por que isso importa:** o estágio 3 precisa rodar mesmo sem esse detalhe.
- **Decisão necessária:** `NEEDS_INPUT` no DNA musical é estado aceitável para o Cluster
  Strategy rodar?
- **Opções possíveis:** rodar com teto de confiança; bloquear até o DNA musical ser
  fornecido.
- **Recomendação:** rodar com teto de confiança.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  Aceitável. O estágio roda com a confiança de `music_relationship` e `market_language_fit`
  limitada a ≤ MEDIUM e uma nota `blocked_by`, do mesmo modo que o pipeline limita
  `music_fit`. O Cluster Strategy nomeia *o que* precisaria de detalhe de DNA musical, sem
  inventá-lo (G10; spec §15).

## D-CS-10 — Ponderação de "value engine" no estágio 3

- **Problema:** a ponderação entre motores de valor segue `NEEDS_INPUT` (`business-dna.md`
  §4; `config/ranking.yaml: value_engine_weighting: NEEDS_INPUT`).
- **Por que isso importa:** se o Cluster Strategy priorizasse vários ângulos, precisaria de
  uma regra.
- **Decisão necessária:** o estágio 3 prioriza múltiplos ângulos/estratégias?
- **Opções possíveis:** não priorizar; priorizar ordinalmente; priorizar com pesos.
- **Recomendação:** não priorizar no V1 do estágio 3.
- **Quem precisa decidir:** Arquitetura + Proprietário.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  O V1 do estágio 3 não prioriza: uma oportunidade entra, uma estratégia sai. Se priorização
  multi-ângulo for adicionada depois, permanece ordinal (C6) até o proprietário fornecer a
  ponderação. Sem dependência da P1.

## D-CS-11 — Tratamento de `schema_version` do contrato

- **Problema:** o `schema_version` do Opportunity Report é `1.0.0`; o comportamento diante
  de um valor futuro diferente não estava definido.
- **Por que isso importa:** adivinhar um schema desconhecido corrompe a entrada
  silenciosamente.
- **Decisão necessária:** o que o estágio 3 faz diante de um `schema_version` diferente de
  `1.0.0`.
- **Opções possíveis:** tentar decodificar mesmo assim; falhar imediatamente.
- **Recomendação:** falhar imediatamente (hard-fail).
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  O Cluster Strategy fixa `schema_version == 1.0.0` e faz **hard-fail** diante de qualquer
  outro valor — no Opportunity Report de entrada e no `ClusterStrategy` montado — surfando a
  divergência (Regra de Engenharia 9) em vez de adivinhar.

## D-CS-12 — Reconciliação de nomes do pipeline

- **Problema:** o Business DNA V1 (§5/§28) usa "Opportunity Discovery" / "Cluster Strategist"
  / "Distribution"; o C8 usa "Opportunity Analysis" / "Cluster Strategy" / "Publishing".
- **Por que isso importa:** afeta a nomeação de componentes e a comunicação; é divergência
  menor, não bloqueante.
- **Decisão necessária:** qual conjunto de nomes usar no estágio 3.
- **Opções possíveis:** nomes do Business DNA V1; nomes canônicos do C8.
- **Recomendação:** nomes canônicos do C8.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-09-01)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-01.

  Usar os nomes canônicos do C8 (`Cluster Strategy`, estágio 3). As divergências de nome do
  Business DNA V1 ficam anotadas, sem edição de documento — mesmo tratamento dado ao C8 (ver
  P10).

---

# 5. GATEWAY EXTERNO DE LLM (OMR)

A decisão **OMR-01** trata da criação de um adaptador externo e opcional de LLM (gateway
OpenAI-compatible via OmniRoute), sem substituir o Claude/Anthropic como stack padrão
(I10) e sem alterar nenhum estágio do pipeline canônico (C8). **Aprovada em 2026-09-04
somente para o adapter isolado** (ver Resultado abaixo) — a integração desse adapter com
qualquer estágio do pipeline continua exigindo uma decisão própria, ainda não tomada. O
comportamento "Claude only" (I10, CLAUDE.md §12) permanece integralmente em vigor.

## OMR-01 — External LLM Gateway — isolated adapter

- **Problema:** o OmniRoute (`http://localhost:20128/v1`, gateway local OpenAI-compatible)
  foi validado isoladamente, fora do projeto: o caminho OmniRoute → Groq →
  `groq/openai/gpt-oss-120b` respondeu HTTP 200 com resultado válido; OmniRoute → Cerebras
  alcançou o provider e recebeu HTTP 402 (billing); OmniRoute → Gemini alcançou o provider,
  mas os testes encontraram indisponibilidade de modelo, sobrecarga e timeout local do
  OmniRoute. Esses testes foram pontuais, isolados, e não alteraram nenhum arquivo do
  projeto. Isso levanta a questão de se o projeto deveria ter, no futuro, uma via opcional
  para chamar modelos externos através do OmniRoute, sem comprometer o stack atual.
- **Por que isso importa:** o stack técnico (I10) e o comportamento "Claude only" descrito no
  CLAUDE.md §12 são decisão de arquitetura vigente; introduzir qualquer capacidade de chamar
  outro provider — mesmo isolada e opcional — é uma mudança de arquitetura e precisa de
  registro explícito (Regra de Engenharia #7/#8), não de um efeito colateral de uma tarefa de
  teste ou de implementação silenciosa.
- **Decisão necessária:** autorizar (ou não) a criação futura de um adapter externo e
  opcional em `src/external_llm_gateway/`, usando o contrato já existente
  `market_intelligence.llm_stage.StageClient`, sem substituir o Claude e sem alterar o
  comportamento padrão "Claude only".
- **Opções possíveis:**
  - (a) autorizar a criação futura do adapter isolado, com o escopo, os não-objetivos e os
    princípios descritos abaixo — mas sem implementá-lo nesta decisão;
  - (b) não autorizar; manter o stack "Claude only" sem exceção alguma;
  - (c) adiar a decisão (DEFERRED) até haver um caso de uso concreto que precise de um
    provider externo.
- **Recomendação:** (a), com o escopo restrito a seguir. A criação do código em si permanece
  uma etapa separada e futura, condicionada a esta decisão estar `DECIDED` antes de qualquer
  arquivo ser criado.

  **Escopo proposto do OMR-01** (menor conjunto de arquivos, todos novos — nenhum arquivo
  existente seria modificado):
  - `src/external_llm_gateway/__init__.py`
  - `src/external_llm_gateway/config.py`
  - `src/external_llm_gateway/omniroute_client.py`
  - `tests/test_external_llm_gateway_omniroute_client.py`
  - `docs/EXTERNAL-LLM-GATEWAY.md`

  **Não-objetivos:**
  - não substituir Anthropic/Claude;
  - não alterar o Claude Code;
  - não alterar a configuração da conta Claude Pro;
  - não alterar `RunConfig.model`;
  - não alterar `ReplayConfig`;
  - não ligar nenhum stage ao OmniRoute por padrão;
  - não alterar Market Intelligence;
  - não alterar Cluster Strategy;
  - não alterar Musical DNA;
  - não alterar Value Engine;
  - não adicionar fallback automático;
  - não introduzir roteamento de modelos em produção;
  - não adicionar dependências sem decisão explícita.

  **Princípios:**
  - Claude continua sendo o caminho padrão;
  - OmniRoute é somente uma capacidade externa opcional;
  - o adapter deve ser desacoplado dos stages;
  - qualquer ligação futura de um stage ao adapter exige uma nova decisão explícita;
  - testes de CI devem ser determinísticos e não depender de OmniRoute ou rede real;
  - credenciais nunca devem ser gravadas no repositório;
  - erros externos devem permanecer distinguíveis de estados de negócio (spec §14).
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  Aprovada **somente** a opção (a) restrita ao adapter isolado, exatamente no escopo
  proposto — nenhuma integração do OmniRoute com o pipeline canônico foi aprovada.

  Implementados em 2026-09-04, exatamente os 5 arquivos do escopo: `src/external_llm_gateway/__init__.py`,
  `src/external_llm_gateway/config.py`, `src/external_llm_gateway/omniroute_client.py`,
  `tests/test_external_llm_gateway_omniroute_client.py` e `docs/EXTERNAL-LLM-GATEWAY.md`.
  `OmniRouteStageClient` implementa `market_intelligence.llm_stage.StageClient`; a
  dependência corre em um único sentido (`external_llm_gateway → market_intelligence.llm_stage`).
  Nenhum stage, `select_*_client()`, arquivo do pipeline canônico, `src/cluster_strategy/`,
  Musical DNA (`business-dna.md` §9), value-engine weighting ou `CLAUDE.md` foi alterado.

  650 testes verdes (629 pré-existentes + 21 novos, transporte HTTP mockado, sem rede real
  e sem depender do OmniRoute estar rodando), `ruff check src tests` limpo.

  Ligar este adapter a qualquer estágio do pipeline continua exigindo uma nova decisão
  explícita, registrada neste arquivo, antes de qualquer código de integração ser escrito.

---

## OMR-02 — External Model Use Cases & Routing Policy

- **Problema:** OMR-01 provou que o adapter isolado (`external_llm_gateway`) funciona
  tecnicamente — conectividade real, validada em teste live, contra OmniRoute → Groq →
  `openai/gpt-oss-120b` (HTTP 200, `dict` válido pelo contrato `StageClient`). Isso não
  responde a uma pergunta diferente e anterior a qualquer conexão real: em quais tarefas,
  se alguma, um modelo externo pode gerar vantagem real sem comprometer qualidade,
  compliance, determinismo ou o comportamento "Claude only" (I10)? Sem uma política
  explícita, a tentação natural é conectar modelos externos onde estão disponíveis, não
  onde fazem sentido.
- **Por que isso importa:** o pipeline mistura tarefas de risco muito diferente — de
  classificação fechada de baixo risco (Signal Normalization) a decisão de negócio com
  compliance embutido (Evaluation) e um estágio formalmente congelado (Cluster Strategy,
  D-CS-1…12). Tratar todas essas tarefas com a mesma régua de "modelo disponível = usar"
  seria uma mudança de arquitetura silenciosa e desproporcional ao risco de cada uma
  (Regra de Engenharia #7/#8).
- **Decisão necessária:** adotar (ou não) uma política de routing entre Claude e modelos
  externos, definida por tarefa e por risco, antes de qualquer integração real de
  `external_llm_gateway` a um stage.
- **Opções possíveis:**
  - (a) adotar a política restritiva descrita na Recomendação — Claude obrigatório nas
    tarefas de maior risco/complexidade/capability, benchmark formal obrigatório antes de
    qualquer uso de produção, Signal Normalization como único candidato primário;
  - (b) permitir uso mais amplo de modelos externos, sem benchmark formal prévio, guiado
    só por custo/disponibilidade;
  - (c) não definir política agora; decidir caso a caso, sem registro.
- **Recomendação:** (a), com o conteúdo a seguir.

  **Princípio central:**
  - Claude/Anthropic continua sendo o LLM padrão do AI Music Media Engine.
  - Nenhum modelo externo pode substituir silenciosamente Claude em qualquer estágio do
    pipeline.

  **Condições para uso de um modelo externo em produção** — todas obrigatórias:
  - benchmark formal da tarefa;
  - critérios de qualidade previamente definidos;
  - aprovação explícita do proprietário;
  - decisão registrada;
  - integração deliberada e opt-in.

  **Tarefas que permanecem Claude-only nesta fase:**
  - **Web Search** — depende da capacidade nativa `web_search` da Anthropic, não
    equivalente a uma chamada chat OpenAI-compatible.
  - **Framing** — alta complexidade, risco de propagação de erro a jusante e necessidade
    de saída estruturada grande ainda não validada externamente.
  - **Evaluation** — explicitamente Claude-only nesta fase: papel de decisão central,
    compliance (G01–G10) e risco máximo.
  - **Cluster Strategy** — formalmente `frozen/closed` pelas decisões D-CS-1…12
    existentes; trocar o client desse estágio reabriria uma decisão D-CS, fora de escopo
    de qualquer OMR.

  **Candidatos a benchmark externo:**
  - **Signal Normalization** — aprovado como **primeiro** candidato a benchmark externo.
  - **Asset Matching** — aprovado apenas como candidato **secundário e condicional**, a
    ser considerado somente depois da validação de Normalization.

  **Estado técnico atual (contexto, não justificativa automática de escolha de provider):**
  - O único caminho externo atualmente comprovado tecnicamente é OmniRoute → Groq →
    `openai/gpt-oss-120b`. Isso prova **conectividade**, não qualidade.
  - Os testes de conectividade do OMR-01 **não** contam como benchmark de qualidade.

  **Segunda opinião externa:** qualquer uso futuro deverá inicialmente ser
  consultivo/sombra e **nunca decisório** — nunca compõe `Evaluation`/`Recommendation`.

  **Garantias técnicas a preservar em qualquer uso futuro de modelo externo em stage
  real:**
  - `StageError` / `ResponseRejected` (o mesmo par de erros que `StageClient` já define);
  - a distinção entre falha técnica e estado de negócio (spec §14);
  - replay/determinismo (spec §22);
  - fixtures gravadas (uma contraparte `RecordedXClient`, hoje inexistente para
    `OmniRouteStageClient` — ver `docs/EXTERNAL-LLM-GATEWAY.md` §10);
  - ausência de dependência de rede real no CI.

  **Não-objetivos desta decisão:**
  - não altera `RunConfig.model`;
  - não altera `ReplayConfig`;
  - não altera nenhum stage.

  **Próximo milestone:** **OMR-03 — Normalization Benchmark Harness** (isolado, offline,
  sem integração com `market_intelligence/normalize/`).

  **Critério para o futuro benchmark (OMR-03) — NÃO decidido agora:** não fica registrado
  como regra que "concordância com Claude = qualidade". O OMR-03 deverá comparar Claude e
  o candidato externo usando critérios objetivos da tarefa, incluindo pelo menos:
  validade estrutural; aderência à taxonomia/enums; preservação dos valores corretos;
  taxa de divergência; casos em que ambos divergem de uma referência válida, quando essa
  referência puder ser estabelecida; custo; latência; comportamento de erro. Os critérios
  e limiares finais de aprovação do benchmark permanecem em aberto — são uma decisão
  própria, a ser registrada antes da implementação/execução do OMR-03.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  Aprovada a opção (a) integralmente, exatamente no conteúdo descrito em Recomendação.
  Claude/Anthropic permanece o LLM padrão; nenhum modelo externo pode substituir Claude
  silenciosamente em qualquer estágio. Web Search, Framing, Evaluation e Cluster Strategy
  permanecem Claude-only nesta fase, pelos motivos registrados acima. Signal Normalization
  é o primeiro candidato a benchmark externo; Asset Matching é candidato secundário e
  condicional, só após Normalization ser validado.

  Confirmado que o único caminho externo tecnicamente comprovado (OmniRoute → Groq →
  `openai/gpt-oss-120b`, OMR-01) prova conectividade, não qualidade, e que os testes de
  conectividade do OMR-01 não substituem um benchmark formal.

  Os critérios e limiares de aprovação de qualidade do benchmark **não** foram decididos
  nesta decisão — ficam explicitamente para uma decisão própria, antes de qualquer
  implementação ou execução do OMR-03.

  Nenhum stage, `RunConfig.model`, `ReplayConfig`, arquivo do pipeline canônico,
  `src/cluster_strategy/`, Musical DNA ou value-engine weighting foi alterado por esta
  decisão. O próximo milestone é **OMR-03 — Normalization Benchmark Harness**, ainda não
  implementado.

---

## OMR-03 — Normalization Benchmark: Threshold Policy V1

- **Problema:** a especificação conceitual do OMR-03 (critérios de aceitação do
  Normalization Benchmark) definiu QUE tipo de critérios seriam necessários, mas deixou
  os valores numéricos como proposta técnica em aberto — deliberadamente, para evitar
  escolher limiares depois de ver resultados. Sem travar esses valores antes de qualquer
  execução, um benchmark futuro correria o risco de ter seus critérios ajustados depois
  do resultado, o que anularia o propósito de um pré-registro.
- **Por que isso importa:** OMR-02 já exige que qualquer uso de modelo externo em
  produção passe por "benchmark formal" e "critérios de qualidade previamente definidos"
  (OMR-02, condições para uso em produção) — sem uma política de limiares travada, essa
  condição não é verificável.
- **Decisão necessária:** fixar a política V1 de limiares de aprovação do Normalization
  Benchmark — hard gates, accuracy mínima por campo, tratamento de degradação/melhoria,
  indetermináveis, divergência, custo, latência e contagem absoluta de erros — como
  pré-registro, antes de qualquer dataset, harness ou chamada real.
- **Opções possíveis:**
  - (a) política **BALANCEADA** — hard gates inegociáveis + limiares por campo
    moderados + estrutura de 2 fases para custo (qualidade antes de custo);
  - (b) política **CONSERVADORA** — limiares muito altos, risco de nunca aprovar nenhum
    candidato;
  - (c) política **ECONÔMICA** — limiares mais baixos, maior peso de custo, maior risco
    de corrupção semântica silenciosa em volume alto.
- **Recomendação:** (a) — adotada integralmente como segue.

  **1. Política geral:** **BALANCEADA**.

  **2. Hard gates** (obrigatórios, zero-tolerance):
  - zero violação de fronteira de campo/contrato;
  - zero invenção de fatos/evidências na `rationale`;
  - nenhuma falha sistemática por classe reconhecível;
  - taxa de erro técnico não pode ser materialmente pior que a do Claude no mesmo
    dataset — **"materialmente pior" permanece sem definição operacional nesta etapa**;
    nenhum número foi inventado.

  **3. Accuracy mínima por campo** (sem média única):
  - `language` ≥ 97%
  - `market` ≥ 95%
  - `signal_type` ≥ 90%
  - `durability_hint` ≥ 80%, **somente** sobre os casos em que ground truth seja
    estabelecível; a taxa de **abstenção apropriada** é medida separadamente; casos
    genuinamente indetermináveis não entram no denominador de nenhum campo.

  **4. Accuracy conjunta:** medida e reportada, **não** usada como gate independente de
  aprovação — serve para detectar possíveis falhas correlacionadas entre campos.

  **5. Degradação vs. melhoria:** assimetria de risco mantida — `market`/`language` =
  severidade alta; `signal_type` = média; `durability_hint` = baixa. Uma degradação de
  alta severidade **não pode ser simplesmente anulada** por uma quantidade equivalente
  de melhorias. **Nenhum multiplicador numérico de compensação foi definido nesta
  etapa** — será definido, se necessário, só durante a formalização operacional do
  benchmark.

  **6. Indetermináveis:** definidos **antes** de qualquer execução dos modelos;
  excluídos do denominador de toda métrica de accuracy; reportados separadamente;
  **nunca** reclassificados depois de observar respostas dos modelos; concordância
  Claude/Groq num caso indeterminável **não** conta como acerto para nenhum dos dois.

  **7. Divergência:** **nenhum percentual fixo** estabelecido como gate nesta versão.
  Usada para investigação dirigida quando: concentrada num campo específico;
  concentrada numa única direção; desproporcional nos casos já classificados como
  fáceis.

  **8. Custo:** estrutura em duas fases —
  - **Fase 1:** qualidade/hard gates primeiro (pass/fail);
  - **Fase 2:** só entre candidatos já aprovados, custo pode ser usado como critério de
    otimização/desempate.
  Custo **nunca** pode compensar reprovação em qualidade.

  **9. Latência:** medida e reportada, **não** usada como gate de aprovação nesta fase.

  **10. Contagem absoluta de erros:** os percentuais mínimos (item 3) são o critério
  principal, mas a interpretação final também deve considerar o **número absoluto** de
  erros permitidos — calculado **somente depois** que o dataset final estiver fechado.
  **Nenhum número de exemplos ou erro absoluto foi inventado nesta etapa.**

  **11. Pré-registro:** esta decisão **é** o pré-registro dos critérios de aprovação do
  Normalization Benchmark. Qualquer alteração posterior deve ser uma **nova decisão
  explícita**, identificada como alteração pós-registro — nunca silenciosa.

  **12. Escopo — o que esta decisão NÃO aprova:**
  - integração de Groq em produção;
  - substituição de Claude;
  - fallback automático;
  - A/B em produção;
  - alteração do pipeline de Normalization;
  - o benchmark em si (execução);
  - a construção do dataset;
  - qualquer chamada paga aos modelos.

  Esta decisão aprova **somente** os critérios que serão usados, no futuro, para avaliar
  o candidato externo no OMR-03 — nada além disso.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  Aprovada a opção (a) — política **BALANCEADA** — integralmente, exatamente no
  conteúdo descrito em Recomendação, como **pré-registro V1** dos critérios de
  aprovação do Normalization Benchmark (OMR-03).

  Nenhum benchmark, dataset, harness ou chamada real a Claude/OmniRoute/Groq foi
  executado ou criado por esta decisão. Nenhum código de produção, `RunConfig`,
  `ReplayConfig`, `normalize/llm.py`, `StageClient`, o adapter OmniRoute
  (`external_llm_gateway`), Cluster Strategy, Musical DNA ou value-engine weighting foi
  alterado. OMR-01 e OMR-02 permanecem intocados.

  Três parâmetros foram deixados explicitamente sem valor numérico, por decisão
  deliberada, e ficam registrados como pendências da formalização operacional do
  benchmark (não desta decisão): (i) o que conta como "materialmente pior" na taxa de
  erro técnico (item 2); (ii) o multiplicador de compensação melhoria×degradação (item
  5); (iii) o número absoluto de erros tolerável (item 10) — calculável apenas depois
  que o dataset final estiver fechado.

  A construção do dataset e do harness isolado do Normalization Benchmark permanecem
  **não aprovados** — dependem de decisões próprias e futuras.

# 6. ESTÁGIO 4 — PAGE BLUEPRINT

As decisões **D-PB-1 a D-PB-12** foram tomadas pelo proprietário do negócio (Nicolas
Alves) em **2026-09-04**, com autorização explícita para abrir o **estágio 4 do pipeline
canônico (C8) — Page Blueprint** — e somente ele ("Fica explicitamente autorizado o início
do Stage 4 — Page Blueprint … equivalente ao padrão D-CS-1"). O estágio 3 (Cluster
Strategy) já está construído, mesclado e validado ao vivo (PR #1); sua saída — o sidecar
`ClusterStrategy` — é o contrato de entrada deste estágio. Os estágios 5–13 permanecem
DEFERRED sob a P4.

A única precondição técnica do estágio 4 — um DNA musical §9 aprovado pelo proprietário em
`knowledge/business-dna/business-dna.md` — está **atendida** (transferida pelo proprietário,
commit `2b8df10`).

O contrato completo do estágio está em `docs/PAGE-BLUEPRINT-V1.md`. Onde este arquivo e uma
decisão DECIDED (C1–C10 / I1–I12 / D-CS-1–D-CS-12) divergirem, a decisão prevalece.

## D-PB-1 — Abertura do estágio 4 (Page Blueprint)

- **Problema:** a P4 mantém os estágios 4–13 como DEFERRED; o próprio registro da D-CS-1
  nomeia "Page Blueprint" entre eles. Construir o estágio 4 depende de uma decisão explícita
  do proprietário para abrir o estágio.
- **Por que isso importa:** abrir um estágio postergável sem autorização registrada quebra a
  ordem de autoridade (`DECISIONS-NEEDED.md` > spec > `CLAUDE.md`).
- **Decisão necessária:** autorizar a abertura do estágio 4 — e somente dele.
- **Opções possíveis:**
  - (a) abrir apenas o estágio 4;
  - (b) abrir os estágios 4–5 em conjunto;
  - (c) manter DEFERRED até uma revisão pós-V1 mais ampla.
- **Recomendação:** (a). Escopo restrito ao Page Blueprint; os estágios 5–13 seguem
  DEFERRED sob a P4.
- **Quem precisa decidir:** Proprietário.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  O **estágio 4 (Page Blueprint)** do pipeline canônico (C8) está aberto para implementação.
  Somente o estágio 4 é aberto; os estágios 5–13 (Content Strategy, Content Production,
  Video Engine, Audio Engine, Quality Control, Publishing, Analytics, Optimization,
  Learning) permanecem DEFERRED sob a P4. A implementação segue o contrato
  `docs/PAGE-BLUEPRINT-V1.md` e as decisões D-PB-2 … D-PB-12 abaixo. A autonomia permanece
  no Nível 1 (o sistema recomenda; o humano aprova e executa).

## D-PB-2 — Fronteira do estágio 4 vs Business DNA V1 §11–§13

- **Problema:** o Business DNA V1 §11 coloca *linguagem, estética, conteúdo e CTA* em
  "Cluster Strategy"; o §12 dá ao Page Blueprint "pilares de conteúdo dessa página"; o C8 e
  a D-CS-8 separam identidade visual (estágio 4) do sistema de conteúdo (estágio 5).
  Divergência direta de documento.
- **Por que isso importa:** determina o que o estágio 4 entrega e o que ele deixa para o
  estágio 5.
- **Decisão necessária:** confirmar a fronteira do estágio 4.
- **Opções possíveis:** seguir o Business DNA V1 §11–§13 literal; confirmar a fronteira V1
  estabelecida.
- **Recomendação:** confirmar a fronteira V1 estabelecida.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  Page Blueprint = identidade da página + identidade visual + tom de voz + um enquadramento
  de conteúdo raso, em nível de página. O sistema de conteúdo (formatos, hooks, estruturas,
  copy de CTA, regras linguísticas/visuais de produção, calendário) é o estágio 5 (Content
  Strategy). O `AI Music Media Engine — Business DNA V1.md` é documento de visão estratégica
  e não supersede as decisões DECIDED (C6, I2, C7–C8, I4, D-CS-8).

## D-PB-3 — Herança verbatim do ativo do Cluster Strategy

- **Problema:** o Business DNA V1 §12 diz que o Page Blueprint "escolhe playlist e artista
  associados"; a I5 e a D-CS-8 já fazem o Cluster Strategy carregar a decisão de ativo do
  `AssetMatch` (reúso de playlist / recomendação de página) adiante.
- **Por que isso importa:** re-decidir o ativo no estágio 4 duplica o julgamento (I5) e abre
  espaço para o estágio 4 contradizer o estágio 3.
- **Decisão necessária:** o Page Blueprint re-decide o ativo (página/playlist/artista) ou o
  carrega?
- **Opções possíveis:** re-decidir; carregar verbatim.
- **Recomendação:** carregar verbatim.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  O `PageAssetLink` embute o objeto `PageStrategy` do estágio 3 por construção; os ids vêm
  diretamente de `ClusterStrategy.asset_strategy`. O Claude recebe o ativo como contexto
  ("reference only, never re-decide"), nunca como escolha. O Page Blueprint nunca re-julga
  se uma página nova se justifica (I5) nem qual ativo ancora a página. Uma nota fixa
  (`asset_inheritance_note`) viaja em todo `PageAssetLink`, verificada byte-a-byte.

## D-PB-4 — Escopo de consumo do DNA musical §9

- **Problema:** o §9 (agora aprovado pelo proprietário) tem tanto um princípio de "house
  sound" / expressão sônica por cluster (§9.9) quanto detalhe de instrumentação, BPM, uso de
  frequências e critérios de rejeição de sonoridade. O Page Blueprint precisa do primeiro; o
  segundo é do Audio Engine (estágio 8).
- **Por que isso importa:** sem um limite, o estágio 4 invade o estágio 8 e a identidade
  visual passa a depender de detalhe que não é seu.
- **Decisão necessária:** quanto do §9 o Page Blueprint consome.
- **Opções possíveis:** consumir o §9 inteiro; consumir apenas o princípio de house sound +
  a expressão §9.9 do cluster.
- **Recomendação:** apenas o princípio de house sound + a expressão §9.9 do cluster.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  A identidade visual e o tom de voz se ancoram **apenas** no princípio de house sound e na
  expressão §9.9 do cluster; `musical_dna_expression_used` deve citar a frase §9.9 usada
  (campo obrigatório, não vazio — validado). Instrumentação, BPM, frequências e critérios de
  sonoridade não são lidos. O caminho de fallback para §9 `NEEDS_INPUT` (confiança ≤ MEDIUM
  + nota `blocked_by`) é mantido no código (ver D-PB-10).

## D-PB-5 — Modelo de avaliação/confiança do estágio 4

- **Problema:** o C9 fixa as 10 dimensões *da oportunidade*; a D-CS-4 fixa 4 dimensões *da
  estratégia de cluster*. Não há modelo decidido para um page blueprint.
- **Por que isso importa:** sem um modelo fixo, cada run pode inventar dimensões e o estágio
  pode se apresentar como uma reavaliação que ele não é.
- **Decisão necessária:** o conjunto de dimensões/confiança do Page Blueprint e se há
  `status` persistente por página.
- **Opções possíveis:** reaproveitar as 4 dimensões do estágio 3; um conjunto próprio; uma
  única confiança sem rubrica.
- **Recomendação:** uma única confiança qualitativa, sem rubrica multidimensional.
- **Quem precisa decidir:** Arquitetura + Proprietário.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  O Page Blueprint tem **uma** `overall_confidence` qualitativa (`LOW`/`MEDIUM`/`HIGH`), sem
  rubrica por dimensão — ele sintetiza a partir de uma estratégia já avaliada e não reavalia
  nada. A confiança é fixada deterministicamente em `min(confiança_do_modelo,
  ClusterStrategy.overall_confidence)` e limitada a MEDIUM enquanto o §9 estiver
  `NEEDS_INPUT`; a síntese nunca aumenta a confiança. Sem score 0–100 (C6). Sem campo
  `status` persistente: uma reexecução sobrescreve `reports/page-blueprint/<opportunity_id>.*`
  (idempotente).

## D-PB-6 — Profundidade do content framing no estágio 4

- **Problema:** o Business DNA V1 §12 lista "pilares de conteúdo dessa página"; o sistema de
  conteúdo é o §13 / estágio 5. Sem uma linha, o estágio 4 invade o estágio 5.
- **Por que isso importa:** define quanto de conteúdo o estágio 4 produz.
- **Decisão necessária:** o quanto de enquadramento de conteúdo o estágio 4 produz.
- **Opções possíveis:** raso (pilares amplos + plataformas + cadência qualitativa); médio (+
  formatos); profundo (sistema de conteúdo).
- **Recomendação:** raso.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  Raso. `content_pillars` = 3–5 pilares **temáticos amplos** para esta página apenas;
  `platforms`; uma `posting_cadence` **qualitativa** (ex.: "3–4x por semana"). Nada de
  formatos, hooks, estruturas, copy de CTA, regras linguísticas/visuais de produção,
  calendário, tamanhos de lote ou templates. `> 5` pilares → WARNING suave; `0` → erro.

## D-PB-7 — Gatilho de entrada no Page Blueprint

- **Problema:** nem o spec nem o Business DNA V1 definem como uma estratégia de cluster é
  encaminhada ao estágio 4.
- **Por que isso importa:** a autonomia L1 e o controle de volume (I12) implicam seleção
  humana; sem um gatilho explícito o estágio pode rodar em lote.
- **Decisão necessária:** quais estratégias entram no Page Blueprint e como o estágio é
  invocado.
- **Opções possíveis:**
  - (a) CLI explícita, por oportunidade, invocada pelo proprietário, com gate
    `target_next_stage == PAGE_BLUEPRINT` no `ClusterStrategy` de entrada;
  - (b) execução automática sobre todo `ClusterStrategy` produzido;
  - (c) execução em lote sob regras.
- **Recomendação:** (a).
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  Gatilho explícito, por oportunidade, invocado pelo proprietário via CLI
  (`python -m page_blueprint reports/cluster-strategy/<opportunity_id>.json`). O estágio
  recusa a execução a menos que `recommendation.target_next_stage == PAGE_BLUEPRINT` no
  `ClusterStrategy` de entrada (além dos gates de `schema_version`, decisão de cluster e
  presença das três seções de estratégia). Não há execução automática nem em lote (autonomia
  L1; I12).

## D-PB-8 — Local de saída e digest do estágio 4

- **Problema:** a I7 (`reports/` = durável) se aplica; o caminho exato e se o estágio 4
  emite um digest não estavam definidos.
- **Por que isso importa:** consistência de saída entre estágios.
- **Decisão necessária:** local de saída e existência de digest.
- **Opções possíveis:** `reports/page-blueprint/<opportunity_id>.{md,json}` sem digest; com
  digest por run.
- **Recomendação:** `reports/page-blueprint/<opportunity_id>.{md,json}`, sem digest.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  `reports/page-blueprint/<opportunity_id>.md` + `.json`. **Sem digest** no V1 do estágio 4
  (uma oportunidade por vez); o relatório é o entregável.

## D-PB-9 — Ausência de escrita em `knowledge/` (contraste com D-CS-7)

- **Problema:** o Cluster Strategy recebeu um append opt-in em `opportunity-registry.yaml`
  (D-CS-7). A questão é se o estágio 4 precisa de equivalente.
- **Por que isso importa:** cada caminho de escrita em `knowledge/` é uma exceção de
  governança (spec §17) e precisa ser explícito.
- **Decisão necessária:** o Page Blueprint escreve em `knowledge/`?
- **Opções possíveis:** append opt-in análogo ao D-CS-7; nenhum caminho de escrita.
- **Recomendação:** nenhum caminho de escrita.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  O Page Blueprint **não tem** caminho de escrita em `knowledge/` — nem opt-in. Ele lê
  `knowledge/` e escreve somente em `reports/page-blueprint/`. O vínculo com o registry
  continua sendo assunto do estágio 3. Um run normal, offline ou ao vivo deixa `knowledge/`
  intocado.

## D-PB-10 — Rodar o estágio 4 com DNA musical `NEEDS_INPUT` (caminho de fallback)

- **Problema:** o §9 agora está aprovado pelo proprietário, mas o caminho de código e a
  possibilidade de uma janela futura de `NEEDS_INPUT` permanecem.
- **Por que isso importa:** o estágio precisa degradar de forma previsível se o §9 voltar a
  `NEEDS_INPUT`.
- **Decisão necessária:** `NEEDS_INPUT` no DNA musical é estado aceitável para o Page
  Blueprint rodar?
- **Opções possíveis:** rodar com teto de confiança; bloquear até o §9 estar disponível.
- **Recomendação:** rodar com teto de confiança.
- **Quem precisa decidir:** Proprietário + Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  Aceitável. O estágio roda com `overall_confidence ≤ MEDIUM`, `musical_dna_expression_used`
  definido como uma nota "§9 indisponível" e uma entrada `blocked_by`; o mesmo teto que o
  pipeline aplica a `music_fit`. O Page Blueprint nomeia *o que* precisaria de detalhe de §9,
  sem inventá-lo (G10; spec §15). Em produção esse caminho está inerte.

## D-PB-11 — Tratamento de `schema_version` do contrato

- **Problema:** o `schema_version` do `ClusterStrategy` é `1.0.0`; o comportamento diante de
  um valor futuro diferente não estava definido.
- **Por que isso importa:** adivinhar um schema desconhecido corrompe a entrada
  silenciosamente.
- **Decisão necessária:** o que o estágio 4 faz diante de um `schema_version` diferente de
  `1.0.0`.
- **Opções possíveis:** tentar decodificar mesmo assim; falhar imediatamente.
- **Recomendação:** falhar imediatamente (hard-fail).
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  O Page Blueprint fixa `schema_version == 1.0.0` e faz **hard-fail** diante de qualquer
  outro valor — no sidecar `ClusterStrategy` de entrada e no `PageBlueprint` montado —
  surfando a divergência (Regra de Engenharia 9) em vez de adivinhar.

## D-PB-12 — Reconciliação de nomes do pipeline

- **Problema:** o Business DNA V1 (§5) usa nomes de estágio diferentes; o C8 é canônico.
  Divergência menor, não bloqueante.
- **Por que isso importa:** afeta a nomeação de componentes e a comunicação.
- **Decisão necessária:** qual conjunto de nomes usar no estágio 4.
- **Opções possíveis:** nomes do Business DNA V1; nomes canônicos do C8.
- **Recomendação:** nomes canônicos do C8.
- **Quem precisa decidir:** Arquitetura.
- **Status:** DECIDED (2026-09-04)
- **Resultado:**

  Decisão tomada pelo proprietário do negócio (Nicolas Alves) em 2026-09-04.

  Usar os nomes canônicos do C8 (`Page Blueprint`, estágio 4). As divergências de nome do
  Business DNA V1 ficam anotadas, sem edição de documento — mesmo tratamento dado ao C8 (ver
  P10, D-CS-12).

---

## Caminho crítico

As decisões que realmente destravam o início do Market Intelligence Agent:

1. **C1** — unidade de "oportunidade".
2. **C2** — fontes de sinal do V1. _(NEEDS INPUT)_
3. **C3 + C4** — Business DNA mínimo + regras de compliance. _(NEEDS INPUT)_
4. **C5 + C9** — lista única de dimensões de avaliação, alinhada ao funil do §4.
5. **C6** — número 0–100 agora ou tiers qualitativos até haver calibração.
6. **C7 + C8** — fronteira do Market Intelligence e pipeline canônico.
