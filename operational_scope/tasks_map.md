# Карта задач

Эта карта отражает только активный backlog после завершения текущего `openai-chatgpt` PoC baseline.

Выполненные PoC-задачи остаются в individual task artifacts и больше не дублируются в этом индексе.

| Задача | Статус | Файл |
| --- | --- | --- |
| Адаптация `user_service` под platform auth baseline для `PoC2` | completed | [`operational_scope/tasks/055-user-service-platform-auth-baseline.md`](operational_scope/tasks/055-user-service-platform-auth-baseline.md:1) |
| Backend admin JWT guard через `user_service` shared-secret baseline | complited | [`operational_scope/tasks/056-backend-admin-jwt-guard-via-user-service.md`](operational_scope/tasks/056-backend-admin-jwt-guard-via-user-service.md:1) |
| Frontend login page и protected admin shell для `PoC2` | planned | [`operational_scope/tasks/057-frontend-login-and-protected-admin-shell.md`](operational_scope/tasks/057-frontend-login-and-protected-admin-shell.md:1) |
| Документирование архитектуры ПО и навигационной структуры docs | ongoing | [`operational_scope/tasks/041-software-architecture-documentation.md`](operational_scope/tasks/041-software-architecture-documentation.md:1) |
| Сравнение monitoring semantics для `openai-chatgpt`, `gemini-cli`, `qwen_code` | отложена после PoC | [`operational_scope/tasks/051-provider-monitoring-semantics-comparison-openai-gemini-qwen.md`](operational_scope/tasks/051-provider-monitoring-semantics-comparison-openai-gemini-qwen.md:1) |
| Generalized `monitoring_dimensions[]` contract design | отложена после PoC | [`operational_scope/tasks/050-generalized-monitoring-dimensions-contract-design.md`](operational_scope/tasks/050-generalized-monitoring-dimensions-contract-design.md:1) |
| Env split `.env` + `.env.oauth` и явная инъекция runtime env в контейнер | отложена после PoC | [`operational_scope/tasks/019-env-split-and-explicit-container-env.md`](operational_scope/tasks/019-env-split-and-explicit-container-env.md:1) |
| Миграция Qwen storage naming в kebab-case | отложена после PoC | [`operational_scope/tasks/033-qwen-storage-kebab-case-migration.md`](operational_scope/tasks/033-qwen-storage-kebab-case-migration.md:1) |
| Recovery archive smoke для `repo-archiver` | отложена после PoC | [`operational_scope/tasks/038-recovery-archive-smoke-for-repo-archiver.md`](operational_scope/tasks/038-recovery-archive-smoke-for-repo-archiver.md:1) |
| Auth и RBAC hardening для admin surface | будущая после PoC | [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md:1) |
