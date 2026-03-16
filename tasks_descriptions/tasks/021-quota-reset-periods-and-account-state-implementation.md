# Task: Реализовать period-based quota reset + persisted account state + Qwen idle refresh

## Контекст
- Источник: каноническая документация в `docs/` (breaking изменения в quota контуре).
- Связанные артефакты:
  - Архитектура: [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
  - ADR: [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)
  - Provider accounts-config schema: [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:1)
  - Account state schemas:
    - [`docs/contracts/state/account-last-used.schema.json`](docs/contracts/state/account-last-used.schema.json:1)
    - [`docs/contracts/state/account-quota-exhausted.schema.json`](docs/contracts/state/account-quota-exhausted.schema.json:1)

## Architecture Context References
- [ ] Канон rotation+groups: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)
- [ ] ADR-0018 (breaking): [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)

## Specification References
- [ ] Provider accounts-config contract: [`docs/contracts/config/provider-accounts-config.schema.json`](docs/contracts/config/provider-accounts-config.schema.json:1)
- [ ] Persisted state contracts: [`docs/contracts/state/account-last-used.schema.json`](docs/contracts/state/account-last-used.schema.json:1), [`docs/contracts/state/account-quota-exhausted.schema.json`](docs/contracts/state/account-quota-exhausted.schema.json:1)

## Test Design References
- [ ] Suite: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
- [ ] Test map: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Workflow References
- [ ] none

## Цель
- Перевести quota reset на период `DD:HH:MM` (breaking) и добавить persisted runtime state (last_used + quota_exhausted) в `secrets/<provider>/state/...`, чтобы exhausted и refresh policy переживали рестарт процесса.

## Шаги реализации
- [ ] Ввести state-store слой (чтение/запись):
  - `last_used_at.json` per account
  - `quota_exhausted/<model>.json` per account+model
  - atomic write (tmp -> rename)
- [ ] Обновить loader provider-config:
  - строго парсить `model_quota_resets` как `DD:HH:MM`
  - валидировать disjoint groups (аккаунт не может быть в нескольких группах)
- [ ] Обновить quota router state:
  - хранить/восстанавливать exhausted из persisted state
  - вычислять exhausted-until как `quota_exhausted_at + period`
- [ ] Обновить Qwen provider:
  - refresh по idle-threshold (env, default=180)
  - на 401/403: refresh + retry один раз
  - `last_used_at` обновлять только если ответ не 401/403
- [ ] Обновить дефолтные пути в [`config.py`](config.py:1) под provider-scoped layout (`secrets/qwen_code/*`, `secrets/gemini_cli/*`).

## Definition of Done
- [ ] Реализация соответствует канонической документации в [`docs/architecture/quota-reset-periods-and-account-state.md`](docs/architecture/quota-reset-periods-and-account-state.md:1)
- [ ] Все unit/integration тесты проходят
- [ ] Проведена проверка синтаксиса `compileall`
- [ ] Документация не требует ссылок на `plans/`

## Execution Status
- Current State: task создан, реализация не начата.
- Next Step: добавить state-store модуль и подключить чтение persisted exhausted в [`services/account_router.py`](services/account_router.py:1).
- Blockers: none
- Contract Changes: present
- Verification: `uv run python -m unittest discover -s tests -p "test_*.py"`
