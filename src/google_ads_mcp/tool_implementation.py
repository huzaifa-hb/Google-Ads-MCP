"""Implementation registry shared by dispatcher, catalog, and capability matrix.

Keep these groups as the source of truth for friendly tools with bespoke mutate
builders. Tools omitted from these sets are treated as raw operation templates
unless they are explicitly unsupported or routed through a service bridge.
"""

from __future__ import annotations


CAMPAIGN_CREATE_TOOLS = frozenset(
    {
        "create_search_campaign",
        "create_display_campaign",
        "create_shopping_campaign",
        "create_pmax_campaign",
        "create_demand_gen_campaign",
        "create_app_campaign",
    }
)

BUDGET_MUTATION_TOOLS = frozenset(
    {
        "create_budget",
        "create_shared_budget",
        "update_budget",
        "update_shared_budget",
        "remove_budget",
        "link_budget_to_campaign",
    }
)
BUDGET_CREATE_TOOLS = frozenset({"create_budget", "create_shared_budget"})
BUDGET_UPDATE_TOOLS = frozenset({"update_budget", "update_shared_budget"})

CAMPAIGN_MUTATION_TOOLS = frozenset(
    {
        "update_campaign",
        "update_network_settings",
        "bulk_pause_campaigns",
        "bulk_enable_campaigns",
        "pause_campaign",
        "enable_campaign",
        "remove_campaign",
    }
)
CAMPAIGN_BULK_STATUS_TOOLS = frozenset({"bulk_pause_campaigns", "bulk_enable_campaigns"})
CAMPAIGN_STATUS_TOOLS = frozenset({"pause_campaign", "enable_campaign"})

AD_GROUP_MUTATION_TOOLS = frozenset(
    {
        "create_ad_group",
        "update_ad_group",
        "pause_ad_group",
        "enable_ad_group",
        "remove_ad_group",
    }
)
AD_GROUP_STATUS_TOOLS = frozenset({"pause_ad_group", "enable_ad_group"})

AD_MUTATION_TOOLS = frozenset(
    {
        "create_responsive_search_ad",
        "pause_ad",
        "enable_ad",
        "remove_ad",
    }
)
AD_STATUS_TOOLS = frozenset({"pause_ad", "enable_ad"})

KEYWORD_MUTATION_TOOLS = frozenset(
    {
        "add_keywords",
        "bulk_add_keywords",
        "update_keyword_bid",
        "bulk_update_bids",
        "pause_keyword",
        "enable_keyword",
        "remove_keywords",
        "bulk_add_negative_keywords",
    }
)
KEYWORD_CREATE_TOOLS = frozenset({"add_keywords", "bulk_add_keywords"})
KEYWORD_BID_TOOLS = frozenset({"update_keyword_bid", "bulk_update_bids"})
KEYWORD_STATUS_TOOLS = frozenset({"pause_keyword", "enable_keyword"})

ASSET_MUTATION_TOOLS = frozenset(
    {
        "create_sitelink",
        "create_callout",
        "create_text_asset",
        "create_video_asset",
    }
)

LABEL_MUTATION_TOOLS = frozenset(
    {
        "create_label",
        "update_label",
        "remove_label",
        "apply_campaign_label",
        "remove_campaign_label",
        "apply_ad_group_label",
        "remove_ad_group_label",
        "apply_ad_label",
        "remove_ad_label",
        "apply_keyword_label",
        "remove_keyword_label",
        "apply_label_to_campaign",
        "apply_label_to_ad_group",
        "apply_label_to_ad",
        "apply_label_to_keyword",
        "remove_label_from_campaign",
        "remove_label_from_ad_group",
        "remove_label_from_ad",
        "remove_label_from_keyword",
    }
)

DIRECT_MUTATION_GROUPS = {
    "campaign_create": CAMPAIGN_CREATE_TOOLS,
    "budget": BUDGET_MUTATION_TOOLS,
    "campaign": CAMPAIGN_MUTATION_TOOLS,
    "ad_group": AD_GROUP_MUTATION_TOOLS,
    "ad": AD_MUTATION_TOOLS,
    "keyword": KEYWORD_MUTATION_TOOLS,
    "asset": ASSET_MUTATION_TOOLS,
    "label": LABEL_MUTATION_TOOLS,
}

DIRECT_MUTATION_TOOLS = frozenset().union(*DIRECT_MUTATION_GROUPS.values())

DIRECT_NEGATIVE_KEYWORD_TOOLS = frozenset(
    {
        "add_negative_keywords_ad_group",
        "add_negative_keywords_campaign",
        "remove_negative_keywords_ad_group",
        "remove_negative_keywords_campaign",
        "create_shared_negative_keyword_list",
        "add_keywords_to_shared_list",
        "remove_keywords_from_shared_list",
        "apply_shared_list_to_campaign",
        "remove_shared_list_from_campaign",
        "bulk_add_negative_keywords",
    }
)

WRITE_BUILDER_TOOLS = DIRECT_MUTATION_TOOLS | DIRECT_NEGATIVE_KEYWORD_TOOLS

