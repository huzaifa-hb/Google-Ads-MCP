from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.tool_config import ToolExposure, build_tool_registry
from google_ads_mcp.tool_implementation import (
    ADDITIVE_WRITE_TOOLS,
    CLASSIFIED_WRITE_TOOLS,
    NON_ADDITIVE_WRITE_TOOLS,
    WRITE_BUILDER_TOOLS,
)
from google_ads_mcp.tool_schemas import parameters_schema_for_exposure


def _exposure(
    registered_name: str,
    *,
    profile: str = "full",
    mode: str = "validation_only",
) -> ToolExposure:
    registry = build_tool_registry({"mode": mode, "tool_profile": profile})
    for exposure in registry.exposures:
        if exposure.registered_name == registered_name:
            return exposure
    raise AssertionError(f"Missing exposure: {registered_name}")


def _payload_schema(registered_name: str, *, profile: str = "full") -> dict[str, object]:
    schema = parameters_schema_for_exposure(_exposure(registered_name, profile=profile))
    return schema["properties"]["payload"]


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

    def test_campaign_create_schemas_expose_channel_specific_payloads(self) -> None:
        app_payload = _payload_schema("campaigns_create_app_campaign")
        shopping_payload = _payload_schema("campaigns_create_shopping_campaign")
        pmax_payload = _payload_schema("campaigns_create_pmax_campaign")
        search_payload = _payload_schema("campaigns_create_search_campaign")

        self.assertEqual(set(app_payload["required"]), {"name", "app_id"})
        self.assertIn("app_store", app_payload["properties"])
        self.assertIn("app_bidding_strategy_goal_type", app_payload["properties"])
        self.assertIn("merchant_id", shopping_payload["properties"])
        self.assertIn("feed_label", shopping_payload["properties"])
        self.assertIn("campaign_priority", shopping_payload["properties"])
        self.assertIn("merchant_id", pmax_payload["properties"])
        self.assertIn("business_name", pmax_payload["properties"])
        self.assertIn("logo_asset_id", pmax_payload["properties"])
        self.assertIn("target_search_network", search_payload["properties"])
        self.assertNotIn("app_id", search_payload["properties"])

    def test_report_schema_exposes_filters_dates_and_row_cap(self) -> None:
        schema = parameters_schema_for_exposure(_exposure("reporting_get_campaign_metrics"))

        properties = schema["properties"]
        self.assertIn("login_customer_id", properties)
        self.assertIn("filters", properties)
        self.assertIn("date_range", properties)
        self.assertIn("max_rows", properties)
        self.assertTrue(properties["page_size"]["deprecated"])
        self.assertNotIn("payload", schema.get("required", []))

    def test_core_search_schema_exposes_login_customer_id(self) -> None:
        schema = parameters_schema_for_exposure(_exposure("generic_google_ads_search"))

        self.assertIn("login_customer_id", schema["properties"])
        self.assertNotIn("login_customer_id", schema.get("required", []))

    def test_list_invoices_schema_requires_billing_setup_payload(self) -> None:
        schema = parameters_schema_for_exposure(_exposure("account_list_invoices"))

        payload = schema["properties"]["payload"]
        self.assertEqual(payload["required"], ["billing_setup"])
        self.assertIn("issue_year", payload["properties"])
        self.assertIn("issue_month", payload["properties"])

    def test_negative_keyword_write_schema_matches_dispatcher_contract(self) -> None:
        payload = _payload_schema("keywords_add_negative_keywords_ad_group")

        self.assertEqual(set(payload["required"]), {"ad_group_id", "keywords"})
        self.assertIn("ad_group_id", payload["properties"])
        self.assertIn("keywords", payload["properties"])
        self.assertNotIn("operations", payload["properties"])

    def test_label_write_schemas_match_dispatcher_contracts(self) -> None:
        campaign_payload = _payload_schema("campaigns_apply_campaign_label")
        keyword_payload = _payload_schema("keywords_apply_keyword_label")

        self.assertEqual(set(campaign_payload["required"]), {"label_id", "campaign_ids"})
        self.assertIn("label_id", campaign_payload["properties"])
        self.assertIn("campaign_ids", campaign_payload["properties"])
        self.assertEqual(
            set(keyword_payload["required"]),
            {"label_id", "ad_group_id", "criterion_ids"},
        )
        self.assertIn("criterion_ids", keyword_payload["properties"])

    def test_keyword_bid_schema_matches_dispatcher_contract(self) -> None:
        payload = _payload_schema("keywords_update_keyword_bid")

        self.assertEqual(payload["required"], ["ad_group_id"])
        self.assertIn("criterion_ids", payload["properties"])
        self.assertIn("cpc_bid_micros", payload["properties"])
        self.assertIn("keyword_bids", payload["properties"])

    def test_budget_write_schemas_match_dispatcher_contracts(self) -> None:
        remove_payload = _payload_schema("budgets_remove_budget")
        link_payload = _payload_schema("budgets_link_budget_to_campaign")

        self.assertEqual(remove_payload["required"], ["budget_id"])
        self.assertEqual(set(link_payload["required"]), {"campaign_id", "budget_id"})
        self.assertIn("campaign_id", link_payload["properties"])

    def test_hand_built_write_tools_do_not_expose_generic_payload_schema(self) -> None:
        registry = build_tool_registry({"mode": "validation_only", "tool_profile": "full"})
        offenders = []

        for exposure in registry.exposures:
            spec = exposure.friendly_spec
            if spec is None or spec.name not in WRITE_BUILDER_TOOLS:
                continue
            payload = parameters_schema_for_exposure(exposure)["properties"].get("payload")
            if not isinstance(payload, dict):
                offenders.append(f"{exposure.registered_name}: missing payload")
                continue
            if payload.get("additionalProperties") is True and payload.get("properties") == {}:
                offenders.append(f"{exposure.registered_name}: open payload")
            if payload.get("required") == ["operations"]:
                offenders.append(f"{exposure.registered_name}: raw operations payload")

        self.assertEqual(offenders, [])

    def test_write_tools_have_explicit_write_effect_classification(self) -> None:
        registry = build_tool_registry({"mode": "validation_only", "tool_profile": "full"})
        write_tools = {
            exposure.canonical_name
            for exposure in registry.exposures
            if exposure.read_write == "write"
        }

        self.assertEqual(ADDITIVE_WRITE_TOOLS & NON_ADDITIVE_WRITE_TOOLS, frozenset())
        self.assertEqual(write_tools - CLASSIFIED_WRITE_TOOLS, set())


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

    async def test_tool_annotations_round_trip_through_tools_list(self) -> None:
        import asyncio

        from fastmcp import Client, FastMCP

        from google_ads_mcp.server import _register_core_tool, _register_friendly_tool

        asyncio.get_running_loop().slow_callback_duration = 30

        class DummyDispatcher:
            async def dispatch(self, *args: object, **kwargs: object) -> dict[str, bool]:
                return {"ok": True}

        async def dummy_core_tool() -> dict[str, bool]:
            return {"ok": True}

        mcp = FastMCP("annotation-roundtrip")
        agency_registry = build_tool_registry(
            {"mode": "write_enabled", "tool_profile": "agency_write"}
        )
        advanced_registry = build_tool_registry(
            {"mode": "write_enabled", "tool_profile": "advanced_mutate"}
        )
        admin_registry = build_tool_registry({"mode": "admin_debug", "tool_profile": "full"})

        for canonical_name in ("get_server_status", "list_accessible_customers"):
            _register_core_tool(mcp, agency_registry, canonical_name, dummy_core_tool)
        _register_core_tool(mcp, advanced_registry, "google_ads_mutate", dummy_core_tool)
        _register_core_tool(mcp, admin_registry, "google_ads_call_service", dummy_core_tool)

        for registered_name in (
            "reporting_get_campaign_metrics",
            "campaigns_create_search_campaign",
            "keywords_add_negative_keywords_campaign",
            "campaigns_apply_campaign_label",
            "bulk_bulk_add_keywords",
            "campaigns_pause_campaign",
            "campaigns_enable_campaign",
            "budgets_update_budget",
            "budgets_link_budget_to_campaign",
            "keywords_remove_keywords",
            "bulk_bulk_update_bids",
        ):
            _register_friendly_tool(
                mcp,
                DummyDispatcher,
                _exposure(registered_name, profile="agency_write", mode="write_enabled"),
            )
        _register_friendly_tool(
            mcp,
            DummyDispatcher,
            _exposure("ads_create_responsive_display_ad", profile="full"),
        )

        async with Client(mcp) as client:
            tools = await client.list_tools()

        annotations = {
            tool.name: tool.annotations.model_dump(exclude_none=True)
            for tool in tools
            if tool.annotations is not None
        }

        def assert_annotations(
            name: str,
            *,
            read_only: bool,
            open_world: bool,
            destructive: bool | None = None,
            title: str | None = None,
        ) -> None:
            self.assertIn(name, annotations)
            annotation = annotations[name]
            self.assertEqual(annotation["readOnlyHint"], read_only)
            self.assertEqual(annotation["openWorldHint"], open_world)
            if destructive is None:
                self.assertNotIn("destructiveHint", annotation)
            else:
                self.assertEqual(annotation["destructiveHint"], destructive)
            if title is not None:
                self.assertEqual(annotation["title"], title)

        assert_annotations(
            "get_server_status",
            read_only=True,
            open_world=False,
            title="Get Server Status",
        )
        assert_annotations(
            "account_list_accessible_customers",
            read_only=True,
            open_world=True,
        )
        assert_annotations(
            "reporting_get_campaign_metrics",
            read_only=True,
            open_world=True,
        )
        for name in (
            "campaigns_create_search_campaign",
            "keywords_add_negative_keywords_campaign",
            "campaigns_apply_campaign_label",
            "bulk_bulk_add_keywords",
        ):
            assert_annotations(name, read_only=False, open_world=True, destructive=False)

        for name in (
            "campaigns_pause_campaign",
            "campaigns_enable_campaign",
            "budgets_update_budget",
            "budgets_link_budget_to_campaign",
            "keywords_remove_keywords",
            "bulk_bulk_update_bids",
            "ads_create_responsive_display_ad",
            "generic_google_ads_mutate",
            "generic_google_ads_call_service",
        ):
            assert_annotations(name, read_only=False, open_world=True, destructive=True)

        self.assertEqual(
            annotations["campaigns_pause_campaign"]["title"],
            "Campaigns: Pause Campaign",
        )
        self.assertEqual(
            annotations["generic_google_ads_call_service"]["title"],
            "Generic: Google Ads Call Service",
        )


if __name__ == "__main__":
    unittest.main()
