import { spawn } from "node:child_process";
import path from "node:path";
import { readEnvFile } from "./env.js";
import { healthUrlForMcpUrl, requestText } from "./http.js";
import { resolvePythonCommand, venvPythonPath } from "./python.js";

export async function runStart(rootDir: string, options: {
  envFile: string;
  profile: string;
  mode: string;
  port?: string;
}): Promise<void> {
  if (options.profile !== "local-direct") {
    throw new Error("start currently launches only the local-direct Python server.");
  }
  if (options.mode === "write_enabled") {
    console.log("Starting in write_enabled mode. Real writes still require the Python confirmation phrase.");
  }
  const envPath = path.resolve(rootDir, options.envFile);
  const envFileValues = await readEnvFile(envPath);
  const port = options.port || process.env.PORT || envFileValues.PORT || "8080";
  const env = {
    ...envFileValues,
    ...process.env,
    GOOGLE_ADS_MCP_MODE: options.mode || "safe_read_only",
    PORT: port
  };
  const venvPython = venvPythonPath(rootDir);
  const python = venvPython
    ? { command: venvPython, args: [] }
    : await resolvePythonCommand();
  if (!python) {
    throw new Error("Python 3.12+ was not found via PYTHON, python, python3, or py.");
  }
  const mcpUrl = `http://localhost:${env.PORT}/mcp`;
  console.log(`Starting Google Ads MCP at ${mcpUrl}`);
  const child = spawn(python.command, [...python.args, "-m", "google_ads_mcp"], {
    cwd: rootDir,
    env,
    stdio: "inherit",
    shell: false
  });
  const childDone = new Promise<void>((resolve, reject) => {
    child.once("error", reject);
    child.once("close", (code) => {
      if (code && code !== 0) {
        reject(new Error(`Python server exited with code ${code}.`));
      } else {
        resolve();
      }
    });
  });

  await Promise.race([
    waitForHealth(mcpUrl),
    childDone.then(() => {
      throw new Error("Python server exited before the health check passed.");
    })
  ]);
  await childDone;
}

async function waitForHealth(mcpUrl: string): Promise<void> {
  const healthUrl = healthUrlForMcpUrl(mcpUrl);
  for (let attempt = 0; attempt < 20; attempt += 1) {
    const result = await requestText(healthUrl, undefined, 1000);
    if (result.ok) {
      console.log("Health check passed.");
      return;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  console.log("Health check did not respond yet. The server process is still attached.");
}
