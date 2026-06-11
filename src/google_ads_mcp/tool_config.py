"""Tool exposure configuration for Google Ads MCP."""

from __future__ import annotations

from dataclasses import dataclass
from importlib import resources
from pathlib import Path
import re
from typing import Any

from .config import ConfigError, Settings
from .tool_catalog import FRIENDLY_TOOL_BY_NAME, FRIENDLY_TOOL_SPECS, FriendlyToolSpec, SERVICE_TOOLS
from .tool_implementation import WRITE_BUILDER_TOOLS


MCP_MODES = {"safe_read_only", "validation_only", "write_enabled", "admin_debug"}
CONFIG_FILENAME = "tools_config.yaml"
PREFIX_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass(frozen=True)
class NamespaceConfig:
    enabled: bool
    prefix: str


@dataclass(frozen=True)
class ToolExposure:
    canonical_name: str
    registered_name: str
    namespace: str
    prefix: str
    source: str
    category: str
    tool_mode: str
    read_write: str
    description: str
    friendly_spec: FriendlyToolSpec | None = None
    deprecated: bool = False
    alias_for: str | None = None

    def to_catalog_entry(self) -> dict[str, Any]:
        return {
            "name": self.registered_name,
            "registered_name": self.registered_name,
            "canonical_name": self.canonical_name,
            "namespace": self.namespace,
            "prefix": self.prefix,
            "source": self.source,
            "category": self.category,
            "mode": self.tool_mode,
            "read_write": self.read_write,
            "description": self.description,
            "deprecated": self.deprecated,
            "alias_for": self.alias_for,
        }


@dataclass(frozen=True)
class ToolRegistry:
    mode: str
    config_source: str
    tool_profile: str
    legacy_aliases_enabled: bool
    namespaces: dict[str, NamespaceConfig]
    exposures: tuple[ToolExposure, ...]

    @property
    def registered_names(self) -> set[str]:
        return {exposure.registered_name for exposure in self.exposures}

    def exposures_for(self, canonical_name: str) -> tuple[ToolExposure, ...]:
        return tuple(
            exposure for exposure in self.exposures if exposure.canonical_name == canonical_name
        )

    def has(self, canonical_name: str) -> bool:
        return bool(self.exposures_for(canonical_name))


CORE_TOOL_DEFS: dict[str, dict[str, str]] = {
    "get_tool_catalog": {
        "namespace": "metadata",
        "mode": "metadata",
        "read_write": "read",
        "description": "Return the currently exposed Google Ads MCP tool catalog.",
    },
    "get_capability_matrix": {
        "namespace": "metadata",
        "mode": "metadata",
        "read_write": "read",
        "description": "Return implementation status for the currently exposed tools.",
    },
    "get_server_status": {
        "namespace": "metadata",
        "mode": "metadata",
        "read_write": "read",
        "description": "Return server mode, auth mode, config source, and exposed tool count.",
    },
    "list_google_ads_services": {
        "namespace": "metadata",
        "mode": "metadata",
        "read_write": "read",
        "description": "List service classes available in the installed Google Ads API client.",
    },
    "list_accessible_customers": {
        "namespace": "account",
        "mode": "query",
        "read_write": "read",
        "description": "List customer resource names accessible to the configured OAuth user.",
    },
    "describe_google_ads_service": {
        "namespace": "metadata",
        "mode": "metadata",
        "read_write": "read",
        "description": "Describe callable methods for a Google Ads service.",
    },
    "describe_google_ads_resource": {
        "namespace": "metadata",
        "mode": "metadata",
        "read_write": "read",
        "description": "Describe fields for a Google Ads API resource.",
    },
    "get_google_ads_resource_metadata": {
        "namespace": "metadata",
        "mode": "metadata",
        "read_write": "read",
        "description": "Return selectable fields, filters, metrics, and segments for a resource.",
    },
    "validate_gaql_fields": {
        "namespace": "metadata",
        "mode": "validation",
        "read_write": "read",
        "description": "Validate GAQL SELECT fields against live resource metadata.",
    },
    "suggest_gaql_fields": {
        "namespace": "metadata",
        "mode": "metadata",
        "read_write": "read",
        "description": "Suggest GAQL fields from live resource metadata.",
    },
    "plan_gaql_query": {
        "namespace": "planning",
        "mode": "query_planning",
        "read_write": "read",
        "description": "Build a validated GAQL query plan without executing it.",
    },
    "explain_gaql_error": {
        "namespace": "planning",
        "mode": "query_planning",
        "read_write": "read",
        "description": "Explain common GAQL errors and suggest safe next steps.",
    },
    "query_google_ads_docs": {
        "namespace": "metadata",
        "mode": "kb_lookup",
        "read_write": "read",
        "description": "Query the offline GAQL knowledge base.",
    },
    "validate_google_ads_payload": {
        "namespace": "metadata",
        "mode": "validation",
        "read_write": "read",
        "description": "Validate a protobuf JSON payload against a Google Ads message type.",
    },
    "google_ads_search": {
        "namespace": "generic",
        "mode": "raw_gaql",
        "read_write": "read",
        "description": "Run a GAQL search query.",
    },
    "google_ads_search_stream": {
        "namespace": "generic",
        "mode": "raw_gaql_stream",
        "read_write": "read",
        "description": "Run a GAQL SearchStream query.",
    },
    "google_ads_mutate": {
        "namespace": "generic",
        "mode": "mutate",
        "read_write": "write",
        "description": "Run GoogleAdsService.mutate against arbitrary operations.",
    },
    "google_ads_call_service": {
        "namespace": "generic",
        "mode": "service",
        "read_write": "generic",
        "description": "Call any Google Ads API service method exposed by the client.",
    },
}


