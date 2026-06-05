from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.safety import (
    CONFIRMATION_PHRASE,
    ValidationError,
    ensure_write_allowed,
    guard_google_ads_write,
    hash_customer_id,
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

    def test_write_guard_denies_read_only_mode(self) -> None:
        events = []
        with self.assertRaises(ValidationError):
            guard_google_ads_write(
                mode="safe_read_only",
                tool_name="pause_campaign",
                customer_id="1234567890",
                validate_only=True,
                audit_sink=events.append,
            )
        self.assertEqual(events[0]["result"], "denied")
        self.assertEqual(events[0]["customer_id_hash"], hash_customer_id("1234567890"))
        self.assertNotIn("1234567890", str(events[0]))

    def test_write_guard_forces_validation_only_mode(self) -> None:
        events = []
        decision = guard_google_ads_write(
            mode="validation_only",
            tool_name="pause_campaign",
            customer_id="1234567890",
            validate_only=False,
            execute=True,
            confirmation_phrase=CONFIRMATION_PHRASE,
            audit_sink=events.append,
        )
        self.assertTrue(decision.validate_only)
        self.assertTrue(decision.forced_validation)
        self.assertEqual(events[0]["result"], "validated")

    def test_write_guard_allows_confirmed_write_enabled_mode(self) -> None:
        events = []
        decision = guard_google_ads_write(
            mode="write_enabled",
            tool_name="pause_campaign",
            customer_id="1234567890",
            validate_only=False,
            execute=True,
            confirmation_phrase=CONFIRMATION_PHRASE,
            audit_sink=events.append,
        )
        self.assertFalse(decision.validate_only)
        self.assertEqual(events[0]["result"], "executed")


if __name__ == "__main__":
    unittest.main()
