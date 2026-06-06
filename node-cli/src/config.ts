import { mkdir, readFile, writeFile } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { confirm } from "./prompt.js";

export type ClientName = "codex" | "claude-desktop" | "generic";
export type TransportName = "remote" | "stdio";

export function renderClientConfig(options: {
  client: ClientName;
  transport: TransportName;
  url: string;
  tokenEnv: string;
  envFile?: string;
  packageName?: string;
}): string {
  const packageName = options.packageName || "@huzaifa-hb/google-ads-mcp";
  const relayArgs = [
    "-y",
    packageName,
    "relay",
    "--url",
    options.url,
    "--token-env",
    options.tokenEnv,
    "--env-file",
    options.envFile || ".env"
  ];
  if (options.client === "codex") {
    if (options.transport === "remote") {
      return [
        "[mcp_servers.google-ads-mcp]",
        `url = "${options.url}"`,
        `bearer_token_env_var = "${options.tokenEnv}"`,
        ""
      ].join("\n");
    }
    return [
      "[mcp_servers.google-ads-mcp]",
      'command = "npx"',
      `args = ${JSON.stringify(relayArgs)}`,
      ""
    ].join("\n");
  }

  const server =
    options.transport === "remote"
      ? {
          httpUrl: options.url,
          headers: {
            Authorization: `Bearer \${${options.tokenEnv}}`
          }
        }
      : {
          command: "npx",
          args: relayArgs
        };

  const wrapper = {
    mcpServers: {
      "google-ads-mcp": server
    }
  };
  return `${JSON.stringify(wrapper, null, 2)}\n`;
}

export function claudeDesktopConfigPath(platform = process.platform, home = os.homedir()): string {
  if (platform === "win32") {
    const appData = process.env.APPDATA || path.join(home, "AppData", "Roaming");
    return path.join(appData, "Claude", "claude_desktop_config.json");
  }
  if (platform === "darwin") {
    return path.join(home, "Library", "Application Support", "Claude", "claude_desktop_config.json");
  }
  return path.join(home, ".config", "Claude", "claude_desktop_config.json");
}

export async function writeClaudeDesktopConfig(configText: string, options: {
  yes?: boolean;
  configPath?: string;
} = {}): Promise<void> {
  const target = options.configPath || claudeDesktopConfigPath();
  if (!options.yes) {
    const allowed = await confirm(`Write MCP config to ${target}?`);
    if (!allowed) {
      throw new Error("Config write cancelled.");
    }
  }
  await mkdir(path.dirname(target), { recursive: true });
  let existing: Record<string, unknown> = {};
  try {
    existing = JSON.parse(await readFile(target, "utf8")) as Record<string, unknown>;
  } catch {
    existing = {};
  }
  const update = JSON.parse(configText) as { mcpServers: Record<string, unknown> };
  const currentServers =
    typeof existing.mcpServers === "object" && existing.mcpServers !== null
      ? (existing.mcpServers as Record<string, unknown>)
      : {};
  existing.mcpServers = {
    ...currentServers,
    ...update.mcpServers
  };
  await writeFile(target, `${JSON.stringify(existing, null, 2)}\n`, "utf8");
}
