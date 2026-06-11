# Tool Configuration

Tool exposure is controlled by `tools_config.yaml`. The server resolves config
in this order:

1. `GOOGLE_ADS_MCP_TOOLS_CONFIG`
2. `tools_config.yaml` in the current working directory
3. bundled default config

`GOOGLE_ADS_MCP_MODE` overrides the file's `mode`.
`GOOGLE_ADS_MCP_TOOL_PROFILE` can switch breadth without editing the file:

- `lean`: default curated 35-tool PPC read catalog. It keeps metadata/planning,
  account basics, campaign/ad group/ad/keyword/budget list/get tools, raw GAQL,
  and the high-frequency campaign, ad group, ad, keyword, search terms, device,
  geo, landing page, and change history reports.
- `standard`: the broader read catalog from earlier releases.
- `agency_write`: read tools plus hand-built media-buyer write helpers for
  campaigns, budgets, ad groups, ads, keywords, negative keywords, assets,
  labels, extensions, and bulk operations. It does not expose raw mutate or the
  generic service bridge.
- `advanced_mutate`: `agency_write` plus `generic_google_ads_mutate` for
  explicit raw mutate workflows. It still does not expose
  `generic_google_ads_call_service`.
- `full`: every read namespace, with write exposure still controlled by
  `GOOGLE_ADS_MCP_MODE`.

`GOOGLE_ADS_MCP_MODE=write_enabled` is only a gate. It permits configured write
tools to commit after confirmation, but it does not load write tools by itself.

## Default Shape

```yaml
mode: safe_read_only
tool_profile: lean

legacy_aliases:
  enabled: false

namespaces:
  metadata:
    enabled: true
    prefix: metadata
  planning:
    enabled: true
    prefix: planning
  reporting:
    enabled: true
    prefix: reporting
  campaigns:
    enabled: true
    prefix: campaigns
  generic:
    enabled: false
    prefix: generic

tools:
  google_ads_mutate:
    enabled: false
  google_ads_call_service:
    enabled: false
```

Most tools register as `<prefix>_<canonical_tool_name>`, such as
`reporting_get_campaign_metrics`. `get_tool_catalog` is the stable unprefixed
introspection tool and returns the currently exposed tool set.
`get_capability_matrix` and `get_server_status` are also unprefixed. They return
implementation status and server mode/config status for the currently exposed
tool set.

The default read-only surface includes:

- `metadata_get_google_ads_resource_metadata`
- `metadata_validate_gaql_fields`
- `metadata_suggest_gaql_fields`
- `planning_plan_gaql_query`
- `planning_explain_gaql_error`
- `get_capability_matrix`
- `get_server_status`

These tools are safe in `safe_read_only`: they inspect metadata, validate field
choices, or build query text. They do not call GoogleAdsService search or mutate.

## Enable Validation-Only Campaign Writes

```yaml
mode: validation_only

legacy_aliases:
  enabled: false

namespaces:
  campaigns:
    enabled: true
    prefix: campaigns

tools:
  pause_campaign:
    enabled: true
  enable_campaign:
    enabled: true
```

In this mode, `campaigns_pause_campaign` can validate a pause operation, but the
server still forces `validate_only=true`.

## Enable Agency Writes

Cloud deployments stay read-only unless you choose both write mode and a
write-capable profile:

```powershell
npx @huzaifa-hb/google-ads-mcp cloud deploy --project YOUR_GCP_PROJECT_ID --mode write_enabled --tool-profile agency_write
```

This exposes tools such as `campaigns_create_search_campaign`,
`campaigns_update_campaign`, `campaigns_pause_campaign`, `ads_pause_ad`,
`budgets_update_budget`, keyword write helpers, negative keyword helpers, and
bulk campaign/bid helpers. Real writes still require `execute=true`,
`validate_only=false`, and
`confirmation_phrase="CONFIRM_GOOGLE_ADS_WRITE"`.

Use `advanced_mutate` only when agents need to plan custom
GoogleAdsService.Mutate operations:

```powershell
npx @huzaifa-hb/google-ads-mcp cloud deploy --project YOUR_GCP_PROJECT_ID --mode write_enabled --tool-profile advanced_mutate
```

## Enable Legacy Aliases

```yaml
mode: validation_only

legacy_aliases:
  enabled: true

namespaces:
  campaigns:
    enabled: true
    prefix: campaigns
```

This exposes both `campaigns_pause_campaign` and `pause_campaign` when the tool
is otherwise allowed by mode and namespace. Keep aliases off when you want a
clean namespaced surface for agents.

## Admin Debug

Generic bridge tools are available only in `admin_debug` and only when the
generic namespace or individual tools are enabled:

```yaml
mode: admin_debug

namespaces:
  generic:
    enabled: true
    prefix: generic

tools:
  google_ads_call_service:
    enabled: true
  google_ads_mutate:
    enabled: true
```

This mode is dangerous because it exposes broad Google Ads API access. Use it
only on a private endpoint and keep the write confirmation gate in place.

Unknown generic service methods are still denied unless
`GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE=true` is also set. Known read-only
methods such as `GoogleAdsFieldService.search_google_ads_fields` and
`InvoiceService.list_invoices` are allowlisted.
