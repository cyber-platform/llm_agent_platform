# Configuration Index

## Назначение

Этот индекс собирает configuration Source of Truth для `llm_agent_platform`.

Он отделяет env layout, service behavior config и provider accounts config друг от друга.

## Карта документов

| Документ | Назначение |
| --- | --- |
| [`env-files.md`](./env-files.md) | Env layout и правила загрузки `.env` / `.env.oauth`. |
| [`provider-accounts-config.md`](./provider-accounts-config.md) | Provider-agnostic semantics accounts-config и rotation settings. |
| [`service-behavior-config.md`](./service-behavior-config.md) | Сервисные behavior/config contracts вне provider accounts config. |

## Рекомендуемый маршрут

1. [`env-files.md`](./env-files.md)
2. [`service-behavior-config.md`](./service-behavior-config.md)
3. [`provider-accounts-config.md`](./provider-accounts-config.md)

## Related documents

- root docs map: [`index.md`](../index.md)
- contracts: [`index.md`](../contracts/index.md)
- providers: [`index.md`](../providers/index.md)
