"""Legacy stdio-to-Streamable-HTTP relay.

The npm `google-ads-mcp relay` command is the canonical relay for user-facing
client configs. This Python entrypoint remains for existing pip-based installs.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


STDIO_RELAY_REMOVAL_DATE = "2026-09-30"


def _extract_json_response(body: bytes, content_type: str) -> str:
    text = body.decode("utf-8")
    if "text/event-stream" not in content_type:
        return text
    for line in text.splitlines():
        if line.startswith("data: "):
            return line.removeprefix("data: ")
    return text


def _json_rpc_error(code: int, message: str, *, request_id: object | None) -> str:
    return json.dumps(
        {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": code, "message": message},
        }
    )


def main() -> None:
    print(
        "google-ads-mcp-stdio-relay is deprecated and will be removed on "
        f"{STDIO_RELAY_REMOVAL_DATE}; use the npm `google-ads-mcp relay` command instead.",
        file=sys.stderr,
    )
    mcp_url = os.environ.get("MCP_URL")
    token = os.environ.get("MCP_BEARER_TOKEN")
    if not mcp_url or not token:
        print(
            "MCP_URL and MCP_BEARER_TOKEN are required for google-ads-mcp-stdio-relay.",
            file=sys.stderr,
        )
        raise SystemExit(2)

    session_id: str | None = None
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request_payload = json.loads(line)
        except json.JSONDecodeError as exc:
            print(_json_rpc_error(-32700, str(exc), request_id=None))
            sys.stdout.flush()
            continue
        request_id = request_payload.get("id") if isinstance(request_payload, dict) else None

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if session_id:
            headers["mcp-session-id"] = session_id
        request = urllib.request.Request(
            mcp_url,
            data=line.encode("utf-8"),
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=300) as response:
                session_id = response.headers.get("mcp-session-id") or session_id
                payload = _extract_json_response(
                    response.read(),
                    response.headers.get("content-type", ""),
                )
        except urllib.error.HTTPError as exc:
            payload = _json_rpc_error(
                exc.code,
                exc.read().decode("utf-8", errors="replace"),
                request_id=request_id,
            )
        except (urllib.error.URLError, OSError) as exc:
            payload = _json_rpc_error(-32000, str(exc), request_id=request_id)
        print(payload)
        sys.stdout.flush()


if __name__ == "__main__":
    main()

