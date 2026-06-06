import path from "node:path";
import { readEnvFile, requiredGoogleAdsEnv, valueLooksMissing } from "./env.js";
import { healthUrlForMcpUrl, requestText } from "./http.js";
import { pythonVersion, venvPythonPath } from "./python.js";
import { runCommand } from "./runner.js";

type Check = {
  name: string;
  ok: boolean;
  detail: string;
  critical?: boolean;
};

function printCheck(check: Check): void {
  const status = check.ok ? "ok" : check.critical ? "fail" : "warn";
  console.log(`[${status}] ${check.name}: ${check.detail}`);
}

export async function runDoctor(rootDir: string, options: {
  envFile?: string;
  url?: string;
} = {}): Promise<number> {
  const checks: Check[] = [];
  checks.push({
    name: "Node.js",
    ok: Number(process.versions.node.split(".")[0]) >= 20,
    detail: process.version,
    critical: true
  });

  const python = await pythonVersion();
  checks.push({
    name: "Python",
    ok: python.ok,
    detail: python.detail,
    critical: true
  });

  const envPath = path.resolve(rootDir, options.envFile || ".env");
  const env = await readEnvFile(envPath);
  checks.push({
    name: ".env",
    ok: Object.keys(env).length > 0,
    detail: Object.keys(env).length > 0 ? envPath : "not found or empty",
    critical: true
  });

  const missing = requiredGoogleAdsEnv().filter((name) => valueLooksMissing(env[name]));
  checks.push({
    name: "Google Ads credentials",
    ok: missing.length === 0,
    detail: missing.length === 0 ? "required values present" : `missing or placeholder: ${missing.join(", ")}`,
    critical: true
  });

  checks.push({
    name: "MCP bearer token",
    ok: !valueLooksMissing(env.MCP_BEARER_TOKEN),
    detail: valueLooksMissing(env.MCP_BEARER_TOKEN) ? "missing or placeholder" : "present",
    critical: true
  });

  const venv = venvPythonPath(rootDir);
  checks.push({
    name: "Python venv",
    ok: Boolean(venv),
    detail: venv || "not found"
  });

  const gcloud = await runCommand("gcloud", ["--version"]);
  checks.push({
    name: "gcloud",
    ok: gcloud.code === 0,
    detail: gcloud.code === 0 ? "available" : "not available"
  });

  const url = options.url || `http://localhost:${env.PORT || "8080"}/mcp`;
  const health = await requestText(healthUrlForMcpUrl(url), undefined, 3000);
  checks.push({
    name: "local healthz",
    ok: health.ok,
    detail: health.ok ? "server responded" : "server not running or unreachable"
  });

  for (const check of checks) {
    printCheck(check);
  }
  return checks.some((check) => check.critical && !check.ok) ? 1 : 0;
}
