# ADR 0024: PoC operator frontend delivery boundary as separate local-only service

- Status: Accepted
- Date: 2026-04-12
- Related:
  - [`docs/architecture/web-ui.md`](docs/architecture/web-ui.md:1)
  - [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)

## Контекст

Для PoC требуется operator-facing frontend поверх backend admin API, но без public exposure admin surface и без смешивания frontend runtime с backend runtime.

## Решение

1. PoC frontend materialize-ится как отдельный local-only service/container.
2. Frontend читает только backend admin API.
3. Same-origin delivery обеспечивается через frontend-owned reverse proxy.
4. Frontend runtime settings и backend service settings хранятся отдельно.
5. `.env` остаётся secrets/env layer, а service behavior config живёт в отдельных config files.

## Alternatives considered

### A. Встроить frontend прямо в backend runtime

- Плюсы: меньше deployment artifacts.
- Минусы: смешиваются trust boundary и delivery lifecycle.

### B. Publicly expose frontend вместе с admin API

- Плюсы: проще initial access.
- Минусы: нарушает PoC security boundary и future hardening path.

### C. CORS-first browser access к backend

- Плюсы: меньше proxy config.
- Минусы: weaker local delivery ergonomics; same-origin proxy лучше fit-ится для PoC.

## Последствия

### Положительные

- frontend остаётся human-facing layer only;
- admin API не нужно публиковать наружу;
- runtime config frontend можно менять отдельно от backend service config и secrets.

### Негативные

- появляется отдельный frontend image/service;
- current repo topology включает отдельный nested frontend repo, что является PoC delivery choice, а не final platform invariant.

## Условия пересмотра

- Если operator UI будет объединён с future full Web UI container.
- Если появится auth/RBAC и shared dev deployment для admin surface.
