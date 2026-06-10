"""Generated MCP input schemas for exposed Google Ads tools."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from .gaql import DEFAULT_DATE_RANGE
from .tool_implementation import (
    AD_GROUP_STATUS_TOOLS,
    AD_STATUS_TOOLS,
    BUDGET_CREATE_TOOLS,
    BUDGET_UPDATE_TOOLS,
    CAMPAIGN_BULK_STATUS_TOOLS,
    CAMPAIGN_CREATE_TOOLS,
    CAMPAIGN_STATUS_TOOLS,
    DIRECT_MUTATION_TOOLS,
    KEYWORD_CREATE_TOOLS,
    KEYWORD_STATUS_TOOLS,
)


TIME_SEGMENTS = ("date", "week", "month", "quarter", "year", "day_of_week", "hour")


def parameters_schema_for_exposure(exposure: Any) -> dict[str, Any]:
    """Return the JSON schema clients should see for one registered tool."""

    spec = getattr(exposure, "friendly_spec", None)
    if spec is None:
        return _core_parameters_schema(str(exposure.canonical_name))
    return _friendly_parameters_schema(spec)


def _core_parameters_schema(name: str) -> dict[str, Any]:
    no_args = {
        "get_tool_catalog",
        "get_capability_matrix",
        "get_server_status",
        "list_google_ads_services",
        "list_accessible_customers",
    }
    if name in no_args:
        return _object_schema({})
    if name == "describe_google_ads_service":
        return _object_schema({"service_name": _string("Google Ads service class name.")}, ["service_name"])
    if name in {"describe_google_ads_resource", "get_google_ads_resource_metadata"}:
        return _object_schema(
            {
                "resource_name": _string("Google Ads GAQL resource name."),
                "force_refresh": _boolean("Refresh live metadata cache before returning results."),
            },
            ["resource_name"],
        )
    if name == "validate_gaql_fields":
        return _object_schema(
            {
                "resource_name": _string("Google Ads GAQL resource name."),
                "fields": _string_array("GAQL fields to validate."),
                "include_metrics": _boolean("Allow metric fields in the validation set.", default=True),
                "include_segments": _boolean("Allow segment fields in the validation set.", default=True),
                "force_refresh": _boolean("Refresh live metadata cache before validation."),
            },
            ["resource_name", "fields"],
        )
    if name == "suggest_gaql_fields":
        return _object_schema(
            {
                "resource_name": _string("Google Ads GAQL resource name."),
                "field_prefix_or_query": _string("Field prefix or natural-language field search."),
                "limit": _integer("Maximum suggestions to return.", default=10, minimum=1),
                "force_refresh": _boolean("Refresh live metadata cache before suggesting fields."),
            },
            ["resource_name", "field_prefix_or_query"],
        )
    if name == "plan_gaql_query":
        return _object_schema(
            {
                "resource_name": _string("Google Ads GAQL resource name."),
                "user_goal": _string("Optional plain-language goal for the query."),
                "fields": _string_array("Resource fields to include."),
                "metrics": _string_array("Metric fields to include."),
                "segments": _string_array("Segment fields to include."),
                **_date_properties(),
                "filters": _filters_schema(),
                "include_primary_field": _boolean("Include the resource primary field.", default=True),
                "force_refresh": _boolean("Refresh live metadata before planning."),
            },
            ["resource_name"],
        )
    if name == "explain_gaql_error":
        return _object_schema({"error_text": _string("GAQL or Google Ads API error text.")}, ["error_text"])
    if name == "query_google_ads_docs":
        return _object_schema(
            {
                "question": _string("Question to answer from the offline Google Ads knowledge base."),
                "category": _string("Optional knowledge-base category filter."),
            },
            ["question"],
        )
    if name == "google_ads_search":
        return _object_schema(
            {
                "customer_id": _customer_id_schema(),
                "query": _string("GAQL query to execute with GoogleAdsService.Search."),
                **_row_cap_properties(),
                "primary_field": _string("Optional primary field used to key or flatten rows."),
            },
            ["customer_id", "query"],
        )
    if name == "google_ads_search_stream":
        return _object_schema(
            {
                "customer_id": _customer_id_schema(),
                "query": _string("GAQL query to execute with GoogleAdsService.SearchStream."),
                "max_rows": _integer("Total row cap for the stream response.", default=10_000, minimum=1),
                "primary_field": _string("Optional primary field used to key or flatten rows."),
            },
            ["customer_id", "query"],
        )
    if name == "google_ads_mutate":
        return _object_schema(
            {
                "customer_id": _customer_id_schema(),
                "operations": _array("GoogleAdsService MutateOperation objects.", {"type": "object"}),
                **_write_safety_properties(),
                "response_content_type": _enum(
                    "Mutation response content type.",
                    ("MUTABLE_RESOURCE", "RESOURCE_NAME_ONLY"),
                    default="MUTABLE_RESOURCE",
                ),
            },
            ["customer_id", "operations"],
        )
    if name == "google_ads_call_service":
        return _object_schema(
            {
                "service_name": _string("Google Ads service class name."),
                "method_name": _string("snake_case service method name."),
                "request": _open_object("Request payload matching the Google Ads protobuf JSON shape."),
                "request_type": _string("Optional protobuf request message type."),
                "is_write": _boolean("Whether this service call mutates Google Ads state."),
                **_write_safety_properties(partial_failure=False),
            },
            ["service_name", "method_name"],
        )
    if name == "validate_google_ads_payload":
        return _object_schema(
            {
                "request_type": _string("Google Ads protobuf request or message type."),
                "payload": _open_object("Protobuf JSON payload to validate."),
            },
            ["request_type", "payload"],
        )
    return _object_schema({})


def _friendly_parameters_schema(spec: Any) -> dict[str, Any]:
    properties: dict[str, Any] = {"customer_id": _customer_id_schema()}
    required = ["customer_id"]

    if spec.name == "get_mcc_hierarchy":
        properties["payload"] = _object_schema(
            {
                "max_depth": _integer("Maximum manager-account recursion depth.", default=10, minimum=0),
            }
        )
        properties.update(_hierarchy_cap_properties())
        return _object_schema(properties, required)

    if spec.mode == "query":
        properties["payload"] = _query_payload_schema(spec)
        properties["filters"] = _filters_schema(spec.resource)
        properties.update(_row_cap_properties())
        return _object_schema(properties, required)

    if spec.mode == "report":
        properties["filters"] = _filters_schema(spec.resource)
        properties.update(_date_properties())
        properties["time_segment"] = _enum("Optional report time segment.", TIME_SEGMENTS)
        properties.update(_row_cap_properties())
        return _object_schema(properties, required)

    if spec.mode == "raw_gaql":
        properties["payload"] = _object_schema(
            {
                "query": _string("GAQL query to execute."),
                "primary_field": _string("Optional primary field used to key or flatten rows."),
            },
            ["query"],
        )
        properties.update(_row_cap_properties())
        required.append("payload")
        return _object_schema(properties, required)

    if spec.mode == "negative_keyword" and spec.name.startswith("list_"):
        properties["payload"] = _negative_keyword_query_payload_schema(spec.name)
        properties["filters"] = _filters_schema(spec.resource)
        properties.update(_row_cap_properties())
        return _object_schema(properties, required)

    if spec.mode == "service":
        properties["payload"] = _service_payload_schema(spec.name)
        if spec.name in {"list_linked_accounts", "get_account_budget", "get_billing_setup"}:
            properties.update(_row_cap_properties(include_page_token=False))
        if _payload_is_required(spec.name):
            required.append("payload")
        return _object_schema(properties, required)

    if spec.mode == "mutate" or spec.mode == "negative_keyword":
        properties["payload"] = _mutation_payload_schema(spec.name)
        properties.update(_write_safety_properties())
        required.append("payload")
        return _object_schema(properties, required)

    properties["payload"] = _open_object("Optional payload for this friendly tool.")
    return _object_schema(properties, required)


def _query_payload_schema(spec: Any) -> dict[str, Any]:
    properties = {
        "id": _string(f"Optional {spec.primary_field or 'resource'} identifier."),
        "resource_id": _string(f"Optional {spec.primary_field or 'resource'} identifier."),
        "resource_name": _string("Full Google Ads resource name."),
        "fields": _string_array("Override the default selected GAQL fields."),
    }
    if spec.name == "list_customers":
        properties["include_managers"] = _boolean("Include manager accounts in list_customers results.")
    return _object_schema(properties)


def _negative_keyword_query_payload_schema(name: str) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    if name == "list_negative_keywords_ad_group":
        properties["ad_group_id"] = _string("Restrict results to one ad group id.")
    elif name == "list_negative_keywords_campaign":
        properties["campaign_id"] = _string("Restrict results to one campaign id.")
    return _object_schema(properties)


def _service_payload_schema(name: str) -> dict[str, Any]:
    if name == "list_invoices":
        return _object_schema(
            {
                "billing_setup": _string("Billing setup resource name returned by get_billing_setup."),
                "issue_year": _string("Invoice issue year. Defaults to the current year."),
                "issue_month": _enum(
                    "Invoice issue month.",
                    (
                        "JANUARY",
                        "FEBRUARY",
                        "MARCH",
                        "APRIL",
                        "MAY",
                        "JUNE",
                        "JULY",
                        "AUGUST",
                        "SEPTEMBER",
                        "OCTOBER",
                        "NOVEMBER",
                        "DECEMBER",
                    ),
                    default="JANUARY",
                ),
            },
            ["billing_setup"],
        )
    if name == "get_keyword_ideas":
        return _object_schema(
            {
                "keywords": _string_array("Seed keywords."),
                "url": _string("Seed URL."),
                "language": _string("Language constant resource name."),
                "geo_target_constants": _string_array("Geo target constant resource names."),
                "include_adult_keywords": _boolean("Include adult keyword ideas.", default=False),
                "page_size": _integer("Keyword idea page size.", minimum=1),
            }
        )
    if name == "get_reach_forecast":
        return _object_schema(
            {
                "method_name": _string("ReachPlanService method name."),
                "request_type": _string("ReachPlanService request protobuf type."),
                "request": _open_object("ReachPlanService request payload."),
            }
        )
    return _open_object("Payload for this Google Ads service helper.")


def _mutation_payload_schema(name: str) -> dict[str, Any]:
    if name == "create_responsive_search_ad":
        text_asset = {
            "anyOf": [
                {"type": "string"},
                _object_schema({"text": _string("Asset text."), "pinned_field": _string("Optional pin.")}),
            ]
        }
        return _object_schema(
            {
                "ad_group_id": _string("Ad group id that will receive the ad."),
                "final_urls": _array("Final URLs for the ad.", {"type": "string"}, min_items=1),
                "headlines": _array("Responsive search ad headlines.", text_asset, min_items=3),
                "descriptions": _array("Responsive search ad descriptions.", text_asset, min_items=2),
                "path1": _string("Optional display URL path 1."),
                "path2": _string("Optional display URL path 2."),
                "status": _enum("Initial ad status.", ("PAUSED", "ENABLED"), default="PAUSED"),
            },
            ["ad_group_id", "final_urls", "headlines", "descriptions"],
        )
    if name in CAMPAIGN_STATUS_TOOLS or name == "remove_campaign":
        return _object_schema({"campaign_id": _string("Campaign id.")}, ["campaign_id"])
    if name in CAMPAIGN_BULK_STATUS_TOOLS:
        return _object_schema({"ids": _string_array("Campaign ids.")}, ["ids"])
    if name in AD_GROUP_STATUS_TOOLS or name == "remove_ad_group":
        return _object_schema({"ad_group_id": _string("Ad group id.")}, ["ad_group_id"])
    if name in AD_STATUS_TOOLS or name == "remove_ad":
        return _object_schema(
            {
                "ad_group_id": _string("Ad group id."),
                "ad_id": _string("Ad id."),
                "resource_name": _string("Full ad group ad resource name."),
            }
        )
    if name in KEYWORD_STATUS_TOOLS or name == "remove_keywords":
        return _object_schema(
            {
                "ad_group_id": _string("Ad group id."),
                "criterion_ids": _string_array("Keyword criterion ids."),
            },
            ["ad_group_id", "criterion_ids"],
        )
    if name in KEYWORD_CREATE_TOOLS:
        return _object_schema(
            {
                "ad_group_id": _string("Ad group id."),
                "keywords": _keyword_items_schema(),
            },
            ["ad_group_id", "keywords"],
        )
    if name in BUDGET_CREATE_TOOLS:
        return _object_schema(
            {
                "name": _string("Budget name."),
                "amount_micros": _integer("Budget amount in micros.", minimum=1),
                "daily_budget_micros": _integer("Daily budget amount in micros.", minimum=1),
                "delivery_method": _enum("Budget delivery method.", ("STANDARD", "ACCELERATED")),
            },
            ["name"],
        )
    if name in BUDGET_UPDATE_TOOLS:
        return _object_schema(
            {
                "budget_id": _string("Campaign budget id."),
                "name": _string("New budget name."),
                "amount_micros": _integer("Budget amount in micros.", minimum=1),
                "daily_budget_micros": _integer("Daily budget amount in micros.", minimum=1),
            },
            ["budget_id"],
        )
    if name == "batch_mutate":
        return _object_schema(
            {"operations": _array("GoogleAdsService MutateOperation objects.", {"type": "object"})},
            ["operations"],
        )
    if name in CAMPAIGN_CREATE_TOOLS:
        return _object_schema(
            {
                "name": _string("Campaign name."),
                "budget_id": _string("Existing campaign budget id."),
                "budget_name": _string("Name for a temporary budget operation."),
                "amount_micros": _integer("Budget amount in micros.", minimum=1),
                "status": _enum("Initial campaign status.", ("PAUSED", "ENABLED", "REMOVED"), default="PAUSED"),
            },
            ["name"],
        )
    if name in DIRECT_MUTATION_TOOLS:
        return _open_object("Payload for this direct Google Ads mutation helper.")
    return _object_schema(
        {"operations": _array("GoogleAdsService MutateOperation objects.", {"type": "object"})},
        ["operations"],
    )


def _payload_is_required(name: str) -> bool:
    return name in {"list_invoices", "get_keyword_ideas", "get_reach_forecast"}


def _date_properties() -> dict[str, Any]:
    return {
        "date_range": _string(
            "GAQL DURING date range token. Use CUSTOM_DATE with start_date and end_date.",
            default=DEFAULT_DATE_RANGE,
        ),
        "start_date": _string("Custom start date in YYYY-MM-DD format."),
        "end_date": _string("Custom end date in YYYY-MM-DD format."),
    }


def _row_cap_properties(*, include_page_token: bool = True) -> dict[str, Any]:
    properties = {
        "max_rows": _integer("Total returned row cap. Replaces deprecated page_size.", default=1000, minimum=1),
        "page_size": {
            **_integer("Deprecated alias for max_rows; this is not a page length.", minimum=1),
            "deprecated": True,
        },
    }
    if include_page_token:
        properties["page_token"] = _string(
            "Legacy Google Ads page token. Only useful when no MCP row cap is injected."
        )
    return properties


def _hierarchy_cap_properties() -> dict[str, Any]:
    return {
        "max_accounts": _integer("Total child accounts to collect across recursive traversal.", minimum=1),
        "page_size": {
            **_integer("Deprecated alias for max_accounts on get_mcc_hierarchy.", minimum=1),
            "deprecated": True,
        },
        "page_token": _string("First-page Google Ads page token for the root manager query."),
    }


def _write_safety_properties(*, partial_failure: bool = True) -> dict[str, Any]:
    properties = {
        "validate_only": _boolean("Validate the mutation without applying it.", default=True),
        "execute": _boolean("Set true only when real writes are intentionally allowed.", default=False),
        "confirmation_phrase": _string("Required confirmation phrase for real writes."),
    }
    if partial_failure:
        properties["partial_failure"] = _boolean("Allow partial failure in mutate requests.", default=False)
    return properties


def _customer_id_schema() -> dict[str, Any]:
    return _string("Google Ads customer id, without dashes.")


def _filters_schema(resource: str | None = None) -> dict[str, Any]:
    description = "GAQL field filters."
    if resource:
        description += f" Fields should be filterable on {resource}."
    return _open_object(description)


def _keyword_items_schema() -> dict[str, Any]:
    return _array(
        "Keyword strings or keyword objects.",
        {
            "anyOf": [
                {"type": "string"},
                _object_schema(
                    {
                        "text": _string("Keyword text."),
                        "match_type": _enum("Keyword match type.", ("EXACT", "PHRASE", "BROAD")),
                        "status": _enum("Keyword status.", ("ENABLED", "PAUSED")),
                    },
                    ["text"],
                ),
            ]
        },
        min_items=1,
    )


def _object_schema(
    properties: dict[str, Any],
    required: list[str] | tuple[str, ...] = (),
    *,
    description: str | None = None,
    additional_properties: bool = False,
) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": deepcopy(properties),
        "additionalProperties": additional_properties,
    }
    if required:
        schema["required"] = list(required)
    if description:
        schema["description"] = description
    return schema


def _open_object(description: str) -> dict[str, Any]:
    return _object_schema({}, description=description, additional_properties=True)


def _string(description: str, *, default: str | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string", "description": description}
    if default is not None:
        schema["default"] = default
    return schema


def _integer(description: str, *, default: int | None = None, minimum: int | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "integer", "description": description}
    if default is not None:
        schema["default"] = default
    if minimum is not None:
        schema["minimum"] = minimum
    return schema


def _boolean(description: str, *, default: bool | None = None) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "boolean", "description": description}
    if default is not None:
        schema["default"] = default
    return schema


def _array(
    description: str,
    items: dict[str, Any],
    *,
    min_items: int | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "array", "description": description, "items": deepcopy(items)}
    if min_items is not None:
        schema["minItems"] = min_items
    return schema


def _string_array(description: str) -> dict[str, Any]:
    return _array(description, {"type": "string"})


def _enum(
    description: str,
    values: tuple[str, ...],
    *,
    default: str | None = None,
) -> dict[str, Any]:
    schema: dict[str, Any] = {"type": "string", "enum": list(values), "description": description}
    if default is not None:
        schema["default"] = default
    return schema
