"""Google Ads API gateway used by MCP tools.

This module is the only place that imports the Google Ads client library. Keeping
that dependency at the edge lets unit tests exercise the MCP safety and routing
logic without live credentials or installed Google Ads packages.
"""

from __future__ import annotations

import asyncio
from collections import OrderedDict
from collections.abc import Callable
from copy import deepcopy
import inspect
import json
import logging
from pathlib import Path
import pkgutil
import random
import re
import time
from typing import Any

from .config import GOOGLE_ADS_OAUTH_SCOPE, Settings, get_settings
from .errors import format_google_ads_exception
from .gaql import (
    GAQL_FIELD_RE,
    Pagination,
    apply_default_parameters,
    apply_pagination,
    date_where_clause,
    ensure_no_offset_clause,
    ensure_primary_field,
    explain_gaql_error,
    gaql_filter_clause,
    gaql_literal,
    normalize_field_list,
    normalize_resource_name,
    select_clause,
    summarize_page,
    suggest_fields,
)
from .safety import ValidationError, guard_google_ads_write, normalize_customer_id, redact_sensitive


LOGGER = logging.getLogger(__name__)

TRANSIENT_ERROR_MARKERS = (
    "RESOURCE_EXHAUSTED",
    "UNAVAILABLE",
    "DEADLINE_EXCEEDED",
    "INTERNAL",
    "RATE_EXCEEDED",
    "QUOTA_EXCEEDED",
)
TRANSIENT_ERROR_RE = re.compile(
    r"\b(resource[_ ]exhausted|unavailable|deadline[_ ]exceeded|internal|"
    r"rate[_ -]?exceeded|rate[_ -]?limit|quota)\b",
    flags=re.IGNORECASE,
)
QUOTA_OR_RATE_RE = re.compile(
    r"\b(resource[_ ]exhausted|rate[_ -]?exceeded|rate[_ -]?limit|quota)\b",
    flags=re.IGNORECASE,
)

MUTATING_METHOD_PREFIXES = (
    "mutate_",
    "apply_",
    "dismiss_",
    "upload_",
    "create_",
    "delete_",
    "remove_",
    "promote_",
    "graduate_",
    "end_",
    "cancel_",
    "set_",
    "run_",
    "add_",
    "update_",
)

READ_ONLY_SERVICE_METHODS = {
    ("CustomerService", "list_accessible_customers"),
    ("GoogleAdsService", "search"),
    ("GoogleAdsService", "search_stream"),
    ("GoogleAdsFieldService", "search_google_ads_fields"),
    ("InvoiceService", "list_invoices"),
    ("KeywordPlanIdeaService", "generate_keyword_ideas"),
    ("ReachPlanService", "generate_reach_forecast"),
}


