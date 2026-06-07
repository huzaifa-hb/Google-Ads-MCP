"""Fail if generated documentation files are stale."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generate_capability_matrix import (  # noqa: E402
    build_markdown as build_capability_matrix,
)
from scripts.generate_kb_docs import build_markdown as build_knowledge_base  # noqa: E402
from scripts.generate_tool_catalog import build_markdown as build_tool_catalog  # noqa: E402


GENERATED_DOCS = {
    Path("docs/tool-catalog.md"): build_tool_catalog,
    Path("src/google_ads_mcp/resources_data/tool-catalog.md"): build_tool_catalog,
    Path("docs/gaql-knowledge-base.md"): build_knowledge_base,
    Path("src/google_ads_mcp/resources_data/gaql-knowledge-base.md"): build_knowledge_base,
    Path("docs/capability-matrix.md"): build_capability_matrix,
    Path("src/google_ads_mcp/resources_data/capability-matrix.md"): build_capability_matrix,
}


def main() -> None:
    stale: list[str] = []
    for path, builder in GENERATED_DOCS.items():
        expected = builder()
        actual_path = ROOT / path
        actual = actual_path.read_text(encoding="utf-8") if actual_path.exists() else ""
        if actual != expected:
            stale.append(str(path))

    if stale:
        joined = ", ".join(stale)
        raise SystemExit(
            f"Generated docs are stale: {joined}. Run the matching scripts/generate_*.py files."
        )


if __name__ == "__main__":
    main()
