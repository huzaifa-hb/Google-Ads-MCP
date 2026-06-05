# Live Metadata And GAQL Planning

Use these tools before writing raw GAQL or broad reports. They are read-only and
remain exposed in `safe_read_only`.

## Resource Metadata

```json
{
  "resource_name": "campaign"
}
```

Call `metadata_get_google_ads_resource_metadata` to return:

- selectable resource fields
- filterable fields
- sortable fields
- compatible metrics
- compatible segments
- cached status

The metadata cache is keyed by API version and resource name.

## Validate Fields

```json
{
  "resource_name": "campaign",
  "fields": ["campaign.id", "campaign.name", "metrics.clicks"]
}
```

Call `metadata_validate_gaql_fields` when an agent or user supplies fields. The
tool returns valid fields, invalid fields, and suggestions for misspellings.

## Suggest Fields

```json
{
  "resource_name": "campaign",
  "field_prefix_or_query": "campaign.na",
  "limit": 10
}
```

Call `metadata_suggest_gaql_fields` to complete field names from live metadata.

## Plan Query

```json
{
  "resource_name": "campaign",
  "user_goal": "campaign clicks and cost for active campaigns",
  "fields": ["campaign.name"],
  "metrics": ["metrics.clicks", "metrics.cost_micros"],
  "filters": {
    "campaign.status": "ENABLED"
  },
  "date_range": "LAST_7_DAYS"
}
```

Call `planning_plan_gaql_query` to return a GAQL string and warnings. It does
not execute the query. Review the query, then run it with a read-only search
tool.

## Explain Errors

```json
{
  "error_text": "EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE"
}
```

Call `planning_explain_gaql_error` after a failed GAQL attempt. It maps common
errors to practical next steps and points back to the metadata/planning tools.
