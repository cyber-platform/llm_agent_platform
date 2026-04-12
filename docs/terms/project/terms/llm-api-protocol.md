# LLM API protocol

## Назначение термина

`LLM API protocol` — общий термин для стандарта API-взаимодействия с LLM: request shape, response shape, streaming semantics, tool-calling envelope и error boundary.

## Роль в проекте

В `llm_agent_platform` этот термин нужен, чтобы явно разделять:

- публичный protocol, который платформа экспонирует клиентам;
- vendor-specific protocols внешних LLM systems;
- внутренние `provider implementation`, которые адаптируют один protocol к другому.

## Канонические подтипы

- [`OpenAI-compatible API`](./openai-compatible-api.md) — основной public protocol платформы.
- `OpenAI API` — vendor-specific protocol от `OpenAI`.
- `Anthropic API` — vendor-specific protocol от `Anthropic`.
- `Google Gemini API` — vendor-specific protocol от `Google`.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`openai-compatible-api`](./openai-compatible-api.md)
- [`provider-implementation`](./provider-implementation.md)
- [`llm-provider`](./llm-provider.md)
