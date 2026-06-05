"""Generate docs/gaql-knowledge-base.md from the offline KB."""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from google_ads_mcp.knowledge_base import ENTRIES  # noqa: E402


def build_markdown() -> str:
    groups = defaultdict(list)
    for entry in ENTRIES:
        groups[entry.category].append(entry)

    lines = [
        "# GAQL Knowledge Base",
        "",
        "This file is generated from `src/google_ads_mcp/knowledge_base.py`.",
        "",
    ]
    for category in sorted(groups):
        lines.append(f"## {category.replace('_', ' ').title()}")
        lines.append("")
        for entry in groups[category]:
            lines.append(f"### `{entry.id}`")
            lines.append("")
            lines.append(f"**Question:** {entry.question}")
            lines.append("")
            lines.append(entry.answer)
            lines.append("")
            if entry.queries:
                lines.append("| Example | Primary Field | GAQL |")
                lines.append("|---|---|---|")
                for query in entry.queries:
                    primary = query.primary_field or ""
                    gaql = query.gaql.replace("|", "\\|")
                    lines.append(f"| {query.label} | `{primary}` | `{gaql}` |")
                lines.append("")
            if entry.notes:
                lines.append("**Notes**")
                lines.append("")
                for note in entry.notes:
                    lines.append(f"- {note}")
                lines.append("")
            if entry.see_also:
                links = ", ".join(f"`{item}`" for item in entry.see_also)
                lines.append(f"**See also:** {links}")
                lines.append("")

    return "\n".join(lines)


def main() -> None:
    target = Path("docs/gaql-knowledge-base.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
