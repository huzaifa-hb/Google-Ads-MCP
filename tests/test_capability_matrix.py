from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.capability_matrix import (
    build_capability_matrix,
    build_full_capability_matrix,
    capability_matrix_payload,
)
from google_ads_mcp.tool_catalog import FRIENDLY_TOOL_SPECS
from google_ads_mcp.tool_config import build_tool_registry


class CapabilityMatrixTests(unittest.TestCase):
    def test_exposed_matrix_matches_registered_tool_set(self) -> None:
        registry = build_tool_registry({"mode": "safe_read_only"})

        payload = capability_matrix_payload(registry)
        matrix_names = {row["registered_name"] for row in payload["tools"]}

        self.assertEqual(matrix_names, registry.registered_names)
        self.assertIn("get_capability_matrix", matrix_names)

    def test_full_matrix_classifies_unsupported_and_generic_tools(self) -> None:
        rows = build_full_capability_matrix(FRIENDLY_TOOL_SPECS)
        by_name = {row.tool: row for row in rows}

        self.assertEqual(by_name["create_similar_audience"].implementation_status, "deprecated")
        self.assertEqual(by_name["get_keyword_ideas"].implementation_status, "generic_routed")
        self.assertEqual(by_name["google_ads_call_service"].implementation_status, "generic_routed")
        self.assertEqual(by_name["pause_campaign"].implementation_status, "hand_implemented")
        self.assertEqual(
            by_name["create_responsive_search_ad"].implementation_status,
            "hand_implemented",
        )
        self.assertEqual(by_name["apply_label_to_campaign"].implementation_status, "hand_implemented")
        self.assertEqual(
            by_name["remove_label_from_keyword"].implementation_status,
            "hand_implemented",
        )
        self.assertEqual(by_name["create_dsa_page_feed"].implementation_status, "operation_template")
        self.assertEqual(by_name["get_topic_report"].implementation_status, "unsupported_by_design")

    def test_safe_read_only_matrix_contains_only_read_classes(self) -> None:
        registry = build_tool_registry({"mode": "safe_read_only"})

        rows = build_capability_matrix(registry)

        self.assertTrue(all(row.read_write == "read" for row in rows))


if __name__ == "__main__":
    unittest.main()
