# Admin monitoring read-model и `Activate` для `openai-chatgpt`

## Контекст

PoC требует локальный operator `Web UI`, который показывает quota/account status для `openai-chatgpt` и позволяет переключать preferred account по клику мыши.

Monitoring contracts и `Activate` response contract уже зафиксированы в `docs/contracts/`.

## Goal

Реализовать admin monitoring read-model endpoints и process-global in-memory `Activate` semantics для групп `openai-chatgpt`.

## Scope

В scope:

- `GET /admin/monitoring/providers`;
- `GET /admin/monitoring/openai-chatgpt`;
- `POST /admin/monitoring/openai-chatgpt/groups/<group_id>/accounts/<account_name>/activate`;
- read-model сборка из runtime state, usage snapshots и provider config;
- process-global in-memory preferred-account override per `(provider_id, group_id)`;
- tests для provider page и activate semantics.

Не входит в scope:

- React UI;
- public auth guard;
- public exposure.

## Canonical references

- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](../../docs/architecture/admin-monitoring-refresh-subsystem.md)
- [`docs/contracts/api/admin/monitoring/providers-list.schema.json`](../../docs/contracts/api/admin/monitoring/providers-list.schema.json)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](../../docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json)
- [`docs/contracts/api/admin/monitoring/openai-chatgpt-activate-account-response.schema.json`](../../docs/contracts/api/admin/monitoring/openai-chatgpt-activate-account-response.schema.json)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)

## Dependencies

- Блокеров по архитектуре нет.
- Может выполняться параллельно с [`042-openai-chatgpt-api-key-registry-and-admin-crud.md`](042-openai-chatgpt-api-key-registry-and-admin-crud.md).
- Является backend dependency для [`045-react-frontend-openai-chatgpt-poc-ui.md`](045-react-frontend-openai-chatgpt-poc-ui.md).

## Implementation notes

1. Frontend должен читать только admin API, а не persisted state files.
2. `Activate` должен менять только process memory.
3. `Activate` не должен bypass-ить cooldown/exhausted/group isolation safeguards.
4. Provider list для PoC должен фактически отдавать только `openai-chatgpt`.

## Definition of Done

- Monitoring endpoints возвращают payloads, совместимые с contract schemas.
- `Activate` возвращает schema-compatible response.
- После `Activate` provider page отражает preferred account marker.
- Restart-safe persistence для override не требуется.
- Добавлены тесты suite `TS-ADMIN-MONITORING-READ-MODEL` и связанный test-map update.

## Что реализовано

- В `llm_agent_platform/api/admin/routes.py` materialized admin monitoring endpoints `GET /admin/monitoring/providers`, `GET /admin/monitoring/openai-chatgpt` и `POST /admin/monitoring/openai-chatgpt/groups/<group_id>/accounts/<account_name>/activate`.
- В `llm_agent_platform/services/openai_chatgpt_admin_monitoring.py` добавлен provider-specific read-model builder для `openai-chatgpt`, который собирает provider page из provider config, router runtime state, `usage_windows` snapshots и `request_usage` snapshots.
- В read-model добавлен fallback для legacy `limits.json`, чтобы backend мог materialize provider page даже при старом persisted layout, но canonical response остаётся совместимым с текущими admin contracts.
- В `llm_agent_platform/services/account_router.py` добавлен process-global preferred-account override per `(provider_id, group_id)` и introspection API `describe_group(...)` / `get_preferred_account(...)` / `set_preferred_account(...)` для admin read-model.
- Routing semantics сохранены: preferred override используется только если account доступен; cooldown и quota-exhausted safeguards по-прежнему блокируют выбор account и не bypass-ятся action `Activate`.
- Для provider page backend выставляет `is_preferred_for_session`, `routing.state`, `block_reason`, `quota_blocked_until`, `drawer.raw_monitoring_payload`, `drawer.raw_request_usage_payload` и `drawer.raw_account_state_payload`.
- В `llm_agent_platform/tests/test_admin_monitoring_read_model.py` добавлены test cases `TC-ADMIN-MONITORING-READ-MODEL-001..003` на provider list, provider page contract и `Activate` semantics без bypass cooldown.
- В `docs/testing/suites/admin-monitoring-read-model.md` и `docs/testing/test-map.md` suite `TS-ADMIN-MONITORING-READ-MODEL` переведена из `planned` в `active`, добавлен target command `uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_read_model.py`.
- Выполнена verification прогоном `uv run python -m unittest llm_agent_platform/tests/test_admin_monitoring_read_model.py`, `uv run python -m unittest llm_agent_platform/tests/test_admin_api_keys.py`, `uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_runtime.py` и `uv run python -m compileall llm_agent_platform`.

## Execution Status

- Current State: реализована.
- Next Step: использовать backend contracts в `045-react-frontend-openai-chatgpt-poc-ui.md`.
- Blockers: none.
