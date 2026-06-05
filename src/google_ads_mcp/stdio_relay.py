"""Small stdio-to-Streamable-HTTP relay for clients that cannot send headers."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request


def _extract_json_response(body: bytes, content_type: str) -> str:
    text = body.decode("utf-8")
    if "text/event-stream" not in content_type:
        return text
    for line in text.splitlines():
        if line.startswith("data: "):
            return line.removeprefix("data: ")
    return text


def _json_rpc_error(code: int, message: str) -> str:
    return json.dumps({"jsonrpc": "2.0", "error": {"code": code, "message": message}})


def main() -> None:
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
            json.loads(line)
        except json.JSONDecodeError as exc:
            print(json.dumps({"jsonrpc": "2.0", "error": {"code": -32700, "message": str(exc)}}))
            sys.stdout.flush()
            continue

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
            )
        except (urllib.error.URLError, OSError) as exc:
            payload = _json_rpc_error(-32000, str(exc))
        print(payload)
        sys.stdout.flush()


if __name__ == "__main__":
    main()

