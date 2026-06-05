# Google Ads MCP

[![CI](https://github.com/huzaifa-hb/Google-Ads-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/huzaifa-hb/Google-Ads-MCP/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Private, Cloud Run-ready, write-capable Google Ads MCP for advanced advertisers,
agencies, and internal automation agents.

The core idea is simple: give agents broad Google Ads coverage, but make the
default posture safe. The server starts in read-only mode, exposes only the tools
allowed by `tools_config.yaml`, validates GAQL with live Google Ads metadata, and
requires an explicit confirmation gate for any real write.

## Why This Exists

The official Google Ads MCP is the safer baseline for trusted read-only
reporting and metadata discovery. This repo is for private operational workflows
that need broader coverage and controlled write paths:

- account, campaign, budget, ad group, ad, keyword, negative, asset, audience,
  conversion, recommendation, reporting, planning, and bulk workflows
- validation-first mutation tools
- live GoogleAdsFieldService metadata and GAQL planning
- configurable tool exposure by namespace and individual tool
- private Cloud Run deployment with bearer auth by default
- optional OAuth proxy front door for clients that require OAuth

See [docs/comparison.md](docs/comparison.md) for the positioning against the
official read-only server.

## Safety Defaults

| Mode | Exposed Tools | Real Writes |
|---|---|---|
| `safe_read_only` | read, reporting, docs, metadata, planning | impossible |
| `validation_only` | configured writes plus read tools | impossible, forced `validate_only=true` |
| `write_enabled` | configured writes plus read tools | requires confirmation |
| `admin_debug` | can expose generic bridges | requires confirmation |

Real writes require all of these:

- `GOOGLE_ADS_MCP_MODE=write_enabled` or `admin_debug`
- `validate_only=false`
- `execute=true`
- `confirmation_phrase="CONFIRM_GOOGLE_ADS_WRITE"`

Generic bridge tools are hidden by default. `google_ads_call_service` now uses a
read-method allowlist and denies unknown service methods unless they are routed
through the write guard or the server is explicitly in `admin_debug` with
`GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE=true`.

Never expose a production endpoint with `ALLOW_UNAUTHENTICATED_MCP=true`.
Never commit `.env`, OAuth JSON files, refresh tokens, developer tokens, bearer
tokens, customer data, invoices, or audience upload files.

## Main Features

- **Configurable tool surface:** `tools_config.yaml` controls mode, namespaces,
  prefixes, legacy aliases, and individual tool enablement.
- **Live metadata:** `metadata_get_google_ads_resource_metadata` returns
  selectable/filterable/sortable fields plus compatible metrics and segments.
- **GAQL planning:** `planning_plan_gaql_query` validates fields and returns a
  query plan without executing it.
- **Capability matrix:** `get_capability_matrix` and
  [docs/capability-matrix.md](docs/capability-matrix.md) show backend routing,
  read/write class, eligibility notes, and implementation status.
- **Write auditability:** every write attempt emits a structured JSON audit event
  with hashed customer ID and no raw payloads.
- **MCP resources:** read-only reference resources are exposed for clients that
  support MCP resources.
- **CI hygiene:** unit tests, compile checks, generated-doc checks, and secret
  scanning run in GitHub Actions.

## Safe First 10 Minutes

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
```

Set local values in `.env`, then start in safe mode:

```powershell
$env:GOOGLE_ADS_MCP_MODE = "safe_read_only"
python -m google_ads_mcp
```

First MCP calls:

```text
get_server_status
get_tool_catalog
get_capability_matrix
metadata_get_google_ads_resource_metadata(resource_name="campaign")
planning_plan_gaql_query(resource_name="campaign", metrics=["metrics.clicks"])
```

The endpoint is:

```text
http://localhost:8080/mcp
```

Health check:

```text
GET http://localhost:8080/healthz
```

## Configuration

Important environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `MCP_BEARER_TOKEN` | none | private MCP bearer token |
| `GOOGLE_ADS_MCP_MODE` | `safe_read_only` | safety/exposure mode |
| `GOOGLE_ADS_MCP_TOOLS_CONFIG` | none | explicit config path |
| `GOOGLE_ADS_MCP_AUTH_MODE` | `bearer` | `bearer` or `oauth_proxy` |
| `GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE` | `false` | dangerous admin-debug bridge escape hatch |
| `GOOGLE_ADS_API_VERSION` | `v24` | Google Ads API version |

Google Ads credentials are still required for live API calls:

- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- optional `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

See [docs/tool-configuration.md](docs/tool-configuration.md),
[docs/modes-and-safety.md](docs/modes-and-safety.md), and
[docs/oauth-front-door.md](docs/oauth-front-door.md).

## Tool Exposure

Tools are namespaced by default:

- `metadata_get_google_ads_resource_metadata`
- `metadata_validate_gaql_fields`
- `metadata_suggest_gaql_fields`
- `planning_plan_gaql_query`
- `planning_explain_gaql_error`
- `reporting_get_campaign_metrics`
- `campaigns_list_campaigns`
- `keywords_list_keywords`

Stable unprefixed introspection tools:

- `get_server_status`
- `get_tool_catalog`
- `get_capability_matrix`

Legacy unprefixed aliases, such as `pause_campaign`, are registered only when
`legacy_aliases.enabled=true`.

## MCP Resources

Read-only resources:

- `resource://google-ads/reference-index`
- `resource://google-ads/discovery-document` compatibility alias
- `resource://google-ads/metrics`
- `resource://google-ads/segments`
- `resource://google-ads/release-notes-index`
- `resource://google-ads/release-notes` compatibility alias
- `resource://google-ads/tool-catalog`
- `resource://google-ads/capability-matrix`
- `resource://google-ads/gaql-knowledge-base`

The reference and release-note resources are indexes/links by design, not full
network-synced snapshots.

## Cloud Run

Use [docs/owner-setup-guide.md](docs/owner-setup-guide.md) for the complete
clone-to-Cloud-Run guide. Short version:

```powershell
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name MCP_BEARER_TOKEN
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_DEVELOPER_TOKEN
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_CLIENT_ID
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_CLIENT_SECRET
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_REFRESH_TOKEN
.\deploy\cloud-run.ps1 -ProjectId YOUR_GCP_PROJECT_ID
```

The Cloud Run service may use public ingress only because app-level bearer or
OAuth auth remains required. Do not deploy unauthenticated access to a real ad
account.

## Validation-Only Write Example

```powershell
$env:GOOGLE_ADS_MCP_MODE = "validation_only"
```

```json
{
  "customer_id": "1234567890",
  "payload": { "campaign_id": "1111111111" },
  "validate_only": true,
  "execute": false
}
```

## Confirmed Real Write Example

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

## Local Checks

```powershell
python -m compileall src scripts tests
python -m unittest discover -s tests
python scripts/check_generated_docs.py
python scripts/scan_for_secrets.py
```

Optional live tests are skipped by default:

```powershell
$env:GOOGLE_ADS_MCP_RUN_INTEGRATION_TESTS = "true"
python -m unittest tests.test_integration_google_ads
```

## Docs Map

- [Capability matrix](docs/capability-matrix.md)
- [Modes and safety](docs/modes-and-safety.md)
- [Tool configuration](docs/tool-configuration.md)
- [Live metadata and GAQL planning](docs/live-metadata-and-gaql-planning.md)
- [OAuth front door](docs/oauth-front-door.md)
- [Sample prompts](docs/sample-prompts.md)
- [Client configuration](docs/clients.md)
- [Owner setup guide](docs/owner-setup-guide.md)
- [Security](SECURITY.md)
- [Contributing](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
