# Plan 040: admin surface auth and RBAC hardening for monitoring UI

## Status

- Stage: future planning only
- Priority: post-PoC
- Current implementation target: not in current PoC scope

## Context

Текущий monitoring UI intentionally остаётся лёгким PoC:

- admin surface допускается без авторизации только в локальном single-user сценарии
- интерфейс используется для наблюдения за состоянием аккаунтов и ручного операторского тестирования поведения системы
- mutating operator actions пока ограничены очень узко
- действие выбора аккаунта трактуется как session-scoped in-memory override текущего процесса
- канонические provider config files не переписываются через UI
- после рестарта система возвращается к config baseline

Эта модель полезна для быстрого исследования UX и runtime heuristics, но не должна становиться долгосрочным baseline для shared dev, multi-user или production-like окружений.

Следующий логический этап после завершения PoC — спроектировать auth boundary и role-based access control для admin surface.

## Goal

Подготовить будущий переход от локального no-auth PoC к безопасному admin surface с аутентификацией, разграничением ролей и явными правилами для mutating operator actions.

## Desired future outcome

После этого этапа monitoring UI должен поддерживать минимум две роли:

- `observer` — может только смотреть monitoring state и admin read-model
- `admin` — может смотреть monitoring state и выполнять mutating operator actions

## Why this is needed

Этот future plan нужен, чтобы текущее PoC-допущение не стало случайным постоянным baseline.

Он должен быть активирован, если произойдёт хотя бы одно из событий:

- admin UI используется не одним локальным пользователем
- admin surface переносится в shared dev environment
- появляется необходимость audit trail по operator actions
- появляются новые mutating operator actions
- появляется требование security review
- появляется production-like deployment scenario

## Functional target

### Role `observer`

Разрешено:

- читать provider list
- читать provider page
- читать account state
- читать usage windows
- читать request usage details
- читать routing metadata
- читать health and refresh status

Запрещено:

- вызывать mutating admin commands
- менять preferred account текущего процесса
- менять provider-level runtime behavior
- запускать operator override actions

### Role `admin`

Разрешено:

- всё, что может `observer`
- вызывать mutating operator actions
- менять текущий preferred account процесса
- выполнять другие согласованные operator commands

## Important current constraint

Даже после появления auth and RBAC должны сохраняться следующие invariants:

- admin UI не должен становиться редактором provider config files без отдельного архитектурного решения
- mutating operator actions не должны скрытно переписывать канонический routing baseline
- session-scoped runtime overrides должны оставаться отделёнными от долговременного config state
- public OpenAI-compatible API не должен смешиваться с admin auth boundary

## Scope of future design

### 1. Auth boundary

Нужно будет зафиксировать:

- как пользователь аутентифицируется в admin surface
- какой transport используется для auth
- как отделяется admin UI boundary от OpenAI-compatible public API
- какие deployment modes допускают включённый admin UI
- как различаются local-dev, shared-dev и production-like scenarios

### 2. RBAC boundary

Нужно будет зафиксировать:

- набор ролей
- список capabilities per role
- какие read endpoints доступны каждой роли
- какие mutating commands доступны только `admin`
- как UI скрывает или показывает capabilities по role claims

### 3. Auditability

Для mutating admin actions нужно будет решить:

- нужен ли audit log
- где хранить operator action trail
- нужно ли связывать action с user identity
- какие поля обязательны для traceability
- какие события считаются security-sensitive

### 4. Contract-first admin API

После активации этого future plan нужно будет зафиксировать contracts для:

- admin auth context
- admin role claims
- provider page read-model capabilities per role
- mutating command response envelope
- audit event structure, если аудит войдёт в scope

## Constraints

- Это не цель текущего PoC
- До отдельного архитектурного цикла local single-user no-auth contour остаётся допустимым только как временное PoC-допущение
- Current operator account switching остаётся только session-scoped in-memory action текущего процесса
- public OpenAI-compatible API не должен смешиваться с admin auth boundary
- любые постоянные config mutations через admin UI требуют отдельного Stage 2 решения

## Proposed future deliverables

1. Stage 2 decision по auth boundary
2. Stage 2 decision по RBAC roles and capabilities
3. Contract-first admin auth and command schemas
4. Updated monitoring UI design with role-aware capabilities
5. Test design for `observer` and `admin` permissions
6. Audit design for mutating operator actions, если аудит войдёт в scope

## Initial questions for future Stage 2

- какой auth mechanism наиболее уместен для admin surface
- нужно ли разделять local-dev auth и shared-dev auth
- считать ли `observer` ролью по умолчанию
- должны ли все mutating operator actions быть доступны только `admin`
- как логировать operator actions без перегруза системы
- где проходит граница между session-scoped runtime override и persistent configuration management

## Durable references

- provider config semantics: [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1)
- env and deployment boundary: [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- dev runtime model: [`docs/run/dev.md`](docs/run/dev.md:1)

## Execution note

Этот план не запускает реализацию автоматически.

Он фиксирует будущий архитектурный backlog item, который должен быть поднят отдельным Stage 2 циклом после завершения текущего PoC и синхронизации канонических docs.
