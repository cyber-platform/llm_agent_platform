# Discussion F-005: no-auth admin surface boundary for `openai-chatgpt` monitoring PoC

## Context

Этот документ разбирает замечание `F-005` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:89).

Critic справедливо отмечает, что в [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:7) пилотный UI объявлен как `без авторизации`, а после решения [`F-004`](plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md:1) в пилоте остаётся mutating action [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147), пусть и только как in-memory override.

Это не обязательно ошибка для локального PoC, но такая граница должна быть зафиксирована как **временное, локально-ограниченное допущение**, а не как нормальный baseline для dev/shared/prod.

## Discovery scope

В этом finding решаем только вопрос:

- где проходит допустимая граница no-auth admin surface для текущего PoC
- в каких условиях такое решение ещё приемлемо
- какой триггер заставляет нас вернуть вопрос в Stage 2 и заморозить auth or RBAC boundary

### Non-scope

Здесь не решаются:

- semantics `Activate`, это уже закрыто в [`plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md`](plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md:1)
- public `429` contract, это `F-003`
- ownership and persistence policy, это `F-002`

## Current baseline

### Current pilot scope

В [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:7) сейчас явно указано:

- без авторизации
- без ролей и разграничений
- только веб-интерфейс администратора сервиса
- первая реализация только для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1)

### Current runtime and dev context

С точки зрения текущего dev runtime:

