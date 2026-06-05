from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.gateway import GoogleAdsGateway
from google_ads_mcp.safety import CONFIRMATION_PHRASE, ValidationError


class RecordingService:
    def __init__(self) -> None:
        self.last_request: dict[str, object] | None = None

    def mutate_campaigns(self, request: dict[str, object]) -> dict[str, object]:
        self.last_request = dict(request)
        return {"ok": True, "request": self.last_request}


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


if __name__ == "__main__":
    unittest.main()
