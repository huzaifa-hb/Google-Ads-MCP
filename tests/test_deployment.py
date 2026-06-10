from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DeploymentConfigTests(unittest.TestCase):
    def test_dockerfile_does_not_copy_gcloudignored_docs(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")
        gcloudignore = (ROOT / ".gcloudignore").read_text(encoding="utf-8")

        copies_docs = "COPY docs " in dockerfile or "COPY docs/" in dockerfile
        ignores_docs = any(
            line.strip().rstrip("/") == "docs"
            for line in gcloudignore.splitlines()
            if line.strip() and not line.strip().startswith("#")
        )

        self.assertFalse(copies_docs and ignores_docs)

    def test_dockerfile_copies_root_tools_config(self) -> None:
        dockerfile = (ROOT / "Dockerfile").read_text(encoding="utf-8")

        self.assertIn("tools_config.yaml", dockerfile)

    def test_secret_helper_writes_utf8_without_bom(self) -> None:
        script = (ROOT / "scripts" / "set_gcp_secret.ps1").read_text(encoding="utf-8")

        self.assertIn("[System.Text.UTF8Encoding]::new($false)", script)
        self.assertIn("[System.IO.File]::WriteAllText($tmp, $Value, $utf8NoBom)", script)

    def test_cloud_run_script_requires_oauth_base_url_and_uses_free_tier_oauth_shape(
        self,
    ) -> None:
        script = (ROOT / "deploy" / "cloud-run.ps1").read_text(encoding="utf-8")

        self.assertNotIn("ToolsConfigPath", script)
        self.assertIn("-McpBaseUrl is required when -McpAuthMode oauth_proxy", script)
        self.assertIn("-McpOAuthClientId is required when -McpAuthMode oauth_proxy", script)
        self.assertIn(
            "unless -GoogleAdsAuthMode per_user_oauth and -McpAllowAllGoogleUsers",
            script,
        )
        self.assertIn("-GoogleAdsAuthMode must be shared_refresh_token or per_user_oauth", script)
        self.assertIn("-McpTokenStorage must be local or firestore", script)
        self.assertIn("GOOGLE_ADS_MCP_BASE_URL=$McpBaseUrl", script)
        self.assertIn("GOOGLE_ADS_AUTH_MODE=$GoogleAdsAuthMode", script)
        self.assertIn("GOOGLE_ADS_MCP_TOKEN_STORAGE=$McpTokenStorage", script)
        self.assertIn("GOOGLE_ADS_MCP_ALLOWED_EMAILS=$McpAllowedEmails", script)
        self.assertIn("GOOGLE_ADS_MCP_ALLOWED_DOMAINS=$McpAllowedDomains", script)
        self.assertIn("GOOGLE_ADS_MCP_ALLOW_ALL_GOOGLE_USERS=true", script)
        self.assertIn("GOOGLE_ADS_MCP_FIRESTORE_DATABASE=$McpFirestoreDatabase", script)
        self.assertIn("GOOGLE_ADS_MCP_OAUTH_CLIENT_ID=$McpOAuthClientId", script)
        self.assertIn('$GoogleAdsAuthMode -eq "shared_refresh_token"', script)
        self.assertIn("--min-instances $MinInstances", script)
        self.assertIn("--max-instances $MaxInstances", script)
        self.assertIn("--memory $Memory", script)
        self.assertIn("--cpu $Cpu", script)
        self.assertIn("--cpu-throttling", script)
        self.assertIn("--no-cpu-boost", script)
        self.assertIn('state=enabled OR state=disabled', script)
        self.assertIn("Remove-OldSecretVersions", script)
        self.assertIn("Remove-OldArtifactImages", script)
        self.assertNotIn(
            "GOOGLE_ADS_MCP_OAUTH_CLIENT_ID=GOOGLE_ADS_MCP_OAUTH_CLIENT_ID:latest",
            script,
        )
        self.assertIn(
            '$secretMappings += "MCP_BEARER_TOKEN=MCP_BEARER_TOKEN:latest"',
            script,
        )
        self.assertIn('if ($McpAuthMode -eq "bearer")', script)
        self.assertIn(
            "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET=GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET:latest",
            script,
        )
        self.assertIn('if ($McpTokenStorage -eq "firestore")', script)
        self.assertIn("roles/datastore.user", script)
        self.assertIn("firestore.googleapis.com", script)


if __name__ == "__main__":
    unittest.main()
