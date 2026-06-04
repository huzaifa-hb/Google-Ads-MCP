"""Small built-in geo target lookup with refresh hook.

Google Ads geo reports return criterion IDs. Production deployments should refresh
this table from Google's published geo target CSV using scripts/refresh_geo_targets.py.
This starter table covers common countries and regions and keeps the MCP useful
without adding per-row lookup latency.
"""

from __future__ import annotations

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
    return GEO_TARGETS.get(str(criterion_id), f"Geo target {criterion_id}")

