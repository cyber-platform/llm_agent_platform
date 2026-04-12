# hydrate

## Назначение термина

`hydrate` — восстановить in-memory state из persisted state.

## Роль в проекте

В `llm_agent_platform` этот термин используется для lazy loading runtime state из `STATE_DIR` после старта процесса или при первом доступе.

Типичный смысл:

- прочитать persisted snapshot с диска;
- собрать по нему рабочее состояние в памяти;
- продолжить обработку запросов уже через in-memory state.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`persist`](./persist.md)
