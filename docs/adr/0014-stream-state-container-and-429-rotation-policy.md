# ADR-0014: Явный state-контейнер для stream retry и разделение 429 policy

- Status: Accepted
- Date: 2026-03-03
- Related: унификация 429 rotation policy и stream state-контейнера (реализовано в runtime).

## Контекст

В stream контуре [`chat_completions()`](llm_agent_platform/api/openai/routes.py:1) и [`gemini_proxy()`](llm_agent_platform/api/gemini/routes.py:1) возникли скрытые мутации состояния при переключении аккаунтов в nested-функциях. Подход с неявным захватом переменных повышает риск ошибок области видимости и усложняет тестирование.

Параллельно принято архитектурное решение разделить класс `429` на семантические категории:
- `rate_limit`
- `quota_exhausted`
- `unknown_429`

и применять разные стратегии ротации аккаунтов.

## Решение

1. Использовать явный runtime state-контейнер для stream retry логики вместо неявных захватов переменных.
2. Все изменения токена, payload, selected_account и url делать через state-контейнер и helper-функции policy слоя.
3. Ввести единую 429 классификацию в transport-слое и единый policy path в роутерах.
4. Разделить реакцию в account-router:
   - `rate_limit`: порог + временный cooldown, без exhausted-метки
   - `quota_exhausted`: порог + exhausted-until по модели до reset time
5. Ошибку `all_accounts_exceed_quota` возвращать только при полном exhausted всех аккаунтов для текущей модели.

## Политика all-cooldown vs all-exhausted

Разделяем два terminal-state и фиксируем разный контракт ответа:

- `all_accounts_on_cooldown`
  - Условие: есть доступные аккаунты по модели, но все временно заблокированы из-за `rate_limit` cooldown окна.
  - Семантика: временное состояние, аккаунты автоматически становятся кандидатами после истечения cooldown.
  - Контракт: HTTP `429` с кодом `all_accounts_on_cooldown`.

- `all_accounts_exceed_quota`
  - Условие: все аккаунты по модели помечены как exhausted до модельного reset time.
  - Семантика: квазипостоянное состояние до reset window для модели.
  - Контракт: HTTP `429` с кодом `all_accounts_exceed_quota`.

Decision rule:
- Если одновременно нет активных аккаунтов и есть хотя бы один cooldown candidate, возвращаем `all_accounts_on_cooldown`.
- Если cooldown candidates нет и все аккаунты exhausted, возвращаем `all_accounts_exceed_quota`.

### Mapping decision rule

| Активные аккаунты | Есть cooldown candidates | Все exhausted | Результат |
| --- | --- | --- | --- |
| да | не важно | не важно | выбрать активный аккаунт и продолжить retry path |
| нет | да | не важно | `all_accounts_on_cooldown` |
| нет | нет | да | `all_accounts_exceed_quota` |
| нет | нет | нет | `all_accounts_on_cooldown` как безопасный transient fallback |

### Нормативный контракт 429

Нормативный формат payload для кодов `all_accounts_on_cooldown` и `all_accounts_exceed_quota` зафиксирован в contract-first артефакте:
- [`docs/contracts/api/openai/errors/429-error.schema.json`](docs/contracts/api/openai/errors/429-error.schema.json:1)

## Альтернативы

### A. Использовать nonlocal в nested stream функциях
- Плюсы: быстрый фикс
- Минусы: хрупкая область видимости, трудно сопровождать при расширении policy

### B. Хранить mutable state в dict без типизации
- Плюсы: проще внедрить
- Минусы: слабая читаемость, риск опечаток ключей, слабая проверяемость

## Последствия

### Позитивные
- Упрощается reasoning по состоянию retry и switch логике.
- Снижается риск `UnboundLocalError` и скрытых side-effect.
- Улучшается тестопригодность policy и router-state переходов.
- Поведение 429 становится детерминированным и наблюдаемым.

### Негативные
- Усложняется объем рефакторинга в stream/non-stream коде.
- Требуется расширение тестов на state-переходы и edge-cases cooldown/exhausted.

## Условия пересмотра

Пересмотреть решение при выполнении одного из условий:
- Введение отдельного orchestration слоя для retries вне роутеров.
- Переход на другую execution-модель стриминга, где state хранится централизованно вне request scope.
- Появление провайдеров с несовместимой моделью квот, требующих иной policy abstraction.

## Contract changes

- present
- Расширение provider-config полями `rotation_policy` и `model_quota_resets`.
- Новые semantics ответа при all-cooldown vs all-exhausted.

## Update (2026-03-16)
`model_quota_resets` меняет семантику (time-of-day → period `DD:HH:MM`) и вводится persisted account state. Это зафиксировано отдельным ADR:
- [`docs/adr/0018-quota-reset-periods-and-account-state.md`](docs/adr/0018-quota-reset-periods-and-account-state.md:1)
