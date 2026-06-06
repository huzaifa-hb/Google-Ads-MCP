# Owner Setup Guide: Host Your Own Google Ads MCP

Last reviewed: 2026-06-05.

This guide is for a private owner deployment where you clone this repo, connect
your own Google Ads access, deploy to Cloud Run, and attach the MCP URL to AI
agents. It is not a SaaS multi-tenant OAuth guide.

## What You Are Building

The final setup has these runtime values:

| Credential | Where it comes from | What it does |
|---|---|---|
| `GOOGLE_ADS_DEVELOPER_TOKEN` | Google Ads manager account API Center | Identifies your app to Google Ads API |
| `GOOGLE_ADS_CLIENT_ID` | Google Cloud OAuth client | Identifies your OAuth app |
| `GOOGLE_ADS_CLIENT_SECRET` | Google Cloud OAuth client | Used with the refresh token |
| `GOOGLE_ADS_REFRESH_TOKEN` | One-time OAuth consent by a Google user | Authorizes access to the ad accounts that user can access |
| `GOOGLE_ADS_LOGIN_CUSTOMER_ID` | Optional Google Ads manager account ID | Lets the API route through your MCC |
| `MCP_BEARER_TOKEN` | You generate it | Protects your Cloud Run MCP endpoint |

The developer token and OAuth token are separate. A developer token alone does
not grant account access. An OAuth token alone cannot call Google Ads API.

## Before You Start

You need:

- A Google account with access to the Google Ads account you want to manage.
- A Google Ads manager account if you need a developer token or MCC hierarchy.
- A Google Cloud project with billing enabled.
- Google Cloud CLI installed and authenticated.
- Python 3.12 or newer.
- Git.
- PowerShell. The examples use PowerShell because this repo's deploy helper is
  a PowerShell script.

Use a leaf Google Ads customer ID for reporting and writes. Customer IDs are 10
digits with no dashes, for example `1234567890`.

## Step 1: Clone And Test The Repo

```powershell
git clone https://github.com/YOUR_ORG/google-ads-mcp.git
cd google-ads-mcp

python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,setup]"

python -m unittest discover -s tests
```

The tests work from a fresh checkout because `tests/_bootstrap.py` adds `src/`
to the Python path. Editable install is still recommended because it installs
runtime dependencies.

## Step 2: Get A Google Ads Developer Token

1. Sign in to the Google Ads manager account that owns the API access.
2. Open the API Center: `https://ads.google.com/aw/apicenter`.
3. Complete the API Access form.
4. After receiving the approval email, return to the API Center and copy the
   developer token.

Important details:

- The API Center is only available from a Google Ads manager account, not a
  normal client account.
- Google generally grants one developer token per company.
- Access level controls where and how much you can call the API. Google's
  current documented levels are Test Account Access, Explorer Access, Basic
  Access, and Standard Access.
- Test Account Access is limited to test accounts. Explorer Access can call
  production accounts with lower production limits and restricted services.
  Basic or Standard Access is the real production path for heavier usage.

Store the token as `GOOGLE_ADS_DEVELOPER_TOKEN`.

## Step 3: Create Or Select A GCP Project

```powershell
gcloud auth login
gcloud config set project YOUR_GCP_PROJECT_ID
```

Enable the APIs the deploy script needs:

```powershell
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable googleads.googleapis.com
```

The deploy script also enables these, but running this early gives cleaner
errors if the project or billing setup is wrong.

## Step 4: Configure OAuth Consent And Test Users

In Google Cloud Console, open Google Auth Platform. In older console navigation,
this may still appear under APIs and Services -> OAuth consent screen.

1. Set branding:
   - App name: something clear, for example `My Google Ads MCP`.
   - User support email: your email.
   - Developer contact email: your email.
2. Set audience:
   - Choose Internal only if all users are in your Google Workspace.
   - Choose External if you use normal Gmail or external accounts.
3. Add the Google Ads scope:
   - `https://www.googleapis.com/auth/adwords`
