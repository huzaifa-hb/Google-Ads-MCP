#!/usr/bin/env node
import { parseArgs, flagBool, flagString } from "./args.js";
import { deployCloudRun, syncSecrets } from "./cloud.js";
import { renderClientConfig, writeClaudeDesktopConfig } from "./config.js";
import { runDoctor } from "./doctor.js";
import { packageRoot } from "./package-root.js";
import { loadProfile } from "./profiles.js";
import { runRelay } from "./relay.js";
import { runSetup } from "./setup.js";
import { runSmoke } from "./smoke.js";
import { runStart } from "./start.js";
import path from "node:path";

const WORK_DIR = process.cwd();
const PACKAGE_ROOT = packageRoot();

function help(): void {
  console.log(`Google Ads MCP wrapper

Usage:
  google-ads-mcp setup [--env-file .env]
  google-ads-mcp doctor [--env-file .env] [--url http://localhost:8080/mcp]
  google-ads-mcp start [--profile local-direct] [--mode safe_read_only]
  google-ads-mcp relay --url <mcp-url> [--token-env MCP_BEARER_TOKEN] [--env-file .env]
  google-ads-mcp config --client codex|claude-desktop|generic --transport remote|stdio
  google-ads-mcp smoke [--profile local-direct]
  google-ads-mcp cloud sync-secrets --project <id> [--auth-mode bearer|oauth_proxy]
  google-ads-mcp cloud deploy --project <id> [--auth-mode bearer|oauth_proxy]
`);
}

async function main(): Promise<void> {
  const parsed = parseArgs(process.argv.slice(2));
  const envFile = flagString(parsed.flags, "env-file", ".env") || ".env";

  if (parsed.command === "help" || flagBool(parsed.flags, "help")) {
    help();
    return;
  }

  if (parsed.command === "setup") {
    await runSetup(WORK_DIR, PACKAGE_ROOT, { envFile });
    return;
  }

  if (parsed.command === "doctor") {
    const code = await runDoctor(WORK_DIR, {
      envFile,
      url: flagString(parsed.flags, "url")
    });
    process.exitCode = code;
    return;
  }

  if (parsed.command === "start") {
    await runStart(WORK_DIR, {
      envFile,
      profile: flagString(parsed.flags, "profile", "local-direct") || "local-direct",
      mode: flagString(parsed.flags, "mode", "safe_read_only") || "safe_read_only",
      port: flagString(parsed.flags, "port")
    });
    return;
  }

  if (parsed.command === "relay") {
    await runRelay({
      url: flagString(parsed.flags, "url") || process.env.MCP_URL || "",
      tokenEnv: flagString(parsed.flags, "token-env", "MCP_BEARER_TOKEN") || "MCP_BEARER_TOKEN",
      envFile
    });
    return;
  }

  if (parsed.command === "config") {
    const profile = await loadProfile(WORK_DIR, {
      profile: flagString(parsed.flags, "profile", "remote-cloud-run") || "remote-cloud-run",
      envFile,
      url: flagString(parsed.flags, "url"),
      tokenEnv: flagString(parsed.flags, "token-env", "MCP_BEARER_TOKEN") || "MCP_BEARER_TOKEN"
    });
    const config = renderClientConfig({
      client: (flagString(parsed.flags, "client", "generic") || "generic") as never,
      transport: (flagString(parsed.flags, "transport", "stdio") || "stdio") as never,
      url: profile.url,
      tokenEnv: profile.tokenEnv,
      envFile: path.resolve(WORK_DIR, envFile)
    });
    if (flagBool(parsed.flags, "write")) {
      if (flagString(parsed.flags, "client") !== "claude-desktop") {
        throw new Error("--write is currently supported only for --client claude-desktop.");
      }
      await writeClaudeDesktopConfig(config, { yes: flagBool(parsed.flags, "yes") });
      console.log("Updated Claude Desktop MCP config.");
    } else {
      process.stdout.write(config);
    }
    return;
  }

  if (parsed.command === "smoke") {
    const profile = await loadProfile(WORK_DIR, {
      profile: flagString(parsed.flags, "profile", "local-direct") || "local-direct",
      envFile,
      url: flagString(parsed.flags, "url"),
      tokenEnv: flagString(parsed.flags, "token-env", "MCP_BEARER_TOKEN") || "MCP_BEARER_TOKEN"
    });
    await runSmoke(profile);
    return;
  }

  if (parsed.command === "cloud" && parsed.subcommand === "sync-secrets") {
    await syncSecrets(
      WORK_DIR,
      flagString(parsed.flags, "project") || "",
      envFile,
      flagString(parsed.flags, "auth-mode", "bearer") || "bearer",
      flagString(parsed.flags, "google-ads-auth-mode", "shared_refresh_token") ||
        "shared_refresh_token"
    );
    return;
  }

  if (parsed.command === "cloud" && parsed.subcommand === "deploy") {
    await deployCloudRun(PACKAGE_ROOT, {
      projectId: flagString(parsed.flags, "project") || "",
      region: flagString(parsed.flags, "region", "us-central1"),
      mode: flagString(parsed.flags, "mode", "safe_read_only"),
      authMode: flagString(parsed.flags, "auth-mode", "bearer"),
      googleAdsAuthMode:
        flagString(parsed.flags, "google-ads-auth-mode", "shared_refresh_token") ||
        "shared_refresh_token",
      mcpBaseUrl: flagString(parsed.flags, "base-url") || flagString(parsed.flags, "mcp-base-url"),
      googleAdsClientId: flagString(parsed.flags, "google-ads-client-id"),
      googleAdsLoginCustomerId: flagString(parsed.flags, "google-ads-login-customer-id"),
      mcpOAuthClientId: flagString(parsed.flags, "mcp-oauth-client-id"),
      mcpAllowedEmails: flagString(parsed.flags, "allowed-emails"),
      mcpAllowedDomains: flagString(parsed.flags, "allowed-domains"),
      mcpTokenStorage: flagString(parsed.flags, "token-storage"),
      mcpFirestoreDatabase: flagString(parsed.flags, "firestore-database"),
      minInstances: flagString(parsed.flags, "min-instances"),
      maxInstances: flagString(parsed.flags, "max-instances"),
      memory: flagString(parsed.flags, "memory"),
      cpu: flagString(parsed.flags, "cpu")
    });
    return;
  }

  help();
  process.exitCode = 2;
}

main().catch((error) => {
  console.error(error instanceof Error ? error.message : String(error));
  process.exitCode = 1;
});
