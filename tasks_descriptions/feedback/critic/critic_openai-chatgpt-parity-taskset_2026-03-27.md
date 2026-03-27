# Critic report: `openai-chatgpt` parity taskset

## Report metadata

- Date: 2026-03-27
- Target feature / plan: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:1)
- Target task set: [`tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md`](tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md:1), [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1), [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:1)
- Critic execution profile: role=Critic, reasoning level=4, skills=[`critic-taskset-semantic-critique`](../critic/critic_openai-chatgpt-parity-taskset_2026-03-27.md:1)

## Executive summary

- Overall assessment: `needs-return-to-stage-2`
- High-severity findings count: 4
- Recommended immediate action: заморозить contract semantics для account auth-health, router terminal states и snapshot impact до старта реализации.

## Findings

### Finding F-001: не зафиксирован contract для расширения [`account_state.json`](docs/contracts/state/account-state.schema.json:1)

- Severity: `high`
- Problem: план уже решил хранить auth-health в общем [`account_state.json`](docs/contracts/state/account-state.schema.json:1), но сам контракт пока знает только `last_used_at`, `cooldown` и `quota_exhausted` в [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:8). При этом задача [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:22) говорит про новый auth-health state, но не фиксирует точный schema shape, optionality и generic naming.
- Impact: реализация начнёт «додумывать» runtime contract в Stage 4; высок риск разъезда между кодом, docs и тестами, а также между [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:27) и каноническим schema.
- Evidence / references: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:188), [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:250), [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1), [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:25)
- Proposed fix:
  - [ ] Вернуть поток в Stage 2 и зафиксировать точный contract для optional `auth` block внутри [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1)
  - [ ] Явно определить generic поля блока `auth` и их семантику: `status`, `reason`, `detected_at`, `last_refresh_attempt_at`, `recommended_action`
  - [ ] Зафиксировать backward compatibility: отсутствие `auth` блока = `unknown`, а не `invalid`
- Traceability:
  - Tasks to update / create: [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1), [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:1)

### Finding F-002: есть риск потери полей из-за last-write-wins по одному файлу [`account_state.json`](llm_agent_platform/services/account_state_store.py:22)

- Severity: `high`
- Problem: coalesce map в [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:58) работает по принципу last-write-wins на весь файл. Если auth-layer и quota/router layer начнут независимо писать один и тот же [`account_state.json`](llm_agent_platform/services/account_state_store.py:22), один payload может затереть поля другого. План это не проговаривает.
- Impact: можно потерять `quota_exhausted`, `cooldown` или новый `auth` block при конкурентных update-path; это приведёт к трудноуловимым state corruption багам и невалидному routing поведению.
- Evidence / references: [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:67), [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:160), [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:239), [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:210)
- Proposed fix:
  - [ ] Не разрешать ad-hoc запись auth-state отдельным модулем напрямую в файл
  - [ ] Расширить единый owner boundary [`llm_agent_platform/services/account_state_store.py`](llm_agent_platform/services/account_state_store.py:1): dataclass, load/save helpers и mutation APIs должны знать про весь envelope целиком
  - [ ] В Stage 2 явно зафиксировать, что новый `auth` block — часть того же canonical envelope, а не независимый payload
- Traceability:
  - Tasks to update / create: [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1)

### Finding F-003: не определено влияние auth-invalid на monitoring snapshot и group-level observability

