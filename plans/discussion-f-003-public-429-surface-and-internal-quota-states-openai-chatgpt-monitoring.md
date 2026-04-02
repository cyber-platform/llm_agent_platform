# Discussion F-003: public `429` surface and internal quota states for `openai-chatgpt`

## Context

Этот документ закрывает замечание `F-003` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:53).

Проблема critic сформулирована точно: новые планы уже вводят более богатую внутреннюю семантику quota states для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1), но публичный OpenAI-compatible `429` contract по-прежнему гораздо уже и знает только два кода из [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1).

Если это не заморозить на Stage 2, то downstream implementation может разойтись по трём разным направлениям:

- runtime начнёт менять внешний `429` envelope
- UI начнёт жить по своей taxonomy
- планы будут описывать internal states как будто они уже обязаны отражаться наружу

## Discovery scope

В этом finding решаем только boundary между:

- internal или admin-only quota states
- публичным OpenAI-compatible `429` surface

### Non-scope

Здесь не решаются:

- ownership и write path policy для state artifacts, это уже закрыто в [`plans/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md`](plans/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md:1)
- contract-first admin read-model как endpoint family, это уже follow-up после `F-001` и `F-002`
- semantics admin action `Activate`, это `F-004`

## Current baseline

### Current public contract

Публичный `429` contract уже зафиксирован в [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1).

Он допускает только два `error.code`:

- `all_accounts_on_cooldown`
- `all_accounts_exceed_quota`

И только два `error.type`:

- `rate_limit_error`
- `insufficient_quota`

### Current test contour

Текущий test contour уже привязан к этой границе:

- contract suite в [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1)
- quota suite в [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)

Следовательно, изменение внешнего `429` surface — это не локальная деталь implementation, а contract change с прямым влиянием на tests и provider docs.

### New internal states introduced by plans

Новые планы вводят richer internal taxonomy.

В [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:91) уже зафиксировано, что `429 usage_limit_reached` нельзя автоматически считать weekly exhausted состоянием.

Также UI-план вводит состояния строки:

- `blocked_short_window`
- `blocked_long_window`
- `refresh_failed`
- `stale`

через [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:157).

То есть internal/admin vocabulary уже богаче, чем публичный contract.

## Why critic is correct

Critic прав полностью.

Проблема не в том, что richer internal taxonomy плоха. Наоборот, для monitoring и operator UX она полезна.

Проблема в том, что планы пока не фиксируют границу:

- какие состояния остаются internal-only
- какие состояния видит admin UI
- какие состояния допускается маппить во внешний OpenAI-compatible `429`

Без этого boundary появится contract drift:

- UI будет считать `blocked_short_window` самостоятельным публичным состоянием
- runtime может начать прокидывать provider-specific `usage_limit_reached` напрямую
- tests и schema останутся в старой модели

## Consolidated target model

Для `F-003` предлагается жёстко разделить **внутреннюю quota taxonomy** и **внешний OpenAI-compatible error envelope**.

### Core principle

Внутреннее состояние сервиса может быть богаче публичного API.

Это нормально и даже желательно.

Но внешний OpenAI-compatible surface должен оставаться минимальным и стабильным, пока не принято отдельное contract-breaking решение.

## Decision options

### Option A: keep public `429` contract unchanged, internal states stay internal or admin-only

#### Summary

Оставляем внешний `429` contract без изменений:

- `all_accounts_on_cooldown`
- `all_accounts_exceed_quota`

Все новые состояния из monitoring и provider-specific logic считаются:

- internal runtime states
- либо admin-only states в backend read-model и UI

#### Mapping rule

- short-window local block сам по себе не обязан отражаться наружу как новый публичный код
- weekly saturation сама по себе не обязана отражаться наружу как новый публичный код
- richer states используются для routing, monitoring и admin UX
- наружу они маппятся только в уже существующие aggregated public outcomes

#### Pros

- сохраняется стабильность OpenAI-compatible API
- не нужно ломать schema и тесты
- UI может быть богаче, чем public API, без конфликта
- provider-specific taxonomy не протекает наружу

