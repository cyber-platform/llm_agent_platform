# abstract provider

## Назначение термина

`abstract provider` — внутренняя абстрактная сущность платформы, представляющая интеграцию с конкретным `LLM provider`.

## Роль в проекте

В `llm_agent_platform` `abstract provider` задаёт provider-centric runtime boundary внутри системы.

Эта сущность нужна, чтобы:

- изолировать platform runtime от provider-specific transport details;
- зафиксировать единый provider-centric способ маршрутизации и выполнения запросов;
- позволить нескольким concrete implementations следовать общей модели интеграции.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`llm-provider`](./llm-provider.md)
- [`provider-implementation`](./provider-implementation.md)
