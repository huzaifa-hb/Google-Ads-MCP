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
        dispatcher = FriendlyDispatcher(
            gateway=GoogleAdsGateway(mode="validation_only"),
        )

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


def _required_env(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise unittest.SkipTest(f"{name} is required for this integration test.")
    return value


if __name__ == "__main__":
    unittest.main()
