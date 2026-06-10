import path from "node:path";
import { readEnvFile } from "./env.js";

export type ConnectionProfile = {
  name: "local-direct" | "remote-cloud-run";
  url: string;
  tokenEnv: string;
  token?: string;
};

export async function loadProfile(rootDir: string, options: {
  profile: string;
  envFile?: string;
  url?: string;
  tokenEnv?: string;
}): Promise<ConnectionProfile> {
  if (options.profile === "brokered-readonly") {
    throw new Error("brokered-readonly is reserved for a future hosted backend and is not implemented.");
  }
  if (options.profile !== "local-direct" && options.profile !== "remote-cloud-run") {
    throw new Error(`Unknown profile '${options.profile}'.`);
  }
  const tokenEnv = options.tokenEnv || "MCP_BEARER_TOKEN";
  const env = await readEnvFile(path.resolve(rootDir, options.envFile || ".env"));
  const token = process.env[tokenEnv] || env[tokenEnv];

  if (options.profile === "local-direct") {
    return {
      name: "local-direct",
      url:
        options.url ||
        process.env.MCP_URL ||
        env.MCP_URL ||
        `http://localhost:${process.env.PORT || env.PORT || "8080"}/mcp`,
      tokenEnv,
      token
    };
  }

  const url = options.url || process.env.MCP_URL || env.MCP_URL;
  if (!url) {
    throw new Error("remote-cloud-run requires --url or MCP_URL.");
  }
  return {
    name: "remote-cloud-run",
    url,
    tokenEnv,
    token
  };
}