DEFAULT_NAMESPACES: dict[str, NamespaceConfig] = {
    "metadata": NamespaceConfig(enabled=True, prefix="metadata"),
    "planning": NamespaceConfig(enabled=True, prefix="planning"),
    "account": NamespaceConfig(enabled=True, prefix="account"),
    "reporting": NamespaceConfig(enabled=True, prefix="reporting"),
    "campaigns": NamespaceConfig(enabled=True, prefix="campaigns"),
    "ad_groups": NamespaceConfig(enabled=True, prefix="adgroups"),
    "ads": NamespaceConfig(enabled=True, prefix="ads"),
    "keywords": NamespaceConfig(enabled=True, prefix="keywords"),
    "assets": NamespaceConfig(enabled=False, prefix="assets"),
    "audiences": NamespaceConfig(enabled=False, prefix="audiences"),
    "conversions": NamespaceConfig(enabled=False, prefix="conversions"),
    "recommendations": NamespaceConfig(enabled=False, prefix="recommendations"),
    "budgets": NamespaceConfig(enabled=True, prefix="budgets"),
    "extensions": NamespaceConfig(enabled=False, prefix="extensions"),
    "bidding": NamespaceConfig(enabled=False, prefix="bidding"),
    "targeting": NamespaceConfig(enabled=False, prefix="targeting"),
    "shopping_pmax": NamespaceConfig(enabled=False, prefix="shoppingpmax"),
    "labels": NamespaceConfig(enabled=False, prefix="labels"),
    "feeds": NamespaceConfig(enabled=False, prefix="feeds"),
    "mutations": NamespaceConfig(enabled=False, prefix="mutate"),
    "bulk": NamespaceConfig(enabled=False, prefix="bulk"),
    "generic": NamespaceConfig(enabled=False, prefix="generic"),
}
LEAN_PROFILE_NAMESPACES = {
    "metadata",
    "planning",
    "account",
    "reporting",
    "campaigns",
    "ad_groups",
    "ads",
    "keywords",
    "budgets",
}
LEAN_PROFILE_TOOL_NAMES = {
    "get_tool_catalog",
    "get_capability_matrix",
    "get_server_status",
    "list_accessible_customers",
    "describe_google_ads_resource",
    "get_google_ads_resource_metadata",
    "validate_gaql_fields",
    "suggest_gaql_fields",
    "query_google_ads_docs",
    "plan_gaql_query",
    "explain_gaql_error",
    "get_account_info",
    "list_customers",
    "get_mcc_hierarchy",
    "get_account_settings",
    "list_campaigns",
    "get_campaign",
    "list_ad_groups",
    "get_ad_group",
    "list_ads",
    "get_ad",
    "list_keywords",
    "get_keyword",
    "list_budgets",
    "get_budget",
    "execute_gaql_query",
    "get_campaign_metrics",
    "get_ad_group_metrics",
    "get_ad_metrics",
    "get_keyword_metrics",
    "get_search_terms_report",
    "get_device_performance",
    "get_geo_performance",
    "get_landing_page_report",
    "get_change_history_report",
}
STANDARD_PROFILE_NAMESPACES = {
    "metadata",
    "planning",
    "account",
    "reporting",
    "campaigns",
    "ad_groups",
    "ads",
    "keywords",
    "assets",
    "audiences",
    "conversions",
    "recommendations",
}
AGENCY_WRITE_PROFILE_NAMESPACES = LEAN_PROFILE_NAMESPACES | {
    "assets",
    "bulk",
    "extensions",
    "labels",
}
FULL_PROFILE_NAMESPACES = set(DEFAULT_NAMESPACES)
TOOL_PROFILE_NAMESPACES = {
    "lean": LEAN_PROFILE_NAMESPACES,
    "standard": STANDARD_PROFILE_NAMESPACES,
    "agency_write": AGENCY_WRITE_PROFILE_NAMESPACES,
    "advanced_mutate": AGENCY_WRITE_PROFILE_NAMESPACES,
    "full": FULL_PROFILE_NAMESPACES,
}
PROFILE_WRITE_ALLOWLISTS = {
    "agency_write": WRITE_BUILDER_TOOLS,
    "advanced_mutate": WRITE_BUILDER_TOOLS | {"google_ads_mutate"},
}
PROFILE_FORCED_TOOLS = {
    "advanced_mutate": {"google_ads_mutate"},
}


