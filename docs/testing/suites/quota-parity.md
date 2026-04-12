# Suite: Quota transport parity

## Suite ID
- `TS-QUOTA-PARITY`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/quota-parity.md`

## Implementation roots
- `services/backend/llm_agent_platform/tests/test_quota_transport_parity.py`
- `services/backend/llm_agent_platform/tests/fixtures/parity/`

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
  - Parity relay endpoint: [`services/backend/llm_agent_platform/api/parity/routes.py`](services/backend/llm_agent_platform/api/parity/routes.py:1)
  - Test map: [`docs/testing/test-map.md`](docs/testing/test-map.md:1)
- Scripts:
  - [`services/backend/llm_agent_platform/tests/test_quota_transport_parity.py`](services/backend/llm_agent_platform/tests/test_quota_transport_parity.py:1)
  - [`services/backend/llm_agent_platform/tests/fixtures/parity/golden_cli_generate_request.json`](services/backend/llm_agent_platform/tests/fixtures/parity/golden_cli_generate_request.json:1)
  - [`services/backend/llm_agent_platform/tests/fixtures/parity/golden_cli_stream_request.json`](services/backend/llm_agent_platform/tests/fixtures/parity/golden_cli_stream_request.json:1)

## Verification Command
- `cd services/backend && uv run python -m unittest llm_agent_platform/tests/test_quota_transport_parity.py`
