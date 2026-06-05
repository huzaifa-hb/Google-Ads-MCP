from __future__ import annotations

from datetime import date
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.friendly import FriendlyDispatcher
from google_ads_mcp.safety import ValidationError


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
        if customer_id == "100":
            return {
                "rows": [
                    {
                        "customer_client": {
                            "id": "200",
                            "descriptive_name": "Manager A",
                            "manager": True,
                            "level": "1",
                            "status": "ENABLED",
                            "client_customer": "customers/200",
                        }
                    },
                    {
                        "customer_client": {
                            "id": "300",
                            "descriptive_name": "Manager B",
                            "manager": True,
                            "level": "1",
                            "status": "ENABLED",
                            "client_customer": "customers/300",
                        }
                    },
                ],
                "query": kwargs["query"],
            }
        if customer_id == "200":
            return {
                "rows": [
                    {
                        "customer_client": {
                            "id": "201",
                            "descriptive_name": "Leaf A",
                            "manager": False,
                            "level": "1",
                            "status": "ENABLED",
                            "client_customer": "customers/201",
                        }
                    }
                ],
                "query": kwargs["query"],
            }
        if customer_id == "300":
            return {
                "rows": [
                    {
                        "customer_client": {
                            "id": "301",
                            "descriptive_name": "Leaf B",
                            "manager": False,
                            "level": "1",
                            "status": "ENABLED",
                            "client_customer": "customers/301",
                        }
                    }
                ],
                "query": kwargs["query"],
            }
        return {"rows": [], "query": kwargs["query"]}


class FriendlyDispatcherTests(unittest.IsolatedAsyncioTestCase):
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
        self.assertEqual(campaign["advertising_channel_type"], "SEARCH")
        self.assertEqual(campaign["campaign_budget"], "customers/1234567890/campaignBudgets/-1")

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
        result = await dispatcher.dispatch("get_mcc_hierarchy", customer_id="100")
        managers = {child["id"]: child for child in result["tree"]["children"]}
        self.assertEqual(managers["200"]["children"][0]["id"], "201")
        self.assertEqual(managers["300"]["children"][0]["id"], "301")

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
            payload={"name": "PMax", "merchant_id": "555", "sales_country": "US"},
        )
        campaign = result["operations"][1]["campaign_operation"]["create"]
        self.assertEqual(campaign["advertising_channel_type"], "PERFORMANCE_MAX")
        self.assertEqual(campaign["shopping_setting"]["merchant_id"], 555)

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


if __name__ == "__main__":
    unittest.main()
