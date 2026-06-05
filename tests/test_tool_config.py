from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.config import ConfigError, Settings
from google_ads_mcp.tool_config import build_tool_registry, load_tool_registry


def make_settings(**overrides: object) -> Settings:
    values = {
        "mcp_bearer_token": "token",
        "developer_token": None,
        "oauth_client_id": None,
        "oauth_client_secret": None,
        "refresh_token": None,
        "login_customer_id": None,
        "google_project_id": None,
        "api_version": "v24",
        "host": "127.0.0.1",
        "port": 8080,
        "auth_mode": "bearer",
        "allow_unauthenticated_mcp": False,
        "mcp_mode": None,
        "tools_config_path": None,
        "allow_legacy_write_defaults": False,
        "enable_generic_service_bridge": False,
        "mcp_oauth_client_id": None,
        "mcp_oauth_client_secret": None,
        "mcp_base_url": None,
        "max_retries": 0,
        "retry_base_seconds": 0.0,
    }
    values.update(overrides)
    return Settings(**values)


class ToolConfigTests(unittest.TestCase):
    def test_bundled_default_loads_without_cwd_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = load_tool_registry(make_settings(), cwd=Path(temp_dir))

        self.assertEqual(registry.mode, "safe_read_only")
        self.assertIn("get_tool_catalog", registry.registered_names)
        self.assertIn("get_capability_matrix", registry.registered_names)
        self.assertIn("get_server_status", registry.registered_names)
        self.assertIn("account_list_accessible_customers", registry.registered_names)
        self.assertIn("metadata_get_google_ads_resource_metadata", registry.registered_names)
        self.assertIn("metadata_validate_gaql_fields", registry.registered_names)
        self.assertIn("planning_plan_gaql_query", registry.registered_names)
        self.assertIn("reporting_get_campaign_metrics", registry.registered_names)
        self.assertNotIn("google_ads_mutate", registry.registered_names)
        self.assertNotIn("generic_google_ads_call_service", registry.registered_names)

    def test_env_config_path_overrides_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "custom.yaml"
            path.write_text(
                """
mode: validation_only
legacy_aliases:
  enabled: true
namespaces:
  campaigns:
    enabled: true
    prefix: camp
tools:
  pause_campaign:
    enabled: true
""",
                encoding="utf-8",
            )
            registry = load_tool_registry(
                make_settings(tools_config_path=str(path)),
                cwd=Path(temp_dir),
            )

        self.assertEqual(registry.mode, "validation_only")
        self.assertIn("camp_pause_campaign", registry.registered_names)
        self.assertIn("pause_campaign", registry.registered_names)

    def test_env_mode_overrides_config_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "custom.yaml"
            path.write_text(
                """
mode: safe_read_only
namespaces:
  campaigns:
    enabled: true
    prefix: campaigns
""",
                encoding="utf-8",
            )
            registry = load_tool_registry(
                make_settings(tools_config_path=str(path), mcp_mode="write_enabled"),
                cwd=Path(temp_dir),
            )
        self.assertEqual(registry.mode, "write_enabled")

    def test_invalid_mode_fails_fast(self) -> None:
        with self.assertRaises(ConfigError):
            build_tool_registry({"mode": "danger"})

    def test_invalid_prefix_fails_fast(self) -> None:
        with self.assertRaises(ConfigError):
            build_tool_registry(
                {
                    "mode": "safe_read_only",
                    "namespaces": {"campaigns": {"enabled": True, "prefix": "Bad-Prefix"}},
                }
            )

    def test_unknown_tool_fails_fast(self) -> None:
        with self.assertRaises(ConfigError):
            build_tool_registry({"tools": {"not_a_tool": {"enabled": True}}})

    def test_safe_read_only_hides_mutation_tools(self) -> None:
        registry = build_tool_registry(
            {
                "mode": "safe_read_only",
                "namespaces": {"campaigns": {"enabled": True, "prefix": "campaigns"}},
                "tools": {"pause_campaign": {"enabled": True}},
            }
        )
        self.assertIn("campaigns_list_campaigns", registry.registered_names)
        self.assertNotIn("campaigns_pause_campaign", registry.registered_names)

    def test_validation_only_exposes_configured_mutations(self) -> None:
        registry = build_tool_registry(
            {
                "mode": "validation_only",
                "namespaces": {"campaigns": {"enabled": True, "prefix": "campaigns"}},
                "tools": {"pause_campaign": {"enabled": True}},
            }
        )
        self.assertIn("campaigns_pause_campaign", registry.registered_names)
        self.assertNotIn("generic_google_ads_mutate", registry.registered_names)

    def test_write_enabled_exposes_configured_writes_but_not_generic_bridge(self) -> None:
        registry = build_tool_registry(
            {
                "mode": "write_enabled",
                "namespaces": {
                    "campaigns": {"enabled": True, "prefix": "campaigns"},
                    "generic": {"enabled": True, "prefix": "generic"},
                },
                "tools": {
                    "pause_campaign": {"enabled": True},
                    "google_ads_call_service": {"enabled": True},
                },
            }
        )
        self.assertIn("campaigns_pause_campaign", registry.registered_names)
        self.assertNotIn("generic_google_ads_call_service", registry.registered_names)

    def test_admin_debug_can_expose_generic_bridge(self) -> None:
        registry = build_tool_registry(
            {
                "mode": "admin_debug",
                "namespaces": {"generic": {"enabled": True, "prefix": "generic"}},
                "tools": {"google_ads_call_service": {"enabled": True}},
            }
        )
        self.assertIn("generic_google_ads_call_service", registry.registered_names)

    def test_legacy_defaults_require_explicit_env_escape_hatch(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            registry = load_tool_registry(
                make_settings(allow_legacy_write_defaults=True),
                cwd=Path(temp_dir),
            )

        self.assertEqual(registry.mode, "admin_debug")
        self.assertIn("generic_google_ads_call_service", registry.registered_names)
        self.assertIn("google_ads_call_service", registry.registered_names)


if __name__ == "__main__":
    unittest.main()
