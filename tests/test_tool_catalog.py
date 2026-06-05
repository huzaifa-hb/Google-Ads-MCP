from __future__ import annotations

import unittest
from unittest.mock import patch

import _bootstrap  # noqa: F401
try:
    from google.ads.googleads.v24.common.types.metrics import Metrics
    from google.ads.googleads.v24.resources.types.asset_group_asset import AssetGroupAsset
except ImportError:  # pragma: no cover - depends on optional local package install
    Metrics = None  # type: ignore[assignment]
    AssetGroupAsset = None  # type: ignore[assignment]
import google_ads_mcp.tool_catalog as catalog
from google_ads_mcp.tool_catalog import (
    DEFAULT_METRICS,
    FRIENDLY_TOOL_BY_NAME,
    FRIENDLY_TOOL_SPECS,
    REPORT_RESOURCES,
    build_tool_specs,
)


class ToolCatalogTests(unittest.TestCase):
    def test_tool_names_are_unique(self) -> None:
        names = [spec.name for spec in FRIENDLY_TOOL_SPECS]
        self.assertEqual(len(names), len(set(names)))

    def test_duplicate_tool_names_raise(self) -> None:
        duplicate_groups = {
            "account": [
                ("list_customers", "first description"),
                ("list_customers", "second description"),
            ],
        }

        with patch.object(catalog, "TOOL_GROUPS", duplicate_groups):
            with self.assertRaisesRegex(ValueError, "Duplicate friendly tool name: list_customers"):
                build_tool_specs()

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
        for name in [
            "get_topic_report",
            "get_reach_frequency_report",
            "get_paid_organic_report",
            "get_auction_insights",
            "get_keyword_bid_estimates",
            "get_ad_preview",
            "get_ad_diagnosis",
        ]:
            self.assertEqual(FRIENDLY_TOOL_BY_NAME[name].mode, "unsupported")

    def test_fixed_report_resources_and_metrics(self) -> None:
        self.assertEqual(FRIENDLY_TOOL_BY_NAME["get_household_income_report"].resource, "income_range_view")
        self.assertEqual(
            FRIENDLY_TOOL_BY_NAME["get_audience_performance_report"].resource,
            "ad_group_audience_view",
        )
        self.assertIn(
            "ad_group_criterion.criterion_id",
            FRIENDLY_TOOL_BY_NAME["get_age_range_report"].fields,
        )
        self.assertNotIn("metrics.", " ".join(FRIENDLY_TOOL_BY_NAME["get_change_history_report"].fields))
        self.assertNotIn("segments.hour", FRIENDLY_TOOL_BY_NAME["get_ad_schedule_report"].fields)

    def test_sensitive_reports_use_curated_metrics(self) -> None:
        search_metrics = {
            "metrics.search_impression_share",
            "metrics.search_budget_lost_impression_share",
            "metrics.search_rank_lost_impression_share",
            "metrics.search_top_impression_share",
            "metrics.search_absolute_top_impression_share",
        }
        video_metrics = {"metrics.video_trueview_views", "metrics.video_trueview_view_rate"}
        report_names = [
            "get_asset_performance_report",
            "get_asset_performance",
            "get_video_performance_report",
            "get_shopping_performance_report",
            "get_bidding_strategy_report",
            "get_pmax_asset_group_performance",
        ]

        for name in report_names:
            fields = set(FRIENDLY_TOOL_BY_NAME[name].fields)
            with self.subTest(name=name):
                self.assertFalse(fields & search_metrics)
                if name != "get_video_performance_report":
                    self.assertFalse(fields & video_metrics)
                else:
                    self.assertTrue(fields & video_metrics)

    @unittest.skipUnless(Metrics is not None, "google-ads package is not installed")
    def test_default_metrics_exist_in_installed_v24_descriptor(self) -> None:
        metric_fields = Metrics.pb().DESCRIPTOR.fields_by_name

        for field in DEFAULT_METRICS:
            with self.subTest(field=field):
                self.assertIn(field.removeprefix("metrics."), metric_fields)

    @unittest.skipUnless(AssetGroupAsset is not None, "google-ads package is not installed")
    def test_asset_group_asset_fields_exist_in_installed_v24_descriptor(self) -> None:
        asset_group_asset_fields = AssetGroupAsset.pb().DESCRIPTOR.fields_by_name

        for tool_name in ("get_asset_performance_report", "get_asset_performance"):
            for field in FRIENDLY_TOOL_BY_NAME[tool_name].fields:
                if field.startswith("asset_group_asset."):
                    with self.subTest(tool_name=tool_name, field=field):
                        self.assertIn(
                            field.removeprefix("asset_group_asset."),
                            asset_group_asset_fields,
                        )


if __name__ == "__main__":
    unittest.main()
