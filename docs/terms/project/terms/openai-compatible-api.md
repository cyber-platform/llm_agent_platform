# OpenAI-compatible API

## Назначение термина

`OpenAI-compatible API` — [`LLM API protocol`](./llm-api-protocol.md), совместимый по request/response shape с `OpenAI API`, но не принадлежащий только vendor `OpenAI`.

## Роль в проекте

В `llm_agent_platform` `OpenAI-compatible API` является основным public protocol для LLM clients.

Платформа экспонирует provider-scoped routes вида `/<provider_name>/v1/*` и `/<provider_name>/<group_name>/v1/*`, сохраняя совместимость с ожидаемым OpenAI-shaped contract.

## Архитектурная граница

- Это platform-owned public API boundary.
- Это не то же самое, что vendor-specific `OpenAI API`.
- Внутренние [`provider-implementation`](./provider-implementation.md) могут адаптировать этот protocol к vendor-specific upstream APIs, например к `Google Gemini API`.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`llm-api-protocol`](./llm-api-protocol.md)
- [`provider-implementation`](./provider-implementation.md)
