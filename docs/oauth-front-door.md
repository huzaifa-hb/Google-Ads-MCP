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
- `https://www.googleapis.com/auth/adwords`

## Production Notes

- Do not set `ALLOW_UNAUTHENTICATED_MCP=true` on a production endpoint.
- Store OAuth client secrets in Secret Manager.
- Keep `safe_read_only` as the first deployment mode.
- OAuth protects MCP access; Google Ads account access still depends on the
  configured Google Ads developer token and OAuth refresh token used by the
  server.
