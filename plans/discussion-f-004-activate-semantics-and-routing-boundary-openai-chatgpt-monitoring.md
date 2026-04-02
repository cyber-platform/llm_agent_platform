# Discussion F-004: `Activate` semantics and routing boundary for `openai-chatgpt` monitoring UI

## Context

Этот документ закрывает замечание `F-004` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:71).

Проблема critic была сформулирована правильно: action [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147) нельзя оставлять как расплывчатую UI-кнопку без замороженной semantics.

После обсуждения с пользователем зафиксировалась более точная трактовка:

- `Activate` не создаёт новый routing mode
- `Activate` не меняет файлы provider config
- `Activate` работает только как **in-memory operator override** для текущей жизни процесса
- цель action — ручное переключение на удобный аккаунт для живого наблюдения за системой и ручного тестирования эвристик

## Discovery scope

В этом finding решается только вопрос:

- что именно означает [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147) в pilot UI
- как это согласуется с `single` и `rounding`
- какие границы нельзя нарушать

### Non-scope

Здесь не решаются:

- auth or no-auth boundary для admin surface, это `F-005`
- public `429` contract, это `F-003`
- ownership и write path policy, это `F-002`

## Current baseline

### Config semantics

В каноне accounts-config:

- `single` — используется `active_account` в [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:43)
- `rounding` — используется rotation pool из `all_accounts` или group pool в [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:45)

В примере [`openai_chatgpt_accounts_config.example.json`](docs/examples/openai_chatgpt_accounts_config.example.json:1):

- поле `active_account` существует
- но `mode` уже установлен в `rounding`
- значит само наличие `active_account` не может автоматически означать глобальную runtime semantics для всех режимов

### Runtime semantics

В runtime router:

- для `single` [`select_account()`](llm_agent_platform/services/account_router.py:121) выбирает `cfg.active_account`
- для `rounding` [`select_account()`](llm_agent_platform/services/account_router.py:121) выбирает аккаунт из available pool
- pool определяется через [`_resolve_pool()`](llm_agent_platform/services/account_router.py:629)
- router уже учитывает cooldown, exhausted state и group isolation

### Important drift already visible

Без уточнения action [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147) мог быть ошибочно понят как:

- редактирование `active_account` в config file
- provider-wide forced pin
- отключение обычной rotation policy
- bypass cooldown or exhausted checks

Именно это drift critic и подсветил.

## Why critic is correct

Critic прав в главном:

- action затрагивает выбор аккаунта и therefore влияет на runtime behavior
- без явного freeze команды могли бы реализовать принципиально разные модели
- UI-план не должен молча вводить новый contract на границе routing

Но после обсуждения стало ясно, что существует безопасная трактовка action без изобретения новой стратегии.

## Clarifications fixed during discussion

### `Activate` is in-memory only

Ключевое уточнение пользователя:

- выбранный аккаунт не записывается в config files
- [`provider-accounts-config`](docs/configuration/provider-accounts-config.md:1) остаётся без изменений
- override живёт только в текущем in-memory состоянии сервиса
- после рестарта система снова стартует от канонического config baseline

Это снимает главный риск скрытой мутации operator config.

### `Activate` is for live operational experimentation

Action нужен не для переписывания канона, а для живого использования системы:

- переключиться на удобный аккаунт во время работы
- посмотреть, как система ведёт себя в реальных сценариях
- вручную тестировать и наблюдать эвристики выбора аккаунтов
- собрать практический материал для будущих стратегий

То есть это operator convenience action, а не config management feature.

### `Activate` in `single`

Для `single` semantics простая:

- оператор выбирает другой аккаунт
- этот аккаунт становится текущим preferred account в памяти процесса
- config file при этом не переписывается
- после рестарта runtime снова возьмёт baseline из config

### `Activate` in `rounding`

Для `rounding` semantics тоже допустима, если её узко зафиксировать:

- оператор выбирает preferred account в memory
- это влияет только на текущее состояние сервиса
- аккаунт всё равно выбирается из допустимых по текущим правилам
- action не bypass-ит cooldown
- action не bypass-ит exhausted checks
- action не отменяет rotation policy
- action не ломает group isolation

Иными словами:

- `Activate` не означает `всегда использовать только этот аккаунт`
- `Activate` означает `сделать этот аккаунт предпочтительным кандидатом внутри уже существующего runtime selection`

### `Activate` does not create a new routing strategy

Важно разделять:

- изменение **входного предпочтения** для текущей стратегии
- и изменение **самой стратегии**

В принятой трактовке action делает только первое.

### `g0` is not an operator-facing semantic anchor

Текущее `g0` в runtime — технический fallback key в [`QuotaAccountRouter._resolve_pool()`](llm_agent_platform/services/account_router.py:629), а не хорошая operator-facing модель.

Следовательно:

- UI не должен строить смысл action вокруг `g0`
- backend read-model должен отдельно нормализовать operator-facing scope
- internal runtime key может остаться внутренней деталью

## Consolidated target model

Для `F-004` принимается следующая модель:

1. `Activate` остаётся в pilot UI.
2. Это **in-memory only** action.
3. Он не меняет config files.
4. Он не меняет канонические routing rules.
5. Он влияет только на текущее runtime состояние процесса.
6. Он нужен как ручной operator override для рабочей сессии и ручного тестирования поведения системы.

