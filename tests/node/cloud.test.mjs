import test from "node:test";
import assert from "node:assert/strict";
import {
  buildDeployCommand,
  buildSecretVersionCommand,
  missingRequiredSecrets,
  requiredSecretsForAuthMode
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
    mcpBaseUrl: "https://example.run.app",
    googleAdsClientId: "google-ads-client.apps.googleusercontent.com",
    mcpOAuthClientId: "mcp-client.apps.googleusercontent.com",
    mcpAllowedDomains: "gmail.com,example.com",
    minInstances: "0",
    maxInstances: "1",
    memory: "512Mi",
    cpu: "1"
  });
  assert.ok(command.args.includes("-McpBaseUrl"));
  assert.ok(command.args.includes("https://example.run.app"));
  assert.ok(command.args.includes("-GoogleAdsClientId"));
  assert.ok(command.args.includes("google-ads-client.apps.googleusercontent.com"));
  assert.ok(command.args.includes("-McpOAuthClientId"));
  assert.ok(command.args.includes("mcp-client.apps.googleusercontent.com"));
  assert.ok(command.args.includes("-McpAllowedDomains"));
  assert.ok(command.args.includes("gmail.com,example.com"));
  assert.ok(command.args.includes("-MinInstances"));
  assert.ok(command.args.includes("0"));
  assert.ok(command.args.includes("-MaxInstances"));
  assert.ok(command.args.includes("1"));
  assert.ok(command.args.includes("-Memory"));
  assert.ok(command.args.includes("512Mi"));
  assert.ok(command.args.includes("-Cpu"));
  assert.ok(command.args.includes("1"));
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

test("OAuth proxy secrets skip bearer token and non-sensitive client IDs", () => {
  assert.deepEqual(requiredSecretsForAuthMode("oauth_proxy"), [
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN",
    "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET"
  ]);
  const missing = missingRequiredSecrets(
    {
      MCP_BEARER_TOKEN: "",
      GOOGLE_ADS_CLIENT_ID: "",
      GOOGLE_ADS_DEVELOPER_TOKEN: "dev",
      GOOGLE_ADS_CLIENT_SECRET: "secret",
      GOOGLE_ADS_REFRESH_TOKEN: "refresh",
      GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET: "oauth-secret"
    },
    "oauth_proxy"
  );
  assert.deepEqual(missing, []);
});
