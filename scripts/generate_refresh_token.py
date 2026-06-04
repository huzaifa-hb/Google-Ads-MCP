"""Generate a Google Ads OAuth refresh token for a single-owner deployment.

The token is printed to stdout so the owner can paste it into Secret Manager.
Do not redirect this output into a tracked file.
"""

from __future__ import annotations

import argparse
import sys

SCOPES = ("https://www.googleapis.com/auth/adwords",)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Google Ads OAuth refresh token.")
    parser.add_argument(
        "--client-secrets",
        help="Path to an OAuth Desktop client JSON file downloaded from Google Cloud.",
    )
    parser.add_argument("--client-id", help="OAuth client ID. Use with --client-secret.")
    parser.add_argument("--client-secret", help="OAuth client secret. Use with --client-id.")
    args = parser.parse_args()

    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError as exc:
        raise SystemExit(
            "Missing google-auth-oauthlib. Install setup extras first: "
            'python -m pip install -e ".[setup]"'
        ) from exc

    if args.client_secrets:
        flow = InstalledAppFlow.from_client_secrets_file(args.client_secrets, scopes=SCOPES)
    elif args.client_id and args.client_secret:
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": args.client_id,
                    "client_secret": args.client_secret,
                    "auth_uri": "https://accounts.google.com/o/oauth2/v2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost"],
                }
            },
            scopes=SCOPES,
        )
    else:
        parser.error("Provide either --client-secrets or both --client-id and --client-secret.")

    credentials = flow.run_local_server(
        host="127.0.0.1",
        port=0,
        authorization_prompt_message="Open this URL and authorize Google Ads access:\n{url}\n",
        success_message="Authorization complete. You can close this browser tab.",
        open_browser=True,
        prompt="consent",
    )
    if not credentials.refresh_token:
        raise SystemExit(
            "Google did not return a refresh token. Re-run after removing prior app access "
            "from your Google Account, or recreate the OAuth client and consent again."
        )

    print("\nGOOGLE_ADS_REFRESH_TOKEN")
    print(credentials.refresh_token)
    print("\nStore this in Secret Manager. Do not commit it.", file=sys.stderr)


if __name__ == "__main__":
    main()
