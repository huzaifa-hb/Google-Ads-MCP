# Security

This project can access Google Ads accounts and can expose write-capable tools
when explicitly configured. Treat it like production infrastructure.

## Defaults

- `GOOGLE_ADS_MCP_MODE=safe_read_only`
- `GOOGLE_ADS_MCP_AUTH_MODE=bearer`
- mutation and generic bridge tools hidden by default
- unknown generic service methods denied unless an explicit admin-debug escape
  hatch is enabled
- real writes require `execute=true`, `validate_only=false`, and
  `confirmation_phrase=CONFIRM_GOOGLE_ADS_WRITE`

## Never Commit

- `.env` files
- developer tokens
- OAuth client secrets
- refresh tokens
- MCP bearer tokens
- customer data
- invoices or invoice PDFs
- Customer Match or audience upload data

## Reporting Issues

For private deployments, rotate affected tokens first. Then open a private issue
or contact the repository owner with the affected component, impact, and whether
external state could have changed.
