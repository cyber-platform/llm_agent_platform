# Drift Register

## Назначение

Этот документ фиксирует известные расхождения между архитектурным каноном, contracts/testing evidence и текущим уровнем materialization в runtime.

Он нужен, чтобы:

- явно отделять accepted target architecture от уже materialized runtime;
- не маскировать planned gaps под якобы завершённую реализацию;
- давать короткий navigation list для следующих doc-fix, contract-fix и code-fix задач.

## Как читать записи

- `Canonical expectation` — что уже зафиксировано в SoT.
- `Observed state` — что видно по docs/tests/runtime evidence сейчас.
- `Drift type` — тип расхождения: `docs > code`, `docs != tests`, `naming drift`, `open question`.
- `Resolution path` — какой следующий шаг нужен: doc fix, code fix, contract/test completion или explicit decision.

## Register

| Drift ID | Area | Canonical expectation | Observed state | Drift type | Impact | Status | Resolution path |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DRIFT-002 | Web UI container vs target architecture breadth | `Web UI` канонизирован как отдельный human-facing container с `RBAC`, dynamic provider navigation и provider-specific monitoring pages. См. [`web-ui.md`](./web-ui.md), [`container-view.md`](./container-view.md). | Local-only operator `Web UI` slice уже materialized в `services/frontend`, но покрывает только `openai-chatgpt` PoC boundary и не materialize-ит full target UI architecture. | `accepted planned gap` | Средний: риск читать current PoC slice как already-complete target UI. | watch | Держать distinction между materialized PoC operator slice и wider target `Web UI`; уточнять по мере multi-provider/UI scope expansion. |
| DRIFT-004 | Provider catalog lifecycle | `docs/providers/README.md` уже описывает не только static bootstrap catalogs, но и `Discovery-capable catalog` как canonized capability vocabulary. | Runtime readiness matrix materialized только для `openai-chatgpt`; discovery lifecycle не materialized и не закреплен отдельным active suite. См. [`docs/providers/README.md`](../providers/README.md). | `docs > code` | Средний: capability vocabulary может читаться как ближний supported path. | watch | Оставлять как capability taxonomy, но не добавлять concrete provider claims без отдельного architectural freeze и test evidence. |
| DRIFT-005 | `user service` / `users DB` boundary | В architecture set boundary пока не канонизирован и явно остается open question. См. [`component-view.md`](./component-view.md). | Отдельного focused document, ADR или decision note нет; boundary может всплывать в future discussions без формального решения. | `open question` | Средний: риск premature architecture assumptions. | open | Нужен explicit decision: `not in scope`, `planned boundary`, или новый focused document/ADR. |
| DRIFT-006 | Terminology completeness outside main entry points | В ключевых architecture/provider/auth/testing entry points уже разведены `LLM provider`, `abstract provider`, `provider implementation`, `OpenAI-compatible API`. | Во вторичных support docs и non-entry artifacts еще вероятны остаточные старые `provider`-формулировки; task 041 прямо оставляет этот хвост. См. [`operational_scope/tasks/041-software-architecture-documentation.md`](../../operational_scope/tasks/041-software-architecture-documentation.md). | `naming drift` | Средний: точечная semantic ambiguity при глубоком чтении. | open | Добить cleanup в secondary docs и закрыть отдельным pass без переписывания canonical entry points. |
| DRIFT-007 | Read-model vs persisted-file mental model | Канон фиксирует, что live admin/UI path строится из process-local monitoring runtime, а persisted files нужны только для startup hydration, restore/audit. См. [`platform-monitoring-runtime.md`](./platform-monitoring-runtime.md), [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md), [`quota-group-state-snapshot-and-state-dir.md`](./quota-group-state-snapshot-and-state-dir.md). | Docs синхронизированы на memory-first model, но multi-instance coordination и universal provider normalization сознательно остаются вне materialized scope. | `open question` | Средний: риск premature assumptions при выходе за single-instance PoC. | open | Вернуться отдельной архитектурной задачей при multi-instance rollout или при materialization новых provider monitoring pages. |

## Notes

- Этот register не является backlog всех улучшений и не заменяет `operational_scope/tasks/`.
- Accepted planned gaps допустимы, если они явно названы и не выдаются за already-materialized runtime.
- Новые записи стоит добавлять только для значимых расхождений, а не для любой wording-мелочи.