4. If the app is in Testing mode, add yourself under test users.

For private setup, adding yourself as a test user usually avoids going through
Google OAuth app verification during initial setup. You will see an unverified
app warning, but listed test users can continue.

The major catch: Testing-mode authorizations expire after seven days for scopes
like Google Ads. If you need this Cloud Run service to run unattended for more
than a week, use one of these durable paths:

- Use an Internal app if you are inside a Google Workspace and all users are in
  that organization.
- Move the app to Production and complete Google verification if Google requires
  it for your app and scopes.
- Re-generate the refresh token periodically while you are still testing.

OAuth app verification and Google Ads developer-token access review are separate
processes. Passing one does not automatically approve the other.

## Step 5: Create OAuth Client Credentials

In Google Cloud Console:

1. Go to APIs and Services -> Credentials.
2. Create OAuth client ID.
3. Choose Desktop app for the simplest owner setup.
4. Download the client JSON file, or copy the client ID and client secret.

With the Desktop app type, you do not need to configure redirect URIs in the
console. The refresh-token helper starts a local callback server on a random
available port.

Do not commit the downloaded OAuth JSON. The repo ignores `client_secret*.json`
and `oauth*.json`.

Generate the Google Ads refresh token:

```powershell
python scripts\generate_refresh_token.py --client-secrets .\client_secret_YOUR_APP.json
```

Or use direct values:

```powershell
python scripts\generate_refresh_token.py `
  --client-id "YOUR_CLIENT_ID.apps.googleusercontent.com" `
  --client-secret "YOUR_CLIENT_SECRET"
```

The script opens a browser. Sign in as the Google user who can access the ad
accounts. Copy the printed `GOOGLE_ADS_REFRESH_TOKEN`.

For local smoke tests, you can also have the script update `.env`
automatically after the Google login succeeds:

```powershell
python scripts\generate_refresh_token.py --write-env --prompt
```

The prompt asks for `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`,
`GOOGLE_ADS_DEVELOPER_TOKEN`, and optional `GOOGLE_ADS_LOGIN_CUSTOMER_ID`.
Omit the login customer ID for direct single-account access. In `--write-env`
mode, the script saves `GOOGLE_ADS_REFRESH_TOKEN` locally and does not print it.

If Google does not return a refresh token, remove the app's prior access from
your Google Account permissions, then run the script again.

## Step 6: Generate The MCP Bearer Token

This token protects the MCP endpoint from random public access.

```powershell
$bytes = New-Object byte[] 32
[System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
$mcpToken = [Convert]::ToBase64String($bytes).TrimEnd("=").Replace("+", "-").Replace("/", "_")
$mcpToken
```

Copy the value. Store it as `MCP_BEARER_TOKEN`.

## Step 7: Local Smoke Test

Create a local `.env` from the example:

```powershell
Copy-Item .env.example .env
```

Fill:

```text
MCP_BEARER_TOKEN=...
GOOGLE_ADS_DEVELOPER_TOKEN=...
GOOGLE_ADS_CLIENT_ID=...
GOOGLE_ADS_CLIENT_SECRET=...
GOOGLE_ADS_REFRESH_TOKEN=...
GOOGLE_ADS_LOGIN_CUSTOMER_ID=
GOOGLE_ADS_API_VERSION=v24
ALLOW_UNAUTHENTICATED_MCP=false
```

For MCC users, set `GOOGLE_ADS_LOGIN_CUSTOMER_ID` to the manager customer ID
with digits only. For direct single-account access, leave it empty.

Keep `ALLOW_UNAUTHENTICATED_MCP=false` in Cloud Run. Setting it to `true` on a
public service exposes the MCP endpoint; the write confirmation gate still helps,
but the service should not be public without authentication.

Start the server:

```powershell
python -m google_ads_mcp
```

Health check:

```powershell
Invoke-WebRequest http://localhost:8080/healthz
Invoke-WebRequest http://localhost:8080/readyz
```

Then connect with any local MCP-capable client and call:

