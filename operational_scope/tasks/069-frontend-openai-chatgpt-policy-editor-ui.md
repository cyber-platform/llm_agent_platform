# Frontend policy editor UI для `openai-chatgpt` reasoning overrides

## Контекст

Policy feature уже materialized на backend, но администратор пока не может управлять ей из Web UI.

Нужен focused admin UI editor для key-scoped reasoning override, который работает в рамках current key/group context.

## Goal

Добавить в admin Web UI редактор key-scoped policy для `reasoning_effort` у поддерживаемых моделей `openai-chatgpt`.

## Scope

В scope:

- использование current key/group context без отдельного global model picker;
- отображение current policy state для key;
- выбор supported model из current key/group context;
- выбор `reasoning_effort` из allowed values;
- выбор policy mode: `force` / `default_if_absent`;
- explicit no-policy/pass-through state;
- save/reset actions.

Не входит в scope:

- поддержка `verbosity`;
- multi-provider UI generalization;
- redesign всего admin shell.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`services/frontend/src/App.tsx`](../../services/frontend/src/App.tsx)
- [`services/frontend/src/api.ts`](../../services/frontend/src/api.ts)

## Dependencies

- Зависит от frontend admin API wiring task.

## Implementation notes

1. UI editor должен работать только для моделей, реально доступных в current key/group context.
2. Для initial MVP editable scope ограничен `reasoning_effort`.
3. Если policy отсутствует, UI должен явно показывать pass-through state, а не скрытый default.
4. Для неподдерживаемых моделей UI должен показывать read-only unsupported/platform-not-configured state.

## Definition of Done

- Администратор может из Web UI прочитать и изменить `reasoning_effort` policy для key.
- UI поддерживает `force`, `default_if_absent` и reset to pass-through.
- UI не предлагает unsupported models или unsupported values.
- Есть verification notes для no-policy, save и reset contours.

## Implementation summary

- Added per-key policy editor cards in `services/frontend/src/App.tsx`, reachable from the API keys panel without introducing a separate global model picker.
- The editor loads current key policy plus capability records for the initial `reasoning_effort` model scope and shows explicit pass-through, save, and reset states.
- Save flow materializes `force` and `default_if_absent` overrides through the existing authenticated admin API client; reset flow deletes the policy and returns the key to pass-through.
- Unsupported capability records are rendered as read-only cards so the UI does not offer invalid values while still exposing platform-not-configured state.
- Added policy-editor layout and feedback styles in `services/frontend/src/styles.css` to keep the new controls inside the current admin shell visual language.

## Verification notes

- `npm run build` in `services/frontend` passed after the policy editor UI was added.
- No-policy contour renders explicit pass-through state until the operator saves an override.
- Save contour persists a single-model `reasoning_effort` override with either `force` or `default_if_absent` mode.
- Reset contour calls `DELETE /admin/request-policies/openai-chatgpt/keys/<key_id>` and returns the card to pass-through state.

## Handoff context for next agent

- Files changed for this task:
  - `services/frontend/src/App.tsx`
  - `services/frontend/src/styles.css`
  - `services/frontend/README.md`
  - `operational_scope/tasks/069-frontend-openai-chatgpt-policy-editor-ui.md`
  - `operational_scope/tasks_map.md`
- API keys panel now includes an `Edit policy` action per active key and expands an inline editor instead of navigating to a separate page.
- The editor fetches one key policy record plus capability records for the initial reasoning model scope: `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex`.
- Editable options are derived only from backend capability payloads (`parameters.reasoning_effort.values` and `default`); the UI does not invent allowed values locally.
- If `model_overrides` is empty, the card shows explicit pass-through/no-policy state via `isOpenAIChatGPTPolicyPassThrough(...)`.
- Save path uses `upsertRequestPolicy(...)` with a single-model override payload in the current key/group context.
- Reset path uses `deleteRequestPolicy(...)` and then rehydrates the local draft from the returned empty policy record.
- Unsupported capability records are shown as read-only informational cards so the next task can extend them with constraints and raw capability drawer content.
- Current implementation intentionally keeps model discovery limited to the initial backend-supported reasoning scope and does not yet derive group-visible models dynamically from monitoring payloads or key metadata.

## Final status

- Current State: completed.
- Next Step: task `070` can extend the same editor area with constraints rendering and raw capability drawer details.
- Blockers: none.
