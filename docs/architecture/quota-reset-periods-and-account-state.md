# Quota: reset periods (`DD:HH:MM`) + persisted per-account state (Proposed)

- Status: Proposed
- Date: 2026-03-16

Update:
- 2026-03-18: унификация persisted account state в `account_state.json` + вынесение state в `STATE_DIR`.
- 2026-03-18: `quota_scope`, group snapshot и async writer вынесены в отдельный ADR [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1).

## Цель
Добавить в quota-роутинг два свойства, которые переживают рестарт процесса и не требуют записи в provider accounts-config:

1) **Период восстановления квоты** на модель (вместо «время суток»).
2) **Persisted state** на аккаунт: когда аккаунт использовался последний раз и когда мы зафиксировали исчерпание квоты.

## Source of Truth (самодостаточно)
- ADR: [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)
- Extension ADR: [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1)
- Contracts:
  - Provider accounts-config: [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:1)
  - Account state v1: [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
  - Group snapshot v1: [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1)
  - Legacy state (исторически): [`docs/contracts/state/account-last-used.schema.json`](docs/contracts/state/account-last-used.schema.json:1), [`docs/contracts/state/account-quota-exhausted.schema.json`](docs/contracts/state/account-quota-exhausted.schema.json:1)
- Реализация (точки интеграции):
  - Router: [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:1)
  - Qwen provider: [`llm_agent_platform/api/openai/providers/qwen_code.py`](llm_agent_platform/api/openai/providers/qwen_code.py:1)

Связанное расширение (группа snapshot + STATE_DIR + quota_scope):

- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)

## Breaking изменения в accounts-config

### 1) `model_quota_resets` меняет смысл
Поле `model_quota_resets` **остается по имени**, но теперь означает **период восстановления квоты**.

Формат значения: `DD:HH:MM`.

Примеры:
- `01:00:00` — квота восстанавливается через 1 день
- `07:00:00` — через 7 дней
- `365:00:00` — через 365 дней

Legacy формат `HH:MM` **не поддерживается**.

### 2) Invariant: disjoint groups
Если задан `groups`, то каждый аккаунт может находиться **только в одной группе**.

Это обязательная валидация при загрузке конфига (JSON Schema не может строго проверить disjointness для всех групп).

## Persisted runtime state (вне accounts-config)
Причина вынесения: accounts-config должен оставаться декларативным и не переписываться конкурентными потоками.

### Layout
Рекомендуемая структура (provider-scoped) с отдельной директрорией state:

```
secrets/
  qwen_code/
    accounts_config.json
    accounts/
      lisa.json
      petr.json

<STATE_DIR>/
  qwen_code/
    accounts/
      lisa/
        account_state.json
      petr/
        account_state.json
```

Где:

- `STATE_DIR` — runtime env переменная (обычно смонтирована на HDD).
- `secrets/` остаётся источником credentials и provider-config и читается в основном при старте.

### Форматы state файлов
Единый файл `account_state.json`:

```json
{
  "version": 1,
  "last_used_at": "2026-03-16T12:00:00Z",
  "cooldown": {
    "last_cooldown_at": "2026-03-16T12:05:00Z"
  },
  "quota_exhausted": {
    "keys": {
      "gemini-3-flash-preview-quota": "2026-03-16T03:10:00Z",
      "__provider__": "2026-03-16T03:10:00Z"
    }
  }
}
```

Комментарии:

- `cooldown.last_cooldown_at` используется для восстановления cooldown после рестарта.
- `quota_exhausted.keys`:
  - при `quota_scope=per_model` ключ — фактическое значение `model` из запроса.
  - при `quota_scope=per_provider` ключ — `__provider__`.

Нормативный контракт нового unified state:

- [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)

## Семантика восстановления квоты
Вместо «reset time-of-day», `quota_exhausted_until` вычисляется как:

`quota_exhausted_until = quota_exhausted_at + period(model_quota_resets[model|default])`

Где `quota_exhausted_at` берётся из `account_state.json.quota_exhausted.keys[model_key]`.

## Policy: Qwen token refresh
Цель: не дергать refresh endpoint на каждый запрос и избежать ситуации «refresh не случился из-за свежего last_used_at».

Решение:
1) Перед запросом: если `now - last_used_at > threshold` → refresh.
2) Если upstream вернул 401/403 → refresh и retry один раз.
3) `last_used_at` обновляем только если auth прошёл (т.е. после ответа, который НЕ 401/403). Ошибки quota/rate_limit считаем использованием.

Конфигурация: threshold задается env-переменной (дефолт 180 секунд).

## Связь с существующей канонической архитектурой
Это расширение дополняет текущий канон quota-роутинга:
- [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
