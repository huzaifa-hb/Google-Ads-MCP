from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.safety import (
    CONFIRMATION_PHRASE,
    ValidationError,
    ensure_write_allowed,
    normalize_customer_id,
)


class SafetyTests(unittest.TestCase):
    def test_customer_id_normalization(self) -> None:
        self.assertEqual(normalize_customer_id("123-456-7890"), "1234567890")

    def test_customer_id_rejects_text(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_customer_id("act_123")

    def test_validate_only_allowed_without_confirmation(self) -> None:
        self.assertTrue(ensure_write_allowed(validate_only=True, execute=False))

    def test_real_write_requires_confirmation(self) -> None:
        with self.assertRaises(ValidationError):
            ensure_write_allowed(validate_only=False, execute=True, confirmation_phrase=None)

    def test_real_write_accepts_exact_phrase(self) -> None:
        self.assertFalse(
            ensure_write_allowed(
                validate_only=False,
                execute=True,
                confirmation_phrase=CONFIRMATION_PHRASE,
            )
        )


if __name__ == "__main__":
    unittest.main()
