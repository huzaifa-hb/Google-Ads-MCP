import test from "node:test";
import assert from "node:assert/strict";
import { renderClientConfig } from "../../dist/node-cli/config.js";

test("codex remote config references token env var", () => {
  const config = renderClientConfig({
    client: "codex",
    transport: "remote",
    url: "https://example.run.app/mcp",
    tokenEnv: "MCP_BEARER_TOKEN"
  });
  assert.match(config, /bearer_token_env_var = "MCP_BEARER_TOKEN"/);
  assert.doesNotMatch(config, /Bearer\s+[A-Za-z0-9]/);
});

test("stdio config uses npx relay without a secret-bearing token arg", () => {
  const config = renderClientConfig({
    client: "claude-desktop",
    transport: "stdio",
    url: "https://example.run.app/mcp",
    tokenEnv: "MCP_BEARER_TOKEN",
    envFile: "C:/repo/.env"
  });
  const parsed = JSON.parse(config);
  const args = parsed.mcpServers["google-ads-mcp"].args;
  assert.deepEqual(args.slice(0, 4), ["-y", "@huzaifa-hb/google-ads-mcp", "relay", "--url"]);
  assert.ok(args.includes("--token-env"));
  assert.ok(args.includes("--env-file"));
  assert.ok(args.includes("C:/repo/.env"));
  assert.ok(!args.some((arg) => String(arg).startsWith("--token=")));
});
