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
  assertJsonRpcOk("initialize", initialize.json);
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
  const customerTool = registeredNameForCanonical(catalog, "list_accessible_customers");
  const customers = await callTool(profile.url, profile.token, sessionId, 4, customerTool);
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
  assertJsonRpcOk(name, result.json);
  return toolPayloadFromResponse(result.json);
}

export function assertJsonRpcOk(name: string, response: unknown): void {
  if (!isRecord(response)) {
    throw new Error(`${name} returned a non-object JSON-RPC response.`);
  }
  if ("error" in response && response.error) {
    throw new Error(`${name} returned JSON-RPC error: ${summaryText(response.error)}`);
  }
  const result = response.result;
  if (isRecord(result) && result.isError === true) {
    throw new Error(`${name} returned MCP tool error: ${summaryText(result)}`);
  }
  const payload = toolPayloadFromResponse(response);
  if (containsOkFalse(payload)) {
    throw new Error(`${name} returned tool-level failure: ${summaryText(payload)}`);
  }
}

export function toolPayloadFromResponse(response: unknown): unknown {
  if (!isRecord(response) || !("result" in response)) {
    return response;
  }
  const result = response.result;
  if (!isRecord(result)) {
    return result;
  }
  if (isRecord(result.structuredContent)) {
    return result.structuredContent;
  }
  if (Array.isArray(result.content)) {
    const textItem = result.content.find(
      (item): item is { text: string } => isRecord(item) && typeof item.text === "string"
    );
    if (textItem) {
      const parsed = parseJsonObject(textItem.text);
      return parsed ?? textItem.text;
    }
  }
  return result;
}

export function registeredNameForCanonical(catalog: unknown, canonicalName: string): string {
  if (!isRecord(catalog) || !Array.isArray(catalog.tools)) {
    throw new Error("Tool catalog response did not include a tools array.");
  }
  const match = catalog.tools.find(
    (tool) => isRecord(tool) && tool.canonical_name === canonicalName
  );
  if (!isRecord(match)) {
    throw new Error(`Tool catalog did not expose canonical tool '${canonicalName}'.`);
  }
  const registeredName = match.registered_name || match.name;
  if (typeof registeredName !== "string" || !registeredName) {
    throw new Error(`Catalog entry for '${canonicalName}' did not include a registered name.`);
  }
  return registeredName;
}

function containsOkFalse(value: unknown): boolean {
  if (isRecord(value)) {
    if (value.ok === false) {
      return true;
    }
    return Object.values(value).some(containsOkFalse);
  }
  if (Array.isArray(value)) {
    return value.some(containsOkFalse);
  }
  if (typeof value === "string") {
    const parsed = parseJsonObject(value);
    return parsed ? containsOkFalse(parsed) : false;
  }
  return false;
}

function parseJsonObject(text: string): unknown | undefined {
  const trimmed = text.trim();
  if (!trimmed.startsWith("{") && !trimmed.startsWith("[")) {
    return undefined;
  }
  try {
    return JSON.parse(trimmed);
  } catch {
    return undefined;
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function summaryText(value: unknown): string {
  const text = JSON.stringify(value);
  if (!text) {
    return "ok";
  }
  return text.length > 240 ? `${text.slice(0, 240)}...` : text;
}
