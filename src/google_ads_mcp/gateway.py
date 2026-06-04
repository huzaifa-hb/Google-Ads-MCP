"""Google Ads API gateway used by MCP tools.

This module is the only place that imports the Google Ads client library. Keeping
that dependency at the edge lets unit tests exercise the MCP safety and routing
logic without live credentials or installed Google Ads packages.
"""

from __future__ import annotations

import asyncio
import inspect
import pkgutil
import random
from collections.abc import Callable
from typing import Any

from .config import Settings, get_settings
from .gaql import (
    Pagination,
    apply_pagination,
    ensure_primary_field,
    summarize_page,
    trim_offset_page,
)
from .safety import ValidationError, ensure_write_allowed, normalize_customer_id, redact_sensitive


TRANSIENT_ERROR_MARKERS = (
    "RESOURCE_EXHAUSTED",
    "UNAVAILABLE",
    "DEADLINE_EXCEEDED",
    "INTERNAL",
    "RATE_EXCEEDED",
    "quota",
    "rate",
)


def snake_to_pascal(value: str) -> str:
    return "".join(part.capitalize() for part in value.split("_") if part)


class GoogleAdsGateway:
    """Lazy wrapper around Google Ads API services."""

    def __init__(self, settings: Settings | None = None, client: Any | None = None) -> None:
        self.settings = settings or get_settings()
        self._client = client

    @property
    def client(self) -> Any:
        if self._client is None:
            try:
                from google.ads.googleads.client import GoogleAdsClient
            except ImportError as exc:
                raise RuntimeError(
                    "google-ads is not installed. Install the package or deploy the Docker image."
                ) from exc
            self._client = GoogleAdsClient.load_from_dict(
                self.settings.google_ads_client_config(),
                version=self.settings.api_version,
            )
        return self._client

    def get_service(self, service_name: str) -> Any:
        return self.client.get_service(service_name)

    def get_type(self, type_name: str) -> Any:
        return self.client.get_type(type_name)

    async def search(
        self,
        *,
        customer_id: str,
        query: str,
        page_size: int = 1000,
        page_token: str | None = None,
        offset: int | None = None,
        primary_field: str | None = None,
    ) -> dict[str, Any]:
        cid = normalize_customer_id(customer_id)
        if primary_field:
            ensure_primary_field(query, primary_field)
        pagination = Pagination(page_size=page_size, offset=offset, page_token=page_token)
        query = apply_pagination(query, pagination)

        def call() -> Any:
            service = self.get_service("GoogleAdsService")
            request = self.get_type("SearchGoogleAdsRequest")
            request.customer_id = cid
            request.query = query
            request.page_size = page_size
            if page_token:
                request.page_token = page_token
            return service.search(request=request)

        response = await self._retry(call)
        raw_rows = [self._message_to_dict(row) for row in response]
        rows = trim_offset_page(raw_rows, page_size, offset)
        next_token = getattr(response, "next_page_token", None)
        return {
            "customer_id": cid,
            "query": query,
            "rows": rows,
            "pagination": summarize_page(
                rows,
                page_size,
                next_token,
                offset=offset,
                fetched_count=len(raw_rows),
            ),
        }

    async def search_stream(
        self,
        *,
        customer_id: str,
        query: str,
        primary_field: str | None = None,
    ) -> dict[str, Any]:
        cid = normalize_customer_id(customer_id)
        if primary_field:
            ensure_primary_field(query, primary_field)

        def call() -> Any:
            service = self.get_service("GoogleAdsService")
            request = self.get_type("SearchGoogleAdsStreamRequest")
            request.customer_id = cid
            request.query = query
            return service.search_stream(request=request)

        stream = await self._retry(call)
        rows: list[dict[str, Any]] = []
        for batch in stream:
            for row in getattr(batch, "results", []):
                rows.append(self._message_to_dict(row))
        return {"customer_id": cid, "query": query, "rows": rows, "row_count": len(rows)}

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
    ) -> dict[str, Any]:
        cid = normalize_customer_id(customer_id)
        validate_only = ensure_write_allowed(
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
        )
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

        response = await self._retry(call)
        return {
            "customer_id": cid,
            "validate_only": validate_only,
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
    ) -> dict[str, Any]:
        payload = payload or {}
        if is_write is None:
            is_write = method_name.startswith(
                (
                    "mutate_",
                    "apply_",
                    "dismiss_",
                    "upload_",
                    "create_",
                    "remove_",
                    "run_",
                    "add_",
                    "update_",
                )
            )
        if is_write:
            ensure_write_allowed(
                validate_only=validate_only,
                execute=execute,
                confirmation_phrase=confirmation_phrase,
            )
            payload = dict(payload)
            payload.setdefault("validate_only", validate_only and not execute)

        inferred_type = request_type or f"{snake_to_pascal(method_name)}Request"

        def call() -> Any:
            service = self.get_service(service_name)
            if not hasattr(service, method_name):
                raise ValidationError(f"{service_name}.{method_name} is not available.")
            method = getattr(service, method_name)
            request = self.get_type(inferred_type)
            self._parse_dict(payload, request)
            return method(request=request)

        response = await self._retry(call)
        return {
            "service": service_name,
            "method": method_name,
            "request_type": inferred_type,
            "is_write": is_write,
            "response": self._message_to_dict(response),
        }

    def list_services(self) -> dict[str, Any]:
        try:
            services_pkg = __import__(
                f"google.ads.googleads.{self.settings.api_version}.services.services",
                fromlist=["__path__"],
            )
            modules = [module.name for module in pkgutil.iter_modules(services_pkg.__path__)]
        except Exception:
            modules = []
        service_names = sorted({snake_to_pascal(name).replace("Service", "") + "Service" for name in modules})
        return {
            "api_version": self.settings.api_version,
            "service_count": len(service_names),
            "services": service_names,
            "note": "Service list is generated from the installed google-ads client package.",
        }

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
        query = (
            "SELECT name, category, data_type, type_url, selectable, filterable, sortable "
            f"WHERE name LIKE '{resource_name}%'"
        )

        def call() -> Any:
            service = self.get_service("GoogleAdsFieldService")
            request = self.get_type("SearchGoogleAdsFieldsRequest")
            request.query = query
            return service.search_google_ads_fields(request=request)

        response = await self._retry(call)
        fields = [self._message_to_dict(field) for field in response]
        return {"resource": resource_name, "field_count": len(fields), "fields": fields}

    async def _retry(self, fn: Callable[[], Any]) -> Any:
        attempt = 0
        while True:
            try:
                return fn()
            except Exception as exc:  # pragma: no cover - exact Google exception classes vary by version.
                attempt += 1
                if attempt > self.settings.max_retries or not self._is_transient(exc):
                    raise self._format_exception(exc)
                delay = self.settings.retry_base_seconds * (2 ** (attempt - 1))
                delay += random.uniform(0, self.settings.retry_base_seconds)
                await asyncio.sleep(delay)

    def _is_transient(self, exc: Exception) -> bool:
        text = str(exc)
        return any(marker in text for marker in TRANSIENT_ERROR_MARKERS)

    def _format_exception(self, exc: Exception) -> RuntimeError:
        message = str(exc)
        lowered = message.lower()
        if "quota" in lowered or "rate" in lowered or "resource_exhausted" in lowered:
            message = (
                "Google Ads quota or rate limit was reached. Reduce request volume, use "
                "pagination or batching, and check the developer-token access level. Raw detail: "
                f"{message}"
            )
        return RuntimeError(message)

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
        except Exception:
            return {"value": str(message)}
