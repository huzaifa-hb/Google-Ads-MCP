from __future__ import annotations

import asyncio
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import _bootstrap  # noqa: F401
from google_ads_mcp.config import ConfigError, Settings, get_settings, reset_settings_cache
from google_ads_mcp.server import (
    BOOTSTRAP_RESULT_FIRESTORE_PREFIX,
    BOOTSTRAP_RESULT_FIRESTORE_SALT,
    _KeyValueBootstrapResultStore,
    _MemoryBootstrapResultStore,
    _OAuthAllowlistProvider,
    _build_bootstrap_result_store,
    _bootstrap_request_allowed,
    _google_ads_access_token_value,
    _google_ads_readiness_payload,
    _oauth_discovery_payload,
    _oauth_token_allowed,
    _server_status_payload,
)
from google_ads_mcp.tool_config import build_tool_registry
from test_tool_config import make_settings


class FakeOAuthProvider:
    issuer = "https://accounts.google.com"

    def __init__(self, token: object | None) -> None:
        self.token = token
        self.seen_token: str | None = None

    async def verify_token(self, token: str) -> object | None:
        self.seen_token = token
        return self.token


class FakeKeyValueStore:
    def __init__(self) -> None:
        self.values: dict[str, dict[str, object]] = {}
        self.deleted: list[str] = []
        self.put_ttl: float | None = None

    async def put(
        self,
        key: str,
        value: dict[str, object],
        *,
        collection: str | None = None,  # noqa: ARG002
        ttl: float | None = None,
    ) -> None:
        self.values[key] = dict(value)
        self.put_ttl = ttl

    async def get(self, key: str, *, collection: str | None = None):  # noqa: ANN201, ARG002
        return self.values.get(key)

    async def delete(self, key: str, *, collection: str | None = None) -> bool:  # noqa: ARG002
        self.deleted.append(key)
        self.values.pop(key, None)
        return True


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

    def test_invalid_google_ads_auth_mode_fails_fast(self) -> None:
        settings = make_settings(google_ads_auth_mode="magic")

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

    def test_per_user_oauth_proxy_requires_allowlist_or_explicit_allow_all(self) -> None:
        settings = make_settings(
            auth_mode="oauth_proxy",
            google_ads_auth_mode="per_user_oauth",
            mcp_oauth_client_id="client-id",
            mcp_oauth_client_secret="client-secret",
            mcp_base_url="https://example.com",
        )

        with self.assertRaisesRegex(ConfigError, "GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS"):
            settings.require_mcp_auth()

    def test_per_user_oauth_proxy_accepts_explicit_allow_all(self) -> None:
        settings = make_settings(
            auth_mode="oauth_proxy",
            google_ads_auth_mode="per_user_oauth",
            mcp_oauth_client_id="client-id",
            mcp_oauth_client_secret="client-secret",
            mcp_base_url="https://example.com",
            mcp_allow_all_google_users=True,
        )

        settings.require_mcp_auth()

    def test_firestore_token_storage_requires_project_id(self) -> None:
        settings = make_settings(
            auth_mode="oauth_proxy",
            google_ads_auth_mode="per_user_oauth",
            mcp_oauth_client_id="client-id",
            mcp_oauth_client_secret="client-secret",
            mcp_base_url="https://example.com",
            mcp_token_storage="firestore",
        )

        with self.assertRaises(ConfigError):
            settings.require_mcp_auth()

    def test_oauth_allowlist_env_values_are_normalized(self) -> None:
        previous_email = os.environ.get("GOOGLE_ADS_MCP_ALLOWED_EMAILS")
        previous_domain = os.environ.get("GOOGLE_ADS_MCP_ALLOWED_DOMAINS")
        previous_allow_all = os.environ.get("GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS")
        os.environ["GOOGLE_ADS_MCP_ALLOWED_EMAILS"] = " Owner@Example.com,ops@example.com "
        os.environ["GOOGLE_ADS_MCP_ALLOWED_DOMAINS"] = " Example.com "
        os.environ["GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS"] = "true"
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
            if previous_allow_all is None:
                os.environ.pop("GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS", None)
            else:
                os.environ["GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS"] = previous_allow_all

        self.assertEqual(settings.mcp_allowed_emails, ("owner@example.com", "ops@example.com"))
        self.assertEqual(settings.mcp_allowed_domains, ("example.com",))
        self.assertTrue(settings.mcp_allow_all_google_users)

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

    def test_per_user_oauth_provider_allows_google_test_user_gate_to_decide(self) -> None:
        token = SimpleNamespace(claims={"email": "stranger@example.net"}, subject="subject")
        provider = FakeOAuthProvider(token)
        wrapper = _OAuthAllowlistProvider(
            provider,
            make_settings(
                google_ads_auth_mode="per_user_oauth",
                mcp_allow_all_google_users=True,
            ),
        )

        result = asyncio.run(wrapper.verify_token("raw-token"))

        self.assertIs(result, token)

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

    def test_per_user_google_ads_readiness_does_not_require_shared_refresh_token(self) -> None:
        payload = _google_ads_readiness_payload(
            make_settings(
                google_ads_auth_mode="per_user_oauth",
                developer_token="dev",
                mcp_oauth_client_id="client",
                mcp_oauth_client_secret="secret",
                mcp_base_url="https://example.run.app",
            )
        )

        self.assertTrue(payload["google_ads_configured"])
        self.assertEqual(payload["missing"], [])
        self.assertEqual(payload["google_ads_auth_mode"], "per_user_oauth")
        self.assertFalse(payload["allow_all_google_users"])

    def test_bootstrap_request_allows_header_token_only(self) -> None:
        request = SimpleNamespace(
            query_params={"token": "secret"},
            headers={"x-google-ads-bootstrap-token": "secret"},
        )

        self.assertTrue(_bootstrap_request_allowed(request, "secret"))

    def test_bootstrap_request_rejects_query_token(self) -> None:
        request = SimpleNamespace(query_params={"token": "secret"}, headers={})

        self.assertFalse(_bootstrap_request_allowed(request, "secret"))

    def test_memory_bootstrap_result_store_pops_once_and_expires(self) -> None:
        store = _MemoryBootstrapResultStore()
        ready = {
            "status": "ready",
            "refresh_token": "refresh",
            "expires_at": 9999999999,
        }

        asyncio.run(store.put("nonce", ready, ttl_seconds=600))

        self.assertEqual(asyncio.run(store.pop("nonce"))["refresh_token"], "refresh")
        self.assertEqual(asyncio.run(store.pop("nonce"))["status"], "pending")

        expired = {"status": "ready", "refresh_token": "old", "expires_at": 1}
        asyncio.run(store.put("expired", expired, ttl_seconds=600))

        self.assertEqual(asyncio.run(store.pop("expired"))["status"], "pending")

    def test_memory_bootstrap_result_store_does_not_store_clear_refresh_token(self) -> None:
        store = _MemoryBootstrapResultStore()
        ready = {
            "status": "ready",
            "refresh_token": "secret-refresh-token",
            "expires_at": 9999999999,
        }

        asyncio.run(store.put("nonce", ready, ttl_seconds=600))

        self.assertNotIn("secret-refresh-token", str(store.results))
        self.assertEqual(asyncio.run(store.pop("nonce"))["refresh_token"], "secret-refresh-token")

    def test_key_value_bootstrap_result_store_pops_and_deletes(self) -> None:
        key_value = FakeKeyValueStore()
        store = _KeyValueBootstrapResultStore(key_value)
        ready = {
            "status": "ready",
            "refresh_token": "refresh",
            "expires_at": 9999999999,
        }

        asyncio.run(store.put("nonce", ready, ttl_seconds=600))
        result = asyncio.run(store.pop("nonce"))

        self.assertEqual(result["refresh_token"], "refresh")
        self.assertEqual(key_value.deleted, ["nonce"])
        self.assertEqual(key_value.put_ttl, 600)

    def test_firestore_bootstrap_store_uses_separate_encrypted_prefix_and_salt(self) -> None:
        key_value = FakeKeyValueStore()
        settings = make_settings(
            mcp_token_storage="firestore",
            google_project_id="project",
            mcp_oauth_client_secret="client-secret",
        )

        with patch("google_ads_mcp.server._build_encrypted_firestore_key_value") as build:
            build.return_value = key_value
            store = _build_bootstrap_result_store(settings)

        self.assertIsInstance(store, _KeyValueBootstrapResultStore)
        build.assert_called_once_with(
            settings,
            prefix=BOOTSTRAP_RESULT_FIRESTORE_PREFIX,
            salt=BOOTSTRAP_RESULT_FIRESTORE_SALT,
        )

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

    def test_server_status_reports_operational_settings_without_paths(self) -> None:
        settings = make_settings(
            audit_log_path="C:/private/audit.jsonl",
            metadata_cache_ttl_seconds=120,
            metadata_cache_max_entries=7,
            metadata_snapshot_path="C:/private/metadata.json",
        )
        registry = build_tool_registry({"mode": "safe_read_only"})

        payload = _server_status_payload(settings, registry)

        self.assertTrue(payload["audit_log_enabled"])
        self.assertEqual(payload["metadata_cache_ttl_seconds"], 120)
        self.assertEqual(payload["metadata_cache_max_entries"], 7)
        self.assertTrue(payload["metadata_snapshot_enabled"])
        self.assertFalse(payload["allow_all_google_users"])
        self.assertNotIn("C:/private", str(payload))

    def test_server_status_reports_explicit_allow_all_google_users(self) -> None:
        settings = make_settings(
            google_ads_auth_mode="per_user_oauth",
            mcp_allow_all_google_users=True,
        )
        registry = build_tool_registry({"mode": "safe_read_only"})

        payload = _server_status_payload(settings, registry)

        self.assertTrue(payload["allow_all_google_users"])

    def test_oauth_discovery_payload_supports_claude_discovery(self) -> None:
        settings = make_settings(mcp_base_url="https://example.run.app/")

        payload = _oauth_discovery_payload(settings)

        self.assertEqual(payload["issuer"], "https://example.run.app/")
        self.assertEqual(
            payload["authorization_endpoint"],
            "https://example.run.app/authorize",
        )
        self.assertEqual(payload["token_endpoint"], "https://example.run.app/token")
        self.assertEqual(payload["registration_endpoint"], "https://example.run.app/register")
        self.assertIn("openid", payload["scopes_supported"])
        self.assertEqual(payload["response_types_supported"], ["code"])
        self.assertIn("authorization_code", payload["grant_types_supported"])
        self.assertTrue(payload["client_id_metadata_document_supported"])

    def test_per_user_oauth_discovery_advertises_google_ads_scope(self) -> None:
        settings = make_settings(
            mcp_base_url="https://example.run.app/",
            google_ads_auth_mode="per_user_oauth",
        )

        payload = _oauth_discovery_payload(settings)

        self.assertIn("https://www.googleapis.com/auth/adwords", payload["scopes_supported"])

    def test_per_user_access_token_helper_requires_ads_scope(self) -> None:
        token = SimpleNamespace(token="google-access-token", scopes=["openid"])

        with self.assertRaises(ConfigError):
            _google_ads_access_token_value(token)

    def test_per_user_access_token_helper_returns_token_value(self) -> None:
        token = SimpleNamespace(
            token="google-access-token",
            scopes=["openid", "https://www.googleapis.com/auth/adwords"],
        )

        self.assertEqual(_google_ads_access_token_value(token), "google-access-token")

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

    def test_operational_env_settings_are_loaded(self) -> None:
        names = {
            "GOOGLE_ADS_AUDIT_LOG_PATH": "C:/logs/google-ads-audit.jsonl",
            "GOOGLE_ADS_METADATA_CACHE_TTL_SECONDS": "120",
            "GOOGLE_ADS_METADATA_CACHE_MAX_ENTRIES": "7",
            "GOOGLE_ADS_METADATA_SNAPSHOT_PATH": "C:/snapshots/metadata.json",
        }
        previous = {name: os.environ.get(name) for name in names}
        try:
            os.environ.update(names)
            settings = Settings.from_env()
        finally:
            for name, value in previous.items():
                if value is None:
                    os.environ.pop(name, None)
                else:
                    os.environ[name] = value

        self.assertEqual(settings.audit_log_path, "C:/logs/google-ads-audit.jsonl")
        self.assertEqual(settings.metadata_cache_ttl_seconds, 120)
        self.assertEqual(settings.metadata_cache_max_entries, 7)
        self.assertEqual(settings.metadata_snapshot_path, "C:/snapshots/metadata.json")


if __name__ == "__main__":
    unittest.main()
