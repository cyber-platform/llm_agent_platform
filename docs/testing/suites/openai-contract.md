# Suite: OpenAI stream/non-stream contract

## Scope
- Проверка ответа `/v1/chat/completions` в non-stream формате.
- Проверка SSE потока с `stream_options.include_usage=true`.
- Проверка маппинга upstream-ошибки в OpenAI error shape.

## Requirement Traceability
- Requirement: стабильный OpenAI-compatible контракт для Kilo Code.
- Task links: [`008-openai-stream-and-contract-tests.md`](tasks_descriptions/tasks/008-openai-stream-and-contract-tests.md), [`012-quota-cli-parity-and-kilo-openai-compat.md`](tasks_descriptions/tasks/012-quota-cli-parity-and-kilo-openai-compat.md)
- Script: [`test_openai_contract.py`](tests/test_openai_contract.py)

## Verification Command
- `uv run python -m unittest tests/test_openai_contract.py`

