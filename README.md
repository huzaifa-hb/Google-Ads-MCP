# Google Ads MCP

[![CI](https://github.com/huzaifa-hb/Google-Ads-MCP/actions/workflows/ci.yml/badge.svg)](https://github.com/huzaifa-hb/Google-Ads-MCP/actions/workflows/ci.yml)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](pyproject.toml)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

Connect an AI assistant to your own Google Ads account without handing your ad
account to a public chatbot or a third-party reporting tool.

This project gives tools like Codex, Claude, and other MCP-capable assistants a
private way to read Google Ads data, plan reports, inspect campaigns, and prepare
safe changes. It starts in read-only mode by default, so it cannot change your
campaigns unless you deliberately turn that on.

The server exposes a broad Google Ads MCP catalog with mixed implementation
levels: hand-built helpers, guarded generic service routes, operation templates,
and explicitly unsupported or eligibility-gated capabilities. Check the
capability matrix before relying on a specific write helper.

## Who This Is For

Use this if you are a marketer, agency owner, media buyer, or PPC operator who
wants an AI assistant to answer questions like:

- Which campaigns spent the most last week?
- Which search terms look wasteful?
- Which campaigns have weak conversion volume?
- Which keywords, ads, or budgets need review?
- What changed recently in this account?

You do not need to write code to use the npm setup path. You do need access to a
Google Ads account, and you need the Google Ads API credentials listed below.
That Google setup is the annoying part. The wrapper is here to make the rest as
simple as possible.

## What You Need

Before setup, collect these:

| Item | Where it comes from | Why it matters |
|---|---|---|
| Google Ads developer token | Google Ads API Center | Lets any tool call the Google Ads API |
| OAuth client ID and secret | Google Cloud Console | Lets you sign in with Google |
| Refresh token | Created during setup | Lets the server keep access after sign-in |
| Optional manager account ID | Your Google Ads MCC | Needed when you manage clients through an MCC |

This repo does not use a hosted broker like GAQL.app. That means you keep the
connection under your control, but Google still requires the API credentials.

## Fast Setup

Install Node.js first if you do not already have it. On Windows, this usually
works:

```powershell
winget install OpenJS.NodeJS.LTS
```

Then open PowerShell in the folder where you want this setup to live and run:

```powershell
npx @huzaifa-hb/google-ads-mcp setup
```

The setup asks for your Google Ads values, opens a browser for Google sign-in,
creates a local `.env` file, and checks whether the server is ready.

Start the local server:

```powershell
npx @huzaifa-hb/google-ads-mcp start
```

Check the connection:

```powershell
npx @huzaifa-hb/google-ads-mcp smoke
```

If the smoke check passes, your AI app can connect.
It also discovers and calls the registered read-only
`list_accessible_customers` tool, so OAuth, developer-token, and account-access
problems fail before you hand the server to an agent.

## Connect Your AI App

For a remote Cloud Run server:

```powershell
npx @huzaifa-hb/google-ads-mcp config --client codex --transport remote --url https://YOUR-CLOUD-RUN-URL/mcp
```

For a local stdio-style client such as Claude Desktop:

```powershell
npx @huzaifa-hb/google-ads-mcp config --client claude-desktop --transport stdio --url https://YOUR-CLOUD-RUN-URL/mcp
```

See [docs/clients.md](docs/clients.md) for copy-paste examples.

## What It Can Do

- List accessible Google Ads accounts.
- Pull campaign, ad group, keyword, ad, search term, asset, audience, conversion,
  recommendation, planning, and reporting data.
- Help build valid GAQL reports without guessing field names.
- Preview changes in validation mode before anything can be committed.
- Run privately on your machine or on your own Google Cloud Run service.

## Safety

The default mode is `safe_read_only`. In that mode, the assistant can read and
analyze data, but it cannot change campaigns.

Real writes require all of this:

- You start the server in `write_enabled` mode.
- The tool call says `validate_only=false`.
- The tool call says `execute=true`.
- The tool call includes `confirmation_phrase="CONFIRM_GOOGLE_ADS_WRITE"`.

Do not put this server online with authentication disabled. Do not share `.env`,
refresh tokens, developer tokens, OAuth secrets, or bearer tokens.

## Migrating To 0.2.0

This release tightens a few public contracts:

- Use `max_rows` for read-tool row caps. `page_size` still works as a deprecated
  alias, but it no longer means rows per page.
- If the server injects a GAQL `LIMIT`, treat that as a total row cap. Responses
  include `limit_injected`, `effective_limit`, and `has_more` metadata when the
  cap may have truncated the result.
- Hosted `oauth_proxy` plus `per_user_oauth` now requires an email/domain
  allowlist, or the explicit opt-in
  `GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS=true`.
- Admin OAuth bootstrap routes accept the bootstrap secret only through the
  `x-google-ads-bootstrap-token` header. Query-string bootstrap tokens are no
  longer accepted.
- The schema/catalog follow-up defaults to a leaner tool profile. Set
  `GOOGLE_ADS_MCP_TOOL_PROFILE=standard` there if you want the broad read-tool
  catalog exposed by earlier versions.

## Cloud Setup

Local setup is best for first use. Cloud Run is better when you want a stable
private URL for multiple AI clients.

The short version:

```powershell
npx @huzaifa-hb/google-ads-mcp cloud sync-secrets --project YOUR_GCP_PROJECT_ID
npx @huzaifa-hb/google-ads-mcp cloud deploy --project YOUR_GCP_PROJECT_ID
```

The full walkthrough is in [docs/owner-setup-guide.md](docs/owner-setup-guide.md).

## If You Are Technical

The Python package is still the real Google Ads engine. The npm wrapper only
makes setup, launch, relay, smoke checks, client config, and Cloud Run setup
easier.

Manual Python setup:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev,setup]"
Copy-Item .env.example .env
python -m google_ads_mcp
```

Run local checks:

```powershell
python -m compileall src scripts tests
python -m unittest discover -s tests
python scripts/check_generated_docs.py
python scripts/scan_for_secrets.py
npm run test:node
```

## Docs

- [Easy npm setup](docs/node-wrapper.md)
- [Client configuration](docs/clients.md)
- [Owner setup guide](docs/owner-setup-guide.md)
- [Modes and safety](docs/modes-and-safety.md)
- [Tool configuration](docs/tool-configuration.md)
- [Live metadata and GAQL planning](docs/live-metadata-and-gaql-planning.md)
- [Capability matrix](docs/capability-matrix.md)
- [Sample prompts](docs/sample-prompts.md)
- [OAuth front door](docs/oauth-front-door.md)
- [Security](SECURITY.md)

## License

Apache-2.0. See [LICENSE](LICENSE).
