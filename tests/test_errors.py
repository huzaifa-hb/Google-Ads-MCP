from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.errors import format_google_ads_exception, format_tool_error
from google_ads_mcp.safety import ValidationError
from google_ads_mcp.server import _tool_response


class FieldPathElement:
    def __init__(self, field_name: str, index: int | None = None) -> None:
        self.field_name = field_name
        self.index = index


class Location:
    field_path_elements = [FieldPathElement("operations", 0), FieldPathElement("create")]


class GoogleAdsError:
    message = "Invalid field name"
    error_code = "query_error: INVALID_FIELD_NAME"
    location = Location()


class Failure:
    errors = [GoogleAdsError()]


class FakeGoogleAdsException(Exception):
    request_id = "abc-123"
    failure = Failure()


class ErrorFormattingTests(unittest.TestCase):
    def test_google_ads_exception_includes_request_id_and_field_path(self) -> None:
        result = format_google_ads_exception(FakeGoogleAdsException("bad request"))

        self.assertEqual(result["error_type"], "GoogleAdsException")
        self.assertEqual(result["request_id"], "abc-123")
        self.assertEqual(result["google_ads_errors"][0]["field_path"], "operations[0].create")
        self.assertIn("Validate fields", result["suggested_fix"])

    def test_validation_error_uses_validation_shape(self) -> None:
        result = format_tool_error(ValidationError("bad input"))

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "ValidationError")

    def test_bidding_strategy_error_is_not_treated_as_rate_limit(self) -> None:
        result = format_google_ads_exception(
            FakeGoogleAdsException("Bidding strategy type is incompatible with shared budget.")
        )

        self.assertNotIn("Reduce request volume", result["suggested_fix"])


class ToolResponseWrapperTests(unittest.IsolatedAsyncioTestCase):
    async def test_wrapper_returns_structured_validation_error(self) -> None:
        async def broken_tool() -> dict[str, object]:
            raise ValidationError("bad tool input")

        result = await _tool_response(broken_tool)()

        self.assertFalse(result["ok"])
        self.assertEqual(result["error_type"], "ValidationError")


if __name__ == "__main__":
    unittest.main()
