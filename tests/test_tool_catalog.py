from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.tool_catalog import FRIENDLY_TOOL_BY_NAME, FRIENDLY_TOOL_SPECS


class ToolCatalogTests(unittest.TestCase):
    def test_tool_names_are_unique(self) -> None:
        names = [spec.name for spec in FRIENDLY_TOOL_SPECS]
        self.assertEqual(len(names), len(set(names)))

    def test_requested_key_tools_are_present(self) -> None:
        for name in [
            "create_pmax_campaign",
            "create_demand_gen_campaign",
            "add_negative_keywords_ad_group",
            "add_negative_keywords_campaign",
            "create_shared_negative_keyword_list",
            "upload_offline_conversions",
            "get_campaign_metrics",
            "execute_gaql_query",
            "batch_mutate",
        ]:
            self.assertIn(name, FRIENDLY_TOOL_BY_NAME)

    def test_similar_audience_is_explicitly_unsupported(self) -> None:
        self.assertEqual(FRIENDLY_TOOL_BY_NAME["create_similar_audience"].mode, "unsupported")


if __name__ == "__main__":
    unittest.main()
