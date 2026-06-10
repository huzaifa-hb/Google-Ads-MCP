# Easy Setup With NPM

This page is for people who want to use the Google Ads MCP without learning the
project internals.

The npm wrapper is a helper. It does not replace the Python Google Ads engine.
It just handles the boring setup steps for you.

## What The Setup Does

When you run setup, it:

- creates a local folder for the Python server,
- creates a private `.env` file for your credentials,
- generates a private MCP bearer token,
- opens the Google sign-in flow,
- installs the Python Google Ads MCP package,
- checks whether the setup looks ready.

It does not send your Google Ads developer token, OAuth secret, refresh token, or
MCP bearer token through command-line arguments.

## First Run

Open PowerShell in the folder where you want the setup to live.

```powershell
npx @huzaifa-hb/google-ads-mcp setup
```

The setup will ask for Google Ads values, store sensitive Google Ads values in
the OS keyring, and write only local references to `.env`. If you do not have
the values yet, use the [owner setup guide](owner-setup-guide.md) to collect
them.

Start the server:

```powershell
npx @huzaifa-hb/google-ads-mcp start
```

Check it:

```powershell
npx @huzaifa-hb/google-ads-mcp smoke
```

## Connect An AI App

Generate a config snippet:

```powershell
npx @huzaifa-hb/google-ads-mcp config --client claude-desktop --transport stdio --url https://YOUR-CLOUD-RUN-URL/mcp
```

Or for Codex:

```powershell
npx @huzaifa-hb/google-ads-mcp config --client codex --transport remote --url https://YOUR-CLOUD-RUN-URL/mcp
```

The generated config references `MCP_BEARER_TOKEN` by name. It does not paste
the token value into the command.

## Profiles

- `local-direct`: use the server on your own computer.
- `remote-cloud-run`: use your Cloud Run URL.
- `brokered-readonly`: reserved for a future hosted option and not available.

## Common Commands

```powershell
npx @huzaifa-hb/google-ads-mcp doctor
npx @huzaifa-hb/google-ads-mcp start
npx @huzaifa-hb/google-ads-mcp smoke
npx @huzaifa-hb/google-ads-mcp cloud sync-secrets --project YOUR_GCP_PROJECT_ID
npx @huzaifa-hb/google-ads-mcp cloud deploy --project YOUR_GCP_PROJECT_ID
```

## Keep These Private

Never share:

- `.env`
- `MCP_BEARER_TOKEN`
- `GOOGLE_ADS_DEVELOPER_TOKEN`
- `GOOGLE_ADS_CLIENT_SECRET`
- `GOOGLE_ADS_REFRESH_TOKEN`
- downloaded OAuth client JSON files
