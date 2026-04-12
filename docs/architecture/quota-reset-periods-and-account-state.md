# Quota reset periods and account state

- Status: superseded
- Date: 2026-03-16

## Назначение

Этот документ больше не является самостоятельным Source of Truth.

Он сохранён как redirect note для старых ссылок на переходный этап, когда reset periods и persisted account state фиксировались в одном месте.

## Что было перенесено в текущий канон

- `model_quota_resets` как период восстановления квоты (`DD:HH:MM`) и provider-agnostic accounts-config semantics: [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1)
- persisted `account_state.json`, `STATE_DIR`, `quota_scope`, group snapshot и async writer: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
- rationale и decision history: [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1), [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1)
- current quota rotation canon: [`docs/architecture/quota-account-rotation-groups-and-models.md`](docs/architecture/quota-account-rotation-groups-and-models.md:1)

## Что осталось исторически важным

- переход от reset time-of-day semantics к period-based `DD:HH:MM`
- переход от mutable accounts-config state к persisted runtime state вне accounts-config
- ранняя фиксация связи между quota exhaustion и persisted per-account state

## Как читать теперь

1. Для текущей quota/config semantics идти в [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1).
2. Для persisted state layout и contracts идти в [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1).
3. Для decision history идти в [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1) и [`docs/adr/0019-state-dir-unified-account-state-and-async-writer.md`](docs/adr/0019-state-dir-unified-account-state-and-async-writer.md:1).
