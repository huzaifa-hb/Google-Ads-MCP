from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.config import ConfigError
from test_tool_config import make_settings


class AuthConfigTests(unittest.TestCase):
    def test_bearer_auth_requires_token_by_default(self) -> None:
        settings = make_settings(mcp_bearer_token=None)

        with self.assertRaises(ConfigError):
            settings.require_mcp_auth()

    def test_unauthenticated_local_dev_bypasses_auth_requirement(self) -> None:
        settings = make_settings(mcp_bearer_token=None, allow_unauthenticated_mcp=True)

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
        )

        settings.require_mcp_auth()


if __name__ == "__main__":
    unittest.main()
