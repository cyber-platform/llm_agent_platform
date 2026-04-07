# Suite: Quota transport parity

## Suite ID
- `TS-QUOTA-PARITY`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/quota-parity.md`

## Implementation roots
- `llm_agent_platform/tests/test_quota_transport_parity.py`
- `llm_agent_platform/tests/fixtures/parity/`

## Search anchors
- `TS-QUOTA-PARITY`
- `test_quota_transport_parity.py`
- `golden_cli_`
- `parity`

## Scope
- Проверка shape outbound quota payload (`model`, `project`, `user_prompt_id`, `request.session_id`, `request.contents`, `request.generationConfig`).
- Проверка unwrap SSE line (`response` envelope).
- Проверка отсутствия legacy `thoughtSignature` bypass в трансформации tool calls.

## Requirement Traceability
- Requirement: strict parity outbound к контракту `gemini-cli`.
- Rollout metadata:
  - suite anchor: `TS-QUOTA-PARITY`
  - future case anchors: `TC-QUOTA-PARITY-...`
- Canonical references:
  - Parity relay endpoint: [`llm_agent_platform/api/parity/routes.py`](llm_agent_platform/api/parity/routes.py:1)
  - Test map: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- Scripts:
  - [`llm_agent_platform/tests/test_quota_transport_parity.py`](llm_agent_platform/tests/test_quota_transport_parity.py:1)
  - [`llm_agent_platform/tests/fixtures/parity/golden_cli_generate_request.json`](llm_agent_platform/tests/fixtures/parity/golden_cli_generate_request.json:1)
  - [`llm_agent_platform/tests/fixtures/parity/golden_cli_stream_request.json`](llm_agent_platform/tests/fixtures/parity/golden_cli_stream_request.json:1)

## Verification Command
- `uv run python -m unittest llm_agent_platform/tests/test_quota_transport_parity.py`
