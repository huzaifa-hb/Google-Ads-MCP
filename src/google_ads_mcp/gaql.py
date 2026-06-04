"""GAQL helpers used by generic and friendly tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from .safety import ValidationError, validate_date


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
    return f"{query} LIMIT {pagination.page_size + 1} OFFSET {pagination.offset}"


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
