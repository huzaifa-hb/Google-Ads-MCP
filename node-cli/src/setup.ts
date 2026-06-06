import { existsSync } from "node:fs";
import { copyFile } from "node:fs/promises";
import path from "node:path";
import { randomBytes } from "node:crypto";
import { readEnvFile, valueLooksMissing, writeEnvUpdates } from "./env.js";
import { runDoctor } from "./doctor.js";
import { ensureVenv, installPythonPackage, runPythonAuthHelper } from "./python.js";

export function generateBearerToken(): string {
  return randomBytes(32).toString("base64url");
}

export async function runSetup(
  workDir: string,
  sourceRoot: string,
  options: { envFile?: string } = {}
): Promise<void> {
  const envFile = options.envFile || ".env";
  const envPath = path.resolve(workDir, envFile);
  if (!existsSync(envPath)) {
    await copyFile(path.join(sourceRoot, ".env.example"), envPath);
    console.log(`Created ${envFile}.`);
  }

  const pythonPath = await ensureVenv(workDir);
  await installPythonPackage(sourceRoot, workDir, pythonPath);

  const env = await readEnvFile(envPath);
  if (valueLooksMissing(env.MCP_BEARER_TOKEN)) {
    await writeEnvUpdates(envPath, { MCP_BEARER_TOKEN: generateBearerToken() });
    console.log("Generated MCP_BEARER_TOKEN in the env file.");
  }

  await runPythonAuthHelper(workDir, pythonPath, envFile);
  const code = await runDoctor(workDir, { envFile });
  process.exitCode = code;
}
