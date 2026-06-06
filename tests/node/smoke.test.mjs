import test from "node:test";
import assert from "node:assert/strict";
import {
  assertJsonRpcOk,
  registeredNameForCanonical,
  toolPayloadFromResponse
} from "../../dist/node-cli/smoke.js";

test("smoke resolves registered tool names from catalog", () => {
  const catalog = {
    tools: [
      {
        canonical_name: "list_accessible_customers",
        registered_name: "account_list_accessible_customers"
      }
    ]
  };

  assert.equal(
    registeredNameForCanonical(catalog, "list_accessible_customers"),
    "account_list_accessible_customers"
  );
});

test("smoke rejects JSON-RPC errors", () => {
  assert.throws(
    () => assertJsonRpcOk("get_tool_catalog", { error: { code: -32602, message: "bad" } }),
    /JSON-RPC error/
  );
});

test("smoke rejects tool-level ok false payloads", () => {
  const response = {
    result: {
      content: [{ type: "text", text: '{"ok":false,"error":"bad credentials"}' }]
    }
  };

  assert.throws(() => assertJsonRpcOk("account_list_accessible_customers", response), /tool-level/);
});

test("smoke extracts FastMCP text JSON payloads", () => {
  const response = {
    result: {
      content: [{ type: "text", text: '{"tools":[{"canonical_name":"x","name":"metadata_x"}]}' }]
    }
  };

  assert.deepEqual(toolPayloadFromResponse(response), {
    tools: [{ canonical_name: "x", name: "metadata_x" }]
  });
});