def load_tool_registry(settings: Settings, cwd: Path | None = None) -> ToolRegistry:
    raw_config, source, explicit_config = _load_raw_config(settings, cwd or Path.cwd())
    if settings.mcp_tool_profile:
        raw_config = {
            **raw_config,
            "tool_profile": settings.mcp_tool_profile,
            "_tool_profile_explicit": True,
        }
        source = f"{source}+profile:{settings.mcp_tool_profile}"
    if settings.mcp_mode:
        raw_config = {**raw_config, "mode": settings.mcp_mode}
    elif settings.allow_legacy_write_defaults and not explicit_config:
        raw_config = _legacy_config()
        source = "legacy-env-defaults"
    if settings.enable_generic_service_bridge and raw_config.get("mode") == "admin_debug":
        raw_tools = dict(raw_config.get("tools", {}))
        raw_tools["google_ads_call_service"] = {"enabled": True}
        raw_config = {**raw_config, "tools": raw_tools}
    return build_tool_registry(raw_config, source=source)


def build_tool_registry(raw_config: dict[str, Any], *, source: str = "memory") -> ToolRegistry:
    mode = str(raw_config.get("mode", "safe_read_only"))
    if mode not in MCP_MODES:
        allowed = ", ".join(sorted(MCP_MODES))
        raise ConfigError(f"Invalid Google Ads MCP mode '{mode}'. Allowed: {allowed}.")

    tool_profile = _normalize_tool_profile(raw_config.get("tool_profile"))
    namespace_defaults = _profile_namespace_defaults(tool_profile)
    raw_namespaces = raw_config.get("namespaces", {})
    if raw_config.get("_tool_profile_explicit"):
        raw_namespaces = _namespace_prefix_overrides(raw_namespaces)
    namespaces = _namespace_config(raw_namespaces, defaults=namespace_defaults)
    tool_overrides = _tool_overrides(raw_config.get("tools", {}))
    legacy_aliases_enabled = _legacy_aliases_enabled(raw_config.get("legacy_aliases", {}))
    known_tools = set(CORE_TOOL_DEFS) | set(FRIENDLY_TOOL_BY_NAME)
    unknown = sorted(set(tool_overrides) - known_tools)
    if unknown:
        raise ConfigError(f"Unknown tool(s) in tools config: {', '.join(unknown)}")

    exposures: list[ToolExposure] = []
    for canonical_name, definition in CORE_TOOL_DEFS.items():
        exposures.extend(
            _exposures_for_tool(
                canonical_name=canonical_name,
                namespace=definition["namespace"],
                category=definition["namespace"],
                tool_mode=definition["mode"],
                read_write=definition["read_write"],
                description=definition["description"],
                source="core",
                mode=mode,
                namespaces=namespaces,
                tool_overrides=tool_overrides,
                legacy_aliases_enabled=legacy_aliases_enabled,
                friendly_spec=None,
                tool_profile=tool_profile,
            )
        )

    for spec in FRIENDLY_TOOL_SPECS:
        read_write = classify_friendly_read_write(spec)
        namespace = _friendly_namespace(spec, read_write, namespaces)
        exposures.extend(
            _exposures_for_tool(
                canonical_name=spec.alias_for or spec.name,
                registered_base_name=spec.name,
                config_name=spec.name,
                namespace=namespace,
                category=spec.category,
                tool_mode=spec.mode,
                read_write=read_write,
                description=spec.description,
                source="friendly",
                mode=mode,
                namespaces=namespaces,
                tool_overrides=tool_overrides,
                legacy_aliases_enabled=legacy_aliases_enabled,
                friendly_spec=spec,
                tool_profile=tool_profile,
                deprecated=spec.deprecated,
                alias_for=spec.alias_for,
            )
        )

    names = [exposure.registered_name for exposure in exposures]
    if len(names) != len(set(names)):
        duplicates = sorted({name for name in names if names.count(name) > 1})
        raise ConfigError(f"Tool config creates duplicate registered names: {', '.join(duplicates)}")

    return ToolRegistry(
        mode=mode,
        config_source=source,
        tool_profile=tool_profile,
        legacy_aliases_enabled=legacy_aliases_enabled,
        namespaces=namespaces,
        exposures=tuple(exposures),
    )


