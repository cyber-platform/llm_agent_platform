# Suite: OpenAI ChatGPT PoC smoke

## Suite ID
- `TS-OPENAI-CHATGPT-POC-SMOKE`

## Documentation roots
- `docs/testing/test-map.md`
- `docs/testing/traceability.md`
- `docs/testing/suites/openai-chatgpt-poc-smoke.md`

## Implementation roots
- `llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py`
- `services/frontend/package.json`
- `services/frontend/config/dev-server.json`
- `services/frontend/public/runtime-config.json`
- `docker-compose.yml`

## Search anchors
- `TS-OPENAI-CHATGPT-POC-SMOKE`
- `test_openai_chatgpt_poc_smoke.py`
- `openai chatgpt poc smoke`
- `demo smoke`

## Scope
- Проверка критического demo path: admin `create key` -> public `models` -> public `chat/completions` -> `revoke` -> `401 invalid_api_key`.
- Проверка schema-critical полей `openai-chatgpt` monitoring page и `Activate` response, от которых зависит React PoC UI.
- Проверка checked-in delivery boundary: frontend и backend публикуются только на localhost, public namespace ограничен `/openai-chatgpt`, admin path остается `/admin`.
- Frontend browser-test contour отсутствует; вместо него suite фиксирует обязательный build smoke `npm run build` в `services/frontend`.

## Requirement Traceability
- Requirement: task 047 завершает `openai-chatgpt` PoC финальным verification contour и doc sync.
- Rollout metadata:
  - suite anchor: `TS-OPENAI-CHATGPT-POC-SMOKE`
  - case anchors: `TC-OPENAI-CHATGPT-POC-SMOKE-001..003`
- Canonical references:
  - [`docs/providers/openai-chatgpt.md`](docs/providers/openai-chatgpt.md:1)
  - [`docs/architecture/admin-monitoring-read-model.md`](docs/architecture/admin-monitoring-read-model.md:1)
  - [`docs/architecture/web-ui.md`](docs/architecture/web-ui.md:1)
  - [`docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-accounts-page.schema.json:1)
  - [`docs/contracts/api/admin/monitoring/openai-chatgpt-activate-account-response.schema.json`](docs/contracts/api/admin/monitoring/openai-chatgpt-activate-account-response.schema.json:1)
  - [`docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json`](docs/contracts/api/openai/errors/401-invalid-api-key-error.schema.json:1)

## Verification Command
- `uv run python -m unittest llm_agent_platform/tests/test_openai_chatgpt_poc_smoke.py`
- `npm run build`

## Demo Checklist
- Создать platform API key через `POST /admin/api-keys/openai-chatgpt` или через локальный frontend.
- Подтвердить `GET /openai-chatgpt/v1/models` с Bearer key и наличие `gpt-5.4` в ответе.
- Выполнить `POST /openai-chatgpt/v1/chat/completions` и подтвердить успешный non-stream ответ.
- Открыть локальный frontend, проверить monitoring page, `Activate`, manual refresh banner и key list/revoke flow.
- Отозвать ключ и перепроверить public route: ожидается `401 invalid_api_key`.
- Для delivery boundary убедиться, что внешний demo URL публикует только `/openai-chatgpt/*`, а `/admin/*` и frontend остаются локальными.

## Status
- active
