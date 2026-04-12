# Service Behavior Config

## Назначение

Этот документ фиксирует boundary для operational behavior config, который не относится к secrets layer.

`Service behavior config` хранит настройки выполнения сервиса, polling cadence, timeout policy и UI/runtime behavior hints.

## Separation of concerns

Каноническое разделение:

- `.env` / `.env.oauth` — secrets, credentials, environment-provided endpoints и sensitive runtime values;
- service behavior config file — non-secret operational behavior и tuning values.

Это разделение особенно важно для monitoring refresh subsystem.

## Backend service config

Для backend monitoring refresh subsystem canonical config layer должна содержать non-secret execution settings.

Канонический контракт:

- [`docs/contracts/config/service-behavior-config.schema.json`](docs/contracts/config/service-behavior-config.schema.json:1)
- Example: [`docs/examples/service_behavior_config.example.yaml`](docs/examples/service_behavior_config.example.yaml:1)

Recommended shape:

```yaml
monitoring:
  background_poll_interval_seconds: 10
  refresh_concurrency: 5
  per_account_refresh_timeout_seconds: 10
  refresh_run_timeout_seconds: 60
  refresh_run_retention_seconds: 300
```

### Semantics

- `background_poll_interval_seconds` — cadence provider-wide background refresh poller;
- `refresh_concurrency` — bounded concurrency for account refresh tasks;
- `per_account_refresh_timeout_seconds` — timeout for one provider usage refresh task;
- `refresh_run_timeout_seconds` — upper bound for one manual refresh run;
- `refresh_run_retention_seconds` — how long completed refresh runs remain queryable in memory.

### Current PoC defaults

- `background_poll_interval_seconds = 10`
- `refresh_concurrency = 5`
- `per_account_refresh_timeout_seconds = 10`
- `refresh_run_timeout_seconds = 60`
- `refresh_run_retention_seconds = 300`

## Frontend runtime config

Frontend runtime settings остаются отдельными от backend service config.

Для current PoC operator UI canonical runtime config file содержит такие значения:

```json
{
  "pageTitle": "OpenAI ChatGPT PoC Console",
  "providerId": "openai-chatgpt",
  "adminApiBasePath": "/admin",
  "publicApiBasePath": "/openai-chatgpt",
  "refreshIntervalMs": 10000
}
```

### Frontend semantics

- `refreshIntervalMs` — обычный page polling interval для provider page;
- manual refresh short polling cadence не обязана жить в том же файле и может быть hardcoded в UI до появления cross-provider reuse need.

Если проект позже захочет свести frontend runtime config и backend service behavior config к единому generated contract, это должно быть отдельным architectural step, а не implicit coupling через одинаковые defaults.

## Policy

- service behavior config не должен использоваться для secrets;
- `.env` не должен становиться storage for non-secret tuning values, если они являются частью durable operational behavior;
- frontend и backend config files остаются раздельными, даже если их defaults согласованы по UX.

## Related documents

- [`docs/configuration/env-files.md`](docs/configuration/env-files.md:1)
- [`docs/contracts/config/service-behavior-config.schema.json`](docs/contracts/config/service-behavior-config.schema.json:1)
- [`docs/architecture/admin-monitoring-refresh-subsystem.md`](docs/architecture/admin-monitoring-refresh-subsystem.md:1)
- [`docs/architecture/web-ui.md`](docs/architecture/web-ui.md:1)
