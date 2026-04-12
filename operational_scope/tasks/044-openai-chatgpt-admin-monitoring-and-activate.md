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

- [`docs/architecture/poc-openai-chatgpt-demo.md`](../../docs/architecture/poc-openai-chatgpt-demo.md)
- [`docs/architecture/admin-monitoring-read-model.md`](../../docs/architecture/admin-monitoring-read-model.md)
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

## Execution Status

- Current State: запланирована.
- Next Step: materialize admin blueprint и in-memory override store.
- Blockers: none.
