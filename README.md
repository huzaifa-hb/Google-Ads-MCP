# Google Ads MCP

Private, Cloud Run-ready, write-capable Model Context Protocol server for Google Ads API access.

This server exposes Google Ads in three layers:

1. Generic API tools for GAQL, streaming GAQL, arbitrary mutate operations, and arbitrary service calls.
2. Generated/friendly tool names for account, campaign, budget, ad group, ads, keywords, negatives, assets, audiences, conversions, reports, recommendations, planning, and bulk workflows.
3. Explicit capability responses for API features that are unavailable, deprecated, or eligibility-gated.

The MCP endpoint is `POST /mcp`. Health checks are available at `GET /healthz`.

## Security Model

This is designed as a private single-owner endpoint:

- Google Ads access uses one OAuth2 refresh token and one developer token.
- MCP access is protected by a bearer token.
- All secrets are read from environment variables or GCP Secret Manager.
- Default mode is `safe_read_only`, which does not expose mutation or generic service bridge tools.
- `validation_only` exposes configured write tools but forces `validate_only=true`.
- Real writes require `GOOGLE_ADS_MCP_MODE=write_enabled` or `admin_debug`, `execute=true`, `validate_only=false`, and `confirmation_phrase="CONFIRM_GOOGLE_ADS_WRITE"`.
- Every write attempt emits a structured audit event with a hashed customer ID.

Never commit `.env`, OAuth JSON files, refresh tokens, customer data, invoices, or uploaded audience files.

See `docs/modes-and-safety.md` and `docs/tool-configuration.md` for copy-paste mode and tool exposure examples.
See `docs/live-metadata-and-gaql-planning.md` for read-only GAQL planning
examples.
See `docs/capability-matrix.md` for implementation status, backend routing,
read/write class, and eligibility notes.

## Tool Exposure

Tools are registered from `tools_config.yaml` and are namespaced by default:

- `metadata_query_google_ads_docs`
- `metadata_describe_google_ads_resource`
- `metadata_get_google_ads_resource_metadata`
- `metadata_validate_gaql_fields`
- `metadata_suggest_gaql_fields`
- `planning_plan_gaql_query`
- `planning_explain_gaql_error`
- `reporting_get_campaign_metrics`
- `campaigns_list_campaigns`
- `keywords_list_keywords`
- `get_tool_catalog`
- `get_capability_matrix`

`get_tool_catalog` returns the currently exposed tool set, including registered name, canonical name, namespace, read/write class, and mode.

Legacy unprefixed aliases, such as `pause_campaign`, are registered only when `legacy_aliases.enabled=true` in the tools config. Generic bridge tools such as `google_ads_mutate` and `google_ads_call_service` are hidden unless explicitly configured and allowed by mode.

Use `metadata_get_google_ads_resource_metadata` before writing raw GAQL. It uses
GoogleAdsFieldService to return selectable resource fields plus compatible
metrics and segments. Use `planning_plan_gaql_query` to build a validated query
without executing it, then run the query with a read-only search tool.

`metadata_query_google_ads_docs` is an offline knowledge base with working
examples, common API errors, and field-combination caveats.

The friendly tools are generated from `src/google_ads_mcp/tool_catalog.py`; see
`docs/tool-catalog.md`. The GAQL knowledge base is generated from
`src/google_ads_mcp/knowledge_base.py`; see `docs/gaql-knowledge-base.md`.

## MCP Resources

Read-only resources are exposed for clients that support MCP resources:

- `resource://google-ads/discovery-document`
- `resource://google-ads/metrics`
- `resource://google-ads/segments`
- `resource://google-ads/release-notes`
- `resource://google-ads/tool-catalog`
- `resource://google-ads/capability-matrix`
- `resource://google-ads/gaql-knowledge-base`

For a full clone-to-Cloud-Run setup, including Google Ads developer token,
OAuth test users, refresh-token generation, GCP secrets, deployment, and agent
connection examples, see `docs/owner-setup-guide.md`.

## Local Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Fill `.env` locally, or set environment variables directly:

