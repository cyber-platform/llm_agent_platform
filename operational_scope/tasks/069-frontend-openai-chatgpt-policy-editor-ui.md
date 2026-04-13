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

## Initial status

- Current State: planned.
- Next Step: materialize policy editor in current admin shell.
- Blockers: none.