## Allowed semantics

### In `single`

`Activate` означает:

- выбрать другой preferred account для текущего процесса
- использовать его как текущий основной аккаунт режима `single`
- не переписывать config baseline

### In `rounding`

`Activate` означает:

- выбрать preferred account для текущего процесса
- использовать его как предпочтительный кандидат внутри уже существующего `rounding` выбора
- сохранить все действующие ограничения и safeguards

### Explicitly forbidden meanings

`Activate` не должен означать:

- редактирование `accounts_config.json`
- постоянное переопределение config baseline
- bypass cooldown
- bypass exhausted logic
- bypass group isolation
- новый routing mode
- скрытый TTL contract, если он не введён отдельным решением

## Draft requirements

### US

- `US-F004-01`: как оператор сервиса, я хочу вручную переключиться на удобный аккаунт во время работы системы, не изменяя канонический config
- `US-F004-02`: как архитектор платформы, я хочу ограничить semantics `Activate`, чтобы action не превратился в скрытую замену routing strategy
- `US-F004-03`: как разработчик UI and backend, я хочу, чтобы action был полезен для ручного тестирования системы, но не ломал runtime invariants

### NFR

- `NFR-F004-01`: `Activate` работает только in-memory и не пишет в provider config files
- `NFR-F004-02`: `Activate` не bypass-ит cooldown, exhausted checks и group isolation
- `NFR-F004-03`: `Activate` не меняет `single | rounding` semantics
- `NFR-F004-04`: после рестарта runtime возвращается к config baseline
- `NFR-F004-05`: UI не использует `g0` как операторский semantic label

### CONS

- `CONS-F004-01`: решение должно быть совместимо с [`docs/configuration/provider-accounts-config.md`](docs/configuration/provider-accounts-config.md:1)
- `CONS-F004-02`: решение должно уважать pool resolution и safeguards в [`llm_agent_platform/services/account_router.py`](llm_agent_platform/services/account_router.py:121)
- `CONS-F004-03`: решение не должно превращать pilot UI в config editor

## Recommendation

Рекомендую зафиксировать `Activate` как **session-scoped in-memory preferred-account override**.

### Why

Этот вариант:

- сохраняет полезность action в пилоте
- не требует переписывать config files
- не ломает канон routing
- хорошо сочетается с in-memory-first моделью, уже принятой в [`plans/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md`](plans/discussion-f-002-state-ownership-and-write-paths-openai-chatgpt-monitoring.md:1)
- создаёт хороший операторский инструмент для ручного тестирования heuristics

## Accepted decision

- Status: `accepted`
- Decision date: `2026-03-31`
- Accepted option: `Activate as in-memory preferred-account override`

### Accepted statements

1. [`Activate`](plans/openai-chatgpt-monitoring-frontend-prototype.md:147) не удаляется из pilot scope.
2. Action работает только на in-memory состоянии текущего процесса.
3. Action не записывает выбранный аккаунт в provider config files.
4. Для `single` action меняет текущий preferred account процесса.
5. Для `rounding` action задаёт preferred account внутри уже существующей selection strategy.
6. Action не bypass-ит cooldown, exhausted checks, group isolation или rotation policy.
7. После рестарта runtime всё возвращается к config baseline.
8. Action допускается как инструмент ручного operational experimentation и наблюдения за реальным поведением системы.

## Consequences for plan rewrite

Теперь downstream plans нужно переписать так, чтобы в них больше не оставалось:

- формулировок, будто `Activate` меняет config files
- формулировок, будто `Activate` вводит новый routing mode
- provider-wide vague semantics без in-memory-only boundary

Конкретно требуется:

- обновить [`plans/openai-chatgpt-monitoring-frontend-prototype.md`](plans/openai-chatgpt-monitoring-frontend-prototype.md:1), описав `Activate` как session-scoped in-memory override
- поправить payload contract так, чтобы action явно отражал in-memory nature и текущий scope
- синхронизировать [`plans/openai-chatgpt-two-level-usage-windows-analysis.md`](plans/openai-chatgpt-two-level-usage-windows-analysis.md:1), если там остаются vague assumptions about activation semantics
- отдельно нормализовать operator-facing group identity, не опираясь на `g0`

## Check: did we clarify everything for `F-004`

### Clarified and closed

Для `F-004` уже прояснены все ключевые архитектурные вопросы:

- должен ли `Activate` остаться в пилоте
- меняет ли он config files
- как он трактуется в `single`
- как он трактуется в `rounding`
- bypass-ит ли он ограничения router
- зачем он нужен операторски
- как он согласуется с in-memory-first моделью сервиса

### Remaining open questions

Блокирующих open questions для `F-004` больше не осталось.

Остаются только downstream design details, которые не меняют freeze решения:

1. точная форма admin command contract для action response
2. точный runtime internal representation preferred-account override
3. точный operator-facing scope label для default group вместо `g0`

## Next finding

Следующий документ должен разбирать `F-005` из [`plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md`](plans/critic-openai-chatgpt-monitoring-and-usage-plans-2026-03-30.md:89) про границы no-auth admin surface как временного PoC-допущения.
