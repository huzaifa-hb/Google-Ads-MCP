"""Friendly MCP tool catalog.

The raw Google Ads API is huge. This catalog gives agents stable, memorable tool
names while the dispatcher routes each tool to GAQL, generic mutate/service calls,
or an explicit unsupported-capability response.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

ToolMode = Literal[
    "query",
    "report",
    "mutate",
    "negative_keyword",
    "raw_gaql",
    "service",
    "unsupported",
]


@dataclass(frozen=True)
class FriendlyToolSpec:
    name: str
    category: str
    description: str
    mode: ToolMode
    resource: str | None = None
    primary_field: str | None = None
    fields: tuple[str, ...] = ()
    notes: str | None = None


TOOL_GROUPS: dict[str, list[tuple[str, str]]] = {
    "account": [
        ("get_account_info", "Account name, currency, time zone, tracking, and auto-tagging status."),
        ("list_customers", "List accessible leaf customer accounts."),
        ("get_mcc_hierarchy", "Traverse manager account hierarchy with parent and child links."),
        ("get_account_settings", "Account-level tracking and conversion settings."),
        ("list_linked_accounts", "List Analytics, Merchant Center, Search Console, and product links."),
        ("get_account_budget", "Read account-level budgets and proposals."),
        ("create_account_budget_proposal", "Create an account-level budget proposal."),
        ("list_invoices", "List billing invoices. Requires payload.billing_setup; call get_billing_setup first."),
        ("download_invoice_pdf", "Return invoice PDF metadata or URL when available from the API."),
        ("get_billing_setup", "Read billing setup details."),
    ],
    "campaigns": [
        ("list_campaigns", "List campaigns with status, type, budget, and bidding strategy."),
        ("get_campaign", "Get one campaign by id or resource name."),
        ("create_search_campaign", "Create a Search campaign from Google Ads mutate operations."),
        ("create_display_campaign", "Create a Display campaign from Google Ads mutate operations."),
        ("create_video_campaign", "Create a Video campaign from Google Ads mutate operations."),
        ("create_shopping_campaign", "Create a Shopping campaign from Google Ads mutate operations."),
        ("create_pmax_campaign", "Create a Performance Max campaign from mutate operations."),
        ("create_demand_gen_campaign", "Create a Demand Gen campaign from mutate operations."),
        ("create_app_campaign", "Create an App campaign from mutate operations."),
        ("create_smart_campaign", "Create a Smart campaign from mutate operations when supported."),
        ("update_campaign", "Update campaign name, status, dates, tracking, or URL options."),
        ("pause_campaign", "Pause a campaign."),
        ("enable_campaign", "Enable a campaign."),
        ("remove_campaign", "Remove a campaign."),
        ("update_network_settings", "Update search/display/search partner network settings."),
        ("set_geo_targeting", "Add or remove targeted and excluded campaign locations."),
        ("set_language_targeting", "Add or remove campaign language criteria."),
        ("set_ad_scheduling", "Set campaign dayparting criteria and bid modifiers."),
        ("set_device_bid_adjustments", "Set campaign device bid modifiers."),
        ("apply_campaign_label", "Attach a label to a campaign."),
        ("remove_campaign_label", "Detach a label from a campaign."),
        ("create_campaign_draft", "Create a campaign draft."),
        ("promote_campaign_draft", "Promote a campaign draft."),
        ("create_campaign_experiment", "Create a campaign experiment."),
        ("graduate_campaign_experiment", "Graduate an experiment."),
        ("end_campaign_experiment", "End an experiment."),
    ],
    "budgets": [
        ("list_budgets", "List campaign budgets."),
        ("get_budget", "Get one campaign budget."),
        ("create_budget", "Create a campaign budget."),
        ("update_budget", "Update a campaign budget."),
        ("remove_budget", "Remove an unattached budget."),
        ("create_shared_budget", "Create a budget shared by campaigns."),
        ("update_shared_budget", "Update a shared budget."),
        ("link_budget_to_campaign", "Attach a shared budget to a campaign."),
        ("list_shared_budgets", "List shared campaign budgets."),
    ],
    "ad_groups": [
        ("list_ad_groups", "List ad groups, optionally filtered by campaign."),
        ("get_ad_group", "Get one ad group."),
        ("create_ad_group", "Create an ad group."),
        ("update_ad_group", "Update ad group name, status, or bids."),
        ("pause_ad_group", "Pause an ad group."),
        ("enable_ad_group", "Enable an ad group."),
        ("remove_ad_group", "Remove an ad group."),
        ("apply_ad_group_label", "Attach a label to an ad group."),
        ("remove_ad_group_label", "Detach a label from an ad group."),
    ],
    "ads": [
        ("list_ads", "List ads by campaign, ad group, status, or type."),
        ("get_ad", "Get one ad with approval status."),
        ("create_responsive_search_ad", "Create a responsive search ad."),
        ("create_responsive_display_ad", "Create a responsive display ad."),
        ("create_call_ad", "Create a call ad."),
        ("create_app_ad", "Create an app ad."),
        ("create_video_ad", "Create a video ad."),
        ("create_demand_gen_ad", "Create a Demand Gen ad."),
        ("create_dynamic_search_ad", "Create a dynamic search ad."),
        ("create_shopping_product_ad", "Create a Shopping product ad."),
        ("create_hotel_ad", "Create a Hotel ad when supported."),
        ("pause_ad", "Pause an ad."),
        ("enable_ad", "Enable an ad."),
        ("remove_ad", "Remove an ad."),
        ("get_ad_approval_status", "Get policy review status and disapproval reasons."),
        ("get_ad_asset_performance", "Get RSA asset serving rate and performance labels."),
        ("apply_ad_label", "Attach a label to an ad."),
        ("remove_ad_label", "Detach a label from an ad."),
    ],
    "keywords": [
        ("list_keywords", "List keywords by campaign, ad group, match type, or status."),
        ("get_keyword", "Get one keyword with bid and quality score fields."),
        ("add_keywords", "Add one or more keywords to an ad group."),
        ("update_keyword_bid", "Update CPC bid on a keyword."),
        ("pause_keyword", "Pause a keyword."),
        ("enable_keyword", "Enable a keyword."),
        ("remove_keywords", "Remove one or more keywords."),
        ("apply_keyword_label", "Attach a label to a keyword."),
        ("remove_keyword_label", "Detach a label from a keyword."),
        ("list_negative_keywords_ad_group", "List ad group-level negative keywords."),
        ("add_negative_keywords_ad_group", "Add ad group-level negative keywords."),
        ("remove_negative_keywords_ad_group", "Remove ad group-level negative keywords."),
        ("list_negative_keywords_campaign", "List campaign-level negative keywords."),
        ("add_negative_keywords_campaign", "Add campaign-level negative keywords."),
        ("remove_negative_keywords_campaign", "Remove campaign-level negative keywords."),
        ("list_shared_negative_keyword_lists", "List account-level shared negative keyword lists."),
        ("create_shared_negative_keyword_list", "Create a shared negative keyword list."),
        ("add_keywords_to_shared_list", "Add keywords to a shared negative list."),
        ("remove_keywords_from_shared_list", "Remove keywords from a shared negative list."),
        ("apply_shared_list_to_campaign", "Attach a shared negative list to a campaign."),
        ("remove_shared_list_from_campaign", "Detach a shared negative list from a campaign."),
        ("get_keyword_bid_estimates", "Get keyword CPC and traffic estimates when supported."),
        ("get_keyword_ideas", "Get Keyword Planner ideas."),
    ],
    "extensions": [
        ("list_extensions", "List assets/extensions by type and level."),
        ("get_extension", "Get one extension or asset."),
        ("create_sitelink", "Create a sitelink asset."),
        ("create_callout", "Create a callout asset."),
        ("create_structured_snippet", "Create a structured snippet asset."),
        ("create_call_extension", "Create a call asset."),
        ("create_price_extension", "Create a price asset."),
        ("create_promotion_extension", "Create a promotion asset."),
        ("create_app_extension", "Create an app asset."),
        ("create_image_extension", "Create an image asset extension."),
        ("create_lead_form_extension", "Create a lead form asset."),
        ("set_extension_scheduling", "Set extension scheduling."),
        ("update_extension_status", "Pause or enable an extension asset."),
        ("remove_extension", "Remove an extension asset."),
        ("get_extension_approval_status", "Get extension policy approval status."),
    ],
    "assets": [
        ("list_assets", "List reusable assets."),
        ("get_asset", "Get one asset with policy and performance data."),
        ("upload_image_asset", "Upload or create an image asset."),
        ("create_text_asset", "Create a text asset."),
        ("create_video_asset", "Create a YouTube video asset."),
        ("get_asset_performance", "Get asset serving performance."),
        ("get_asset_approval_status", "Get asset policy approval status."),
        ("remove_asset", "Remove an asset."),
    ],
    "bidding": [
        ("list_bidding_strategies", "List portfolio bidding strategies."),
        ("get_bidding_strategy", "Get one bidding strategy."),
        ("create_bidding_strategy", "Create a portfolio bidding strategy."),
        ("update_bidding_strategy", "Update a portfolio bidding strategy."),
        ("remove_bidding_strategy", "Remove an unused portfolio bidding strategy."),
        ("attach_bidding_strategy_to_campaign", "Attach portfolio strategy to campaign."),
        ("set_campaign_inline_bid_strategy", "Set campaign-level inline bid strategy."),
        ("get_bidding_strategy_report", "Report performance by bidding strategy."),
        ("set_audience_bid_adjustments", "Set audience bid modifiers."),
        ("set_demographic_bid_adjustments", "Set demographic bid modifiers."),
        ("set_ad_schedule_bid_adjustments", "Set ad schedule bid modifiers."),
        ("create_seasonal_bid_adjustment", "Create a seasonal conversion rate adjustment."),
    ],
    "targeting": [
        ("add_audience_to_campaign", "Add campaign audience targeting or observation."),
        ("add_audience_to_ad_group", "Add ad group audience targeting or observation."),
        ("remove_audience_from_campaign", "Remove campaign audience targeting."),
        ("remove_audience_from_ad_group", "Remove ad group audience targeting."),
        ("set_demographic_targeting", "Set age, gender, parental, or household targeting."),
        ("add_topic_targeting", "Add GDN topic targeting."),
        ("remove_topic_targeting", "Remove GDN topic targeting."),
        ("add_placement_targeting", "Add placement targeting."),
        ("add_placement_exclusions", "Add placement exclusions."),
        ("add_content_label_exclusions", "Add sensitive content exclusions."),
    ],
    "audiences": [
        ("list_audiences", "List user lists and audience resources."),
        ("get_audience", "Get one audience or user list."),
        ("create_customer_match_audience", "Create a Customer Match audience."),
        ("append_to_customer_match_audience", "Append hashed members to Customer Match."),
        ("remove_from_customer_match_audience", "Remove members from Customer Match."),
        ("create_website_remarketing_list", "Create website remarketing list."),
        ("create_youtube_remarketing_list", "Create YouTube remarketing list."),
        ("create_app_remarketing_list", "Create app remarketing list."),
        ("create_similar_audience", "Similar audiences are deprecated; returns replacement guidance."),
        ("create_combined_audience", "Create a combined audience."),
        ("create_custom_segment", "Create a custom segment."),
        ("get_audience_size_estimate", "Estimate audience reach when available."),
        ("update_audience", "Update audience or user list."),
        ("remove_audience", "Remove audience or user list."),
    ],
    "conversions": [
        ("list_conversion_actions", "List conversion actions."),
        ("get_conversion_action", "Get one conversion action."),
        ("create_conversion_action", "Create a conversion action."),
        ("update_conversion_action", "Update conversion action settings."),
        ("pause_conversion_action", "Pause conversion action."),
        ("remove_conversion_action", "Remove conversion action."),
        ("upload_offline_conversions", "Upload GCLID-based offline conversions."),
        ("upload_call_conversions", "Upload call conversions."),
        ("upload_store_visit_conversions", "Upload store visit conversions when eligible."),
        ("upload_enhanced_conversions", "Upload enhanced conversion user data."),
        ("get_conversion_attribution_settings", "Get attribution settings."),
        ("update_conversion_attribution_model", "Update conversion attribution model."),
    ],
    "shopping_pmax": [
        ("get_shopping_campaign_settings", "Get Merchant Center and Shopping campaign settings."),
        ("create_listing_group_tree", "Create a Shopping listing group tree."),
        ("update_listing_group", "Update a listing group node."),
        ("remove_listing_group", "Remove a listing group node."),
        ("list_pmax_asset_groups", "List PMax asset groups."),
        ("get_pmax_asset_group", "Get one PMax asset group."),
        ("create_pmax_asset_group", "Create a PMax asset group."),
        ("update_pmax_asset_group", "Update a PMax asset group."),
        ("remove_pmax_asset_group", "Remove a PMax asset group."),
        ("set_pmax_audience_signals", "Set PMax audience signals and search themes."),
        ("get_pmax_search_term_themes", "Get PMax search term themes where exposed."),
        ("get_pmax_asset_group_performance", "Report PMax asset group performance."),
        ("get_pmax_campaign_insights", "Report PMax campaign insights."),
    ],
    "reporting": [
        ("get_campaign_metrics", "Campaign metrics with preset or custom date ranges."),
        ("get_ad_group_metrics", "Ad group metrics with preset or custom date ranges."),
        ("get_ad_metrics", "Ad metrics with preset or custom date ranges."),
        ("get_keyword_metrics", "Keyword metrics plus quality score fields."),
        ("get_search_terms_report", "Search query performance report."),
        ("get_auction_insights", "Auction insight metrics."),
        ("get_device_performance", "Performance by device."),
        ("get_geo_performance", "Performance by geographic target id and readable name."),
        ("get_hour_of_day_performance", "Performance by hour of day."),
        ("get_day_of_week_performance", "Performance by day of week."),
        ("get_age_range_report", "Performance by age range."),
        ("get_gender_report", "Performance by gender."),
        ("get_parental_status_report", "Performance by parental status."),
        ("get_household_income_report", "Performance by household income."),
        ("get_audience_performance_report", "Performance by audience segment."),
        ("get_placement_report", "Display placement performance."),
        ("get_topic_report", "GDN topic performance."),
        ("get_ad_schedule_report", "Performance by scheduled time block."),
        ("get_asset_performance_report", "Asset performance for RSA and PMax."),
        ("get_video_performance_report", "Video performance report."),
        ("get_shopping_performance_report", "Shopping product performance."),
        ("get_display_performance_report", "Display network performance."),
        ("get_landing_page_report", "Landing page performance."),
        ("get_call_details_report", "Call details report."),
        ("get_change_history_report", "Change history report."),
        ("get_reach_frequency_report", "Reach and frequency report."),
        ("get_paid_organic_report", "Paid and organic report when Search Console is linked."),
        ("execute_gaql_query", "Execute raw GAQL for uncovered reporting needs."),
    ],
    "labels": [
        ("list_labels", "List account labels."),
        ("create_label", "Create a label."),
        ("update_label", "Update label name, color, or description."),
        ("remove_label", "Remove a label."),
        ("apply_label_to_campaign", "Attach label to campaigns."),
        ("apply_label_to_ad_group", "Attach label to ad groups."),
        ("apply_label_to_ad", "Attach label to ads."),
        ("apply_label_to_keyword", "Attach label to keywords."),
        ("remove_label_from_campaign", "Detach label from campaigns."),
        ("remove_label_from_ad_group", "Detach label from ad groups."),
        ("remove_label_from_ad", "Detach label from ads."),
        ("remove_label_from_keyword", "Detach label from keywords."),
    ],
    "recommendations": [
        ("list_recommendations", "List pending Google recommendations."),
        ("apply_recommendation", "Apply a recommendation."),
        ("dismiss_recommendation", "Dismiss a recommendation."),
        ("get_recommendation_types", "List supported recommendation type metadata."),
    ],
    "feeds": [
        ("create_dsa_page_feed", "Create a Dynamic Search Ads page feed."),
        ("update_dsa_page_feed", "Update DSA page feed rows."),
        ("list_dsa_page_feeds", "List DSA page feeds."),
        ("create_ad_customizer_feed", "Create ad customizer feed or attributes."),
        ("update_ad_customizer_feed", "Update ad customizer rows."),
        ("set_custom_parameters", "Set URL custom parameters."),
    ],
    "planning": [
        ("get_reach_forecast", "Get Reach Planner forecast where available."),
        ("get_ad_preview", "Get ad preview or serving simulation data when available."),
        ("get_ad_diagnosis", "Diagnose why an ad is not serving when API surface allows."),
    ],
    "bulk": [
        ("batch_mutate", "Run up to 5,000 mixed mutate operations."),
        ("bulk_pause_campaigns", "Pause campaigns in bulk."),
        ("bulk_enable_campaigns", "Enable campaigns in bulk."),
        ("bulk_update_bids", "Update keyword bids in bulk."),
        ("bulk_add_keywords", "Add keywords in bulk."),
        ("bulk_add_negative_keywords", "Add negative keywords in bulk."),
    ],
}


QUERY_RESOURCE_BY_TOOL: dict[str, tuple[str, tuple[str, ...], str]] = {
    "get_account_info": (
        "customer",
        ("customer.id", "customer.descriptive_name", "customer.currency_code", "customer.time_zone"),
        "customer.id",
    ),
    "get_account_settings": (
        "customer",
        ("customer.id", "customer.auto_tagging_enabled", "customer.final_url_suffix"),
        "customer.id",
    ),
    "list_customers": (
        "customer_client",
        (
            "customer_client.id",
            "customer_client.descriptive_name",
            "customer_client.manager",
            "customer_client.status",
        ),
        "customer_client.id",
    ),
    "get_mcc_hierarchy": (
        "customer_client",
        (
            "customer_client.id",
            "customer_client.descriptive_name",
            "customer_client.manager",
            "customer_client.level",
            "customer_client.status",
            "customer_client.client_customer",
        ),
        "customer_client.id",
    ),
    "list_campaigns": (
        "campaign",
        (
            "campaign.id",
            "campaign.name",
            "campaign.status",
            "campaign.advertising_channel_type",
            "campaign.campaign_budget",
            "campaign.bidding_strategy_type",
        ),
        "campaign.id",
    ),
    "list_budgets": (
        "campaign_budget",
        (
            "campaign_budget.id",
            "campaign_budget.name",
            "campaign_budget.amount_micros",
            "campaign_budget.delivery_method",
            "campaign_budget.explicitly_shared",
        ),
        "campaign_budget.id",
    ),
    "list_shared_budgets": (
        "campaign_budget",
        (
            "campaign_budget.id",
            "campaign_budget.name",
            "campaign_budget.amount_micros",
            "campaign_budget.explicitly_shared",
        ),
        "campaign_budget.id",
    ),
    "list_ad_groups": (
        "ad_group",
        ("ad_group.id", "ad_group.name", "ad_group.status", "ad_group.campaign"),
        "ad_group.id",
    ),
    "list_ads": (
        "ad_group_ad",
        ("ad_group_ad.ad.id", "ad_group_ad.status", "ad_group.id", "campaign.id"),
        "ad_group_ad.ad.id",
    ),
    "list_keywords": (
        "keyword_view",
        (
            "ad_group_criterion.criterion_id",
            "ad_group_criterion.keyword.text",
            "ad_group_criterion.keyword.match_type",
            "ad_group_criterion.status",
            "ad_group.id",
            "campaign.id",
        ),
        "ad_group_criterion.criterion_id",
    ),
    "list_assets": (
        "asset",
        ("asset.id", "asset.name", "asset.type", "asset.policy_summary.approval_status"),
        "asset.id",
    ),
    "list_bidding_strategies": (
        "bidding_strategy",
        (
            "bidding_strategy.id",
            "bidding_strategy.name",
            "bidding_strategy.type",
            "bidding_strategy.status",
        ),
        "bidding_strategy.id",
    ),
    "list_audiences": (
        "user_list",
        ("user_list.id", "user_list.name", "user_list.type", "user_list.size_for_search"),
        "user_list.id",
    ),
    "list_conversion_actions": (
        "conversion_action",
        (
            "conversion_action.id",
            "conversion_action.name",
            "conversion_action.category",
            "conversion_action.status",
        ),
        "conversion_action.id",
    ),
    "list_labels": (
        "label",
        ("label.id", "label.name", "label.status", "label.text_label.background_color"),
        "label.id",
    ),
    "list_recommendations": (
        "recommendation",
        ("recommendation.resource_name", "recommendation.type", "recommendation.impact"),
        "recommendation.resource_name",
    ),
    "list_pmax_asset_groups": (
        "asset_group",
        ("asset_group.id", "asset_group.name", "asset_group.status", "campaign.id"),
        "asset_group.id",
    ),
}

GET_ALIASES: dict[str, str] = {
    "get_campaign": "list_campaigns",
    "get_budget": "list_budgets",
    "get_ad_group": "list_ad_groups",
    "get_ad": "list_ads",
    "get_keyword": "list_keywords",
    "get_asset": "list_assets",
    "get_bidding_strategy": "list_bidding_strategies",
    "get_audience": "list_audiences",
    "get_conversion_action": "list_conversion_actions",
    "get_pmax_asset_group": "list_pmax_asset_groups",
}

SERVICE_TOOLS = {
    "list_linked_accounts",
    "get_account_budget",
    "list_invoices",
    "download_invoice_pdf",
    "get_billing_setup",
    "get_keyword_ideas",
    "get_keyword_bid_estimates",
    "get_reach_forecast",
    "get_ad_preview",
    "get_ad_diagnosis",
    "get_recommendation_types",
}

UNSUPPORTED_TOOLS: dict[str, str] = {
    "create_similar_audience": (
        "Similar audiences are no longer a generally available creation path in Google Ads. "
        "Use audience signals, optimized targeting, Customer Match, or custom segments."
    ),
    "get_topic_report": (
        "Topic performance fields are version and campaign-type sensitive. Use live metadata and "
        "planning_plan_gaql_query to build a topic-compatible GAQL query for the target account."
    ),
    "get_reach_frequency_report": (
        "Reach and frequency reporting is not a universal GAQL view. Use live metadata to confirm "
        "compatible reach/frequency fields before querying."
    ),
    "get_paid_organic_report": (
        "Paid and organic reporting depends on Search Console linkage and version-specific fields. "
        "Use live metadata before building this report."
    ),
    "upload_store_visit_conversions": (
        "Store visit conversion uploads are eligibility-gated and not available for most API users. "
        "Use google_ads_call_service if your account has the required service access."
    ),
}

REPORT_RESOURCES: dict[str, tuple[str, tuple[str, ...], str]] = {
    "get_campaign_metrics": ("campaign", ("campaign.id", "campaign.name"), "campaign.id"),
    "get_ad_group_metrics": (
        "ad_group",
        ("ad_group.id", "ad_group.name", "campaign.id"),
        "ad_group.id",
    ),
    "get_ad_metrics": (
        "ad_group_ad",
        ("ad_group_ad.ad.id", "ad_group.id", "campaign.id"),
        "ad_group_ad.ad.id",
    ),
    "get_keyword_metrics": (
        "keyword_view",
        (
            "ad_group_criterion.criterion_id",
            "ad_group_criterion.keyword.text",
            "ad_group_criterion.quality_info.quality_score",
            "ad_group_criterion.quality_info.search_predicted_ctr",
            "ad_group_criterion.quality_info.creative_quality_score",
            "ad_group_criterion.quality_info.post_click_quality_score",
            "ad_group.id",
            "campaign.id",
        ),
        "ad_group_criterion.criterion_id",
    ),
    "get_search_terms_report": (
        "search_term_view",
        ("search_term_view.search_term", "ad_group.id", "campaign.id"),
        "search_term_view.search_term",
    ),
    "get_auction_insights": (
        "campaign",
        ("campaign.id", "campaign.name"),
        "campaign.id",
    ),
    "get_device_performance": ("campaign", ("campaign.id", "segments.device"), "campaign.id"),
    "get_geo_performance": (
        "geographic_view",
        ("campaign.id", "geographic_view.country_criterion_id"),
        "campaign.id",
    ),
    "get_hour_of_day_performance": ("campaign", ("campaign.id", "segments.hour"), "campaign.id"),
    "get_day_of_week_performance": (
        "campaign",
        ("campaign.id", "segments.day_of_week"),
        "campaign.id",
    ),
    "get_age_range_report": (
        "age_range_view",
        ("campaign.id", "ad_group.id", "ad_group_criterion.age_range.type"),
        "ad_group_criterion.criterion_id",
    ),
    "get_gender_report": (
        "gender_view",
        ("campaign.id", "ad_group.id", "ad_group_criterion.gender.type"),
        "ad_group_criterion.criterion_id",
    ),
    "get_parental_status_report": (
        "parental_status_view",
        ("campaign.id", "ad_group.id", "ad_group_criterion.parental_status.type"),
        "ad_group_criterion.criterion_id",
    ),
    "get_household_income_report": (
        "household_income_view",
        ("campaign.id", "ad_group.id", "ad_group_criterion.income_range.type"),
        "ad_group_criterion.criterion_id",
    ),
    "get_audience_performance_report": (
        "audience_view",
        ("campaign.id", "ad_group.id", "user_list.id", "user_list.name"),
        "user_list.id",
    ),
    "get_placement_report": (
        "group_placement_view",
        ("campaign.id", "ad_group.id", "group_placement_view.placement"),
        "group_placement_view.placement",
    ),
    "get_asset_performance_report": (
        "asset_group_asset",
        ("asset.id", "asset_group.id", "asset_group_asset.performance_label"),
        "asset.id",
    ),
    "get_ad_asset_performance": (
        "ad_group_ad_asset_view",
        (
            "ad_group_ad_asset_view.resource_name",
            "ad_group_ad_asset_view.field_type",
            "ad_group_ad_asset_view.performance_label",
            "ad_group_ad.ad.id",
            "ad_group.id",
            "campaign.id",
        ),
        "ad_group_ad_asset_view.resource_name",
    ),
    "get_asset_performance": (
        "asset_group_asset",
        (
            "asset.id",
            "asset_group.id",
            "asset_group_asset.field_type",
            "asset_group_asset.performance_label",
            "campaign.id",
        ),
        "asset.id",
    ),
    "get_video_performance_report": ("video", ("video.id", "video.title"), "video.id"),
    "get_shopping_performance_report": (
        "shopping_performance_view",
        ("campaign.id", "segments.product_item_id", "segments.product_title"),
        "campaign.id",
    ),
    "get_landing_page_report": (
        "landing_page_view",
        ("landing_page_view.unexpanded_final_url", "campaign.id"),
        "landing_page_view.unexpanded_final_url",
    ),
    "get_call_details_report": (
        "call_view",
        ("call_view.resource_name", "call_view.call_duration_seconds", "campaign.id"),
        "call_view.resource_name",
    ),
    "get_change_history_report": (
        "change_event",
        (
            "change_event.resource_name",
            "change_event.change_date_time",
            "change_event.user_email",
            "change_event.change_resource_name",
        ),
        "change_event.resource_name",
    ),
    "get_ad_schedule_report": (
        "campaign",
        ("campaign.id", "campaign.name", "segments.day_of_week", "segments.hour"),
        "campaign.id",
    ),
    "get_display_performance_report": (
        "campaign",
        ("campaign.id", "campaign.name", "segments.ad_network_type"),
        "campaign.id",
    ),
    "get_bidding_strategy_report": (
        "bidding_strategy",
        ("bidding_strategy.id", "bidding_strategy.name", "bidding_strategy.type"),
        "bidding_strategy.id",
    ),
    "get_pmax_asset_group_performance": (
        "asset_group",
        ("asset_group.id", "asset_group.name", "asset_group.status", "campaign.id"),
        "asset_group.id",
    ),
}

DEFAULT_METRICS = (
    "metrics.impressions",
    "metrics.clicks",
    "metrics.cost_micros",
    "metrics.average_cost",
    "metrics.conversions",
    "metrics.conversions_value",
    "metrics.cost_per_conversion",
    "metrics.conversion_rate",
    "metrics.all_conversions",
    "metrics.all_conversions_value",
    "metrics.ctr",
    "metrics.average_cpc",
    "metrics.engagements",
    "metrics.video_views",
    "metrics.view_rate",
    "metrics.search_impression_share",
    "metrics.search_budget_lost_impression_share",
    "metrics.search_rank_lost_impression_share",
    "metrics.search_top_impression_share",
    "metrics.search_absolute_top_impression_share",
)


def _infer_mode(name: str) -> ToolMode:
    if name in UNSUPPORTED_TOOLS:
        return "unsupported"
    if name == "execute_gaql_query":
        return "raw_gaql"
    if "negative_keyword" in name or "shared_negative_keyword" in name or "shared_list" in name:
        return "negative_keyword"
    if name in REPORT_RESOURCES or name.endswith("_report") or name.endswith("_performance"):
        return "report"
    if name in SERVICE_TOOLS:
        return "service"
    if name.startswith(("list_", "get_")):
        return "query"
    return "mutate"


def _query_definition_for(name: str) -> tuple[str | None, tuple[str, ...], str | None]:
    alias = GET_ALIASES.get(name, name)
    resource, fields, primary = QUERY_RESOURCE_BY_TOOL.get(alias, (None, (), None))
    return resource, fields, primary


def build_tool_specs() -> tuple[FriendlyToolSpec, ...]:
    specs: list[FriendlyToolSpec] = []
    seen: set[str] = set()
    for category, entries in TOOL_GROUPS.items():
        for name, description in entries:
            if name in seen:
                continue
            seen.add(name)
            mode = _infer_mode(name)
            resource: str | None = None
            fields: tuple[str, ...] = ()
            primary_field: str | None = None
            notes = UNSUPPORTED_TOOLS.get(name)
            if mode == "query":
                resource, fields, primary_field = _query_definition_for(name)
                if resource is None:
                    mode = "service"
            elif mode == "report":
                if name not in REPORT_RESOURCES:
                    mode = "unsupported"
                    notes = (
                        "Report mapping is not defined. Use live metadata and "
                        "planning_plan_gaql_query to build this report safely."
                    )
                    resource, fields, primary_field = None, (), None
                else:
                    resource, base_fields, primary_field = REPORT_RESOURCES[name]
                    fields = base_fields + DEFAULT_METRICS
            specs.append(
                FriendlyToolSpec(
                    name=name,
                    category=category,
                    description=description,
                    mode=mode,
                    resource=resource,
                    primary_field=primary_field,
                    fields=fields,
                    notes=notes,
                )
            )
    return tuple(specs)


FRIENDLY_TOOL_SPECS = build_tool_specs()
FRIENDLY_TOOL_BY_NAME = {spec.name: spec for spec in FRIENDLY_TOOL_SPECS}
