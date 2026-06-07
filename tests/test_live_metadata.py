from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.gateway import GoogleAdsGateway
from google_ads_mcp.safety import ValidationError
from test_tool_config import make_settings


FIELD_ROWS = [
    {
        "name": "campaign.id",
        "category": "ATTRIBUTE",
        "data_type": "INT64",
        "selectable": True,
        "filterable": True,
        "sortable": True,
        "is_repeated": False,
        "selectable_with": [],
    },
    {
        "name": "campaign.name",
        "category": "ATTRIBUTE",
        "data_type": "STRING",
        "selectable": True,
        "filterable": True,
        "sortable": True,
        "is_repeated": False,
        "selectable_with": [],
    },
    {
        "name": "campaign.status",
        "category": "ATTRIBUTE",
        "data_type": "ENUM",
        "selectable": True,
        "filterable": True,
        "sortable": True,
        "is_repeated": False,
        "selectable_with": [],
    },
]

COMPATIBLE_ROWS = [
    {
        "name": "metrics.clicks",
        "category": "METRIC",
        "data_type": "INT64",
        "selectable": True,
        "filterable": False,
        "sortable": True,
        "is_repeated": False,
        "selectable_with": ["campaign"],
    },
    {
        "name": "metrics.impressions",
        "category": "METRIC",
        "data_type": "INT64",
        "selectable": True,
        "filterable": False,
        "sortable": True,
        "is_repeated": False,
        "selectable_with": ["campaign"],
    },
    {
        "name": "segments.date",
        "category": "SEGMENT",
        "data_type": "DATE",
        "selectable": True,
        "filterable": True,
        "sortable": True,
        "is_repeated": False,
        "selectable_with": ["campaign"],
    },
]


class Request:
    query = ""


class MetadataService:
    def __init__(self) -> None:
        self.queries: list[str] = []

    def search_google_ads_fields(self, request: Request) -> list[dict[str, object]]:
        self.queries.append(request.query)
        if "WHERE selectable_with" in request.query:
            return COMPATIBLE_ROWS
        return FIELD_ROWS


class FailingMetadataService:
    def search_google_ads_fields(self, request: Request) -> list[dict[str, object]]:  # noqa: ARG002
        raise RuntimeError("field service unavailable")


class FakeClient:
    def __init__(self, service: object) -> None:
        self.service = service

    def get_service(self, service_name: str) -> object:  # noqa: ARG002
        return self.service

    def get_type(self, type_name: str) -> Request:  # noqa: ARG002
        return Request()


class LiveMetadataTests(unittest.IsolatedAsyncioTestCase):
    async def test_resource_metadata_uses_cache(self) -> None:
        service = MetadataService()
        gateway = GoogleAdsGateway(client=FakeClient(service))

        first = await gateway.get_resource_metadata("campaign")
        second = await gateway.get_resource_metadata("campaign")

        self.assertTrue(first["ok"])
        self.assertFalse(first["cached"])
        self.assertTrue(second["cached"])
        self.assertEqual(len(service.queries), 2)
        self.assertIn("campaign.name", first["resource_fields"])
        self.assertIn("metrics.clicks", first["metrics"])
        self.assertIn("segments.date", first["segments"])

    async def test_resource_metadata_cache_can_be_disabled(self) -> None:
        service = MetadataService()
        gateway = GoogleAdsGateway(
            client=FakeClient(service),
            settings=make_settings(metadata_cache_ttl_seconds=0),
        )

        first = await gateway.get_resource_metadata("campaign")
        second = await gateway.get_resource_metadata("campaign")

        self.assertFalse(first["cached"])
        self.assertFalse(second["cached"])
        self.assertEqual(len(service.queries), 4)

    async def test_resource_metadata_cache_evicts_oldest_entry(self) -> None:
        service = MetadataService()
        gateway = GoogleAdsGateway(
            client=FakeClient(service),
            settings=make_settings(metadata_cache_max_entries=1),
        )

        await gateway.get_resource_metadata("campaign")
        await gateway.get_resource_metadata("ad_group")
        result = await gateway.get_resource_metadata("campaign")

        self.assertFalse(result["cached"])
        self.assertEqual(len(service.queries), 6)

    async def test_metadata_snapshot_fallback_when_field_service_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            snapshot_path = Path(temp_dir) / "metadata.json"
            snapshot_path.write_text(
                json.dumps(
                    {
                        "resources": {
                            "campaign": {
                                "attributes": FIELD_ROWS,
                                "compatible": COMPATIBLE_ROWS,
                            }
                        }
                    }
                ),
                encoding="utf-8",
            )
            gateway = GoogleAdsGateway(
                client=FakeClient(FailingMetadataService()),
                settings=make_settings(metadata_snapshot_path=str(snapshot_path)),
            )

            result = await gateway.get_resource_metadata("campaign")

        self.assertTrue(result["ok"])
        self.assertEqual(result["source"], "metadata_snapshot")
        self.assertIn("campaign.name", result["resource_fields"])
        self.assertIn("metrics.clicks", result["metrics"])
        self.assertIn("Live GoogleAdsFieldService unavailable", " ".join(result["warnings"]))

    async def test_invalid_resource_name_is_rejected(self) -> None:
        gateway = GoogleAdsGateway(client=FakeClient(MetadataService()))

        with self.assertRaises(ValidationError):
            await gateway.get_resource_metadata("campaign; DROP")

    async def test_metadata_api_error_returns_structured_response(self) -> None:
        gateway = GoogleAdsGateway(client=FakeClient(FailingMetadataService()))

        result = await gateway.get_resource_metadata("campaign")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "GOOGLE_ADS_FIELD_SERVICE_ERROR")
        self.assertNotIn("developer_token", str(result))

    async def test_validate_gaql_fields_reports_invalid_fields(self) -> None:
        gateway = GoogleAdsGateway(client=FakeClient(MetadataService()))

        result = await gateway.validate_gaql_fields(
            "campaign",
            ["campaign.id", "metrics.clicks", "campaign.missing"],
        )

        self.assertTrue(result["ok"])
        self.assertFalse(result["valid"])
        self.assertEqual(result["valid_fields"], ["campaign.id", "metrics.clicks"])
        self.assertEqual(result["invalid_fields"][0]["field"], "campaign.missing")

    async def test_suggest_gaql_fields_prefers_prefix_matches(self) -> None:
        gateway = GoogleAdsGateway(client=FakeClient(MetadataService()))

        result = await gateway.suggest_gaql_fields("campaign", "campaign.na")

        self.assertEqual(result["suggestions"][0], "campaign.name")

    async def test_plan_gaql_query_builds_safe_query_without_execution(self) -> None:
        gateway = GoogleAdsGateway(client=FakeClient(MetadataService()))

        result = await gateway.plan_gaql_query(
            resource_name="campaign",
            user_goal="campaign click report",
            fields=["campaign.name"],
            metrics=["metrics.clicks"],
            filters={"campaign.status": "ENABLED"},
            date_range="LAST_7_DAYS",
        )

        self.assertTrue(result["ok"])
        self.assertTrue(result["not_executed"])
        self.assertEqual(
            result["query"],
            "SELECT campaign.id, campaign.name, metrics.clicks FROM campaign "
            "WHERE segments.date DURING LAST_7_DAYS AND campaign.status = ENABLED",
        )


if __name__ == "__main__":
    unittest.main()
