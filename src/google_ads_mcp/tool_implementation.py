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