1. `get_tool_catalog`
2. `account_list_customers`
3. `account_get_account_info` with a leaf `customer_id`
4. `reporting_get_campaign_metrics` with a custom `start_date` and `end_date`

Do not test real writes first. Use validation mode:

```json
{
  "customer_id": "1234567890",
  "payload": {},
  "validate_only": true
}
```

## Step 8: Store Secrets In GCP Secret Manager

Set your project:

```powershell
gcloud config set project YOUR_GCP_PROJECT_ID
```

Create each required secret without a trailing newline. Do not paste secrets
into `gcloud secrets create --data-file=-` interactively; pressing Enter before
ending stdin stores a newline in the secret value, and bearer tokens and OAuth
secrets are exact string values.

Use the helper script:

```powershell
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name MCP_BEARER_TOKEN
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_DEVELOPER_TOKEN
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_CLIENT_ID
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_CLIENT_SECRET
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_REFRESH_TOKEN
```

If you use an MCC login customer ID:

```powershell
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_LOGIN_CUSTOMER_ID
```

The helper creates a new secret when one does not exist and adds a new secret
version when it already exists.

If you do not want to use the helper, use a temp file and write the exact value
without a newline:

```powershell
$ProjectId = "YOUR_GCP_PROJECT_ID"
$value = "paste-exact-secret-value-here"
$tmp = [System.IO.Path]::GetTempFileName()
[System.IO.File]::WriteAllText($tmp, $value, [System.Text.Encoding]::UTF8)
gcloud secrets create MCP_BEARER_TOKEN --data-file=$tmp --project=$ProjectId
Remove-Item $tmp
```

Never paste these values into ChatGPT, Claude, GitHub issues, PR comments, or
agent prompts.

## Step 9: Grant Cloud Run Access To Secrets

The Cloud Run runtime service account must be allowed to read Secret Manager
values. The deploy script grants this role automatically for the default compute
service account, but if you are deploying manually, run:

```powershell
$ProjectId = "YOUR_GCP_PROJECT_ID"
$projectNumber = gcloud projects describe $ProjectId --format "value(projectNumber)"
$sa = "$projectNumber-compute@developer.gserviceaccount.com"
gcloud projects add-iam-policy-binding $ProjectId `
  --member "serviceAccount:$sa" `
  --role "roles/secretmanager.secretAccessor"
```

Wait 30 to 60 seconds before deploying so the IAM binding has time to
propagate.

## Step 10: Deploy To Cloud Run

Run:

```powershell
.\deploy\cloud-run.ps1 -ProjectId YOUR_GCP_PROJECT_ID
```

Defaults:

| Setting | Value |
|---|---|
| Cloud Run service | `google-ads-mcp` |
| Region | `us-central1` |
| Artifact Registry repo | `mcp-servers` |
| Port | `8080` |
| MCP path | `/mcp` |
| Health path | `/healthz` |
| Readiness path | `/readyz` |

The service uses public ingress because most external AI clients cannot mint
Google IAM tokens. The app still requires `Authorization: Bearer
<MCP_BEARER_TOKEN>`.

Cloud Run may scale to zero after idle time. The first request after idle can
take 5 to 15 seconds while a new instance starts; later requests are normally
much faster.

Get the URL:

```powershell
$url = gcloud run services describe google-ads-mcp `
  --region us-central1 `
  --format "value(status.url)"
$url
```

Your MCP URL is:

```text
https://YOUR-CLOUD-RUN-SERVICE-URL/mcp
```

## Step 11: Cloud Run Smoke Test

Health check:

```powershell
Invoke-WebRequest "$url/healthz"
Invoke-WebRequest "$url/readyz"
```

MCP initialize check:

