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

## Initial status

- Current State: planned.
- Next Step: run smoke verification after frontend editor tasks are complete.
- Blockers: none.
