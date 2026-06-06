"""Geo target lookup with a bundled fallback and optional CSV override.

Google Ads geo reports return criterion IDs. Production deployments should refresh
this table from Google's published geo target CSV using scripts/refresh_geo_targets.py
or point GOOGLE_ADS_GEO_TARGETS_CSV at a downloaded CSV file. This starter table
covers common countries and regions and keeps the MCP useful without adding
per-row lookup latency.
"""

from __future__ import annotations

import csv
import logging
import os
from functools import lru_cache
from pathlib import Path


LOGGER = logging.getLogger(__name__)

GEO_TARGETS: dict[str, str] = {
    "2840": "United States",
    "2124": "Canada",
    "2826": "United Kingdom",
    "2036": "Australia",
    "2392": "Japan",
    "2356": "India",
    "2276": "Germany",
    "2250": "France",
    "2380": "Italy",
    "2724": "Spain",
    "2586": "Pakistan",
    "2784": "United Arab Emirates",
    "2682": "Saudi Arabia",
}


def resolve_geo_target(criterion_id: str | int) -> str:
    key = str(criterion_id)
    return _runtime_geo_targets().get(key) or GEO_TARGETS.get(key, f"Geo target {criterion_id}")


@lru_cache(maxsize=1)
def _runtime_geo_targets() -> dict[str, str]:
    path = os.environ.get("GOOGLE_ADS_GEO_TARGETS_CSV")
    if not path:
        return {}
    try:
        return _read_geo_targets_csv(Path(path))
    except OSError as exc:
        LOGGER.warning("Unable to read GOOGLE_ADS_GEO_TARGETS_CSV %s: %s", path, exc)
        return {}


def _read_geo_targets_csv(path: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            criterion_id = row.get("Criteria ID") or row.get("criterion_id")
            name = row.get("Name") or row.get("name")
            canonical = row.get("Canonical Name") or row.get("canonical_name")
            if criterion_id and name:
                rows[str(criterion_id)] = canonical or name
    return rows

