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

## Initial status

- Current State: planned.
- Next Step: materialize constraints and drawer view in admin shell.
- Blockers: none.
