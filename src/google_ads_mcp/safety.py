"""Shared validation and write-safety helpers."""

from __future__ import annotations

import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from collections.abc import Callable
from typing import Any


CONFIRMATION_PHRASE = "CONFIRM_GOOGLE_ADS_WRITE"
CUSTOMER_ID_RE = re.compile(r"^\d{3,}$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WRITE_MODES = {"safe_read_only", "validation_only", "write_enabled", "admin_debug"}
AUDIT_LOGGER = logging.getLogger("google_ads_mcp.audit")


class ValidationError(ValueError):
    """Raised when caller input is not valid enough to send to Google Ads."""


@dataclass(frozen=True)
class WriteDecision:
    """Normalized write gate result."""

    validate_only: bool
    execute: bool
    allowed: bool
    reason: str
    mode: str = "write_enabled"
    forced_validation: bool = False


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
    if execute and validate_only is False and confirmation_phrase == CONFIRMATION_PHRASE:
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
            "Real writes require validate_only=false, execute=true, and "
            f"confirmation_phrase='{CONFIRMATION_PHRASE}'. "
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


def guard_google_ads_write(
    *,
    mode: str,
    tool_name: str,
    customer_id: str | int,
    validate_only: bool = True,
    execute: bool = False,
    confirmation_phrase: str | None = None,
    operation_type: str | None = None,
    operation_count: int | None = None,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
) -> WriteDecision:
    """Enforce mode-aware write safety and emit a redacted audit event."""

    normalized_customer_id = normalize_customer_id(customer_id)
    if mode not in WRITE_MODES:
        raise ValidationError(f"Unknown Google Ads MCP mode '{mode}'.")

    if mode == "safe_read_only":
        decision = WriteDecision(
            validate_only=True,
            execute=False,
            allowed=False,
            reason="Google Ads writes are disabled in safe_read_only mode.",
            mode=mode,
        )
    elif mode == "validation_only":
        decision = WriteDecision(
            validate_only=True,
            execute=False,
            allowed=True,
            reason="Validation-only mode forces all Google Ads writes to validate_only=true.",
            mode=mode,
            forced_validation=bool(execute or not validate_only),
        )
    else:
        base_decision = evaluate_write_gate(
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
        )
        decision = WriteDecision(
            validate_only=base_decision.validate_only,
            execute=base_decision.execute,
            allowed=base_decision.allowed,
            reason=base_decision.reason,
            mode=mode,
        )

    emit_write_audit_event(
        {
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "tool": tool_name,
            "customer_id_hash": hash_customer_id(normalized_customer_id),
            "operation_type": operation_type or tool_name,
            "operation_count": operation_count,
            "mode": mode,
            "validate_only": decision.validate_only,
            "execute": decision.execute,
            "confirmed": decision.allowed and decision.execute and not decision.validate_only,
            "validation_forced": decision.forced_validation,
            "result": _audit_result(decision),
            "reason": decision.reason,
        },
        audit_sink=audit_sink,
    )
    if not decision.allowed:
        raise ValidationError(decision.reason)
    return decision


def hash_customer_id(customer_id: str | int) -> str:
    normalized = normalize_customer_id(customer_id)
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def emit_write_audit_event(
    event: dict[str, Any],
    *,
    audit_sink: Callable[[dict[str, Any]], None] | None = None,
) -> None:
    if audit_sink is not None:
        audit_sink(dict(event))
        return
    AUDIT_LOGGER.info(json.dumps(event, sort_keys=True))


def _audit_result(decision: WriteDecision) -> str:
    if not decision.allowed:
        return "denied"
    if decision.validate_only:
        return "validated"
    return "executed"


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
            if any(
                token in lowered
                for token in (
                    "secret",
                    "token",
                    "refresh",
                    "password",
                    "key",
                    "email",
                    "phone",
                    "address",
                    "user_identifier",
                    "gclid",
                    "gbraid",
                    "wbraid",
                    "customer_match",
                )
            ):
                redacted[key] = "[REDACTED]"
            else:
                redacted[key] = redact_sensitive(item)
        return redacted
    if isinstance(value, list):
        return [redact_sensitive(item) for item in value]
    return value

