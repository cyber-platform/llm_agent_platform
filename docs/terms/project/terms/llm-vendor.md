# LLM Vendor

## Назначение термина

`LLM Vendor` — компания или внешний владелец LLM-платформ и model access surfaces.

Важно: один `LLM Vendor` может предоставлять несколько разных `LLM provider`.

## Примеры

- `LLM Vendor`: `Google`
  - `LLM provider`: `Google Gemini CLI`
  - `LLM provider`: `Google AI Studio`
  - `LLM provider`: `Google Vertex AI`
- `LLM Vendor`: `OpenAI`
- `LLM Vendor`: `Alibaba`

## Роль в проекте

В `llm_agent_platform` `LLM Vendor` является более высоким внешним уровнем группировки, чем `LLM provider`.

Этот термин нужен, чтобы не смешивать:

- компанию-вендора;
- внешнюю platform surface доступа к моделям;
- внутреннюю provider-centric абстракцию платформы.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`llm-provider`](./llm-provider.md)
