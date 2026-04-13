# Contracts Index

## Назначение

Этот индекс является entry point для machine-readable contracts проекта.

Здесь собраны JSON schemas, которые фиксируют API surface, declarative config и persisted state semantics.

## Карта разделов

| Раздел | Назначение |
| --- | --- |
| `api/` | HTTP contracts для public и admin API surfaces. |
| `config/` | Declarative configuration schemas. |
| `state/` | Persisted runtime state и snapshot schemas. |

## Как читать

1. Сначала найти system-level context в [`traceability-map.md`](../architecture/traceability-map.md).
2. Затем открыть нужный schema family в `api/`, `config/` или `state/`.
3. Для verification path перейти в [`index.md`](../testing/index.md).

## Related documents

- architecture traceability: [`traceability-map.md`](../architecture/traceability-map.md)
- provider matrix: [`index.md`](../providers/index.md)
- test map: [`index.md`](../testing/index.md)

## Recent config schemas

- [`config/openai-chatgpt-model-capabilities-registry.schema.json`](./config/openai-chatgpt-model-capabilities-registry.schema.json:1)
- [`config/openai-chatgpt-request-policy-registry.schema.json`](./config/openai-chatgpt-request-policy-registry.schema.json:1)

These schemas support the request-policy-override boundary canonized in [`docs/architecture/provider-request-policy-overrides.md`](../architecture/provider-request-policy-overrides.md:1).

## Recent admin API schemas

- [`api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json`](./api/admin/model-capabilities/openai-chatgpt-model-capabilities-read.schema.json:1)
- [`api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json`](./api/admin/request-policies/openai-chatgpt-request-policy-read.schema.json:1)
- [`api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json`](./api/admin/request-policies/openai-chatgpt-request-policy-upsert-request.schema.json:1)
- [`api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json`](./api/admin/request-policies/openai-chatgpt-request-policy-upsert-response.schema.json:1)

## Related examples

- [`../examples/openai-chatgpt-model-capabilities-registry.example.json`](../examples/openai-chatgpt-model-capabilities-registry.example.json:1)
- [`../examples/openai-chatgpt-request-policy-registry.example.json`](../examples/openai-chatgpt-request-policy-registry.example.json:1)
