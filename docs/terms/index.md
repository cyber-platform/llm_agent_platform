# Карта scopes терминов

## Назначение

Этот документ является root entry point для терминологии `llm_agent_platform`.

Он нужен, чтобы:

- дать человеку и агенту первую точку входа в `docs/terms/`;
- показать, какие terminology scopes существуют в проекте;
- дать links на все scoped `terms-map.md`.

## Карта scopes

| Scope | Назначение | Entry point |
| --- | --- | --- |
| `project` | Project-specific терминология платформы, архитектуры и provider-centric модели. | [`terms-map.md`](./project/terms-map.md) |

## Правила для scopes

- Каждый scope должен иметь свой `terms-map.md`.
- Individual term pages живут внутри `docs/terms/<scope>/terms/`.
- Scope должен быть достаточно цельным, чтобы его можно было переносить между проектами как reusable terminology package.

## Related documents

- `project` scope: [`terms-map.md`](./project/terms-map.md)