def snake_to_pascal(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_") if part)


class GoogleAdsGateway:
    """Lazy wrapper around Google Ads API services."""

    def __init__(
        self,
        settings: Settings | None = None,
        client: Any | None = None,
        mode: str | None = None,
        audit_sink: Callable[[dict[str, Any]], None] | None = None,
        access_token: str | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._client = client
        self.access_token = access_token
        self.mode = mode or self.settings.mcp_mode or "safe_read_only"
        self.audit_sink = audit_sink
        self._resource_metadata_cache: OrderedDict[
            tuple[str, str], tuple[float, dict[str, Any]]
        ] = OrderedDict()
        self._metadata_snapshot: dict[str, Any] | None = None

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                from google.ads.googleads.client import GoogleAdsClient
            except ImportError as exc:
                raise RuntimeError(
                    "google-ads is not installed. Install the package or deploy the Docker image."
                ) from exc
            if self.access_token:
                self._client = self._load_client_from_access_token(GoogleAdsClient)
            else:
                self._client = GoogleAdsClient.load_from_dict(
                    self.settings.google_ads_client_config(),
                    version=self.settings.api_version,
                )
        return self._client

    def _load_client_from_access_token(self, google_ads_client_cls: Any) -> Any:
        try:
            from google.oauth2.credentials import Credentials
        except ImportError as exc:
            raise RuntimeError("google-auth is required for per-user Google Ads OAuth.") from exc
        config = self.settings.google_ads_access_token_client_config()
        credentials = Credentials(
            token=self.access_token,
            scopes=[GOOGLE_ADS_OAUTH_SCOPE],
        )
        return google_ads_client_cls(
            credentials=credentials,
            developer_token=config["developer_token"],
            login_customer_id=config.get("login_customer_id"),
            version=self.settings.api_version,
            use_proto_plus=True,
        )

    def get_service(self, service_name: str) -> Any:
        return self.client.get_service(service_name)

    def get_type(self, type_name: str) -> Any:
        return self.client.get_type(type_name)

    async def list_accessible_customers(self) -> dict[str, Any]:
        def call() -> Any:
            service = self.get_service("CustomerService")
            request = self.get_type("ListAccessibleCustomersRequest")
            try:
                return service.list_accessible_customers(request=request)
            except TypeError:
                return service.list_accessible_customers()

        response = await self._retry(call)
        data = self._message_to_dict(response)
        resource_names = []
        if isinstance(data, dict):
            resource_names = list(data.get("resource_names") or data.get("resourceNames") or [])
        return {
            "resource_names": resource_names,
            "customer_ids": [
                str(name).rsplit("/", 1)[-1] for name in resource_names if str(name).startswith("customers/")
            ],
            "response": data,
        }

    async def search(
        self,
        *,
        customer_id: str,
        query: str,
        page_size: int = 1000,
        page_token: str | None = None,
        primary_field: str | None = None,
    ) -> dict[str, Any]:
        cid = normalize_customer_id(customer_id)
        if primary_field:
            ensure_primary_field(query, primary_field)
        pagination = Pagination(page_size=page_size, page_token=page_token)
        query = apply_pagination(query, pagination)
        query = apply_default_parameters(query)

        def call() -> Any:
            service = self.get_service("GoogleAdsService")
            request = self.get_type("SearchGoogleAdsRequest")
            request.customer_id = cid
            request.query = query
            if page_token:
                request.page_token = page_token
            return service.search(request=request)

        response = await self._retry(call)
        page_results = getattr(response, "results", response)
        raw_rows = [self._message_to_dict(row) for row in page_results]
        next_token = getattr(response, "next_page_token", None)
        return {
            "customer_id": cid,
            "query": query,
            "rows": raw_rows,
            "pagination": summarize_page(
                raw_rows,
                page_size,
                next_token,
                fetched_count=len(raw_rows),
            ),
        }

    async def search_stream(
        self,
        *,
        customer_id: str,
        query: str,
        primary_field: str | None = None,
        max_rows: int = 10_000,
    ) -> dict[str, Any]:
        cid = normalize_customer_id(customer_id)
        if max_rows < 1:
            raise ValidationError("max_rows must be at least 1.")
        if primary_field:
            ensure_primary_field(query, primary_field)
        ensure_no_offset_clause(query)
        query = apply_default_parameters(query)

        def call() -> Any:
            service = self.get_service("GoogleAdsService")
            request = self.get_type("SearchGoogleAdsStreamRequest")
            request.customer_id = cid
            request.query = query
            return service.search_stream(request=request)

        stream = await self._retry(call)
        rows: list[dict[str, Any]] = []
        truncated = False
        for batch in stream:
            for row in getattr(batch, "results", []):
                if len(rows) >= max_rows:
                    truncated = True
                    break
                rows.append(self._message_to_dict(row))
            if truncated:
                break
        return {
            "customer_id": cid,
            "query": query,
            "rows": rows,
            "row_count": len(rows),
            "max_rows": max_rows,
            "truncated": truncated,
        }

    async def mutate(
        self,
        *,
        customer_id: str,
        operations: list[dict[str, Any]],
        validate_only: bool = True,
        execute: bool = False,
        confirmation_phrase: str | None = None,
        partial_failure: bool = False,
        response_content_type: str = "MUTABLE_RESOURCE",
        tool_name: str = "google_ads_mutate",
        operation_type: str | None = None,
    ) -> dict[str, Any]:
        cid = normalize_customer_id(customer_id)
        write_decision = guard_google_ads_write(
            mode=self.mode,
            tool_name=tool_name,
            customer_id=cid,
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
            operation_type=operation_type or "google_ads_mutate",
            operation_count=len(operations),
            audit_sink=self.audit_sink,
        )
        validate_only = write_decision.validate_only
        if len(operations) > 5000:
            raise ValidationError("Google Ads mutate batches can include at most 5,000 operations.")

        def call() -> Any:
            service = self.get_service("GoogleAdsService")
            request = self.get_type("MutateGoogleAdsRequest")
            request.customer_id = cid
            request.partial_failure = partial_failure
            request.validate_only = validate_only
            request.response_content_type = response_content_type
            for operation_payload in operations:
                operation = self.get_type("MutateOperation")
                self._parse_dict(operation_payload, operation)
                request.mutate_operations.append(operation)
            return service.mutate(request=request)

        response = await self._retry(call, retryable=write_decision.validate_only)
        return {
            "customer_id": cid,
            "mode": self.mode,
            "validate_only": validate_only,
            "validation_forced": write_decision.forced_validation,
            "partial_failure": partial_failure,
            "operation_count": len(operations),
            "response": self._message_to_dict(response),
        }

    async def call_service(
        self,
        *,
        service_name: str,
        method_name: str,
        payload: dict[str, Any] | None = None,
        request_type: str | None = None,
        is_write: bool | None = None,
        validate_only: bool = True,
        execute: bool = False,
        confirmation_phrase: str | None = None,
        tool_name: str = "google_ads_call_service",
    ) -> dict[str, Any]:
        payload = dict(payload or {})
        method_looks_mutating = method_name.startswith(MUTATING_METHOD_PREFIXES)
        effective_is_write = bool(is_write) or method_looks_mutating
        read_allowed = (service_name, method_name) in READ_ONLY_SERVICE_METHODS
        generic_bridge_enabled = (
            self.mode == "admin_debug" and self.settings.enable_generic_service_bridge
        )
        if not effective_is_write and not read_allowed:
            if generic_bridge_enabled:
                effective_is_write = True
            else:
                raise ValidationError(
                    f"{service_name}.{method_name} is not on the read-only service allowlist. "
                    "Set is_write=true to route it through the write guard, or enable "
                    "GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE=true in admin_debug mode for "
                    "explicit generic bridge debugging."
                )
        write_decision = None
        if effective_is_write:
            customer_id = payload.get("customer_id") or payload.get("customerId")
            if not customer_id:
                raise ValidationError("customer_id is required for Google Ads service writes.")
            write_decision = guard_google_ads_write(
                mode=self.mode,
                tool_name=tool_name,
                customer_id=customer_id,
                validate_only=validate_only,
                execute=execute,
                confirmation_phrase=confirmation_phrase,
                operation_type=method_name,
                operation_count=1,
                audit_sink=self.audit_sink,
            )
        inferred_type = request_type or f"{snake_to_pascal(method_name)}Request"

        def call() -> Any:
            service = self.get_service(service_name)
            if not hasattr(service, method_name):
                raise ValidationError(f"{service_name}.{method_name} is not available.")
            method = getattr(service, method_name)
            request = self.get_type(inferred_type)
            request_payload = dict(payload)
            if write_decision is not None:
                supports_validate_only = self._message_has_field(request, "validate_only")
                if supports_validate_only:
                    request_payload["validate_only"] = write_decision.validate_only
                elif write_decision.validate_only:
                    raise ValidationError(
                        f"{inferred_type} does not support validate_only. "
                        "This service method cannot be previewed safely through "
                        "google_ads_call_service; use a native validation-capable mutate path "
                        "or confirm a real write explicitly."
                    )
                else:
                    request_payload.pop("validate_only", None)
            self._parse_dict(request_payload, request)
            return method(request=request)

        response = await self._retry(
            call,
            retryable=not write_decision or write_decision.validate_only,
        )
        return {
            "service": service_name,
            "method": method_name,
            "request_type": inferred_type,
            "is_write": effective_is_write,
            "mode": self.mode,
            "validation_forced": bool(write_decision and write_decision.forced_validation),
            "response": self._message_to_dict(response),
        }

    def list_services(self) -> dict[str, Any]:
        try:
            services_pkg = __import__(
                f"google.ads.googleads.{self.settings.api_version}.services.services",
                fromlist=["__path__"],
            )
            modules = [module.name for module in pkgutil.iter_modules(services_pkg.__path__)]
        except Exception as exc:
            LOGGER.warning("Unable to list Google Ads services: %s", exc)
            modules = []
        service_names = sorted({snake_to_pascal(name).replace("Service", "") + "Service" for name in modules})
        payload: dict[str, Any] = {
            "api_version": self.settings.api_version,
            "service_count": len(service_names),
            "services": service_names,
            "note": "Service list is generated from the installed google-ads client package.",
        }
        if not service_names:
            payload["warning"] = "Unable to inspect installed Google Ads service modules."
        return payload

    def describe_service(self, service_name: str) -> dict[str, Any]:
        service = self.get_service(service_name)
        methods = []
        for name, value in inspect.getmembers(service):
            if name.startswith("_"):
                continue
            if callable(value):
                methods.append(name)
        return {"service": service_name, "methods": sorted(methods)}

    async def describe_resource(self, resource_name: str) -> dict[str, Any]:
        resource = normalize_resource_name(resource_name)
        query = (
            "SELECT name, category, data_type, type_url, selectable, filterable, sortable "
            f"WHERE name LIKE '{resource}%'"
        )
        fields = await self._search_google_ads_fields(query)
        return {"resource": resource, "field_count": len(fields), "fields": fields}

    async def get_resource_metadata(
        self,
        resource_name: str,
        *,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        resource = normalize_resource_name(resource_name)
        cache_key = (self.settings.api_version, resource)
        if not force_refresh:
            cached = self._cached_resource_metadata(cache_key)
            if cached is not None:
                return cached

        cache_label = f"{self.settings.api_version}:{resource}"
        warnings: list[str] = []
        attributes_query = (
            "SELECT name, category, data_type, type_url, selectable, filterable, sortable, "
            "selectable_with, is_repeated "
            f"WHERE name LIKE '{resource}.%' AND category = 'ATTRIBUTE'"
        )
        try:
            attributes = await self._search_google_ads_fields(attributes_query)
        except Exception as exc:  # pragma: no cover - exact Google exception types vary.
            warnings.append("Attribute category filter failed; retried without category filter.")
            fallback_query = (
                "SELECT name, category, data_type, type_url, selectable, filterable, sortable, "
                "selectable_with, is_repeated "
                f"WHERE name LIKE '{resource}.%'"
            )
            try:
                attributes = await self._search_google_ads_fields(fallback_query)
            except Exception as fallback_exc:
                snapshot = self._metadata_from_snapshot(
                    resource=resource,
                    cache_key=cache_label,
                    exc=fallback_exc,
                    warnings=warnings,
                    original_error=exc,
                )
                if snapshot is not None:
                    self._store_resource_metadata(cache_key, snapshot)
                    return snapshot
                return self._metadata_error(
                    resource=resource,
                    cache_key=cache_label,
                    exc=fallback_exc,
                    warnings=warnings,
                    original_error=exc,
                )

        compatible_query = (
            "SELECT name, category, data_type, type_url, selectable, filterable, sortable, "
            "selectable_with, is_repeated "
            f"WHERE selectable_with CONTAINS ANY('{resource}')"
        )
        compatible: list[dict[str, Any]] = []
        try:
            compatible = await self._search_google_ads_fields(compatible_query)
        except Exception as exc:  # pragma: no cover - exact Google exception types vary.
            warnings.append(
                "Compatible metrics and segments query failed; returned resource attributes only."
            )
            warnings.append(str(exc))

        metadata = self._build_resource_metadata(
            resource=resource,
            cache_key=cache_label,
            attributes=attributes,
            compatible=compatible,
            warnings=warnings,
        )
        self._store_resource_metadata(cache_key, metadata)
        return metadata

    async def validate_gaql_fields(
        self,
        resource_name: str,
        fields: list[str] | str | None,
        *,
        include_metrics: bool = True,
        include_segments: bool = True,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        resource = normalize_resource_name(resource_name)
        requested_fields = normalize_field_list(fields)
        metadata = await self.get_resource_metadata(resource, force_refresh=force_refresh)
        if not metadata.get("ok", False):
            return {
                "ok": False,
                "resource": resource,
                "api_version": self.settings.api_version,
                "valid": False,
                "error": metadata,
            }

        allowed = set(metadata.get("selectable", []))
        if not include_metrics:
            allowed -= {field for field in allowed if field.startswith("metrics.")}
        if not include_segments:
            allowed -= {field for field in allowed if field.startswith("segments.")}

        invalid_fields: list[dict[str, Any]] = []
        valid_fields: list[str] = []
        all_candidates = sorted(allowed)
        for field in requested_fields:
            if not GAQL_FIELD_RE.fullmatch(field):
                invalid_fields.append(
                    {
                        "field": field,
                        "reason": "invalid_format",
                        "suggestions": self._field_suggestions(field, all_candidates),
                    }
                )
                continue
            if field not in allowed:
                invalid_fields.append(
                    {
                        "field": field,
                        "reason": "not_selectable_with_resource",
                        "suggestions": self._field_suggestions(field, all_candidates),
                    }
                )
                continue
            valid_fields.append(field)

        return {
            "ok": True,
            "resource": resource,
            "api_version": self.settings.api_version,
            "valid": not invalid_fields,
            "requested_fields": requested_fields,
            "valid_fields": valid_fields,
            "invalid_fields": invalid_fields,
            "metadata_cached": metadata.get("cached", False),
        }

    async def suggest_gaql_fields(
        self,
        resource_name: str,
        field_prefix_or_query: str,
        *,
        limit: int = 10,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        resource = normalize_resource_name(resource_name)
        metadata = await self.get_resource_metadata(resource, force_refresh=force_refresh)
        if not metadata.get("ok", False):
            return {
                "ok": False,
                "resource": resource,
                "api_version": self.settings.api_version,
                "error": metadata,
            }
        candidates = sorted(metadata.get("selectable", []))
        query = (field_prefix_or_query or "").strip()
        suggestions = self._field_suggestions(query, candidates, limit=limit)
        return {
            "ok": True,
            "resource": resource,
            "api_version": self.settings.api_version,
            "query": query,
            "suggestions": suggestions,
            "metadata_cached": metadata.get("cached", False),
        }

    async def plan_gaql_query(
        self,
        *,
        resource_name: str,
        user_goal: str | None = None,
        fields: list[str] | str | None = None,
        metrics: list[str] | str | None = None,
        segments: list[str] | str | None = None,
        date_range: str | None = "LAST_7_DAYS",
        start_date: str | None = None,
        end_date: str | None = None,
        filters: dict[str, Any] | None = None,
        include_primary_field: bool = True,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        resource = normalize_resource_name(resource_name)
        metadata = await self.get_resource_metadata(resource, force_refresh=force_refresh)
        if not metadata.get("ok", False):
            return {
                "ok": False,
                "resource": resource,
                "api_version": self.settings.api_version,
                "error": metadata,
            }

        selectable = set(metadata.get("selectable", []))
        requested_fields = normalize_field_list(fields)
        requested_metrics = normalize_field_list(metrics)
        requested_segments = normalize_field_list(segments)
        warnings: list[str] = []

        selected = self._default_gaql_fields(
            resource=resource,
            selectable=selectable,
            requested_fields=requested_fields,
            requested_metrics=requested_metrics,
            requested_segments=requested_segments,
            include_primary_field=include_primary_field,
        )

        validation = await self.validate_gaql_fields(
            resource,
            selected,
            force_refresh=False,
        )
        if validation.get("invalid_fields"):
            invalid_names = {item["field"] for item in validation["invalid_fields"]}
            warnings.append(
                "Removed fields that are not selectable with this resource: "
                + ", ".join(sorted(invalid_names))
            )
            selected = [field for field in selected if field not in invalid_names]

        if not selected:
            return {
                "ok": False,
                "resource": resource,
                "api_version": self.settings.api_version,
                "error_type": "NO_SELECTABLE_FIELDS",
                "message": "No selectable fields were available after validation.",
                "validation": validation,
            }

        where_clauses = self._filter_clauses(filters or {}, metadata, warnings)
        date_clause = date_where_clause(
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
        )
        if date_clause:
            where_clauses.insert(0, date_clause)

        query = f"{select_clause(selected)} FROM {resource}"
        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)

        return {
            "ok": True,
            "resource": resource,
            "api_version": self.settings.api_version,
            "user_goal": user_goal,
            "query": query,
            "selected_fields": selected,
            "where_clauses": where_clauses,
            "warnings": warnings,
            "metadata_cached": metadata.get("cached", False),
            "not_executed": True,
            "next_step": "Review the query, then run it with a read-only search tool.",
        }

    def explain_gaql_error(self, error_text: str) -> dict[str, object]:
        return explain_gaql_error(error_text)

    async def _search_google_ads_fields(self, query: str) -> list[dict[str, Any]]:
        def call() -> Any:
            service = self.get_service("GoogleAdsFieldService")
            request = self.get_type("SearchGoogleAdsFieldsRequest")
            self._set_request_value(request, "query", query)
            return service.search_google_ads_fields(request=request)

        response = await self._retry(call)
        return [self._message_to_dict(field) for field in response]

    def _metadata_error(
        self,
        *,
        resource: str,
        cache_key: str,
        exc: Exception,
        warnings: list[str],
        original_error: Exception | None = None,
    ) -> dict[str, Any]:
        formatted = format_google_ads_exception(exc)
        error_type = (
            "GoogleAdsException"
            if formatted.get("error_type") == "GoogleAdsException"
            else "GOOGLE_ADS_FIELD_SERVICE_ERROR"
        )
        errors = [str(exc)]
        if original_error:
            errors.insert(0, str(original_error))
        return {
            "ok": False,
            "resource": resource,
            "api_version": self.settings.api_version,
            "cache_key": cache_key,
            "cached": False,
            "error_type": error_type,
            "message": formatted.get("message", str(exc)),
            "request_id": formatted.get("request_id"),
            "google_ads_errors": formatted.get("google_ads_errors", []),
            "suggested_fix": formatted.get("suggested_fix"),
            "warnings": warnings,
            "error_summary": " | ".join(errors),
        }

    def _cached_resource_metadata(self, cache_key: tuple[str, str]) -> dict[str, Any] | None:
        if self.settings.metadata_cache_ttl_seconds <= 0:
            return None
        entry = self._resource_metadata_cache.get(cache_key)
        if entry is None:
            return None
        created_at, metadata = entry
        age = time.monotonic() - created_at
        if age > self.settings.metadata_cache_ttl_seconds:
            self._resource_metadata_cache.pop(cache_key, None)
            return None
        self._resource_metadata_cache.move_to_end(cache_key)
        cached = deepcopy(metadata)
        cached["cached"] = True
        cached["cache_age_seconds"] = round(age, 3)
        cached["cache_ttl_seconds"] = self.settings.metadata_cache_ttl_seconds
        return cached

    def _store_resource_metadata(
        self,
        cache_key: tuple[str, str],
        metadata: dict[str, Any],
    ) -> None:
        if (
            self.settings.metadata_cache_ttl_seconds <= 0
            or self.settings.metadata_cache_max_entries <= 0
        ):
            return
        self._resource_metadata_cache[cache_key] = (time.monotonic(), deepcopy(metadata))
        self._resource_metadata_cache.move_to_end(cache_key)
        while len(self._resource_metadata_cache) > self.settings.metadata_cache_max_entries:
            self._resource_metadata_cache.popitem(last=False)

    def _metadata_from_snapshot(
        self,
        *,
        resource: str,
        cache_key: str,
        exc: Exception,
        warnings: list[str],
        original_error: Exception | None = None,
    ) -> dict[str, Any] | None:
        snapshot = self._load_metadata_snapshot()
        resources = snapshot.get("resources", snapshot)
        if not isinstance(resources, dict):
            return None
        raw_metadata = resources.get(resource)
        if not isinstance(raw_metadata, dict):
            return None
        snapshot_warnings = [
            *warnings,
            "Live GoogleAdsFieldService unavailable; returned configured metadata snapshot.",
        ]
        errors = [str(exc)]
        if original_error:
            errors.insert(0, str(original_error))
        if "attributes" in raw_metadata or "compatible" in raw_metadata:
            metadata = self._build_resource_metadata(
                resource=resource,
                cache_key=cache_key,
                attributes=list(raw_metadata.get("attributes", [])),
                compatible=list(raw_metadata.get("compatible", [])),
                warnings=snapshot_warnings,
            )
        else:
            metadata = deepcopy(raw_metadata)
            metadata.setdefault("ok", True)
            metadata.setdefault("resource", resource)
            metadata.setdefault("api_version", self.settings.api_version)
            metadata.setdefault("cache_key", cache_key)
            metadata["cached"] = False
            metadata["warnings"] = snapshot_warnings + list(metadata.get("warnings", []))
        metadata["source"] = "metadata_snapshot"
        metadata["live_error_summary"] = " | ".join(errors)
        return metadata

    def _load_metadata_snapshot(self) -> dict[str, Any]:
        if self._metadata_snapshot is not None:
            return self._metadata_snapshot
        path = self.settings.metadata_snapshot_path
        if not path:
            self._metadata_snapshot = {}
            return self._metadata_snapshot
        try:
            snapshot_path = Path(path).expanduser()
            self._metadata_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            LOGGER.warning("Failed to load Google Ads metadata snapshot: %s", exc)
            self._metadata_snapshot = {}
        return self._metadata_snapshot

    def _build_resource_metadata(
        self,
        *,
        resource: str,
        cache_key: str,
        attributes: list[dict[str, Any]],
        compatible: list[dict[str, Any]],
        warnings: list[str],
    ) -> dict[str, Any]:
        fields_by_name: dict[str, dict[str, Any]] = {}
        for field in attributes + compatible:
            name = str(field.get("name", "")).strip()
            if not name:
                continue
            fields_by_name.setdefault(name, self._field_summary(field))

        selectable = sorted(
            name for name, field in fields_by_name.items() if bool(field.get("selectable"))
        )
        filterable = sorted(
            name for name, field in fields_by_name.items() if bool(field.get("filterable"))
        )
        sortable = sorted(name for name, field in fields_by_name.items() if bool(field.get("sortable")))
        metrics = sorted(name for name in selectable if name.startswith("metrics."))
        segments = sorted(name for name in selectable if name.startswith("segments."))
        resource_fields = sorted(name for name in selectable if name.startswith(f"{resource}."))
        fields = sorted(fields_by_name.values(), key=lambda field: str(field.get("name", "")))

        return {
            "ok": True,
            "resource": resource,
            "api_version": self.settings.api_version,
            "cache_key": cache_key,
            "cached": False,
            "cache_ttl_seconds": self.settings.metadata_cache_ttl_seconds,
            "field_count": len(fields),
            "selectable": selectable,
            "filterable": filterable,
            "sortable": sortable,
            "resource_fields": resource_fields,
            "metrics": metrics,
            "segments": segments,
            "compatible_fields": sorted(set(selectable) - set(resource_fields)),
            "fields": fields,
            "warnings": warnings,
        }

    def _field_summary(self, field: dict[str, Any]) -> dict[str, Any]:
        return {
            "name": field.get("name"),
            "category": field.get("category"),
            "data_type": field.get("data_type"),
            "type_url": field.get("type_url"),
            "selectable": bool(field.get("selectable")),
            "filterable": bool(field.get("filterable")),
            "sortable": bool(field.get("sortable")),
            "is_repeated": bool(field.get("is_repeated")),
            "selectable_with": list(field.get("selectable_with") or []),
        }

    def _field_suggestions(
        self,
        query: str,
        candidates: list[str],
        *,
        limit: int = 5,
    ) -> list[str]:
        normalized = (query or "").strip()
        if not normalized:
            return candidates[:limit]
        prefix_matches = [field for field in candidates if field.startswith(normalized)]
        close_matches = suggest_fields(normalized, candidates, limit=limit)
        combined = prefix_matches + close_matches
        return list(dict.fromkeys(combined))[:limit]

    def _default_gaql_fields(
        self,
        *,
        resource: str,
        selectable: set[str],
        requested_fields: list[str],
        requested_metrics: list[str],
        requested_segments: list[str],
        include_primary_field: bool,
    ) -> list[str]:
        selected: list[str] = []
        primary_field = f"{resource}.id"
        if include_primary_field and primary_field in selectable:
            selected.append(primary_field)

        selected.extend(requested_fields)
        selected.extend(requested_metrics)
        selected.extend(requested_segments)

        if not requested_fields and not requested_metrics and not requested_segments:
            for field in (f"{resource}.name", f"{resource}.status"):
                if field in selectable:
                    selected.append(field)
            for field in ("metrics.impressions", "metrics.clicks", "metrics.cost_micros"):
                if field in selectable:
                    selected.append(field)

        return list(dict.fromkeys(selected))

    def _filter_clauses(
        self,
        filters: dict[str, Any],
        metadata: dict[str, Any],
        warnings: list[str],
    ) -> list[str]:
        clauses: list[str] = []
        filterable = set(metadata.get("filterable", []))
        candidates = sorted(filterable)
        field_types = {
            str(field.get("name")): str(field.get("data_type", "")).upper()
            for field in metadata.get("fields", [])
            if field.get("name")
        }
        for field, raw_value in filters.items():
            field_name = str(field).strip()
            if not GAQL_FIELD_RE.fullmatch(field_name):
                warnings.append(f"Skipped invalid filter field '{field_name}'.")
                continue
            if field_name not in filterable:
                suggestions = self._field_suggestions(field_name, candidates)
                suffix = f" Suggestions: {', '.join(suggestions)}." if suggestions else ""
                warnings.append(f"Skipped non-filterable field '{field_name}'.{suffix}")
                continue
            clause = self._single_filter_clause(
                field_name,
                raw_value,
                field_types.get(field_name, ""),
            )
            if clause:
                clauses.append(clause)
        return clauses

    def _single_filter_clause(
        self,
        field_name: str,
        raw_value: Any,
        data_type: str,
    ) -> str | None:
        return gaql_filter_clause(field_name, raw_value, data_type)

    def _gaql_literal(self, value: Any, data_type: str = "") -> str:
        return gaql_literal(value, data_type)

    def _set_request_value(self, request: Any, name: str, value: Any) -> None:
        if isinstance(request, dict):
            request[name] = value
        else:
            setattr(request, name, value)

    async def _retry(self, fn: Callable[[], Any], *, retryable: bool = True) -> Any:
        attempt = 0
        while True:
            try:
                return await asyncio.to_thread(fn)
            except ValidationError:
                raise
            except Exception as exc:  # pragma: no cover - exact Google exception classes vary by version.
                attempt += 1
                if not retryable or attempt > self.settings.max_retries or not self._is_transient(exc):
                    raise self._format_exception(exc) from exc
                delay = self.settings.retry_base_seconds * (2 ** (attempt - 1))
                delay += random.uniform(0, self.settings.retry_base_seconds)
                await asyncio.sleep(delay)

    def _is_transient(self, exc: Exception) -> bool:
        text = str(exc)
        upper = text.upper()
        return any(marker in upper for marker in TRANSIENT_ERROR_MARKERS) or bool(
            TRANSIENT_ERROR_RE.search(text)
        )

    def _format_exception(self, exc: Exception) -> RuntimeError:
        formatted = format_google_ads_exception(exc)
        message = str(exc)
        if QUOTA_OR_RATE_RE.search(message):
            message = (
                "Google Ads quota or rate limit was reached. Reduce request volume, use "
                "pagination or batching, and check the developer-token access level. Raw detail: "
                f"{message}"
            )
        elif formatted.get("error_type") == "GoogleAdsException":
            message = str(formatted)
        return RuntimeError(message)

    def _message_has_field(self, message: Any, field_name: str) -> bool:
        if isinstance(message, dict):
            return True
        target = getattr(message, "_pb", message)
        descriptor = getattr(target, "DESCRIPTOR", None)
        fields = getattr(descriptor, "fields_by_name", {})
        return field_name in fields

    def _parse_dict(self, payload: dict[str, Any], message: Any) -> Any:
        try:
            from google.protobuf.json_format import ParseDict
        except ImportError as exc:
            raise RuntimeError("protobuf is required for Google Ads payload parsing.") from exc
        target = getattr(message, "_pb", message)
        try:
            ParseDict(payload, target, ignore_unknown_fields=False)
        except Exception as exc:
            raise ValidationError(
                f"Payload does not match {message.__class__.__name__}: {redact_sensitive(payload)}"
            ) from exc
        return message

    def _message_to_dict(self, message: Any) -> dict[str, Any] | list[Any] | str:
        if message is None:
            return {}
        if isinstance(message, (dict, list, str, int, float, bool)):
            return message
        try:
            from google.protobuf.json_format import MessageToDict
        except ImportError:
            return {"value": str(message)}
        target = getattr(message, "_pb", message)
        try:
            return MessageToDict(target, preserving_proto_field_name=True)
        except Exception as exc:
            LOGGER.warning("Unable to convert protobuf message to dict: %s", exc)
            return {"value": str(message)}
