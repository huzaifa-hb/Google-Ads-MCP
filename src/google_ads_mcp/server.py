"""FastMCP server registration."""

from __future__ import annotations

import os
from typing import Any

from .config import ConfigError, get_settings
from .friendly import FriendlyDispatcher
from .gateway import GoogleAdsGateway
from .tool_catalog import FRIENDLY_TOOL_SPECS


def build_mcp() -> Any:
    try:
        from fastmcp import FastMCP
        from starlette.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover - exercised only without dependencies installed.
        raise RuntimeError("fastmcp and starlette are required to run the MCP server.") from exc

    settings = get_settings()
    settings.require_mcp_auth()
    auth = _build_auth(settings)
    mcp = FastMCP("Google Ads Full API MCP", auth=auth)
    gateway = GoogleAdsGateway(settings=settings)
    dispatcher = FriendlyDispatcher(gateway=gateway)

    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(request: Any) -> Any:  # noqa: ARG001
        return JSONResponse(
            {
                "status": "ok",
                "service": "google-ads-mcp",
                "api_version": settings.api_version,
                "auth": "bearer" if settings.mcp_bearer_token else "disabled-local-dev",
            }
        )

    @mcp.tool
    async def get_tool_catalog() -> dict[str, Any]:
        """Return the registered friendly Google Ads MCP tool catalog."""

        return {
            "tool_count": len(FRIENDLY_TOOL_SPECS),
            "tools": [
                {
                    "name": spec.name,
                    "category": spec.category,
                    "mode": spec.mode,
                    "resource": spec.resource,
                    "description": spec.description,
                }
                for spec in FRIENDLY_TOOL_SPECS
            ],
        }

    @mcp.tool
    async def list_google_ads_services() -> dict[str, Any]:
        """List service classes available in the installed Google Ads API client."""

        return gateway.list_services()

    @mcp.tool
    async def describe_google_ads_service(service_name: str) -> dict[str, Any]:
        """Describe callable methods for a Google Ads service."""

        return gateway.describe_service(service_name)

    @mcp.tool
    async def describe_google_ads_resource(resource_name: str) -> dict[str, Any]:
        """Describe fields for a Google Ads API resource using GoogleAdsFieldService."""

        return await gateway.describe_resource(resource_name)

    @mcp.tool
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

    @mcp.tool
    async def google_ads_search(
        customer_id: str,
        query: str,
        page_size: int = 1000,
        page_token: str | None = None,
        offset: int | None = None,
        primary_field: str | None = None,
    ) -> dict[str, Any]:
        """Run a GAQL search query."""

        return await gateway.search(
            customer_id=customer_id,
            query=query,
            page_size=page_size,
            page_token=page_token,
            offset=offset,
            primary_field=primary_field,
        )

    @mcp.tool
    async def google_ads_search_stream(
        customer_id: str,
        query: str,
        primary_field: str | None = None,
    ) -> dict[str, Any]:
        """Run a GAQL SearchStream query."""

        return await gateway.search_stream(
            customer_id=customer_id,
            query=query,
            primary_field=primary_field,
        )

    @mcp.tool
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
        )

    @mcp.tool
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
        )

    @mcp.tool
    async def validate_google_ads_payload(
        request_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Validate a protobuf JSON payload against a Google Ads request/message type."""

        message = gateway.get_type(request_type)
        gateway._parse_dict(payload, message)  # noqa: SLF001 - exposed as an MCP validation tool.
        return {"valid": True, "request_type": request_type}

    for spec in FRIENDLY_TOOL_SPECS:
        _register_friendly_tool(mcp, dispatcher, spec.name, spec.description)

    return mcp


def _build_auth(settings: Any) -> Any:
    if settings.allow_unauthenticated_mcp:
        return None
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


def _register_friendly_tool(
    mcp: Any,
    dispatcher: FriendlyDispatcher,
    tool_name: str,
    description: str,
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
        offset: int | None = None,
        validate_only: bool = True,
        execute: bool = False,
        confirmation_phrase: str | None = None,
        partial_failure: bool = False,
    ) -> dict[str, Any]:
        return await dispatcher.dispatch(
            tool_name,
            customer_id=customer_id or None,
            payload=payload,
            filters=filters,
            date_range=date_range,
            start_date=start_date,
            end_date=end_date,
            time_segment=time_segment,
            page_size=page_size,
            page_token=page_token,
            offset=offset,
            validate_only=validate_only,
            execute=execute,
            confirmation_phrase=confirmation_phrase,
            partial_failure=partial_failure,
        )

    friendly_tool.__name__ = tool_name
    friendly_tool.__doc__ = description
    mcp.tool(name=tool_name)(friendly_tool)


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
