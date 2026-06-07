# Deployment Notes

For the full owner setup, including Google Ads developer token, OAuth consent,
test users, refresh-token generation, Secret Manager, Cloud Run, and agent
connection examples, see `docs/owner-setup-guide.md`.

## Required GCP APIs

- Cloud Run
- Cloud Build
- Artifact Registry
- Secret Manager
- Google Ads API

The deployment script enables these APIs.

## Secret Manager

Required secrets:

- `MCP_BEARER_TOKEN`
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_ID`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`

Optional:

- `GOOGLE_ADS_LOGIN_CUSTOMER_ID`

The deploy script includes the optional login customer secret only when that
secret exists in Secret Manager.

Optional runtime environment values:

- `GOOGLE_ADS_AUDIT_LOG_PATH`
- `GOOGLE_ADS_METADATA_CACHE_TTL_SECONDS`
- `GOOGLE_ADS_METADATA_CACHE_MAX_ENTRIES`
- `GOOGLE_ADS_METADATA_SNAPSHOT_PATH`

Use `scripts/set_gcp_secret.ps1` to create or rotate secrets without trailing
newlines:

```powershell
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name MCP_BEARER_TOKEN
```

Do not paste secrets into interactive `gcloud --data-file=-` stdin unless you
know how to avoid storing a trailing newline.

## Secret Access IAM

The Cloud Run runtime service account needs `roles/secretmanager.secretAccessor`
to read secrets injected with `--set-secrets`. The deploy script grants this role
to the default compute service account and waits for IAM propagation. If you
deploy manually, grant the same role before deploying.

## Cloud Run Defaults

- Service: `google-ads-mcp`
- Region: `us-central1`
- Artifact Registry repository: `mcp-servers`
- Port: `8080`
- MCP path: `/mcp`
- Health path: `/healthz`
- Readiness path: `/readyz`
- MCP mode: `safe_read_only`
- MCP auth mode: `bearer`
- Generic service bridge escape hatch: disabled

Cloud Run is configured with public ingress because most external AI agents cannot mint Google IAM identity tokens. The MCP server still requires its own bearer token.

Cloud Run may scale to zero after idle time. The first request after idle can
take 5 to 15 seconds; later requests are normally faster.

`GOOGLE_ADS_MAX_RETRIES` counts retries after the first attempt, so a value of
`3` allows one initial call plus up to three retries.

Override safety settings deliberately:

```powershell
.\deploy\cloud-run.ps1 `
  -ProjectId YOUR_GCP_PROJECT_ID `
  -McpMode validation_only
```

Only use `-EnableGenericServiceBridge` for private `admin_debug` deployments.

## Post-Deploy Checks

```powershell
$url = gcloud run services describe google-ads-mcp --region us-central1 --format "value(status.url)"
Invoke-WebRequest "$url/healthz"
Invoke-WebRequest "$url/readyz"
```

Then attach an MCP client to:

```text
$url/mcp
```

with:

```text
Authorization: Bearer <MCP_BEARER_TOKEN>
```
