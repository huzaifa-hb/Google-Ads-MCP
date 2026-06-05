"""Generate docs/capability-matrix.md from the internal tool registry."""

from __future__ import annotations

from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from google_ads_mcp.capability_matrix import (  # noqa: E402
    capability_matrix_markdown,
    build_full_capability_matrix,
)
from google_ads_mcp.tool_catalog import FRIENDLY_TOOL_SPECS  # noqa: E402


def build_markdown() -> str:
    return capability_matrix_markdown(build_full_capability_matrix(FRIENDLY_TOOL_SPECS))


def main() -> None:
    target = Path("docs/capability-matrix.md")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(build_markdown(), encoding="utf-8")


if __name__ == "__main__":
    main()
