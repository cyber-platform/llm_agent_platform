# Plan: implement two-level usage windows for `openai-chatgpt`

## Purpose

Этот plan больше не является архитектурным SoT.

Его задача — зафиксировать implementation sequence поверх уже обновлённого канона в `docs/`.

## Engineering SoT

Реализация обязана опираться на:

- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- [`docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md`](docs/adr/0021-account-centric-provider-monitoring-and-admin-read-model.md:1)
- [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- [`docs/contracts/state/openai-chatgpt-usage-windows.schema.json`](docs/contracts/state/openai-chatgpt-usage-windows.schema.json:1)
- [`docs/contracts/state/openai-chatgpt-request-usage.schema.json`](docs/contracts/state/openai-chatgpt-request-usage.schema.json:1)
- [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1)

## Delivery slices

1. Обновить runtime path resolution под canonical account-centric layout.
2. Разделить monitoring truth (`usage_windows.json`) и request observability (`request_usage.json`).
3. Ввести provider-specific quota handler для `openai-chatgpt`.
4. Перевести `usage_limit_reached` на normalized `block_account_until` semantics.
5. Подключить shared async persistence path для новых artifacts.
6. Обновить или добавить тесты по state persistence и public `429` boundary.

## Verification references

- [`docs/testing/suites/quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md:1)
- [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)
- [`docs/testing/test-map.md`](docs/testing/test-map.md:1)

## Non-goals of this plan

- не переопределять архитектуру вне `docs/`
- не описывать future auth/RBAC hardening
- не расширять public `429` contract

## Future work moved out

Future-only направления вынесены из current focus:

- auth/RBAC hardening: [`tasks_descriptions/plans/040-admin-surface-auth-and-rbac-hardening.md`](tasks_descriptions/plans/040-admin-surface-auth-and-rbac-hardening.md:1)
- monitoring UI evolution: [`tasks_descriptions/ideas/041-monitoring-ui-future-evolution.md`](tasks_descriptions/ideas/041-monitoring-ui-future-evolution.md:1)
