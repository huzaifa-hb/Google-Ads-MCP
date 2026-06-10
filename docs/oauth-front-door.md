# OAuth Front Door

Bearer auth remains the default and recommended path for a private owner Cloud
Run deployment. Use OAuth proxy mode only when the MCP client needs an OAuth
flow instead of a static bearer header.

## Bearer Default

```powershell
$env:GOOGLE_ADS_MCP_AUTH_MODE = "bearer"
$env:MCP_BEARER_TOKEN = "long-random-token"
python -m google_ads_mcp
```

## OAuth Proxy Mode

```powershell
$env:GOOGLE_ADS_MCP_AUTH_MODE = "oauth_proxy"
$env:GOOGLE_ADS_MCP_OAUTH_CLIENT_ID = "your-oauth-client-id"
$env:GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET = "your-oauth-client-secret"
$env:GOOGLE_ADS_MCP_BASE_URL = "https://your-cloud-run-url"
python -m google_ads_mcp
```

Required scopes:

- `openid`
- `https://www.googleapis.com/auth/userinfo.email`
- `https://www.googleapis.com/auth/userinfo.profile`

Optional access allowlists:

```powershell
$env:GOOGLE_ADS_MCP_ALLOWED_EMAILS = "owner@example.com,ops@example.com"
$env:GOOGLE_ADS_MCP_ALLOWED_DOMAINS = "example.com"
```

When either allowlist is configured, OAuth users must match an allowed email,
subject, hosted domain, or email domain before the MCP accepts the token.

For hosted per-user Google Ads access, each connected user signs in with their
own Google account:

```powershell
$env:GOOGLE_ADS_AUTH_MODE = "per_user_oauth"
```

In this mode, `oauth_proxy` still needs an access policy. Use an email/domain
allowlist for private team deployments. If you deliberately want any Google
OAuth user allowed through the MCP front door, set:

```powershell
$env:GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS = "true"
```

Do not set that flag casually. It means Google OAuth succeeds for any Google
identity; Google Ads account access is then limited by that user's Google Ads
permissions.

## Google Ads OAuth Bootstrap

If `GOOGLE_ADS_OAUTH_BOOTSTRAP_TOKEN` is configured, admin bootstrap routes can
generate a Google Ads refresh token through the hosted OAuth callback. Send the
bootstrap secret only as this HTTP header:

```text
x-google-ads-bootstrap-token: <bootstrap-token>
```

The old query-string form is rejected so the secret is less likely to appear in
browser history, logs, or shared links.

Bootstrap results contain refresh tokens. With
`GOOGLE_ADS_MCP_TOKEN_STORAGE=firestore`, the server stores them through the
same Fernet-encrypted Firestore key-value pattern used for OAuth token storage,
with a separate namespace and salt. Results are deleted on first read, and
expired results are treated as pending.

With local token storage, bootstrap results stay in process memory only and are
encrypted with a process-local key until they are popped. That is fine for a
single local instance, but it is not reliable for multiple Cloud Run instances
or restarts.

## Production Notes

- Do not set `ALLOW_UNAUTHENTICATED_MCP=true` on a production endpoint.
- Store OAuth client secrets in Secret Manager.
- Configure email or domain allowlists before exposing OAuth proxy mode beyond a
  single private tester.
- Keep `safe_read_only` as the first deployment mode.
- Keep `GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE=false` unless you are doing
  private `admin_debug` work.
- OAuth protects MCP access; Google Ads account access still depends on the
  configured Google Ads developer token and OAuth refresh token used by the
  server.
