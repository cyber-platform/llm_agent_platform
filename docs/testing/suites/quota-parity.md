# Suite: Quota transport parity

## Scope
- Проверка shape outbound quota payload (`model`, `project`, `user_prompt_id`, `request.session_id`, `request.contents`, `request.generationConfig`).
- Проверка unwrap SSE line (`response` envelope).
- Проверка отсутствия legacy `thoughtSignature` bypass в трансформации tool calls.

## Requirement Traceability
- Requirement: strict parity outbound к контракту `gemini-cli`.
- Canonical references:
  - Parity relay endpoint: [`api/parity/routes.py`](api/parity/routes.py:1)
  - Test map: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- Scripts:
  - [`test_quota_transport_parity.py`](tests/test_quota_transport_parity.py)
  - [`golden_cli_generate_request.json`](tests/fixtures/parity/golden_cli_generate_request.json)
  - [`golden_cli_stream_request.json`](tests/fixtures/parity/golden_cli_stream_request.json)

## Verification Command
- `uv run python -m unittest tests/test_quota_transport_parity.py`
