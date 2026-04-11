# provider implementation

## Назначение термина

`provider implementation` — конкретная реализация `abstract provider` в коде платформы для общения с конкретным `LLM provider`.

## Примеры

- `openai-chatgpt`
- `gemini-cli`
- `google-ai-studio`
- `vertex-ai`
- `qwen-code`

## Роль в проекте

В `llm_agent_platform` `provider implementation` materialize-ит transport, auth, quota и response semantics для выбранного `LLM provider` внутри общей provider-centric архитектуры.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`llm-provider`](./llm-provider.md)
- [`abstract-provider`](./abstract-provider.md)
