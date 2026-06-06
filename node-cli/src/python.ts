import { existsSync } from "node:fs";
import path from "node:path";
import { runCommand } from "./runner.js";

export type PythonCommand = {
  command: string;
  args: string[];
  label: string;
};

export function venvPythonPath(rootDir: string): string | undefined {
  const candidate =
    process.platform === "win32"
      ? path.join(rootDir, ".venv", "Scripts", "python.exe")
      : path.join(rootDir, ".venv", "bin", "python");
  return existsSync(candidate) ? candidate : undefined;
}

export function pythonCandidates(
  env: NodeJS.ProcessEnv = process.env,
  platform: NodeJS.Platform = process.platform
): PythonCommand[] {
  const candidates: PythonCommand[] = [];
  if (env.PYTHON) {
    candidates.push({ command: env.PYTHON, args: [], label: env.PYTHON });
  }
  candidates.push({ command: "python", args: [], label: "python" });
  candidates.push({ command: "python3", args: [], label: "python3" });
  if (platform === "win32") {
    candidates.push({ command: "py", args: ["-3.12"], label: "py -3.12" });
    candidates.push({ command: "py", args: ["-3"], label: "py -3" });
  }
  const seen = new Set<string>();
  return candidates.filter((candidate) => {
    const key = `${candidate.command}\0${candidate.args.join("\0")}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
    return true;
  });
}

export async function resolvePythonCommand(): Promise<(PythonCommand & { detail: string }) | undefined> {
  for (const candidate of pythonCandidates()) {
    const result = await runCommand(candidate.command, [...candidate.args, "--version"]);
    const detail = (result.stdout || result.stderr || `${candidate.label} not found`).trim();
    if (result.code === 0 && /Python 3\.(1[2-9]|[2-9]\d)\./.test(detail)) {
      return { ...candidate, detail };
    }
  }
  return undefined;
}

export async function pythonVersion(): Promise<{ ok: boolean; detail: string }> {
  const resolved = await resolvePythonCommand();
  if (!resolved) {
    return { ok: false, detail: "Python 3.12+ not found via PYTHON, python, python3, or py." };
  }
  return { ok: true, detail: `${resolved.detail} (${resolved.label})` };
}

export async function ensureVenv(rootDir: string): Promise<string> {
  const existing = venvPythonPath(rootDir);
  if (existing) {
    return existing;
  }
  const python = await resolvePythonCommand();
  if (!python) {
    throw new Error("Python 3.12+ was not found via PYTHON, python, python3, or py.");
  }
  const result = await runCommand(python.command, [...python.args, "-m", "venv", ".venv"], {
    cwd: rootDir,
    stdio: "inherit"
  });
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
