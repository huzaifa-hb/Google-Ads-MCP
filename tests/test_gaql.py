from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.gaql import (
    Pagination,
    apply_default_parameters,
    apply_pagination,
    apply_pagination_plan,
    date_where_clause,
    ensure_no_offset_clause,
    ensure_primary_field,
    explain_gaql_error,
    gaql_filter_clause,
)
from google_ads_mcp.safety import ValidationError


class GaqlTests(unittest.TestCase):
    def test_custom_date_range(self) -> None:
        clause = date_where_clause(start_date="2026-01-01", end_date="2026-01-31")
        self.assertEqual(clause, "segments.date BETWEEN '2026-01-01' AND '2026-01-31'")

    def test_custom_date_range_expands_datetime_fields_to_full_days(self) -> None:
        clause = date_where_clause(
            start_date="2026-01-01",
            end_date="2026-01-31",
            field="change_event.change_date_time",
        )

        self.assertEqual(
            clause,
            "change_event.change_date_time BETWEEN "
            "'2026-01-01 00:00:00' AND '2026-01-31 23:59:59'",
        )

    def test_preset_date_range(self) -> None:
        self.assertEqual(date_where_clause(date_range="LAST_7_DAYS"), "segments.date DURING LAST_7_DAYS")

    def test_numeric_filter_literals_allow_signed_values(self) -> None:
        cases = [
            ("-5", "INT64", "metrics.clicks > -5"),
            ("+5", "INT64", "metrics.clicks > +5"),
            ("-1.25", "DOUBLE", "metrics.clicks > -1.25"),
        ]

        for value, data_type, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(
                    gaql_filter_clause(
                        "metrics.clicks",
                        {"operator": ">", "value": value},
                        data_type,
                    ),
                    expected,
                )

    def test_numeric_filter_literals_still_quote_non_numeric_text(self) -> None:
        self.assertEqual(
            gaql_filter_clause(
                "metrics.clicks",
                {"operator": ">", "value": "not-a-number"},
                "INT64",
            ),
            "metrics.clicks > 'not-a-number'",
        )

    def test_primary_field_required(self) -> None:
        with self.assertRaises(ValidationError):
            ensure_primary_field("SELECT campaign.name FROM campaign", "campaign.id")

    def test_primary_field_present(self) -> None:
        ensure_primary_field("SELECT campaign.id, campaign.name FROM campaign", "campaign.id")

    def test_default_parameters_added_once(self) -> None:
        query = apply_default_parameters("SELECT campaign.id FROM campaign")

        self.assertIn("PARAMETERS omit_unselected_resource_names = true", query)
        self.assertEqual(apply_default_parameters(query), query)

    def test_pagination_preserves_query_with_parameters(self) -> None:
        query = apply_pagination(
            "SELECT campaign.id FROM campaign PARAMETERS include_drafts = true",
            Pagination(max_rows=2),
        )

        self.assertEqual(
            query,
            "SELECT campaign.id FROM campaign LIMIT 2 PARAMETERS include_drafts = true",
        )

    def test_pagination_preserves_existing_limit(self) -> None:
        query = apply_pagination(
            "SELECT campaign.id FROM campaign LIMIT 5",
            Pagination(max_rows=2),
        )

        self.assertEqual(query, "SELECT campaign.id FROM campaign LIMIT 5")

    def test_pagination_does_not_add_gaql_limit_when_max_rows_is_none(self) -> None:
        query = apply_pagination(
            "SELECT campaign.id FROM campaign",
            Pagination(max_rows=None),
        )

        self.assertEqual(query, "SELECT campaign.id FROM campaign")

    def test_pagination_injects_limit_from_max_rows(self) -> None:
        plan = apply_pagination_plan(
            "SELECT campaign.id FROM campaign",
            Pagination(max_rows=2),
        )

        self.assertEqual(plan.query, "SELECT campaign.id FROM campaign LIMIT 2")
        self.assertTrue(plan.limit_injected)
        self.assertEqual(plan.effective_limit, 2)
        self.assertFalse(plan.page_size_deprecated)

    def test_pagination_treats_page_size_as_deprecated_alias(self) -> None:
        plan = apply_pagination_plan(
            "SELECT campaign.id FROM campaign",
            Pagination(page_size=2),
        )

        self.assertEqual(plan.query, "SELECT campaign.id FROM campaign LIMIT 2")
        self.assertTrue(plan.limit_injected)
        self.assertEqual(plan.effective_limit, 2)
        self.assertTrue(plan.page_size_deprecated)

    def test_pagination_rejects_page_token_with_injected_limit(self) -> None:
        with self.assertRaisesRegex(ValidationError, "page_token"):
            apply_pagination_plan(
                "SELECT campaign.id FROM campaign",
                Pagination(max_rows=2, page_token="next-token"),
            )

    def test_pagination_allows_page_token_without_injected_limit(self) -> None:
        plan = apply_pagination_plan(
            "SELECT campaign.id FROM campaign",
            Pagination(max_rows=None, page_token="next-token"),
        )

        self.assertEqual(plan.query, "SELECT campaign.id FROM campaign")
        self.assertFalse(plan.limit_injected)

    def test_pagination_allows_page_token_with_large_user_limit(self) -> None:
        plan = apply_pagination_plan(
            "SELECT campaign.id FROM campaign LIMIT 10000",
            Pagination(max_rows=2, page_token="next-token"),
        )

        self.assertEqual(plan.query, "SELECT campaign.id FROM campaign LIMIT 10000")
        self.assertFalse(plan.limit_injected)
        self.assertEqual(plan.effective_limit, 10000)

    def test_change_event_requires_finite_limit(self) -> None:
        with self.assertRaisesRegex(ValidationError, "change_event"):
            apply_pagination_plan(
                "SELECT change_event.resource_name FROM change_event",
                Pagination(max_rows=None),
            )

    def test_change_event_rejects_limit_over_api_cap(self) -> None:
        with self.assertRaisesRegex(ValidationError, "10,000"):
            apply_pagination_plan(
                "SELECT change_event.resource_name FROM change_event LIMIT 10001",
                Pagination(max_rows=None),
            )

    def test_pagination_shape_is_page_token_only(self) -> None:
        pagination = Pagination(page_size=2, page_token="next-token")

        self.assertFalse(hasattr(pagination, "offset"))

    def test_pagination_rejects_offset_clause(self) -> None:
        with self.assertRaisesRegex(ValidationError, "OFFSET"):
            apply_pagination(
                "SELECT campaign.id FROM campaign LIMIT 10 OFFSET 10",
                Pagination(page_size=10),
            )

    def test_offset_word_inside_string_literal_is_allowed(self) -> None:
        ensure_no_offset_clause("SELECT campaign.id FROM campaign WHERE campaign.name = 'offset'")

    def test_explain_gaql_error_returns_specific_guidance(self) -> None:
        result = explain_gaql_error("EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE")

        self.assertEqual(result["error_type"], "EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE")
        self.assertIn("planning_plan_gaql_query", result["related_tools"])

    def test_explain_gaql_error_returns_offset_guidance(self) -> None:
        result = explain_gaql_error("Unexpected input OFFSET")

        self.assertEqual(result["error_type"], "UNSUPPORTED_OFFSET")
        self.assertIn("page_token", result["suggested_fix"])

    def test_explain_gaql_error_returns_page_size_guidance(self) -> None:
        result = explain_gaql_error("PAGE_SIZE_NOT_SUPPORTED")

        self.assertEqual(result["error_type"], "PAGE_SIZE_NOT_SUPPORTED")
        self.assertIn("10,000", result["explanation"])

    def test_explain_gaql_error_does_not_match_rate_inside_word(self) -> None:
        result = explain_gaql_error("Bidding strategy type is incompatible.")

        self.assertEqual(result["error_type"], "UNKNOWN_GAQL_ERROR")

    def test_explain_gaql_error_matches_rate_limit_phrase(self) -> None:
        result = explain_gaql_error("RATE_LIMIT exceeded by request.")

        self.assertEqual(result["error_type"], "QUOTA_OR_RATE_LIMIT")

    def test_default_parameters_ignores_word_inside_string_literal(self) -> None:
        query = "SELECT campaign.id FROM campaign WHERE campaign.name = 'has parameters text'"

        result = apply_default_parameters(query)

        self.assertTrue(result.endswith("PARAMETERS omit_unselected_resource_names = true"))


if __name__ == "__main__":
    unittest.main()
