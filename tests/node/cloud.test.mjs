import test from "node:test";
import assert from "node:assert/strict";
import {
  buildDeployCommand,
  buildSecretVersionCommand,
  missingRequiredSecrets
} from "../../dist/node-cli/cloud.js";

test("secret commands use data files instead of secret values", () => {
  const create = buildSecretVersionCommand("MCP_BEARER_TOKEN", "project-1", "C:/tmp/secret", false);
  assert.equal(create.command, "gcloud");
  assert.deepEqual(create.args, [
    "secrets",
    "create",
    "MCP_BEARER_TOKEN",
    "--data-file=C:/tmp/secret",
    "--project=project-1"
  ]);

  const add = buildSecretVersionCommand("MCP_BEARER_TOKEN", "project-1", "C:/tmp/secret", true);
  assert.equal(add.args[0], "secrets");
  assert.equal(add.args[1], "versions");
  assert.equal(add.args[2], "add");
  assert.ok(!add.args.some((arg) => arg.includes("secret-value")));
});

test("deploy command delegates to the existing Cloud Run script", () => {
  const command = buildDeployCommand("C:/repo", {
    projectId: "project-1",
    region: "us-central1",
    mode: "safe_read_only",
    authMode: "bearer"
  });
  assert.ok(command.args.includes("-ProjectId"));
  assert.ok(command.args.includes("project-1"));
  assert.ok(command.args.includes("-McpMode"));
  assert.ok(command.args.includes("safe_read_only"));
});

test("deploy command passes OAuth proxy base URL", () => {
  const command = buildDeployCommand("C:/repo", {
    projectId: "project-1",
    region: "us-central1",
    mode: "safe_read_only",
    authMode: "oauth_proxy",
    mcpBaseUrl: "https://example.run.app"
  });
  assert.ok(command.args.includes("-McpBaseUrl"));
  assert.ok(command.args.includes("https://example.run.app"));
});

test("required secret validation rejects placeholders", () => {
  const missing = missingRequiredSecrets({
    MCP_BEARER_TOKEN: "replace-with-long-random-token",
    GOOGLE_ADS_DEVELOPER_TOKEN: "dev",
    GOOGLE_ADS_CLIENT_ID: "client",
    GOOGLE_ADS_CLIENT_SECRET: "secret",
    GOOGLE_ADS_REFRESH_TOKEN: "refresh"
  });
  assert.deepEqual(missing, ["MCP_BEARER_TOKEN"]);
});
