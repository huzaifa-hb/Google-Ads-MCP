from __future__ import annotations

from datetime import date
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.capability_matrix import build_full_capability_matrix
from google_ads_mcp.friendly import FriendlyDispatcher
from google_ads_mcp.safety import ValidationError
from google_ads_mcp.tool_catalog import FRIENDLY_TOOL_SPECS


class FakeGateway:
    def __init__(self) -> None:
        self.last_search = None
        self.last_mutate = None
        self.last_service = None

    async def search(self, **kwargs):
        self.last_search = kwargs
        if "customer_client" in kwargs["query"]:
            return {
                "rows": [
                    {
                        "customer_client": {
                            "id": "222",
                            "descriptive_name": "Child",
                            "manager": False,
                            "level": "0",
                            "status": "ENABLED",
                        }
                    }
                ],
                "query": kwargs["query"],
            }
        return {"rows": [], "query": kwargs["query"]}

    async def mutate(self, **kwargs):
        self.last_mutate = kwargs
        return {"operation_count": len(kwargs["operations"]), "operations": kwargs["operations"]}

    async def call_service(self, **kwargs):
        self.last_service = kwargs
        return {"service_call": kwargs}


class BranchingGateway(FakeGateway):
    async def search(self, **kwargs):
        customer_id = kwargs["customer_id"]
        if customer_id == "1000000000":
            return {
                "rows": [
                    {
                        "customer_client": {
                            "id": "2000000000",
                            "descriptive_name": "Manager A",
                            "manager": True,
                            "level": "1",
                            "status": "ENABLED",
                            "client_customer": "customers/2000000000",
                        }
                    },
                    {
                        "customer_client": {
                            "id": "3000000000",
                            "descriptive_name": "Manager B",
                            "manager": True,
                            "level": "1",
                            "status": "ENABLED",
                            "client_customer": "customers/3000000000",
                        }
                    },
                ],
                "query": kwargs["query"],
            }
        if customer_id == "2000000000":
            return {
                "rows": [
                    {
                        "customer_client": {
                            "id": "2010000000",
                            "descriptive_name": "Leaf A",
                            "manager": False,
                            "level": "1",
                            "status": "ENABLED",
                            "client_customer": "customers/2010000000",
                        }
                    }
                ],
                "query": kwargs["query"],
            }
        if customer_id == "3000000000":
            return {
                "rows": [
                    {
                        "customer_client": {
                            "id": "3010000000",
                            "descriptive_name": "Leaf B",
                            "manager": False,
                            "level": "1",
                            "status": "ENABLED",
                            "client_customer": "customers/3010000000",
                        }
                    }
                ],
                "query": kwargs["query"],
            }
        return {"rows": [], "query": kwargs["query"]}


