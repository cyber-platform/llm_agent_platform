# ADR 0022: admin monitoring live refresh subsystem for PoC-stage operator UI

- Status: Accepted
- Date: 2026-04-12
- Related:
  - [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
  - [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1)
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)

## Контекст

Admin monitoring read-model уже materialized, но provider page может отставать от runtime событий:

- routing truth меняется сразу;
- monitoring usage snapshot может быть stale;
- operator UI нуждается в live refresh without direct filesystem reads.

Для PoC было рассмотрено несколько способов обновления monitoring state.

## Решение

1. Вводится backend-owned live refresh subsystem.
2. Backend запускает provider-wide background poller.
3. UI manual refresh materialize-ится через async trigger + status polling, а не через synchronous long-running request.
4. During manual refresh frontend временно переключается с обычного page polling на short polling refresh status endpoint.
5. Routing truth и monitoring freshness показываются как разные части provider page.

## Alternatives considered

### A. Backend push callback в frontend

- Плюсы: теоретически near-live updates.
- Минусы: frontend не является каноническим callback receiver; усложняется trust boundary и local delivery model.

### B. Только synchronous refresh endpoint

- Плюсы: простой HTTP contract.
- Минусы: button UX становится тяжелым при росте account count; сложнее показывать progress.

### C. SSE/WebSocket push

- Плюсы: near-live UX без polling.
- Минусы: для текущего PoC преждевременно; требуется более сложный event contract и reconnect model.

### D. Только background poller без manual refresh

- Плюсы: меньше operator API.
- Минусы: operator не может потребовать immediate refresh вручную.

## Последствия

### Положительные

- UI получает live-ish behavior без прямого coupling к upstream adapters;
- backend остаётся единственным owner refresh lifecycle;
- manual refresh и background poller используют один architectural subsystem;
- progress banner и итоговый summary становятся архитектурно допустимыми.

### Негативные

- появляется in-memory refresh run registry;
- нужен status endpoint и cleanup lifecycle для completed runs;
- решение пока process-local и PoC-scoped.

## Условия пересмотра

- Если понадобится multi-instance backend deployment.
- Если operator UI потребует true push-driven updates.
- Если job lifecycle должен стать durable across restart.
