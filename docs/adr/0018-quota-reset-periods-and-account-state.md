# ADR-0018: Breaking — quota reset periods + persisted account state + disjoint groups

- Status: Proposed
- Date: 2026-03-16
- Related:
  - [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
  - [`docs/adr/0014-stream-state-container-and-429-rotation-policy.md`](docs/adr/0014-stream-state-container-and-429-rotation-policy.md:1)
  - [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1)

## Контекст
Quota-роутер сейчас:
- интерпретирует `model_quota_resets` как время суток `HH:MM` (time-of-day reset),
- хранит exhausted state только в памяти (теряется при рестарте),
- Qwen refresh делает на каждый запрос, что вызывает лишние refresh вызовы.

Нужно:
1) Поддержать модели с квотами на дни/недели/произвольные периоды.
2) Переживать рестарт процесса, сохраняя исчерпание квоты и недавнее использование аккаунта.
3) Избежать конкурентной перезаписи provider config в рантайме.

## Решение
1) `model_quota_resets` переопределяется как **период восстановления квоты**.
   - Формат: `DD:HH:MM`.
   - Legacy `HH:MM` не поддерживается.

2) Вводится persisted runtime state вне provider-config:
   - `last_used_at` (для idle-refresh и диагностики)
   - `quota_exhausted_at` per-model (чтобы после рестарта понимать, восстановилась квота или нет)

3) Вводится обязательный инвариант disjoint-groups:
   - один аккаунт не может входить более чем в одну группу.

4) Для Qwen вводится token refresh policy:
   - refresh по idle-threshold,
   - refresh + retry один раз на 401/403,
   - last_used_at обновляется только если auth прошёл.

## Альтернативы
### A) Хранить runtime state внутри accounts-config
- Минусы: гонки записей, конфиг перестает быть декларативным.

### B) Оставить reset time-of-day и не делать periods
- Минусы: не выражает недельные/длинные квоты, зависит от timezone.

### C) Один общий JSON state на провайдера
- Минусы: нужна синхронизация/lock, сложнее безопасная конкуренция.

## Последствия
### Позитивные
- Exhausted state переживает рестарт → меньше ложных 429 и более детерминированный роутинг.
- Period-based reset легко выражает любые окна квот в днях.
- Refresh Qwen становится реже и управляемее.

### Негативные
- Breaking изменение формата `model_quota_resets`.
- Добавляется файловое состояние в `secrets/<provider>/state`.

## Contract changes
- present

Контракты:
- Provider accounts-config: [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:1)
- last_used_at state: [`docs/contracts/state/account-last-used.schema.json`](docs/contracts/state/account-last-used.schema.json:1)
- quota_exhausted state: [`docs/contracts/state/account-quota-exhausted.schema.json`](docs/contracts/state/account-quota-exhausted.schema.json:1)

## Условия пересмотра
- Если потребуется календарная семантика «месяц/неделя по timezone», а не дни.
- Если появится многопроцессный режим на одной машине и потребуется строгий file-lock.

## Update (2026-03-18)

Persisted state контур расширен отдельным решением:

- runtime state вынесен из `secrets/` в `STATE_DIR`;
- split state layout унифицирован в `account_state.json`;
- добавлены `quota_scope`, group snapshot `quota_state.json` и async writer semantics.

Это зафиксировано в [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1).
