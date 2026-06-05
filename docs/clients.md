# Client Configuration

Replace the URL and bearer token with your Cloud Run service values.

For platform-by-platform setup, including Codex, Claude Code, Antigravity,
ChatGPT Developer Mode, Claude custom connectors, and stdio-only clients, see
`docs/owner-setup-guide.md`.

## Header-Capable Remote MCP Clients

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "httpUrl": "https://YOUR-CLOUD-RUN-URL/mcp",
      "headers": {
        "Authorization": "Bearer YOUR_MCP_BEARER_TOKEN"
      }
    }
  }
}
```

Some clients call the field `url` instead of `httpUrl`; use the field your client expects.

Cloud chatbots that do not support static bearer headers need an OAuth front
door, an auth-injecting gateway, or a separate private test deployment. Do not
expose a no-auth service connected to a real Google Ads account.

For the built-in OAuth proxy mode, see `docs/oauth-front-door.md`.

## Codex-Style Config

If the client supports remote MCP URLs with bearer tokens:

```toml
[mcp_servers.google-ads-mcp]
url = "https://YOUR-CLOUD-RUN-URL/mcp"
bearer_token_env_var = "MCP_BEARER_TOKEN"
```

## Stdio-Only Clients

Use the included relay when a client supports stdio only and cannot attach HTTP headers:

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "command": "google-ads-mcp-stdio-relay",
      "env": {
        "MCP_URL": "https://YOUR-CLOUD-RUN-URL/mcp",
        "MCP_BEARER_TOKEN": "YOUR_MCP_BEARER_TOKEN"
      }
    }
  }
}
```

The relay forwards JSON-RPC stdio messages to Streamable HTTP and carries the MCP session id between requests.

## Smoke Test

Call:

```text
get_tool_catalog
```

Then test a read:

```text
list_customers
```

For writes, use validation mode first. Real writes require:

```text
execute=true
confirmation_phrase=CONFIRM_GOOGLE_ADS_WRITE
```
