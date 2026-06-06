import { existsSync } from "node:fs";
import { readFile, writeFile } from "node:fs/promises";

export type EnvMap = Record<string, string>;

const PLACEHOLDER_PREFIXES = ["replace-with", "YOUR_", "YOUR-", "set-in-"];

export function parseEnv(content: string): EnvMap {
  const values: EnvMap = {};
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) {
      continue;
    }
    const [rawKey, ...rest] = trimmed.split("=");
    const key = rawKey?.trim();
    if (!key) {
      continue;
    }
    values[key] = unquote(rest.join("=").trim());
  }
  return values;
}

function unquote(value: string): string {
  if (
    (value.startsWith('"') && value.endsWith('"')) ||
    (value.startsWith("'") && value.endsWith("'"))
  ) {
    return value.slice(1, -1);
  }
  return value;
}

export async function readEnvFile(path: string): Promise<EnvMap> {
  if (!existsSync(path)) {
    return {};
  }
  return parseEnv(await readFile(path, "utf8"));
}

export async function writeEnvUpdates(path: string, updates: EnvMap): Promise<void> {
  const existing = existsSync(path) ? await readFile(path, "utf8") : "";
  const seen = new Set<string>();
  const output: string[] = [];

  for (const line of existing.split(/\r?\n/)) {
    if (!line) {
      output.push(line);
      continue;
    }
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#") || !trimmed.includes("=")) {
      output.push(line);
      continue;
    }
    const key = trimmed.split("=", 1)[0]?.trim();
    if (key && Object.prototype.hasOwnProperty.call(updates, key)) {
      output.push(`${key}=${updates[key] ?? ""}`);
      seen.add(key);
    } else {
      output.push(line);
    }
  }

  if (output.length > 0 && output[output.length - 1]?.trim()) {
    output.push("");
  }
  for (const [key, value] of Object.entries(updates)) {
    if (!seen.has(key)) {
      output.push(`${key}=${value}`);
    }
  }
  await writeFile(path, `${output.join("\n").replace(/\n+$/, "")}\n`, "utf8");
}

export function loadEnvIntoProcess(values: EnvMap): void {
  for (const [key, value] of Object.entries(values)) {
    if (process.env[key] === undefined) {
      process.env[key] = value;
    }
  }
}

export function valueLooksMissing(value: string | undefined): boolean {
  if (!value || !value.trim()) {
    return true;
  }
  const normalized = value.trim();
  return PLACEHOLDER_PREFIXES.some((prefix) => normalized.startsWith(prefix));
}

export function requiredGoogleAdsEnv(): string[] {
  return [
    "GOOGLE_ADS_DEVELOPER_TOKEN",
    "GOOGLE_ADS_CLIENT_ID",
    "GOOGLE_ADS_CLIENT_SECRET",
    "GOOGLE_ADS_REFRESH_TOKEN"
  ];
}
