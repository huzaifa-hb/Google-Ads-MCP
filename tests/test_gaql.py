from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.gaql import (
    Pagination,
    apply_default_parameters,
    apply_pagination,
    date_where_clause,
    ensure_primary_field,
    explain_gaql_error,
    summarize_page,
    trim_offset_page,
)
from google_ads_mcp.safety import ValidationError


class GaqlTests(unittest.TestCase):
    def test_custom_date_range(self) -> None:
        clause = date_where_clause(start_date="2026-01-01", end_date="2026-01-31")
        self.assertEqual(clause, "segments.date BETWEEN '2026-01-01' AND '2026-01-31'")

    def test_preset_date_range(self) -> None:
        self.assertEqual(date_where_clause(date_range="LAST_7_DAYS"), "segments.date DURING LAST_7_DAYS")

    def test_primary_field_required(self) -> None:
        with self.assertRaises(ValidationError):
            ensure_primary_field("SELECT campaign.name FROM campaign", "campaign.id")

    def test_primary_field_present(self) -> None:
        ensure_primary_field("SELECT campaign.id, campaign.name FROM campaign", "campaign.id")

    def test_offset_pagination_fetches_extra_row_and_reports_next_offset(self) -> None:
        query = apply_pagination("SELECT campaign.id FROM campaign", Pagination(page_size=2, offset=50))
        self.assertIn("LIMIT 3 OFFSET 50", query)
        rows = [{"id": 1}, {"id": 2}, {"id": 3}]
        trimmed = trim_offset_page(rows, page_size=2, offset=50)
        self.assertEqual(len(trimmed), 2)
        summary = summarize_page(trimmed, page_size=2, offset=50, fetched_count=len(rows))
        self.assertTrue(summary["has_more"])
        self.assertEqual(summary["next_offset"], 52)

    def test_default_parameters_added_once(self) -> None:
        query = apply_default_parameters("SELECT campaign.id FROM campaign")

        self.assertIn("PARAMETERS omit_unselected_resource_names = true", query)
        self.assertEqual(apply_default_parameters(query), query)

    def test_pagination_is_inserted_before_existing_parameters(self) -> None:
        query = apply_pagination(
            "SELECT campaign.id FROM campaign PARAMETERS include_drafts = true",
            Pagination(page_size=2, offset=10),
        )

        self.assertEqual(
            query,
            "SELECT campaign.id FROM campaign LIMIT 3 OFFSET 10 PARAMETERS include_drafts = true",
        )

    def test_explain_gaql_error_returns_specific_guidance(self) -> None:
        result = explain_gaql_error("EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE")

        self.assertEqual(result["error_type"], "EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE")
        self.assertIn("planning_plan_gaql_query", result["related_tools"])


if __name__ == "__main__":
    unittest.main()
