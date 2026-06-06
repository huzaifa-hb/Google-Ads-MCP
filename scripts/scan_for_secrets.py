"""Small repository secret scanner for CI.

This intentionally catches obvious committed credentials. It is not a replacement
for platform secret scanning, but it gives a quick local/CI tripwire.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".ruff_cache",
    ".codex-run",
    ".claude",
    ".next",
    ".turbo",
    "coverage",
    "dist",
    "google_ads_mcp.egg-info",
    "node_modules",
}
SCAN_SUFFIXES = {".py", ".ps1", ".toml", ".yaml", ".yml", ".json", ".env", ".example"}
SECRET_PATTERNS = {
    "google_api_key": re.compile(r"AIza[0-9A-Za-z_-]{30,}"),
    "google_oauth_access_token": re.compile(r"ya29\.[0-9A-Za-z_-]{20,}"),
    "google_oauth_refresh_token": re.compile(r"1//[0-9A-Za-z_-]{20,}"),
    "google_oauth_client_secret": re.compile(r"GOCSPX-[0-9A-Za-z_-]{20,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
}


def main() -> None:
    findings: list[str] = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or _skip(path):
            continue
        if path.suffix not in SCAN_SUFFIXES and path.name != ".env":
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{path.relative_to(ROOT)}: {name}")

    if findings:
        raise SystemExit("Potential secrets found:\n" + "\n".join(findings))


def _skip(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if relative.as_posix() in IGNORED_PATHS:
        return True
    parts = set(relative.parts)
    return bool(parts & SKIP_DIRS)


def _git_ignored_paths(root: Path) -> set[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files", "--others", "-i", "--exclude-standard"],
            cwd=root,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError:
        return set()
    if result.returncode != 0:
        return set()
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


IGNORED_PATHS = _git_ignored_paths(ROOT)


if __name__ == "__main__":
    main()
