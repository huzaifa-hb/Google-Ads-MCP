"""Shared validation and write-safety helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Any


CONFIRMATION_PHRASE = "CONFIRM_GOOGLE_ADS_WRITE"
CUSTOMER_ID_RE = re.compile(r"^\d{3,}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ValidationError(ValueError):
    """Raised when caller input is not valid enough to send to Google Ads."""


@dataclass(frozen=True)
class WriteDecision:
    """Normalized write gate result."""

    validate_only: bool
    execute: bool
    allowed: bool
    reason: str


def normalize_customer_id(customer_id: str | int) -> str:
    value = str(customer_id).replace("-", "").strip()
    if not CUSTOMER_ID_RE.match(value):
        raise ValidationError("customer_id must contain digits only, with no dashes.")
    return value


def require_leaf_customer(customer_id: str | int, is_manager: bool | None = None) -> str:
    normalized = normalize_customer_id(customer_id)
    if is_manager is True:
        raise ValidationError(
            "This operation requires a leaf customer account. Manager/MCC accounts cannot "
            "run leaf-only metric or mutate operations."
        )
    return normalized


def evaluate_write_gate(
    *,
    validate_only: bool = True,
    execute: bool = False,
    confirmation_phrase: str | None = None,
) -> WriteDecision:
    if validate_only and not execute:
        return WriteDecision(
            validate_only=True,
            execute=False,
            allowed=True,
            reason="Validation-only request. No external write will be committed.",
        )
    if execute and confirmation_phrase == CONFIRMATION_PHRASE:
        return WriteDecision(
            validate_only=False,
            execute=True,
            allowed=True,
            reason="Explicit Google Ads write confirmation accepted.",
        )
    return WriteDecision(
        validate_only=True,
        execute=False,
        allowed=False,
        reason=(
            f"Real writes require execute=true and confirmation_phrase='{CONFIRMATION_PHRASE}'. "
            "Call again with validate_only=true to preview without committing."
        ),
    )


def ensure_write_allowed(
    *,
    validate_only: bool = True,
    execute: bool = False,
    confirmation_phrase: str | None = None,
) -> bool:
    decision = evaluate_write_gate(
        validate_only=validate_only,
        execute=execute,
        confirmation_phrase=confirmation_phrase,
    )
    if not decision.allowed:
        raise ValidationError(decision.reason)
    return decision.validate_only


def validate_date(value: str, field_name: str) -> str:
    if not DATE_RE.match(value):
        raise ValidationError(f"{field_name} must be YYYY-MM-DD.")
    try:
        date.fromisoformat(value)
    except ValueError as exc:
        raise ValidationError(f"{field_name} must be a real calendar date.") from exc
    return value


def redact_sensitive(value: Any) -> Any:
    """Return a copy with obvious secrets hidden for logs and error payloads."""

    if isinstance(value, dict):
        redacted: dict[str, Any] = {}
        for key, item in value.items():
            lowered = key.lower()
            if any(token in lowered for token in ("secret", "token", "refresh", "password", "key")):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value

