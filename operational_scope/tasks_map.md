# Карта задач

Эта карта отражает только активный backlog после завершения текущего `openai-chatgpt` PoC baseline.

Выполненные PoC-задачи остаются в individual task artifacts и больше не дублируются в этом индексе.

| Задача | Статус | Файл |
| --- | --- | --- |
| Документирование архитектуры ПО и навигационной структуры docs | ongoing | [`operational_scope/tasks/041-software-architecture-documentation.md`](operational_scope/tasks/041-software-architecture-documentation.md:1) |
| Выделение `Backend service` в отдельный repository | completed | [`operational_scope/tasks/053-backend-service-repo-extraction.md`](operational_scope/tasks/053-backend-service-repo-extraction.md:1) |
| Сравнение monitoring semantics для `openai-chatgpt`, `gemini-cli`, `qwen_code` | отложена после PoC | [`operational_scope/tasks/051-provider-monitoring-semantics-comparison-openai-gemini-qwen.md`](operational_scope/tasks/051-provider-monitoring-semantics-comparison-openai-gemini-qwen.md:1) |
| Generalized `monitoring_dimensions[]` contract design | отложена после PoC | [`operational_scope/tasks/050-generalized-monitoring-dimensions-contract-design.md`](operational_scope/tasks/050-generalized-monitoring-dimensions-contract-design.md:1) |
| Двухуровневые usage windows для `openai-chatgpt` | отложена после PoC | [`operational_scope/tasks/039-two-level-openai-chatgpt.md`](operational_scope/tasks/039-two-level-openai-chatgpt.md:1) |
| Env split `.env` + `.env.oauth` и явная инъекция runtime env в контейнер | отложена после PoC | [`operational_scope/tasks/019-env-split-and-explicit-container-env.md`](operational_scope/tasks/019-env-split-and-explicit-container-env.md:1) |
| Миграция Qwen storage naming в kebab-case | отложена после PoC | [`operational_scope/tasks/033-qwen-storage-kebab-case-migration.md`](operational_scope/tasks/033-qwen-storage-kebab-case-migration.md:1) |
| Recovery archive smoke для `repo-archiver` | отложена после PoC | [`operational_scope/tasks/038-recovery-archive-smoke-for-repo-archiver.md`](operational_scope/tasks/038-recovery-archive-smoke-for-repo-archiver.md:1) |
| Auth и RBAC hardening для admin surface | будущая после PoC | [`operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md`](operational_scope/plans/040-admin-surface-auth-and-rbac-hardening.md:1) |
