# ADR 0021: account-centric provider monitoring and admin read-model boundary

- Status: Accepted
- Date: 2026-04-05
- Related:
  - [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:1)
  - [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)

## Контекст

Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) платформа получила richer monitoring semantics:

- short и long usage windows;
- request-driven observability state;
- provider-specific quota interpretation;
- admin monitoring UI с provider-specific page и drawer.

Старый baseline с legacy `usage-limits` snapshot и file-oriented assumptions перестал быть достаточным:

- monitoring truth и routing truth смешивались;
- persisted files могли быть ошибочно восприняты как live UI source;
- public `429` surface рисковал дрейфовать вслед за internal taxonomy;
- `Activate` action оставался семантически расплывчатым.

## Решение

1. Для provider-specific monitoring вводится account-centric boundary:
   - `account_state.json` — routing/runtime truth;
   - `usage_windows.json` — provider-specific monitoring truth;
   - `request_usage.json` — request-driven observability truth;
   - `quota_state.json` — group-level derived snapshot.

2. Runtime работает по in-memory-first модели:
   - runtime и admin UI используют in-memory state;
   - persisted files нужны только для restore after restart и audit trail.

3. Все mutable state files пишутся только через shared async writer с coalesce semantics.

4. Public OpenAI-compatible `429` contract не расширяется:
   - публично допустимы только `all_accounts_on_cooldown` и `all_accounts_exceed_quota`;
   - richer quota taxonomy остаётся internal/admin-only.

5. Admin monitoring UI получает данные только через backend admin read-model:
   - provider list — общий контракт;
   - provider page и drawer — provider-specific contracts.

6. Для текущего PoC no-auth admin surface допустима только в local single-user boundary.

7. `Activate` фиксируется как session-scoped in-memory preferred-account override и не меняет provider config files.

## Contract changes

- present

Новые или обновлённые контракты:

- [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
- [`docs/contracts/state/openai-chatgpt-usage-windows.schema.json`](docs/contracts/state/openai-chatgpt-usage-windows.schema.json:1)
- [`docs/contracts/state/openai-chatgpt-request-usage.schema.json`](docs/contracts/state/openai-chatgpt-request-usage.schema.json:1)
- [`docs/contracts/api/admin/monitoring/providers-list.schema.json`](docs/contracts/api/admin/monitoring/providers-list.schema.json:1)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)

## Alternatives considered

### A. Сохранить legacy `usage-limits` snapshot как канон

- Плюсы: меньше immediate изменений.
- Минусы: не разделяет monitoring truth и request observability, не даёт clean contract-first основу для admin UI.

### B. Читать admin UI напрямую из persisted files

- Плюсы: проще первый прототип.
- Минусы: UI становится зависимым от async flush timing и file races.

### C. Расширить public `429` surface provider-specific codes

- Плюсы: более богатая публичная диагностика.
- Минусы: contract drift, coupling к provider-specific semantics и усложнение multi-provider boundary.

## Последствия

### Положительные

- docs и contracts получают единый канонический boundary для provider monitoring;
- admin UI можно развивать без протечки persisted-file semantics в delivery path;
- public API остаётся стабильным при richer internal taxonomy;
- provider-specific monitoring pages и drawers становятся архитектурно допустимым pattern.

### Негативные

- legacy `usage-limits` contract выводится из канона;
- появляется несколько новых contracts и docs, которые нужно держать синхронными;
- future auth/RBAC hardening остаётся отдельным этапом после PoC.

## Условия пересмотра

- Если admin surface выйдет за пределы local single-user PoC.
- Если потребуется расширить public `429` schema provider-specific codes.
- Если provider-specific pages нужно будет унифицировать в более строгий cross-provider contract.
