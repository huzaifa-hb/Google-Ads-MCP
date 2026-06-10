from __future__ import annotations

from types import SimpleNamespace
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.gateway import GoogleAdsGateway
from google_ads_mcp.safety import CONFIRMATION_PHRASE, ValidationError
from test_tool_config import make_settings

try:
    from google.ads.googleads.v24.services.types.recommendation_service import (
        ApplyRecommendationRequest,
    )
except ImportError:  # pragma: no cover - dependency is part of project env
    ApplyRecommendationRequest = None  # type: ignore[assignment]

try:
    from google.ads.googleads.v24.services.services.google_ads_service.pagers import (
        SearchPager as RealSearchPager,
    )
    from google.ads.googleads.v24.services.types.google_ads_service import (
        SearchGoogleAdsRequest,
        SearchGoogleAdsResponse,
    )
except ImportError:  # pragma: no cover - dependency is part of project env
    RealSearchPager = None  # type: ignore[assignment]
    SearchGoogleAdsRequest = None  # type: ignore[assignment]
    SearchGoogleAdsResponse = None  # type: ignore[assignment]


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

    def apply_recommendation(self, request: object) -> dict[str, object]:
        self.last_request = {"request_class": request.__class__.__name__}
        return {"ok": True, "request_class": request.__class__.__name__}

    def list_accessible_customers(self, request: dict[str, object]) -> dict[str, object]:
        self.last_request = dict(request)
        return {"resource_names": ["customers/1234567890", "customers/2223334444"]}


class SearchRequest:
    def __init__(self) -> None:
        self.page_size: int | None = None


class RecordingGoogleAdsClient:
    def __init__(self, **kwargs: object) -> None:
        self.kwargs = kwargs


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


class FieldQueryGateway(GoogleAdsGateway):
    def __init__(self) -> None:
        super().__init__(mode="safe_read_only")
        self.field_query = ""

    async def _search_google_ads_fields(self, query: str):  # noqa: ANN201, SLF001
        self.field_query = query
        return []


class StreamService:
    def search_stream(self, request: SearchRequest) -> list[SimpleNamespace]:  # noqa: ARG002
        return [
            SimpleNamespace(results=[{"row": 1}, {"row": 2}]),
            SimpleNamespace(results=[{"row": 3}]),
        ]


class FailingStream:
    def __iter__(self):
        raise RuntimeError("INTERNAL")


class IterationFailingStreamService:
    def __init__(self) -> None:
        self.calls = 0

    def search_stream(self, request: SearchRequest):  # noqa: ANN201, ARG002
        self.calls += 1
        if self.calls == 1:
            return FailingStream()
        return [SimpleNamespace(results=[{"row": "ok"}])]


class StreamClient:
    def __init__(self, service: StreamService | IterationFailingStreamService) -> None:
        self.service = service

    def get_service(  # noqa: ARG002
        self,
        service_name: str,
    ) -> StreamService | IterationFailingStreamService:
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


class RealTypeClient(FakeClient):
    def get_type(self, type_name: str) -> object:
        if type_name == "ApplyRecommendationRequest":
            if ApplyRecommendationRequest is None:
                raise AssertionError("ApplyRecommendationRequest test type was not imported.")
            return ApplyRecommendationRequest()
        return super().get_type(type_name)


class ParsingGateway(GoogleAdsGateway):
    def _parse_dict(self, payload: dict[str, object], message: dict[str, object]) -> dict[str, object]:
        message.update(payload)
        return message

    def _message_to_dict(self, message: object) -> object:
        return message


