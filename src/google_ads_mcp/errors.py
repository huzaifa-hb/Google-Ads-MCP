"""Shared error formatting helpers for MCP tool responses and logs."""

from __future__ import annotations

import re
from typing import Any

from .safety import ValidationError, redact_sensitive


QUOTA_OR_RATE_RE = re.compile(
    r"\b(resource[_ ]exhausted|rate[_ -]?exceeded|rate[_ -]?limit|quota)\b",
    flags=re.IGNORECASE,
)
TRANSIENT_STATUS_RE = re.compile(
    r"\b(?:RESOURCE_EXHAUSTED|UNAVAILABLE|DEADLINE_EXCEEDED|INTERNAL)\b"
)


def is_quota_or_rate_error(message: str) -> bool:
    return bool(QUOTA_OR_RATE_RE.search(message or ""))


def is_transient_google_ads_error(exc: Exception | str) -> bool:
    message = str(exc)
    return bool(TRANSIENT_STATUS_RE.search(message) or is_quota_or_rate_error(message))


def format_validation_error(exc: ValidationError) -> dict[str, Any]:
    return {
        "ok": False,
        "error_type": "ValidationError",
        "message": str(exc),
        "suggested_fix": "Fix the request shape or field values, then retry.",
    }


def format_tool_error(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, ValidationError):
        return format_validation_error(exc)
    google_error = format_google_ads_exception(exc)
    if google_error["error_type"] != "GoogleAdsException":
        return {
            "ok": False,
            "error_type": exc.__class__.__name__,
            "message": str(exc),
            "suggested_fix": _suggested_fix(str(exc)),
        }
    return google_error


def format_google_ads_exception(exc: Exception) -> dict[str, Any]:
    request_id = getattr(exc, "request_id", None)
    failure = getattr(exc, "failure", None)
    errors = []
    if failure is not None:
        errors = [_format_google_ads_error(error) for error in getattr(failure, "errors", [])]

    if request_id or errors:
        message = str(exc)
        return {
            "ok": False,
            "error_type": "GoogleAdsException",
            "request_id": request_id,
            "message": message,
            "google_ads_errors": errors,
            "suggested_fix": _suggested_fix(message, errors),
        }

    return {
        "ok": False,
        "error_type": exc.__class__.__name__,
        "message": str(exc),
        "request_id": None,
        "google_ads_errors": [],
        "suggested_fix": _suggested_fix(str(exc)),
    }


def _format_google_ads_error(error: Any) -> dict[str, Any]:
    code = getattr(error, "error_code", None)
    if code is not None:
        code = _message_to_plain(code)
    field_path = getattr(error, "location", None)
    return {
        "code": code,
        "message": redact_sensitive(getattr(error, "message", "")),
        "field_path": _field_path(field_path),
    }


def _field_path(location: Any) -> str:
    if location is None:
        return ""
    elements = getattr(location, "field_path_elements", []) or []
    names = []
    for element in elements:
        field_name = getattr(element, "field_name", "")
        index = getattr(element, "index", None)
        if index is not None:
            names.append(f"{field_name}[{index}]")
        elif field_name:
            names.append(field_name)
    return ".".join(names)


def _message_to_plain(value: Any) -> str:
    text = str(value)
    return " ".join(text.split())


def _suggested_fix(message: str, errors: list[dict[str, Any]] | None = None) -> str:
    text = " ".join([message] + [str(error.get("code", "")) for error in errors or []]).lower()
    if "missing required google ads environment values" in text:
        return "Run google-ads-mcp setup or check /readyz to see which required environment values are missing."
    if "expected_referenced_field_in_select_clause" in text:
        return "Add the primary field for the GAQL resource to SELECT."
    if "invalid_field" in text or "unrecognized field" in text:
        return "Validate fields with metadata_validate_gaql_fields before retrying."
    if "field_not_selectable" in text or "field_not_filterable" in text:
        return "Check live metadata for selectable and filterable fields."
    if is_quota_or_rate_error(text):
        return "Reduce request volume, use pagination, and retry later."
    if "permission" in text or "authorization" in text:
        return (
            "Check the OAuth user and developer-token access level. If this is a child "
            "account under an MCC, pass login_customer_id=<manager id> or set "
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID."
        )
    return "Review the request and retry with validation-only mode first for writes."
