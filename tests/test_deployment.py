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

    def test_cloud_run_script_requires_oauth_base_url_and_uses_secret_mappings(self) -> None:
        script = (ROOT / "deploy" / "cloud-run.ps1").read_text(encoding="utf-8")

        self.assertNotIn("ToolsConfigPath", script)
        self.assertIn("-McpBaseUrl is required when -McpAuthMode oauth_proxy", script)
        self.assertIn("GOOGLE_ADS_MCP_BASE_URL=$McpBaseUrl", script)
        self.assertIn(
            "GOOGLE_ADS_MCP_OAUTH_CLIENT_ID=GOOGLE_ADS_MCP_OAUTH_CLIENT_ID:latest",
            script,
        )
        self.assertIn(
            "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET=GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET:latest",
            script,
        )


if __name__ == "__main__":
    unittest.main()
