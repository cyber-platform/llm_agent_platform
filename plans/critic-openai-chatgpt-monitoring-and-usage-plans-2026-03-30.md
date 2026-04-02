# Critic report: monitoring UI + two-level usage windows plans

- Date: 2026-03-30
- Target feature / plan: [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1), [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1)
- Target task set: source task [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1) + будущая декомпозиция в [`tasks_descriptions/tasks/`](tasks_descriptions/tasks:1)
- Critic execution profile: role=Critic, reasoning level=4, skills=[`critic-taskset-semantic-critique`](../../../../.kilocode/skills-critic/critic-taskset-semantic-critique/SKILL.md:1), [`critic-taskset-semantic-critique-llm-platform`](.kilocode/skills-critic/critic-taskset-semantic-critique-llm-platform/SKILL.md:1)
- Storage note: отчёт сохранён в [`plans/`](plans:1) по явному запросу пользователя; канонический runtime-путь для critic report по skill остаётся [`tasks_descriptions/feedback/critic/`](tasks_descriptions/feedback/critic:1)

## Executive summary

- Overall assessment: `needs-return-to-stage-2`
- High-severity findings count: 4
- Recommended immediate action: зафиксировать state/contracts/admin semantics до разбиения планов на Stage 3 задачи

## Findings

### Finding F-001: план вводит новый state/read-model без замороженного contract boundary

- Severity: `high`
- Problem: планы фактически переводят provider monitoring c текущего snapshot [`limits.json`](llm_agent_platform/services/runtime_state_paths.py:37) и контракта [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) на новый account-centric набор артефактов [`usage_windows.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:173), [`request_usage.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:174), refresh metadata и admin read-model endpoint [`GET /admin/monitoring/providers/openai-chatgpt/accounts`](plans/openai-chatgpt-monitoring-frontend-prototype.md:242). При этом в каноне всё ещё закреплены старые storage и schema assumptions через [`docs/auth.md`](docs/auth.md:176), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:104) и текущую реализацию [`OpenAIChatGptUsageLimitsAdapter.write_snapshot()`](llm_agent_platform/services/provider_usage_limits.py:91).
- Impact: если декомпозировать планы в задачи прямо сейчас, backend, runtime state и UI почти наверняка будут опираться на разные формы Source of Truth. Это создаст скрытый contract drift, миграционный хвост и конфликт между документацией, тестами и фактическим storage layout.
- Evidence / references:
  - текущий snapshot contract: [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1)
  - текущий путь snapshot: [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48)
  - новый layout из плана: [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:163)
  - новый admin read-model из плана: [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:219)
- Proposed fix:
  - [ ] Вернуть решение в Stage 2 и сначала заморозить platform-level contracts для [`usage_windows.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:173), [`request_usage.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:174) и admin read-model payload.
  - [ ] Синхронизировать [`docs/auth.md`](docs/auth.md:176), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:102), [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:73) и runtime path rules до появления implementation tasks.
  - [ ] Явно решить, заменяет ли новый layout старый [`limits.json`](llm_agent_platform/services/runtime_state_paths.py:37) или требует миграционного bridge.
- Traceability:
  - Plans to update: [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1), [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1)
  - Tasks to update / create: [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1), новый Stage 3 task в [`tasks_descriptions/tasks/`](tasks_descriptions/tasks:1) для contract freeze + docs sync

### Finding F-002: не определён единый owner для shared state и write path

- Severity: `high`
- Problem: план правильно разделяет monitoring truth и routing truth, но не назначает owner boundaries для записи в [`account_state.json`](docs/contracts/state/account-state.schema.json:1), [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1), [`usage_windows.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:173) и [`request_usage.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:174). Сейчас роутер пишет persisted state через [`QuotaAccountRouter.register_event()`](llm_agent_platform/services/account_router.py:274) и [`QuotaAccountRouter._enqueue_group_snapshot_unlocked()`](llm_agent_platform/services/account_router.py:737), а usage adapter отдельно пишет snapshot через [`OpenAIChatGptUsageLimitsAdapter.write_snapshot()`](llm_agent_platform/services/provider_usage_limits.py:91). Архитектурный канон при этом ожидает write-behind/coalesce semantics через [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:222).
- Impact: после разбиения на задачи разные исполнители могут независимо менять одни и те же state artifacts, но с разной freshness semantics. Результат — race conditions, stale admin UI, неочевидные overwrite-конфликты и нарушение гарантии «один артефакт — один владелец».
- Evidence / references:
  - mutation points канона: [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:232)
  - текущая sync запись usage snapshot: [`OpenAIChatGptUsageLimitsAdapter.write_snapshot()`](llm_agent_platform/services/provider_usage_limits.py:91)
  - текущая запись router state: [`QuotaAccountRouter._persist_account_state_unlocked()`](llm_agent_platform/services/account_router.py:701)
  - новый split monitoring/runtime файлов: [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:138)