def classify_friendly_read_write(spec: FriendlyToolSpec) -> str:
    if spec.mode in {"query", "report", "raw_gaql", "unsupported"}:
        return "read"
    if spec.mode == "negative_keyword":
        return "read" if spec.name.startswith("list_") else "write"
    if spec.mode == "service":
        return "read" if spec.name in SERVICE_TOOLS else "generic"
    return "write"


def _exposures_for_tool(
    *,
    canonical_name: str,
    registered_base_name: str | None = None,
    config_name: str | None = None,
    namespace: str,
    category: str,
    tool_mode: str,
    read_write: str,
    description: str,
    source: str,
    mode: str,
    namespaces: dict[str, NamespaceConfig],
    tool_overrides: dict[str, bool],
    legacy_aliases_enabled: bool,
    friendly_spec: FriendlyToolSpec | None,
    tool_profile: str,
    deprecated: bool = False,
    alias_for: str | None = None,
) -> list[ToolExposure]:
    config_name = config_name or canonical_name
    profile_requested = (
        (deprecated and tool_profile in {"standard", "full"})
        or canonical_name in PROFILE_FORCED_TOOLS.get(tool_profile, set())
    )
    if not _tool_is_enabled(
        config_name,
        namespace,
        tool_mode,
        read_write,
        mode,
        namespaces,
        tool_overrides,
        force_requested=profile_requested,
        tool_profile=tool_profile,
    ):
        return []

    namespace_config = namespaces[namespace]
    base_name = registered_base_name or canonical_name
    registered_names = [_registered_name(base_name, namespace_config.prefix)]
    if canonical_name in {"get_tool_catalog", "get_capability_matrix", "get_server_status"}:
        registered_names = [canonical_name]
    elif legacy_aliases_enabled:
        registered_names.append(base_name)

    return [
        ToolExposure(
            canonical_name=canonical_name,
            registered_name=registered_name,
            namespace=namespace,
            prefix=namespace_config.prefix,
            source=source,
            category=category,
            tool_mode=tool_mode,
            read_write=read_write,
            description=description,
            friendly_spec=friendly_spec,
            deprecated=deprecated,
            alias_for=alias_for,
        )
        for registered_name in registered_names
    ]


