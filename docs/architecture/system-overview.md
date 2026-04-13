# System Overview

## Назначение

Этот документ даёт high-level представление о системе и задаёт общий zoom-in path для дальнейшей навигации.

В текущем наборе документации `system-overview` фиксирует именно `C4 Context` уровень. Более глубокие уровни вынесены в отдельные focused documents.

## System context

`llm_agent_platform` — `LLM provider`-centric система для LLM-агентов и developer tools.

Система materialize-ится как набор автономных services, где текущий system boundary уже включает `Backend service`, `User service` и local-only `Frontend service` как текущий operator/admin slice target `Web UI`.

Платформа предоставляет:

- `LLM provider`-scoped [`OpenAI-compatible API`](../terms/project/terms/openai-compatible-api.md) через `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`;
- human-facing operator/admin UI поверх backend admin API;
- login and identity boundary через `User service`;
- `LLM provider`-local catalogs, auth и quota semantics;
- contracts, `LLM provider` pages и tests как канонический evidence layer.

Общий product canon: [`docs/vision.md`](docs/vision.md:1)

## System boundary

В текущем target framing `llm_agent_platform` нужно читать как assembled multi-service system, а не как один runtime process.

Внутри system boundary находятся:

- `Frontend service` — current local-only operator/admin frontend service, materializing текущий slice target `Web UI`;
- `Backend service` — machine-facing provider API и admin-facing backend runtime;
- `User service` — identity service для login, JWT issuance и user storage;
- local operational helpers, если они нужны для OAuth bootstrap и локальной подготовки credentials.

Технологический стек системы оркестрируется через [`HSM`](../terms/project/terms/hsm.md), но `HSM` не является runtime container платформы.

## External systems and storage

```mermaid
flowchart LR
  Human[Operator or administrator] --> Frontend[Frontend service]
  Machine[LLM agent or developer tool] --> Backend[Backend service]
  Frontend --> Backend
  Frontend --> UserService[User service]
  OAuth[OAuth bootstrap scripts] --> Secrets[Secrets storage]
  Backend --> Secrets
  Backend --> State[STATE_DIR storage]
  Backend --> Provider[LLM provider]
  Docs[Docs contracts ADR tests] -. SoT and evidence .-> Backend
```

Подписи на диаграмме:

- `Operator or administrator` — human actor, который использует `Frontend service`.
- `LLM agent or developer tool` — внешний machine-facing клиент, который использует публичный [`OpenAI-compatible API`](../terms/project/terms/openai-compatible-api.md) платформы.
- `Frontend service` — human-facing service для operator/admin scenarios.
- `Backend service` — основной runtime service платформы.
- `User service` — identity boundary для login flow и JWT issuance.
- `OAuth bootstrap scripts` — локальные scripts, которые получают и обновляют user credentials вне runtime process.
- `Secrets storage` — пользовательские credentials и `LLM provider` accounts-config.
- `STATE_DIR storage` — mutable runtime state и monitoring artifacts.
- `LLM provider` — внешняя [`LLM provider`](../terms/project/terms/llm-provider.md) system boundary, к которой обращается платформа.
- `Docs contracts ADR tests` — канонический Source of Truth и evidence layer, который определяет rules, contracts и verification.

В codebase и runtime boundaries платформы присутствуют следующие внешние `LLM provider` integrations:

- `openai-chatgpt`
- `gemini-cli`
- `google-vertex`
- `qwen-code`

Это внешние systems, а не внутренние части `llm_agent_platform`.

Текущий provider matrix canon и степень readiness централизованы в [`docs/providers/index.md`](docs/providers/index.md:1); на текущем этапе fully documented provider page materialized только для `openai-chatgpt`.

## Архитектурные драйверы

- `LLM provider` является основной runtime-сущностью; `model_id` живут в `LLM provider`-local catalog.
- Route namespace выбирает `LLM provider`; `model_id` никогда не должен неявно выбирать `LLM provider`.
- Groups живут внутри `LLM provider` namespace и изолируют account state.
- Runtime работает по in-memory-first модели; persisted state нужен для restore after restart и audit trail.
- Credentials, declarative config и mutable runtime state являются разными границами хранения и ответственности.
- Публичный [`OpenAI-compatible API`](../terms/project/terms/openai-compatible-api.md) должен оставаться стабильным, даже если `provider implementation` адаптирует его к более богатому vendor-specific upstream protocol.
- `Frontend service` и `Backend service` остаются отдельными service boundaries даже если локально поднимаются вместе.

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
- Local-only operator UI slice materialized как отдельный frontend service в nested repo [`services/frontend/`](services/frontend:1), использует `user_service` для login и backend admin API для operator actions.
- `Backend service` materialized как service-local boundary в [`services/backend/`](services/backend:1); root repo сохраняет только system assembly и system-level SoT.
- `User service` интегрирован в текущий mini-release как platform auth baseline для operator/admin contour.
- `LLM provider`-specific details и materialization boundary должны уточняться на страницах в [`docs/providers/`](docs/providers:1).
