import { redactText } from "./redact.js";

export type McpHttpResult = {
  status: number;
  ok: boolean;
  sessionId?: string;
  text: string;
  json?: unknown;
};

export function extractJsonResponse(body: string, contentType: string): string {
  if (!contentType.includes("text/event-stream")) {
    return body;
  }
  for (const line of body.split(/\r?\n/)) {
    if (line.startsWith("data: ")) {
      return line.slice("data: ".length);
    }
  }
  return body;
}

export async function mcpPost(options: {
  url: string;
  token?: string;
  payload: unknown;
  sessionId?: string;
  timeoutMs?: number;
}): Promise<McpHttpResult> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), options.timeoutMs || 300000);
  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      Accept: "application/json, text/event-stream"
    };
    if (options.token) {
      headers.Authorization = `Bearer ${options.token}`;
    }
    if (options.sessionId) {
      headers["mcp-session-id"] = options.sessionId;
    }
    const response = await fetch(options.url, {
      method: "POST",
      headers,
      body: JSON.stringify(options.payload),
      signal: controller.signal
    });
    const raw = await response.text();
    const text = extractJsonResponse(raw, response.headers.get("content-type") || "");
    let json: unknown;
    if (text.trim()) {
      try {
        json = JSON.parse(text);
      } catch {
        json = undefined;
      }
    }
    return {
      status: response.status,
      ok: response.ok,
      sessionId: response.headers.get("mcp-session-id") || options.sessionId,
      text: redactText(text),
      json
    };
  } finally {
    clearTimeout(timer);
  }
}

export async function requestText(
  url: string,
  token?: string,
  timeoutMs = 3000
): Promise<{ ok: boolean; status?: number; text: string }> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const headers: Record<string, string> = {};
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
    const response = await fetch(url, { headers, signal: controller.signal });
    return {
      ok: response.ok,
      status: response.status,
      text: redactText(await response.text())
    };
  } catch (error) {
    return { ok: false, text: error instanceof Error ? error.message : String(error) };
  } finally {
    clearTimeout(timer);
  }
}

export function healthUrlForMcpUrl(mcpUrl: string): string {
  const url = new URL(mcpUrl);
  url.pathname = "/healthz";
  url.search = "";
  return url.toString();
}
