"""Runtime configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


class ConfigError(ValueError):
    """Raised when required runtime configuration is missing or invalid."""


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name, default)
    if value is None:
        return None
    value = value.strip()
    return value or None


@dataclass(frozen=True)
class Settings:
    """Application settings.

    Secrets are intentionally read only from the environment so the repository can be
    public-safe and Cloud Run can inject values from Secret Manager.
    """

    mcp_bearer_token: str | None
    developer_token: str | None
    oauth_client_id: str | None
    oauth_client_secret: str | None
    refresh_token: str | None
    login_customer_id: str | None
    google_project_id: str | None
    api_version: str
    host: str
    port: int
    auth_mode: str
    allow_unauthenticated_mcp: bool
    mcp_mode: str | None
    tools_config_path: str | None
    allow_legacy_write_defaults: bool
    enable_generic_service_bridge: bool
    mcp_oauth_client_id: str | None
    mcp_oauth_client_secret: str | None
    mcp_base_url: str | None
    max_retries: int
    retry_base_seconds: float

    @classmethod
    def from_env(cls) -> "Settings":
        port = int(_env("PORT", "8080") or "8080")
        max_retries = int(_env("GOOGLE_ADS_MAX_RETRIES", "3") or "3")
        retry_base_seconds = float(_env("GOOGLE_ADS_RETRY_BASE_SECONDS", "0.5") or "0.5")
        allow_unauthenticated = (_env("ALLOW_UNAUTHENTICATED_MCP", "false") or "").lower()
        allow_legacy_write_defaults = (
            _env("GOOGLE_ADS_MCP_ALLOW_LEGACY_WRITE_DEFAULTS", "false") or ""
        ).lower()
        enable_generic_service_bridge = (
            _env("GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE", "false") or ""
        ).lower()
        auth_mode = (_env("GOOGLE_ADS_MCP_AUTH_MODE", "bearer") or "bearer").lower()
        return cls(
            mcp_bearer_token=_env("MCP_BEARER_TOKEN"),
            developer_token=_env("GOOGLE_ADS_DEVELOPER_TOKEN"),
            oauth_client_id=_env("GOOGLE_ADS_CLIENT_ID"),
            oauth_client_secret=_env("GOOGLE_ADS_CLIENT_SECRET"),
            refresh_token=_env("GOOGLE_ADS_REFRESH_TOKEN"),
            login_customer_id=_env("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
            google_project_id=_env("GOOGLE_PROJECT_ID") or _env("GOOGLE_CLOUD_PROJECT"),
            api_version=_env("GOOGLE_ADS_API_VERSION", "v24") or "v24",
            host=_env("HOST", "0.0.0.0") or "0.0.0.0",
            port=port,
            auth_mode=auth_mode,
            allow_unauthenticated_mcp=allow_unauthenticated in {"1", "true", "yes"},
            mcp_mode=_env("GOOGLE_ADS_MCP_MODE"),
            tools_config_path=_env("GOOGLE_ADS_MCP_TOOLS_CONFIG"),
            allow_legacy_write_defaults=allow_legacy_write_defaults in {"1", "true", "yes"},
            enable_generic_service_bridge=enable_generic_service_bridge in {"1", "true", "yes"},
            mcp_oauth_client_id=_env("GOOGLE_ADS_MCP_OAUTH_CLIENT_ID"),
            mcp_oauth_client_secret=_env("GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET"),
            mcp_base_url=_env("GOOGLE_ADS_MCP_BASE_URL"),
            max_retries=max_retries,
            retry_base_seconds=retry_base_seconds,
        )

    def require_mcp_auth(self) -> None:
        if self.allow_unauthenticated_mcp:
            return
        if self.auth_mode not in {"bearer", "oauth_proxy"}:
            raise ConfigError(
                "GOOGLE_ADS_MCP_AUTH_MODE must be 'bearer' or 'oauth_proxy'."
            )
        if self.auth_mode == "bearer" and not self.mcp_bearer_token:
            raise ConfigError(
                "MCP_BEARER_TOKEN is required. Set ALLOW_UNAUTHENTICATED_MCP=true only "
                "for local development."
            )
        if self.auth_mode == "oauth_proxy":
            missing = [
                name
                for name, value in {
                    "GOOGLE_ADS_MCP_OAUTH_CLIENT_ID": self.mcp_oauth_client_id,
                    "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET": self.mcp_oauth_client_secret,
                    "GOOGLE_ADS_MCP_BASE_URL": self.mcp_base_url,
                }.items()
                if not value
            ]
            if missing:
                raise ConfigError(f"Missing OAuth MCP auth values: {', '.join(missing)}")

    def require_google_ads(self) -> None:
        missing = [
            name
            for name, value in {
                "GOOGLE_ADS_DEVELOPER_TOKEN": self.developer_token,
                "GOOGLE_ADS_CLIENT_ID": self.oauth_client_id,
                "GOOGLE_ADS_CLIENT_SECRET": self.oauth_client_secret,
                "GOOGLE_ADS_REFRESH_TOKEN": self.refresh_token,
            }.items()
            if not value
        ]
        if missing:
            raise ConfigError(f"Missing required Google Ads environment values: {', '.join(missing)}")

    def google_ads_client_config(self) -> dict[str, object]:
        self.require_google_ads()
        config: dict[str, object] = {
            "developer_token": self.developer_token,
            "client_id": self.oauth_client_id,
            "client_secret": self.oauth_client_secret,
            "refresh_token": self.refresh_token,
            "use_proto_plus": True,
        }
        if self.login_customer_id:
            config["login_customer_id"] = self.login_customer_id
        return config


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()

