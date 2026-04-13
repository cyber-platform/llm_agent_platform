# Frontend constraints rendering и raw capability drawer для `openai-chatgpt`

## Контекст

Capability admin response уже содержит `parameters`, optional `constraints` и raw capability payload drawer source.

Для удобного admin UX нужно показать ограничения и read-only raw JSON без превращения UI в config editor.

## Goal

Добавить в policy UI отображение capability constraints и collapsible raw capability JSON drawer.

## Scope

В scope:

- rendering `constraints` из capability response;
- read-only collapsible panel для raw capability payload;
- clear messaging around supported reasoning values and known restrictions;
- integration with current policy editor screen.

Не входит в scope:

- editable raw JSON;
- generalized docs browser;
- complex diff/history UX.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json`](../../docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json)
- [`docs/examples/openai-chatgpt-model-capabilities-registry.example.json`](../../docs/examples/openai-chatgpt-model-capabilities-registry.example.json)

## Dependencies

- Зависит от frontend admin API wiring task.
- Желательно реализовывать вместе или сразу после policy editor UI task.

## Implementation notes

1. Constraints должны показываться как hint/guardrail, а не как editable rules engine.
2. Raw JSON drawer должен быть read-only.
3. UI должен особенно явно показать constraints для `gpt-5.4*`, если они приходят в capability response.

## Definition of Done

- Constraints отображаются в policy UI, если они присутствуют в capability response.
- Raw capability JSON доступен через collapsible read-only drawer.
- UI не смешивает display of constraints с policy editing controls.
- Есть verification notes для supported-model capability rendering.

## Implementation summary

- Extended the inline policy editor in `services/frontend/src/App.tsx` with a read-only capability note that surfaces supported reasoning values, default value, and backend-provided description for the selected model.
- Added a dedicated constraints card for the selected capability that renders backend `constraints[]` as guardrails instead of editable policy controls.
- Added a collapsible `details` drawer for `drawer.raw_capability_payload`, keeping the raw registry payload visible as read-only JSON without turning the UI into a config editor.
- Added layout and presentation styles in `services/frontend/src/styles.css` for the capability note, constraints card, and raw payload drawer while preserving the existing admin shell visual language.

## Verification notes

- `npm run build` in `services/frontend` passed after adding capability constraints rendering and the raw payload drawer.
- Supported models now show backend-derived reasoning values, default value, and description directly inside the policy editor context.
- Models with backend `constraints` render them as read-only guardrails, separate from editable `reasoning_effort` controls.
- Models with `drawer.raw_capability_payload` expose the raw JSON through a collapsible panel instead of inline editable fields.

## Handoff context for next agent

- Files changed for this task:
  - `services/frontend/src/App.tsx`
  - `services/frontend/src/styles.css`
  - `operational_scope/tasks/070-frontend-openai-chatgpt-capability-constraints-and-raw-drawer.md`
  - `operational_scope/tasks_map.md`
- The policy editor still scopes editable controls to `reasoning_effort`, but now also surfaces backend capability metadata for the currently selected supported model.
- Constraint rendering is intentionally read-only and currently formats `forbid_parameters_when` rules into operator-facing guardrail text plus compact pill metadata.
- Raw capability payload rendering only appears when `drawer.raw_capability_payload` is present in the admin response and uses the existing `JsonCard` renderer for formatting.
- Unsupported capability cards remain separate from the selected-model constraint area so the UI does not blur unsupported state with editable controls.
- Follow-up verification task `071` can exercise selected-model switching, constraint visibility for `gpt-5.4*`, and raw drawer behavior against live backend payloads.

## Initial status

- Current State: completed.
- Next Step: task `071` can verify end-to-end capability rendering and tighten UX details if backend payloads reveal edge cases.
- Blockers: none.
