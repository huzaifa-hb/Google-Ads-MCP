from __future__ import annotations

import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.config import ConfigError, Settings, get_settings, reset_settings_cache
from google_ads_mcp.server import (
    _OAuthAllowlistProvider,
    _google_ads_readiness_payload,
    _oauth_token_allowed,
)
from test_tool_config import make_settings


class FakeOAuthProvider:
    issuer = "https://accounts.google.com"

    def __init__(self, token: object | None) -> None:
        self.token = token
        self.seen_token: str | None = None

    async def verify_token(self, token: str) -> object | None:
        self.seen_token = token
        return self.token


class AuthConfigTests(unittest.TestCase):
    def test_bearer_auth_requires_token_by_default(self) -> None:
        settings = make_settings(mcp_bearer_token=None)

        with self.assertRaises(ConfigError):
            settings.require_mcp_auth()

    def test_unauthenticated_local_dev_bypasses_auth_requirement(self) -> None:
        settings = make_settings(mcp_bearer_token=None, allow_unauthenticated_mcp=True)

        settings.require_mcp_auth()

    def test_unauthenticated_local_dev_still_validates_auth_mode(self) -> None:
        settings = make_settings(auth_mode="magic", allow_unauthenticated_mcp=True)

        with self.assertRaises(ConfigError):
            settings.require_mcp_auth()

    def test_invalid_auth_mode_fails_fast(self) -> None:
        settings = make_settings(auth_mode="magic")

        with self.assertRaises(ConfigError):
            settings.require_mcp_auth()

    def test_oauth_proxy_requires_oauth_values(self) -> None:
        settings = make_settings(auth_mode="oauth_proxy")

        with self.assertRaises(ConfigError):
            settings.require_mcp_auth()

    def test_oauth_proxy_accepts_complete_config(self) -> None:
        settings = make_settings(
            auth_mode="oauth_proxy",
            mcp_oauth_client_id="client-id",
            mcp_oauth_client_secret="client-secret",
            mcp_base_url="https://example.com",
            mcp_allowed_emails=("owner@example.com",),
        )

        settings.require_mcp_auth()

    def test_oauth_proxy_requires_allowlist(self) -> None:
        settings = make_settings(
            auth_mode="oauth_proxy",
            mcp_oauth_client_id="client-id",
            mcp_oauth_client_secret="client-secret",
            mcp_base_url="https://example.com",
        )

        with self.assertRaises(ConfigError):
            settings.require_mcp_auth()

    def test_oauth_allowlist_env_values_are_normalized(self) -> None:
        previous_email = os.environ.get("GOOGLE_ADS_MCP_ALLOWED_EMAILS")
        previous_domain = os.environ.get("GOOGLE_ADS_MCP_ALLOWED_DOMAINS")
        os.environ["GOOGLE_ADS_MCP_ALLOWED_EMAILS"] = " Owner@Example.com,ops@example.com "
        os.environ["GOOGLE_ADS_MCP_ALLOWED_DOMAINS"] = " Example.com "
        try:
            settings = Settings.from_env()
        finally:
            if previous_email is None:
                os.environ.pop("GOOGLE_ADS_MCP_ALLOWED_EMAILS", None)
            else:
                os.environ["GOOGLE_ADS_MCP_ALLOWED_EMAILS"] = previous_email
            if previous_domain is None:
                os.environ.pop("GOOGLE_ADS_MCP_ALLOWED_DOMAINS", None)
            else:
                os.environ["GOOGLE_ADS_MCP_ALLOWED_DOMAINS"] = previous_domain

        self.assertEqual(settings.mcp_allowed_emails, ("owner@example.com", "ops@example.com"))
        self.assertEqual(settings.mcp_allowed_domains, ("example.com",))

    def test_reset_settings_cache_refreshes_environment(self) -> None:
        previous = os.environ.get("PORT")
        try:
            reset_settings_cache()
            os.environ["PORT"] = "8081"
            self.assertEqual(get_settings().port, 8081)
            os.environ["PORT"] = "8082"
            self.assertEqual(get_settings().port, 8081)
            reset_settings_cache()
            self.assertEqual(get_settings().port, 8082)
        finally:
            if previous is None:
                os.environ.pop("PORT", None)
            else:
                os.environ["PORT"] = previous
            reset_settings_cache()

    def test_oauth_allowlist_accepts_email_domain_or_subject(self) -> None:
        allowed_emails = {"owner@example.com", "subject-123"}
        allowed_domains = {"example.org", "example.net"}

        cases = [
            SimpleNamespace(claims={"email": "owner@example.com"}, subject="other"),
            SimpleNamespace(claims={"email": "user@example.org"}, subject="other"),
            SimpleNamespace(claims={"email": "user@other.test", "hd": "example.net"}, subject="other"),
            SimpleNamespace(claims={"email": "user@other.test"}, subject="subject-123"),
        ]
        for token in cases:
            with self.subTest(token=token):
                self.assertTrue(
                    _oauth_token_allowed(
                        token,
                        allowed_emails=allowed_emails,
                        allowed_domains=allowed_domains,
                    )
                )

    def test_oauth_allowlist_rejects_unknown_identity(self) -> None:
        token = SimpleNamespace(claims={"email": "user@other.test"}, subject="unknown")

        self.assertFalse(
            _oauth_token_allowed(
                token,
                allowed_emails={"owner@example.com"},
                allowed_domains={"example.org"},
            )
        )

    def test_oauth_allowlist_rejects_empty_policy(self) -> None:
        token = SimpleNamespace(claims={"email": "owner@example.com"}, subject="subject")

        self.assertFalse(_oauth_token_allowed(token, allowed_emails=set(), allowed_domains=set()))

    def test_oauth_allowlist_provider_filters_and_proxies_attributes(self) -> None:
        token = SimpleNamespace(claims={"email": "owner@example.com"}, subject="subject")
        provider = FakeOAuthProvider(token)
        wrapper = _OAuthAllowlistProvider(
            provider,
            make_settings(mcp_allowed_emails=("owner@example.com",)),
        )

        result = asyncio.run(wrapper.verify_token("raw-token"))

        self.assertIs(result, token)
        self.assertEqual(provider.seen_token, "raw-token")
        self.assertEqual(wrapper.issuer, "https://accounts.google.com")

    def test_oauth_allowlist_provider_rejects_unknown_identity(self) -> None:
        token = SimpleNamespace(claims={"email": "stranger@example.net"}, subject="subject")
        provider = FakeOAuthProvider(token)
        wrapper = _OAuthAllowlistProvider(
            provider,
            make_settings(mcp_allowed_emails=("owner@example.com",)),
        )

        result = asyncio.run(wrapper.verify_token("raw-token"))

        self.assertIsNone(result)

    def test_google_ads_readiness_payload_reports_missing_credentials(self) -> None:
        payload = _google_ads_readiness_payload(make_settings())

        self.assertFalse(payload["google_ads_configured"])
        self.assertIn("GOOGLE_ADS_DEVELOPER_TOKEN", payload["missing"])

    def test_google_ads_readiness_payload_reports_configured_credentials(self) -> None:
        payload = _google_ads_readiness_payload(
            make_settings(
                developer_token="dev",
                oauth_client_id="client",
                oauth_client_secret="secret",
                refresh_token="refresh",
            )
        )

        self.assertTrue(payload["google_ads_configured"])
        self.assertEqual(payload["missing"], [])

    def test_google_ads_readiness_payload_treats_placeholders_as_missing(self) -> None:
        payload = _google_ads_readiness_payload(
            make_settings(
                developer_token="replace-with-developer-token",
                oauth_client_id="client",
                oauth_client_secret="secret",
                refresh_token="refresh",
            )
        )

        self.assertFalse(payload["google_ads_configured"])
        self.assertIn("GOOGLE_ADS_DEVELOPER_TOKEN", payload["missing"])

    def test_google_ads_client_config_normalizes_login_customer_id(self) -> None:
        settings = make_settings(
            developer_token="dev",
            oauth_client_id="client",
            oauth_client_secret="secret",
            refresh_token="refresh",
            login_customer_id="123-456-7890",
        )

        config = settings.google_ads_client_config()

        self.assertEqual(config["login_customer_id"], "1234567890")

    def test_google_ads_client_config_rejects_invalid_login_customer_id(self) -> None:
        settings = make_settings(
            developer_token="dev",
            oauth_client_id="client",
            oauth_client_secret="secret",
            refresh_token="refresh",
            login_customer_id="act_123",
        )

        with self.assertRaises(ConfigError):
            settings.google_ads_client_config()

    def test_dotenv_file_is_loaded_without_overriding_process_env(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            Path(temp_dir, ".env").write_text(
                "MCP_BEARER_TOKEN=from-dotenv\nPORT=9090\n",
                encoding="utf-8",
            )
            env = os.environ.copy()
            env.pop("MCP_BEARER_TOKEN", None)
            env.pop("PORT", None)
            src_path = str(Path(__file__).resolve().parents[1] / "src")
            env["PYTHONPATH"] = (
                src_path
                if not env.get("PYTHONPATH")
                else src_path + os.pathsep + env["PYTHONPATH"]
            )
            result = subprocess.run(
                [
                    sys.executable,
                    "-c",
                    (
                        "from google_ads_mcp.config import Settings; "
                        "s = Settings.from_env(); "
                        "print(f'{s.mcp_bearer_token}:{s.port}')"
                    ),
                ],
                cwd=temp_dir,
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )

        self.assertEqual(result.stdout.strip(), "from-dotenv:9090")

    def test_numeric_env_errors_are_config_errors(self) -> None:
        previous = os.environ.get("PORT")
        os.environ["PORT"] = "not-a-port"
        try:
            with self.assertRaises(ConfigError):
                Settings.from_env()
        finally:
            if previous is None:
                os.environ.pop("PORT", None)
            else:
                os.environ["PORT"] = previous


if __name__ == "__main__":
    unittest.main()