def _tool_is_enabled(
    canonical_name: str,
    namespace: str,
    tool_mode: str,
    read_write: str,
    mode: str,
    namespaces: dict[str, NamespaceConfig],
    tool_overrides: dict[str, bool],
    force_requested: bool = False,
    tool_profile: str = "custom",
) -> bool:
    if canonical_name in tool_overrides and not tool_overrides[canonical_name]:
        return False
    namespace_config = namespaces.get(namespace)
    if namespace_config is None:
        raise ConfigError(f"Tool '{canonical_name}' uses unknown namespace '{namespace}'.")
    if not _profile_allows_tool(
        tool_profile=tool_profile,
        canonical_name=canonical_name,
        tool_mode=tool_mode,
        read_write=read_write,
    ):
        return False
    if canonical_name in tool_overrides and tool_overrides[canonical_name]:
        requested = True
    else:
        if tool_profile == "lean" and canonical_name not in LEAN_PROFILE_TOOL_NAMES:
            return False
        requested = (
            force_requested
            or
            namespace_config.enabled
            or canonical_name in {"get_tool_catalog", "get_capability_matrix", "get_server_status"}
            or (
                read_write == "write"
                and bool(namespaces.get("mutations") and namespaces["mutations"].enabled)
            )
        )
    if not requested:
        return False
    if mode == "safe_read_only":
        return read_write == "read"
    if mode == "validation_only":
        return read_write in {"read", "write"}
    if mode == "write_enabled":
        return read_write in {"read", "write"}
    return True


def _profile_allows_tool(
    *,
    tool_profile: str,
    canonical_name: str,
    tool_mode: str,
    read_write: str,
) -> bool:
    allowed_writes = PROFILE_WRITE_ALLOWLISTS.get(tool_profile)
    if allowed_writes is None:
        return True
    if tool_mode == "unsupported":
        return False
    if read_write == "write":
        return canonical_name in allowed_writes
    if read_write == "generic":
        return False
    return True


def _registered_name(canonical_name: str, prefix: str) -> str:
    return f"{prefix}_{canonical_name}"


def _friendly_namespace(
    spec: FriendlyToolSpec,
    read_write: str,
    namespaces: dict[str, NamespaceConfig],
) -> str:
    if spec.category in namespaces:
        return spec.category
    if spec.mode in {"report", "raw_gaql"}:
        return "reporting"
    if read_write == "write":
        return "mutations"
    return "metadata"


def _normalize_tool_profile(raw_profile: Any) -> str:
    profile = str(raw_profile or "custom").strip().lower()
    if profile == "custom":
        return profile
    if profile not in TOOL_PROFILE_NAMESPACES:
        allowed = ", ".join(sorted(TOOL_PROFILE_NAMESPACES))
        raise ConfigError(f"Invalid GOOGLE_ADS_MCP_TOOL_PROFILE '{profile}'. Allowed: {allowed}.")
    return profile


def _profile_namespace_defaults(profile: str) -> dict[str, NamespaceConfig]:
    if profile == "custom":
        return DEFAULT_NAMESPACES
    enabled_namespaces = TOOL_PROFILE_NAMESPACES[profile]
    return {
        name: NamespaceConfig(enabled=name in enabled_namespaces, prefix=config.prefix)
        for name, config in DEFAULT_NAMESPACES.items()
    }


def _namespace_prefix_overrides(raw_namespaces: Any) -> Any:
    if not isinstance(raw_namespaces, dict):
        return raw_namespaces
    overrides: dict[str, dict[str, Any]] = {}
    for name, raw_config in raw_namespaces.items():
        if isinstance(raw_config, dict) and "prefix" in raw_config:
            overrides[name] = {"prefix": raw_config["prefix"]}
    return overrides


