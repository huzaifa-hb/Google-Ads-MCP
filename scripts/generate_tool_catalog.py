"""Generate docs/tool-catalog.md from the friendly tool registry."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from google_ads_mcp.tool_catalog import FRIENDLY_TOOL_SPECS  # noqa: E402
from google_ads_mcp.tool_config import CORE_TOOL_DEFS  # noqa: E402


def build_markdown() -> str:
    groups = defaultdict(list)
    for spec in FRIENDLY_TOOL_SPECS:
        groups[spec.category].append(spec)

    lines = [
        "# Google Ads MCP Tool Catalog",
        "",
        "This file is generated from `src/google_ads_mcp/tool_catalog.py` and "
        "`src/google_ads_mcp/tool_config.py`.",
        "",
        "## Planning",
        "",
        "| Tool | Mode | Resource | Description |",
        "|---|---|---|---|",
    ]
    for name, definition in sorted(CORE_TOOL_DEFS.items()):
        namespace = definition["namespace"]
        mode = definition["mode"]
        description = definition["description"]
        lines.append(f"| `{name}` | `{mode}` | `{namespace}` | {description} |")
    lines.append("")
    for category in sorted(groups):
        lines.append(f"## {category.replace('_', ' ').title()}")
        lines.append("")
        lines.append("| Tool | Mode | Resource | Description |")
        lines.append("|---|---|---|---|")
        for spec in groups[category]:
            resource = spec.resource or ""
            lines.append(f"| `{spec.name}` | `{spec.mode}` | `{resource}` | {spec.description} |")
        lines.append("")

    return "\n".join(lines)


def main() -> None:
    target = Path("docs/tool-catalog.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
