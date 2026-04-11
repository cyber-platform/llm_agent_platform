# Документирование архитектуры ПО

## Контекст

Задача фиксирует ongoing работу по построению навигабельной архитектурной документации для `llm_agent_platform`.

Цель текущего этапа:

- привести архитектурную документацию к многоуровневой модели `C4 Context -> C4 Container -> C4 Component -> flows -> packages`;
- отделить overview, container-level, component-level и policy-level документы;
- зафиксировать terminology layer для архитектуры и provider-centric модели;
- сохранить continuation context для нового чата без потери уже принятых решений.

## Goal

Собрать цельный и трассируемый набор архитектурных документов, в котором агент и человек могут:

- быстро понять систему сверху;
- найти runtime containers, components и package ownership;
- понять ключевые interaction paths;
- использовать согласованную терминологию без semantic ambiguity.

## Scope

В scope этой задачи входят:

- `docs/architecture/` как engineering SoT для архитектуры;
- `docs/terms/` как terminology entry points;
- связанные `operational_scope` artifacts для handoff и continuation.

Не входят в scope:

- production code changes;
- реализация `Web UI` или admin surface;
- реализация `user service`;
- полное устранение contract drift в существующих runtime docs.

## Key decisions already fixed

- `system-overview.md` фиксируется как `C4 Context` уровень.
- `container-view.md` фиксируется как `C4 Container` уровень.
- `component-view.md` фиксируется как `C4 Component` уровень, а `component-map.md` — как code-oriented component map.
- `Web UI` фиксируется как один human-facing container, а не как два отдельных UI containers.
- `RBAC` фиксируется как отдельная architectural policy, а не как container.
- terminology для provider-centric модели разведена на `LLM Vendor`, `LLM provider`, `abstract provider`, `provider implementation`.
- terminology для `LLM API protocol` зафиксирована через различие между `OpenAI API`, `OpenAI-compatible API` и vendor-specific APIs вроде `Google Gemini API`.
- `docs/terms/` переведён на reusable structure: `index.md -> <scope>/terms-map.md -> <scope>/terms/<term>.md`.

## Canonical documents to continue from

### Архитектурные entry points

- [`docs/architecture/index.md`](../../docs/architecture/index.md)
- [`docs/architecture/system-overview.md`](../../docs/architecture/system-overview.md)
- [`docs/architecture/container-view.md`](../../docs/architecture/container-view.md)
- [`docs/architecture/component-view.md`](../../docs/architecture/component-view.md)
- [`docs/architecture/component-map.md`](../../docs/architecture/component-map.md)
- [`docs/architecture/layers.md`](../../docs/architecture/layers.md)
- [`docs/architecture/package-map.md`](../../docs/architecture/package-map.md)
- [`docs/architecture/runtime-flows.md`](../../docs/architecture/runtime-flows.md)
- [`docs/architecture/web-ui.md`](../../docs/architecture/web-ui.md)
- [`docs/architecture/rbac.md`](../../docs/architecture/rbac.md)
- [`docs/architecture/rbac-roles.md`](../../docs/architecture/rbac-roles.md)

### Канонические supporting docs

