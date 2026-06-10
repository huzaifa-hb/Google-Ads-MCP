from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.safety import (
    CONFIRMATION_PHRASE,
    ValidationError,
    build_jsonl_audit_sink,
    ensure_write_allowed,
    guard_google_ads_write,
    hash_customer_id,
    normalize_customer_id,
    redact_sensitive,
)


class SafetyTests(unittest.TestCase):
    def test_customer_id_normalization(self) -> None:
        self.assertEqual(normalize_customer_id("123-456-7890"), "1234567890")

    def test_customer_id_rejects_text(self) -> None:
        with self.assertRaises(ValidationError):
            normalize_customer_id("act_123")

    def test_customer_id_rejects_short_or_long_values(self) -> None:
        for value in ("123456789", "12345678901"):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    normalize_customer_id(value)

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

    def test_real_write_denies_confirmation_when_validate_only_true(self) -> None:
        with self.assertRaises(ValidationError):
            ensure_write_allowed(
                validate_only=True,
                execute=True,
                confirmation_phrase=CONFIRMATION_PHRASE,
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
        self.assertEqual(events[0]["result"], "authorized")

    def test_write_guard_denies_execute_with_validate_only_true(self) -> None:
        events = []
        with self.assertRaises(ValidationError):
            guard_google_ads_write(
                mode="write_enabled",
                tool_name="pause_campaign",
                customer_id="1234567890",
                validate_only=True,
                execute=True,
                confirmation_phrase=CONFIRMATION_PHRASE,
                audit_sink=events.append,
            )
        self.assertEqual(events[0]["result"], "denied")

    def test_jsonl_audit_sink_appends_redacted_event(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "audit" / "writes.jsonl"
            sink = build_jsonl_audit_sink(str(path))
            self.assertIsNotNone(sink)

            guard_google_ads_write(
                mode="validation_only",
                tool_name="pause_campaign",
                customer_id="1234567890",
                validate_only=False,
                execute=True,
                confirmation_phrase=CONFIRMATION_PHRASE,
                audit_sink=sink,
            )

            lines = path.read_text(encoding="utf-8").splitlines()

        self.assertEqual(len(lines), 1)
        event = json.loads(lines[0])
        self.assertEqual(event["result"], "validated")
        self.assertNotIn("1234567890", lines[0])

    def test_redact_sensitive_preserves_keyword_payloads(self) -> None:
        payload = {
            "keywords": [{"text": "buy shoes", "match_type": "EXACT"}],
            "campaign_id": "1234567890",
            "developer_token": "secret-token",
            "api_key": "secret-key",
        }

        redacted = redact_sensitive(payload)

        self.assertEqual(
            redacted["keywords"],
            [{"text": "buy shoes", "match_type": "EXACT"}],
        )
        self.assertEqual(redacted["campaign_id"], "1234567890")
        self.assertEqual(redacted["developer_token"], "[REDACTED]")
        self.assertEqual(redacted["api_key"], "[REDACTED]")


if __name__ == "__main__":
    unittest.main()
