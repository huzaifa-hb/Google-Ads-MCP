import { ConnectionProfile } from "./profiles.js";
import { mcpPost } from "./http.js";

export async function runSmoke(profile: ConnectionProfile): Promise<void> {
  if (!profile.token) {
    throw new Error(`${profile.tokenEnv} is required for smoke checks.`);
  }
  let sessionId: string | undefined;
  const initialize = await mcpPost({
    url: profile.url,
    token: profile.token,
    payload: {
      jsonrpc: "2.0",
      id: 1,
      method: "initialize",
      params: {
        protocolVersion: "2025-03-26",
        capabilities: {},
        clientInfo: {
          name: "google-ads-mcp-cli",
          version: "0.1.0"
        }
      }
    }
  });
  if (!initialize.ok) {
    throw new Error(`MCP initialize failed: ${initialize.text}`);
  }
  sessionId = initialize.sessionId;
  await mcpPost({
    url: profile.url,
    token: profile.token,
    sessionId,
    payload: {
      jsonrpc: "2.0",
      method: "notifications/initialized"
    }
  });

  const status = await callTool(profile.url, profile.token, sessionId, 2, "get_server_status");
  const catalog = await callTool(profile.url, profile.token, sessionId, 3, "get_tool_catalog");
  const customers = await callTool(profile.url, profile.token, sessionId, 4, "list_accessible_customers");
  console.log("Smoke check passed.");
  console.log(`Server status: ${summaryText(status)}`);
  console.log(`Tool catalog: ${summaryText(catalog)}`);
  console.log(`Accessible customers: ${summaryText(customers)}`);
}

async function callTool(
  url: string,
  token: string,
  sessionId: string | undefined,
  id: number,
  name: string
): Promise<unknown> {
  const result = await mcpPost({
    url,
    token,
    sessionId,
    payload: {
      jsonrpc: "2.0",
      id,
      method: "tools/call",
      params: {
        name,
        arguments: {}
      }
    }
  });
  if (!result.ok) {
    throw new Error(`${name} failed: ${result.text}`);
  }
  return result.json;
}

function summaryText(value: unknown): string {
  const text = JSON.stringify(value);
  if (!text) {
    return "ok";
  }
  return text.length > 240 ? `${text.slice(0, 240)}...` : text;
}
