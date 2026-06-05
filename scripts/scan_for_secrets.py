"""Small repository secret scanner for CI.

This intentionally catches obvious committed credentials. It is not a replacement
for platform secret scanning, but it gives a quick local/CI tripwire.
"""

from __future__ import annotations

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", "google_ads_mcp.egg-info"}
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
    parts = set(path.relative_to(ROOT).parts)
    return bool(parts & SKIP_DIRS)


if __name__ == "__main__":
    main()
