# Modes And Safety

Google Ads MCP defaults to `safe_read_only`. That is the right mode for audits,
diagnostics, reporting, and first-time setup.

## Modes

| Mode | What is exposed | Real writes |
|---|---|---|
| `safe_read_only` | Read, reporting, docs, and metadata tools | Impossible |
| `validation_only` | Configured mutation tools plus read tools | Impossible; forced `validate_only=true` |
| `write_enabled` | Configured write tools plus read tools | Allowed only with confirmation |
| `admin_debug` | Configured generic bridge tools can be exposed | Allowed only with confirmation |

Modes do not choose the tool catalog by themselves. `write_enabled` only opens
the gate for write tools that are already exposed by a tool profile or explicit
tool config.

Set the mode with:

```powershell
$env:GOOGLE_ADS_MCP_MODE = "safe_read_only"
```

## Validation Preview

Use this when you want agents to build or validate write payloads without any
chance of committing spend-impacting changes:

```powershell
$env:GOOGLE_ADS_MCP_MODE = "validation_only"
python -m google_ads_mcp
```

Even if a request sends `execute=true` and `validate_only=false`, the server
forces `validate_only=true`.

## Safe Query Planning

The default `safe_read_only` mode exposes live metadata and GAQL planning tools:

- `metadata_get_google_ads_resource_metadata`
- `metadata_validate_gaql_fields`
- `metadata_suggest_gaql_fields`
- `planning_plan_gaql_query`
- `planning_explain_gaql_error`

Use these before running broad reports. They help avoid invalid fields,
missing primary resource fields, and incompatible metric or segment choices
without creating or changing anything in Google Ads.

## Real Writes

Use this only for a private endpoint protected by a strong bearer token:

```powershell
$env:GOOGLE_ADS_MCP_MODE = "write_enabled"
$env:GOOGLE_ADS_MCP_TOOL_PROFILE = "agency_write"
python -m google_ads_mcp
```

Use `advanced_mutate` instead of `agency_write` only when you deliberately want
to expose `generic_google_ads_mutate`.

Real writes still require all three request values:

```json
{
  "validate_only": false,
  "execute": true,
  "confirmation_phrase": "CONFIRM_GOOGLE_ADS_WRITE"
}
```

## Audit Events

Every write attempt logs a JSON audit event with:

- mode
- tool name
- operation type and count
- validate-only and execute flags
- result: `denied`, `validated`, or `authorized`
- hashed customer ID

Audit events do not include raw payloads, secrets, audience upload data, invoice
files, or raw customer data.

By default, audit events go to the `google_ads_mcp.audit` logger. For production,
set `GOOGLE_ADS_AUDIT_LOG_PATH` to append the same redacted events to a JSONL
file:

```env
GOOGLE_ADS_AUDIT_LOG_PATH=/var/log/google-ads-mcp/write-audit.jsonl
```

## Production Warning

Do not expose a production Cloud Run endpoint with
`ALLOW_UNAUTHENTICATED_MCP=true`. Public ingress is acceptable only when the MCP
bearer token remains required and secret values are injected from Secret Manager.
