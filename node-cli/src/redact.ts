const SECRET_NAME_RE = /(secret|token|refresh|password|developer|client_secret|authorization|api_key|gclid|gbraid|wbraid)/i;

export function isSensitiveName(name: string): boolean {
  return SECRET_NAME_RE.test(name);
}

export function redactValue(name: string, value: string | undefined): string {
  if (!value) {
    return "";
  }
  return isSensitiveName(name) ? "[REDACTED]" : value;
}

export function redactText(text: string): string {
  return text
    .replace(/Bearer\s+[A-Za-z0-9._~+/=-]+/gi, "Bearer [REDACTED]")
    .replace(/(gptToken=)[^&\s]+/gi, "$1[REDACTED]")
    .replace(/(refresh_token["'=:\s]+)[^"',\s]+/gi, "$1[REDACTED]")
    .replace(/(client_secret["'=:\s]+)[^"',\s]+/gi, "$1[REDACTED]")
    .replace(/(developer_token["'=:\s]+)[^"',\s]+/gi, "$1[REDACTED]")
    .replace(/(MCP_BEARER_TOKEN["'=:\s]+)[^"',\s]+/g, "$1[REDACTED]");
}
