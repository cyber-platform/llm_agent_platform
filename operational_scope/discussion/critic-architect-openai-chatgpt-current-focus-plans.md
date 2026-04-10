# Critic report: Architect output

## Metadata
- Date: 2026-04-10
- Target artifact(s): `operational_scope/plans/current_focus/openai-chatgpt-monitoring-frontend-prototype.md`, `operational_scope/plans/current_focus/openai-chatgpt-two-level-usage-windows-analysis.md`
- Critic profile: role=Critic

## Executive Summary
- Verdict: `ok-with-gaps`
- Main concern: планы в целом опираются на канонический SoT, но между ними оставлены implicit зависимости и незафиксированные boundary decisions, из-за которых реализация может разъехаться по naming, lifecycle и execution order.
- Recommended next step: `architect refinement`

## Problem Frame Reconstruction
- Goal: довести `openai-chatgpt` до account-centric monitoring semantics с двумя usage windows и поверх этого поднять pilot admin monitoring UI через backend read-model.
- Constraints: `docs/` уже зафиксировали in-memory-first read path, account-centric state layout, minimal public `429` contract, provider-specific page/drawer и no-auth boundary только для local single-user PoC.
- Intended architectural move: сначала нормализовать monitoring/runtime semantics и persistence boundary для `openai-chatgpt`, затем вывести provider-specific admin UI, не нарушая provider-centric и contract-first канон.

## Findings

### Finding F-001: Зависимость UI-пилота от rollout двухуровневых окон оставлена неявной
- Severity: `high`
- Type: `missing-decision`
- Problem: UI-план описан как самостоятельная implementation sequence, но его backend page contract требует `short_window`, `long_window`, `refresh`, `routing` и action semantics, которые появляются только после реализации account-centric usage windows и provider-specific quota handling. План не фиксирует, какие slices второго плана являются prerequisite, и не описывает допустимый degraded mode, если UI делается раньше.
- Impact: команда может либо строить page contract на заглушках, либо читать persisted files напрямую, либо тащить в UI неготовую семантику из runtime. Во всех трёх случаях появляется drift относительно SoT и повышается риск двойной переделки backend read-model.
- Evidence / references: `operational_scope/plans/current_focus/openai-chatgpt-monitoring-frontend-prototype.md:29`, `operational_scope/plans/current_focus/openai-chatgpt-monitoring-frontend-prototype.md:31`, `operational_scope/plans/current_focus/openai-chatgpt-two-level-usage-windows-analysis.md:22`, `operational_scope/plans/current_focus/openai-chatgpt-two-level-usage-windows-analysis.md:24`, `docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:143`, `docs/providers/openai-chatgpt.md:138`
- Recommended next action: `architect refinement` — явно зафиксировать dependency graph между планами и указать, может ли UI идти только после slices 1-5 второго плана или допустим временный reduced payload с отдельным contract decision.

### Finding F-002: Нормализация `block_account_until` не доведена до явного contract mapping
- Severity: `high`
- Type: `contract-gap`
- Problem: второй план делает центральным шагом перевод `usage_limit_reached` в `block_account_until` semantics, но в persisted routing truth и admin read-model используются другие имена: `quota_blocked_until`, `quota_block_reason`, `block_reason`. План не фиксирует, где именно проходит boundary между normalized handler output и canonical persisted/admin fields.
- Impact: реализация может породить три близких, но неэквивалентных vocabulary слоя: handler output, `account_state.json` и admin page payload. Это создаёт риск semantic drift, дублирования полей и расхождения между routing truth и operator-facing read-model.
- Evidence / references: `operational_scope/plans/current_focus/openai-chatgpt-two-level-usage-windows-analysis.md:25`, `docs/providers/openai-chatgpt.md:157`, `docs/architecture/quota-group-state-snapshot-and-state-dir.md:111`, `docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:79`
- Recommended next action: `contract refinement` — зафиксировать явное mapping rule: какие поля возвращает handler, какие поля пишет router в `account_state.json`, и как admin read-model их проецирует наружу.

### Finding F-003: `Activate` остаётся семантически неполным на уровне implementation plan
- Severity: `medium`
- Type: `boundary-gap`
- Problem: UI-план правильно повторяет, что `Activate` — session-scoped in-memory action без config mutation, но не фиксирует, где живёт сама session boundary в no-auth local single-user PoC, как она переживает page refresh, как отражается в read-model и где проходит граница между process-local state и browser session.
- Impact: разработка легко уедет либо в process-global override, либо в скрытую persisted mutation, либо в псевдо-session semantics, которая на самом деле неотличима от глобального флага. Это опасно именно потому, что `Activate` уже канонизирован как узкий и временный semantic carve-out.
- Evidence / references: `operational_scope/plans/current_focus/openai-chatgpt-monitoring-frontend-prototype.md:25`, `operational_scope/plans/current_focus/openai-chatgpt-monitoring-frontend-prototype.md:34`, `docs/providers/openai-chatgpt.md:214`, `docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:157`
- Recommended next action: `architect refinement` — явно описать storage/lifecycle для preferred-account override и связать это с backend mutation endpoint и read-model field `is_preferred_for_session`.

