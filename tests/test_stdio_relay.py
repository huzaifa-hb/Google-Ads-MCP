from __future__ import annotations

import json
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.stdio_relay import _json_rpc_error


class StdioRelayTests(unittest.TestCase):
    def test_json_rpc_error_shape_for_network_failures(self) -> None:
        payload = json.loads(_json_rpc_error(-32000, "connection refused", request_id=7))

        self.assertEqual(payload["jsonrpc"], "2.0")
        self.assertEqual(payload["id"], 7)
        self.assertEqual(payload["error"]["code"], -32000)
        self.assertEqual(payload["error"]["message"], "connection refused")

    def test_json_rpc_error_uses_null_id_for_parse_errors(self) -> None:
        payload = json.loads(_json_rpc_error(-32700, "bad json", request_id=None))

        self.assertIsNone(payload["id"])


if __name__ == "__main__":
    unittest.main()
