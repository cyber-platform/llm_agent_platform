# persist

## Назначение термина

`persist` — сохранить runtime state из памяти в устойчивое хранилище.

## Роль в проекте

В `llm_agent_platform` этот термин используется для записи account state, group snapshots и provider-specific monitoring state в `STATE_DIR`.

Типичный смысл:

- взять актуальное in-memory state;
- подготовить payload для записи;
- записать его на диск синхронно или через async writer.

## Связанные документы

- [`terms-map.md`](../terms-map.md)
- [`hydrate`](./hydrate.md)
