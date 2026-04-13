# Plan 062: admin endpoints и path semantics для `openai-chatgpt` capabilities и request policies

## Status

- Stage: canonized to `docs/`
- Role now: navigation artifact only

## Canonical Source of Truth

- architecture canon: [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md:1)
- provider page: [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md:1)
- capability read schema: [`docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json`](../../docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json:1)
- request policy schemas: [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json:1), [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json:1), [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json:1)

## Note

Executable tasks для admin routes должны ссылаться на SoT artifacts выше и не использовать этот plan как primary endpoint specification.
