"""Local Google Ads OAuth setup helper.

This module backs the ``google-ads-mcp-auth`` console script. It performs the
one-time browser OAuth flow used to generate a refresh token, and can optionally
write local smoke-test values into an env file.
"""

from __future__ import annotations

import argparse
import getpass
import json
from pathlib import Path
import secrets
from collections.abc import Sequence
import sys
from typing import Any

SCOPES = ("https://www.googleapis.com/auth/adwords",)

ENV_DEFAULTS = {
    "GOOGLE_ADS_API_VERSION": "v24",
    "HOST": "0.0.0.0",
    "PORT": "8080",
    "GOOGLE_ADS_MCP_MODE": "safe_read_only",
    "GOOGLE_ADS_MCP_AUTH_MODE": "bearer",
    "ALLOW_UNAUTHENTICATED_MCP": "false",
    "GOOGLE_ADS_MCP_ALLOW_LEGACY_WRITE_DEFAULTS": "false",
    "GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE": "false",
}


def main(argv: Sequence[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.prompt and not args.client_secrets:
        if not args.client_id:
            args.client_id = input("GOOGLE_ADS_CLIENT_ID: ").strip()
        if not args.client_secret:
            args.client_secret = getpass.getpass("GOOGLE_ADS_CLIENT_SECRET: ").strip()

    if not args.client_secrets and not (args.client_id and args.client_secret):
        parser.error("Provide either --client-secrets or both --client-id and --client-secret.")

    credentials = _run_oauth_flow(args)
    _emit_or_store_credentials(args, credentials, parser)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a Google Ads OAuth refresh token.")
    parser.add_argument(
        "--client-secrets",
        help="Path to an OAuth Desktop client JSON file downloaded from Google Cloud.",
    )
    parser.add_argument("--client-id", help="OAuth client ID. Use with --client-secret.")
    parser.add_argument("--client-secret", help="OAuth client secret. Use with --client-id.")
    parser.add_argument(
        "--developer-token",
        help="Google Ads developer token. Required with --write-env unless already in the env file.",
    )
    parser.add_argument(
        "--login-customer-id",
        help="Optional manager account ID used as login_customer_id. Digits only, no dashes.",
    )
    parser.add_argument(
        "--env-file",
        default=".env",
        help="Path to the env file to update when --write-env is set. Defaults to .env.",
    )
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Write local .env values instead of printing the refresh token.",
    )
    parser.add_argument(
        "--prompt",
        action="store_true",
        help="Prompt locally for missing client and token values.",
    )
    return parser


def _run_oauth_flow(args: argparse.Namespace) -> Any:
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit(
            "Missing google-auth-oauthlib. Install setup extras first: "
            'python -m pip install -e ".[setup]"'
        ) from exc

    if args.client_secrets:
        flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, scopes=SCOPES)
    else:
        flow = InstalledAppFlow.from_client_config(
            _installed_client_config(args.client_id, args.client_secret),
            scopes=SCOPES,
        )

    return flow.run_local_server(
        host="127.0.0.1",
        port=0,
        authorization_prompt_message="Open this URL and authorize Google Ads access:\n{url}\n",
        success_message="Authorization complete. You can close this browser tab.",
        open_browser=True,
        prompt="consent",
    )


def _installed_client_config(client_id: str, client_secret: str) -> dict[str, dict[str, object]]:
    return {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }


def _emit_or_store_credentials(
    args: argparse.Namespace,
    credentials: Any,
    parser: argparse.ArgumentParser,
) -> None:
    refresh_token = getattr(credentials, "refresh_token", None)
    if not refresh_token:
        raise SystemExit(
            "Google did not return a refresh token. Re-run after removing prior app access "
            "from your Google Account, or recreate the OAuth client and consent again."
        )

    if args.write_env:
        _write_env_credentials(args, refresh_token, parser)
        print(f"Updated {Path(args.env_file)} with Google Ads OAuth values.")
        print("Refresh token was saved locally and was not printed.")
        return

    print("\nGOOGLE_ADS_REFRESH_TOKEN")
    print(refresh_token)
    print("\nStore this in Secret Manager. Do not commit it.", file=sys.stderr)


def _write_env_credentials(
    args: argparse.Namespace,
    refresh_token: str,
    parser: argparse.ArgumentParser,
) -> None:
    client_id = args.client_id
    client_secret = args.client_secret
    if args.client_secrets:
        client_id, client_secret = _client_values_from_file(Path(args.client_secrets))
    if not client_id or not client_secret:
        parser.error("--write-env requires --client-id and --client-secret, or --client-secrets.")

    env_path = Path(args.env_file)
    current = _read_env(env_path)
    developer_token = args.developer_token or current.get("GOOGLE_ADS_DEVELOPER_TOKEN")
    if not developer_token and args.prompt:
        developer_token = getpass.getpass("GOOGLE_ADS_DEVELOPER_TOKEN: ").strip()
    if not developer_token:
        parser.error("--write-env requires --developer-token or an existing GOOGLE_ADS_DEVELOPER_TOKEN.")
    if (
        args.prompt
        and args.login_customer_id is None
        and not current.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID")
    ):
        login_customer_id = input(
            "GOOGLE_ADS_LOGIN_CUSTOMER_ID, optional manager ID, digits only: "
        ).strip()
        args.login_customer_id = login_customer_id or None

    values = {
        **ENV_DEFAULTS,
        "MCP_BEARER_TOKEN": current.get("MCP_BEARER_TOKEN") or secrets.token_urlsafe(32),
        "GOOGLE_ADS_DEVELOPER_TOKEN": developer_token,
        "GOOGLE_ADS_CLIENT_ID": client_id,
        "GOOGLE_ADS_CLIENT_SECRET": client_secret,
        "GOOGLE_ADS_REFRESH_TOKEN": refresh_token,
        "GOOGLE_ADS_LOGIN_CUSTOMER_ID": (
            args.login_customer_id
            if args.login_customer_id is not None
            else current.get("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "")
        ),
    }
    _write_env(env_path, values)


def _client_values_from_file(path: Path) -> tuple[str | None, str | None]:
    data = json.loads(path.read_text(encoding="utf-8"))
    client_config = data.get("installed") or data.get("web") or {}
    return client_config.get("client_id"), client_config.get("client_secret")


def _read_env(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def _write_env(path: Path, updates: dict[str, str]) -> None:
    existing_lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    seen: set[str] = set()
    output: list[str] = []

    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            output.append(line)
            continue
        key = stripped.split("=", 1)[0].strip()
        if key in updates:
            output.append(f"{key}={updates[key]}")
            seen.add(key)
        else:
            output.append(line)

    if output and output[-1].strip():
        output.append("")

    for key, value in updates.items():
        if key not in seen:
            output.append(f"{key}={value}")

    path.write_text("\n".join(output) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