```powershell
$body = @{
  jsonrpc = "2.0"
  id = 1
  method = "initialize"
  params = @{
    protocolVersion = "2025-03-26"
    capabilities = @{}
    clientInfo = @{
      name = "google-ads-mcp-smoke-test"
      version = "1.0"
    }
  }
} | ConvertTo-Json -Depth 10

Invoke-WebRequest `
  -Uri "$url/mcp" `
  -Method Post `
  -ContentType "application/json" `
  -Headers @{
    Authorization = "Bearer $env:MCP_BEARER_TOKEN"
    Accept = "application/json, text/event-stream"
  } `
  -Body $body
```

If this returns `401`, the MCP bearer token in your shell does not match the
Secret Manager value used by Cloud Run.

## Step 12: Connect AI Agents

Use this URL everywhere:

```text
https://YOUR-CLOUD-RUN-SERVICE-URL/mcp
```

Use this header when the client supports custom headers:

```text
Authorization: Bearer YOUR_MCP_BEARER_TOKEN
```

### Generic Remote MCP JSON

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "type": "http",
      "url": "https://YOUR-CLOUD-RUN-SERVICE-URL/mcp",
      "headers": {
        "Authorization": "Bearer ${MCP_BEARER_TOKEN}"
      }
    }
  }
}
```

Some clients use `serverUrl` or `httpUrl` instead of `url`.

### Codex

Preferred CLI setup:

```powershell
$env:MCP_BEARER_TOKEN = "YOUR_MCP_BEARER_TOKEN"
codex mcp add google-ads-mcp `
  --url https://YOUR-CLOUD-RUN-SERVICE-URL/mcp `
  --bearer-token-env-var MCP_BEARER_TOKEN
codex mcp list
```

Equivalent `~/.codex/config.toml`:

```toml
[mcp_servers.google-ads-mcp]
url = "https://YOUR-CLOUD-RUN-SERVICE-URL/mcp"
bearer_token_env_var = "MCP_BEARER_TOKEN"
```

Then ask Codex:

```text
Use google-ads-mcp. First call get_tool_catalog, then account_list_customers.
Do not run real writes unless I provide CONFIRM_GOOGLE_ADS_WRITE.
```

### Claude Code Or Claude Agent SDK

Preferred CLI setup:

```powershell
$env:MCP_BEARER_TOKEN = "YOUR_MCP_BEARER_TOKEN"
claude mcp add --transport http google-ads-mcp `
  --header "Authorization: Bearer $env:MCP_BEARER_TOKEN" `
  https://YOUR-CLOUD-RUN-SERVICE-URL/mcp
```

For project config, create `.mcp.json`. Use the exact schema supported by your
Claude Code version; a minimal remote HTTP shape is:

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "url": "https://YOUR-CLOUD-RUN-SERVICE-URL/mcp",
      "headers": {
        "Authorization": "Bearer ${MCP_BEARER_TOKEN}"
      }
    }
  }
}
```

When using the Agent SDK, allow tools from this server explicitly:

```text
mcp__google-ads-mcp__*
```

For safer operation, allow only read tools at first, then add write tools after
you trust the setup.

### Antigravity

If your Antigravity workspace supports remote MCP servers, check its workspace
documentation for the exact key names. Some builds use `serverUrl`:

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "serverUrl": "https://YOUR-CLOUD-RUN-SERVICE-URL/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_BEARER_TOKEN"
      }
    }
  }
}
```

If your Antigravity build supports environment interpolation in headers, prefer
that over pasting the token directly.

### ChatGPT Developer Mode

ChatGPT Developer Mode can create apps from remote MCP servers and supports
streaming HTTP. The current documented auth paths are OAuth, no authentication,
and mixed authentication.

This repo currently protects `/mcp` with a static bearer token. Because ChatGPT
may not let you attach an arbitrary static `Authorization` header in the app UI,
use one of these paths:

1. Recommended production path: add an OAuth 2.1 front door for this MCP, or put
   a tiny OAuth-aware gateway in front of Cloud Run that injects the bearer
   token when calling the private MCP service.
2. Private testing only: deploy a separate test service with
   `ALLOW_UNAUTHENTICATED_MCP=true`, keep writes gated by the server's
   confirmation phrase, use a non-production Google Ads account, and delete the
   service after testing.

Do not expose a no-auth Cloud Run service connected to a real ad account.

### Claude.ai Custom Connectors

Claude custom connectors use remote MCP servers reachable from Anthropic's cloud
infrastructure. Use the Cloud Run `/mcp` URL. If the connector UI supports custom
headers, pass the same bearer header. If it requires OAuth instead, use the same
OAuth front-door pattern described for ChatGPT.

### Stdio-Only Clients

Some older clients can only launch local stdio MCP servers. Use the relay:

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "command": "google-ads-mcp-stdio-relay",
      "env": {
        "MCP_URL": "https://YOUR-CLOUD-RUN-SERVICE-URL/mcp",
        "MCP_BEARER_TOKEN": "YOUR_MCP_BEARER_TOKEN"
      }
    }
  }
}
```

