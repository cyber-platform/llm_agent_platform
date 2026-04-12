# Idea 041: monitoring UI future evolution after current PoC

## Status

- Type: future idea
- Priority: after current docs-first critic cycle

## Why this exists

Текущий PoC intentionally ограничен:

- первый provider page только для `openai-chatgpt`
- local single-user boundary
- polling-only admin UI
- одинаковые thresholds для short and long window только для текущего pilot stage

После завершения текущего docs-first цикла эти направления можно поднимать отдельными stage-2/plan артефактами.

## Future directions

### 1. Multi-provider monitoring pages

- добавить provider-specific pages для других providers
- расширить provider list capabilities
- определить provider-specific columns и drawer sections для каждого нового provider

### 2. Live delivery beyond polling

- оценить SSE или WebSocket для admin monitoring updates
- сохранить current rule: UI всё равно читает backend read-model, а не state files

### 3. Provider-specific presentation tuning

- разрешить отдельные thresholds per provider
- разрешить provider-specific color and severity rules
- разрешить разные window labels и different observability blocks

### 4. Public API evolution only by separate decision

- richer internal/admin taxonomy already допустима
- любое расширение public `429` contract должно идти отдельным архитектурным циклом и отдельным critic review

## Durable references

- [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
- [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md:1)
