from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.tool_config import ToolExposure, build_tool_registry
from google_ads_mcp.tool_schemas import parameters_schema_for_exposure


def _exposure(registered_name: str) -> ToolExposure:
    registry = build_tool_registry({"mode": "validation_only", "tool_profile": "lean"})
    for exposure in registry.exposures:
        if exposure.registered_name == registered_name:
            return exposure
    raise AssertionError(f"Missing exposure: {registered_name}")


class ToolSchemaTests(unittest.TestCase):
    def test_requested_tools_have_distinct_generated_schemas(self) -> None:
        schemas = {
            name: parameters_schema_for_exposure(_exposure(name))
            for name in [
                "ads_create_responsive_search_ad",
                "campaigns_pause_campaign",
                "reporting_get_campaign_metrics",
                "account_list_invoices",
            ]
        }

        self.assertNotEqual(
            schemas["ads_create_responsive_search_ad"],
            schemas["campaigns_pause_campaign"],
        )
        self.assertNotEqual(
            schemas["reporting_get_campaign_metrics"],
            schemas["account_list_invoices"],
        )

    def test_create_responsive_search_ad_schema_exposes_payload_contract(self) -> None:
        schema = parameters_schema_for_exposure(_exposure("ads_create_responsive_search_ad"))

        payload = schema["properties"]["payload"]
        self.assertEqual(payload["type"], "object")
        self.assertEqual(
            set(payload["required"]),
            {"ad_group_id", "final_urls", "headlines", "descriptions"},
        )
        self.assertIn("path1", payload["properties"])
        self.assertNotIn("campaign_id", payload["properties"])

    def test_pause_campaign_schema_uses_campaign_id_payload(self) -> None:
        schema = parameters_schema_for_exposure(_exposure("campaigns_pause_campaign"))

        payload = schema["properties"]["payload"]
        self.assertEqual(payload["required"], ["campaign_id"])
        self.assertIn("campaign_id", payload["properties"])
        self.assertNotIn("headlines", payload["properties"])

    def test_report_schema_exposes_filters_dates_and_row_cap(self) -> None:
        schema = parameters_schema_for_exposure(_exposure("reporting_get_campaign_metrics"))

        properties = schema["properties"]
        self.assertIn("filters", properties)
        self.assertIn("date_range", properties)
        self.assertIn("max_rows", properties)
        self.assertTrue(properties["page_size"]["deprecated"])
        self.assertNotIn("payload", schema.get("required", []))

    def test_list_invoices_schema_requires_billing_setup_payload(self) -> None:
        schema = parameters_schema_for_exposure(_exposure("account_list_invoices"))

        payload = schema["properties"]["payload"]
        self.assertEqual(payload["required"], ["billing_setup"])
        self.assertIn("issue_year", payload["properties"])
        self.assertIn("issue_month", payload["properties"])


class ToolSchemaRoundTripTests(unittest.IsolatedAsyncioTestCase):
    async def test_custom_schema_round_trips_through_tools_list(self) -> None:
        import asyncio

        from fastmcp import Client, FastMCP

        from google_ads_mcp.server import _register_friendly_tool

        asyncio.get_running_loop().slow_callback_duration = 30

        class DummyDispatcher:
            async def dispatch(self, *args: object, **kwargs: object) -> dict[str, bool]:
                return {"ok": True}

        mcp = FastMCP("schema-roundtrip")
        for registered_name in (
            "ads_create_responsive_search_ad",
            "campaigns_pause_campaign",
            "reporting_get_campaign_metrics",
            "account_list_invoices",
        ):
            _register_friendly_tool(mcp, DummyDispatcher, _exposure(registered_name))

        async with Client(mcp) as client:
            tools = await client.list_tools()

        schemas = {tool.name: tool.inputSchema for tool in tools}
        rsa_payload = schemas["ads_create_responsive_search_ad"]["properties"]["payload"]
        pause_payload = schemas["campaigns_pause_campaign"]["properties"]["payload"]
        report_properties = schemas["reporting_get_campaign_metrics"]["properties"]

        self.assertIn("headlines", rsa_payload["properties"])
        self.assertNotIn("headlines", pause_payload["properties"])
        self.assertIn("filters", report_properties)
        self.assertIn("billing_setup", schemas["account_list_invoices"]["properties"]["payload"]["properties"])


if __name__ == "__main__":
    unittest.main()
