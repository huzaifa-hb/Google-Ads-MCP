"""Read-only MCP resource payloads for Google Ads reference material."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .capability_matrix import capability_matrix_payload
from .knowledge_base import ENTRIES
from .tool_catalog import DEFAULT_METRICS
from .tool_config import ToolRegistry


COMMON_SEGMENTS = (
    "segments.date",
    "segments.week",
    "segments.month",
    "segments.device",
    "segments.hour",
    "segments.day_of_week",
    "segments.ad_network_type",
    "segments.click_type",
    "segments.conversion_action",
    "segments.conversion_action_category",
    "segments.geo_target_city",
    "segments.geo_target_country",
)


def discovery_document_resource(api_version: str) -> str:
    return _json(
        {
            "api_version": api_version,
            "name": "Google Ads API reference",
            "kind": "reference-index",
            "field_reference": f"https://developers.google.com/google-ads/api/fields/{api_version}",
            "rest_reference": f"https://developers.google.com/google-ads/api/rest/reference/rest/{api_version}",
            "client_library_reference": "https://developers.google.com/google-ads/api/docs/client-libs",
            "note": (
                "Google Ads API is primarily documented through versioned field and "
                "service references rather than a single committed discovery JSON file."
            ),
        }
    )


def metrics_resource(api_version: str) -> str:
    return _json(
        {
            "api_version": api_version,
            "kind": "metrics-index",
            "metrics": list(DEFAULT_METRICS),
            "source": "Common reporting metrics used by this MCP's friendly report tools.",
            "live_check": "Use metadata_get_google_ads_resource_metadata for resource-specific compatibility.",
        }
    )


def segments_resource(api_version: str) -> str:
    return _json(
        {
            "api_version": api_version,
            "kind": "segments-index",
            "segments": list(COMMON_SEGMENTS),
            "source": "Common GAQL segments used by reports and planning helpers.",
            "live_check": "Use metadata_get_google_ads_resource_metadata for resource-specific compatibility.",
        }
    )


def release_notes_resource(api_version: str) -> str:
    return _json(
        {
            "api_version": api_version,
            "kind": "release-notes-index",
            "latest_release_notes": "https://developers.google.com/google-ads/api/docs/release-notes",
            "version_diffs": "https://developers.google.com/google-ads/api/docs/release-notes#versions",
            "note": "Release notes are linked instead of fetched at runtime to avoid a network dependency.",
        }
    )


def tool_catalog_resource() -> str:
    return _read_doc("tool-catalog.md")


def capability_matrix_resource(registry: ToolRegistry) -> str:
    return _json(capability_matrix_payload(registry))


def gaql_knowledge_base_resource() -> str:
    path = _docs_dir() / "gaql-knowledge-base.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return _json({"entries": [entry.to_dict() for entry in ENTRIES]})


def _read_doc(filename: str) -> str:
    path = _docs_dir() / filename
    if path.exists():
        return path.read_text(encoding="utf-8")
    return ""


def _docs_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "docs"


def _json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True)
