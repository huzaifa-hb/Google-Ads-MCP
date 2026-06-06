# Connect Your AI App

This page shows how to connect an AI app after the Google Ads MCP server is
running.

You need two things:

- the MCP URL, usually something like `https://YOUR-CLOUD-RUN-URL/mcp`,
- the private bearer token stored as `MCP_BEARER_TOKEN`.

Do not paste the real token into public docs, screenshots, support tickets, or
chat messages.

## Codex

If Codex supports remote MCP URLs, use:

```toml
[mcp_servers.google-ads-mcp]
url = "https://YOUR-CLOUD-RUN-URL/mcp"
bearer_token_env_var = "MCP_BEARER_TOKEN"
```

You can generate this with:

```powershell
npx @huzaifa-hb/google-ads-mcp config --client codex --transport remote --url https://YOUR-CLOUD-RUN-URL/mcp
```

## Claude Desktop Or Apps That Launch Local Tools

Some apps launch tools through a local command instead of connecting directly to
a remote URL. Use the npm relay for those apps:

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "command": "npx",
      "args": [
        "-y",
        "@huzaifa-hb/google-ads-mcp",
        "relay",
        "--url",
        "https://YOUR-CLOUD-RUN-URL/mcp",
        "--token-env",
        "MCP_BEARER_TOKEN"
      ]
    }
  }
}
```

Generate it with:

```powershell
npx @huzaifa-hb/google-ads-mcp config --client claude-desktop --transport stdio --url https://YOUR-CLOUD-RUN-URL/mcp
```

The relay reads the token from the environment. It does not put the token in a
`--token` argument.

## Generic Remote MCP Clients

If your AI app lets you add headers, use:

```json
{
  "mcpServers": {
    "google-ads-mcp": {
      "httpUrl": "https://YOUR-CLOUD-RUN-URL/mcp",
      "headers": {
        "Authorization": "Bearer ${MCP_BEARER_TOKEN}"
      }
    }
  }
}
```

Some apps use `url` instead of `httpUrl`. Use the field name your app expects.

## Test The Connection

In your AI app, ask it to call:

```text
get_tool_catalog
```

Then try a read-only request:

```text
List my accessible Google Ads accounts.
```

If the app cannot connect, check:

- Is the MCP URL correct?
- Is `MCP_BEARER_TOKEN` set in the same place where the AI app runs?
- Did you restart the AI app after changing its config?
- Is the Cloud Run service awake and healthy?

## Writes Are Still Locked Down

The server starts in read-only mode. Real campaign changes require write mode
and the confirmation phrase:

```text
CONFIRM_GOOGLE_ADS_WRITE
```
