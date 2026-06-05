from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.gateway import GoogleAdsGateway
from google_ads_mcp.safety import CONFIRMATION_PHRASE, ValidationError
from test_tool_config import make_settings


class RecordingService:
    def __init__(self) -> None:
        self.last_request: dict[str, object] | None = None

    def mutate_campaigns(self, request: dict[str, object]) -> dict[str, object]:
        self.last_request = dict(request)
        return {"ok": True, "request": self.last_request}

    def list_invoices(self, request: dict[str, object]) -> dict[str, object]:
        self.last_request = dict(request)
        return {"ok": True, "request": self.last_request}

    def get_unlisted_report(self, request: dict[str, object]) -> dict[str, object]:
        self.last_request = dict(request)
        return {"ok": True, "request": self.last_request}

    def list_accessible_customers(self, request: dict[str, object]) -> dict[str, object]:
        self.last_request = dict(request)
        return {"resource_names": ["customers/1234567890", "customers/2223334444"]}


class FakeClient:
    def __init__(self, service: RecordingService) -> None:
        self.service = service

    def get_service(self, service_name: str) -> RecordingService:  # noqa: ARG002
        return self.service

    def get_type(self, type_name: str) -> dict[str, object]:  # noqa: ARG002
        return {}


class ParsingGateway(GoogleAdsGateway):
    def _parse_dict(self, payload: dict[str, object], message: dict[str, object]) -> dict[str, object]:
        message.update(payload)
        return message

    def _message_to_dict(self, message: object) -> object:
        return message


class GatewayWriteSafetyTests(unittest.IsolatedAsyncioTestCase):
    async def test_mutating_method_cannot_be_marked_read_only(self) -> None:
        gateway = GoogleAdsGateway()
        with self.assertRaises(ValidationError):
            await gateway.call_service(
                service_name="CampaignService",
                method_name="mutate_campaigns",
                request_type="MutateCampaignsRequest",
                payload={"customer_id": "1234567890"},
                is_write=False,
                validate_only=False,
                execute=False,
            )

    async def test_validation_only_overrides_raw_request_validate_only(self) -> None:
        service = RecordingService()
        gateway = ParsingGateway(client=FakeClient(service), mode="validation_only")

        result = await gateway.call_service(
            service_name="CampaignService",
            method_name="mutate_campaigns",
            request_type="MutateCampaignsRequest",
            payload={"customer_id": "1234567890", "validate_only": False},
            is_write=True,
            validate_only=True,
            execute=False,
        )

        self.assertTrue(result["is_write"])
        self.assertIsNotNone(service.last_request)
        self.assertTrue(service.last_request["validate_only"])  # type: ignore[index]

    async def test_confirmed_write_overrides_raw_request_validate_only(self) -> None:
        service = RecordingService()
        gateway = ParsingGateway(client=FakeClient(service), mode="write_enabled")

        result = await gateway.call_service(
            service_name="CampaignService",
            method_name="mutate_campaigns",
            request_type="MutateCampaignsRequest",
            payload={"customer_id": "1234567890", "validate_only": True},
            is_write=False,
            validate_only=False,
            execute=True,
            confirmation_phrase=CONFIRMATION_PHRASE,
        )

        self.assertTrue(result["is_write"])
        self.assertIsNotNone(service.last_request)
        self.assertFalse(service.last_request["validate_only"])  # type: ignore[index]

    async def test_unlisted_service_read_is_denied_by_default(self) -> None:
        service = RecordingService()
        gateway = ParsingGateway(client=FakeClient(service), mode="admin_debug")

        with self.assertRaises(ValidationError):
            await gateway.call_service(
                service_name="SomeService",
                method_name="get_unlisted_report",
                request_type="GetUnlistedReportRequest",
                payload={"customer_id": "1234567890"},
                is_write=False,
            )

    async def test_allowlisted_service_read_is_allowed(self) -> None:
        service = RecordingService()
        gateway = ParsingGateway(client=FakeClient(service), mode="safe_read_only")

        result = await gateway.call_service(
            service_name="InvoiceService",
            method_name="list_invoices",
            request_type="ListInvoicesRequest",
            payload={"customer_id": "1234567890"},
            is_write=False,
        )

        self.assertFalse(result["is_write"])
        self.assertEqual(service.last_request, {"customer_id": "1234567890"})

    async def test_admin_debug_escape_hatch_allows_unlisted_read(self) -> None:
        service = RecordingService()
        settings = make_settings(enable_generic_service_bridge=True)
        gateway = ParsingGateway(client=FakeClient(service), mode="admin_debug", settings=settings)

        result = await gateway.call_service(
            service_name="SomeService",
            method_name="get_unlisted_report",
            request_type="GetUnlistedReportRequest",
            payload={"customer_id": "1234567890"},
            is_write=False,
        )

        self.assertFalse(result["is_write"])
        self.assertEqual(service.last_request, {"customer_id": "1234567890"})

    async def test_list_accessible_customers_uses_customer_service(self) -> None:
        service = RecordingService()
        gateway = ParsingGateway(client=FakeClient(service), mode="safe_read_only")

        result = await gateway.list_accessible_customers()

        self.assertEqual(result["customer_ids"], ["1234567890", "2223334444"])
        self.assertEqual(service.last_request, {})


if __name__ == "__main__":
    unittest.main()
