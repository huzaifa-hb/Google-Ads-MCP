from __future__ import annotations

import os
from pathlib import Path
import tempfile
import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp import geo_targets


class GeoTargetTests(unittest.TestCase):
    def tearDown(self) -> None:
        os.environ.pop("GOOGLE_ADS_GEO_TARGETS_CSV", None)
        geo_targets._runtime_geo_targets.cache_clear()  # noqa: SLF001 - test resets env-backed cache.

    def test_builtin_geo_target_lookup_remains_available(self) -> None:
        self.assertEqual(geo_targets.resolve_geo_target("2840"), "United States")

    def test_runtime_csv_overrides_and_expands_geo_targets(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "geo_target_constants.csv"
            path.write_text(
                "Criteria ID,Name,Canonical Name\n"
                "2840,United States,United States override\n"
                "999001,Test City,Test City, Test Region, Test Country\n",
                encoding="utf-8",
            )
            os.environ["GOOGLE_ADS_GEO_TARGETS_CSV"] = str(path)
            geo_targets._runtime_geo_targets.cache_clear()  # noqa: SLF001

            self.assertEqual(geo_targets.resolve_geo_target("2840"), "United States override")
            self.assertEqual(
                geo_targets.resolve_geo_target("999001"),
                "Test City",
            )

    def test_missing_runtime_csv_falls_back_to_builtin_table(self) -> None:
        os.environ["GOOGLE_ADS_GEO_TARGETS_CSV"] = "C:/does/not/exist.csv"
        geo_targets._runtime_geo_targets.cache_clear()  # noqa: SLF001

        with self.assertLogs(geo_targets.LOGGER, level="WARNING"):
            self.assertEqual(geo_targets.resolve_geo_target("2840"), "United States")


if __name__ == "__main__":
    unittest.main()