The relay forwards stdio JSON-RPC to the hosted Streamable HTTP endpoint.

## Step 13: First Useful Prompts

Read-only account discovery:

```text
Use google-ads-mcp. Call account_list_customers, then account_get_mcc_hierarchy
if a manager account is available. Summarize only account names, IDs, currency,
and time zone.
```

Custom-date report:

```text
Use google-ads-mcp. For customer_id 1234567890, run
reporting_get_campaign_metrics from 2026-05-01 to 2026-05-31. Include
impressions, clicks, cost, conversions, CPA, and ROAS. Do not mutate anything.
```

GAQL planning:

```text
Before writing GAQL, call metadata_query_google_ads_docs for "quality score
keyword metrics", then use reporting_execute_gaql_query only after checking the
primary field rule.
```

Validation-only write:

```text
Use google-ads-mcp to validate adding the negative exact keyword [free] at the
campaign level for customer_id 1234567890 and campaign_id 1111111111. Use
validate_only=true. Do not execute the write.
```

Real write:

```text
Use google-ads-mcp to pause campaign 1111111111 in customer_id 1234567890.
execute=true. confirmation_phrase=CONFIRM_GOOGLE_ADS_WRITE.
```

## Write Safety Rules

Every write tool defaults to `validate_only=true`.

A real write requires all of these:

- `execute=true`
- `validate_only=false`
- `confirmation_phrase="CONFIRM_GOOGLE_ADS_WRITE"`
- explicit `customer_id`

Use validation-only writes for campaign creation, PMax asset groups, negatives,
audience updates, and conversion upload payload checks before making any real
change.

## MCC And Multi-Account Setup

If the OAuth user has access to a manager account:

1. Set `GOOGLE_ADS_LOGIN_CUSTOMER_ID` to the manager ID, digits only.
2. Use `account_list_customers` to discover accessible accounts.
3. Use `account_get_mcc_hierarchy` to map parent and child accounts.
4. Use a leaf customer ID for reports and writes.

Manager accounts are for hierarchy traversal. Most reporting and mutate calls
must target a leaf account.

## Maintenance

### Rotate A Secret

Use this whenever a refresh token expires, an MCP bearer token leaks, or you
replace OAuth credentials:

```powershell
.\scripts\set_gcp_secret.ps1 -ProjectId YOUR_GCP_PROJECT_ID -Name GOOGLE_ADS_REFRESH_TOKEN
```

Then create a new Cloud Run revision so running instances pick up the new
Secret Manager version:

```powershell
gcloud run services update google-ads-mcp `
  --region us-central1 `
  --update-secrets "GOOGLE_ADS_REFRESH_TOKEN=GOOGLE_ADS_REFRESH_TOKEN:latest"
```

For `MCP_BEARER_TOKEN`, also update every agent/client configuration that sends
the bearer token.

### Update The Google Ads API Version

The deploy script currently sets `GOOGLE_ADS_API_VERSION=v24`. When Google
deprecates that version:

1. Update the `google-ads` Python package constraint in `pyproject.toml` if the
   new API version requires a newer client.
