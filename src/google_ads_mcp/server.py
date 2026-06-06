"""FastMCP server registration."""

from __future__ import annotations

from functools import wraps
import os
import inspect
from typing import Any

from .capability_matrix import capability_matrix_payload
from .config import ConfigError, get_settings, value_looks_missing
from .errors import format_tool_error
from .friendly import FriendlyDispatcher
from .gateway import GoogleAdsGateway
from .resources import (
    capability_matrix_resource,
    discovery_document_resource,
    gaql_knowledge_base_resource,
    metrics_resource,
    release_notes_resource,
    segments_resource,
    tool_catalog_resource,
)
from .tool_config import ToolExposure, ToolRegistry, load_tool_registry
from .tool_catalog import FRIENDLY_TOOL_SPECS


def build_mcp() -> Any:
    try:
        from fastmcp import FastMCP
        from starlette.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover - exercised only without dependencies installed.
        raise RuntimeError("fastmcp and starlette are required to run the MCP server.") from exc

    settings = get_settings()
    settings.require_mcp_auth()
    registry = load_tool_registry(settings)
    auth = _build_auth(settings)
    mcp = FastMCP("Google Ads Full API MCP", auth=auth)
    gateway = GoogleAdsGateway(settings=settings, mode=registry.mode)
    dispatcher = FriendlyDispatcher(gateway=gateway)

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(request: Any) -> Any:  # noqa: ARG001
        return JSONResponse(_server_status_payload(settings, registry))

    @mcp.custom_route("/readyz", methods=["GET"])
    async def readyz(request: Any) -> Any:  # noqa: ARG001
        payload = _google_ads_readiness_payload(settings)
        return JSONResponse(payload, status_code=200 if payload["google_ads_configured"] else 503)

    async def get_server_status() -> dict[str, Any]:
        """Return server mode, auth mode, config source, and exposed tool count."""

        return _server_status_payload(settings, registry)

    async def get_tool_catalog() -> dict[str, Any]:
        """Return the currently exposed Google Ads MCP tool catalog."""

        return {
            "mode": registry.mode,
            "tools_config_source": registry.config_source,
            "legacy_aliases_enabled": registry.legacy_aliases_enabled,
            "tool_count": len(registry.exposures),
            "tools": [exposure.to_catalog_entry() for exposure in registry.exposures],
        }

    async def get_capability_matrix() -> dict[str, Any]:
        """Return implementation status for the currently exposed tools."""

        return capability_matrix_payload(registry)

    async def list_google_ads_services() -> dict[str, Any]:
        """List service classes available in the installed Google Ads API client."""

        return gateway.list_services()

    async def list_accessible_customers() -> dict[str, Any]:
        """List customer resource names accessible to the configured OAuth user."""

        return await gateway.list_accessible_customers()

    async def describe_google_ads_service(service_name: str) -> dict[str, Any]:
        """Describe callable methods for a Google Ads service."""

        return gateway.describe_service(service_name)

    async def describe_google_ads_resource(resource_name: str) -> dict[str, Any]:
        """Describe fields for a Google Ads API resource using GoogleAdsFieldService."""

        return await gateway.describe_resource(resource_name)

    async def get_google_ads_resource_metadata(
        resource_name: str,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Return selectable, filterable, sortable, metric, and segment metadata."""

        return await gateway.get_resource_metadata(
            resource_name,
            force_refresh=force_refresh,
        )

    async def validate_gaql_fields(
        resource_name: str,
        fields: list[str],
        include_metrics: bool = True,
        include_segments: bool = True,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Validate GAQL SELECT fields against live resource metadata."""

        return await gateway.validate_gaql_fields(
            resource_name,
            fields,
            include_metrics=include_metrics,
            include_segments=include_segments,
            force_refresh=force_refresh,
        )

    async def suggest_gaql_fields(
        resource_name: str,
        field_prefix_or_query: str,
        limit: int = 10,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Suggest GAQL fields from live metadata for a resource."""

        return await gateway.suggest_gaql_fields(
            resource_name,
            field_prefix_or_query,
            limit=limit,
            force_refresh=force_refresh,
        )

    async def plan_gaql_query(
        resource_name: str,
        user_goal: str | None = None,
        fields: list[str] | None = None,
        metrics: list[str] | None = None,
        segments: list[str] | None = None,
        date_range: str | None = "LAST_7_DAYS",
        start_date: str | None = None,
        end_date: str | None = None,
        filters: dict[str, Any] | None = None,
        include_primary_field: bool = True,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Build and validate a GAQL query plan without executing it."""

        return await gateway.plan_gaql_query(
            resource_name=resource_name,
            user_goal=user_goal,
            fields=fields,
            metrics=metrics,
            segments=segments,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            filters=filters,
            include_primary_field=include_primary_field,
            force_refresh=force_refresh,
        )

    async def explain_gaql_error(error_text: str) -> dict[str, object]:
        """Explain a common GAQL error and suggest the next safe tool to use."""

        return gateway.explain_gaql_error(error_text)

    async def query_google_ads_docs(
        question: str,
        category: str | None = None,
    ) -> dict[str, Any]:
        """Query the offline GAQL knowledge base before writing Google Ads queries."""

        from .knowledge_base import search as kb_search
        from .knowledge_base import total_entry_count

        entries = kb_search(question, category=category)
        count = total_entry_count()
        return {
            "question": question,
            "category": category,
            "matched_entries": [entry.to_dict() for entry in entries],
            "total_entries": count,
            "total_kb_entries": count,
            "hint": (
                "Always include the primary resource field in SELECT to avoid "
                "EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE errors. Use "
                "describe_google_ads_resource to inspect live field metadata."
            ),
        }

    async def google_ads_search(
        customer_id: str,
        query: str,
        page_size: int = 1000,
        page_token: str | None = None,
        primary_field: str | None = None,
    ) -> dict[str, Any]:
        """Run a GAQL search query."""

        return await gateway.search(
            customer_id=customer_id,
            query=query,
            page_size=page_size,
            page_token=page_token,
            primary_field=primary_field,
        )

    async def google_ads_search_stream(
        customer_id: str,
        query: str,
        primary_field: str | None = None,
        max_rows: int = 10_000,
    ) -> dict[str, Any]:
        """Run a GAQL SearchStream query."""

        return await gateway.search_stream(
            customer_id=customer_id,
            query=query,
            primary_field=primary_field,
            max_rows=max_rows,
        )

    async def google_ads_mutate(
        customer_id: str,
        operations: list[dict[str, Any]],
        validate_only: bool = True,
        execute: bool = False,
        confirmation_phrase: str | None = None,
        partial_failure: bool = False,
        response_content_type: str = "MUTABLE_RESOURCE",
    ) -> dict[str, Any]:
        """Run GoogleAdsService.mutate against arbitrary MutateOperation payloads."""

        return await gateway.mutate(
            customer_id=customer_id,
            operations=operations,
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
            partial_failure=partial_failure,
            response_content_type=response_content_type,
            tool_name="google_ads_mutate",
            operation_type="google_ads_mutate",
        )

    async def google_ads_call_service(
        service_name: str,
        method_name: str,
        request: dict[str, Any] | None = None,
        request_type: str | None = None,
        is_write: bool | None = None,
        validate_only: bool = True,
        execute: bool = False,
        confirmation_phrase: str | None = None,
    ) -> dict[str, Any]:
        """Call any Google Ads API service method exposed by the installed client."""

        return await gateway.call_service(
            service_name=service_name,
            method_name=method_name,
            payload=request or {},
            request_type=request_type,
            is_write=is_write,
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
            tool_name="google_ads_call_service",
        )

    async def validate_google_ads_payload(
        request_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate a protobuf JSON payload against a Google Ads request/message type."""

        message = gateway.get_type(request_type)
        gateway._parse_dict(payload, message)  # noqa: SLF001 - exposed as an MCP validation tool.
        return {"valid": True, "request_type": request_type}

    core_tools = {
        "get_server_status": get_server_status,
        "get_tool_catalog": get_tool_catalog,
        "get_capability_matrix": get_capability_matrix,
        "list_accessible_customers": list_accessible_customers,
        "list_google_ads_services": list_google_ads_services,
        "describe_google_ads_service": describe_google_ads_service,
        "describe_google_ads_resource": describe_google_ads_resource,
        "get_google_ads_resource_metadata": get_google_ads_resource_metadata,
        "validate_gaql_fields": validate_gaql_fields,
        "suggest_gaql_fields": suggest_gaql_fields,
        "plan_gaql_query": plan_gaql_query,
        "explain_gaql_error": explain_gaql_error,
        "query_google_ads_docs": query_google_ads_docs,
        "google_ads_search": google_ads_search,
        "google_ads_search_stream": google_ads_search_stream,
        "google_ads_mutate": google_ads_mutate,
        "google_ads_call_service": google_ads_call_service,
        "validate_google_ads_payload": validate_google_ads_payload,
    }
    for canonical_name, func in core_tools.items():
        _register_core_tool(mcp, registry, canonical_name, func)

    for spec in FRIENDLY_TOOL_SPECS:
        for exposure in registry.exposures_for(spec.name):
            _register_friendly_tool(mcp, dispatcher, exposure)

    _register_resources(mcp, settings, registry)

    return mcp


def _build_auth(settings: Any) -> Any:
    if settings.allow_unauthenticated_mcp:
        return None
    if settings.auth_mode == "oauth_proxy":
        try:
            from fastmcp.server.auth.providers.google import GoogleProvider
        except ImportError as exc:  # pragma: no cover
            raise ConfigError("fastmcp GoogleProvider is required for OAuth proxy auth.") from exc
        provider = GoogleProvider(
            client_id=settings.mcp_oauth_client_id,
            client_secret=settings.mcp_oauth_client_secret,
            base_url=settings.mcp_base_url,
            required_scopes=[
                "openid",
                "https://www.googleapis.com/auth/userinfo.email",
                "https://www.googleapis.com/auth/userinfo.profile",
            ],
        )
        return _OAuthAllowlistProvider(provider, settings)
    try:
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
    except ImportError as exc:  # pragma: no cover
        raise ConfigError("fastmcp StaticTokenVerifier is required for bearer auth.") from exc
    return StaticTokenVerifier(
        tokens={
            settings.mcp_bearer_token: {
                "client_id": "configured-mcp-client",
                "scopes": ["google_ads:read", "google_ads:write"],
            }
        },
        required_scopes=["google_ads:read"],
    )


class _OAuthAllowlistProvider:
    def __init__(self, provider: Any, settings: Any) -> None:
        self.provider = provider
        self.allowed_emails = set(settings.mcp_allowed_emails)
        self.allowed_domains = set(settings.mcp_allowed_domains)

    def __getattr__(self, name: str) -> Any:
        return getattr(self.provider, name)

    async def verify_token(self, token: str) -> Any:
        access_token = await self.provider.verify_token(token)
        if access_token is None:
            return None
        if not _oauth_token_allowed(
            access_token,
            allowed_emails=self.allowed_emails,
            allowed_domains=self.allowed_domains,
        ):
            return None
        return access_token


def _oauth_token_allowed(
    access_token: Any,
    *,
    allowed_emails: set[str],
    allowed_domains: set[str],
) -> bool:
    if not allowed_emails and not allowed_domains:
        return False
    claims = getattr(access_token, "claims", {}) or {}
    email = str(claims.get("email") or "").strip().lower()
    subject = str(getattr(access_token, "subject", "") or claims.get("sub") or "").strip().lower()
    hosted_domain = str(claims.get("hd") or "").strip().lower()
    email_domain = email.rsplit("@", 1)[-1] if "@" in email else ""
    return (
        bool(email and email in allowed_emails)
        or bool(subject and subject in allowed_emails)
        or bool(hosted_domain and hosted_domain in allowed_domains)
        or bool(email_domain and email_domain in allowed_domains)
    )


def _register_friendly_tool(
    mcp: Any,
    dispatcher: FriendlyDispatcher,
    exposure: ToolExposure,
) -> None:
    async def friendly_tool(
        customer_id: str = "",
        payload: dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        date_range: str | None = "LAST_30_DAYS",
        start_date: str | None = None,
        end_date: str | None = None,
        time_segment: str | None = None,
        page_size: int = 1000,
        page_token: str | None = None,
        validate_only: bool = True,
        execute: bool = False,
        confirmation_phrase: str | None = None,
        partial_failure: bool = False,
    ) -> dict[str, Any]:
        try:
            return await dispatcher.dispatch(
                exposure.canonical_name,
                customer_id=customer_id or None,
                payload=payload,
                filters=filters,
                date_range=date_range,
                start_date=start_date,
                end_date=end_date,
                time_segment=time_segment,
                page_size=page_size,
                page_token=page_token,
                validate_only=validate_only,
                execute=execute,
                confirmation_phrase=confirmation_phrase,
                partial_failure=partial_failure,
            )
        except Exception as exc:  # pragma: no cover - behavior covered through helper tests.
            return format_tool_error(exc)

    friendly_tool.__name__ = exposure.registered_name
    friendly_tool.__doc__ = exposure.description
    mcp.tool(name=exposure.registered_name)(friendly_tool)


def _register_core_tool(
    mcp: Any,
    registry: ToolRegistry,
    canonical_name: str,
    func: Any,
) -> None:
    for exposure in registry.exposures_for(canonical_name):
        registered = _tool_response(func)
        registered.__name__ = exposure.registered_name
        registered.__doc__ = exposure.description
        mcp.tool(name=exposure.registered_name)(registered)


def _tool_response(func: Any) -> Any:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            result = func(*args, **kwargs)
            if inspect.isawaitable(result):
                return await result
            return result
        except Exception as exc:
            return format_tool_error(exc)

    return wrapper


def _server_status_payload(settings: Any, registry: ToolRegistry) -> dict[str, Any]:
    readiness = _google_ads_readiness_payload(settings)
    return {
        "status": "ok",
        "service": "google-ads-mcp",
        "api_version": settings.api_version,
        "auth": "disabled-local-dev" if settings.allow_unauthenticated_mcp else settings.auth_mode,
        "mode": registry.mode,
        "google_ads_configured": readiness["google_ads_configured"],
        "tools_config_source": registry.config_source,
        "exposed_tool_count": len(registry.exposures),
        "legacy_aliases_enabled": registry.legacy_aliases_enabled,
        "generic_service_bridge_enabled": bool(settings.enable_generic_service_bridge),
        "oauth_allowlist_configured": bool(
            settings.mcp_allowed_emails or settings.mcp_allowed_domains
        ),
    }


def _google_ads_readiness_payload(settings: Any) -> dict[str, Any]:
    required = {
        "GOOGLE_ADS_DEVELOPER_TOKEN": settings.developer_token,
        "GOOGLE_ADS_CLIENT_ID": settings.oauth_client_id,
        "GOOGLE_ADS_CLIENT_SECRET": settings.oauth_client_secret,
        "GOOGLE_ADS_REFRESH_TOKEN": settings.refresh_token,
    }
    missing = [name for name, value in required.items() if value_looks_missing(value)]
    return {
        "status": "ready" if not missing else "not_ready",
        "service": "google-ads-mcp",
        "google_ads_configured": not missing,
        "missing": missing,
    }


def _register_resources(mcp: Any, settings: Any, registry: ToolRegistry) -> None:
    @mcp.resource(
        "resource://google-ads/discovery-document",
        name="Google Ads Discovery Document",
        mime_type="application/json",
    )
    def discovery_document() -> str:
        return discovery_document_resource(
            settings.api_version,
            alias_of="resource://google-ads/reference-index",
        )

    @mcp.resource(
        "resource://google-ads/reference-index",
        name="Google Ads Reference Index",
        mime_type="application/json",
    )
    def reference_index() -> str:
        return discovery_document_resource(settings.api_version)

    @mcp.resource(
        "resource://google-ads/metrics",
        name="Google Ads Metrics",
        mime_type="application/json",
    )
    def metrics() -> str:
        return metrics_resource(settings.api_version)

    @mcp.resource(
        "resource://google-ads/segments",
        name="Google Ads Segments",
        mime_type="application/json",
    )
    def segments() -> str:
        return segments_resource(settings.api_version)

    @mcp.resource(
        "resource://google-ads/release-notes",
        name="Google Ads Release Notes",
        mime_type="application/json",
    )
    def release_notes() -> str:
        return release_notes_resource(
            settings.api_version,
            alias_of="resource://google-ads/release-notes-index",
        )

    @mcp.resource(
        "resource://google-ads/release-notes-index",
        name="Google Ads Release Notes Index",
        mime_type="application/json",
    )
    def release_notes_index() -> str:
        return release_notes_resource(settings.api_version)

    @mcp.resource(
        "resource://google-ads/tool-catalog",
        name="Google Ads MCP Tool Catalog",
        mime_type="text/markdown",
    )
    def tool_catalog() -> str:
        return tool_catalog_resource()

    @mcp.resource(
        "resource://google-ads/capability-matrix",
        name="Google Ads MCP Capability Matrix",
        mime_type="application/json",
    )
    def capability_matrix() -> str:
        return capability_matrix_resource(registry)

    @mcp.resource(
        "resource://google-ads/gaql-knowledge-base",
        name="Google Ads GAQL Knowledge Base",
        mime_type="text/markdown",
    )
    def gaql_knowledge_base() -> str:
        return gaql_knowledge_base_resource()


def main() -> None:
    settings = get_settings()
    mcp = build_mcp()
    mcp.run(
        transport="http",
        host=settings.host,
        port=settings.port,
        path=os.environ.get("MCP_PATH", "/mcp"),
    )


if __name__ == "__main__":
    main()