def _namespace_config(
    raw_namespaces: Any,
    *,
    defaults: dict[str, NamespaceConfig],
) -> dict[str, NamespaceConfig]:
    if raw_namespaces is None:
        raw_namespaces = {}
    if not isinstance(raw_namespaces, dict):
        raise ConfigError("tools_config.yaml namespaces must be a mapping.")
    namespaces = dict(defaults)
    for name, raw_config in raw_namespaces.items():
        if not isinstance(name, str) or name not in DEFAULT_NAMESPACES:
            raise ConfigError(f"Unknown tools_config namespace '{name}'.")
        if raw_config is None:
            raw_config = {}
        if not isinstance(raw_config, dict):
            raise ConfigError(f"Namespace '{name}' must be a mapping.")
        enabled = bool(raw_config.get("enabled", namespaces[name].enabled))
        prefix = str(raw_config.get("prefix", namespaces[name].prefix))
        if not PREFIX_RE.fullmatch(prefix):
            raise ConfigError(
                f"Namespace '{name}' prefix '{prefix}' is invalid. Use lowercase letters, "
                "digits, and underscores, starting with a letter."
            )
        namespaces[name] = NamespaceConfig(enabled=enabled, prefix=prefix)
    return namespaces


def _tool_overrides(raw_tools: Any) -> dict[str, bool]:
    if raw_tools is None:
        return {}
    if not isinstance(raw_tools, dict):
        raise ConfigError("tools_config.yaml tools must be a mapping.")
    overrides: dict[str, bool] = {}
    for name, raw_config in raw_tools.items():
        if not isinstance(name, str):
            raise ConfigError("Tool config keys must be strings.")
        if isinstance(raw_config, bool):
            overrides[name] = raw_config
            continue
        if raw_config is None:
            raw_config = {}
        if not isinstance(raw_config, dict):
            raise ConfigError(f"Tool '{name}' config must be a mapping.")
        if "enabled" in raw_config:
            overrides[name] = bool(raw_config["enabled"])
    return overrides


def _legacy_aliases_enabled(raw_legacy_aliases: Any) -> bool:
    if raw_legacy_aliases is None:
        return False
    if isinstance(raw_legacy_aliases, bool):
        return raw_legacy_aliases
    if not isinstance(raw_legacy_aliases, dict):
        raise ConfigError("legacy_aliases must be a mapping.")
    return bool(raw_legacy_aliases.get("enabled", False))


def _load_raw_config(settings: Settings, cwd: Path) -> tuple[dict[str, Any], str, bool]:
    if settings.tools_config_path:
        path = Path(settings.tools_config_path)
        if not path.exists():
            raise ConfigError(f"GOOGLE_ADS_MCP_TOOLS_CONFIG does not exist: {path}")
        return _load_yaml_file(path), str(path), True

    cwd_config = cwd / CONFIG_FILENAME
    if cwd_config.exists():
        return _load_yaml_file(cwd_config), str(cwd_config), True

    bundled = resources.files("google_ads_mcp").joinpath("default_tools_config.yaml")
    with bundled.open("r", encoding="utf-8") as handle:
        return _load_yaml_text(handle.read()), "bundled-default", False


def _load_yaml_file(path: Path) -> dict[str, Any]:
    return _load_yaml_text(path.read_text(encoding="utf-8"))


def _load_yaml_text(text: str) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:  # pragma: no cover - dependency is required by pyproject.
        raise ConfigError("PyYAML is required to load tools_config.yaml.") from exc
    else:
        parsed = yaml.safe_load(text) or {}
    if not isinstance(parsed, dict):
        raise ConfigError("tools_config.yaml must contain a mapping at the top level.")
    return parsed


def _legacy_config() -> dict[str, Any]:
    namespaces = {
        name: {"enabled": True, "prefix": config.prefix}
        for name, config in DEFAULT_NAMESPACES.items()
    }
    return {
        "mode": "admin_debug",
        "legacy_aliases": {"enabled": True},
        "namespaces": namespaces,
        "tools": {},
    }