#### Cons

- публичный клиент видит более грубую картину, чем оператор в admin UI
- часть richer semantics будет intentionally hidden от внешнего API

#### Verdict

Это самый безопасный и архитектурно чистый вариант для текущего этапа проекта.

### Option B: expand public `429` contract with provider-specific codes

#### Summary

Расширяем [`429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1), добавляя provider-specific или richer codes:

- `blocked_short_window`
- `blocked_long_window`
- `refresh_failed`
- `stale`
- возможно provider-specific `usage_limit_reached`

#### Pros

- внешний контракт становится информативнее
- public API ближе к внутренней taxonomy

#### Cons

- ломает текущий OpenAI-compatible минималистичный surface
- резко увеличивает coupling между provider-specific semantics и public API
- потребует синхронной правки schema, docs, tests и client assumptions
- затруднит поддержку нескольких providers с разной quota vocabulary

#### Verdict

Для текущего этапа это слишком дорогой и рискованный путь.

### Option C: staged hybrid, where some internal states may later promote into public codes

#### Summary

Сейчас сохраняем внешний contract, но заранее допускаем, что позже некоторые internal states могут быть повышены до public surface через отдельное Stage 2 решение.

#### Pros

- оставляет пространство для эволюции
- не требует ломать contract прямо сейчас

#### Cons

- если зафиксировать это слишком расплывчато, снова появится неоднозначность в implementation
- без строгого wording команды могут начать раньше времени протаскивать richer public mapping

#### Verdict

Допустимо только как secondary note, но не как основной operational baseline.

## Clarifications fixed during discussion

### Public API vs admin UI

В обсуждении `F-002` уже зафиксировано, что frontend получает только backend admin read-model, а не читает state files напрямую через [`plans/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md`](plans/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md:1).

Следовательно, admin UI может и должен жить по richer taxonomy, не заставляя public API меняться.

### Meaning of short-window block

`usage_limit_reached` с `resets_at` или `resets_in_seconds` для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) трактуется как internal short-window block, а не как автоматический публичный `all_accounts_exceed_quota`, согласно [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:91).

### Meaning of long-window saturation

Long-window saturation сама по себе тоже не должна автоматически становиться новым публичным кодом.

Она может использоваться как:

- routing hint
- monitoring signal
- admin-only status

Но во внешний `429` surface должна попадать только через уже зафиксированный агрегированный outcome, если runtime действительно пришёл к `all_accounts_exceed_quota` по контрактной логике.

### Internal taxonomy is allowed to be richer

Наличие внутренних состояний вроде:

- `blocked_short_window`
- `blocked_long_window`
- `refresh_failed`
- `stale`

не является проблемой само по себе.

Проблемой было отсутствие зафиксированной границы между этими состояниями и публичным envelope.

## Mapping policy proposal

### Internal or admin-only states

Следующие состояния считаются internal/admin-only и не должны напрямую протекать в публичный OpenAI-compatible `429` contract:

- `blocked_short_window`
- `blocked_long_window`
- `refresh_failed`
- `stale`
- provider-specific `usage_limit_reached` как raw semantic label
- любые provider-local refresh или monitoring states

### Public `429` surface

Во внешний API разрешено отдавать только два contract-level outcome из [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1):

- `all_accounts_on_cooldown`
- `all_accounts_exceed_quota`

### Public mapping rule

Внешний `429` формируется не из отдельных internal labels, а из агрегированного runtime conclusion:

- если runtime пришёл к состоянию `all available accounts are on cooldown` → `all_accounts_on_cooldown`
- если runtime пришёл к состоянию `all available accounts are exhausted by contract logic` → `all_accounts_exceed_quota`
- intermediate provider-specific блокировки и monitoring signals остаются internal or admin-only

## Draft requirements

### US

- `US-F003-01`: как архитектор платформы, я хочу жёстко разделить internal quota taxonomy и внешний OpenAI-compatible error surface, чтобы provider-specific semantics не протекала наружу случайно
- `US-F003-02`: как разработчик admin UI, я хочу иметь richer internal statuses, не ломая публичный API контракт
- `US-F003-03`: как разработчик public API, я хочу сохранить стабильный minimal `429` envelope, чтобы tests и client assumptions не дрейфовали

### NFR

- `NFR-F003-01`: public `429` surface не меняется без отдельного contract-first решения
- `NFR-F003-02`: internal/admin states могут быть богаче публичного API
- `NFR-F003-03`: mapping в публичный `429` должен происходить только из агрегированного runtime conclusion, а не из raw provider labels
- `NFR-F003-04`: test contour должен явно отражать границу public vs internal states

### CONS

- `CONS-F003-01`: решение должно оставаться совместимым с [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1)
- `CONS-F003-02`: решение должно быть совместимым с [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1) и [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
- `CONS-F003-03`: решение должно сохранять richer admin taxonomy из [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:157)

## Recommendation

Рекомендую принять `Option A` как accepted baseline, а `Option C` оставить только как future note без operational ambiguity.

### Why

Этот вариант:

- сохраняет стабильный публичный API
- лучше всего согласуется с multi-provider архитектурой
- позволяет UI и monitoring быть богаче без протечки provider-specific semantics наружу
- не требует немедленного breaking change в schema, docs и tests

## Accepted decision

- Status: `accepted`
- Decision date: `2026-03-31`
- Accepted option: `Option A`

### Accepted statements

1. Внешний OpenAI-compatible `429` contract пока не расширяется.
2. Публично допустимы только `all_accounts_on_cooldown` и `all_accounts_exceed_quota` из [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1).
3. Internal/admin taxonomy для monitoring и routing может быть богаче публичного API.
4. Для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1) short-window и long-window блокировки могут приходить как один и тот же upstream класс `429`, различаясь duration и message semantics, но это не создаёт новых public error codes в нашем контракте.
5. Для нашего сервиса ключевой internal результат — нормализованный `block_account_until` плюс metadata о характере блокировки, чтобы общий router мог учитывать длительность блокировки независимо от provider-specific wording.
6. `usage_limit_reached` и другие provider-specific quota labels трактуются как internal provider-specific signals, а не как автоматические новые public error codes.
7. Long-window saturation остаётся internal/admin signal до момента, когда runtime по contract logic действительно приходит к агрегированному `all_accounts_exceed_quota`.
8. Admin UI может показывать `blocked_short_window`, `blocked_long_window`, `refresh_failed`, `stale` и другие richer states без изменения внешнего OpenAI-compatible contract.

## Consequences for plan rewrite

Если решение подтверждается, downstream нужно будет:

- переписать [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1), явно отделив internal quota semantics от public `429` mapping
- переписать [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1), явно пометив row statuses как admin-only taxonomy
- добавить traceability из plan rewrite в [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1) и [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1)
- при необходимости позже завести отдельный Stage 2 discussion, если кто-то захочет реально расширять public error schema

## Check: did we clarify everything for `F-003`

### Clarified and closed

Для `F-003` уже прояснены ключевые архитектурные вопросы:

- какие состояния должны оставаться internal or admin-only
- какие коды допустимы во внешнем `429`
- что short-window block не равен автоматически `all_accounts_exceed_quota`
- что long-window saturation не обязана сама по себе становиться публичным кодом
- что richer admin taxonomy допустима без изменения public API

### Remaining open questions

Блокирующих open questions для `F-003` больше не осталось.

Остаются только downstream design details, которые уже не меняют принятое решение:

1. точная wording policy для `message` внутри публичного `429` при short-window и long-window случаях
2. точная нормализация metadata в admin read-model для различения short-window и long-window block duration
3. конкретные тест-кейсы, которые будут добавлены в contract suite и admin UI suite после rewrite планов

## Next finding

Следующий документ после freeze `F-003` должен разбирать `F-004` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:71) про semantics [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147) и совместимость с groups и `rounding` semantics.
