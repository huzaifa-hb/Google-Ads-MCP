"""GAQL helpers used by generic and friendly tools."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
import re
from typing import Any, Iterable

from .safety import ValidationError, validate_date


GAQL_FIELD_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
GAQL_RESOURCE_RE = re.compile(r"^[a-z][a-z0-9_]*$")
QUOTA_OR_RATE_RE = re.compile(
    r"\b(resource[_ ]exhausted|rate[_ -]?exceeded|rate[_ -]?limit|quota)\b",
    flags=re.IGNORECASE,
)
SIGNED_INTEGER_RE = re.compile(r"^[+-]?\d+$")
SIGNED_NUMBER_RE = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")
ALLOWED_FILTER_OPERATORS = {"=", "!=", ">", ">=", "<", "<=", "LIKE", "IN", "NOT IN"}

PRESET_DATE_RANGES = {
    "TODAY",
    "YESTERDAY",
    "LAST_7_DAYS",
    "LAST_14_DAYS",
    "LAST_30_DAYS",
    "LAST_90_DAYS",
    "THIS_MONTH",
    "LAST_MONTH",
    "ALL_TIME",
}

TIME_SEGMENTS = {
    "day": "segments.date",
    "week": "segments.week",
    "month": "segments.month",
    "hour": "segments.hour",
}


def normalize_resource_name(resource_name: str) -> str:
    resource = (resource_name or "").strip().lower()
    if not GAQL_RESOURCE_RE.fullmatch(resource):
        raise ValidationError(
            "resource_name must be a Google Ads resource identifier like 'campaign' or 'ad_group'."
        )
    return resource


def normalize_field_name(field: str) -> str:
    value = (field or "").strip()
    if not GAQL_FIELD_RE.fullmatch(value):
        raise ValidationError(f"Invalid GAQL field name '{field}'.")
    return value


def normalize_field_list(fields: Iterable[str] | str | None) -> list[str]:
    if fields is None:
        return []
    if isinstance(fields, str):
        raw_fields = fields.split(",")
    else:
        raw_fields = fields
    clean: list[str] = []
    for field in raw_fields:
        value = str(field or "").strip()
        if value:
            clean.append(value)
    return list(dict.fromkeys(clean))


@dataclass(frozen=True)
class Pagination:
    max_rows: int | None = None
    page_size: int | None = None
    page_token: str | None = None


@dataclass(frozen=True)
class AppliedPagination:
    query: str
    effective_limit: int | None
    limit_injected: bool
    page_size_deprecated: bool
    existing_limit: int | None


def date_where_clause(
    *,
    date_range: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    field: str = "segments.date",
) -> str:
    if start_date or end_date:
        if not start_date or not end_date:
            raise ValidationError("Both start_date and end_date are required for a custom range.")
        start = validate_date(start_date, "start_date")
        end = validate_date(end_date, "end_date")
        if field.endswith("_date_time"):
            return f"{field} BETWEEN '{start} 00:00:00' AND '{end} 23:59:59'"
        return f"{field} BETWEEN '{start}' AND '{end}'"

    selected = (date_range or "LAST_30_DAYS").upper()
    if selected == "ALL_TIME":
        return ""
    if selected not in PRESET_DATE_RANGES:
        allowed = ", ".join(sorted(PRESET_DATE_RANGES))
        raise ValidationError(f"Unknown date_range '{date_range}'. Allowed: {allowed}.")
    return f"{field} DURING {selected}"


def select_clause(fields: Iterable[str]) -> str:
    clean = [field.strip() for field in fields if field and field.strip()]
    if not clean:
        raise ValidationError("At least one GAQL field is required.")
    return "SELECT " + ", ".join(dict.fromkeys(clean))


def ensure_primary_field(query: str, primary_field: str) -> None:
    """Catch a common GAQL error before sending the request.

    Google Ads often requires the primary resource id to be present in SELECT when
    related fields are referenced. This helper intentionally gives a clearer error
    than the raw EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE response.
    """

    normalized_query = " ".join(query.lower().split())
    normalized_primary = primary_field.lower()
    if "select " not in normalized_query or " from " not in normalized_query:
        raise ValidationError("GAQL query must contain SELECT and FROM clauses.")
    select_part = normalized_query.split(" from ", 1)[0].replace("select ", "", 1)
    fields = {field.strip() for field in select_part.split(",")}
    if normalized_primary not in fields:
        raise ValidationError(
            f"GAQL SELECT must include primary resource field '{primary_field}' to avoid "
            "EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE."
        )


def _query_without_string_literals(query: str) -> str:
    return re.sub(r"'(?:\\.|''|[^'\\])*'", "''", query)


def ensure_no_offset_clause(query: str) -> None:
    scrubbed = _query_without_string_literals(query)
    if re.search(r"\boffset\b", scrubbed, flags=re.IGNORECASE):
        raise ValidationError(
            "GAQL does not support OFFSET. Use pagination.next_page_token as page_token "
            "to fetch the next page."
        )


def apply_pagination(query: str, pagination: Pagination) -> str:
    return apply_pagination_plan(query, pagination).query


def apply_pagination_plan(query: str, pagination: Pagination) -> AppliedPagination:
    ensure_no_offset_clause(query)
    effective_limit, page_size_deprecated = _effective_max_rows(pagination)
    existing_limit = _existing_limit(query)
    is_change_event = _uses_resource(query, "change_event")

    if existing_limit is not None:
        effective_limit = existing_limit
    elif effective_limit is not None:
        if pagination.page_token:
            raise ValidationError(
                "page_token cannot be combined with MCP-injected max_rows. "
                "Use max_rows=None or a GAQL LIMIT of at least 10000 when paging."
            )
        query = _inject_limit(query, effective_limit)
    if pagination.page_token and existing_limit is not None and existing_limit < 10_000:
        raise ValidationError(
            "page_token is supported only with a user GAQL LIMIT of at least 10000 "
            "or with max_rows=None."
        )
    if is_change_event:
        if effective_limit is None:
            raise ValidationError("change_event queries require a finite LIMIT.")
        if effective_limit > 10_000:
            raise ValidationError("change_event LIMIT must be 10,000 or less.")
    return AppliedPagination(
        query=query,
        effective_limit=effective_limit,
        limit_injected=existing_limit is None and effective_limit is not None,
        page_size_deprecated=page_size_deprecated,
        existing_limit=existing_limit,
    )


def _effective_max_rows(pagination: Pagination) -> tuple[int | None, bool]:
    page_size_deprecated = pagination.page_size is not None
    if pagination.max_rows is not None and pagination.max_rows < 1:
        raise ValidationError("max_rows must be at least 1.")
    if pagination.page_size is not None and pagination.page_size < 1:
        raise ValidationError("page_size must be at least 1.")
    if pagination.max_rows is None:
        return pagination.page_size, page_size_deprecated
    if pagination.page_size is not None and pagination.page_size != pagination.max_rows:
        raise ValidationError("Use max_rows instead of page_size; do not set both.")
    return pagination.max_rows, page_size_deprecated


def _existing_limit(query: str) -> int | None:
    scrubbed = _query_without_string_literals(query)
    match = re.search(r"\blimit\s+(\d+)\b", scrubbed, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def _uses_resource(query: str, resource: str) -> bool:
    scrubbed = _query_without_string_literals(query)
    return bool(re.search(rf"\bfrom\s+{re.escape(resource)}\b", scrubbed, flags=re.IGNORECASE))


def _inject_limit(query: str, max_rows: int) -> str:
    parameters_index = _find_keyword_outside_string(query, "PARAMETERS")
    if parameters_index is None:
        return f"{query} LIMIT {max_rows}"
    before = query[:parameters_index].rstrip()
    after = query[parameters_index:].lstrip()
    return f"{before} LIMIT {max_rows} {after}"


def _find_keyword_outside_string(query: str, keyword: str) -> int | None:
    keyword_lower = keyword.lower()
    in_string = False
    index = 0
    while index < len(query):
        char = query[index]
        if char == "'" and (index == 0 or query[index - 1] != "\\"):
            in_string = not in_string
            index += 1
            continue
        if not in_string and query[index : index + len(keyword)].lower() == keyword_lower:
            before = query[index - 1] if index > 0 else " "
            after_index = index + len(keyword)
            after = query[after_index] if after_index < len(query) else " "
            if not (before.isalnum() or before == "_") and not (after.isalnum() or after == "_"):
                return index
        index += 1
    return None


def apply_default_parameters(query: str) -> str:
    scrubbed = _query_without_string_literals(query)
    if re.search(r"\bparameters\b", scrubbed, flags=re.IGNORECASE):
        return query
    return f"{query} PARAMETERS omit_unselected_resource_names = true"


def gaql_literal(value: object, data_type: str = "") -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"
    normalized_type = data_type.upper()
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return str(value)
    text = str(value)
    if normalized_type in {"INT32", "INT64", "UINT64", "DOUBLE", "FLOAT"}:
        number_text = text.strip()
        if normalized_type == "UINT64" and number_text.isdigit():
            return number_text
        if normalized_type in {"INT32", "INT64"} and SIGNED_INTEGER_RE.fullmatch(
            number_text
        ):
            return number_text
        if normalized_type in {"DOUBLE", "FLOAT"} and SIGNED_NUMBER_RE.fullmatch(number_text):
            return number_text
    if normalized_type == "ENUM":
        enum_text = text.strip().upper()
        if enum_text.replace("_", "").isalnum():
            return enum_text
    escaped = text.replace("\\", "\\\\").replace("'", "\\'")
    return f"'{escaped}'"


def gaql_filter_clause(field_name: str, raw_value: Any, data_type: str = "") -> str | None:
    if isinstance(raw_value, dict):
        operator = str(raw_value.get("operator", "=")).strip().upper()
        value = raw_value.get("value")
    elif isinstance(raw_value, (list, tuple, set)):
        operator = "IN"
        value = raw_value
    else:
        operator = "="
        value = raw_value
    if operator not in ALLOWED_FILTER_OPERATORS:
        raise ValidationError(f"Unsupported GAQL filter operator '{operator}'.")
    if value is None:
        return None
    if operator in {"IN", "NOT IN"}:
        values = value if isinstance(value, (list, tuple, set)) else [value]
        return (
            f"{field_name} {operator} "
            f"({', '.join(gaql_literal(item, data_type) for item in values)})"
        )
    return f"{field_name} {operator} {gaql_literal(value, data_type)}"


def summarize_page(
    rows: list[dict],
    requested_max_rows: int | None,
    page_token: str | None = None,
    fetched_count: int | None = None,
    *,
    effective_limit: int | None = None,
    limit_injected: bool = False,
    page_size_deprecated: bool = False,
) -> dict:
    reached_injected_limit = bool(
        limit_injected and effective_limit is not None and len(rows) >= effective_limit
    )
    has_more: bool | str = "unknown_when_limit_reached" if reached_injected_limit else bool(page_token)
    return {
        "row_count": len(rows),
        "fetched_count": fetched_count if fetched_count is not None else len(rows),
        "has_more": has_more,
        "next_page_token": None if reached_injected_limit else page_token,
        "requested_max_rows": requested_max_rows,
        "requested_page_size": requested_max_rows,
        "google_ads_fixed_page_size": 10_000,
        "limit_injected": limit_injected,
        "effective_limit": effective_limit,
        "pagination_deprecated": page_size_deprecated,
    }


def suggest_fields(field: str, candidates: Iterable[str], limit: int = 5) -> list[str]:
    return get_close_matches(field, sorted(set(candidates)), n=limit, cutoff=0.45)


def explain_gaql_error(error_text: str) -> dict[str, object]:
    text = error_text or ""
    lowered = text.lower()
    if "page_size_not_supported" in lowered or "setting the page size is not supported" in lowered:
        return {
            "ok": True,
            "error_type": "PAGE_SIZE_NOT_SUPPORTED",
            "explanation": "Google Ads Search uses a fixed 10,000-row page size.",
            "suggested_fix": (
                "Do not set SearchGoogleAdsRequest.page_size. Use next_page_token/page_token "
                "for pages after the first, and use GAQL LIMIT only to cap the total result set."
            ),
            "related_tools": ["google_ads_search"],
        }
    if "offset" in lowered:
        return {
            "ok": True,
            "error_type": "UNSUPPORTED_OFFSET",
            "explanation": "GAQL does not support OFFSET-based pagination.",
            "suggested_fix": "Use pagination.next_page_token as page_token to fetch the next page.",
            "related_tools": ["google_ads_search", "google_ads_search_stream"],
        }
    if "expected_referenced_field_in_select_clause" in lowered:
        return {
            "ok": True,
            "error_type": "EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE",
            "explanation": "The query references a resource but does not select its primary field.",
            "suggested_fix": (
                "Add the primary field for the resource, such as campaign.id for FROM campaign."
            ),
            "related_tools": ["metadata_get_google_ads_resource_metadata", "planning_plan_gaql_query"],
        }
    if "invalid_field_name" in lowered or "unrecognized field" in lowered:
        return {
            "ok": True,
            "error_type": "INVALID_FIELD_NAME",
            "explanation": "At least one GAQL field does not exist in this Google Ads API version.",
            "suggested_fix": "Call validate_gaql_fields or get_google_ads_resource_metadata for the resource.",
            "related_tools": ["metadata_validate_gaql_fields", "metadata_suggest_gaql_fields"],
        }
    if "prohibited_segment_with_metric_in_select_or_where_clause" in lowered:
        return {
            "ok": True,
            "error_type": "SEGMENT_METRIC_INCOMPATIBILITY",
            "explanation": "The selected segment cannot be combined with one or more metrics.",
            "suggested_fix": "Call planning_plan_gaql_query with the desired metrics and segments.",
            "related_tools": ["planning_plan_gaql_query"],
        }
    if "date_range_too_wide" in lowered or "change_event" in lowered:
        return {
            "ok": True,
            "error_type": "DATE_RANGE_LIMIT",
            "explanation": "Some Google Ads resources, especially change_event, require narrow date ranges.",
            "suggested_fix": "Use a preset like LAST_14_DAYS or a custom range within the resource limits.",
            "related_tools": ["reporting_execute_gaql_query"],
        }
    if "field_not_selectable" in lowered:
        return {
            "ok": True,
            "error_type": "FIELD_NOT_SELECTABLE",
            "explanation": "The field exists but cannot be used in the SELECT clause.",
            "suggested_fix": "Choose a selectable field from get_google_ads_resource_metadata.",
            "related_tools": ["metadata_get_google_ads_resource_metadata"],
        }
    if "prohibited_field_combination" in lowered:
        return {
            "ok": True,
            "error_type": "PROHIBITED_FIELD_COMBINATION",
            "explanation": "The query combines incompatible resources, metrics, or segments.",
            "suggested_fix": "Plan the query again with fewer metrics or segments, then add fields gradually.",
            "related_tools": ["planning_plan_gaql_query"],
        }
    if QUOTA_OR_RATE_RE.search(error_text):
        return {
            "ok": True,
            "error_type": "QUOTA_OR_RATE_LIMIT",
            "explanation": "The request hit Google Ads quota or rate limits.",
            "suggested_fix": "Reduce request volume, use pagination, and retry later.",
            "related_tools": ["metadata_query_google_ads_docs"],
        }
    return {
        "ok": True,
        "error_type": "UNKNOWN_GAQL_ERROR",
        "explanation": "The error was not recognized by the built-in GAQL helper.",
        "suggested_fix": "Use query_google_ads_docs and live metadata to validate fields before retrying.",
        "related_tools": ["metadata_query_google_ads_docs", "metadata_get_google_ads_resource_metadata"],
    }
