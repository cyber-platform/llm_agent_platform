# Verification и UX stabilization для `openai-chatgpt` policy editor

## Контекст

После materialization frontend wiring и UI editor нужно закрепить user-visible behavior через verification notes и targeted smoke checks.

## Goal

Проверить и стабилизировать admin-facing UX для `openai-chatgpt` reasoning policy editor.

## Scope

В scope:

- smoke verification для no-policy/pass-through state;
- save contour для `force`;
- save contour для `default_if_absent`;
- reset contour back to pass-through;
- constraints/raw drawer visibility checks;
- basic frontend build verification.

Не входит в scope:

- e2e automation framework redesign;
- non-`openai-chatgpt` providers;
- future parameter families.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/contracts/index.md`](../../docs/contracts/index.md)
- [`services/frontend/README.md`](../../services/frontend/README.md)

## Dependencies

- Зависит от frontend tasks `068`-`070`.

## Implementation notes

1. Verification должен покрывать explicit no-policy state, а не только happy-path save.
2. Нужно проверить, что UI работает только для supported current models.
3. Build verification обязателен после UI changes.

## Definition of Done

- Зафиксированы verification notes для no-policy, `force`, `default_if_absent`, reset и constraints drawer contours.
- Frontend build проходит.
- Если понадобились test/docs updates, они materialized и ссылаются на canonical SoT.

## Implementation summary

- Stabilized the policy editor in `services/frontend/src/App.tsx` with explicit policy mode helper text so operators can distinguish `force` from `default_if_absent` without referring back to backend docs.
- Added draft-vs-applied detection in `services/frontend/src/App.tsx` so the save action is disabled when the selected override is already persisted, reducing accidental duplicate writes during manual smoke verification.
- Added `field-help-text` styling in `services/frontend/src/styles.css` to keep the verification-oriented helper copy consistent with the existing admin shell typography.
- Consolidated smoke-verification outcomes into this task artifact so the no-policy, save, reset, constraints, raw drawer, and build contours are all recorded in one place.

## Verification notes

- `npm run build` in `services/frontend` passed after the verification stabilization changes.
- No-policy contour: when backend returns empty `model_overrides`, the card still renders explicit pass-through state and keeps reset disabled.
- `force` save contour: selecting a supported model and value keeps the save action available until the override is persisted, then the button switches to disabled `Override saved` state.
- `default_if_absent` save contour: mode helper text now clarifies that the platform only fills requests missing `reasoning_effort`, which reduces ambiguity during operator review.
- Reset contour: reset remains enabled only when a persisted override exists and returns the card to pass-through after delete succeeds.
- Constraints/raw drawer contour: selected supported models continue to render read-only constraints and raw payload drawer only when backend capability payloads expose those fields.

## Handoff context for next agent

- Files changed for this task:
  - `services/frontend/src/App.tsx`
  - `services/frontend/src/styles.css`
  - `operational_scope/tasks/071-frontend-openai-chatgpt-policy-editor-verification.md`
  - `operational_scope/tasks_map.md`
- Verification for this task is smoke-level and build-based; there is still no browser automation suite for the policy editor.
- The save button now reflects persisted state by comparing the current draft against backend-loaded `model_overrides` for the selected model.
- Policy mode copy is intentionally short and operator-facing so the editor can stand alone without requiring direct reading of `docs/providers/openai-chatgpt.md` during routine admin use.
- Constraint and raw drawer behavior still depends entirely on backend capability payload shape; frontend does not invent fallback constraints or synthetic raw content.

## Initial status

- Current State: completed.
- Next Step: the policy editor feature set is verified at smoke/build level; future work can add automated browser coverage if this surface becomes regression-prone.
- Blockers: none.
