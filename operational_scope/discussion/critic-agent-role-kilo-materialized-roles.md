# Critic report: Kilo materialized agent roles

## Metadata
- Date: 2026-04-10
- Target artifact(s): `.kilo/agents/architect.md`, `.kilo/agents/critic.md`, `.kilo/agents/deep-researcher.md`
- Supporting context: `sot_layers/hyper-graph/docs/terms/terms_map.md`, `sot_layers/hyper-graph/docs/terms/project/terms/agent-role.md`, `sot_layers/hyper-graph/docs/terms/project/terms/role-pack.md`, `sot_layers/hyper-graph/docs/terms/project/terms/step-vacancy.md`, `sot_layers/hyper-graph/docs/terms/project/terms/workflow-step.md`, `sot_layers/hyper-graph/docs/methodology-layer/overview.md`, `sot_layers/hyper-graph/docs/methodology-layer/workflow-and-roles.md`, `sot_layers/hyper-graph/docs/methodology-layer/agent-system-assets-and-materialization-boundaries.md`, `sot_layers/hyper-graph/docs/methodology-layer/layered-sot-and-materialization-model.md`, `sot_layers/hyper-graph/assets/skills/skills-critic/critic-agent-role-semantic-critique/SKILL.md`
- Critic profile: role=Critic

## Executive Summary
- Verdict: `usable-with-minor-gaps`
- Main concern: набор ролей уже выглядит как осмысленные materialized Kilo artifacts, но capability projection contract для систем без native role-local rules/skills/tools пока остается implicit, а граница `Architect self-check` vs `Critic independent critique` все еще недостаточно жестко зафиксирована.
- Recommended next step: `docs refinement`

## Problem Frame Reconstruction
- Goal: апробировать модель `agent-role` через target system Kilo, начиная не с abstract canonical role packs, а с уже materialized Kilo-facing role artifacts в `.kilo/agents/`.
- Constraints: Kilo и некоторые другие agent systems не поддерживают native role-specific `rules`, `skills` и `MCP tools`; therefore capability scoping должно materialize через prompt-visible inventory и brokered access path.
- Intended architectural move: HyperGraph хранит reusable role semantics отдельно от Kilo projection, а materialized role получает role-specific capabilities через `hyper-graph-mcp`, который выступает capability broker и proxy access layer.

## Findings

### Finding F-001: Capability projection contract через `hyper-graph-mcp` пока не зафиксирован как канонический слой
- Severity: `high`
- Type: `missing-decision`
- Problem: в каноне уже есть distinction между reusable source assets, project-owned context-entry artifacts и Kilo materialization targets, а также distinction между core `agent-role` и `agent-system`-specific projection. Но special case для систем без native role-local capabilities пока не описан явно: role-specific `rules`, `skills` и `MCP tools` фактически materialize как prompt-advertised inventory плюс access path через `hyper-graph-mcp.get_skill(...)` и `hyper-graph-mcp.use_tool(...)`.
- Impact: без явной фиксации система остается понятной только из устных пояснений. Это создает риск, что разные authors будут по-разному трактовать, где проходит граница между reusable capability semantics, materialized visible inventory и runtime invocation contract. В результате role packs, Kilo projections и future adapters могут разъехаться по смыслу.
- Evidence / references: `sot_layers/hyper-graph/docs/methodology-layer/workflow-and-roles.md:96`, `sot_layers/hyper-graph/docs/methodology-layer/overview.md:17`, `sot_layers/hyper-graph/docs/methodology-layer/agent-system-assets-and-materialization-boundaries.md:152`, `sot_layers/hyper-graph/docs/methodology-layer/layered-sot-and-materialization-model.md:95`
- Recommended next action: `docs refinement` — явно описать `runtime capability projection` как materialization pattern для agent systems без native role-local support и привязать к нему `hyper-graph-mcp` как capability broker/proxy.

### Finding F-002: `Critic` все еще оставляет слишком широкий люфт в сторону proposal-authoring
- Severity: `medium`
- Type: `boundary-gap`
- Problem: роль уже хорошо центрирована на semantic critique и не выглядит decorative persona, но текущее ограничение “предлагай направления для исправления, но не подменяй собой автора решения” остается недостаточно строгим. Оно не фиксирует stop condition между pinpointed correction guidance и развернутым replacement design.
- Impact: в реальном использовании `Critic` может начать фактически строить альтернативное решение под видом рекомендаций. Тогда cognitive boundary между `Critic` и `Architect` размывается, а role set теряет одну из главных причин существования как разделение cognitive labor.
- Evidence / references: `.kilo/agents/critic.md:60`, `.kilo/agents/critic.md:65`, `.kilo/agents/architect.md:42`, `.kilo/agents/architect.md:44`, `sot_layers/hyper-graph/assets/skills/skills-critic/critic-agent-role-semantic-critique/SKILL.md:79`
- Recommended next action: `role refinement` — добавить явный guardrail, что `Critic` может давать correction vector, boundary correction, pinpointed recommendations и escalation to Architect, но не должен разворачивать полноценный alternative design/proposal.

