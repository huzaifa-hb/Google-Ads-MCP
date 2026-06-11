# Comparison

This repo is not trying to replace the official Google Ads MCP server.

## Official Google Ads MCP

Best fit:

- trusted read-only reporting
- live resource metadata discovery
- OAuth-first client integrations
- a smaller official tool surface

Tradeoff:

- intentionally less focused on controlled write workflows
- less broad for operational agency-style tasks

## This Repo

Best fit:

- private owner or agency deployments
- validation-first write workflows
- broad friendly tool coverage
- configurable tool exposure by namespace
- Cloud Run deployment with bearer auth by default

Tradeoff:

- broader tool surface requires stricter configuration discipline
- real writes need careful operational controls
- optional OAuth front door is a deployment choice, not the default

## Recommended Default

Start with `safe_read_only`, use `validation_only` for payload previews, and only
use `write_enabled` plus an explicit write-capable tool profile on a private
endpoint with the confirmation phrase gate.
