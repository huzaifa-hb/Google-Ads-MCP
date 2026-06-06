import http from "node:http";
import test from "node:test";
import assert from "node:assert/strict";
import { extractJsonResponse } from "../../dist/node-cli/http.js";
import { relayLine } from "../../dist/node-cli/relay.js";

test("extractJsonResponse reads first event-stream data line", () => {
  const body = "event: message\ndata: {\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{}}\n\n";
  assert.equal(extractJsonResponse(body, "text/event-stream"), "{\"jsonrpc\":\"2.0\",\"id\":1,\"result\":{}}");
});

test("relayLine forwards authorization header and preserves session id", async () => {
  const server = http.createServer((req, res) => {
    assert.equal(req.headers.authorization, "Bearer test-token");
    res.setHeader("content-type", "text/event-stream");
    res.setHeader("mcp-session-id", "session-1");
    res.end("data: {\"jsonrpc\":\"2.0\",\"id\":7,\"result\":{\"ok\":true}}\n\n");
  });
  await new Promise((resolve) => server.listen(0, resolve));
  const address = server.address();
  assert.equal(typeof address, "object");
  try {
    const result = await relayLine({
      line: "{\"jsonrpc\":\"2.0\",\"id\":7,\"method\":\"ping\"}",
      url: `http://127.0.0.1:${address.port}/mcp`,
      token: "test-token"
    });
    assert.equal(result.sessionId, "session-1");
    assert.deepEqual(JSON.parse(result.output).result, { ok: true });
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});

test("relayLine returns JSON-RPC parse errors", async () => {
  const result = await relayLine({
    line: "{",
    url: "http://127.0.0.1:1/mcp",
    token: "test-token"
  });
  const parsed = JSON.parse(result.output);
  assert.equal(parsed.error.code, -32700);
});

test("relayLine emits no output for empty successful notification response", async () => {
  const server = http.createServer((req, res) => {
    assert.equal(req.headers.authorization, "Bearer test-token");
    res.statusCode = 202;
    res.end("");
  });
  await new Promise((resolve) => server.listen(0, resolve));
  const address = server.address();
  assert.equal(typeof address, "object");
  try {
    const result = await relayLine({
      line: "{\"jsonrpc\":\"2.0\",\"method\":\"notifications/initialized\"}",
      url: `http://127.0.0.1:${address.port}/mcp`,
      token: "test-token"
    });
    assert.equal(result.output, undefined);
  } finally {
    await new Promise((resolve) => server.close(resolve));
  }
});
