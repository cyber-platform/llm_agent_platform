# provider implementation

## Назначение термина

`provider implementation` — конкретная реализация `abstract provider` в коде платформы для общения с конкретным `LLM provider` и адаптации platform public protocol к vendor-specific upstream API.

## Примеры

- `openai-chatgpt`
- `gemini-cli`
- `google-ai-studio`
- `vertex-ai`
- `qwen-code`

## Роль в проекте

В `llm_agent_platform` `provider implementation` materialize-ит transport, auth, quota и response semantics для выбранного `LLM provider` внутри общей provider-centric архитектуры.

Оно не владеет публичным client contract платформы. Публичный contract задается через [`OpenAI-compatible API`](./openai-compatible-api.md), а `provider implementation` при необходимости конвертирует его в vendor-specific upstream protocol, например `Google Gemini API`.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`llm-provider`](./llm-provider.md)
- [`abstract-provider`](./abstract-provider.md)
- [`llm-api-protocol`](./llm-api-protocol.md)
- [`openai-compatible-api`](./openai-compatible-api.md)
