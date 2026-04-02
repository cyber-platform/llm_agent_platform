# Discussion F-001: state and contract boundary for `openai-chatgpt` monitoring

## Context

Этот документ разбирает замечание `F-001` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:17) и подготавливает Stage 2 решение до правки [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1) и [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1).

Проблема critic сформулирована точно: текущий канон всё ещё опирается на legacy snapshot [`limits.json`](llm_agent_platform/services/runtime_state_paths.py:11), контракт [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) и runtime/documentation assumptions в [`docs/auth.md`](docs/auth.md:174), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:102), [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:69), тогда как новые планы уже фактически проектируют другой state boundary с [`usage_windows.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:173), [`request_usage.json`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:174) и admin read-model [`GET /admin/monitoring/providers/openai-chatgpt/accounts`](plans/openai-chatgpt-monitoring-frontend-prototype.md:242).

## Discovery scope

### Scope boundary

Нужно принять архитектурное решение по одному вопросу:

- сохраняем ли мы legacy contract [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) как канон для monitoring state;
- или переводим платформу на новый account-centric monitoring boundary с `usage_windows` и `request_usage` как отдельными provider-specific артефактами.

### Что не решаем в этом документе

- ownership matrix и write path arbitration для нескольких writer-ов — это отдельное замечание `F-002` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:35);
- mapping внутренних quota states во внешний `429` surface — это `F-003` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:53);
- semantics `Activate` — это `F-004` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:71).

## Current baseline

### Current contract and storage

Сейчас явно зафиксировано следующее:

- usage snapshot хранится отдельным provider-specific артефактом по пути [`usage_snapshot_path`](llm_agent_platform/services/runtime_state_paths.py:37), который сегодня ведёт в `usage/accounts/<account>/limits.json`;
- schema [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) описывает один object `limits` с произвольными ключами `primary`, `secondary` и metadata;
- [`docs/auth.md`](docs/auth.md:176) резервирует путь `<STATE_DIR>/openai-chatgpt/usage/limits.json`, что уже расходится с фактическим path resolver в [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48);
- [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:104) описывает usage state как normalized `primary/secondary` contract, но не различает monitoring snapshot и runtime request usage counters;
- общий layout в [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:73) знает только [`account_state.json`](docs/contracts/state/account-state.schema.json:1) и [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1), без provider-specific account monitoring files.

### Proposed plan baseline

Новые планы уже исходят из другого дизайна:

- account-centric layout в [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:163);
- раздельные файлы `usage_windows.json` и `request_usage.json` в [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:190);
- UI/backend read-model, который ожидает оба файла, в [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:344).

Вывод: сегодня у нас уже есть contract drift между docs, runtime path assumptions и Stage 2 plan artifacts.

## Why critic is correct

Critic прав в трёх пунктах:

1. Нельзя одновременно считать каноном legacy schema [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) и планировать новый layout без явного migration decision.
2. Нельзя проектировать admin read-model поверх файлов, которые ещё не получили platform-level contract freeze.
3. Нельзя оставлять рассинхрон между текстом в [`docs/auth.md`](docs/auth.md:176) и фактическим resolver-ом в [`llm_agent_platform/services/runtime_state_paths.py`](llm_agent_platform/services/runtime_state_paths.py:1), потому что это ломает docs-first SoT.

## Decision options

### Option A: keep legacy `limits.json` as canonical contract

#### Summary

Сохраняем [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) и [`limits.json`](llm_agent_platform/services/runtime_state_paths.py:11) как единственный канон monitoring snapshot.

#### Pros

- минимальный объём изменений в docs и runtime;
- нет немедленного breaking change для monitoring adapter;
- read-model можно строить поверх уже существующего snapshot.

#### Cons

- `limits.json` смешивает operator-facing windows и будущие refresh semantics слишком неявно;
- нет явной границы между monitoring snapshot и runtime request usage counters;
- UI-план всё равно ожидает richer model, что приведёт к ad-hoc DTO и новой скрытой схеме вне [`docs/contracts/`](docs/contracts:1);
- account-centric layout останется неполным и непоследовательным относительно [`account_state.json`](docs/contracts/state/account-state.schema.json:1).

#### Verdict

Для краткосрочного hotfix вариант допустим, но стратегически слабый. Он не закрывает архитектурную причину замечания `F-001`.

### Option B: replace legacy contract with new account-centric monitoring contracts

#### Summary

Замораживаем новый platform-level boundary:

- `account_state.json` остаётся общим runtime/router state;
- `usage_windows.json` становится provider-specific monitoring truth;
- `request_usage.json` становится provider-specific runtime observability truth;
- group-level [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) остаётся агрегированным monitoring snapshot.

#### Pros

- явно разделяет monitoring truth и request-usage truth;
- совпадает с account-centric layout из [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:163);
- даёт чистую основу для admin read-model из [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:242);
- лучше согласуется с platform principle о provider-specific optional state artifacts в [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:126).

#### Cons

- требует contract-first работы до implementation;
- потребует обновить несколько docs и path rules;
- legacy [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) либо удаляется, либо переводится в deprecated/migration status.

#### Verdict

Это лучший архитектурный вариант, если мы действительно хотим monitoring UI и two-level usage windows как устойчивую platform feature, а не одноразовый PoC-хак.

### Option C: transitional bridge

#### Summary

Сначала вводим новые contracts и layout, но временно поддерживаем bridge:

- writer пишет новый canonical `usage_windows.json`;
- optional compatibility layer ещё формирует legacy `limits.json` для старых читателей;
- admin read-model читает только новый канон.

#### Pros

- снижает риск migration breakage;
- позволяет перейти на новый канон без мгновенного удаления старого формата.

#### Cons

- удваивает surface area и тестовую матрицу;
- создаёт риск, что временный bridge станет постоянным хвостом;
- противоречит текущему желанию держать [`docs/`](docs:1) self-contained и без исторических хвостов.

#### Verdict

Допустимо только если после проверки кода выяснится, что legacy `limits.json` уже имеет несколько активных читателей. Пока по планам это не выглядит обязательным.

## Draft requirements

### US

- `US-F001-01`: как архитектор платформы, я хочу иметь один явный contract boundary для provider-specific monitoring state у [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1), чтобы docs, runtime и admin read-model не расходились.
- `US-F001-02`: как разработчик backend read-model, я хочу читать только канонические state artifacts, чтобы UI DTO не зависел от скрытых ad-hoc преобразований.
- `US-F001-03`: как оператор сервиса, я хочу видеть отдельно usage windows и request usage, чтобы monitoring и observability не смешивались в одном файле.

### NFR

- `NFR-F001-01`: state boundary должен быть contract-first и иметь явные schema artifacts в [`docs/contracts/`](docs/contracts:1) до начала implementation tasks.
- `NFR-F001-02`: docs-first SoT должен быть консистентным: path rules в [`docs/auth.md`](docs/auth.md:1), provider docs и architecture docs не должны противоречить [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48).
- `NFR-F001-03`: admin read-model не должен зависеть от legacy compatibility file, если этот файл помечен как transitional/deprecated.

### CONS

- `CONS-F001-01`: решение должно сохранять platform-level разделение между [`account_state.json`](docs/contracts/state/account-state.schema.json:1) как routing truth и provider-specific monitoring snapshot как observability truth.
- `CONS-F001-02`: решение не должно смешивать OAuth credentials и mutable monitoring state, согласно [`docs/auth.md`](docs/auth.md:190).
- `CONS-F001-03`: решение должно учитывать текущий account-centric layout в [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:163).

### OQ

- `OQ-F001-01`: legacy [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) удаляется полностью или переиздаётся как deprecated migration contract?
- `OQ-F001-02`: нужен ли временный compatibility bridge `limits.json`, или можно сразу перевести всех readers на `usage_windows.json`?
- `OQ-F001-03`: admin read-model payload должен получить собственный contract artifact в [`docs/contracts/`](docs/contracts:1) или пока остаётся backend-internal DTO?

## Recommendation

Рекомендую принять `Option B` как целевой Stage 2 baseline:

- новым каноном становится account-centric layout из [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:163);
- [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) нужно либо заменить новым schema artifact для `usage_windows.json`, либо перевести в deprecated status;
- `request_usage.json` нужно описать отдельным contract artifact до implementation;
- [`docs/auth.md`](docs/auth.md:174), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:102) и [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:69) нужно синхронизировать под новый boundary;
- вопрос про compatibility bridge оставить как отдельное короткое decision после проверки числа реальных readers.

## Proposed Stage 2 freeze for discussion

Если идём по рекомендуемому варианту, то я предлагаю заморозить следующее:

1. `account_state.json` — единственный канон routing/runtime state account-level.
2. `usage_windows.json` — единственный канон provider-specific monitoring windows для [`openai-chatgpt`](docs/providers/openai-chatgpt.md:1).
3. `request_usage.json` — отдельный provider-specific observability artifact, который не влияет на routing decisions.
4. [`quota_state.json`](docs/contracts/state/group-quota-state.schema.json:1) — агрегированный group snapshot, read-only для admin monitoring.
5. Legacy `limits.json` не считается долгосрочным каноном; максимум — временный migration bridge при доказанной необходимости.

## Accepted decision

Пользователь согласовал `Option B` как итоговое Stage 2 решение.

### Decision status

- Status: `accepted`
- Decision date: `2026-03-31`

### Accepted answers

1. Подтверждаем `Option B`: platform canonical boundary переводится на новый account-centric monitoring layout вместо legacy [`limits.json`](llm_agent_platform/services/runtime_state_paths.py:11).
2. Migration bridge не нужен: legacy `limits.json` и связанный legacy contract удаляются полностью как допустимый early-stage breaking change.
3. Admin read-model считается contract-first артефактом: для него нужно завести явный contract в [`docs/contracts/`](docs/contracts:1), а документация и code-level docstrings должны ссылаться именно на этот contract.

### Consequences for plan rewrite

- [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1) должен быть переписан так, чтобы новый account-centric boundary был объявлен единственным каноном без упоминания обратной совместимости.
- [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1) должен опираться только на новый contract-first layout и на отдельный contract admin read-model.
- [`docs/contracts/state/openai-chatgpt-usage-limits.schema.json`](docs/contracts/state/openai-chatgpt-usage-limits.schema.json:1) нужно вывести из канона и заменить новыми schema artifacts для `usage_windows.json`, `request_usage.json` и admin read-model.
- [`docs/auth.md`](docs/auth.md:174), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:102), [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:69) и path rules вокруг [`resolve_runtime_state_paths()`](llm_agent_platform/services/runtime_state_paths.py:48) должны синхронизироваться уже под новый boundary.

## Next finding

Следующий документ должен разобрать ownership matrix и write-path boundary из замечания `F-002` в [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:35).
