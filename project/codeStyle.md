# Code Style

## Назначение

Этот файл фиксирует project-specific coding style и authoring conventions для `llm_agent_platform`.

Он дополняет technical baseline из `project/techContext.md`, но не подменяет architecture, contracts или testing documentation.

## Базовые правила

- Основной язык реализации - Python `3.13+`.
- HTTP/API runtime построен вокруг Flask и `httpx`.
- Package and environment workflow строятся вокруг `uv`.
- Containerized verification и local runtime используют Docker и Docker Compose.

## Язык в разных слоях

- Код, identifiers, docstrings, code comments и commit messages пиши на английском языке.
- Правила, skills и документацию проекта пиши на русском языке.
- Если для термина нет устойчивого русского аналога, используй общепринятый English term.

## Стиль Python-кода

- Предпочитай ясный, читаемый Python без лишней магии.
- Держи modules and functions компактными и с одной основной ответственностью.
- Избегай скрытых side effects и неявных глобальных зависимостей.
- Имена `modules`, `functions`, `variables` и field-like identifiers оформляй в `snake_case`.
- Имена `classes` оформляй в `PascalCase`.
- Public API, DTO-like models и integration boundaries должны иметь предсказуемые имена и не дрейфовать между слоями.

## Provider-centric naming

- Проектируй runtime сущности и naming с provider-centric точки зрения.
- Не предполагай, что `model_id` глобально уникален вне конкретного provider.
- Provider-local catalogs, groups, auth и quota semantics должны оставаться явными в именах и документации.
- OpenAI-compatible surface не должен размывать provider-specific boundaries внутри internal model.

## Docstrings

- Python docstrings оформляй в Google style как baseline convention.
- Module docstring используй как preferred place для suite-level metadata, если один test module реализует один suite.
- Test function docstring используй как preferred place для `Test case:` и `Requirement:` metadata, если test suite уже применяет traceability conventions из `docs/testing/traceability.md`.
- Structured testing metadata не заменяет обычный explanatory docstring, а дополняет его.

Пример module docstring:

```python
"""Provider OpenAI chat adapter tests.

Suite: TS-OPENAI-CONTRACT
"""
```

Пример test function docstring:

```python
def test_returns_429_when_quota_exhausted():
    """Returns 429 when provider quota is exhausted.

    Test case: TC-OPENAI-CONTRACT-003
    Requirement: REQ-OPENAI-012
    """
```

## Работа с документацией и кодом

- Если изменение затрагивает public behavior, contracts или long-lived architecture, сначала обновляй relevant `docs/` artifacts или делай это в том же change set.
- Temporary plans, research и execution notes должны жить в `tasks_descriptions/`, а не в `docs/`.
- Не дублируй glossary-like definitions в code-adjacent docs; используй канонические термины и архитектурные документы проекта.

## Тесты и качество

- Новое поведение должно сопровождаться релевантной проверкой на уровне component, contract или integration scope.
- Если меняется contract или observable behavior, синхронизируй tests и documentation вместе с кодом.
- Regression fixes должны сопровождаться проверкой сценария, который раньше ломался.

## Связанные файлы

- `project/techContext.md`
- `project/entry-points.md`
- `docs/testing/traceability.md`
- `docs/testing/test-map.md`
- `docs/providers/README.md`
- `docs/providers/openai-chatgpt.md`
- `docs/contracts/`