- Severity: `high`
- Problem: router должен исключать auth-invalid аккаунты по [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:223), но текущий group snapshot contract считает только cooldown/exhausted в [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:158) и [`docs/testing/suites/quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md:38). Не определено, должны ли auth-invalid аккаунты отражаться в [`quota_state.json`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:144), и если да — в каком виде.
- Impact: routing и admin-observability разъедутся: группа может быть фактически неработоспособной, но monitoring snapshot продолжит выглядеть «здоровым». Это создаст ложную диагностику и затруднит эксплуатацию.
- Evidence / references: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:221), [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:144), [`docs/testing/suites/quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md:32), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:22)
- Proposed fix:
  - [ ] Вернуть вопрос в Stage 2 и решить, входит ли auth-invalid в group snapshot contract
  - [ ] Если входит — расширить [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1) и suite [`docs/testing/suites/quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md:1)
  - [ ] Если не входит — явно зафиксировать альтернативный monitoring channel для auth-invalid accounts и не обещать их видимость через group snapshot
- Traceability:
  - Tasks to update / create: [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1), [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:1)

### Finding F-004: не заморожен внешний error contract для сценариев `single invalid` и `all accounts auth-invalid`

- Severity: `high`
- Problem: план и задача [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:22) вводят новый terminal state `all accounts auth-invalid`, но не определяют HTTP status, `error.type`, `error.message` и различие между `single` и `rounding` path. Это уже внешний observable behavior OpenAI-compatible surface.
- Impact: реализация может произвольно выбрать 401/403/429/500; тесты и клиенты начнут зависеть от незафиксированного поведения. Это прямой semantic gap перед реализацией.
- Evidence / references: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:228), [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:235), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:23), [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1), [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:29)
- Proposed fix:
  - [ ] Вернуть в Stage 2 решение по OpenAI-compatible error envelope для `auth-invalid`
  - [ ] Явно определить, какой status/error.type/message используется для `single invalid account`
  - [ ] Явно определить, какой status/error.type/message используется для `all accounts auth-invalid`
  - [ ] Добавить traceability в suite [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1) и при необходимости в отдельный error contract
- Traceability:
  - Tasks to update / create: [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1), [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:1)

### Finding F-005: не определён recovery path для уже помеченного `invalid_grant` аккаунта

- Severity: `medium`
- Problem: план говорит, что состояние может перейти `invalid_grant -> valid` после reauth в [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:247), но не определено, кто и когда снимет флаг invalid, если router уже исключил аккаунт. Не зафиксировано, происходит ли clear автоматически при успешном чтении новых creds, при bootstrap script, при старте процесса или при отдельном maintenance path.
- Impact: есть риск зависшего invalid state, когда оператор обновил creds, но runtime продолжает игнорировать аккаунт.
- Evidence / references: [`plans/openai-chatgpt-parity-audit-plan.md`](plans/openai-chatgpt-parity-audit-plan.md:239), [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:29), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:26)
- Proposed fix:
  - [ ] Явно описать trigger снятия invalid state
  - [ ] Указать owner этого перехода: bootstrap script, auth manager или отдельный reconcile step
  - [ ] Добавить тест-кейс на reauth recovery и повторное включение аккаунта в pool
- Traceability:
  - Tasks to update / create: [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1)

### Finding F-006: тестовый контур и doc-sync не покрывают все изменяемые канонические артефакты

- Severity: `medium`
- Problem: задача [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:25) ссылается в основном на [`docs/testing/suites/openai-contract.md`](docs/testing/suites/openai-contract.md:1), но новые semantics затрагивают также [`docs/testing/suites/quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md:1), [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:1), [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1) и, возможно, [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:60).
- Impact: часть канона останется несинхронизированной, а тест map не будет отражать новые требования.
- Evidence / references: [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:15), [`docs/testing/suites/quota-state-persistence.md`](docs/testing/suites/quota-state-persistence.md:28), [`docs/testing/suites/quota-account-rotation.md`](docs/testing/suites/quota-account-rotation.md:23), [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:60)
- Proposed fix:
  - [ ] Расширить scope [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:1) на state/rotation suites и schema sync
  - [ ] Явно добавить в verification contour документы и тесты, связанные с state persistence и router semantics
- Traceability:
  - Tasks to update / create: [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:1)

## Non-findings (what is explicitly fine)

- Декомпозиция на отдельные ветки [`tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md`](tasks_descriptions/tasks/034-openai-chatgpt-tool-and-streaming-parity.md:1), [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1), [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1) и [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:1) в целом логична и соответствует архитектурным boundaries.
- Решение не удалять credentials автоматически и держать remediation через [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1) согласуется с separation of concerns между secrets и runtime state.
- Capability-gated rollout для auth-health хорошо вписывается в provider-centric модель и не ломает providers без такой диагностики.
- Решение писать auth-health через тот же persistence boundary и coalesce-map механизм согласуется с [`docs/architecture/quota-group-state-snapshot-and-state-dir.md`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:222), если будет один canonical owner envelope.

## Open questions raised by Critic

- Должен ли [`auth` block](docs/contracts/state/account-state.schema.json:1) быть полностью generic для всех providers или допускается provider-specific `reason` vocabulary только в metadata? → эскалировать в Stage 2 / Architect.
- Должен ли `all accounts auth-invalid` входить в тот же класс пользовательских ошибок, что и quota/cooldown, или это отдельный auth-failure contract? → эскалировать в Stage 2 / Architect.
- Нужно ли отражать auth-invalid состояние в [`quota_state.json`](docs/architecture/quota-group-state-snapshot-and-state-dir.md:144) или нужен отдельный monitoring snapshot? → эскалировать в Stage 2 / Architect.
- Кто снимает invalid flag после reauth: [`scripts/get_openai-chatgpt_credentials.py`](scripts/get_openai-chatgpt_credentials.py:1), [`llm_agent_platform/auth/openai_chatgpt_oauth.py`](llm_agent_platform/auth/openai_chatgpt_oauth.py:1) или отдельный runtime reconcile path? → эскалировать в Stage 2 / Architect.

## Suggested changes to Stage 3 artifacts

- Уточнить [`tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md`](tasks_descriptions/tasks/035-openai-chatgpt-auth-invalid-state.md:1): auth-health должен быть описан как расширение canonical envelope [`account_state.json`](docs/contracts/state/account-state.schema.json:1), а не как расплывчатый «отдельный state».
- Уточнить [`tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md`](tasks_descriptions/tasks/036-account-router-auth-invalid-exclusion.md:1): добавить явную зависимость от freeze error semantics и snapshot decision.
- Уточнить [`tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md`](tasks_descriptions/tasks/037-openai-chatgpt-parity-regression-and-doc-sync.md:1): добавить sync для state/rotation suites и schema contracts.
- До реализации вернуть поток в Stage 2 для фиксации contract-level решений по [`docs/contracts/state/account-state.schema.json`](docs/contracts/state/account-state.schema.json:1), возможному обновлению [`docs/contracts/state/group-quota-state.schema.json`](docs/contracts/state/group-quota-state.schema.json:1) и внешнему error contract.