- Proposed fix:
  - [ ] До декомпозиции добавить ownership matrix: кто пишет, кто читает, кто инициирует refresh, какой freshness SLA у каждого state artifact.
  - [ ] Явно указать, какие файлы обязаны проходить через единый async writer, а какие допускают отдельный sync write path.
  - [ ] Зафиксировать lifecycle для forced refresh, startup warmup и refresh-on-unblock так, чтобы они не порождали независимые write paths в один и тот же snapshot.
- Traceability:
  - Plans to update: [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:111), [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:344)
  - Tasks to update / create: [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1), новые Stage 3 tasks в [`tasks_descriptions/tasks/`](tasks_descriptions/tasks:1) для state ownership и persistence/tests sync

### Finding F-003: новая quota semantics не замораживает внешний OpenAI-compatible error surface

- Severity: `high`
- Problem: план меняет смысл [`429 usage_limit_reached`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:91) с generic exhausted на временный short-window block, а UI-план добавляет статусы [`blocked_short_window`](plans/openai-chatgpt-monitoring-frontend-prototype.md:164), [`blocked_long_window`](plans/openai-chatgpt-monitoring-frontend-prototype.md:165), [`refresh_failed`](plans/openai-chatgpt-monitoring-frontend-prototype.md:166) и [`stale`](plans/openai-chatgpt-monitoring-frontend-prototype.md:167). Но публичный контракт [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1) по-прежнему знает только [`all_accounts_on_cooldown`](docs/contracts/api/openai/errors/429-error.schema.json:46) и [`all_accounts_exceed_quota`](docs/contracts/api/openai/errors/429-error.schema.json:65). Планы не фиксируют, какие состояния остаются внутренними admin-only, а какие отражаются клиенту через OpenAI-compatible API.
- Impact: при разбиении на задачи неизбежно появятся взаимоисключающие реализации: одна команда будет менять внутренний routing state, другая — внешний `429` envelope, третья — UI taxonomy. Это прямой риск contract drift на публичной API surface.
- Evidence / references:
  - новая трактовка [`usage_limit_reached`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:91)
  - существующий `429` contract: [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1)
  - текущая тестовая suite по API surface: [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)
  - текущая quota suite: [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
- Proposed fix:
  - [ ] Вернуть решение в Stage 2 и заморозить boundary: какие provider-specific quota states остаются internal/admin-only, а какие маппятся в публичный [`429`](docs/contracts/api/openai/errors/429-error.schema.json:1).
  - [ ] Если внешний envelope меняется, сначала обновить schema и provider docs, а потом декомпозировать implementation tasks.
  - [ ] Добавить в план explicit traceability до [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1) и [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1).
- Traceability:
  - Plans to update: [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:89), [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:157)
  - Tasks to update / create: [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1), новый Stage 3 task в [`tasks_descriptions/tasks/`](tasks_descriptions/tasks:1) для error-surface/tests freeze

### Finding F-004: `Activate` action конфликтует с каноном groups и rounding semantics

- Severity: `high`
- Problem: UI-план вводит mutating endpoint [`POST /admin/monitoring/providers/openai-chatgpt/accounts/<account_name>/activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:308) как будто у provider существует единый глобальный `active account`. Но в текущем каноне [`active_account`](docs/examples/openai_chatgpt_accounts_config.example.json:2) имеет определённый смысл прежде всего для `single`, тогда как `rounding` работает через pool selection и state isolation по ключу [`(provider, group_id)`](llm_agent_platform/services/account_router.py:119). Дополнительно UI-план использует группу [`g0`](plans/openai-chatgpt-monitoring-frontend-prototype.md:258), тогда как канон default group в конфиге и маршрутизации описан иначе — через первую группу или весь provider pool в [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:122) и [`QuotaAccountRouter._resolve_pool()`](llm_agent_platform/services/account_router.py:629).
- Impact: если разложить это в задачи без архитектурной фиксации, команды реализуют несовместимые модели: provider-wide pin, per-group pin, single-only activation или редактирование config-файла на лету. Это уже не деталь UI, а изменение routing semantics.
- Evidence / references:
  - activate action в плане: [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:306)
  - current accounts-config example: [`docs/examples/openai_chatgpt_accounts_config.example.json`](docs/examples/openai_chatgpt_accounts_config.example.json:1)
  - default group semantics: [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:122)
  - runtime pool resolution: [`QuotaAccountRouter._resolve_pool()`](llm_agent_platform/services/account_router.py:629)
- Proposed fix:
  - [ ] До декомпозиции либо сузить пилот до read-only monitoring UI, либо вернуть в Stage 2 и заморозить одну из семантик activation: single-only, per-group override, provider-wide temporary pin с TTL.
  - [ ] Привести group identity в UI-плане к канонической модели runtime и отказаться от неявного смешения [`g0`](llm_agent_platform/services/account_router.py:125) с operator-facing named groups.
  - [ ] Если activation меняет routing behavior, это должно быть отражено не только в UI-плане, но и в provider/runtime docs и test contour.
- Traceability:
  - Plans to update: [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147), [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:251)
  - Tasks to update / create: [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1), новый Stage 3 task в [`tasks_descriptions/tasks/`](tasks_descriptions/tasks:1) для admin mutating actions

### Finding F-005: boundary для no-auth admin surface допустима для PoC, но должна быть явно помечена как временная

- Severity: `low`
- Problem: пилот явно декларирует [`без авторизации`](plans/openai-chatgpt-monitoring-frontend-prototype.md:9) и включает mutating action [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147). Для локального PoC на одном ПК это допустимое практическое допущение, но оно пока не помечено как временное и контекстно-ограниченное решение.
- Impact: для текущего локального PoC риск низкий, но при переносе прототипа в shared/dev/prod окружение отсутствие явной пометки может привести к тому, что no-auth admin surface будет воспринята как нормальная baseline-семантика, а не как локальное исключение.
- Evidence / references:
  - no-auth scope: [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:7)
  - mutating endpoint: [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:306)
  - runtime deployment/env canon: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1), [`docs/run/dev.md`](docs/run/dev.md:1)
- Proposed fix:
  - [ ] Зафиксировать в плане, что no-auth admin surface допустима только для локального single-user PoC.
  - [ ] При первом выходе за пределы локального PoC вернуть вопрос в Stage 2 и заморозить auth/RBAC/deployment boundary.
- Traceability:
  - Plans to update: [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:3)
  - Tasks to update / create: [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1), будущий Stage 3 task в [`tasks_descriptions/tasks/`](tasks_descriptions/tasks:1) для hardening admin surface при выходе из PoC

## Non-findings (what is explicitly fine)

- Разделение monitoring truth и routing truth само по себе логично и хорошо согласуется с monitoring-only позицией usage adapter в [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:118).
- Идея вынести provider-specific трактовку quota semantics из общего strategy layer в отдельный handler согласуется с границей provider-specific behavior, описанной в [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:113) и текущим provider-specific runtime boundary в [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:76).
- Запрет на прямое чтение state-файлов фронтендом — правильное решение; backend read-model boundary в [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:353) нужен и не выглядит спорным.

## Open questions raised by Critic

- Должно ли состояние long window когда-либо самостоятельно переводить систему в публичный [`all_accounts_exceed_quota`](docs/contracts/api/openai/errors/429-error.schema.json:65), или weekly saturation остаётся только internal/admin signal до runtime-confirmed failure? → эскалация в Stage 2
- Что именно означает operator action [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147): запись в config, временный in-memory override, override только для `single` или pin внутри конкретной group? → эскалация в Stage 2
- Является ли новый admin read-model самостоятельным contract-first API артефактом, который должен жить рядом с [`docs/contracts/`](docs/contracts:1), или это локальный backend-only DTO без статуса публичного контракта? → эскалация в Stage 2

## Return to Stage 2 triggers

- Нужно заморозить новый state boundary между [`limits.json`](llm_agent_platform/services/runtime_state_paths.py:37) и proposed [`usage_windows.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:173) / [`request_usage.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:174).
- Нужно заморозить внешний OpenAI-compatible `429` mapping до начала implementation tasks, иначе появится скрытый contract drift относительно [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1).
- Нужно заморозить semantics и ownership для admin action [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147), потому что это уже меняет routing/contracts, а не только UI.

## Suggested changes to Stage 3 artifacts (optional)

- После возврата из Stage 2 обновить [`docs/testing/test-map.md`](docs/testing/test-map.md:1) и добавить трассировку для monitoring/admin read-model и нового quota lifecycle.
- При будущей декомпозиции связать новые задачи с исходным критическим отчётом и source task [`tasks_descriptions/tasks/039-two-level-openai-chatgpt.md`](tasks_descriptions/tasks/039-two-level-openai-chatgpt.md:1).