class FriendlyDispatcherTests(unittest.IsolatedAsyncioTestCase):
    async def test_all_friendly_tools_have_dispatch_behavior_matching_capability_status(self) -> None:
        status_by_name = {
            row.tool: row.implementation_status
            for row in build_full_capability_matrix(FRIENDLY_TOOL_SPECS)
            if row.tool in {spec.name for spec in FRIENDLY_TOOL_SPECS}
        }

        for spec in FRIENDLY_TOOL_SPECS:
            with self.subTest(tool=spec.name):
                gateway = FakeGateway()
                dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
                status = status_by_name[spec.name]
                payload = {} if status == "operation_template" else _dispatcher_smoke_payload(spec.name)

                result = await dispatcher.dispatch(
                    spec.name,
                    customer_id="1234567890",
                    payload=payload,
                )

                if status == "operation_template":
                    self.assertIn("operations", result["required_payload"])
                elif status in {"unsupported_by_design", "deprecated", "eligibility_gated"}:
                    self.assertEqual(result["error"], "unsupported_capability")
                else:
                    self.assertNotEqual(result.get("error"), "unsupported_capability")
                    self.assertNotIn("required_payload", result)

    async def test_campaign_report_builds_custom_date_query(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "get_campaign_metrics",
            customer_id="1234567890",
            start_date="2026-01-01",
            end_date="2026-01-31",
            filters={"campaign.status": "ENABLED"},
        )
        self.assertIn("segments.date BETWEEN '2026-01-01' AND '2026-01-31'", result["query"])
        self.assertIn("campaign.status = 'ENABLED'", result["query"])

    async def test_friendly_filters_reject_non_field_keys(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]
        with self.assertRaises(ValidationError):
            await dispatcher.dispatch(
                "get_campaign_metrics",
                customer_id="1234567890",
                filters={"campaign.status OR metrics.clicks > 0": "ENABLED"},
            )

    async def test_add_campaign_negative_keywords_builds_operations(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "add_negative_keywords_campaign",
            customer_id="1234567890",
            payload={
                "campaign_id": "111",
                "keywords": [{"text": "free", "match_type": "BROAD"}, "cheap"],
            },
        )
        self.assertEqual(result["operation_count"], 2)
        first = result["operations"][0]["campaign_criterion_operation"]["create"]
        self.assertTrue(first["negative"])
        self.assertEqual(first["campaign"], "customers/1234567890/campaigns/111")

    async def test_bulk_pause_campaigns_builds_status_updates(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "bulk_pause_campaigns",
            customer_id="1234567890",
            payload={"ids": ["1", "2"]},
        )
        self.assertEqual(result["operation_count"], 2)
        status = result["operations"][0]["campaign_operation"]["update"]["status"]
        self.assertEqual(status, "PAUSED")

    async def test_create_search_campaign_builds_budget_and_campaign(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "create_search_campaign",
            customer_id="1234567890",
            payload={"name": "Brand Search", "amount_micros": 5_000_000},
        )
        self.assertEqual(result["operation_count"], 2)
        budget = result["operations"][0]["campaign_budget_operation"]["create"]
        campaign = result["operations"][1]["campaign_operation"]["create"]
        self.assertEqual(budget["resource_name"], "customers/1234567890/campaignBudgets/-1")
        self.assertFalse(budget["explicitly_shared"])
        self.assertEqual(campaign["advertising_channel_type"], "SEARCH")
        self.assertEqual(campaign["campaign_budget"], "customers/1234567890/campaignBudgets/-1")
        self.assertEqual(
            campaign["contains_eu_political_advertising"],
            "DOES_NOT_CONTAIN_EU_POLITICAL_ADVERTISING",
        )

    async def test_create_responsive_search_ad_builds_operation(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "create_responsive_search_ad",
            customer_id="1234567890",
            payload={
                "ad_group_id": "123",
                "final_urls": ["https://example.com"],
                "headlines": ["One", "Two", "Three"],
                "descriptions": ["Desc one", "Desc two"],
            },
        )
        ad = result["operations"][0]["ad_group_ad_operation"]["create"]["ad"]
        self.assertIn("responsive_search_ad", ad)
        self.assertEqual(ad["final_urls"], ["https://example.com"])

    async def test_update_keyword_bid_builds_operation(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "update_keyword_bid",
            customer_id="1234567890",
            payload={"ad_group_id": "321", "criterion_ids": ["999"], "cpc_bid_micros": 2_000_000},
        )
        update = result["operations"][0]["ad_group_criterion_operation"]["update"]
        self.assertEqual(update["cpc_bid_micros"], 2_000_000)
        self.assertEqual(update["resource_name"], "customers/1234567890/adGroupCriteria/321~999")

    async def test_get_keyword_ideas_uses_default_service_mapping(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "get_keyword_ideas",
            customer_id="1234567890",
            payload={"keywords": ["shoes"], "language": "languageConstants/1000"},
        )
        call = result["service_call"]
        self.assertEqual(call["service_name"], "KeywordPlanIdeaService")
        self.assertEqual(call["method_name"], "generate_keyword_ideas")
        self.assertEqual(call["payload"]["keyword_seed"]["keywords"], ["shoes"])

    async def test_list_customers_defaults_to_leaf_accounts(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch("list_customers", customer_id="1234567890")
        self.assertIn("customer_client.manager = FALSE", result["query"])

    async def test_get_mcc_hierarchy_includes_tree(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch("get_mcc_hierarchy", customer_id="1234567890")
        self.assertEqual(result["tree"]["children"][0]["id"], "222")

    async def test_get_mcc_hierarchy_preserves_branches(self) -> None:
        gateway = BranchingGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch("get_mcc_hierarchy", customer_id="1000000000")
        managers = {child["id"]: child for child in result["tree"]["children"]}
        self.assertEqual(managers["2000000000"]["children"][0]["id"], "2010000000")
        self.assertEqual(managers["3000000000"]["children"][0]["id"], "3010000000")

    async def test_list_invoices_defaults_to_current_year(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "list_invoices",
            customer_id="1234567890",
            payload={"billing_setup": "customers/1234567890/billingSetups/1"},
        )
        call = result["service_call"]
        self.assertEqual(call["service_name"], "InvoiceService")
        self.assertEqual(call["payload"]["issue_year"], str(date.today().year))

    async def test_billing_setup_uses_default_gaql(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch("get_billing_setup", customer_id="1234567890")
        self.assertIn("FROM billing_setup", result["query"])

    async def test_pmax_campaign_with_merchant_id_builds_shopping_setting(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "create_pmax_campaign",
            customer_id="1234567890",
            payload={
                "name": "PMax",
                "merchant_id": "555",
                "feed_label": "US",
                "campaign_priority": 2,
                "url_expansion_opt_out": True,
                "logo_asset_id": "999",
            },
        )
        campaign = result["operations"][1]["campaign_operation"]["create"]
        self.assertEqual(campaign["advertising_channel_type"], "PERFORMANCE_MAX")
        self.assertEqual(campaign["shopping_setting"]["merchant_id"], 555)
        self.assertEqual(campaign["shopping_setting"]["feed_label"], "US")
        self.assertNotIn("campaign_priority", campaign["shopping_setting"])
        self.assertNotIn("sales_country", campaign["shopping_setting"])
        self.assertNotIn("url_expansion_opt_out", campaign)
        self.assertIn("maximize_conversion_value", campaign)
        self.assertEqual(campaign["resource_name"], "customers/1234567890/campaigns/-2")
        asset = result["operations"][2]["asset_operation"]["create"]
        campaign_asset = result["operations"][3]["campaign_asset_operation"]["create"]
        self.assertEqual(asset["text_asset"]["text"], "PMax")
        self.assertEqual(campaign_asset["field_type"], "BUSINESS_NAME")
        self.assertEqual(campaign_asset["campaign"], "customers/1234567890/campaigns/-2")
        logo_campaign_asset = result["operations"][4]["campaign_asset_operation"]["create"]
        self.assertEqual(logo_campaign_asset["asset"], "customers/1234567890/assets/999")
        self.assertEqual(logo_campaign_asset["field_type"], "LOGO")

    async def test_shopping_campaign_keeps_priority_and_feed_label(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "create_shopping_campaign",
            customer_id="1234567890",
            payload={"name": "Shopping", "merchant_id": "555", "feed_label": "US", "campaign_priority": 2},
        )
        campaign = result["operations"][1]["campaign_operation"]["create"]

        self.assertEqual(campaign["advertising_channel_type"], "SHOPPING")
        self.assertEqual(campaign["shopping_setting"]["feed_label"], "US")
        self.assertEqual(campaign["shopping_setting"]["campaign_priority"], 2)
        self.assertNotIn("sales_country", campaign["shopping_setting"])

    async def test_non_search_campaign_defaults_to_compatible_bidding(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]
        cases = {
            "create_demand_gen_campaign": "maximize_conversions",
            "create_smart_campaign": "maximize_conversions",
        }

        for tool_name, expected_key in cases.items():
            with self.subTest(tool_name=tool_name):
                result = await dispatcher.dispatch(
                    tool_name,
                    customer_id="1234567890",
                    payload={"name": tool_name},
                )
                campaign = result["operations"][1]["campaign_operation"]["create"]
                self.assertIn(expected_key, campaign)

    async def test_video_campaign_creation_returns_unsupported_guidance(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch(
            "create_video_campaign",
            customer_id="1234567890",
            payload={"name": "Video"},
        )

        self.assertEqual(result["error"], "unsupported_capability")

    async def test_target_roas_is_validated_as_ratio(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        valid = await dispatcher.dispatch(
            "create_search_campaign",
            customer_id="1234567890",
            payload={
                "name": "Search",
                "bidding_strategy_type": "TARGET_ROAS",
                "target_roas": 4.0,
            },
        )
        campaign = valid["operations"][1]["campaign_operation"]["create"]
        self.assertEqual(campaign["target_roas"]["target_roas"], 4.0)

        with self.assertRaises(ValidationError):
            await dispatcher.dispatch(
                "create_search_campaign",
                customer_id="1234567890",
                payload={
                    "name": "Search",
                    "bidding_strategy_type": "TARGET_ROAS",
                    "target_roas": 0.001,
                },
            )

    async def test_demographic_and_audience_reports_use_valid_resources_and_primary_fields(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]
        expectations = {
            "get_age_range_report": ("FROM age_range_view", "ad_group_criterion.criterion_id"),
            "get_gender_report": ("FROM gender_view", "ad_group_criterion.criterion_id"),
            "get_parental_status_report": (
                "FROM parental_status_view",
                "ad_group_criterion.criterion_id",
            ),
            "get_household_income_report": (
                "FROM income_range_view",
                "ad_group_criterion.criterion_id",
            ),
            "get_audience_performance_report": ("FROM ad_group_audience_view", "user_list.id"),
        }

        for tool_name, (resource_clause, primary_field) in expectations.items():
            with self.subTest(tool_name=tool_name):
                result = await dispatcher.dispatch(tool_name, customer_id="1234567890")
                self.assertIn(resource_clause, result["query"])
                self.assertIn(primary_field, result["query"])

    async def test_hour_segment_adds_required_date_segment(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch(
            "get_campaign_metrics",
            customer_id="1234567890",
            time_segment="hour",
        )

        self.assertIn("segments.hour", result["query"])
        self.assertIn("segments.date", result["query"])

    async def test_baked_hour_report_adds_required_date_segment(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch("get_hour_of_day_performance", customer_id="1234567890")

        self.assertIn("segments.hour", result["query"])
        self.assertIn("segments.date", result["query"])

    async def test_change_history_uses_change_event_date_field_without_metrics(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch("get_change_history_report", customer_id="1234567890")

        self.assertIn("FROM change_event", result["query"])
        self.assertIn("change_event.change_date_time DURING LAST_30_DAYS", result["query"])
        self.assertNotIn("metrics.", result["query"])

    async def test_ad_schedule_report_uses_single_segment_and_curated_metrics(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch("get_ad_schedule_report", customer_id="1234567890")

        self.assertIn("segments.day_of_week", result["query"])
        self.assertNotIn("segments.hour", result["query"])
        self.assertNotIn("metrics.search_impression_share", result["query"])

    async def test_keyword_ids_do_not_fall_back_to_campaign_ids(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        with self.assertRaises(ValidationError):
            await dispatcher.dispatch(
                "update_keyword_bid",
                customer_id="1234567890",
                payload={"ad_group_id": "321", "campaign_ids": ["999"], "cpc_bid_micros": 2_000_000},
            )

    async def test_bulk_campaigns_accept_campaign_ids(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch(
            "bulk_enable_campaigns",
            customer_id="1234567890",
            payload={"campaign_ids": ["1", "2"]},
        )

        self.assertEqual(result["operation_count"], 2)

    async def test_bulk_add_negative_keywords_routes_through_negative_keyword_helper(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch(
            "bulk_add_negative_keywords",
            customer_id="1234567890",
            payload={"campaign_id": "123-456", "keywords": ["free"]},
        )

        create = result["operations"][0]["campaign_criterion_operation"]["create"]
        self.assertEqual(create["campaign"], "customers/1234567890/campaigns/123456")
        self.assertEqual(create["keyword"]["text"], "free")

    async def test_bulk_add_negative_keywords_supports_ad_group_level(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch(
            "bulk_add_negative_keywords",
            customer_id="1234567890",
            payload={"level": "ad_group", "ad_group_id": "789-000", "keywords": ["cheap"]},
        )

        create = result["operations"][0]["ad_group_criterion_operation"]["create"]
        self.assertEqual(create["ad_group"], "customers/1234567890/adGroups/789000")
        self.assertEqual(create["keyword"]["text"], "cheap")

    async def test_required_text_values_preserve_hyphens(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        label = await dispatcher.dispatch(
            "create_label",
            customer_id="1234567890",
            payload={"name": "summer-sale-2026"},
        )
        video = await dispatcher.dispatch(
            "create_video_asset",
            customer_id="1234567890",
            payload={"youtube_video_id": "abc-def_123"},
        )

        label_create = label["operations"][0]["label_operation"]["create"]
        video_create = video["operations"][0]["asset_operation"]["create"]["youtube_video_asset"]
        self.assertEqual(label_create["name"], "summer-sale-2026")
        self.assertEqual(video_create["youtube_video_id"], "abc-def_123")

    async def test_required_ids_still_normalize_hyphens(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        result = await dispatcher.dispatch(
            "create_ad_group",
            customer_id="1234567890",
            payload={"campaign_id": "111-222", "name": "Core Ad Group"},
        )

        create = result["operations"][0]["ad_group_operation"]["create"]
        self.assertEqual(create["campaign"], "customers/1234567890/campaigns/111222")

    async def test_create_budget_requires_explicit_name_and_amount(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        with self.assertRaises(ValidationError):
            await dispatcher.dispatch("create_budget", customer_id="1234567890", payload={})

        result = await dispatcher.dispatch(
            "create_budget",
            customer_id="1234567890",
            payload={"name": "Monthly-budget-2026", "amount_micros": 1_500_000},
        )
        create = result["operations"][0]["campaign_budget_operation"]["create"]
        self.assertEqual(create["name"], "Monthly-budget-2026")
        self.assertEqual(create["amount_micros"], 1_500_000)

    async def test_label_apply_direct_ad_payload(self) -> None:
        gateway = FakeGateway()
        dispatcher = FriendlyDispatcher(gateway=gateway)  # type: ignore[arg-type]
        result = await dispatcher.dispatch(
            "apply_ad_label",
            customer_id="1234567890",
            payload={"label_id": "7", "ad_group_id": "10", "ad_id": "20"},
        )
        create = result["operations"][0]["ad_group_ad_label_operation"]["create"]
        self.assertEqual(create["ad_group_ad"], "customers/1234567890/adGroupAds/10~20")
        self.assertEqual(create["label"], "customers/1234567890/labels/7")

    async def test_geo_performance_adds_readable_name(self) -> None:
        class GeoGateway(FakeGateway):
            async def search(self, **kwargs):
                return {
                    "rows": [{"geographic_view": {"country_criterion_id": "2840"}}],
                    "query": kwargs["query"],
                }

        dispatcher = FriendlyDispatcher(gateway=GeoGateway())  # type: ignore[arg-type]
        result = await dispatcher.dispatch("get_geo_performance", customer_id="1234567890")
        self.assertEqual(result["rows"][0]["geographic_view"]["country_name"], "United States")

    async def test_rsa_requires_final_urls(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]
        with self.assertRaises(ValidationError):
            await dispatcher.dispatch(
                "create_responsive_search_ad",
                customer_id="1234567890",
                payload={
                    "ad_group_id": "123",
                    "headlines": ["One"],
                    "descriptions": ["Desc"],
                },
            )

    async def test_rsa_requires_minimum_asset_counts(self) -> None:
        dispatcher = FriendlyDispatcher(gateway=FakeGateway())  # type: ignore[arg-type]

        with self.assertRaises(ValidationError):
            await dispatcher.dispatch(
                "create_responsive_search_ad",
                customer_id="1234567890",
                payload={
                    "ad_group_id": "123",
                    "final_urls": ["https://example.com"],
                    "headlines": ["One", "Two"],
                    "descriptions": ["Desc one", "Desc two"],
                },
            )
        with self.assertRaises(ValidationError):
            await dispatcher.dispatch(
                "create_responsive_search_ad",
                customer_id="1234567890",
                payload={
                    "ad_group_id": "123",
                    "final_urls": ["https://example.com"],
                    "headlines": ["One", "Two", "Three"],
                    "descriptions": ["Desc one"],
                },
            )


def _dispatcher_smoke_payload(tool_name: str) -> dict:
    payload = {
        "name": f"Smoke {tool_name}",
        "budget_name": f"Budget {tool_name}",
        "amount_micros": 1_000_000,
        "daily_budget_micros": 1_000_000,
        "campaign_id": "111",
        "campaign_ids": ["111", "222"],
        "budget_id": "999",
        "ad_group_id": "333",
        "ad_group_ids": ["333"],
        "ad_id": "444",
        "label_id": "555",
        "ids": ["111"],
        "criterion_ids": ["666"],
        "keywords": [{"text": "smoke keyword", "match_type": "PHRASE"}],
        "keyword_bids": [{"criterion_id": "666", "cpc_bid_micros": 1_000_000}],
        "cpc_bid_micros": 1_000_000,
        "final_urls": ["https://example.com"],
        "headlines": ["Headline one", "Headline two", "Headline three"],
        "descriptions": ["Description one", "Description two"],
        "link_text": "Sitelink",
        "callout_text": "Callout",
        "text": "Text asset",
        "youtube_video_id": "abc-def_123",
        "shared_set_id": "777",
        "campaign_shared_set_id": "888",
        "billing_setup": "customers/1234567890/billingSetups/999",
        "keywords_to_add": ["smoke"],
        "language": "languageConstants/1000",
        "url": "https://example.com",
        "service_name": "GoogleAdsService",
        "method_name": "search",
        "request_type": "SearchGoogleAdsRequest",
        "request": {"customer_id": "1234567890", "query": "SELECT customer.id FROM customer"},
        "query": "SELECT campaign.id FROM campaign",
        "primary_field": "campaign.id",
        "merchant_id": "123456",
        "feed_label": "US",
        "campaign_priority": 1,
        "target_roas": 4.0,
        "target_cpa_micros": 1_000_000,
        "background_color": "#4285F4",
        "ads": [{"ad_group_id": "333", "ad_id": "444"}],
    }
    if tool_name == "batch_mutate":
        payload["operations"] = [
            {
                "campaign_operation": {
                    "update": {
                        "resource_name": "customers/1234567890/campaigns/111",
                        "status": "PAUSED",
                    },
                    "update_mask": "status",
                }
            }
        ]
    return payload


if __name__ == "__main__":
    unittest.main()
