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
