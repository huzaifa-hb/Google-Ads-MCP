import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { readEnvFile, valueLooksMissing } from "./env.js";
import { runCommand } from "./runner.js";

const REQUIRED_SECRETS = [
  "MCP_BEARER_TOKEN",
  "GOOGLE_ADS_DEVELOPER_TOKEN",
  "GOOGLE_ADS_CLIENT_ID",
  "GOOGLE_ADS_CLIENT_SECRET",
  "GOOGLE_ADS_REFRESH_TOKEN"
];

export type GcloudCommand = {
  command: string;
  args: string[];
};

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

export function missingRequiredSecrets(env: Record<string, string | undefined>): string[] {
  return REQUIRED_SECRETS.filter((name) => valueLooksMissing(env[name]));
}

export async function syncSecrets(rootDir: string, projectId: string, envFile = ".env"): Promise<void> {
  if (!projectId) {
    throw new Error("--project is required.");
  }
  const env = await readEnvFile(path.resolve(rootDir, envFile));
  const missing = missingRequiredSecrets(env);
  if (missing.length > 0) {
    throw new Error(`Missing or placeholder .env values: ${missing.join(", ")}`);
  }

  const tempDir = await mkdtemp(path.join(tmpdir(), "google-ads-mcp-secrets-"));
  try {
    for (const name of REQUIRED_SECRETS) {
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

export function buildDeployCommand(rootDir: string, options: {
  projectId: string;
  region: string;
  mode: string;
  authMode: string;
  mcpBaseUrl?: string;
}): GcloudCommand {
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
  return { command: shell, args };
}

export async function deployCloudRun(rootDir: string, options: {
  projectId: string;
  region?: string;
  mode?: string;
  authMode?: string;
  mcpBaseUrl?: string;
}): Promise<void> {
  if (!options.projectId) {
    throw new Error("--project is required.");
  }
  if (options.authMode === "oauth_proxy" && !options.mcpBaseUrl) {
    throw new Error("--base-url is required with --auth-mode oauth_proxy.");
  }
  const command = buildDeployCommand(rootDir, {
    projectId: options.projectId,
    region: options.region || "us-central1",
    mode: options.mode || "safe_read_only",
    authMode: options.authMode || "bearer",
    mcpBaseUrl: options.mcpBaseUrl
  });
  const result = await runCommand(command.command, command.args, { cwd: rootDir, stdio: "inherit" });
  if (result.code !== 0) {
    throw new Error("Cloud Run deployment failed.");
  }
}
