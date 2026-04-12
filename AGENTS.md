# LLM Agent Platform

Provider-centric платформа для LLM-агентов и developer tools.

- Продукт предоставляет единый OpenAI-compatible API поверх нескольких providers.
- Provider является основной runtime-сущностью; модели живут в provider-local catalogs и могут иметь одинаковый `model_id` у разных providers.
- Routing, auth, quota handling, contracts и testing описываются с provider-centric точки зрения.

## Канонические источники

- Продуктовый и архитектурный канон: [`docs/vision.md`](docs/vision.md:1), [`docs/architecture/component-map.md`](docs/architecture/component-map.md:1), [`docs/architecture/openai-chat-completions-pipeline.md`](docs/architecture/openai-chat-completions-pipeline.md:1)
- Матрица providers и provider-specific behavior: [`docs/providers/index.md`](docs/providers/index.md:1), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- Contracts: [`docs/contracts/`](docs/contracts:1)
- Тестовый контур и suites: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Как читать контекст

- Durable project context: [`project/index.md`](project/index.md:1)
- Границы репозиториев и nested repos: [`project/gitContext.md`](project/gitContext.md:1)
- Технический стек и environment context: [`project/techContext.md`](project/techContext.md:1)
- Concrete loading order и ownership split: [`project/entry-points.md`](project/entry-points.md:1)
- Coding conventions: [`project/codeStyle.md`](project/codeStyle.md:1)
- Активные задачи текущей итерации: [`operational_scope/tasks_map.md`](operational_scope/tasks_map.md:1)

Если scope задачи уходит в autonomous nested project, переключайся на его local context. Это особенно важно для [`sot_layers/hyper-graph/`](sot_layers/hyper-graph:1), у которого есть собственный `AGENTS.md` и более новый layered canon.

## Рабочие правила

- `docs/` — Source of Truth для реализованной архитектуры.
- `project/` хранит durable repository context, но не канон архитектуры.
- `operational_scope/` хранит operational context задач и не является каноном архитектуры.
- Если работа затрагивает nested repo, Git-операции нужно запускать из его корня; см. [`project/gitContext.md`](project/gitContext.md:1).
