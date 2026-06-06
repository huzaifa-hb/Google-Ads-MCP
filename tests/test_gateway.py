from __future__ import annotations

from types import SimpleNamespace
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


class SearchRequest:
    pass


class SearchPager:
    next_page_token = "next-token"
    results = [{"campaign": {"id": "1"}}, {"campaign": {"id": "2"}}]

    def __iter__(self):
        raise AssertionError("search() must not iterate the pager across all pages.")


class SearchService:
    def __init__(self) -> None:
        self.last_request: SearchRequest | None = None

    def search(self, request: SearchRequest) -> SearchPager:
        self.last_request = request
        return SearchPager()


class SearchClient:
    def __init__(self, service: SearchService) -> None:
        self.service = service

    def get_service(self, service_name: str) -> SearchService:  # noqa: ARG002
        return self.service

    def get_type(self, type_name: str) -> SearchRequest:  # noqa: ARG002
        return SearchRequest()


class StreamService:
    def search_stream(self, request: SearchRequest) -> list[SimpleNamespace]:  # noqa: ARG002
        return [
            SimpleNamespace(results=[{"row": 1}, {"row": 2}]),
            SimpleNamespace(results=[{"row": 3}]),
        ]


class StreamClient:
    def __init__(self, service: StreamService) -> None:
        self.service = service

    def get_service(self, service_name: str) -> StreamService:  # noqa: ARG002
        return self.service

    def get_type(self, type_name: str) -> SearchRequest:  # noqa: ARG002
        return SearchRequest()


class MutateRequest:
    def __init__(self) -> None:
        self.mutate_operations: list[dict[str, object]] = []


class FailingMutateService:
    def __init__(self) -> None:
        self.calls = 0

    def mutate(self, request: MutateRequest) -> dict[str, object]:  # noqa: ARG002
        self.calls += 1
        raise RuntimeError("INTERNAL")


class MutateClient:
    def __init__(self, service: FailingMutateService) -> None:
        self.service = service

    def get_service(self, service_name: str) -> FailingMutateService:  # noqa: ARG002
        return self.service

    def get_type(self, type_name: str) -> MutateRequest | dict[str, object]:
        if type_name == "MutateGoogleAdsRequest":
            return MutateRequest()
        return {}


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

    async def test_admin_debug_escape_hatch_routes_unlisted_method_through_write_guard(self) -> None:
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

        self.assertTrue(result["is_write"])
        self.assertEqual(service.last_request, {"customer_id": "1234567890", "validate_only": True})

    async def test_delete_prefix_is_treated_as_mutating(self) -> None:
        gateway = GoogleAdsGateway(mode="safe_read_only")

        with self.assertRaises(ValidationError):
            await gateway.call_service(
                service_name="SomeService",
                method_name="delete_unlisted_report",
                request_type="DeleteUnlistedReportRequest",
                payload={"customer_id": "1234567890"},
                is_write=False,
            )

    async def test_list_accessible_customers_uses_customer_service(self) -> None:
        service = RecordingService()
        gateway = ParsingGateway(client=FakeClient(service), mode="safe_read_only")

        result = await gateway.list_accessible_customers()

        self.assertEqual(result["customer_ids"], ["1234567890", "2223334444"])
        self.assertEqual(service.last_request, {})

    async def test_search_reads_only_first_pager_page(self) -> None:
        service = SearchService()
        gateway = ParsingGateway(client=SearchClient(service), mode="safe_read_only")

        result = await gateway.search(
            customer_id="1234567890",
            query="SELECT campaign.id FROM campaign",
            page_size=2,
            page_token="existing-token",
        )

        self.assertEqual(result["rows"], SearchPager.results)
        self.assertEqual(result["pagination"]["next_page_token"], "next-token")
        self.assertIsNotNone(service.last_request)
        self.assertEqual(service.last_request.page_token, "existing-token")  # type: ignore[union-attr]
        self.assertFalse(hasattr(service.last_request, "page_size"))

    async def test_committed_mutate_is_not_retried_on_transient_error(self) -> None:
        service = FailingMutateService()
        settings = make_settings(max_retries=3, retry_base_seconds=0.0)
        gateway = ParsingGateway(
            client=MutateClient(service),
            mode="write_enabled",
            settings=settings,
        )

        with self.assertRaises(RuntimeError):
            await gateway.mutate(
                customer_id="1234567890",
                operations=[{"campaign_operation": {"create": {"name": "Test"}}}],
                validate_only=False,
                execute=True,
                confirmation_phrase=CONFIRMATION_PHRASE,
            )

        self.assertEqual(service.calls, 1)

    async def test_search_stream_caps_rows_and_marks_truncated(self) -> None:
        gateway = ParsingGateway(client=StreamClient(StreamService()), mode="safe_read_only")

        result = await gateway.search_stream(
            customer_id="1234567890",
            query="SELECT campaign.id FROM campaign",
            max_rows=2,
        )

        self.assertEqual(result["row_count"], 2)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["max_rows"], 2)

    async def test_search_stream_rejects_invalid_max_rows(self) -> None:
        gateway = ParsingGateway(client=StreamClient(StreamService()), mode="safe_read_only")

        with self.assertRaises(ValidationError):
            await gateway.search_stream(
                customer_id="1234567890",
                query="SELECT campaign.id FROM campaign",
                max_rows=0,
            )

    async def test_retry_count_means_retries_after_first_attempt(self) -> None:
        settings = make_settings(max_retries=2, retry_base_seconds=0.0)
        gateway = GoogleAdsGateway(settings=settings)
        calls = 0

        def flaky() -> str:
            nonlocal calls
            calls += 1
            if calls < 3:
                raise RuntimeError("INTERNAL")
            return "ok"

        result = await gateway._retry(flaky)  # noqa: SLF001

        self.assertEqual(result, "ok")
        self.assertEqual(calls, 3)

    def test_list_services_returns_warning_when_package_inspection_fails(self) -> None:
        gateway = GoogleAdsGateway(settings=make_settings(api_version="v999"))

        with self.assertLogs("google_ads_mcp.gateway", level="WARNING"):
            result = gateway.list_services()

        self.assertEqual(result["service_count"], 0)
        self.assertIn("warning", result)

    def test_message_to_dict_logs_conversion_fallback(self) -> None:
        gateway = GoogleAdsGateway()

        with self.assertLogs("google_ads_mcp.gateway", level="WARNING"):
            result = gateway._message_to_dict(object())  # noqa: SLF001

        self.assertIn("value", result)


if __name__ == "__main__":
    unittest.main()
