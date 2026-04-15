# Release Notes: `2026-04-15-openai-chatgpt-policy-editor-release`

## Version

- Release version: `v0.0.3`

## Scope

Этот релиз завершает admin-facing rollout key-scoped request policy overrides для `openai-chatgpt`.

В release входят:

- provider-scoped capability overlay и request policy registry;
- admin routes для model capabilities и key-scoped policies;
- pipeline policy application с `pass-through by default` и policy-driven overwrite semantics;
- adapter-side `reasoning_effort` integration;
- local-only admin Web UI policy editor с constraints rendering и raw capability drawer.

## Changed release units

- root project
- `services/backend`
- `services/frontend`

## Not part of this release

- `services/user_service`

## Canonical references

- [`provider-request-policy-overrides.md`](../architecture/provider-request-policy-overrides.md)
- [`openai-chatgpt.md`](../providers/openai-chatgpt.md)
- [`web-ui.md`](../architecture/web-ui.md)
- [`test-map.md`](../testing/test-map.md)
