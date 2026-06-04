# Google Ads MCP

Cloud Run-ready Model Context Protocol server for Google Ads API access.

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
- All writes default to validation mode.
- Real writes require `execute=true` and `confirmation_phrase="CONFIRM_GOOGLE_ADS_WRITE"`.

Never commit `.env`, OAuth JSON files, refresh tokens, customer data, invoices, or uploaded audience files.

## Core Tools

- `google_ads_search`
- `google_ads_search_stream`
- `google_ads_mutate`
- `google_ads_call_service`
- `list_google_ads_services`
- `describe_google_ads_service`
- `describe_google_ads_resource`
- `query_google_ads_docs`
- `validate_google_ads_payload`
- `get_tool_catalog`

Use `query_google_ads_docs` before writing raw GAQL. It is an offline knowledge
base with working examples, common API errors, and field-combination caveats.

The friendly tools are generated from `src/google_ads_mcp/tool_catalog.py`; see
`docs/tool-catalog.md`. The GAQL knowledge base is generated from
`src/google_ads_mcp/knowledge_base.py`; see `docs/gaql-knowledge-base.md`.

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

## Write Example

Validation-only campaign pause:

```json
{
  "customer_id": "1234567890",
  "payload": { "campaign_id": "1111111111" },
  "validate_only": true
}
```

Real write:

```json
{
  "customer_id": "1234567890",
  "payload": { "campaign_id": "1111111111" },
  "validate_only": false,
  "execute": true,
  "confirmation_phrase": "CONFIRM_GOOGLE_ADS_WRITE"
}
```

Complex campaign types such as Performance Max use `payload.operations` in Google Ads `MutateOperation` protobuf JSON shape. Use `validate_google_ads_payload` before executing large batches.

## Reporting Dates

Reporting tools accept either:

- `date_range`: `TODAY`, `YESTERDAY`, `LAST_7_DAYS`, `LAST_14_DAYS`, `LAST_30_DAYS`, `LAST_90_DAYS`, `THIS_MONTH`, `LAST_MONTH`, `ALL_TIME`
- `start_date` and `end_date` in `YYYY-MM-DD`

Pagination supports `page_size`, `offset`, and `page_token`.

## Limitations

The generic bridge can call any service and method exposed by the installed Google Ads client. Friendly tools return an `unsupported_capability` response if Google does not expose the requested feature, the feature is deprecated, or the account requires special eligibility.

Quota behavior depends on your developer-token access level and service-specific Google limits; this server does not hardcode a universal daily operation limit.
