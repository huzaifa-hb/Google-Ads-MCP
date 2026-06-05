"""GAQL helpers used by generic and friendly tools."""

from __future__ import annotations

from dataclasses import dataclass
from difflib import get_close_matches
import re
from typing import Iterable

from .safety import ValidationError, validate_date


GAQL_FIELD_RE = re.compile(r"^[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+$")
GAQL_RESOURCE_RE = re.compile(r"^[a-z][a-z0-9_]*$")

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
    page_size: int = 1000
    offset: int | None = None
    page_token: str | None = None


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


def apply_pagination(query: str, pagination: Pagination) -> str:
    if pagination.offset is None:
        return query
    if " limit " in query.lower():
        return query
    # Fetch one extra row in offset mode so callers get a reliable has_more value.
    limit_clause = f"LIMIT {pagination.page_size + 1} OFFSET {pagination.offset}"
    parameters_index = query.lower().find(" parameters ")
    if parameters_index >= 0:
        return f"{query[:parameters_index]} {limit_clause}{query[parameters_index:]}"
    return f"{query} {limit_clause}"


def apply_default_parameters(query: str) -> str:
    if " parameters " in f" {query.lower()} ":
        return query
    return f"{query} PARAMETERS omit_unselected_resource_names = true"


def trim_offset_page(rows: list[dict], page_size: int, offset: int | None = None) -> list[dict]:
    if offset is None:
        return rows
    return rows[:page_size]


def summarize_page(
    rows: list[dict],
    page_size: int,
    page_token: str | None = None,
    offset: int | None = None,
    fetched_count: int | None = None,
) -> dict:
    fetched = len(rows) if fetched_count is None else fetched_count
    has_more = bool(page_token) or (offset is not None and fetched > page_size)
    return {
        "row_count": len(rows),
        "has_more": has_more,
        "next_offset": (offset or 0) + len(rows) if has_more and not page_token else None,
        "next_page_token": page_token,
    }


def suggest_fields(field: str, candidates: Iterable[str], limit: int = 5) -> list[str]:
    return get_close_matches(field, sorted(set(candidates)), n=limit, cutoff=0.45)


def explain_gaql_error(error_text: str) -> dict[str, object]:
    text = error_text or ""
    lowered = text.lower()
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
    if "resource_exhausted" in lowered or "quota" in lowered or "rate" in lowered:
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
