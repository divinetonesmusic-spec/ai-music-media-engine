# External LLM Gateway — OmniRoute adapter (OMR-01)

> **Status:** isolated adapter, implemented. Not connected to any pipeline stage.
> Governing decision: `knowledge/DECISIONS-NEEDED.md`, **OMR-01**.

## 1. Propósito

`src/external_llm_gateway/` dá ao projeto a **capacidade técnica** de chamar um
modelo de LLM externo (Groq, Cerebras, Gemini, …) através de um gateway local
OpenAI-compatible ([OmniRoute](https://github.com)), sem alterar o comportamento
atual do AI Music Media Engine. É a implementação isolada aprovada por OMR-01 —
**não** é uma integração com o pipeline.

## 2. Arquitetura

```
src/external_llm_gateway/
├── __init__.py           # exporta OmniRouteConfig, OmniRouteStageClient
├── config.py              # OmniRouteConfig — endpoint, modelo, nome da env var da chave
└── omniroute_client.py    # OmniRouteStageClient(StageClient)
```

`OmniRouteStageClient` implementa o contrato já existente
`market_intelligence.llm_stage.StageClient` (`complete(*, stage, key, prompt,
schema, model) -> dict`) — o mesmo contrato que `AnthropicStageClient` (Framing /
Matching / Evaluation) e `AnthropicClusterStrategyClient` (Cluster Strategy) já
implementam.

**A dependência corre em um único sentido:**

```
external_llm_gateway  →  market_intelligence.llm_stage.StageClient
```

Nunca o inverso. Nenhum módulo em `market_intelligence/` ou `cluster_strategy/`
importa `external_llm_gateway`.

## 3. Relação com Claude/Anthropic

Claude continua sendo o **único caminho padrão** do pipeline. Este adapter:

- não substitui `AnthropicStageClient`, `AnthropicWebSearch`, `AnthropicNormalization`
  ou `AnthropicClusterStrategyClient`;
- não altera `market_intelligence.llm_stage.select_stage_client()` — esse seletor
  continua devolvendo `AnthropicStageClient` (live) ou `RecordedStageClient`
  (replay), exatamente como antes;
- não altera `RunConfig.model` nem `ReplayConfig`;
- não muda em nada a configuração ou a conta do Claude Code, que segue OAuth /
  Claude Pro normalmente.

## 4. OmniRoute como gateway externo opcional

[OmniRoute](https://localhost:20128) é um processo **local, externo ao
repositório**, que expõe um endpoint OpenAI-compatible
(`POST /v1/chat/completions`) na frente de vários providers (Groq, Cerebras,
Gemini, …). Este adapter **não gerencia esse processo**:

- não inicia o OmniRoute (`omniroute serve`);
- não para o OmniRoute (`omniroute stop`);
- não supervisiona, reinicia nem monitora o processo;
- não depende de `omniroute setup-claude` nem de `omniroute launch`;
- não lê nem modifica as credenciais internas do OmniRoute
  (`~/.omniroute/storage.sqlite`).

**OmniRoute precisa estar disponível separadamente** — subido manualmente pelo
operador (ou por um script isolado, fora deste pacote) antes de qualquer chamada.
Se não estiver, a chamada falha com um `StageError` de transporte (conexão
recusada) — o adapter não tenta subir o processo por conta própria.

## 5. Configuração

```python
from external_llm_gateway import OmniRouteConfig

config = OmniRouteConfig(
    base_url="http://localhost:20128/v1",   # padrão — configurável
    model="groq/openai/gpt-oss-120b",        # obrigatório (ou passado por chamada)
    api_key_env_var="OMNIROUTE_API_KEY",     # padrão — configurável
    connect_timeout=10.0,
    read_timeout=60.0,
)
```

Nenhum destes valores é lido de `config/*.yaml` do pipeline nem de `RunConfig` —
é um dataclass próprio, construído explicitamente pelo chamador.

## 6. Autenticação

A chave nunca é hardcoded e nunca é lida do cofre interno do OmniRoute. `
OmniRouteConfig.resolve_api_key()` lê, no momento da chamada, a variável de
ambiente cujo **nome** está em `api_key_env_var` (padrão `OMNIROUTE_API_KEY`).

- Se a variável não estiver definida, a requisição é enviada **sem** cabeçalho
  `Authorization` — um OmniRoute local com `REQUIRE_API_KEY=false` (o padrão
  observado numa instância loopback) responde normalmente.
- Se estiver definida, é enviada como `Authorization: Bearer <valor>`.
- O valor da chave nunca aparece em nenhuma mensagem de erro levantada pelo
  adapter (testado explicitamente — ver `tests/test_external_llm_gateway_omniroute_client.py`).
- O adapter não usa o módulo `logging` — não há nada para vazar segredo em log.

## 7. Exemplo de uso isolado

**O único uso suportado nesta etapa é instanciação explícita, fora do pipeline** —
num script ou teste isolado:

```python
from external_llm_gateway import OmniRouteConfig, OmniRouteStageClient

config = OmniRouteConfig(model="groq/openai/gpt-oss-120b")
client = OmniRouteStageClient(config)

result = client.complete(
    stage="manual-test",
    key="probe-1",
    prompt='Responda apenas com o JSON {"ok": true}',
    schema={},
    model="",  # usa config.model
)
print(result)  # {"ok": True}
```

Pressupõe: (a) o OmniRoute já está rodando em `base_url` (subido separadamente,
ex. `omniroute serve`); (b) o modelo escolhido responde com um objeto JSON no
conteúdo da mensagem — o adapter faz *parsing* leniente (aceita um bloco
` ```json … ``` `), igual ao fallback de prompt-guided JSON já usado em
`market_intelligence.evaluation` (fallback C, 2026-08-31).

## 8. Modelos / providers

O `model` passado é o slug completo que o OmniRoute espera (ex.
`groq/openai/gpt-oss-120b`, `cerebras/gpt-oss-120b`, `gemini/gemini-3.5-flash-lite`).
O adapter não valida, não traduz e não mantém um catálogo de modelos — apenas
repassa a string configurada. `model` passado a `complete(...)` tem precedência
sobre `OmniRouteConfig.model` quando não vazio.

Validado empiricamente, fora deste código, antes da implementação (OMR-01,
seção "Problema" em `knowledge/DECISIONS-NEEDED.md`): OmniRoute → Groq →
`groq/openai/gpt-oss-120b` → HTTP 200; OmniRoute → Cerebras → alcançou o
provider, HTTP 402 (billing); OmniRoute → Gemini → alcançou o provider, mas com
problemas de disponibilidade/capacidade nos modelos testados.

## 9. Tratamento de erros

Nenhuma exceção crua do `httpx` escapa de `OmniRouteStageClient.complete()`. Tudo
vira um dos dois erros que o contrato `StageClient` já define:

| Situação | Exceção |
|---|---|
| HTTP ≥ 400 (qualquer status) | `StageError` — mensagem nomeia a categoria: `400` inválido/modelo fora do catálogo, `402` billing, `503` indisponibilidade do provider, `504` timeout do gateway, outros com o número do status |
| Timeout de conexão/leitura (`httpx.TimeoutException`) | `StageError` |
| Erro de transporte — conexão recusada, DNS, etc. (`httpx.TransportError`) | `StageError` |
| Sem `model` configurado nem passado | `StageError` |
| Corpo da resposta HTTP não é JSON | `ResponseRejected` |
| Resposta sem `choices` ou sem `message.content` utilizável | `ResponseRejected` |
| `message.content` não é um objeto JSON válido | `ResponseRejected` |

Essa distinção preserva a regra já estabelecida no pipeline (spec §14): uma
falha de infraestrutura (`StageError`) nunca é confundida com um estado de
negócio, e uma resposta 200 mas inutilizável (`ResponseRejected`) é tratada à
parte de uma falha de transporte/autenticação/billing.

## 10. Limitações atuais

- **Sem fallback.** Uma falha em um modelo/provider não tenta outro modelo, outro
  provider nem outro transporte — uma chamada, um resultado ou um erro.
- **Sem retry automático.** `complete()` faz exatamente uma tentativa HTTP. (O
  retry-once do pipeline em `llm_stage.call_stage()` é uma função separada que
  este adapter não usa nesta etapa.)
- **`schema` não é enviado ao OmniRoute.** O parâmetro `schema` do contrato
  `StageClient` é aceito (assinatura compatível) mas não é traduzido para nenhum
  parâmetro OpenAI-compatible (`response_format`, `tools`, etc.) — o suporte do
  OmniRoute a saída estruturada não foi validado. O adapter conta apenas com
  *parsing* leniente de JSON no texto da resposta.
- **`httpx` é dependência transitiva**, não direta — vem hoje via `anthropic` no
  `pyproject.toml`. Se essa dependência transitiva mudar, adicionar `httpx`
  diretamente ao `pyproject.toml` exige uma decisão própria (fora do escopo do
  OMR-01, que foi explicitamente instruído a não tocar `pyproject.toml`).
- **Sem gestão de processo.** Ver seção 4 — o adapter não sobe nem derruba o
  OmniRoute.
- **Catálogo de modelos não verificado.** O adapter não confirma que o `model`
  configurado existe no catálogo ao vivo do OmniRoute antes de chamar — um
  modelo inexistente simplesmente retorna HTTP 400, tratado como `StageError`.

## 11. Nenhum stage usa este adapter por padrão

- Nenhum arquivo em `market_intelligence/` ou `cluster_strategy/` importa
  `external_llm_gateway`.
- `market_intelligence.llm_stage.select_stage_client()` **não foi alterado** —
  continua devolvendo apenas `AnthropicStageClient` ou `RecordedStageClient`.
- `market_intelligence.normalize.llm.select_normalization_client` (e o
  equivalente em `cluster_strategy`) também não foram tocados.
- O único caminho de uso desta etapa é a instanciação explícita mostrada na
  seção 7 — num script ou teste isolado, nunca a partir de `orchestrator.py` ou
  de qualquer `evaluate_opportunities` / `frame_signals` / `match_assets` /
  `cluster_strategy` real.

## 12. Qualquer integração futura exige uma nova decisão

Conectar este adapter a **qualquer** estágio do pipeline canônico — passar um
`OmniRouteStageClient` para `frame_signals(client=...)`, `match_assets(client=...)`,
`evaluate_opportunities(client=...)`, alterar `select_stage_client()` para
escolher entre providers, ou qualquer forma de roteamento de modelos em
produção — é uma mudança de arquitetura fora do escopo de OMR-01 e **exige um
novo registro de decisão** em `knowledge/DECISIONS-NEEDED.md`, aprovado pelo
proprietário do negócio, antes de qualquer código ser escrito (Regra de
Engenharia #7/#8, CLAUDE.md §17).
