from __future__ import annotations

import os
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.friendly import FriendlyDispatcher
from google_ads_mcp.gateway import GoogleAdsGateway
from google_ads_mcp.safety import CONFIRMATION_PHRASE


RUN_INTEGRATION = os.environ.get("GOOGLE_ADS_MCP_RUN_INTEGRATION_TESTS", "").lower() in {
    "1",
    "true",
    "yes",
}


@unittest.skipUnless(RUN_INTEGRATION, "Set GOOGLE_ADS_MCP_RUN_INTEGRATION_TESTS=true to run.")
class GoogleAdsIntegrationTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.gateway = GoogleAdsGateway(mode=os.environ.get("GOOGLE_ADS_MCP_MODE", "safe_read_only"))

    async def test_live_campaign_metadata(self) -> None:
        result = await self.gateway.get_resource_metadata("campaign", force_refresh=True)

        self.assertTrue(result["ok"])
        self.assertIn("campaign.id", result["selectable"])

    async def test_harmless_search_query(self) -> None:
        customer_id = _required_env("GOOGLE_ADS_MCP_TEST_CUSTOMER_ID")

        result = await self.gateway.search(
            customer_id=customer_id,
            query="SELECT customer.id FROM customer",
            page_size=1,
            primary_field="customer.id",
        )

        self.assertIn("rows", result)

    async def test_validation_only_campaign_pause(self) -> None:
        customer_id = _required_env("GOOGLE_ADS_MCP_TEST_CUSTOMER_ID")
        campaign_id = _required_env("GOOGLE_ADS_MCP_TEST_CAMPAIGN_ID")
        dispatcher = _validation_dispatcher()

        result = await dispatcher.dispatch(
            "pause_campaign",
            customer_id=customer_id,
            payload={"campaign_id": campaign_id},
            validate_only=False,
            execute=True,
            confirmation_phrase=CONFIRMATION_PHRASE,
        )

        self.assertTrue(result["validate_only"])
        self.assertTrue(result["validation_forced"])

    async def test_validation_only_campaign_create_helpers(self) -> None:
        customer_id = _required_env("GOOGLE_ADS_MCP_TEST_CUSTOMER_ID")
        dispatcher = _validation_dispatcher()
        cases = {
            "create_search_campaign": _campaign_payload("Search"),
            "create_display_campaign": _campaign_payload("Display"),
            "create_video_campaign": _campaign_payload("Video"),
            "create_pmax_campaign": _campaign_payload("PMax"),
            "create_demand_gen_campaign": _campaign_payload("Demand Gen"),
        }

        for tool_name, payload in cases.items():
            with self.subTest(tool_name=tool_name):
                result = await _validate_only_dispatch(dispatcher, tool_name, customer_id, payload)
                self.assertTrue(result["validate_only"])

    async def test_validation_only_shopping_campaign_create_helper(self) -> None:
        customer_id = _required_env("GOOGLE_ADS_MCP_TEST_CUSTOMER_ID")
        merchant_id = _required_env("GOOGLE_ADS_MCP_TEST_MERCHANT_ID")
        dispatcher = _validation_dispatcher()

        result = await _validate_only_dispatch(
            dispatcher,
            "create_shopping_campaign",
            customer_id,
            {
                **_campaign_payload("Shopping"),
                "merchant_id": merchant_id,
                "feed_label": os.environ.get("GOOGLE_ADS_MCP_TEST_FEED_LABEL", "US"),
                "campaign_priority": 1,
            },
        )

        self.assertTrue(result["validate_only"])

    async def test_validation_only_budget_and_asset_helpers(self) -> None:
        customer_id = _required_env("GOOGLE_ADS_MCP_TEST_CUSTOMER_ID")
        dispatcher = _validation_dispatcher()
        cases = {
            "create_budget": {
                "name": _test_name("Budget"),
                "amount_micros": 1_000_000,
            },
            "create_shared_budget": {
                "name": _test_name("Shared Budget"),
                "amount_micros": 1_000_000,
            },
            "create_sitelink": {
                "name": _test_name("Sitelink"),
                "link_text": "Book now",
                "description1": "Smoke validation",
                "description2": "No write",
                "final_urls": ["https://example.com"],
            },
            "create_callout": {
                "name": _test_name("Callout"),
                "callout_text": "Free quote",
            },
            "create_text_asset": {
                "name": _test_name("Text Asset"),
                "text": "Smoke asset",
            },
            "create_label": {
                "name": _test_name("Label"),
                "background_color": "#4285F4",
            },
        }

        for tool_name, payload in cases.items():
            with self.subTest(tool_name=tool_name):
                result = await _validate_only_dispatch(dispatcher, tool_name, customer_id, payload)
                self.assertTrue(result["validate_only"])

    async def test_validation_only_video_asset_helper(self) -> None:
        customer_id = _required_env("GOOGLE_ADS_MCP_TEST_CUSTOMER_ID")
        youtube_video_id = _required_env("GOOGLE_ADS_MCP_TEST_YOUTUBE_VIDEO_ID")
        dispatcher = _validation_dispatcher()

        result = await _validate_only_dispatch(
            dispatcher,
            "create_video_asset",
            customer_id,
            {"name": _test_name("Video Asset"), "youtube_video_id": youtube_video_id},
        )

        self.assertTrue(result["validate_only"])

    async def test_validation_only_ad_group_keyword_and_rsa_helpers(self) -> None:
        customer_id = _required_env("GOOGLE_ADS_MCP_TEST_CUSTOMER_ID")
        campaign_id = _required_env("GOOGLE_ADS_MCP_TEST_CAMPAIGN_ID")
        ad_group_id = _required_env("GOOGLE_ADS_MCP_TEST_AD_GROUP_ID")
        dispatcher = _validation_dispatcher()
        cases = {
            "create_ad_group": {
                "campaign_id": campaign_id,
                "name": _test_name("Ad Group"),
                "cpc_bid_micros": 1_000_000,
            },
            "add_keywords": {
                "ad_group_id": ad_group_id,
                "keywords": [{"text": "smoke validation keyword", "match_type": "EXACT"}],
            },
            "create_responsive_search_ad": {
                "ad_group_id": ad_group_id,
                "final_urls": ["https://example.com"],
                "headlines": ["Smoke one", "Smoke two", "Smoke three"],
                "descriptions": ["Smoke description one", "Smoke description two"],
            },
        }

        for tool_name, payload in cases.items():
            with self.subTest(tool_name=tool_name):
                result = await _validate_only_dispatch(dispatcher, tool_name, customer_id, payload)
                self.assertTrue(result["validate_only"])


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise unittest.SkipTest(f"{name} is required for this integration test.")
    return value


def _validation_dispatcher() -> FriendlyDispatcher:
    return FriendlyDispatcher(gateway=GoogleAdsGateway(mode="validation_only"))


async def _validate_only_dispatch(
    dispatcher: FriendlyDispatcher,
    tool_name: str,
    customer_id: str,
    payload: dict,
) -> dict:
    return await dispatcher.dispatch(
        tool_name,
        customer_id=customer_id,
        payload=payload,
        validate_only=False,
        execute=True,
        confirmation_phrase=CONFIRMATION_PHRASE,
    )


def _campaign_payload(channel: str) -> dict:
    return {
        "name": _test_name(channel),
        "amount_micros": 1_000_000,
        "status": "PAUSED",
    }


def _test_name(label: str) -> str:
    return f"MCP validation {label} {os.getpid()}"


if __name__ == "__main__":
    unittest.main()