- [`docs/vision.md`](../../docs/vision.md)
- [`docs/providers/README.md`](../../docs/providers/README.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/auth.md`](../../docs/auth.md)
- [`docs/configuration/provider-accounts-config.md`](../../docs/configuration/provider-accounts-config.md)
- [`docs/configuration/env-files.md`](../../docs/configuration/env-files.md)
- [`docs/testing/test-map.md`](../../docs/testing/test-map.md)

### Терминология

- [`docs/terms/index.md`](../../docs/terms/index.md)
- [`docs/terms/project/terms-map.md`](../../docs/terms/project/terms-map.md)
- [`docs/terms/project/terms/llm-vendor.md`](../../docs/terms/project/terms/llm-vendor.md)
- [`docs/terms/project/terms/llm-provider.md`](../../docs/terms/project/terms/llm-provider.md)
- [`docs/terms/project/terms/abstract-provider.md`](../../docs/terms/project/terms/abstract-provider.md)
- [`docs/terms/project/terms/provider-implementation.md`](../../docs/terms/project/terms/provider-implementation.md)
- [`docs/terms/project/terms/llm-api-protocol.md`](../../docs/terms/project/terms/llm-api-protocol.md)
- [`docs/terms/project/terms/openai-compatible-api.md`](../../docs/terms/project/terms/openai-compatible-api.md)
- [`docs/terms/project/terms/rbac.md`](../../docs/terms/project/terms/rbac.md)

### Runtime evidence and code roots

- [`llm_agent_platform/__main__.py`](../../llm_agent_platform/__main__.py)
- [`llm_agent_platform/api/openai/`](../../llm_agent_platform/api/openai)
- [`llm_agent_platform/api/gemini/routes.py`](../../llm_agent_platform/api/gemini/routes.py)
- [`llm_agent_platform/api/parity/routes.py`](../../llm_agent_platform/api/parity/routes.py)
- [`llm_agent_platform/auth/`](../../llm_agent_platform/auth)
- [`llm_agent_platform/services/`](../../llm_agent_platform/services)
- [`llm_agent_platform/provider_registry/`](../../llm_agent_platform/provider_registry)
- [`llm_agent_platform/tests/`](../../llm_agent_platform/tests)

### Methodology and reusable terminology assets

- [`sot_layers/hyper-graph/docs/methodology-layer/assets/terms-management/terms-map.md`](../../sot_layers/hyper-graph/docs/methodology-layer/assets/terms-management/terms-map.md)
- [`sot_layers/hyper-graph/docs/methodology-layer/assets/terms-management/resources/terms-index.template.md`](../../sot_layers/hyper-graph/docs/methodology-layer/assets/terms-management/resources/terms-index.template.md)
- [`sot_layers/hyper-graph/docs/methodology-layer/assets/terms-management/resources/terms-map.template.md`](../../sot_layers/hyper-graph/docs/methodology-layer/assets/terms-management/resources/terms-map.template.md)
- [`sot_layers/hyper-graph/assets/metodologes/waterfall/software-architecture-documentation-methodology.md`](../../sot_layers/hyper-graph/assets/metodologes/waterfall/software-architecture-documentation-methodology.md)

## Remaining work

1. Пройтись по архитектурным документам и заменить неоднозначное `provider` на канонические термины там, где это важно.
2. Решить, нужен ли отдельный focused document для `user service` / `users DB` boundary.
3. Сформировать drift register по расхождениям code vs docs/contracts.

## Definition of Done

- Архитектурная навигация покрывает `Context`, `Container`, `Component`, `flows`, `packages`, `terms`.
- `docs/architecture/index.md` ведёт по всем ключевым entry points.
- `docs/terms/` использует reusable structure со scopes.
- Для `Web UI`, `RBAC` и provider-centric терминологии есть focused documents.
- В task-файле достаточно ссылок и handoff context для безопасного продолжения в новом чате.

## Execution Status

- Current State: созданы и частично согласованы `system-overview.md`, `container-view.md`, `component-view.md`, `component-map.md`, `package-map.md`, `web-ui.md`, `rbac.md`, `rbac-roles.md`, terminology layer в `docs/terms/`; `sot_layers/hyper-graph/docs/terms/` и reusable terms-management assets приведены к новой structure.
- Next Step: пройти terminology cleanup по ambiguous `provider` mentions, затем зафиксировать drift register.
- Blockers: none.
- Contract Changes: present.
- Verification: docs updated by direct file inspection; no command-based verification was run.

## Handoff Notes

### What is done

- Добавлен архитектурный index и многослойная navigation в [`docs/architecture/index.md`](../../docs/architecture/index.md).
- `system-overview.md` зафиксирован как `C4 Context` в [`docs/architecture/system-overview.md`](../../docs/architecture/system-overview.md).
- Добавлен `C4 Container` документ в [`docs/architecture/container-view.md`](../../docs/architecture/container-view.md).
- Добавлен отдельный `C4 Component` документ в [`docs/architecture/component-view.md`](../../docs/architecture/component-view.md).
- `component-map.md` переориентирован на code-oriented component navigation в [`docs/architecture/component-map.md`](../../docs/architecture/component-map.md).
- `package-map.md` перегруппирован вокруг components вместо layer-first представления в [`docs/architecture/package-map.md`](../../docs/architecture/package-map.md).
- Зафиксирована taxonomy для `LLM API protocol` и разделены `OpenAI API`, `OpenAI-compatible API` и `provider implementation` в [`docs/terms/project/terms-map.md`](../../docs/terms/project/terms-map.md).
- `Web UI` вынесен в focused document [`docs/architecture/web-ui.md`](../../docs/architecture/web-ui.md).
- `RBAC` и роли вынесены в [`docs/architecture/rbac.md`](../../docs/architecture/rbac.md) и [`docs/architecture/rbac-roles.md`](../../docs/architecture/rbac-roles.md).
- Терминология проекта оформлена в [`docs/terms/index.md`](../../docs/terms/index.md), [`docs/terms/project/terms-map.md`](../../docs/terms/project/terms-map.md) и detail pages в [`docs/terms/project/terms/`](../../docs/terms/project/terms).
- `hyper-graph` reusable terms-management assets дополнены шаблонами и приведены к той же structure в [`sot_layers/hyper-graph/docs/terms/index.md`](../../sot_layers/hyper-graph/docs/terms/index.md).

### Immediate fix first

- Ближайший шаг смещается с `C4 Component` уровня на terminology cleanup и drift register.

### Pending work

- terminology cleanup for `provider` mentions
- decision on `user service` / `users DB` boundary
- drift register

### Commands to run

- No verification commands captured yet.

### User constraints

- Документация проекта и methodology assets пишутся на русском языке, кроме устойчивых English terms.
- `docs/` остаётся engineering SoT.
- Архитектурная документация должна быть навигабельной, трассируемой и удобной для продолжения в новом чате.
- `Web UI` — один container с `RBAC`, backend — enforcement boundary.
- Терминология должна использовать reusable `docs/terms/index.md -> <scope>/terms-map.md -> <scope>/terms/<term>.md` structure.
