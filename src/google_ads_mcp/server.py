"""FastMCP server registration."""

from __future__ import annotations

import base64
from functools import wraps
import hashlib
import hmac
import inspect
import os
import secrets
import time
from typing import Any
from urllib.parse import urlencode

from .capability_matrix import capability_matrix_payload
from .config import GOOGLE_ADS_OAUTH_SCOPE, ConfigError, get_settings, value_looks_missing
from .errors import format_tool_error
from .friendly import FriendlyDispatcher
from .gaql import DEFAULT_DATE_RANGE
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
from .safety import build_jsonl_audit_sink
from .tool_config import ToolExposure, ToolRegistry, load_tool_registry
from .tool_schemas import parameters_schema_for_exposure

OAUTH_TOKEN_FIRESTORE_PREFIX = "google-ads-mcp-oauth"
OAUTH_TOKEN_FIRESTORE_SALT = "google-ads-mcp-firestore-token-storage-v1"
BOOTSTRAP_RESULT_FIRESTORE_PREFIX = "google-ads-mcp-bootstrap"
BOOTSTRAP_RESULT_FIRESTORE_SALT = "google-ads-mcp-firestore-bootstrap-results-v1"


def build_mcp() -> Any:
    try:
        from fastmcp import FastMCP
        from fastmcp.server.dependencies import get_access_token
        from starlette.responses import JSONResponse
    except ImportError as exc:  # pragma: no cover - exercised only without dependencies installed.
        raise RuntimeError("fastmcp and starlette are required to run the MCP server.") from exc

    settings = get_settings()
    settings.require_mcp_auth()
    registry = load_tool_registry(settings)
    auth = _build_auth(settings)
    mcp = FastMCP("Google Ads Full API MCP", auth=auth)
    audit_sink = build_jsonl_audit_sink(settings.audit_log_path)
    shared_gateway = (
        GoogleAdsGateway(
            settings=settings,
            mode=registry.mode,
            audit_sink=audit_sink,
        )
        if settings.google_ads_auth_mode == "shared_refresh_token"
        else None
    )

    def gateway_for_request() -> GoogleAdsGateway:
        if settings.google_ads_auth_mode == "per_user_oauth":
            return GoogleAdsGateway(
                settings=settings,
                mode=registry.mode,
                audit_sink=audit_sink,
                access_token=_google_ads_access_token_value(get_access_token()),
            )
        if shared_gateway is None:
            raise ConfigError("Shared Google Ads gateway is not configured.")
        return shared_gateway

    def dispatcher_for_request() -> FriendlyDispatcher:
        return FriendlyDispatcher(gateway=gateway_for_request())

    @mcp.custom_route("/healthz/", methods=["GET"])
    @mcp.custom_route("/healthz", methods=["GET"])
    async def healthz(request: Any) -> Any:  # noqa: ARG001
        return JSONResponse(_server_status_payload(settings, registry))

    @mcp.custom_route("/readyz", methods=["GET"])
    async def readyz(request: Any) -> Any:  # noqa: ARG001
        payload = _google_ads_readiness_payload(settings)
        return JSONResponse(payload, status_code=200 if payload["google_ads_configured"] else 503)

    @mcp.custom_route("/.well-known/openid-configuration", methods=["GET"])
    async def openid_configuration(request: Any) -> Any:  # noqa: ARG001
        if settings.auth_mode != "oauth_proxy":
            return JSONResponse({"detail": "Not Found"}, status_code=404)
        return JSONResponse(_oauth_discovery_payload(settings))

    if settings.google_ads_oauth_bootstrap_token:

        @mcp.custom_route("/admin/google-ads-oauth/start", methods=["GET"])
        async def google_ads_oauth_start(request: Any) -> Any:
            if not _bootstrap_request_allowed(
                request, settings.google_ads_oauth_bootstrap_token
            ):
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            provider = _bootstrap_provider(auth)
            if provider is None:
                return JSONResponse({"detail": "Bootstrap unavailable"}, status_code=404)
            nonce, authorization_url = provider.google_ads_bootstrap_authorization_url()
            if request.query_params.get("format") == "json":
                return JSONResponse(
                    {
                        "status": "authorization_required",
                        "nonce": nonce,
                        "authorization_url": authorization_url,
                    },
                    headers={"Cache-Control": "no-store"},
                )
            from starlette.responses import RedirectResponse

            return RedirectResponse(authorization_url, status_code=302)

        @mcp.custom_route("/admin/google-ads-oauth/result", methods=["GET"])
        async def google_ads_oauth_result(request: Any) -> Any:
            if not _bootstrap_request_allowed(
                request, settings.google_ads_oauth_bootstrap_token
            ):
                return JSONResponse({"detail": "Not Found"}, status_code=404)
            provider = _bootstrap_provider(auth)
            if provider is None:
                return JSONResponse({"detail": "Bootstrap unavailable"}, status_code=404)
            nonce = request.query_params.get("nonce") or ""
            result = await provider.pop_google_ads_bootstrap_result(nonce)
            status_code = 200 if result["status"] == "ready" else 202
            return JSONResponse(
                result,
                status_code=status_code,
                headers={"Cache-Control": "no-store"},
            )

    async def get_server_status() -> dict[str, Any]:
        """Return server mode, auth mode, config source, and exposed tool count."""

        return _server_status_payload(settings, registry)

    async def get_tool_catalog() -> dict[str, Any]:
        """Return the currently exposed Google Ads MCP tool catalog."""

        return {
            "mode": registry.mode,
            "tool_profile": registry.tool_profile,
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

        return gateway_for_request().list_services()

    async def list_accessible_customers() -> dict[str, Any]:
        """List customer resource names accessible to the authenticated Google user."""

        return await gateway_for_request().list_accessible_customers()

    async def describe_google_ads_service(service_name: str) -> dict[str, Any]:
        """Describe callable methods for a Google Ads service."""

        return gateway_for_request().describe_service(service_name)

    async def describe_google_ads_resource(resource_name: str) -> dict[str, Any]:
        """Describe fields for a Google Ads API resource using GoogleAdsFieldService."""

        return await gateway_for_request().describe_resource(resource_name)

    async def get_google_ads_resource_metadata(
        resource_name: str,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Return selectable, filterable, sortable, metric, and segment metadata."""

        return await gateway_for_request().get_resource_metadata(
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

        return await gateway_for_request().validate_gaql_fields(
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

        return await gateway_for_request().suggest_gaql_fields(
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
        date_range: str | None = DEFAULT_DATE_RANGE,
        start_date: str | None = None,
        end_date: str | None = None,
        filters: dict[str, Any] | None = None,
        include_primary_field: bool = True,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Build and validate a GAQL query plan without executing it."""

        return await gateway_for_request().plan_gaql_query(
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

        return gateway_for_request().explain_gaql_error(error_text)

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
        max_rows: int | None = 1000,
        page_size: int | None = None,
        page_token: str | None = None,
        primary_field: str | None = None,
    ) -> dict[str, Any]:
        """Run a GAQL search query."""

        return await gateway_for_request().search(
            customer_id=customer_id,
            query=query,
            max_rows=max_rows,
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

        return await gateway_for_request().search_stream(
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

        return await gateway_for_request().mutate(
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

        return await gateway_for_request().call_service(
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

        gateway = gateway_for_request()
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

    for exposure in registry.exposures:
        if exposure.source == "friendly":
            _register_friendly_tool(mcp, dispatcher_for_request, exposure)

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
        provider_cls = (
            _google_ads_oauth_bootstrap_provider_class(GoogleProvider)
            if settings.google_ads_oauth_bootstrap_token
            else GoogleProvider
        )
        provider_kwargs: dict[str, Any] = {}
        if settings.google_ads_oauth_bootstrap_token:
            provider_kwargs["google_ads_bootstrap_token"] = (
                settings.google_ads_oauth_bootstrap_token
            )
            provider_kwargs["google_ads_bootstrap_result_store"] = (
                _build_bootstrap_result_store(settings)
            )
        if settings.mcp_token_storage == "firestore":
            provider_kwargs["client_storage"] = _build_firestore_token_storage(settings)
        provider = provider_cls(
            client_id=settings.mcp_oauth_client_id,
            client_secret=settings.mcp_oauth_client_secret,
            base_url=settings.mcp_base_url,
            required_scopes=_google_oauth_scopes(settings),
            valid_scopes=_google_oauth_scopes(settings),
            **provider_kwargs,
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


def _google_oauth_scopes(settings: Any) -> list[str]:
    scopes = [
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ]
    if settings.google_ads_auth_mode == "per_user_oauth":
        scopes.append(GOOGLE_ADS_OAUTH_SCOPE)
    return scopes


def _build_encrypted_firestore_key_value(settings: Any, *, prefix: str, salt: str) -> Any:
    try:
        from key_value.aio.stores.firestore import (
            FirestoreStore,
            FirestoreV1CollectionSanitizationStrategy,
            FirestoreV1KeySanitizationStrategy,
        )
        from key_value.aio.wrappers.encryption import FernetEncryptionWrapper
        from key_value.aio.wrappers.prefix_collections import PrefixCollectionsWrapper
    except ImportError as exc:  # pragma: no cover - depends on optional runtime packages.
        raise ConfigError(
            "Firestore token storage requires google-cloud-firestore and FastMCP key-value "
            "Firestore support."
        ) from exc
    if value_looks_missing(settings.mcp_oauth_client_secret):
        raise ConfigError(
            "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET is required to encrypt Firestore token storage."
        )
    store = FirestoreStore(
        project=settings.google_project_id,
        database=settings.mcp_firestore_database,
        key_sanitization_strategy=FirestoreV1KeySanitizationStrategy(),
        collection_sanitization_strategy=FirestoreV1CollectionSanitizationStrategy(),
    )
    namespaced_store = PrefixCollectionsWrapper(
        store,
        prefix=prefix,
    )
    return FernetEncryptionWrapper(
        key_value=namespaced_store,
        source_material=settings.mcp_oauth_client_secret,
        salt=salt,
        raise_on_decryption_error=False,
    )


def _build_firestore_token_storage(settings: Any) -> Any:
    return _build_encrypted_firestore_key_value(
        settings,
        prefix=OAUTH_TOKEN_FIRESTORE_PREFIX,
        salt=OAUTH_TOKEN_FIRESTORE_SALT,
    )


class _MemoryBootstrapResultStore:
    def __init__(self) -> None:
        self.results: dict[str, dict[str, Any]] = {}

    async def put(self, nonce: str, result: dict[str, Any], *, ttl_seconds: int) -> None:
        self.results[nonce] = dict(result)

    async def pop(self, nonce: str) -> dict[str, Any]:
        self._purge_expired()
        if not nonce:
            return {"status": "missing_nonce"}
        result = self.results.pop(nonce, None)
        if result is None:
            return {"status": "pending"}
        return result

    def _purge_expired(self) -> None:
        now = int(time.time())
        expired = [
            nonce
            for nonce, result in self.results.items()
            if int(result.get("expires_at") or 0) < now
        ]
        for nonce in expired:
            self.results.pop(nonce, None)


class _KeyValueBootstrapResultStore:
    def __init__(self, key_value: Any) -> None:
        self.key_value = key_value

    async def put(self, nonce: str, result: dict[str, Any], *, ttl_seconds: int) -> None:
        await self.key_value.put(nonce, result, ttl=ttl_seconds)

    async def pop(self, nonce: str) -> dict[str, Any]:
        if not nonce:
            return {"status": "missing_nonce"}
        result = await self.key_value.get(nonce)
        if result is None:
            return {"status": "pending"}
        await self.key_value.delete(nonce)
        if int(result.get("expires_at") or 0) < int(time.time()):
            return {"status": "pending"}
        return result


def _build_bootstrap_result_store(settings: Any) -> _MemoryBootstrapResultStore | _KeyValueBootstrapResultStore:
    if settings.mcp_token_storage == "firestore":
        return _KeyValueBootstrapResultStore(
            _build_encrypted_firestore_key_value(
                settings,
                prefix=BOOTSTRAP_RESULT_FIRESTORE_PREFIX,
                salt=BOOTSTRAP_RESULT_FIRESTORE_SALT,
            )
        )
    return _MemoryBootstrapResultStore()


class _OAuthAllowlistProvider:
    def __init__(self, provider: Any, settings: Any) -> None:
        self.provider = provider
        self.allowed_emails = set(settings.mcp_allowed_emails)
        self.allowed_domains = set(settings.mcp_allowed_domains)
        self.allow_all_google_users = (
            settings.google_ads_auth_mode == "per_user_oauth"
            and settings.mcp_allow_all_google_users
            and not self.allowed_emails
            and not self.allowed_domains
        )

    def __getattr__(self, name: str) -> Any:
        return getattr(self.provider, name)

    async def verify_token(self, token: str) -> Any:
        access_token = await self.provider.verify_token(token)
        if access_token is None:
            return None
        if self.allow_all_google_users:
            return access_token
        if not _oauth_token_allowed(
            access_token,
            allowed_emails=self.allowed_emails,
            allowed_domains=self.allowed_domains,
        ):
            return None
        return access_token


class _GoogleAdsOAuthBootstrapMixin:
    _STATE_PREFIX = "gads-bootstrap"
    _GOOGLE_ADS_SCOPE = "https://www.googleapis.com/auth/adwords"
    _STATE_TTL_SECONDS = 600
    _RESULT_TTL_SECONDS = 600

    def __init__(
        self,
        *args: Any,
        google_ads_bootstrap_token: str,
        google_ads_bootstrap_result_store: Any | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._google_ads_bootstrap_token = google_ads_bootstrap_token
        self._google_ads_bootstrap_result_store = (
            google_ads_bootstrap_result_store or _MemoryBootstrapResultStore()
        )

    def google_ads_bootstrap_authorization_url(self) -> tuple[str, str]:
        nonce = secrets.token_urlsafe(24)
        expires_at = int(time.time() + self._STATE_TTL_SECONDS)
        state = self._sign_google_ads_bootstrap_state(nonce, expires_at)
        redirect_uri = self._google_ads_bootstrap_redirect_uri()
        params = {
            "client_id": self._upstream_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": self._GOOGLE_ADS_SCOPE,
            "access_type": "offline",
            "prompt": "consent",
            "include_granted_scopes": "true",
            "state": state,
        }
        return nonce, f"{self._upstream_authorization_endpoint}?{urlencode(params)}"

    async def pop_google_ads_bootstrap_result(self, nonce: str) -> dict[str, Any]:
        return await self._google_ads_bootstrap_result_store.pop(nonce)

    async def _handle_idp_callback(self, request: Any) -> Any:
        nonce = self._verify_google_ads_bootstrap_state(
            str(request.query_params.get("state") or "")
        )
        if nonce:
            return await self._handle_google_ads_bootstrap_callback(request, nonce)
        return await super()._handle_idp_callback(request)

    async def _handle_google_ads_bootstrap_callback(self, request: Any, nonce: str) -> Any:
        from starlette.responses import HTMLResponse

        if request.query_params.get("error"):
            error = request.query_params.get("error")
            return HTMLResponse(
                _google_ads_bootstrap_html(
                    "Authorization failed",
                    f"Google returned: {error}",
                ),
                status_code=400,
            )
        code = request.query_params.get("code")
        if not code:
            return HTMLResponse(
                _google_ads_bootstrap_html(
                    "Authorization failed",
                    "Google did not return an authorization code.",
                ),
                status_code=400,
            )
        try:
            async with self._upstream_oauth_client() as oauth_client:
                tokens = await oauth_client.fetch_token(
                    url=self._upstream_token_endpoint,
                    code=code,
                    redirect_uri=self._google_ads_bootstrap_redirect_uri(),
                    scope=self._GOOGLE_ADS_SCOPE,
                )
        except Exception:
            return HTMLResponse(
                _google_ads_bootstrap_html(
                    "Token exchange failed",
                    "Google accepted the login but did not issue usable tokens.",
                ),
                status_code=500,
            )

        refresh_token = tokens.get("refresh_token")
        if not refresh_token:
            return HTMLResponse(
                _google_ads_bootstrap_html(
                    "No refresh token returned",
                    "Remove this app from your Google Account permissions, then retry.",
                ),
                status_code=400,
            )

        await self._google_ads_bootstrap_result_store.put(
            nonce,
            {
                "status": "ready",
                "client_id": self._upstream_client_id,
                "refresh_token": refresh_token,
                "created_at": int(time.time()),
                "expires_at": int(time.time() + self._RESULT_TTL_SECONDS),
            },
            ttl_seconds=self._RESULT_TTL_SECONDS,
        )
        return HTMLResponse(
            _google_ads_bootstrap_html(
                "Authorization complete",
                "You can close this tab and return to Codex.",
            ),
            status_code=200,
        )

    def _google_ads_bootstrap_redirect_uri(self) -> str:
        return f"{str(self.base_url).rstrip('/')}{self._redirect_path}"

    def _sign_google_ads_bootstrap_state(self, nonce: str, expires_at: int) -> str:
        payload = f"{nonce}.{expires_at}"
        digest = hmac.new(
            self._google_ads_bootstrap_token.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        signature = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return f"{self._STATE_PREFIX}.{payload}.{signature}"

    def _verify_google_ads_bootstrap_state(self, state: str) -> str | None:
        parts = state.split(".")
        if len(parts) != 4 or parts[0] != self._STATE_PREFIX:
            return None
        _, nonce, expires_at_raw, signature = parts
        try:
            expires_at = int(expires_at_raw)
        except ValueError:
            return None
        if expires_at < int(time.time()):
            return None
        expected = self._sign_google_ads_bootstrap_state(nonce, expires_at).rsplit(
            ".", 1
        )[1]
        if not hmac.compare_digest(signature, expected):
            return None
        return nonce

def _google_ads_oauth_bootstrap_provider_class(google_provider_cls: type[Any]) -> type[Any]:
    return type(
        "GoogleAdsOAuthBootstrapProvider",
        (_GoogleAdsOAuthBootstrapMixin, google_provider_cls),
        {},
    )


def _bootstrap_provider(auth: Any) -> Any | None:
    provider = getattr(auth, "provider", auth)
    if hasattr(provider, "google_ads_bootstrap_authorization_url"):
        return provider
    return None


def _bootstrap_request_allowed(request: Any, expected_token: str | None) -> bool:
    if not expected_token:
        return False
    provided = request.headers.get("x-google-ads-bootstrap-token")
    return bool(provided and hmac.compare_digest(str(provided), str(expected_token)))


def _google_ads_bootstrap_html(title: str, message: str) -> str:
    safe_title = _escape_html(title)
    safe_message = _escape_html(message)
    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        "<title>Google Ads OAuth</title>"
        "<style>body{font-family:Arial,sans-serif;margin:3rem;line-height:1.45;"
        "color:#202124}main{max-width:42rem}h1{font-size:1.5rem}</style>"
        f"</head><body><main><h1>{safe_title}</h1><p>{safe_message}</p></main>"
        "</body></html>"
    )


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


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


def _google_ads_access_token_value(access_token: Any | None) -> str:
    if access_token is None:
        raise ConfigError(
            "Authenticated Google OAuth token is required for per-user Google Ads access."
        )
    token_value = str(getattr(access_token, "token", "") or "").strip()
    if not token_value:
        raise ConfigError("Authenticated Google OAuth token did not include an access token.")
    scopes = set(getattr(access_token, "scopes", []) or [])
    if GOOGLE_ADS_OAUTH_SCOPE not in scopes:
        raise ConfigError(
            "Authenticated Google account did not grant Google Ads access. "
            "Reconnect Claude and approve the Google Ads scope."
        )
    return token_value


def _register_friendly_tool(
    mcp: Any,
    dispatcher_factory: Any,
    exposure: ToolExposure,
) -> None:
    async def friendly_tool(
        customer_id: str = "",
        payload: dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        date_range: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        time_segment: str | None = None,
        max_rows: int | None = 1000,
        max_accounts: int | None = None,
        page_size: int | None = None,
        page_token: str | None = None,
        validate_only: bool = True,
        execute: bool = False,
        confirmation_phrase: str | None = None,
        partial_failure: bool = False,
    ) -> dict[str, Any]:
        try:
            return await dispatcher_factory().dispatch(
                exposure.canonical_name,
                customer_id=customer_id or None,
                payload=payload,
                filters=filters,
                date_range=date_range,
                start_date=start_date,
                end_date=end_date,
                time_segment=time_segment,
                max_rows=max_rows,
                max_accounts=max_accounts,
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
    _register_function_tool(mcp, friendly_tool, exposure)


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
        _register_function_tool(mcp, registered, exposure)


def _register_function_tool(mcp: Any, func: Any, exposure: ToolExposure) -> None:
    from fastmcp.tools.function_tool import FunctionTool

    tool = FunctionTool.from_function(
        func,
        name=exposure.registered_name,
        description=exposure.description,
    )
    tool.parameters = parameters_schema_for_exposure(exposure)
    mcp.add_tool(tool)


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
        "google_ads_auth_mode": settings.google_ads_auth_mode,
        "mode": registry.mode,
        "tool_profile": registry.tool_profile,
        "google_ads_configured": readiness["google_ads_configured"],
        "tools_config_source": registry.config_source,
        "exposed_tool_count": len(registry.exposures),
        "legacy_aliases_enabled": registry.legacy_aliases_enabled,
        "generic_service_bridge_enabled": bool(settings.enable_generic_service_bridge),
        "audit_log_enabled": bool(settings.audit_log_path),
        "metadata_cache_ttl_seconds": settings.metadata_cache_ttl_seconds,
        "metadata_cache_max_entries": settings.metadata_cache_max_entries,
        "metadata_snapshot_enabled": bool(settings.metadata_snapshot_path),
        "oauth_token_storage": settings.mcp_token_storage,
        "oauth_allowlist_configured": bool(
            settings.mcp_allowed_emails or settings.mcp_allowed_domains
        ),
        "allow_all_google_users": bool(settings.mcp_allow_all_google_users),
    }


def _oauth_discovery_payload(settings: Any) -> dict[str, Any]:
    base_url = (settings.mcp_base_url or "").rstrip("/")
    return {
        "issuer": f"{base_url}/",
        "authorization_endpoint": f"{base_url}/authorize",
        "token_endpoint": f"{base_url}/token",
        "registration_endpoint": f"{base_url}/register",
        "scopes_supported": _google_oauth_scopes(settings),
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": [
            "client_secret_post",
            "client_secret_basic",
        ],
        "code_challenge_methods_supported": ["S256"],
        "client_id_metadata_document_supported": True,
    }


def _google_ads_readiness_payload(settings: Any) -> dict[str, Any]:
    if settings.google_ads_auth_mode == "per_user_oauth":
        required = {
            "GOOGLE_ADS_DEVELOPER_TOKEN": settings.developer_token,
            "GOOGLE_ADS_MCP_OAUTH_CLIENT_ID": settings.mcp_oauth_client_id,
            "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET": settings.mcp_oauth_client_secret,
            "GOOGLE_ADS_MCP_BASE_URL": settings.mcp_base_url,
        }
        if settings.mcp_token_storage == "firestore":
            required["GOOGLE_PROJECT_ID"] = settings.google_project_id
    else:
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
        "google_ads_auth_mode": settings.google_ads_auth_mode,
        "oauth_token_storage": settings.mcp_token_storage,
        "allow_all_google_users": bool(settings.mcp_allow_all_google_users),
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
