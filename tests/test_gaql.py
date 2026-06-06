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

    def test_default_parameters_added_once(self) -> None:
        query = apply_default_parameters("SELECT campaign.id FROM campaign")

        self.assertIn("PARAMETERS omit_unselected_resource_names = true", query)
        self.assertEqual(apply_default_parameters(query), query)

    def test_pagination_adds_limit_before_parameters(self) -> None:
        query = apply_pagination(
            "SELECT campaign.id FROM campaign PARAMETERS include_drafts = true",
            Pagination(page_size=2, page_token="next-token"),
        )

        self.assertEqual(
            query,
            "SELECT campaign.id FROM campaign LIMIT 2 PARAMETERS include_drafts = true",
        )

    def test_pagination_preserves_existing_limit(self) -> None:
        query = apply_pagination(
            "SELECT campaign.id FROM campaign LIMIT 5",
            Pagination(page_size=2),
        )

        self.assertEqual(query, "SELECT campaign.id FROM campaign LIMIT 5")

    def test_pagination_shape_is_page_token_only(self) -> None:
        pagination = Pagination(page_size=2, page_token="next-token")

        self.assertFalse(hasattr(pagination, "offset"))

    def test_explain_gaql_error_returns_specific_guidance(self) -> None:
        result = explain_gaql_error("EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE")

        self.assertEqual(result["error_type"], "EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE")
        self.assertIn("planning_plan_gaql_query", result["related_tools"])


if __name__ == "__main__":
    unittest.main()
