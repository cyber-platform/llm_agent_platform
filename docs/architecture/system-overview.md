# System Overview

## Назначение

Этот документ даёт high-level представление о системе и задаёт общий zoom-in path для дальнейшей навигации.

В текущем наборе документации `system-overview` фиксирует именно `C4 Context` уровень. Более глубокие уровни вынесены в отдельные focused documents.

## System context

`llm_agent_platform` — `LLM provider`-centric runtime слой для LLM-агентов и developer tools.

Платформа предоставляет:

- `LLM provider`-scoped [`OpenAI-compatible API`](../terms/project/terms/openai-compatible-api.md) через `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`;
- `LLM provider`-local catalogs, auth и quota semantics;
- единый runtime path для request routing, account rotation, streaming normalization и error shaping;
- contracts, `LLM provider` pages и tests как канонический evidence layer.

Общий product canon: [`docs/vision.md`](docs/vision.md:1)

## System boundary

Текущий root runtime — один Flask-based process, собираемый через [`llm_agent_platform/__main__.py`](llm_agent_platform/__main__.py:1).

Внутри него живут:

- `LLM provider`-scoped [`OpenAI-compatible API`](../terms/project/terms/openai-compatible-api.md) routes;
- provider-native routes для Gemini;
- parity relay routes;
- `abstract provider` registry, auth, quota router, runtime state persistence и `provider implementation` integrations.

## External systems and storage

```mermaid
flowchart LR
  Client[LLM agent or developer tool] --> App[llm_agent_platform runtime]
  OAuth[OAuth bootstrap scripts] --> Secrets[Secrets storage]
  App --> Secrets
  App --> State[STATE_DIR storage]
  App --> Provider[LLM provider]
  Docs[Docs contracts ADR tests] -. SoT and evidence .-> App
```

Подписи на диаграмме:

- `LLM agent or developer tool` — внешний клиент, который использует публичный [`OpenAI-compatible API`](../terms/project/terms/openai-compatible-api.md) платформы.
- `llm_agent_platform runtime` — основной runtime process этого репозитория.
- `OAuth bootstrap scripts` — локальные scripts, которые получают и обновляют user credentials вне runtime process.
- `Secrets storage` — пользовательские credentials и `LLM provider` accounts-config.
- `STATE_DIR storage` — mutable runtime state и monitoring artifacts.
- `LLM provider` — внешняя [`LLM provider`](../terms/project/terms/llm-provider.md) system boundary, к которой обращается платформа.
- `Docs contracts ADR tests` — канонический Source of Truth и evidence layer, который определяет rules, contracts и verification.

В scope текущего runtime `LLM provider` включает следующие внешние integrations:

- `openai-chatgpt`
- `gemini-cli`
- `google-vertex`
- `qwen-code`

Это внешние systems, а не внутренние части `llm_agent_platform`.

## Архитектурные драйверы

- `LLM provider` является основной runtime-сущностью; `model_id` живут в `LLM provider`-local catalog.
- Route namespace выбирает `LLM provider`; `model_id` никогда не должен неявно выбирать `LLM provider`.
- Groups живут внутри `LLM provider` namespace и изолируют account state.
- Runtime работает по in-memory-first модели; persisted state нужен для restore after restart и audit trail.
- Credentials, declarative config и mutable runtime state являются разными границами хранения и ответственности.
- Публичный [`OpenAI-compatible API`](../terms/project/terms/openai-compatible-api.md) должен оставаться стабильным, даже если `provider implementation` адаптирует его к более богатому vendor-specific upstream protocol.

Ключевые документы rationale:

- [`docs/adr/0020-provider-centric-routing-and-provider-catalogs.md`](docs/adr/0020-provider-centric-routing-and-provider-catalogs.md:1)
- [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1)
- [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1)

## Дальнейшая навигация

Этот документ сознательно останавливается на уровне `C4 Context`.

Для следующих уровней детализации нужно идти в отдельные документы:

- container view: [`container-view.md`](./container-view.md)
- layers: [`layers.md`](./layers.md)
- `C4 Component`: [`component-view.md`](./component-view.md)
- component-to-code map: [`component-map.md`](./component-map.md)
- runtime interactions: [`runtime-flows.md`](./runtime-flows.md)
- packages: [`package-map.md`](./package-map.md)
- detailed pipeline view: [`openai-chat-completions-pipeline.md`](./openai-chat-completions-pipeline.md)

## Status notes

- OpenAI pipeline, `LLM provider`-centric routing, `abstract provider` registry, auth, quota router и state persistence materialized в runtime code.
- Group-scoped platform API key auth guard для public `openai-chatgpt` OpenAI-compatible API materialized и входит в working PoC baseline.
- Admin monitoring read-model, live refresh subsystem и memory-first monitoring runtime materialized для `openai-chatgpt` в границе current single-instance PoC.
- Local-only operator `Web UI` slice materialized как отдельный frontend service в nested repo [`services/frontend/`](services/frontend:1) и использует только backend admin API.
- Current PoC delivery boundary already distinguishes local-only operator/admin surface from machine-facing public `/<provider>/v1/*` exposure path.
- `LLM provider`-specific details и materialization boundary должны уточняться на страницах в [`docs/providers/`](docs/providers:1).