- `MCP_BEARER_TOKEN`
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- optional `GOOGLE_ADS_LOGIN_CUSTOMER_ID`
- optional `GOOGLE_ADS_API_VERSION`, default `v24`
- optional `GOOGLE_ADS_MCP_MODE`, default `safe_read_only`
- optional `GOOGLE_ADS_MCP_TOOLS_CONFIG`, explicit path to a tools config
- optional `GOOGLE_ADS_MCP_AUTH_MODE`, default `bearer`

Start the server:

```powershell
python -m google_ads_mcp
```

The endpoint is:

```text
http://localhost:8080/mcp
```

Run tests from a fresh checkout:

```powershell
python -m unittest discover -s tests
```

The tests bootstrap the local `src/` path through `tests/_bootstrap.py`, so the
command works before `pip install -e ".[dev]"`. Installing editable mode is still
recommended for normal development because it also installs runtime and dev
dependencies.

Run the full CI-equivalent local checks:

```powershell
python -m compileall src scripts tests
python -m unittest discover -s tests
python scripts/check_generated_docs.py
python scripts/scan_for_secrets.py
```

## Auth Modes

Bearer auth is the private-owner default. Optional OAuth proxy mode is available
for clients that require OAuth instead of static bearer headers. See
`docs/oauth-front-door.md`.

## Cloud Run Deployment

For the complete version, use `docs/owner-setup-guide.md`. The short version is:

Create Secret Manager values first:

```powershell
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name MCP_BEARER_TOKEN
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_DEVELOPER_TOKEN
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_CLIENT_ID
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_CLIENT_SECRET
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_REFRESH_TOKEN
```

Create `GOOGLE_ADS_LOGIN_CUSTOMER_ID` only if you route through an MCC manager
account.

Then deploy:

```powershell
.\deploy\cloud-run.ps1 -ProjectId YOUR_GCP_PROJECT_ID
```

The service is deployed with public ingress but app-level bearer token protection. That makes it attachable by external AI agents that can send an `Authorization` header.
Do not set `ALLOW_UNAUTHENTICATED_MCP=true` on a production Cloud Run endpoint.

## Write Example

Writes are unavailable in the default `safe_read_only` mode. To preview a write, set:

```powershell
$env:GOOGLE_ADS_MCP_MODE = "validation_only"
```

Validation-only campaign pause:

```json
{
  "customer_id": "1234567890",
  "payload": { "campaign_id": "1111111111" },
  "validate_only": true
}
```

Real write:

```powershell
$env:GOOGLE_ADS_MCP_MODE = "write_enabled"
```

```json
{
  "customer_id": "1234567890",
  "payload": { "campaign_id": "1111111111" },
  "validate_only": false,
  "execute": true,
  "confirmation_phrase": "CONFIRM_GOOGLE_ADS_WRITE"
}
```

Complex campaign types such as Performance Max use `payload.operations` in Google Ads `MutateOperation` protobuf JSON shape. Use `metadata_validate_google_ads_payload` before executing large batches when that metadata namespace tool is exposed.

## Reporting Dates

Reporting tools accept either:

- `date_range`: `TODAY`, `YESTERDAY`, `LAST_7_DAYS`, `LAST_14_DAYS`, `LAST_30_DAYS`, `LAST_90_DAYS`, `THIS_MONTH`, `LAST_MONTH`, `ALL_TIME`
- `start_date` and `end_date` in `YYYY-MM-DD`

Pagination supports `page_size`, `offset`, and `page_token`.

## GAQL Planning

Plan a campaign query without executing it:

```json
{
  "resource_name": "campaign",
  "user_goal": "campaign clicks and cost for the last week",
  "fields": ["campaign.name"],
  "metrics": ["metrics.clicks", "metrics.cost_micros"],
  "filters": { "campaign.status": "ENABLED" },
  "date_range": "LAST_7_DAYS"
}
```

The planner validates fields against live metadata, adds `campaign.id` when
available, and returns `not_executed=true`.

## Limitations

The generic bridge can call any service and method exposed by the installed Google Ads client. Friendly tools return an `unsupported_capability` response if Google does not expose the requested feature, the feature is deprecated, or the account requires special eligibility.

Quota behavior depends on your developer-token access level and service-specific Google limits; this server does not hardcode a universal daily operation limit.
