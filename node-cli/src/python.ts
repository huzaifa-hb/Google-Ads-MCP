import { existsSync } from "node:fs";
import path from "node:path";
import { runCommand } from "./runner.js";

export function venvPythonPath(rootDir: string): string | undefined {
  const candidate =
    process.platform === "win32"
      ? path.join(rootDir, ".venv", "Scripts", "python.exe")
      : path.join(rootDir, ".venv", "bin", "python");
  return existsSync(candidate) ? candidate : undefined;
}

export async function pythonVersion(): Promise<{ ok: boolean; detail: string }> {
  const result = await runCommand("python", ["--version"]);
  const detail = (result.stdout || result.stderr || "python not found").trim();
  return {
    ok: result.code === 0 && /Python 3\.(1[2-9]|[2-9]\d)\./.test(detail),
    detail
  };
}

export async function ensureVenv(rootDir: string): Promise<string> {
  const existing = venvPythonPath(rootDir);
  if (existing) {
    return existing;
  }
  const result = await runCommand("python", ["-m", "venv", ".venv"], { cwd: rootDir, stdio: "inherit" });
  if (result.code !== 0) {
    throw new Error("Failed to create Python virtual environment.");
  }
  const created = venvPythonPath(rootDir);
  if (!created) {
    throw new Error("Python virtual environment was not created.");
  }
  return created;
}

export async function installPythonPackage(
  sourceRoot: string,
  workDir: string,
  pythonPath: string
): Promise<void> {
  const sameRoot = path.resolve(sourceRoot) === path.resolve(workDir);
  const args = sameRoot
    ? ["-m", "pip", "install", "-e", ".[setup]"]
    : ["-m", "pip", "install", `${sourceRoot}[setup]`];
  const result = await runCommand(pythonPath, args, {
    cwd: sameRoot ? sourceRoot : workDir,
    stdio: "inherit"
  });
  if (result.code !== 0) {
    throw new Error("Failed to install Python package.");
  }
}

export async function runPythonAuthHelper(rootDir: string, pythonPath: string, envFile: string): Promise<void> {
  const result = await runCommand(
    pythonPath,
    ["-m", "google_ads_mcp.auth_setup", "--write-env", "--prompt", "--env-file", envFile],
    { cwd: rootDir, stdio: "inherit" }
  );
  if (result.code !== 0) {
    throw new Error("Google Ads OAuth setup did not complete.");
  }
}