- проект живёт в dev-container модели через [`docs/run/dev.md`](docs/run/dev.md:1)
- runtime env и deployment boundary документированы в [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- mutating admin action после `F-004` трактуется только как session-scoped in-memory override, а не как config mutation, см. [`plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md`](plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md:223)

### Why boundary is still needed

Даже при in-memory-only mutating action отсутствие auth boundary остаётся архитектурно чувствительным, потому что:

- сам admin surface остаётся операторским интерфейсом
- при выходе за пределы одного локального пользователя это уже не harmless convenience feature
- без явной пометки команда может позже воспринимать no-auth как норму для shared dev deployment

## Why critic is correct

Critic прав по сути полностью.

Здесь проблема не в том, что no-auth для PoC невозможен. Проблема в том, что без явной фиксации границы решение начинает выглядеть как канонический baseline.

Если эту границу не заморозить, downstream implementation может молча допустить:

- публикацию admin UI вне локального single-user контура
- перенос no-auth surface в shared dev environment
- расширение числа mutating actions без пересмотра security boundary

## Consolidated target model

Для `F-005` нужно зафиксировать простое правило:

- no-auth admin surface допустима **только** как локальный single-user PoC boundary
- это решение временное и контекстно-ограниченное
- при первом выходе за этот контекст вопрос обязан вернуться в Stage 2

## Decision options

### Option A: allow no-auth only for local single-user PoC

#### Summary

Оставляем no-auth boundary в пилоте, но помечаем её очень узко:

- только локальный single-user сценарий
- только PoC stage
- не shared dev
- не multi-user
- не internet or team-facing deployment

#### Pros

- не тормозит PoC
- соответствует текущему практическому сценарию
- не усложняет первую версию auth/RBAC слоем
- хорошо сочетается с тем, что mutating action из `F-004` остаётся in-memory-only

#### Cons

- требует явных предупреждений в планах и docs
- требует явного триггера на возврат в Stage 2

#### Verdict

Это лучший вариант для текущего этапа.

### Option B: remove all mutating actions while keeping no-auth

#### Summary
n
Оставляем no-auth, но допускаем только read-only admin UI.

#### Pros

- снижает риск no-auth surface
- проще объяснить security boundary

#### Cons

- конфликтует с уже принятым `F-004`, где `Activate` сохранён как полезный in-memory operator action
- обесценивает часть практической пользы пилота

#### Verdict

Для текущего направления уже не выглядит лучшим компромиссом.

### Option C: add auth immediately in pilot

#### Summary

Сразу проектируем auth or RBAC boundary даже для первой версии.

#### Pros

- security boundary сразу становится production-like

#### Cons

- сильно раздувает первый пилот
- отвлекает от проверки реальной ценности monitoring UI
- преждевременно втягивает Stage 2 в auth design без подтверждённой продуктовой необходимости

#### Verdict

Для текущей стадии слишком тяжёлый путь.

## Clarifications fixed during discussion

### No-auth is acceptable only because scope is tiny

Допустимость no-auth связана не с тем, что admin surface якобы безопасна сама по себе, а с тем, что current scope очень узкий:

- локальный запуск
- один оператор
- PoC
- ограниченный feature set
- отсутствует shared deployment requirement

### `Activate` does not cancel the need for boundary

После `F-004` action [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147) остаётся в пилоте, но это не отменяет нужду в boundary.

Наоборот, boundary должна явно сказать:

- mutating actions допустимы только в локальном single-user PoC
- если surface начинает использоваться за пределами этого контекста, нужна отдельная security freeze

### Return-to-Stage-2 trigger must be explicit

Самое важное в этом finding — не просто написать `пока без auth`, а зафиксировать условия, когда это решение перестаёт быть допустимым.

## Boundary policy proposal

### Allowed now

No-auth admin surface допустима, если одновременно верны все условия:

- интерфейс используется только локально одним оператором
- это PoC or exploratory stage
- feature используется только для внутренней разработки or локальной отладки
- нет требования разделения ролей и прав
- нет требования exposing admin surface в shared environment

### Forbidden without new Stage 2 freeze

Нельзя оставлять no-auth boundary, если появляется хотя бы одно из условий:

- admin UI становится доступен нескольким пользователям
- admin UI становится доступен вне локальной машины разработчика
- интерфейс попадает в shared dev environment
- добавляются более сильные mutating commands, чем текущий in-memory `Activate`
- появляется требование аудита операторских действий or RBAC
- появляется требование security review перед rollout

## Draft requirements

### US

- `US-F005-01`: как архитектор платформы, я хочу явно ограничить no-auth admin surface локальным PoC-контекстом, чтобы временное допущение не стало дефолтной нормой
- `US-F005-02`: как разработчик пилота, я хочу сохранить скорость итерации без раннего внедрения auth or RBAC
- `US-F005-03`: как будущий владелец production-like deployment, я хочу иметь чёткий trigger, когда нужно вернуть вопрос безопасности в Stage 2

### NFR

- `NFR-F005-01`: no-auth admin surface должна быть явно помечена как temporary PoC-only boundary
- `NFR-F005-02`: решение не должно трактоваться как baseline для shared dev or prod
- `NFR-F005-03`: переход за границы single-user local use обязан триггерить новый Stage 2 security discussion

### CONS

- `CONS-F005-01`: решение должно быть совместимо с текущим dev runtime контуром из [`docs/run/dev.md`](docs/run/dev.md:1)
- `CONS-F005-02`: решение должно быть совместимо с env and deployment narrative из [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- `CONS-F005-03`: решение должно учитывать уже принятый in-memory mutating action baseline из [`plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md`](plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md:223)

## Recommendation

Рекомендую принять `Option A`.

### Why

Это лучший компромисс между:

- быстрым PoC
- полезным operator UI
- отсутствием premature auth design
- и честной фиксацией того, что решение временное и локально-ограниченное

## Accepted decision

- Status: `accepted`
- Decision date: `2026-03-31`
- Accepted option: `Option A`

### Accepted statements

1. No-auth admin surface допустима только для локального single-user PoC.
2. Текущее решение не считается baseline для shared dev or prod.
3. Текущее решение допускается, потому что pilot ориентирован на быстрый локальный цикл разработки.
4. При первом выходе за пределы local single-user boundary вопрос auth or RBAC возвращается в Stage 2.
5. Mutating actions в no-auth surface допустимы только в пределах уже согласованного PoC scope.
6. На будущее фиксируется отдельный backlog item на auth и role-based access control, где минимум `observer` сможет только наблюдать, а `admin` сможет выполнять mutating operator actions.
7. Этот future backlog не входит в текущий PoC scope и не отменяет текущую временную no-auth границу.

## Consequences for plan rewrite

Если решение подтверждается, downstream нужно будет:

- переписать [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1), явно пометив no-auth surface как `local single-user PoC only`
- добавить explicit note, что это не shared dev baseline
- добавить trigger section: когда требуется вернуться к Stage 2 security freeze
- синхронизировать wording с [`plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md`](plans/discussion-f-004-activate-semantics-and-routing-boundary-openai-chatgpt-monitoring.md:1)

## Check: did we clarify everything for `F-005`

### Clarified and closed

Для `F-005` уже прояснены:

- почему no-auth допустим сейчас
- почему он не должен считаться нормой
- почему mutating action не отменяет need for boundary
- какой trigger должен вернуть вопрос в Stage 2

### Remaining open questions

Блокирующих open questions для `F-005` почти не осталось, но перед финальным freeze ещё нужно одно подтверждение человека:

1. подтверждаем ли мы, что локальный single-user PoC — это единственный допустимый контекст для no-auth admin surface на текущем этапе

После этого `F-005` можно считать замороженным.

## Next step

После freeze `F-005` можно переходить к rewrite исходных планов [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1) и [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1) с учётом решений `F-001`–`F-005`.
