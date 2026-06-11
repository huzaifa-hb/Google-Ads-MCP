# Sample Prompts

Use these as starting points for clients or agents connected to this MCP.

## Safe Account Read

```text
Call get_tool_catalog first. Then list customers and summarize which accounts
are leaf accounts. Do not call any write or generic service tools.
```

## Campaign Performance

```text
For customer 1234567890, use planning_plan_gaql_query to build a campaign
performance query for the last 7 days with campaign name, clicks, cost, and
conversions. Then run the query with a read-only reporting/search tool.
```

## Metadata Before GAQL

```text
Use metadata_get_google_ads_resource_metadata for campaign. Validate these
fields before making a query: campaign.name, metrics.clicks, metrics.cost_micros,
segments.date.
```

## Validation-Only Pause

```text
In validation_only mode, validate pausing campaign 1111111111 for customer
1234567890. Keep validate_only=true and do not execute a real write.
```

## Controlled Real Write

```text
Only if the server is in write_enabled mode and exposes a write-capable profile,
pause campaign 1111111111 for customer 1234567890 with validate_only=false,
execute=true, and confirmation_phrase=CONFIRM_GOOGLE_ADS_WRITE. Show the audit
status afterward.
```

## Troubleshoot GAQL

```text
Explain this GAQL error and recommend the next safe metadata tool:
EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE.
```
