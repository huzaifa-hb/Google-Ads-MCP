"""Offline GAQL knowledge base for query planning.

The entries here are intentionally static. They help agents draft working GAQL
without spending quota or depending on live Google Ads credentials.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class KBQuery:
    label: str
    gaql: str
    primary_field: str | None
    required_in_select: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "label": self.label,
            "gaql": self.gaql,
            "primary_field": self.primary_field,
            "required_in_select": list(self.required_in_select),
        }


@dataclass(frozen=True)
class KBEntry:
    id: str
    category: str
    question: str
    keywords: tuple[str, ...]
    answer: str
    queries: tuple[KBQuery, ...] = ()
    notes: tuple[str, ...] = ()
    see_also: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "category": self.category,
            "question": self.question,
            "answer": self.answer,
            "example_queries": [query.to_dict() for query in self.queries],
            "notes": list(self.notes),
            "see_also": list(self.see_also),
        }


PRIMARY_FIELDS = {
    "campaign": "campaign.id",
    "ad_group": "ad_group.id",
    "ad_group_ad": "ad_group_ad.ad.id",
    "keyword_view": "ad_group_criterion.criterion_id",
    "ad_group_criterion": "ad_group_criterion.criterion_id",
    "search_term_view": "search_term_view.search_term",
    "geographic_view": "campaign.id",
    "age_range_view": "ad_group_criterion.criterion_id",
    "gender_view": "ad_group_criterion.criterion_id",
    "income_range_view": "ad_group_criterion.criterion_id",
    "parental_status_view": "ad_group_criterion.criterion_id",
    "ad_group_audience_view": "user_list.id",
    "group_placement_view": "group_placement_view.placement",
    "asset_group_asset": "asset.id",
    "video": "video.id",
    "shopping_performance_view": "campaign.id",
    "landing_page_view": "landing_page_view.unexpanded_final_url",
    "call_view": "call_view.resource_name",
    "change_event": "change_event.resource_name",
    "bidding_strategy": "bidding_strategy.id",
    "campaign_budget": "campaign_budget.id",
    "label": "label.id",
    "user_list": "user_list.id",
    "conversion_action": "conversion_action.id",
    "asset": "asset.id",
    "asset_group": "asset_group.id",
    "recommendation": "recommendation.resource_name",
}


def q(label: str, gaql: str, primary_field: str | None, *required: str) -> KBQuery:
    return KBQuery(label=label, gaql=" ".join(gaql.split()), primary_field=primary_field, required_in_select=required)


ENTRIES: tuple[KBEntry, ...] = (
    KBEntry(
        id="gaql-syntax",
        category="syntax",
        question="How does GAQL syntax work?",
        keywords=("gaql", "syntax", "select", "from", "where", "order", "limit", "sql"),
        answer=(
            "GAQL uses SELECT, FROM, WHERE, ORDER BY, and LIMIT, but it is not SQL. "
            "There are no JOINs or subqueries, and FROM always names one Google Ads resource. "
            "String literals use single quotes, enum literals are unquoted, and numeric filters use normal comparisons."
        ),
        notes=(
            "Metrics are only available on compatible resources, and most metric queries need a date filter.",
            "Use AND/OR carefully; incompatible metrics and segments fail with query errors.",
        ),
        see_also=("primary-field-requirement", "common-errors", "segment-compatibility"),
    ),
    KBEntry(
        id="date-range-presets",
        category="syntax",
        question="What date range presets are available?",
        keywords=("date", "range", "preset", "during", "last_30_days", "today", "all_time"),
        answer=(
            "Use segments.date DURING with TODAY, YESTERDAY, LAST_7_DAYS, LAST_14_DAYS, "
            "LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, or ALL_TIME."
        ),
        queries=(
            q(
                "Last 30 days clicks by campaign",
                "SELECT campaign.id, metrics.clicks FROM campaign WHERE segments.date DURING LAST_30_DAYS",
                "campaign.id",
            ),
        ),
        notes=("ALL_TIME does not work on all resources. change_event has a 30-day maximum lookback.",),
        see_also=("date-range-custom", "change-history"),
    ),
    KBEntry(
        id="date-range-custom",
        category="filters",
        question="How do I use a custom date range?",
        keywords=("custom", "date", "range", "between", "start", "end", "yyyy-mm-dd"),
        answer=(
            "Use WHERE segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'. Both dates are "
            "required and the range is inclusive."
        ),
        queries=(
            q(
                "January campaign metrics",
                "SELECT campaign.id, campaign.name, metrics.clicks, metrics.cost_micros FROM campaign WHERE segments.date BETWEEN '2025-01-01' AND '2025-01-31'",
                "campaign.id",
            ),
        ),
        notes=("Date strings must be real calendar dates in YYYY-MM-DD format.",),
        see_also=("date-range-presets",),
    ),
    KBEntry(
        id="primary-field-requirement",
        category="errors",
        question="Why do I get EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE?",
        keywords=("expected_referenced", "referenced", "primary", "field", "select", "clause", "missing", "id"),
        answer=(
            "Include the primary field for the resource you query or reference. Common primaries: "
            + "; ".join(f"{resource} -> {field}" for resource, field in PRIMARY_FIELDS.items())
            + "."
        ),
        queries=(
            q(
                "Correct campaign query with primary field",
                "SELECT campaign.id, campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS",
                "campaign.id",
            ),
        ),
        notes=("This is the most common GAQL error when an LLM writes queries from memory.",),
        see_also=("common-errors", "available-resources"),
    ),
    KBEntry(
        id="resource-name-format",
        category="filters",
        question="What is the format of a resource_name?",
        keywords=("resource", "resource_name", "format", "customers", "adgroupads", "criteria", "labels"),
        answer=(
            "Common formats: customers/{customer_id}/campaigns/{campaign_id}; "
            "customers/{customer_id}/adGroups/{ad_group_id}; "
            "customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}; "
            "customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}; "
            "customers/{customer_id}/campaignBudgets/{budget_id}; "
            "customers/{customer_id}/labels/{label_id}."
        ),
        notes=("Customer IDs are digits only, no dashes.",),
        see_also=("primary-field-requirement", "filters-operators"),
    ),
    KBEntry(
        id="filters-operators",
        category="filters",
        question="How do filters and operators work in GAQL?",
        keywords=("filter", "where", "operators", "in", "between", "contains", "enum", "literal"),
        answer=(
            "WHERE supports equality, comparisons, IN lists, BETWEEN ranges, DURING date presets, "
            "LIKE, CONTAINS ANY, CONTAINS ALL, and CONTAINS NONE where a field allows it. "
            "String literals use single quotes; enum values such as ENABLED are unquoted."
        ),
        queries=(
            q(
                "Enabled campaigns in a set",
                "SELECT campaign.id, campaign.name FROM campaign WHERE campaign.status = ENABLED AND campaign.id IN (111, 222)",
                "campaign.id",
            ),
        ),
        notes=("Use describe_google_ads_resource to verify filterable=true before adding a field to WHERE.",),
    ),
    KBEntry(
        id="pagination-patterns",
        category="pagination",
        question="How does GAQL pagination work?",
        keywords=("pagination", "max_rows", "page_size", "page_token", "limit", "next"),
        answer=(
            "Google Ads search supports page_token for API paging. Search responses use Google's "
            "fixed 10,000-row page size, and setting request.page_size is rejected by the API. "
            "This MCP uses max_rows as a total row cap and injects a GAQL LIMIT when your query "
            "does not already have one. The older page_size parameter is only a deprecated alias "
            "for max_rows; it is not rows per API page. Use page_token only when you deliberately "
            "avoid MCP-injected limits, or when your own GAQL LIMIT is at least Google's fixed "
            "10,000-row API page size. GAQL has no OFFSET clause, and this MCP rejects OFFSET "
            "before sending the query to Google Ads."
        ),
        queries=(
            q(
                "Small first page",
                "SELECT campaign.id, campaign.name FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY campaign.id LIMIT 100",
                "campaign.id",
            ),
        ),
        notes=(
            "For larger reports, raise max_rows or provide your own GAQL LIMIT; "
            "do not rely on page_size as a page length.",
            "When an injected limit is reached, the response marks has_more as unknown_when_limit_reached.",
        ),
    ),
    KBEntry(
        id="available-resources",
        category="resources",
        question="What resources are available in GAQL?",
        keywords=("resources", "campaign", "ad_group", "keyword_view", "asset", "billing", "product_link"),
        answer=(
            "Core reporting: campaign, ad_group, ad_group_ad, keyword_view, ad_group_criterion, "
            "search_term_view. Segment views: geographic_view, age_range_view, gender_view, "
            "income_range_view, parental_status_view, ad_group_audience_view, group_placement_view. "
            "Entities: campaign_budget, bidding_strategy, label, asset, asset_group, asset_group_asset, "
            "user_list, conversion_action, recommendation. Other/special: shopping_performance_view, "
            "video, landing_page_view, call_view, change_event, product_link, account_budget, billing_setup."
        ),
        notes=("Not every resource supports metrics. Check no-metrics-resources before adding metric fields.",),
        see_also=("no-metrics-resources", "primary-field-requirement"),
    ),
    KBEntry(
        id="segment-compatibility",
        category="segments",
        question="Which segments can I use together and what cannot be combined?",
        keywords=("segments", "segment", "hour", "day_of_week", "date", "device", "slot", "shopping"),
        answer=(
            "Common segments include segments.date, hour, day_of_week, week, month, device, slot, "
            "product_item_id, product_title, and network. Adding a segment changes the grain: one row "
            "per segment value rather than an aggregate total."
        ),
        notes=(
            "segments.hour cannot combine with segments.date in many report queries.",
            "segments.slot is search-only. Shopping product segments belong on shopping resources.",
        ),
        see_also=("common-errors", "shopping-performance", "hour-of-day"),
    ),
    KBEntry(
        id="metric-field-names",
        category="metrics",
        question="What are the exact field names for common metrics?",
        keywords=("metrics", "field", "cost", "cpc", "conversion", "ctr", "impression", "quality", "score"),
        answer=(
            "Common fields: metrics.impressions, clicks, cost_micros, average_cpc, average_cost, ctr, "
            "conversions, all_conversions, conversions_value, all_conversions_value, cost_per_conversion, "
            "conversion_rate, engagements, video_views, view_rate, search_impression_share, "
            "search_budget_lost_impression_share, search_rank_lost_impression_share, "
            "search_top_impression_share, search_absolute_top_impression_share. Keyword quality fields "
            "live under ad_group_criterion.quality_info."
        ),
        notes=(
            "Cost fields are micros; divide by 1,000,000 for account currency.",
            "CTR and impression share fields are fractions. Impression share can be null with low volume.",
        ),
        see_also=("keyword-metrics", "impression-share-null", "conversion-fields"),
    ),
    KBEntry(
        id="campaign-metrics",
        category="reporting",
        question="How do I get campaign performance metrics?",
        keywords=("campaign", "metrics", "performance", "cost", "roas", "cpa", "daily"),
        answer="Use the campaign resource with campaign.id in SELECT and a date filter.",
        queries=(
            q("Last 30 days all campaigns", "SELECT campaign.id, campaign.name, campaign.status, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.ctr, metrics.average_cpc, metrics.conversions, metrics.cost_per_conversion, metrics.search_impression_share FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC", "campaign.id"),
            q("Specific campaign by ID", "SELECT campaign.id, campaign.name, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE campaign.id = 1234567890 AND segments.date DURING LAST_7_DAYS", "campaign.id"),
            q("Enabled only this month", "SELECT campaign.id, campaign.name, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE campaign.status = ENABLED AND segments.date DURING THIS_MONTH", "campaign.id"),
            q("Daily breakdown", "SELECT campaign.id, campaign.name, segments.date, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY segments.date DESC", "campaign.id"),
        ),
        see_also=("ad-group-metrics", "device-performance", "auction-insights"),
    ),
    KBEntry(
        id="ad-group-metrics",
        category="reporting",
        question="How do I get ad group performance metrics?",
        keywords=("ad", "group", "ad_group", "metrics", "performance"),
        answer="Use FROM ad_group and include ad_group.id plus campaign.id for context.",
        queries=(
            q("Last 30 days ad groups", "SELECT ad_group.id, ad_group.name, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM ad_group WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC", "ad_group.id"),
            q("Ad groups in one campaign", "SELECT ad_group.id, ad_group.name, campaign.id, metrics.impressions, metrics.clicks FROM ad_group WHERE campaign.id = 1234567890 AND segments.date DURING LAST_7_DAYS", "ad_group.id"),
        ),
        see_also=("campaign-metrics", "keyword-metrics"),
    ),
    KBEntry(
        id="keyword-metrics",
        category="reporting",
        question="How do I get keyword performance including Quality Score?",
        keywords=("keyword", "quality", "score", "qs", "keyword_view", "match", "bid"),
        answer=(
            "Use keyword_view and include ad_group_criterion.criterion_id. Quality Score fields are "
            "on ad_group_criterion.quality_info and may be absent when volume is too low."
        ),
        queries=(
            q("All keywords with QS", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.quality_info.quality_score, ad_group_criterion.quality_info.search_predicted_ctr, ad_group_criterion.quality_info.creative_quality_score, ad_group_criterion.quality_info.post_click_quality_score, ad_group.id, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.average_cpc, metrics.conversions FROM keyword_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.impressions DESC", "ad_group_criterion.criterion_id"),
            q("Exact keywords only", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group.id, campaign.id, metrics.clicks, metrics.cost_micros FROM keyword_view WHERE ad_group_criterion.keyword.match_type = EXACT AND segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
        ),
        notes=("Quality Score is 1-10 and can be missing for low-impression keywords.",),
        see_also=("search-terms-report", "metric-field-names"),
    ),
    KBEntry(
        id="search-terms-report",
        category="reporting",
        question="How do I get the search terms report?",
        keywords=("search", "terms", "query", "search_term_view", "match"),
        answer="Use search_term_view. Include search_term_view.search_term, status, ad_group.id, and campaign.id.",
        queries=(
            q("Search terms last 30 days", "SELECT search_term_view.search_term, search_term_view.status, ad_group.id, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM search_term_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC", "search_term_view.search_term"),
            q("Search terms for one campaign", "SELECT search_term_view.search_term, search_term_view.status, ad_group.id, campaign.id, metrics.clicks FROM search_term_view WHERE campaign.id = 1234567890 AND segments.date DURING LAST_14_DAYS", "search_term_view.search_term"),
        ),
        notes=("ALL_TIME is supported here but not on all resources.",),
        see_also=("keyword-metrics", "campaign-metrics"),
    ),
    KBEntry(
        id="auction-insights",
        category="reporting",
        question="How do I get auction insights or impression share data?",
        keywords=("auction", "insights", "impression", "share", "top", "rank", "budget", "competitor"),
        answer="Use campaign-level impression share metrics. Competitor names and overlap rates are not exposed by the API.",
        queries=(
            q("Enabled campaigns impression share", "SELECT campaign.id, campaign.name, metrics.search_impression_share, metrics.search_budget_lost_impression_share, metrics.search_rank_lost_impression_share, metrics.search_top_impression_share, metrics.search_absolute_top_impression_share FROM campaign WHERE campaign.status = ENABLED AND segments.date DURING LAST_30_DAYS ORDER BY metrics.search_impression_share ASC", "campaign.id"),
            q("Campaign IS last 7 days", "SELECT campaign.id, campaign.name, metrics.search_impression_share, metrics.search_rank_lost_impression_share FROM campaign WHERE segments.date DURING LAST_7_DAYS", "campaign.id"),
        ),
        notes=("Competitor domains and overlap metrics are not available via Google Ads API GAQL.",),
        see_also=("impression-share-null", "campaign-metrics"),
    ),
    KBEntry(
        id="device-performance",
        category="reporting",
        question="How do I get device performance?",
        keywords=("device", "mobile", "desktop", "tablet", "connected_tv"),
        answer="Use segments.device on campaign or ad_group resources. Values include MOBILE, DESKTOP, TABLET, CONNECTED_TV, and OTHER.",
        queries=(
            q("Campaign by device", "SELECT campaign.id, campaign.name, segments.device, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS", "campaign.id"),
            q("Ad groups by device", "SELECT ad_group.id, campaign.id, segments.device, metrics.clicks, metrics.cost_micros FROM ad_group WHERE segments.date DURING LAST_14_DAYS", "ad_group.id"),
        ),
        see_also=("campaign-metrics",),
    ),
    KBEntry(
        id="geo-performance",
        category="reporting",
        question="How do I get geo performance?",
        keywords=("geo", "geographic", "location", "country", "city", "region"),
        answer="Use geographic_view. It returns criterion IDs, not readable names; map IDs through geo_target_constant or a local lookup.",
        queries=(
            q("Geo by country criterion", "SELECT campaign.id, geographic_view.country_criterion_id, metrics.impressions, metrics.clicks, metrics.cost_micros FROM geographic_view WHERE segments.date DURING LAST_30_DAYS", "campaign.id"),
            q("Geo for one campaign", "SELECT campaign.id, geographic_view.country_criterion_id, metrics.conversions, metrics.cost_micros FROM geographic_view WHERE campaign.id = 1234567890 AND segments.date DURING LAST_30_DAYS", "campaign.id"),
        ),
        notes=(
            "This MCP contains a local geo target lookup for common IDs, an optional "
            "GOOGLE_ADS_GEO_TARGETS_CSV runtime override, and a refresh script.",
        ),
        see_also=("resource-name-format",),
    ),
    KBEntry(
        id="hour-of-day",
        category="reporting",
        question="How do I get hour of day performance?",
        keywords=("hour", "daypart", "dayparting", "schedule", "0-23"),
        answer="Use segments.hour, which returns values 0 through 23.",
        queries=(
            q("Campaign by hour", "SELECT campaign.id, segments.hour, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY segments.hour", "campaign.id"),
            q("Ad group by hour", "SELECT ad_group.id, campaign.id, segments.hour, metrics.clicks, metrics.conversions FROM ad_group WHERE segments.date DURING LAST_7_DAYS ORDER BY segments.hour", "ad_group.id"),
        ),
        notes=("Do not combine segments.hour and segments.day_of_week in the same query.",),
        see_also=("day-of-week", "segment-compatibility"),
    ),
    KBEntry(
        id="day-of-week",
        category="reporting",
        question="How do I get day of week performance?",
        keywords=("day", "week", "weekday", "monday", "sunday"),
        answer="Use segments.day_of_week. Values are MONDAY through SUNDAY.",
        queries=(
            q("Campaign by day of week", "SELECT campaign.id, segments.day_of_week, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY segments.day_of_week", "campaign.id"),
            q("Ad group by day of week", "SELECT ad_group.id, campaign.id, segments.day_of_week, metrics.conversions FROM ad_group WHERE segments.date DURING LAST_30_DAYS", "ad_group.id"),
        ),
        notes=("Do not combine segments.hour and segments.day_of_week in the same query.",),
        see_also=("hour-of-day",),
    ),
    KBEntry(
        id="age-range",
        category="reporting",
        question="How do I get age range performance?",
        keywords=("age", "range", "demographic", "18", "24", "65"),
        answer="Use age_range_view and ad_group_criterion.age_range.type.",
        queries=(
            q("Age range performance", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.age_range.type, ad_group.id, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros FROM age_range_view WHERE segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
            q("Age conversions", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.age_range.type, campaign.id, metrics.conversions FROM age_range_view WHERE segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
        ),
        notes=("Values include AGE_RANGE_18_24 through AGE_RANGE_65_UP and AGE_RANGE_UNDETERMINED.",),
    ),
    KBEntry(
        id="gender",
        category="reporting",
        question="How do I get gender performance?",
        keywords=("gender", "male", "female", "undetermined", "demographic"),
        answer="Use gender_view and ad_group_criterion.gender.type.",
        queries=(
            q("Gender performance", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.gender.type, ad_group.id, campaign.id, metrics.impressions, metrics.clicks FROM gender_view WHERE segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
            q("Gender conversions", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.gender.type, campaign.id, metrics.conversions FROM gender_view WHERE segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
        ),
        notes=("Values include MALE, FEMALE, and UNDETERMINED.",),
    ),
    KBEntry(
        id="parental-status",
        category="reporting",
        question="How do I get parental status performance?",
        keywords=("parental", "parent", "not_a_parent", "demographic"),
        answer="Use parental_status_view and ad_group_criterion.parental_status.type.",
        queries=(
            q("Parental status performance", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.parental_status.type, ad_group.id, campaign.id, metrics.impressions, metrics.clicks FROM parental_status_view WHERE segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
            q("Parental status conversions", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.parental_status.type, campaign.id, metrics.conversions FROM parental_status_view WHERE segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
        ),
        notes=("Values include PARENT, NOT_A_PARENT, and UNDETERMINED.",),
    ),
    KBEntry(
        id="household-income",
        category="reporting",
        question="How do I get household income performance?",
        keywords=("household", "income", "hhi", "demographic", "top", "lower"),
        answer="Use income_range_view and ad_group_criterion.income_range.type.",
        queries=(
            q("Household income performance", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.income_range.type, ad_group.id, campaign.id, metrics.impressions, metrics.clicks FROM income_range_view WHERE segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
            q("Household income cost", "SELECT ad_group_criterion.criterion_id, ad_group_criterion.income_range.type, campaign.id, metrics.cost_micros, metrics.conversions FROM income_range_view WHERE segments.date DURING LAST_30_DAYS", "ad_group_criterion.criterion_id"),
        ),
        notes=("Values include INCOME_RANGE_0_50 through INCOME_RANGE_90_UP and UNDETERMINED.",),
    ),
    KBEntry(
        id="audience-performance",
        category="audiences",
        question="How do I get audience performance?",
        keywords=("audience", "ad_group_audience_view", "user_list", "remarketing", "in-market"),
        answer="Use ad_group_audience_view and include user_list.id in SELECT.",
        queries=(
            q("Audience performance", "SELECT user_list.id, user_list.name, campaign.id, ad_group.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM ad_group_audience_view WHERE segments.date DURING LAST_30_DAYS", "user_list.id"),
            q("Audience conversions", "SELECT user_list.id, user_list.name, campaign.id, metrics.conversions, metrics.conversions_value FROM ad_group_audience_view WHERE segments.date DURING LAST_30_DAYS", "user_list.id"),
        ),
        see_also=("manager-account-limits",),
    ),
    KBEntry(
        id="placement-report",
        category="reporting",
        question="How do I get display placement performance?",
        keywords=("placement", "gdn", "display", "website", "app", "group_placement_view"),
        answer="Use group_placement_view for Display placements. The primary field is group_placement_view.placement.",
        queries=(
            q("Placement report", "SELECT group_placement_view.placement, campaign.id, ad_group.id, metrics.impressions, metrics.clicks, metrics.cost_micros FROM group_placement_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC", "group_placement_view.placement"),
            q("Placement conversions", "SELECT group_placement_view.placement, campaign.id, metrics.conversions FROM group_placement_view WHERE segments.date DURING LAST_30_DAYS", "group_placement_view.placement"),
        ),
    ),
    KBEntry(
        id="shopping-performance",
        category="shopping",
        question="How do I get Shopping product performance?",
        keywords=("shopping", "product", "item", "title", "brand", "category", "merchant"),
        answer="Use shopping_performance_view and product segments such as product_item_id, product_title, product_brand, and product_category_level1.",
        queries=(
            q("Shopping product report", "SELECT campaign.id, segments.product_item_id, segments.product_title, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM shopping_performance_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC", "campaign.id"),
            q("Shopping brand report", "SELECT campaign.id, segments.product_brand, segments.product_category_level1, metrics.clicks, metrics.cost_micros FROM shopping_performance_view WHERE segments.date DURING LAST_30_DAYS", "campaign.id"),
        ),
        notes=("Shopping product segments only belong on Shopping-compatible resources.",),
    ),
    KBEntry(
        id="video-performance",
        category="video",
        question="How do I get video campaign performance?",
        keywords=("video", "youtube", "views", "view_rate", "quartile", "watch"),
        answer="Use the video resource with video.id and YouTube video fields. Duration is exposed as video.duration_millis.",
        queries=(
            q("Video performance", "SELECT video.id, video.title, video.channel_id, video.duration_millis, metrics.video_trueview_views, metrics.video_trueview_view_rate, metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate, metrics.video_quartile_p100_rate FROM video WHERE segments.date DURING LAST_30_DAYS", "video.id"),
            q("Video cost and conversions", "SELECT video.id, video.title, metrics.impressions, metrics.video_trueview_views, metrics.cost_micros, metrics.conversions FROM video WHERE segments.date DURING LAST_30_DAYS", "video.id"),
        ),
        notes=("The current Google Ads field is video.duration_millis, not video.duration_seconds.",),
    ),
    KBEntry(
        id="landing-page-performance",
        category="reporting",
        question="How do I get landing page performance?",
        keywords=("landing", "page", "url", "final", "mobile"),
        answer="Use landing_page_view and include landing_page_view.unexpanded_final_url plus campaign.id.",
        queries=(
            q("Landing page report", "SELECT landing_page_view.unexpanded_final_url, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM landing_page_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC", "landing_page_view.unexpanded_final_url"),
            q("Landing pages this month", "SELECT landing_page_view.unexpanded_final_url, campaign.id, metrics.clicks FROM landing_page_view WHERE segments.date DURING THIS_MONTH", "landing_page_view.unexpanded_final_url"),
        ),
    ),
    KBEntry(
        id="call-details",
        category="reporting",
        question="How do I get call details?",
        keywords=("call", "details", "duration", "phone", "call_view"),
        answer="Use call_view. Date filter is required.",
        queries=(
            q("Call details", "SELECT call_view.resource_name, call_view.call_duration_seconds, call_view.call_status, call_view.call_tracking_display_location, campaign.id FROM call_view WHERE segments.date DURING LAST_30_DAYS", "call_view.resource_name"),
            q("Long calls", "SELECT call_view.resource_name, call_view.call_duration_seconds, campaign.id FROM call_view WHERE call_view.call_duration_seconds > 60 AND segments.date DURING LAST_30_DAYS", "call_view.resource_name"),
        ),
    ),
    KBEntry(
        id="change-history",
        category="change_history",
        question="How do I get change history?",
        keywords=("change", "history", "change_event", "user", "operation", "30"),
        answer="Use change_event. It has a hard 30-day maximum lookback regardless of date filter.",
        queries=(
            q("Recent changes", "SELECT change_event.resource_name, change_event.change_date_time, change_event.user_email, change_event.change_resource_name, change_event.change_resource_type, change_event.resource_change_operation FROM change_event WHERE change_event.change_date_time DURING LAST_14_DAYS LIMIT 500", "change_event.resource_name"),
            q("Campaign changes", "SELECT change_event.resource_name, change_event.change_date_time, change_event.change_resource_name, change_event.resource_change_operation FROM change_event WHERE change_event.change_resource_type = CAMPAIGN AND change_event.change_date_time DURING LAST_30_DAYS LIMIT 500", "change_event.resource_name"),
        ),
        notes=("Do not use ALL_TIME. Keep LIMIT around 100-500.",),
        see_also=("common-errors",),
    ),
    KBEntry(
        id="asset-performance",
        category="assets",
        question="How do I get RSA or PMax asset performance?",
        keywords=("asset", "performance", "pmax", "rsa", "label", "best", "good", "low"),
        answer="Use asset_group_asset for PMax asset group assets. performance_label values include BEST, GOOD, LOW, PENDING, and UNRATED.",
        queries=(
            q("Asset group asset performance", "SELECT asset.id, asset_group.id, asset_group_asset.field_type, asset_group_asset.primary_status, metrics.impressions, metrics.clicks, metrics.conversions FROM asset_group_asset WHERE segments.date DURING LAST_30_DAYS", "asset.id"),
            q("Limited assets", "SELECT asset.id, asset_group.id, asset_group_asset.field_type, asset_group_asset.primary_status FROM asset_group_asset WHERE asset_group_asset.primary_status = LIMITED AND segments.date DURING LAST_30_DAYS", "asset.id"),
        ),
    ),
    KBEntry(
        id="bidding-strategy-report",
        category="reporting",
        question="How do I get bidding strategy performance?",
        keywords=("bidding", "strategy", "target_cpa", "target_roas", "maximize", "manual"),
        answer="Use campaign.bidding_strategy_type as the campaign-level segment/dimension.",
        queries=(
            q("Bidding strategy by campaign", "SELECT campaign.id, campaign.name, campaign.bidding_strategy_type, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS", "campaign.id"),
            q("Target CPA campaigns", "SELECT campaign.id, campaign.name, campaign.bidding_strategy_type, metrics.cost_per_conversion, metrics.conversions FROM campaign WHERE campaign.bidding_strategy_type = TARGET_CPA AND segments.date DURING LAST_30_DAYS", "campaign.id"),
        ),
        notes=("Common values include TARGET_CPA, TARGET_ROAS, MAXIMIZE_CONVERSIONS, MAXIMIZE_CONVERSION_VALUE, MANUAL_CPC, and TARGET_IMPRESSION_SHARE. target_roas is a ratio, so 4.0 means 400%.",),
    ),
    KBEntry(
        id="no-metrics-resources",
        category="limitations",
        question="Which resources do not support metrics?",
        keywords=("no", "metrics", "resources", "customer_client", "billing", "label", "shared_set"),
        answer=(
            "Do not add metrics fields to customer_client, product_link, account_budget, billing_setup, "
            "shared_set, label, shared_criterion, or campaign_shared_set."
        ),
        notes=("Use these resources for structure/configuration, not performance reporting.",),
        see_also=("available-resources", "common-errors"),
    ),
    KBEntry(
        id="manager-account-limits",
        category="limitations",
        question="What cannot be done from a manager or MCC account?",
        keywords=("manager", "mcc", "leaf", "customer", "limits", "mutate", "metrics"),
        answer=(
            "Metric queries must use a leaf customer ID. Manager accounts are mainly for customer_client "
            "hierarchy traversal. Mutate operations require the target leaf account."
        ),
        notes=("Customer IDs should be digits only, without dashes.",),
        see_also=("primary-field-requirement",),
    ),
    KBEntry(
        id="impression-share-null",
        category="limitations",
        question="Why are impression share fields returning null?",
        keywords=("impression", "share", "null", "threshold", "insufficient", "budget", "rank"),
        answer=(
            "Search impression share fields require enough auction volume. Below Google's privacy or "
            "minimum-data thresholds, they return null."
        ),
        notes=("Impression share should not be segmented by hour or day of week.",),
        see_also=("auction-insights", "metric-field-names"),
    ),
    KBEntry(
        id="conversion-fields",
        category="conversions",
        question="What is the difference between conversions and all_conversions?",
        keywords=("conversion", "conversions", "all_conversions", "value", "include", "metric"),
        answer=(
            "metrics.conversions counts only conversion actions with include_in_conversions_metric = TRUE. "
            "metrics.all_conversions counts broader conversion activity including actions excluded from the "
            "main conversions column. Value fields follow the same split."
        ),
        queries=(
            q("Conversion action settings", "SELECT conversion_action.id, conversion_action.name, conversion_action.include_in_conversions_metric, conversion_action.category, conversion_action.status FROM conversion_action", "conversion_action.id"),
        ),
        see_also=("metric-field-names",),
    ),
    KBEntry(
        id="common-errors",
        category="errors",
        question="What are the most common GAQL errors and how do I fix them?",
        keywords=("errors", "invalid_field_name", "field_not_selectable", "prohibited", "quota", "query_error"),
        answer=(
            "EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE means add the primary field. INVALID_FIELD_NAME "
            "usually means typo or wrong resource. FIELD_NOT_SELECTABLE/FILTERABLE means the field exists "
            "but cannot be used in that clause. PROHIBITED_FIELD_COMBINATION means incompatible fields or "
            "segments. RESOURCE_EXHAUSTED means quota/rate limits. QUERY_ERROR means malformed GAQL."
        ),
        notes=(
            "Use describe_google_ads_resource to check selectable and filterable flags.",
            "String literals use single quotes; enum values are unquoted.",
        ),
        see_also=("primary-field-requirement", "segment-compatibility", "no-metrics-resources"),
    ),
)


ENTRY_BY_ID = {entry.id: entry for entry in ENTRIES}
CATEGORIES = tuple(sorted({entry.category for entry in ENTRIES}))


def total_entry_count() -> int:
    return len(ENTRIES)


def _tokens(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9_]+", text.lower().replace("-", "_")))


def search(question: str, category: str | None = None) -> list[KBEntry]:
    """Return the top 5 matching entries by deterministic keyword overlap."""

    question_tokens = _tokens(question)
    candidates = [entry for entry in ENTRIES if category is None or entry.category == category]
    scored: list[tuple[int, int, KBEntry]] = []
    for index, entry in enumerate(candidates):
        haystack = _tokens(" ".join((entry.id, entry.question, entry.answer, " ".join(entry.keywords))))
        overlap = len(question_tokens & haystack)
        if overlap:
            scored.append((overlap, -index, entry))
    scored.sort(reverse=True)
    matches = [entry for _, _, entry in scored[:5]]
    return matches or [ENTRY_BY_ID["gaql-syntax"]]
