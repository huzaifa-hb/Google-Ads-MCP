from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.tool_catalog import FRIENDLY_TOOL_BY_NAME, FRIENDLY_TOOL_SPECS, REPORT_RESOURCES


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

    def test_reports_do_not_fall_back_to_generic_campaign_mapping(self) -> None:
        for spec in FRIENDLY_TOOL_SPECS:
            if spec.mode == "report":
                self.assertIn(spec.name, REPORT_RESOURCES)
                self.assertIsNotNone(spec.resource)
                self.assertNotEqual(spec.fields, ("campaign.id",))

    def test_uncertain_reports_are_downgraded_to_unsupported(self) -> None:
        for name in ["get_topic_report", "get_reach_frequency_report", "get_paid_organic_report"]:
            self.assertEqual(FRIENDLY_TOOL_BY_NAME[name].mode, "unsupported")


if __name__ == "__main__":
    unittest.main()
