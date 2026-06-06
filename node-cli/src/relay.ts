import readline from "node:readline";
import path from "node:path";
import { loadEnvIntoProcess, readEnvFile } from "./env.js";
import { mcpPost } from "./http.js";

export function jsonRpcError(code: number, message: string, id: unknown = null): string {
  return JSON.stringify({
    jsonrpc: "2.0",
    id,
    error: {
      code,
      message
    }
  });
}

export async function relayLine(options: {
  line: string;
  url: string;
  token: string;
  sessionId?: string;
}): Promise<{ output?: string; sessionId?: string }> {
  let payload: unknown;
  let id: unknown = null;
  try {
    payload = JSON.parse(options.line);
    if (payload && typeof payload === "object" && "id" in payload) {
      id = (payload as { id?: unknown }).id ?? null;
    }
  } catch (error) {
    return {
      output: jsonRpcError(-32700, error instanceof Error ? error.message : String(error), id),
      sessionId: options.sessionId
    };
  }

  try {
    const response = await mcpPost({
      url: options.url,
      token: options.token,
      payload,
      sessionId: options.sessionId
    });
    if (!response.ok) {
      return {
        output: jsonRpcError(response.status, response.text, id),
        sessionId: response.sessionId
      };
    }
    return {
      output: response.text || undefined,
      sessionId: response.sessionId
    };
  } catch (error) {
    return {
      output: jsonRpcError(-32000, error instanceof Error ? error.message : String(error), id),
      sessionId: options.sessionId
    };
  }
}

export async function runRelay(options: {
  url: string;
  tokenEnv: string;
  envFile?: string;
}): Promise<void> {
  if (!options.url) {
    throw new Error("MCP URL is required. Pass --url or set MCP_URL.");
  }
  if (options.envFile) {
    loadEnvIntoProcess(await readEnvFile(path.resolve(process.cwd(), options.envFile)));
  }
  const token = process.env[options.tokenEnv];
  if (!token) {
    throw new Error(`${options.tokenEnv} is required in the environment or ${options.envFile || ".env"}.`);
  }

  let sessionId: string | undefined;
  const rl = readline.createInterface({ input: process.stdin });
  for await (const line of rl) {
    if (!line.trim()) {
      continue;
    }
    const result = await relayLine({
      line,
      url: options.url,
      token,
      sessionId
    });
    sessionId = result.sessionId;
    if (result.output) {
      process.stdout.write(`${result.output}\n`);
    }
  }
}
