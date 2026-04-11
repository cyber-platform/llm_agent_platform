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
| DRIFT-001 | Admin monitoring runtime surface | Admin monitoring read-model канонизирован как backend API boundary между runtime и UI. См. [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md). | В `system-overview.md` прямо зафиксировано, что root runtime admin API materialized не полностью, а suite `TS-ADMIN-MONITORING-READ-MODEL` остается planned. См. [`system-overview.md`](./system-overview.md), [`docs/testing/suites/admin-monitoring-read-model.md`](../testing/suites/admin-monitoring-read-model.md). | `docs > code` | Высокий: boundary уже в SoT, но implementation/evidence неполны. | open | Сначала materialize backend admin API или сузить канон до planned boundary; затем активировать suite. |
| DRIFT-002 | Web UI container | `Web UI` канонизирован как отдельный human-facing container с `RBAC` и `LLM provider`-specific monitoring pages. См. [`web-ui.md`](./web-ui.md), [`container-view.md`](./container-view.md). | `Web UI` остается planned container и не имеет materialized local package map или active test contour. | `docs > code` | Средний: container useful for target architecture, но может читаться как ближняя реализация. | accepted planned gap | Держать как target boundary, но не расширять детали без materialization или отдельного repo-local context. |
| DRIFT-003 | Admin monitoring test evidence | Для admin read-model уже есть architecture boundary и API contracts. См. [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md), [`docs/contracts/api/admin/monitoring/`](../contracts/api/admin/monitoring). | В `test-map.md` suite `TS-ADMIN-MONITORING-READ-MODEL` всё еще planned, implementation root отсутствует. См. [`docs/testing/test-map.md`](../testing/test-map.md). | `docs != tests` | Высокий: contracts есть, но executable evidence пока нет. | open | Добавить suite implementation или явно пометить boundary как contract-only до следующего stage. |
| DRIFT-004 | Provider catalog lifecycle | `docs/providers/README.md` уже описывает не только static bootstrap catalogs, но и `Discovery-capable catalog` как canonized capability vocabulary. | Runtime readiness matrix materialized только для `openai-chatgpt`; discovery lifecycle не materialized и не закреплен отдельным active suite. См. [`docs/providers/README.md`](../providers/README.md). | `docs > code` | Средний: capability vocabulary может читаться как ближний supported path. | watch | Оставлять как capability taxonomy, но не добавлять concrete provider claims без отдельного architectural freeze и test evidence. |
| DRIFT-005 | `user service` / `users DB` boundary | В architecture set boundary пока не канонизирован и явно остается open question. См. [`component-view.md`](./component-view.md). | Отдельного focused document, ADR или decision note нет; boundary может всплывать в future discussions без формального решения. | `open question` | Средний: риск premature architecture assumptions. | open | Нужен explicit decision: `not in scope`, `planned boundary`, или новый focused document/ADR. |
| DRIFT-006 | Terminology completeness outside main entry points | В ключевых architecture/provider/auth/testing entry points уже разведены `LLM provider`, `abstract provider`, `provider implementation`, `OpenAI-compatible API`. | Во вторичных support docs и non-entry artifacts еще вероятны остаточные старые `provider`-формулировки; task 041 прямо оставляет этот хвост. См. [`operational_scope/tasks/041-software-architecture-documentation.md`](../../operational_scope/tasks/041-software-architecture-documentation.md). | `naming drift` | Средний: точечная semantic ambiguity при глубоком чтении. | open | Добить cleanup в secondary docs и закрыть отдельным pass без переписывания canonical entry points. |
| DRIFT-007 | Read-model vs persisted-file mental model | Канон фиксирует, что live admin/UI path строится из in-memory state, а persisted files нужны для restore/audit. См. [`admin-monitoring-read-model.md`](./admin-monitoring-read-model.md), [`quota-group-state-snapshot-and-state-dir.md`](./quota-group-state-snapshot-and-state-dir.md). | Contracts и docs сильные, но runtime/test evidence для полной read-model chain пока неполны; это особенно видно по planned admin suite. | `docs > tests` | Средний: риск неверного operational reading, будто persisted files already drive UI. | open | После materialization admin boundary добавить integration tests на end-to-end read path `in-memory -> admin API -> UI contract`. |

## Notes

- Этот register не является backlog всех улучшений и не заменяет `operational_scope/tasks/`.
- Accepted planned gaps допустимы, если они явно названы и не выдаются за already-materialized runtime.
- Новые записи стоит добавлять только для значимых расхождений, а не для любой wording-мелочи.
