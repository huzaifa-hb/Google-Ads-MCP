"""Capability matrix generation shared by docs and MCP tools."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .tool_catalog import FriendlyToolSpec, REPORT_RESOURCES, SERVICE_TOOLS, UNSUPPORTED_TOOLS
from .tool_config import CORE_TOOL_DEFS, ToolExposure, ToolRegistry, classify_friendly_read_write


DIRECT_MUTATION_TOOLS = {
    "create_search_campaign",
    "create_display_campaign",
    "create_video_campaign",
    "create_shopping_campaign",
    "create_pmax_campaign",
    "create_demand_gen_campaign",
    "create_app_campaign",
    "create_smart_campaign",
    "create_budget",
    "create_shared_budget",
    "update_budget",
    "update_shared_budget",
    "remove_budget",
    "link_budget_to_campaign",
    "update_campaign",
    "update_network_settings",
    "bulk_pause_campaigns",
    "bulk_enable_campaigns",
    "pause_campaign",
    "enable_campaign",
    "remove_campaign",
    "create_ad_group",
    "update_ad_group",
    "pause_ad_group",
    "enable_ad_group",
    "remove_ad_group",
    "create_responsive_search_ad",
    "pause_ad",
    "enable_ad",
    "remove_ad",
    "add_keywords",
    "bulk_add_keywords",
    "update_keyword_bid",
    "bulk_update_bids",
    "pause_keyword",
    "enable_keyword",
    "remove_keywords",
    "bulk_add_negative_keywords",
    "create_sitelink",
    "create_callout",
    "create_text_asset",
    "create_video_asset",
    "create_label",
    "update_label",
    "remove_label",
    "apply_campaign_label",
    "remove_campaign_label",
    "apply_ad_group_label",
    "remove_ad_group_label",
    "apply_ad_label",
    "remove_ad_label",
    "apply_keyword_label",
    "remove_keyword_label",
    "apply_label_to_campaign",
    "apply_label_to_ad_group",
    "apply_label_to_ad",
    "apply_label_to_keyword",
    "remove_label_from_campaign",
    "remove_label_from_ad_group",
    "remove_label_from_ad",
    "remove_label_from_keyword",
}

DIRECT_NEGATIVE_KEYWORD_TOOLS = {
    "add_negative_keywords_ad_group",
    "add_negative_keywords_campaign",
    "remove_negative_keywords_ad_group",
    "remove_negative_keywords_campaign",
    "create_shared_negative_keyword_list",
    "add_keywords_to_shared_list",
    "remove_keywords_from_shared_list",
    "apply_shared_list_to_campaign",
    "remove_shared_list_from_campaign",
}


@dataclass(frozen=True)
class CapabilityRow:
    tool: str
    namespace: str
    mode: str
    implementation_status: str
    backend: str
    read_write: str
    requires_eligibility: str
    notes: str
    canonical_name: str
    registered_name: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool": self.tool,
            "registered_name": self.registered_name or self.tool,
            "canonical_name": self.canonical_name,
            "namespace": self.namespace,
            "mode": self.mode,
            "implementation_status": self.implementation_status,
            "backend": self.backend,
            "read_write": self.read_write,
            "requires_eligibility": self.requires_eligibility,
            "notes": self.notes,
        }


def build_capability_matrix(registry: ToolRegistry | None = None) -> list[CapabilityRow]:
    """Build capability rows for all known tools or only currently exposed tools."""

    if registry is not None:
        return [_row_for_exposure(exposure) for exposure in registry.exposures]

    rows: list[CapabilityRow] = []
    for name, definition in CORE_TOOL_DEFS.items():
        rows.append(
            CapabilityRow(
                tool=name,
                canonical_name=name,
                namespace=definition["namespace"],
                mode=definition["mode"],
                implementation_status=_core_status(name, definition["read_write"]),
                backend=_core_backend(name),
                read_write=definition["read_write"],
                requires_eligibility=(
                    "depends"
                    if name in {"google_ads_mutate", "google_ads_call_service"}
                    else "no"
                ),
                notes=definition["description"],
            )
        )
    return rows


def build_full_capability_matrix(specs: tuple[FriendlyToolSpec, ...]) -> list[CapabilityRow]:
    """Build the committed full matrix from core definitions plus friendly specs."""

    rows = build_capability_matrix()
    rows.extend(_row_for_spec(spec) for spec in specs)
    return sorted(rows, key=lambda row: (row.namespace, row.tool))


def capability_matrix_payload(registry: ToolRegistry) -> dict[str, Any]:
    rows = build_capability_matrix(registry)
    return {
        "mode": registry.mode,
        "tools_config_source": registry.config_source,
        "tool_count": len(rows),
        "tools": [row.to_dict() for row in rows],
    }


def capability_matrix_markdown(rows: list[CapabilityRow]) -> str:
    lines = [
        "# Google Ads MCP Capability Matrix",
        "",
        "This file is generated from `src/google_ads_mcp/tool_catalog.py`, "
        "`src/google_ads_mcp/tool_config.py`, and `src/google_ads_mcp/capability_matrix.py`.",
        "",
        "| Tool | Namespace | Mode | Implementation Status | Backend | Read/Write | Requires Eligibility | Notes |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        lines.append(
            "| "
            + " | ".join(
                [
                    f"`{row.tool}`",
                    f"`{row.namespace}`",
                    f"`{row.mode}`",
                    f"`{row.implementation_status}`",
                    _escape(row.backend),
                    f"`{row.read_write}`",
                    row.requires_eligibility,
                    _escape(row.notes),
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _row_for_exposure(exposure: ToolExposure) -> CapabilityRow:
    if exposure.friendly_spec is not None:
        base = _row_for_spec(exposure.friendly_spec)
    else:
        base = CapabilityRow(
            tool=exposure.canonical_name,
            canonical_name=exposure.canonical_name,
            namespace=exposure.namespace,
            mode=exposure.tool_mode,
            implementation_status=_core_status(exposure.canonical_name, exposure.read_write),
            backend=_core_backend(exposure.canonical_name),
            read_write=exposure.read_write,
            requires_eligibility=(
                "depends"
                if exposure.canonical_name in {"google_ads_mutate", "google_ads_call_service"}
                else "no"
            ),
            notes=exposure.description,
        )
    return CapabilityRow(
        tool=exposure.registered_name,
        registered_name=exposure.registered_name,
        canonical_name=exposure.canonical_name,
        namespace=exposure.namespace,
        mode=exposure.tool_mode,
        implementation_status=base.implementation_status,
        backend=base.backend,
        read_write=exposure.read_write,
        requires_eligibility=base.requires_eligibility,
        notes=base.notes,
    )


def _row_for_spec(spec: FriendlyToolSpec) -> CapabilityRow:
    read_write = classify_friendly_read_write(spec)
    return CapabilityRow(
        tool=spec.name,
        canonical_name=spec.name,
        namespace=spec.category,
        mode=spec.mode,
        implementation_status=_friendly_status(spec),
        backend=_friendly_backend(spec),
        read_write=read_write,
        requires_eligibility=_requires_eligibility(spec),
        notes=spec.notes or spec.description,
    )


def _core_status(name: str, read_write: str) -> str:
    if name in {"google_ads_mutate", "google_ads_call_service"}:
        return "generic_routed"
    if read_write == "generic":
        return "generic_routed"
    return "hand_implemented"


def _core_backend(name: str) -> str:
    backends = {
        "google_ads_search": "GoogleAdsService.Search",
        "google_ads_search_stream": "GoogleAdsService.SearchStream",
        "google_ads_mutate": "GoogleAdsService.Mutate",
        "google_ads_call_service": "Generic Google Ads service bridge",
        "list_accessible_customers": "CustomerService.ListAccessibleCustomers",
        "describe_google_ads_resource": "GoogleAdsFieldService.SearchGoogleAdsFields",
        "get_google_ads_resource_metadata": "GoogleAdsFieldService.SearchGoogleAdsFields",
        "validate_gaql_fields": "GoogleAdsFieldService.SearchGoogleAdsFields",
        "suggest_gaql_fields": "GoogleAdsFieldService.SearchGoogleAdsFields",
        "plan_gaql_query": "Metadata-backed GAQL planner",
        "explain_gaql_error": "Static GAQL error helper",
        "query_google_ads_docs": "Offline GAQL knowledge base",
        "validate_google_ads_payload": "Protobuf JSON parser",
        "get_capability_matrix": "Local tool registry",
    }
    return backends.get(name, "Local metadata/introspection")


def _friendly_status(spec: FriendlyToolSpec) -> str:
    if spec.name == "create_similar_audience":
        return "deprecated"
    if spec.name in UNSUPPORTED_TOOLS:
        if "eligibility" in (spec.notes or "").lower():
            return "eligibility_gated"
        return "unsupported_by_design"
    if spec.mode == "service" or spec.name in SERVICE_TOOLS:
        return "generic_routed"
    if spec.mode in {"query", "report"}:
        if spec.mode == "report" and spec.name not in REPORT_RESOURCES:
            return "unmapped_report"
        return "hand_implemented"
    if spec.mode == "negative_keyword":
        if spec.name.startswith("list_") or spec.name in DIRECT_NEGATIVE_KEYWORD_TOOLS:
            return "hand_implemented"
        return "operation_template"
    if spec.mode == "raw_gaql":
        return "generic_routed"
    if spec.name == "batch_mutate":
        return "generic_routed"
    if spec.name in DIRECT_MUTATION_TOOLS:
        return "hand_implemented"
    return "operation_template"


def _friendly_backend(spec: FriendlyToolSpec) -> str:
    if spec.mode == "query":
        return f"GoogleAdsService.Search FROM {spec.resource or 'resource'}"
    if spec.mode == "report":
        return f"GoogleAdsService.Search report FROM {spec.resource or 'campaign'}"
    if spec.mode == "raw_gaql":
        return "GoogleAdsService.Search"
    if spec.mode == "negative_keyword":
        return "GoogleAdsService.Search or GoogleAdsService.Mutate"
    if spec.mode == "service" or spec.name in SERVICE_TOOLS:
        return "Google Ads service bridge"
    if spec.mode == "unsupported":
        return "n/a"
    return "GoogleAdsService.Mutate"


def _requires_eligibility(spec: FriendlyToolSpec) -> str:
    text = f"{spec.name} {spec.description} {spec.notes or ''}".lower()
    if any(marker in text for marker in ("eligibility", "invoice", "billing", "reach planner")):
        return "yes"
    if spec.mode == "service":
        return "depends"
    return "no"


def _escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")