ADDITIVE_WRITE_TOOLS = frozenset(
    {
        "add_keywords",
        "add_keywords_to_shared_list",
        "add_negative_keywords_ad_group",
        "add_negative_keywords_campaign",
        "apply_ad_group_label",
        "apply_ad_label",
        "apply_campaign_label",
        "apply_keyword_label",
        "apply_shared_list_to_campaign",
        "bulk_add_keywords",
        "bulk_add_negative_keywords",
        "create_ad_group",
        "create_app_campaign",
        "create_budget",
        "create_callout",
        "create_demand_gen_campaign",
        "create_display_campaign",
        "create_label",
        "create_pmax_campaign",
        "create_responsive_search_ad",
        "create_search_campaign",
        "create_shared_budget",
        "create_shared_negative_keyword_list",
        "create_shopping_campaign",
        "create_sitelink",
        "create_text_asset",
        "create_video_asset",
    }
)

NON_ADDITIVE_WRITE_TOOLS = frozenset(
    {
        "add_audience_to_ad_group",
        "add_audience_to_campaign",
        "add_content_label_exclusions",
        "add_placement_exclusions",
        "add_placement_targeting",
        "add_topic_targeting",
        "append_to_customer_match_audience",
        "apply_recommendation",
        "attach_bidding_strategy_to_campaign",
        "batch_mutate",
        "bulk_enable_campaigns",
        "bulk_pause_campaigns",
        "bulk_update_bids",
        "create_account_budget_proposal",
        "create_ad_customizer_feed",
        "create_app_ad",
        "create_app_extension",
        "create_app_remarketing_list",
        "create_bidding_strategy",
        "create_call_ad",
        "create_call_extension",
        "create_campaign_draft",
        "create_campaign_experiment",
        "create_combined_audience",
        "create_conversion_action",
        "create_custom_segment",
        "create_customer_match_audience",
        "create_demand_gen_ad",
        "create_dsa_page_feed",
        "create_dynamic_search_ad",
        "create_hotel_ad",
        "create_image_extension",
        "create_lead_form_extension",
        "create_listing_group_tree",
        "create_pmax_asset_group",
        "create_price_extension",
        "create_promotion_extension",
        "create_responsive_display_ad",
        "create_seasonal_bid_adjustment",
        "create_shopping_product_ad",
        "create_structured_snippet",
        "create_video_ad",
        "create_website_remarketing_list",
        "create_youtube_remarketing_list",
        "dismiss_recommendation",
        "enable_ad",
        "enable_ad_group",
        "enable_campaign",
        "enable_keyword",
        "end_campaign_experiment",
        "google_ads_mutate",
        "graduate_campaign_experiment",
        "link_budget_to_campaign",
        "pause_ad",
        "pause_ad_group",
        "pause_campaign",
        "pause_conversion_action",
        "pause_keyword",
        "promote_campaign_draft",
        "remove_ad",
        "remove_ad_group",
        "remove_ad_group_label",
        "remove_ad_label",
        "remove_asset",
        "remove_audience",
        "remove_audience_from_ad_group",
        "remove_audience_from_campaign",
        "remove_bidding_strategy",
        "remove_budget",
        "remove_campaign",
        "remove_campaign_label",
        "remove_conversion_action",
        "remove_extension",
        "remove_from_customer_match_audience",
        "remove_keyword_label",
        "remove_keywords",
        "remove_keywords_from_shared_list",
        "remove_label",
        "remove_listing_group",
        "remove_negative_keywords_ad_group",
        "remove_negative_keywords_campaign",
        "remove_pmax_asset_group",
        "remove_shared_list_from_campaign",
        "remove_topic_targeting",
        "set_ad_schedule_bid_adjustments",
        "set_ad_scheduling",
        "set_audience_bid_adjustments",
        "set_campaign_inline_bid_strategy",
        "set_custom_parameters",
        "set_demographic_bid_adjustments",
        "set_demographic_targeting",
        "set_device_bid_adjustments",
        "set_extension_scheduling",
        "set_geo_targeting",
        "set_language_targeting",
        "set_pmax_audience_signals",
        "update_ad_customizer_feed",
        "update_ad_group",
        "update_audience",
        "update_bidding_strategy",
        "update_budget",
        "update_campaign",
        "update_conversion_action",
        "update_conversion_attribution_model",
        "update_dsa_page_feed",
        "update_extension_status",
        "update_keyword_bid",
        "update_label",
        "update_listing_group",
        "update_network_settings",
        "update_pmax_asset_group",
        "update_shared_budget",
        "upload_call_conversions",
        "upload_enhanced_conversions",
        "upload_image_asset",
        "upload_offline_conversions",
    }
)

CLASSIFIED_WRITE_TOOLS = ADDITIVE_WRITE_TOOLS | NON_ADDITIVE_WRITE_TOOLS

CAMPAIGN_CHANNEL_BY_CREATE_TOOL = {
    "create_search_campaign": "SEARCH",
    "create_display_campaign": "DISPLAY",
    "create_shopping_campaign": "SHOPPING",
    "create_pmax_campaign": "PERFORMANCE_MAX",
    "create_demand_gen_campaign": "DEMAND_GEN",
    "create_app_campaign": "MULTI_CHANNEL",
}

APPLY_LABEL_TOOLS = frozenset(name for name in LABEL_MUTATION_TOOLS if name.startswith("apply_"))
REMOVE_LABEL_FROM_TOOLS = frozenset(name for name in LABEL_MUTATION_TOOLS if name.startswith("remove_"))