2. Update `GOOGLE_ADS_API_VERSION` in `deploy/cloud-run.ps1`.
3. Run tests locally.
4. Redeploy with `.\deploy\cloud-run.ps1 -ProjectId YOUR_GCP_PROJECT_ID`.

For a one-off Cloud Run environment update after the image already supports the
new version:

```powershell
gcloud run services update google-ads-mcp `
  --region us-central1 `
  --set-env-vars "GOOGLE_ADS_API_VERSION=v25,GOOGLE_PROJECT_ID=YOUR_GCP_PROJECT_ID"
```

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `401` from `/mcp` | Wrong MCP bearer token | Rotate `MCP_BEARER_TOKEN` in Secret Manager and update the client env var |
| `500` on `/healthz` immediately after deploy | Cloud Run service account cannot read Secret Manager or IAM has not propagated | Grant `roles/secretmanager.secretAccessor` and wait 30 to 60 seconds |
| `403` or developer token error | Token access level or approval issue | Check API Center and token access level |
| `The API Center is only available to manager accounts` | You are in a client account | Sign into or create a Google Ads manager account |
| Refresh token works locally but expires after a week | OAuth app is in Testing mode | Move to durable OAuth path or regenerate token |
| Client times out on first request after idle | Cloud Run cold start | Retry once after 15 seconds, or configure minimum instances if you need instant first calls |
| Metrics fail on MCC ID | Manager account used for leaf-only call | Use a child leaf customer ID |
| `EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE` | GAQL missing primary field | Call `metadata_query_google_ads_docs` and include the primary field |
| Cloud Run is healthy but client cannot connect | Client cannot send headers or cannot reach public URL | Use a header-capable config, OAuth gateway, or stdio relay |
| Google Ads linked accounts missing | API surface or account linking not available | Use generic service tools or `unsupported_capability` output to confirm |

## What To Publish To GitHub

Safe:

- Source code.
- `.env.example`.
- Docs.
- Tests.
- Generated tool catalog and GAQL KB docs.
- Deploy scripts.

Never publish:

- `.env`
- OAuth JSON files.
- Refresh tokens.
- Developer tokens.
- MCP bearer tokens.
- Customer data.
- Invoices or invoice PDFs.
- Customer Match or audience upload files.
- Logs that contain request payloads or customer IDs you consider sensitive.

Run before publishing:

```powershell
python -m unittest discover -s tests
python -m compileall src scripts tests
$pattern = "AIza|ya29\.|1//|refresh_token|client_secret|developer_token|MCP_BEARER_TOKEN"
Get-ChildItem -Recurse -File |
  Where-Object {
    $_.FullName -notmatch "\\__pycache__\\" -and
    $_.Extension -notin @(".md", ".example")
  } |
  Select-String -Pattern $pattern
```

The scan ignores markdown and `.example` files. Review any match manually before
publishing.

## Source References

- Google Ads developer token: https://developers.google.com/google-ads/api/docs/api-policy/developer-token
- Google Ads API access levels: https://developers.google.com/google-ads/api/docs/api-policy/access-levels
- Google Ads OAuth single-user auth: https://developers.google.com/google-ads/api/docs/oauth/single-user-authentication
- Google Ads REST auth headers: https://developers.google.com/google-ads/api/rest/auth
- Google Cloud OAuth app audience and test users: https://support.google.com/cloud/answer/15549945
- Cloud Run Secret Manager access requirements: https://docs.cloud.google.com/run/docs/configuring/services/secrets
- Cloud Run deploy flags and Secret Manager env mapping: https://docs.cloud.google.com/sdk/gcloud/reference/run/deploy
- ChatGPT Developer Mode MCP apps: https://platform.openai.com/docs/guides/developer-mode
- Claude Code MCP configuration: https://docs.anthropic.com/en/docs/claude-code/mcp
- Claude custom remote MCP connectors: https://support.anthropic.com/en/articles/11175166-getting-started-with-custom-integrations-using-remote-mcp
- Antigravity MCP integration: check your Antigravity workspace documentation.