### Finding F-004: Restart/hydrate semantics для provider monitoring artifacts выпали из второго плана
- Severity: `medium`
- Type: `missing-decision`
- Problem: план покрывает path resolution, ownership split и async persistence, но не называет отдельным deliverable восстановление `usage_windows.json` и `request_usage.json` в in-memory snapshots после рестарта. Между тем SoT явно говорит, что persisted artifacts существуют для restore after restart, а admin read-model работает поверх in-memory state.
- Impact: можно получить реализацию, в которой persistence формально есть, но после рестарта UI показывает пустые monitoring windows до первого внешнего refresh, а routing/admin side живут в разных временных состояниях. Это не обязательно противоречит SoT напрямую, но оставляет важный lifecycle behavior implicit.
- Evidence / references: `operational_scope/plans/current_focus/openai-chatgpt-two-level-usage-windows-analysis.md:22`, `operational_scope/plans/current_focus/openai-chatgpt-two-level-usage-windows-analysis.md:26`, `docs/architecture/quota-group-state-snapshot-and-state-dir.md:241`, `docs/architecture/quota-group-state-snapshot-and-state-dir.md:245`, `docs/providers/openai-chatgpt.md:134`
- Recommended next action: `architect refinement` — добавить явное решение: monitoring snapshots hydrate-ятся из persisted files, либо после рестарта считаются intentionally empty до refresh; затем закрепить это тестом на restart lifecycle.

### Finding F-005: Dynamic provider list в пилоте имеет незафиксированную границу применимости
- Severity: `low`
- Type: `hidden-assumption`
- Problem: UI-план требует dynamic provider list, но одновременно ограничивает pilot scope одним provider page. Не зафиксировано, должен ли shell показывать только providers с готовым page contract, или любой зарегистрированный provider, даже если для него нет provider-specific page.
- Impact: пока в UI один provider, проблема скрыта. Но как только в runtime появится второй provider без страницы, динамическая навигация может начать вести в dead end, а команда будет вынуждена ad hoc решать, где проходит boundary между discoverability и implemented capability.
- Evidence / references: `operational_scope/plans/current_focus/openai-chatgpt-monitoring-frontend-prototype.md:21`, `operational_scope/plans/current_focus/openai-chatgpt-monitoring-frontend-prototype.md:30`, `docs/architecture/admin-monitoring-read-model.md:25`, `docs/architecture/admin-monitoring-read-model.md:44`
- Recommended next action: `architect refinement` — зафиксировать, фильтрует ли providers list только реализованные monitoring pages или UI должен уметь показывать disabled/placeholder state.

## Non-findings
- Оба плана корректно позиционируют себя как implementation layer поверх уже принятого SoT в `docs/` и не пытаются переписать архитектуру внутри operational artifacts.
- Разделение monitoring truth (`usage_windows.json`), request observability (`request_usage.json`) и routing truth (`account_state.json`) не выглядит случайным или противоречивым; оно согласовано с `docs/providers/openai-chatgpt.md` и `docs/architecture/quota-group-state-snapshot-and-state-dir.md`.
- UI-план не пытается протащить persisted files в live frontend path и в этом месте остаётся согласованным с admin read-model canon.
- Оба плана сознательно не расширяют public `429` contract и не смешивают internal/admin taxonomy с внешним OpenAI-compatible error envelope.
- Вынос auth/RBAC hardening в отдельный future stage выглядит осознанным и сам по себе не является semantic defect, пока сохраняется local single-user PoC boundary.

## Open Questions
- Какие именно slices второго плана считаются hard prerequisite для начала backend admin read-model endpoints из первого плана?
- Где живёт session boundary для `Activate` в no-auth PoC: Flask session/cookie, process-local operator context или другой механизм?
- Что должно происходить с `usage_windows` и `request_usage` сразу после рестарта процесса до первого refresh: hydrate из диска или intentional empty state?
- Должен ли dynamic provider list отражать только providers с реализованным page contract или весь runtime registry?

## Freeze Readiness
- Safe to freeze now: `partially`
- What blocks freeze: execution order между двумя планами, явное mapping-решение для normalized quota block semantics и lifecycle-решение для `Activate`/restart hydration ещё не зафиксированы достаточно явно.

## Recommended Next Step
- `architect refinement`
- Notes: достаточно короткого refinement pass, который добавит dependency graph между планами, зафиксирует mapping handler -> `account_state` -> admin read-model и снимет ambiguity по `Activate` session boundary и restart behavior. После этого планы будут выглядеть существенно безопаснее для реализации.
