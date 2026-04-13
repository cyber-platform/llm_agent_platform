# Frontend admin API wiring для `openai-chatgpt` capabilities и request policies

## Контекст

Backend уже materialized capability and policy admin APIs для `openai-chatgpt`, но frontend пока не использует эти endpoints.

Для доведения feature до admin-facing состояния нужен frontend data layer, который сможет читать capabilities и policy state и вызывать save/reset actions.

## Goal

Подключить frontend admin API client к capability и request policy endpoints `openai-chatgpt`.

## Scope

В scope:

- client functions для `GET /admin/model-capabilities/openai-chatgpt/models/<model_id>`;
- client functions для `GET|PUT|DELETE /admin/request-policies/openai-chatgpt/keys/<key_id>`;
- typed frontend payload mapping для capability records, constraints и policy records;
- integration с existing frontend auth/bearer path.

Не входит в scope:

- визуальный policy editor;
- raw JSON drawer rendering;
- end-user UX polish beyond data plumbing.

## Canonical references

- [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md)
- [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md)
- [`docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json`](../../docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json)
- [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json)

## Dependencies

- Опирается на backend tasks `063`-`067`.
- Является dependency для UI editor tasks.

## Implementation notes

1. Frontend не должен invent-ить allowed values или constraints locally.
2. `GET policy` с empty `model_overrides` должен явно трактоваться как pass-through/no-policy state.
3. Initial supported model set для reasoning editor: `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.3-codex`.

## Definition of Done

- Frontend умеет читать capability record и key policy через admin API.
- Frontend умеет сохранять и удалять key policy через admin API.
- Typed mapping покрывает `parameters`, `constraints`, `model_overrides` и no-policy state.
- Есть verification notes для successful reads/writes и auth-bound request path.

## Implementation summary

- Added typed frontend payloads for capability records, optional capability constraints, request policy records, and request-policy upsert payloads in `services/frontend/src/types.ts`.
- Added authenticated admin API client functions for capability read and request policy read/upsert/delete in `services/frontend/src/api.ts`.
- Reused existing bearer-token request path via `requestJson(..., { token })`, so the new endpoints stay inside the same protected admin boundary as monitoring and API-key flows.
- Updated `services/frontend/README.md` endpoint inventory to include the new admin policy/capability routes.

## Handoff context for next agent

- Files changed for this task:
  - `services/frontend/src/types.ts`
  - `services/frontend/src/api.ts`
  - `services/frontend/README.md`
  - `operational_scope/tasks/068-frontend-admin-api-wiring-for-openai-chatgpt-policies.md`
  - `operational_scope/tasks_map.md`
- New capability typing covers current admin response shape: `provider_id`, `model_id`, `display_name`, `parameters`, optional `constraints`, and optional `drawer.raw_capability_payload`.
- New policy typing covers read/upsert/delete response shape with explicit no-policy state represented as `model_overrides: {}`.
- Added helper `isOpenAIChatGPTPolicyPassThrough(...)` so the next UI task can detect pass-through state without inventing fake defaults.
- API client functions added in `services/frontend/src/api.ts`:
  - `getModelCapabilities(modelId, config, token)`
  - `getRequestPolicy(keyId, config, token)`
  - `upsertRequestPolicy(keyId, payload, config, token)`
  - `deleteRequestPolicy(keyId, config, token)`
- All new requests reuse the existing protected admin path and `Authorization: Bearer <token>` behavior from the shared `requestJson` helper; no separate auth wiring was introduced.
- The frontend still does not consume these endpoints in `services/frontend/src/App.tsx`; this task only materialized the reusable typed client/data layer for task `069`.
- Capability `constraints` are typed as optional because current backend admin contract for task `065` does not yet guarantee them in the response; task `070` can use the field when backend payloads expose it.
- The intended initial editor scope remains `reasoning_effort` for `gpt-5.4`, `gpt-5.4-mini`, and `gpt-5.3-codex`, but this task did not hardcode those models into the API layer.

## Verification notes

- `npm run build` in `services/frontend` passed after the new types and API client functions were added.
- New request-policy client maps empty `model_overrides` to the existing explicit no-policy/pass-through state instead of inventing frontend defaults.
- Capability typing keeps `constraints` optional so the current contract remains compatible while task `070` can render them when backend payloads start exposing that field.

## Final status

- Current State: completed.
- Next Step: task `069` can consume the new client and types for the policy editor UI.
- Blockers: none.