class GatewayWriteSafetyTests(unittest.IsolatedAsyncioTestCase):
    def test_per_user_access_token_client_uses_google_oauth_credentials(self) -> None:
        gateway = GoogleAdsGateway(
            settings=make_settings(
                google_ads_auth_mode="per_user_oauth",
                developer_token="developer-token",
                login_customer_id="123-456-7890",
            ),
            access_token="user-access-token",
        )

        client = gateway._load_client_from_access_token(RecordingGoogleAdsClient)  # noqa: SLF001

        self.assertEqual(client.kwargs["developer_token"], "developer-token")
        self.assertEqual(client.kwargs["login_customer_id"], "1234567890")
        self.assertEqual(client.kwargs["version"], "v24")
        self.assertEqual(client.kwargs["credentials"].token, "user-access-token")
        self.assertIn(
            "https://www.googleapis.com/auth/adwords",
            client.kwargs["credentials"].scopes,
        )

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

    @unittest.skipUnless(
        ApplyRecommendationRequest is not None,
        "google-ads package is not installed",
    )
    async def test_validation_only_service_write_requires_request_validate_field(self) -> None:
        service = RecordingService()
        gateway = GoogleAdsGateway(client=RealTypeClient(service), mode="validation_only")

        with self.assertRaisesRegex(ValidationError, "does not support validate_only"):
            await gateway.call_service(
                service_name="RecommendationService",
                method_name="apply_recommendation",
                request_type="ApplyRecommendationRequest",
                payload={"customer_id": "1234567890", "operations": []},
                is_write=True,
                validate_only=True,
                execute=False,
            )

        self.assertIsNone(service.last_request)

    @unittest.skipUnless(
        ApplyRecommendationRequest is not None,
        "google-ads package is not installed",
    )
    async def test_confirmed_service_write_without_validate_field_does_not_inject_it(self) -> None:
        service = RecordingService()
        gateway = GoogleAdsGateway(client=RealTypeClient(service), mode="write_enabled")

        result = await gateway.call_service(
            service_name="RecommendationService",
            method_name="apply_recommendation",
            request_type="ApplyRecommendationRequest",
            payload={"customer_id": "1234567890", "operations": []},
            is_write=True,
            validate_only=False,
            execute=True,
            confirmation_phrase=CONFIRMATION_PHRASE,
        )

        self.assertTrue(result["is_write"])
        self.assertEqual(service.last_request, {"request_class": "ApplyRecommendationRequest"})

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

    async def test_search_injects_max_rows_limit_and_marks_possible_truncation(self) -> None:
        service = SearchService()
        gateway = ParsingGateway(client=SearchClient(service), mode="safe_read_only")

        result = await gateway.search(
            customer_id="1234567890",
            query="SELECT campaign.id FROM campaign",
            max_rows=2,
        )

        self.assertEqual(result["rows"], SearchPager.results)
        self.assertEqual(result["pagination"]["next_page_token"], None)
        self.assertEqual(result["pagination"]["requested_max_rows"], 2)
        self.assertEqual(result["pagination"]["google_ads_fixed_page_size"], 10_000)
        self.assertTrue(result["pagination"]["limit_injected"])
        self.assertEqual(result["pagination"]["effective_limit"], 2)
        self.assertIsNone(result["pagination"]["has_more"])
        self.assertTrue(result["pagination"]["limit_reached"])
        self.assertIsNotNone(service.last_request)
        self.assertIsNone(service.last_request.page_size)  # type: ignore[union-attr]
        self.assertIn("LIMIT 2", service.last_request.query)  # type: ignore[union-attr]

    async def test_search_preserves_large_user_limit_with_page_token(self) -> None:
        service = SearchService()
        gateway = ParsingGateway(client=SearchClient(service), mode="safe_read_only")

        result = await gateway.search(
            customer_id="1234567890",
            query="SELECT campaign.id FROM campaign LIMIT 10000",
            max_rows=2,
            page_token="existing-token",
        )

        self.assertFalse(result["pagination"]["limit_injected"])
        self.assertEqual(result["pagination"]["effective_limit"], 10000)
        self.assertEqual(result["pagination"]["next_page_token"], "next-token")
        self.assertEqual(service.last_request.page_token, "existing-token")  # type: ignore[union-attr]
        self.assertEqual(service.last_request.query, "SELECT campaign.id FROM campaign LIMIT 10000 PARAMETERS omit_unselected_resource_names = true")  # type: ignore[union-attr]

    @unittest.skipUnless(
        RealSearchPager is not None
        and SearchGoogleAdsRequest is not None
        and SearchGoogleAdsResponse is not None,
        "google-ads package is not installed",
    )
    def test_real_search_pager_delegates_results_and_next_page_token(self) -> None:
        response = SearchGoogleAdsResponse()
        response.next_page_token = "next-token"
        pager = RealSearchPager(
            lambda request, **kwargs: response,
            SearchGoogleAdsRequest(),
            response,
        )

        self.assertEqual(list(pager.results), list(response.results))
        self.assertEqual(pager.next_page_token, "next-token")

    async def test_search_rejects_page_token_with_injected_limit(self) -> None:
        service = SearchService()
        gateway = ParsingGateway(client=SearchClient(service), mode="safe_read_only")

        with self.assertRaisesRegex(ValidationError, "page_token"):
            await gateway.search(
                customer_id="1234567890",
                query="SELECT campaign.id FROM campaign",
                max_rows=2,
                page_token="existing-token",
            )

        self.assertIsNone(service.last_request)

    async def test_search_page_size_alias_sets_deprecated_metadata(self) -> None:
        service = SearchService()
        gateway = ParsingGateway(client=SearchClient(service), mode="safe_read_only")

        result = await gateway.search(
            customer_id="1234567890",
            query="SELECT campaign.id FROM campaign",
            page_size=2,
        )

        self.assertTrue(result["pagination"]["pagination_deprecated"])
        self.assertEqual(result["pagination"]["requested_max_rows"], 2)

    async def test_search_rejects_offset_before_service_call(self) -> None:
        service = SearchService()
        gateway = ParsingGateway(client=SearchClient(service), mode="safe_read_only")

        with self.assertRaisesRegex(ValidationError, "OFFSET"):
            await gateway.search(
                customer_id="1234567890",
                query="SELECT campaign.id FROM campaign LIMIT 10 OFFSET 10",
            )

        self.assertIsNone(service.last_request)

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

    def test_transient_detection_does_not_match_rate_inside_words(self) -> None:
        gateway = GoogleAdsGateway(mode="safe_read_only")

        self.assertFalse(gateway._is_transient(Exception("accurate validation error")))
        self.assertTrue(gateway._is_transient(Exception("RATE_EXCEEDED")))

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

    async def test_search_stream_retries_iterator_time_transient_errors(self) -> None:
        service = IterationFailingStreamService()
        settings = make_settings(max_retries=1, retry_base_seconds=0.0)
        gateway = ParsingGateway(
            client=StreamClient(service),
            mode="safe_read_only",
            settings=settings,
        )

        result = await gateway.search_stream(
            customer_id="1234567890",
            query="SELECT campaign.id FROM campaign",
            max_rows=10,
        )

        self.assertEqual(service.calls, 2)
        self.assertEqual(result["rows"], [{"row": "ok"}])

    async def test_search_stream_rejects_invalid_max_rows(self) -> None:
        gateway = ParsingGateway(client=StreamClient(StreamService()), mode="safe_read_only")

        with self.assertRaises(ValidationError):
            await gateway.search_stream(
                customer_id="1234567890",
                query="SELECT campaign.id FROM campaign",
                max_rows=0,
            )

    async def test_search_stream_rejects_offset_clause(self) -> None:
        gateway = ParsingGateway(client=StreamClient(StreamService()), mode="safe_read_only")

        with self.assertRaisesRegex(ValidationError, "OFFSET"):
            await gateway.search_stream(
                customer_id="1234567890",
                query="SELECT campaign.id FROM campaign LIMIT 10 OFFSET 10",
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

    async def test_describe_resource_matches_only_resource_field_prefix(self) -> None:
        gateway = FieldQueryGateway()

        await gateway.describe_resource("campaign")

        self.assertIn("WHERE name LIKE 'campaign.%'", gateway.field_query)
        self.assertNotIn("WHERE name LIKE 'campaign%'", gateway.field_query)

    def test_message_to_dict_logs_conversion_fallback(self) -> None:
        gateway = GoogleAdsGateway()

        with self.assertLogs("google_ads_mcp.gateway", level="WARNING"):
            result = gateway._message_to_dict(object())  # noqa: SLF001

        self.assertIn("value", result)


if __name__ == "__main__":
    unittest.main()
