"""Refresh the bundled geo-target lookup from Google's published CSV.

Usage:
    python scripts/refresh_geo_targets.py path/to/geo_target_constants.csv

Download source:
    https://developers.google.com/google-ads/api/data/geotargets
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path


def main() -> None:
    if len(sys.argv) != 2:
        print("Usage: python scripts/refresh_geo_targets.py path/to/geo_target_constants.csv")
        raise SystemExit(2)

    source = Path(sys.argv[1])
    rows = {}
    with source.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            criterion_id = row.get("Criteria ID") or row.get("criterion_id")
            name = row.get("Name") or row.get("name")
            canonical = row.get("Canonical Name") or row.get("canonical_name")
            if criterion_id and name:
                rows[criterion_id] = canonical or name

    lines = [
        '"""Generated geo target lookup. See scripts/refresh_geo_targets.py."""',
        "",
        "from __future__ import annotations",
        "",
        "GEO_TARGETS: dict[str, str] = {",
    ]
    for criterion_id, name in sorted(rows.items(), key=lambda item: int(item[0])):
        safe_name = name.replace("\\", "\\\\").replace('"', '\\"')
        lines.append(f'    "{criterion_id}": "{safe_name}",')
    lines.extend(
        [
            "}",
            "",
            "",
            "def resolve_geo_target(criterion_id: str | int) -> str:",
            '    return GEO_TARGETS.get(str(criterion_id), f"Geo target {criterion_id}")',
            "",
        ]
    )
    Path("src/google_ads_mcp/geo_targets.py").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(rows)} geo targets.")


if __name__ == "__main__":
    main()

