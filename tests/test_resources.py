from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.resources import (
    capability_matrix_resource,
    discovery_document_resource,
    metrics_resource,
    release_notes_resource,
    segments_resource,
    tool_catalog_resource,
    gaql_knowledge_base_resource,
)
from google_ads_mcp.tool_config import build_tool_registry


class ResourcePayloadTests(unittest.TestCase):
    def test_discovery_document_is_versioned(self) -> None:
        payload = json.loads(discovery_document_resource("v24"))

        self.assertEqual(payload["api_version"], "v24")
        self.assertEqual(payload["kind"], "reference-index")
        self.assertIn("/v24", payload["field_reference"])

    def test_metrics_and_segments_resources_are_versioned(self) -> None:
        metrics = json.loads(metrics_resource("v24"))
        segments = json.loads(segments_resource("v24"))

        self.assertEqual(metrics["api_version"], "v24")
        self.assertIn("metrics.clicks", metrics["metrics"])
        self.assertEqual(segments["api_version"], "v24")
        self.assertIn("segments.date", segments["segments"])

    def test_release_notes_resource_links_latest_notes(self) -> None:
        payload = json.loads(release_notes_resource("v24"))

        self.assertEqual(payload["api_version"], "v24")
        self.assertIn("release-notes", payload["latest_release_notes"])

    def test_capability_matrix_resource_matches_safe_registry(self) -> None:
        registry = build_tool_registry({"mode": "safe_read_only"})
        payload = json.loads(capability_matrix_resource(registry))

        self.assertEqual(payload["mode"], "safe_read_only")
        self.assertEqual(payload["tool_count"], len(registry.exposures))

    def test_docs_resources_have_runtime_fallbacks(self) -> None:
        with patch("google_ads_mcp.resources._docs_dir", return_value=Path("missing-docs")):
            self.assertIn("Google Ads MCP Tool Catalog", tool_catalog_resource())
            self.assertIn("GAQL Knowledge Base", gaql_knowledge_base_resource())


if __name__ == "__main__":
    unittest.main()
