import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { readEnvFile, valueLooksMissing } from "./env.js";
import { runCommand } from "./runner.js";

const BEARER_REQUIRED_SECRETS = [
  "MCP_BEARER_TOKEN",
  "GOOGLE_ADS_DEVELOPER_TOKEN",
  "GOOGLE_ADS_CLIENT_ID",
  "GOOGLE_ADS_CLIENT_SECRET",
  "GOOGLE_ADS_REFRESH_TOKEN"
];

const OAUTH_PROXY_REQUIRED_SECRETS = [
  "GOOGLE_ADS_DEVELOPER_TOKEN",
  "GOOGLE_ADS_CLIENT_SECRET",
  "GOOGLE_ADS_REFRESH_TOKEN",
  "GOOGLE_ADS_MCP_OAUTH_CLIENT_SECRET"
];

export type GcloudCommand = {
  command: string;
  args: string[];
};

export type AuthMode = "bearer" | "oauth_proxy";

export type DeployOptions = {
  projectId: string;
  region: string;
  mode: string;
  authMode: string;
  mcpBaseUrl?: string;
  googleAdsClientId?: string;
  googleAdsLoginCustomerId?: string;
  mcpOAuthClientId?: string;
  mcpAllowedDomains?: string;
  minInstances?: string;
  maxInstances?: string;
  memory?: string;
  cpu?: string;
};

export function requiredSecretsForAuthMode(authMode = "bearer"): string[] {
  if (authMode === "oauth_proxy") {
    return [...OAUTH_PROXY_REQUIRED_SECRETS];
  }
  if (authMode === "bearer") {
    return [...BEARER_REQUIRED_SECRETS];
  }
  throw new Error("--auth-mode must be bearer or oauth_proxy.");
}

export function buildSecretVersionCommand(
  name: string,
  projectId: string,
  dataFile: string,
  exists: boolean
): GcloudCommand {
  if (exists) {
    return {
      command: "gcloud",
      args: ["secrets", "versions", "add", name, `--data-file=${dataFile}`, `--project=${projectId}`]
    };
  }
  return {
    command: "gcloud",
    args: ["secrets", "create", name, `--data-file=${dataFile}`, `--project=${projectId}`]
  };
}

export function missingRequiredSecrets(
  env: Record<string, string | undefined>,
  authMode = "bearer"
): string[] {
  return requiredSecretsForAuthMode(authMode).filter((name) => valueLooksMissing(env[name]));
}

export async function syncSecrets(
  rootDir: string,
  projectId: string,
  envFile = ".env",
  authMode = "bearer"
): Promise<void> {
  if (!projectId) {
    throw new Error("--project is required.");
  }
  const env = await readEnvFile(path.resolve(rootDir, envFile));
  const requiredSecrets = requiredSecretsForAuthMode(authMode);
  const missing = missingRequiredSecrets(env, authMode);
  if (missing.length > 0) {
    throw new Error(`Missing or placeholder .env values: ${missing.join(", ")}`);
  }

  const tempDir = await mkdtemp(path.join(tmpdir(), "google-ads-mcp-secrets-"));
  try {
    for (const name of requiredSecrets) {
      const value = env[name];
      if (!value) {
        continue;
      }
      const dataFile = path.join(tempDir, name);
      await writeFile(dataFile, value, { encoding: "utf8", mode: 0o600 });
      const describe = await runCommand("gcloud", [
        "secrets",
        "describe",
        name,
        `--project=${projectId}`
      ]);
      const command = buildSecretVersionCommand(name, projectId, dataFile, describe.code === 0);
      const result = await runCommand(command.command, command.args);
      if (result.code !== 0) {
        throw new Error(`Failed to sync ${name}.`);
      }
      console.log(`Synced ${name}.`);
    }
  } finally {
    await rm(tempDir, { recursive: true, force: true });
  }
}

export function buildDeployCommand(rootDir: string, options: DeployOptions): GcloudCommand {
  const scriptPath = path.join(rootDir, "deploy", "cloud-run.ps1");
  const shell = process.platform === "win32" ? "powershell.exe" : "pwsh";
  const args = [
    "-NoProfile",
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    scriptPath,
    "-ProjectId",
    options.projectId,
    "-Region",
    options.region,
    "-McpMode",
    options.mode,
    "-McpAuthMode",
    options.authMode
  ];
  if (options.mcpBaseUrl) {
    args.push("-McpBaseUrl", options.mcpBaseUrl);
  }
  if (options.googleAdsClientId) {
    args.push("-GoogleAdsClientId", options.googleAdsClientId);
  }
  if (options.googleAdsLoginCustomerId) {
    args.push("-GoogleAdsLoginCustomerId", options.googleAdsLoginCustomerId);
  }
  if (options.mcpOAuthClientId) {
    args.push("-McpOAuthClientId", options.mcpOAuthClientId);
  }
  if (options.mcpAllowedDomains) {
    args.push("-McpAllowedDomains", options.mcpAllowedDomains);
  }
  if (options.minInstances) {
    args.push("-MinInstances", options.minInstances);
  }
  if (options.maxInstances) {
    args.push("-MaxInstances", options.maxInstances);
  }
  if (options.memory) {
    args.push("-Memory", options.memory);
  }
  if (options.cpu) {
    args.push("-Cpu", options.cpu);
  }
  return { command: shell, args };
}

export async function deployCloudRun(rootDir: string, options: {
  projectId: string;
  region?: string;
  mode?: string;
  authMode?: string;
  mcpBaseUrl?: string;
  googleAdsClientId?: string;
  googleAdsLoginCustomerId?: string;
  mcpOAuthClientId?: string;
  mcpAllowedDomains?: string;
  minInstances?: string;
  maxInstances?: string;
  memory?: string;
  cpu?: string;
}): Promise<void> {
  if (!options.projectId) {
    throw new Error("--project is required.");
  }
  const authMode = options.authMode || "bearer";
  if (authMode === "oauth_proxy") {
    if (!options.mcpBaseUrl) {
      throw new Error("--base-url is required with --auth-mode oauth_proxy.");
    }
    if (!options.googleAdsClientId) {
      throw new Error("--google-ads-client-id is required with --auth-mode oauth_proxy.");
    }
    if (!options.mcpOAuthClientId) {
      throw new Error("--mcp-oauth-client-id is required with --auth-mode oauth_proxy.");
    }
    if (!options.mcpAllowedDomains) {
      throw new Error("--allowed-domains is required with --auth-mode oauth_proxy.");
    }
  }
  const command = buildDeployCommand(rootDir, {
    projectId: options.projectId,
    region: options.region || "us-central1",
    mode: options.mode || "safe_read_only",
    authMode,
    mcpBaseUrl: options.mcpBaseUrl,
    googleAdsClientId: options.googleAdsClientId,
    googleAdsLoginCustomerId: options.googleAdsLoginCustomerId,
    mcpOAuthClientId: options.mcpOAuthClientId,
    mcpAllowedDomains: options.mcpAllowedDomains,
    minInstances: options.minInstances,
    maxInstances: options.maxInstances,
    memory: options.memory,
    cpu: options.cpu
  });
  const result = await runCommand(command.command, command.args, { cwd: rootDir, stdio: "inherit" });
  if (result.code !== 0) {
    throw new Error("Cloud Run deployment failed.");
  }
}
