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
        "import csv",
        "import logging",
        "import os",
        "from functools import lru_cache",
        "from pathlib import Path",
        "",
        "",
        "LOGGER = logging.getLogger(__name__)",
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
            "    key = str(criterion_id)",
            '    return _runtime_geo_targets().get(key) or GEO_TARGETS.get(key, f"Geo target {criterion_id}")',
            "",
            "",
            "@lru_cache(maxsize=1)",
            "def _runtime_geo_targets() -> dict[str, str]:",
            '    path = os.environ.get("GOOGLE_ADS_GEO_TARGETS_CSV")',
            "    if not path:",
            "        return {}",
            "    try:",
            "        return _read_geo_targets_csv(Path(path))",
            "    except OSError as exc:",
            '        LOGGER.warning("Unable to read GOOGLE_ADS_GEO_TARGETS_CSV %s: %s", path, exc)',
            "        return {}",
            "",
            "",
            "def _read_geo_targets_csv(path: Path) -> dict[str, str]:",
            "    rows: dict[str, str] = {}",
            '    with path.open("r", encoding="utf-8-sig", newline="") as handle:',
            "        reader = csv.DictReader(handle)",
            "        for row in reader:",
            '            criterion_id = row.get("Criteria ID") or row.get("criterion_id")',
            '            name = row.get("Name") or row.get("name")',
            '            canonical = row.get("Canonical Name") or row.get("canonical_name")',
            "            if criterion_id and name:",
            "                rows[str(criterion_id)] = canonical or name",
            "    return rows",
            "",
        ]
    )
    Path("src/google_ads_mcp/geo_targets.py").write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {len(rows)} geo targets.")


if __name__ == "__main__":
    main()

