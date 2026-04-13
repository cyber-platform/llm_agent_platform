# Plan 059: provider-specific model capabilities и key-scoped request overrides

## Status

- Stage: canonized to `docs/`
- Role now: navigation artifact only

## Canonical Source of Truth

- architecture canon: [`docs/architecture/provider-request-policy-overrides.md`](../../docs/architecture/provider-request-policy-overrides.md:1)
- pipeline canon: [`docs/architecture/openai-chat-completions-pipeline.md`](../../docs/architecture/openai-chat-completions-pipeline.md:1)
- provider-specific canon: [`docs/providers/openai-chatgpt.md`](../../docs/providers/openai-chatgpt.md:1)
- contracts index: [`docs/contracts/index.md`](../../docs/contracts/index.md:1)

## Supporting canonized contracts

- capability registry schema: [`docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json`](../../docs/contracts/config/openai-chatgpt-model-capabilities-registry.schema.json:1)
- request policy registry schema: [`docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json`](../../docs/contracts/config/openai-chatgpt-request-policy-registry.schema.json:1)
- capability read schema: [`docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json`](../../docs/contracts/api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json:1)
- request policy schemas: [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json:1), [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json:1), [`docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json`](../../docs/contracts/api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json:1)

## Follow-up decomposition point

Implementation tasks должны ссылаться на `docs/` как на SoT и не пересказывать заново архитектурные решения из этого artifact.
