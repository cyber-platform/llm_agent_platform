# Task: Обновить тесты под period-based quota reset + persisted account state + disjoint groups

## Контекст
- Источник: каноническая документация в `docs/` (breaking изменения в quota контуре).
- Связанные артефакты:
  - Архитектура: [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
  - ADR: [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)
  - Test design suite: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)

## Architecture Context References
- [ ] Канон расширения: [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
- [ ] ADR-0018: [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)

## Specification References
- [ ] Provider accounts-config schema: [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:1)
- [ ] State schemas: [`docs/contracts/state/account-last-used.schema.json`](docs/contracts/state/account-last-used.schema.json:1), [`docs/contracts/state/account-quota-exhausted.schema.json`](docs/contracts/state/account-quota-exhausted.schema.json:1)

## Test Design References
- [ ] Suite: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
- [ ] Test map: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [ ] none

## Цель
- Обновить/добавить тесты так, чтобы новое поведение (period-based reset + persisted exhausted + disjoint groups + Qwen idle refresh policy) было зафиксировано в автотестах.

## Шаги реализации
- [ ] Обновить тестовые фикстуры provider-config:
  - `model_quota_resets` теперь `DD:HH:MM` (breaking)
  - группы должны быть disjoint
- [ ] Добавить тесты period-based reset:
  - exhausted-until = exhausted-at + period
- [ ] Добавить тесты persisted exhausted state:
  - после «рестарта» (новый инстанс router + тот же state dir) поведение сохраняется
- [ ] Добавить тест на disjoint group validation:
  - пересечение аккаунтов в группах → config error
- [ ] Добавить/обновить тесты Qwen refresh policy (mock):
  - idle-refresh по `last_used_at`
  - refresh+retry один раз на 401/403

## Definition of Done
- [ ] Все тесты проходят локально
- [ ] Suite документация остаётся согласованной с тестами
- [ ] Нет ссылок на `plans/` в docs

## Execution Status
- Current State: task создан, тесты не обновлены.
- Next Step: обновить `tests/test_quota_account_router.py` и `tests/test_refactor_p2_routes.py` фикстуры `model_quota_resets` на `DD:HH:MM`.
- Blockers: none
- Contract Changes: none
- Verification: `uv run python -m unittest discover -s tests -p "test_*.py"`
