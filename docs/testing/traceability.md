# Testing Traceability

## Purpose
- Этот файл фиксирует текущие traceability conventions для testing layer проекта.
- Markdown остается Source of Truth; будущий graph storage будет производным representation поверх `docs/testing/` и code metadata.

## Target Traceability Chain
- Целевая модель: `requirement -> suite -> test case -> test implementation`.
- Текущее состояние rollout:
  - suite-level IDs уже каноничны;
  - test-case-level IDs вводятся постепенно;
  - существующие legacy case labels могут сохраняться до следующего обновления suite.

## Identifier Families
- `REQ-<AREA>-<NNN>` для requirement IDs, когда suite уже использует нормализованные requirement identifiers.
- `TS-<AREA>-<SUITE>` для suite IDs.
- `TC-<AREA>-<SUITE>-<NNN>` для test case IDs.

## Code Metadata Keys
- Module-level suite metadata:

```python
"""Provider OpenAI chat adapter tests.

Suite: TS-OPENAI-CONTRACT
"""
```

- Function-level test metadata:

```python
def test_returns_429_when_quota_exhausted():
    """Returns 429 when provider quota is exhausted.

    Test case: TC-OPENAI-CONTRACT-003
    Requirement: REQ-OPENAI-012
    """
```

## Search Policy
- Если агенту нужна test documentation, search должен начинаться в `docs/testing/`.
- Если агенту нужна code implementation, search должен начинаться с `Implementation roots`, указанных в нужной suite page.
- Если агенту нужен конкретный identifier, search нужно делать по stable anchors:
  - `TS-...`
  - `TC-...`
  - `REQ-...`

## Suite Page Responsibilities
- Каждая suite page должна задавать:
  - `Suite ID`
  - `Documentation roots`
  - `Implementation roots`
  - `Search anchors`
- Suite pages остаются canonical navigation entry для конкретного suite.

## Related Files
- `docs/testing/test-map.md`
- `docs/testing/suites/`
