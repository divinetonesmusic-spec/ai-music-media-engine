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
| P4 | Estágios seguintes do pipeline | POSTERGÁVEL | DEFERRED (2026-08-27) | Proprietário |
| P5 | Orquestração multi-agente | POSTERGÁVEL | DEFERRED (2026-08-27) | Arquitetura |
| P6 | Governança de criação de cluster novo | POSTERGÁVEL | DEFERRED (2026-08-27) | Proprietário + Arquitetura |
| P7 | Dashboards / tracking entre runs | POSTERGÁVEL | DEFERRED (2026-08-27) | Arquitetura |
| P8 | Versionamento de prompts / reprodutibilidade | POSTERGÁVEL | DEFERRED (2026-08-27) | Arquitetura |
| P9 | Conjunto de referência de concorrentes por cluster | POSTERGÁVEL | DEFERRED (2026-08-27) | Arquitetura |
| P10 | Reconciliação textual completa do pipeline no CLAUDE.md | POSTERGÁVEL | DECIDED (2026-08-27) | Proprietário + Arquitetura |

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
- **Status:** DEFERRED (2026-08-27)
- **Resultado:**

  Formalizada como DEFERRED pelo proprietário do negócio (Nicolas Alves) em 2026-08-27, com
  a aprovação do conjunto de decisões. Não bloqueia o V1; conteúdo, recomendação e
  justificativa acima permanecem válidos como registro. Será revisitada após a validação do
  V1 (ver C10), quando aplicável.

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

## Caminho crítico

As decisões que realmente destravam o início do Market Intelligence Agent:

1. **C1** — unidade de "oportunidade".
2. **C2** — fontes de sinal do V1. _(NEEDS INPUT)_
3. **C3 + C4** — Business DNA mínimo + regras de compliance. _(NEEDS INPUT)_
4. **C5 + C9** — lista única de dimensões de avaliação, alinhada ao funil do §4.
5. **C6** — número 0–100 agora ou tiers qualitativos até haver calibração.
6. **C7 + C8** — fronteira do Market Intelligence e pipeline canônico.
