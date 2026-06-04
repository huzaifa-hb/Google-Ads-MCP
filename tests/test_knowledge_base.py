from __future__ import annotations

import unittest

import _bootstrap  # noqa: F401
from google_ads_mcp.gaql import ensure_primary_field
from google_ads_mcp.knowledge_base import CATEGORIES, ENTRIES, ENTRY_BY_ID, KBEntry, search, total_entry_count


class KnowledgeBaseTests(unittest.TestCase):
    def test_quality_score_search_returns_keyword_metrics(self) -> None:
        matches = search("how to get quality score")
        self.assertEqual(matches[0].id, "keyword-metrics")
        self.assertIn("ad_group_criterion.quality_info.quality_score", matches[0].queries[0].gaql)

    def test_resource_name_search_returns_resource_format(self) -> None:
        matches = search("what is the format of resource_name")
        self.assertEqual(matches[0].id, "resource-name-format")

    def test_expected_referenced_search_returns_primary_field_entry(self) -> None:
        matches = search("why do I get EXPECTED_REFERENCED")
        self.assertEqual(matches[0].id, "primary-field-requirement")

    def test_unknown_question_falls_back_to_gaql_syntax(self) -> None:
        matches = search("something completely unknown xyz")
        self.assertEqual([entry.id for entry in matches], ["gaql-syntax"])

    def test_category_filter_returns_matching_category(self) -> None:
        matches = search("quality score fields", category="metrics")
        self.assertTrue(matches)
        self.assertTrue(all(entry.category == "metrics" for entry in matches))

    def test_category_filter_with_no_match_still_falls_back(self) -> None:
        matches = search("zzzzzzzzzz", category="metrics")
        self.assertEqual(matches[0].id, "gaql-syntax")

    def test_every_category_has_an_entry(self) -> None:
        seen = {entry.category for entry in ENTRIES}
        expected = {
            "syntax",
            "resources",
            "metrics",
            "segments",
            "filters",
            "pagination",
            "reporting",
            "shopping",
            "video",
            "assets",
            "conversions",
            "audiences",
            "change_history",
            "limitations",
            "errors",
        }
        self.assertEqual(seen, expected)
        self.assertEqual(tuple(sorted(seen)), CATEGORIES)

    def test_every_category_can_return_a_result(self) -> None:
        for category in CATEGORIES:
            first = next(entry for entry in ENTRIES if entry.category == category)
            matches = search(first.keywords[0], category=category)
            self.assertTrue(matches, category)
            if matches[0].id != "gaql-syntax":
                self.assertEqual(matches[0].category, category)

    def test_total_entry_count_matches_entries(self) -> None:
        self.assertEqual(total_entry_count(), len(ENTRIES))

    def test_entry_ids_are_unique(self) -> None:
        self.assertEqual(len(ENTRY_BY_ID), len(ENTRIES))

    def test_to_dict_shape(self) -> None:
        entry = ENTRY_BY_ID["keyword-metrics"].to_dict()
        self.assertEqual(entry["id"], "keyword-metrics")
        self.assertIsInstance(entry["example_queries"], list)
        self.assertIn("primary_field", entry["example_queries"][0])

    def test_all_entries_are_dataclasses(self) -> None:
        self.assertTrue(all(isinstance(entry, KBEntry) for entry in ENTRIES))

    def test_all_examples_with_primary_field_pass_primary_validation(self) -> None:
        for entry in ENTRIES:
            for query in entry.queries:
                if query.primary_field:
                    with self.subTest(entry=entry.id, label=query.label):
                        ensure_primary_field(query.gaql, query.primary_field)

    def test_representative_reporting_queries_pass_primary_validation(self) -> None:
        for entry_id in [
            "campaign-metrics",
            "keyword-metrics",
            "search-terms-report",
            "geo-performance",
            "change-history",
        ]:
            query = ENTRY_BY_ID[entry_id].queries[0]
            ensure_primary_field(query.gaql, query.primary_field or "")

    def test_common_errors_mentions_expected_error(self) -> None:
        entry = ENTRY_BY_ID["common-errors"]
        self.assertIn("EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE", entry.answer)

    def test_manager_limits_mentions_leaf_customer(self) -> None:
        entry = ENTRY_BY_ID["manager-account-limits"]
        self.assertIn("leaf customer ID", entry.answer)

    def test_search_returns_at_most_five(self) -> None:
        self.assertLessEqual(len(search("metrics campaign keyword conversion report")), 5)

    def test_category_slugs_are_lowercase(self) -> None:
        for entry in ENTRIES:
            self.assertEqual(entry.category, entry.category.lower())
            self.assertNotIn(" ", entry.category)


if __name__ == "__main__":
    unittest.main()
