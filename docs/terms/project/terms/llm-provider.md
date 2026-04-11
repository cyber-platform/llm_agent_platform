# LLM provider

## Назначение термина

`LLM provider` — внешняя система доступа к LLM-моделям со своим catalog, auth-mechanism, quota semantics и usage policy.

Важно: `LLM provider` не равен компании-вендору как таковой. Один [`LLM Vendor`](./llm-vendor.md) может предоставлять несколько разных `LLM provider` surfaces.

## Примеры

- `LLM Vendor`: `OpenAI`
  - `LLM provider`: `OpenAI ChatGPT`
- `LLM Vendor`: `Google`
  - `LLM provider`: `Google Gemini CLI`
  - `LLM provider`: `Google AI Studio`
  - `LLM provider`: `Google Vertex AI`

## Роль в проекте

В `llm_agent_platform` `LLM provider` является внешней system boundary, с которой взаимодействует платформа через внутренние `abstract provider` и их `provider implementation`.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`llm-vendor`](./llm-vendor.md)
- [`abstract-provider`](./abstract-provider.md)
- [`provider-implementation`](./provider-implementation.md)
