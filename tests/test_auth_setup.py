from __future__ import annotations

import argparse
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp import auth_setup


class AuthSetupTests(unittest.TestCase):
    def test_client_values_from_installed_client_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir, "client_secret.json")
            path.write_text(
                json.dumps(
                    {
                        "installed": {
                            "client_id": "client-id.apps.googleusercontent.com",
                            "client_secret": "client-secret",
                        }
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                auth_setup._client_values_from_file(path),
                ("client-id.apps.googleusercontent.com", "client-secret"),
            )

    def test_client_values_from_web_client_secret_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir, "client_secret.json")
            path.write_text(
                json.dumps(
                    {
                        "web": {
                            "client_id": "web-client-id.apps.googleusercontent.com",
                            "client_secret": "web-client-secret",
                        }
                    }
                ),
                encoding="utf-8",
            )

            self.assertEqual(
                auth_setup._client_values_from_file(path),
                ("web-client-id.apps.googleusercontent.com", "web-client-secret"),
            )

    def test_write_env_preserves_comments_and_updates_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir, ".env")
            path.write_text(
                "# existing file\n"
                "GOOGLE_ADS_CLIENT_ID=old-client\n"
                "UNCHANGED=value\n",
                encoding="utf-8",
            )

            auth_setup._write_env(
                path,
                {
                    "GOOGLE_ADS_CLIENT_ID": "new-client",
                    "GOOGLE_ADS_REFRESH_TOKEN": "refresh-token",
                },
            )

            content = path.read_text(encoding="utf-8")

        self.assertIn("# existing file\n", content)
        self.assertIn("GOOGLE_ADS_CLIENT_ID=new-client\n", content)
        self.assertIn("UNCHANGED=value\n", content)
        self.assertIn("GOOGLE_ADS_REFRESH_TOKEN=refresh-token\n", content)

    def test_missing_client_credentials_errors_before_oauth_import(self) -> None:
        stderr = io.StringIO()

        with redirect_stderr(stderr), self.assertRaises(SystemExit) as raised:
            auth_setup.main([])

        self.assertEqual(raised.exception.code, 2)
        self.assertIn("Provide either --client-secrets", stderr.getvalue())

    def test_write_env_does_not_print_refresh_token(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            env_path = Path(temp_dir, ".env")
            args = argparse.Namespace(
                client_secrets=None,
                client_id="client-id",
                client_secret="client-secret",
                developer_token="developer-token",
                login_customer_id=None,
                env_file=str(env_path),
                write_env=True,
                prompt=False,
            )
            credentials = SimpleNamespace(refresh_token="secret-refresh-token")
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                auth_setup._emit_or_store_credentials(
                    args,
                    credentials,
                    auth_setup.build_parser(),
                )

            output = stdout.getvalue()
            content = env_path.read_text(encoding="utf-8")

        self.assertNotIn("secret-refresh-token", output)
        self.assertIn("Refresh token was saved locally and was not printed.", output)
        self.assertIn("GOOGLE_ADS_REFRESH_TOKEN=secret-refresh-token\n", content)
        self.assertIn("GOOGLE_ADS_CLIENT_ID=client-id\n", content)
        self.assertIn("GOOGLE_ADS_CLIENT_SECRET=client-secret\n", content)


if __name__ == "__main__":
    unittest.main()