### Finding F-003: Tool-fit для `Deep Researcher` зависит от внешнего capability substrate, но это не видно из самого materialized role artifact
- Severity: `medium`
- Type: `tool-fit-gap`
- Problem: роль обещает многослойное evidence-based research по нескольким источникам и нескольким search channels, однако сам Kilo materialized artifact не показывает, за счет какого capability substrate это обеспечивается. После ваших пояснений понятно, что intended substrate — `hyper-graph-mcp`, но это знание пока не встроено в канонический bridge между role semantics и Kilo projection.
- Impact: роль выглядит сильнее, чем документированная capability surface. Для текущей команды это может быть терпимо, но для future materialization и adapter work это создает ambiguity: что является semantic promise роли, а что просто наличное поведение конкретного runtime environment.
- Evidence / references: `.kilo/agents/deep-researcher.md:18`, `.kilo/agents/deep-researcher.md:33`, `.kilo/agents/deep-researcher.md:49`, `sot_layers/hyper-graph/docs/methodology-layer/component-architecture.md:74`
- Recommended next action: `docs refinement` — связать research-heavy roles с общим capability projection pattern, а не оставлять это implicit через environment knowledge.

### Finding F-004: Граница между `Architect` и `Critic` как разными cognitive functions пока описана недостаточно явно
- Severity: `medium`
- Type: `role-overlap`
- Problem: текущая семантика `Architect` уже включает critique-like деятельность: explicit unknowns, assumptions, white spots, consistency sweep и safe-freeze checks. Это полезно и само по себе не является дефектом. Но в артефактах не зафиксировано достаточно явно, что для `Architect` это именно author-side self-check, а не независимая adversarial critique. В результате overlap с `Critic` остается слишком широким и может читаться как дублирование двух ролей с разной риторикой.
- Impact: если `Architect` начнет делать полный external-style critique своего же proposal, `Critic` потеряет distinct function и role set начнет collapse-иться в двух гибридных reviewer/architect personas. С другой стороны, если запретить `Architect` любой consistency check, он станет продуцировать raw design без минимальной защиты от собственных противоречий. Значит проблема не в overlap как таковом, а в незафиксированной границе допустимого overlap.
- Evidence / references: `.kilo/agents/architect.md:35`, `.kilo/agents/architect.md:45`, `.kilo/agents/architect.md:53`, `.kilo/agents/critic.md:16`, `.kilo/agents/critic.md:23`, `.kilo/agents/critic.md:33`, `sot_layers/hyper-graph/docs/methodology-layer/principles.md:233`
- Recommended next action: `role refinement` — явно закрепить, что `Architect` делает только self-consistency/self-freeze pass по собственному решению, а `Critic` выполняет отдельную независимую semantic verification после candidate/freeze-ready артефакта.

## Non-findings
- `.kilo/agents/*.md` не являются semantic error сами по себе: канон уже различает core role semantics и Kilo-facing materialization, поэтому трактовка этих файлов как materialized roles согласована с `sot_layers/hyper-graph/docs/methodology-layer/agent-system-assets-and-materialization-boundaries.md:221`.
- Подход “начать апробацию с Kilo как текущей primary target system” выглядит архитектурно разумным и не противоречит layered SoT модели, пока materialized artifacts не объявляются semantic owner layer.
- `Architect` как интерактивный human-in-the-loop ассистент теперь выглядит согласованным с intended role semantics; требование согласования перед deep research/spike не выглядит случайной workflow leakage, если это часть role profile.
- Частичный overlap между `Architect` и `Critic` сам по себе не является defect: авторский self-check у `Architect` нужен, чтобы не фиксировать очевидно противоречивое решение до внешней критики.
- Все три роли являются functional personas, а не декоративными character prompts: они реально steer-ят attention, reasoning priorities и negative focus.
- Разделение между `agent-role`, `step-vacancy` и `workflow-step` в самих role prompts не нарушено; роли не перепутаны с workflow assignment layer.

## Open Questions
- В каком именно каноническом документе должен жить pattern `runtime capability projection`: в `sot_layers/hyper-graph/docs/methodology-layer/agent-system-assets-and-materialization-boundaries.md`, в отдельном focused spec или в contracts layer?
- Должен ли `hyper-graph-mcp` описываться как самостоятельный architectural component/capability broker term, или достаточно contract-level описания без выделения нового термина?
- Нужен ли для materialized Kilo roles явный `when_to_use` block прямо в `.kilo/agents/*.md`, если Kilo artifact уже является projection, а не canonical core role?
- Должен ли `Critic` явно эскалировать в `Architect`, когда critique naturally требует полноценного redesign, или достаточно мягкого stop condition без явной handoff semantics?
- Нужно ли явно описать рекомендуемую sequencing model `Architect draft -> Architect self-check -> Critic independent critique -> Architect refinement/freeze`, или это должно оставаться workflow-level decision вне role definitions?

## Freeze Readiness
- Safe to freeze now: `partially`
- What blocks freeze: role set уже пригоден для пилотной materialization под Kilo, но capability-projection bridge через `hyper-graph-mcp` еще не зафиксирован как канонический механизм, а boundary `Architect self-check` vs `Critic independent critique` еще можно безопасно усилить до более четкого stop condition и handoff semantics.

## Recommended Next Step
- `docs refinement`
- Notes: сначала зафиксировать canonical pattern для capability projection в systems без native role-local support, затем развести `Architect` и `Critic` по схеме `author-side self-check` vs `independent critique`, не убирая у `Architect` минимальную consistency responsibility. После этого role set будет выглядеть не только практически рабочим, но и значительно более устойчивым как reusable methodology baseline.
