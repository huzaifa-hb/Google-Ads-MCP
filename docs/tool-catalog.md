# Google Ads MCP Tool Catalog

This file is generated from `src/google_ads_mcp/tool_catalog.py` and `src/google_ads_mcp/tool_config.py`.

## Planning

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `describe_google_ads_resource` | `metadata` | `metadata` | Describe fields for a Google Ads API resource. |
| `describe_google_ads_service` | `metadata` | `metadata` | Describe callable methods for a Google Ads service. |
| `explain_gaql_error` | `query_planning` | `planning` | Explain common GAQL errors and suggest safe next steps. |
| `get_capability_matrix` | `metadata` | `metadata` | Return implementation status for the currently exposed tools. |
| `get_google_ads_resource_metadata` | `metadata` | `metadata` | Return selectable fields, filters, metrics, and segments for a resource. |
| `get_server_status` | `metadata` | `metadata` | Return server mode, auth mode, config source, and exposed tool count. |
| `get_tool_catalog` | `metadata` | `metadata` | Return the currently exposed Google Ads MCP tool catalog. |
| `google_ads_call_service` | `service` | `generic` | Call any Google Ads API service method exposed by the client. |
| `google_ads_mutate` | `mutate` | `generic` | Run GoogleAdsService.mutate against arbitrary operations. |
| `google_ads_search` | `raw_gaql` | `generic` | Run a GAQL search query. |
| `google_ads_search_stream` | `raw_gaql_stream` | `generic` | Run a GAQL SearchStream query. |
| `list_accessible_customers` | `query` | `account` | List customer resource names accessible to the configured OAuth user. |
| `list_google_ads_services` | `metadata` | `metadata` | List service classes available in the installed Google Ads API client. |
| `plan_gaql_query` | `query_planning` | `planning` | Build a validated GAQL query plan without executing it. |
| `query_google_ads_docs` | `kb_lookup` | `metadata` | Query the offline GAQL knowledge base. |
| `suggest_gaql_fields` | `metadata` | `metadata` | Suggest GAQL fields from live resource metadata. |
| `validate_gaql_fields` | `validation` | `metadata` | Validate GAQL SELECT fields against live resource metadata. |
| `validate_google_ads_payload` | `validation` | `metadata` | Validate a protobuf JSON payload against a Google Ads message type. |

## Account

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `get_account_info` | `query` | `customer` | Account name, currency, time zone, tracking, and auto-tagging status. |
| `list_customers` | `query` | `customer_client` | List accessible leaf customer accounts. |
| `get_mcc_hierarchy` | `query` | `customer_client` | Traverse manager account hierarchy with parent and child links. |
| `get_account_settings` | `query` | `customer` | Account-level tracking and conversion settings. |
| `list_linked_accounts` | `service` | `` | List Analytics, Merchant Center, Search Console, and product links. |
| `get_account_budget` | `service` | `` | Read account-level budgets and proposals. |
| `create_account_budget_proposal` | `mutate` | `` | Template only: Create an account-level budget proposal. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `list_invoices` | `service` | `` | List billing invoices. Requires payload.billing_setup; call get_billing_setup first. |
| `download_invoice_pdf` | `service` | `` | Return invoice PDF metadata or URL when available from the API. |
| `get_billing_setup` | `service` | `` | Read billing setup details. |

## Ad Groups

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_ad_groups` | `query` | `ad_group` | List ad groups, optionally filtered by campaign. |
| `get_ad_group` | `query` | `ad_group` | Get one ad group. |
| `create_ad_group` | `mutate` | `` | Create an ad group. |
| `update_ad_group` | `mutate` | `` | Update ad group name, status, or bids. |
| `pause_ad_group` | `mutate` | `` | Pause an ad group. |
| `enable_ad_group` | `mutate` | `` | Enable an ad group. |
| `remove_ad_group` | `mutate` | `` | Remove an ad group. |
| `apply_ad_group_label` | `mutate` | `` | Attach a label to an ad group. |
| `remove_ad_group_label` | `mutate` | `` | Detach a label from an ad group. |

## Ads

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_ads` | `query` | `ad_group_ad` | List ads by campaign, ad group, status, or type. |
| `get_ad` | `query` | `ad_group_ad` | Get one ad with approval status. |
| `create_responsive_search_ad` | `mutate` | `` | Create a responsive search ad. |
| `create_responsive_display_ad` | `mutate` | `` | Template only: Create a responsive display ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_call_ad` | `mutate` | `` | Template only: Create a call ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_app_ad` | `mutate` | `` | Template only: Create an app ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_video_ad` | `mutate` | `` | Template only: Create a video ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_demand_gen_ad` | `mutate` | `` | Template only: Create a Demand Gen ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_dynamic_search_ad` | `mutate` | `` | Template only: Create a dynamic search ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_shopping_product_ad` | `mutate` | `` | Template only: Create a Shopping product ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_hotel_ad` | `mutate` | `` | Template only: Create a Hotel ad when supported. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `pause_ad` | `mutate` | `` | Pause an ad. |
| `enable_ad` | `mutate` | `` | Enable an ad. |
| `remove_ad` | `mutate` | `` | Remove an ad. |
| `get_ad_approval_status` | `service` | `` | Get policy review status and disapproval reasons. |
| `get_ad_asset_performance` | `report` | `ad_group_ad_asset_view` | Get RSA asset serving rate and performance labels. |
| `apply_ad_label` | `mutate` | `` | Attach a label to an ad. |
| `remove_ad_label` | `mutate` | `` | Detach a label from an ad. |

## Assets

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_assets` | `query` | `asset` | List reusable assets. |
| `get_asset` | `query` | `asset` | Get one asset with policy and performance data. |
| `upload_image_asset` | `mutate` | `` | Template only: Upload or create an image asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_text_asset` | `mutate` | `` | Create a text asset. |
| `create_video_asset` | `mutate` | `` | Create a YouTube video asset. |
| `get_asset_performance` | `report` | `asset_group_asset` | Get asset serving performance. |
| `get_asset_approval_status` | `service` | `` | Get asset policy approval status. |
| `remove_asset` | `mutate` | `` | Template only: Remove an asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |

## Audiences

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_audiences` | `query` | `user_list` | List user lists and audience resources. |
| `get_audience` | `query` | `user_list` | Get one audience or user list. |
| `create_customer_match_audience` | `mutate` | `` | Template only: Create a Customer Match audience. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `append_to_customer_match_audience` | `mutate` | `` | Template only: Append hashed members to Customer Match. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_from_customer_match_audience` | `mutate` | `` | Template only: Remove members from Customer Match. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_website_remarketing_list` | `mutate` | `` | Template only: Create website remarketing list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_youtube_remarketing_list` | `mutate` | `` | Template only: Create YouTube remarketing list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_app_remarketing_list` | `mutate` | `` | Template only: Create app remarketing list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_similar_audience` | `unsupported` | `` | Unsupported by this MCP: Similar audiences are no longer a generally available creation path in Google Ads. Use audience signals, optimized targeting, Customer Match, or custom segments. |
| `create_combined_audience` | `mutate` | `` | Template only: Create a combined audience. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_custom_segment` | `mutate` | `` | Template only: Create a custom segment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_audience_size_estimate` | `service` | `` | Estimate audience reach when available. |
| `update_audience` | `mutate` | `` | Template only: Update audience or user list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_audience` | `mutate` | `` | Template only: Remove audience or user list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |

## Bidding

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_bidding_strategies` | `query` | `bidding_strategy` | List portfolio bidding strategies. |
| `get_bidding_strategy` | `query` | `bidding_strategy` | Get one bidding strategy. |
| `create_bidding_strategy` | `mutate` | `` | Template only: Create a portfolio bidding strategy. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_bidding_strategy` | `mutate` | `` | Template only: Update a portfolio bidding strategy. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_bidding_strategy` | `mutate` | `` | Template only: Remove an unused portfolio bidding strategy. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `attach_bidding_strategy_to_campaign` | `mutate` | `` | Template only: Attach portfolio strategy to campaign. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_campaign_inline_bid_strategy` | `mutate` | `` | Template only: Set campaign-level inline bid strategy. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_bidding_strategy_report` | `report` | `bidding_strategy` | Report performance by bidding strategy. |
| `set_audience_bid_adjustments` | `mutate` | `` | Template only: Set audience bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_demographic_bid_adjustments` | `mutate` | `` | Template only: Set demographic bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_ad_schedule_bid_adjustments` | `mutate` | `` | Template only: Set ad schedule bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_seasonal_bid_adjustment` | `mutate` | `` | Template only: Create a seasonal conversion rate adjustment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |

## Budgets

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_budgets` | `query` | `campaign_budget` | List campaign budgets. |
| `get_budget` | `query` | `campaign_budget` | Get one campaign budget. |
| `create_budget` | `mutate` | `` | Create a campaign budget. |
| `update_budget` | `mutate` | `` | Update a campaign budget. |
| `remove_budget` | `mutate` | `` | Remove an unattached budget. |
| `create_shared_budget` | `mutate` | `` | Create a budget shared by campaigns. |
| `update_shared_budget` | `mutate` | `` | Update a shared budget. |
| `link_budget_to_campaign` | `mutate` | `` | Attach a shared budget to a campaign. |
| `list_shared_budgets` | `query` | `campaign_budget` | List shared campaign budgets. |

## Bulk

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `batch_mutate` | `mutate` | `` | Run up to 5,000 mixed mutate operations. |
| `bulk_pause_campaigns` | `mutate` | `` | Pause campaigns in bulk. |
| `bulk_enable_campaigns` | `mutate` | `` | Enable campaigns in bulk. |
| `bulk_update_bids` | `mutate` | `` | Update keyword bids in bulk. |
| `bulk_add_keywords` | `mutate` | `` | Add keywords in bulk. |
| `bulk_add_negative_keywords` | `negative_keyword` | `` | Add negative keywords in bulk. |

## Campaigns

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_campaigns` | `query` | `campaign` | List campaigns with status, type, budget, and bidding strategy. |
| `get_campaign` | `query` | `campaign` | Get one campaign by id or resource name. |
| `create_search_campaign` | `mutate` | `` | Create a Search campaign from Google Ads mutate operations. |
| `create_display_campaign` | `mutate` | `` | Create a Display campaign from Google Ads mutate operations. |
| `create_video_campaign` | `unsupported` | `` | Unsupported by this MCP: Direct VIDEO campaign creation is not supported through this MCP's GoogleAdsService mutate path in the current Google Ads API surface. Use Demand Gen, Performance Max, or the Google Ads UI for video-first campaign setup. |
| `create_shopping_campaign` | `mutate` | `` | Create a Shopping campaign from Google Ads mutate operations. |
| `create_pmax_campaign` | `mutate` | `` | Create a Performance Max campaign from mutate operations. |
| `create_demand_gen_campaign` | `mutate` | `` | Create a Demand Gen campaign from mutate operations. |
| `create_app_campaign` | `mutate` | `` | Create an App campaign from mutate operations. |
| `create_smart_campaign` | `unsupported` | `` | Unsupported by this MCP: Direct Smart campaign creation is not exposed because SmartCampaignSetting cannot be validated with validate_only in the current Google Ads API surface. Use the Google Ads UI or a raw API flow only after explicit real-write approval. |
| `update_campaign` | `mutate` | `` | Update campaign name, status, dates, tracking, or URL options. |
| `pause_campaign` | `mutate` | `` | Pause a campaign. |
| `enable_campaign` | `mutate` | `` | Enable a campaign. |
| `remove_campaign` | `mutate` | `` | Remove a campaign. |
| `update_network_settings` | `mutate` | `` | Update search/display/search partner network settings. |
| `set_geo_targeting` | `mutate` | `` | Template only: Add or remove targeted and excluded campaign locations. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_language_targeting` | `mutate` | `` | Template only: Add or remove campaign language criteria. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_ad_scheduling` | `mutate` | `` | Template only: Set campaign dayparting criteria and bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_device_bid_adjustments` | `mutate` | `` | Template only: Set campaign device bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `apply_campaign_label` | `mutate` | `` | Attach a label to a campaign. |
| `remove_campaign_label` | `mutate` | `` | Detach a label from a campaign. |
| `create_campaign_draft` | `mutate` | `` | Template only: Create a campaign draft. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `promote_campaign_draft` | `mutate` | `` | Template only: Promote a campaign draft. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_campaign_experiment` | `mutate` | `` | Template only: Create a campaign experiment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `graduate_campaign_experiment` | `mutate` | `` | Template only: Graduate an experiment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `end_campaign_experiment` | `mutate` | `` | Template only: End an experiment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |

## Conversions

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_conversion_actions` | `query` | `conversion_action` | List conversion actions. |
| `get_conversion_action` | `query` | `conversion_action` | Get one conversion action. |
| `create_conversion_action` | `mutate` | `` | Template only: Create a conversion action. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_conversion_action` | `mutate` | `` | Template only: Update conversion action settings. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `pause_conversion_action` | `mutate` | `` | Template only: Pause conversion action. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_conversion_action` | `mutate` | `` | Template only: Remove conversion action. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `upload_offline_conversions` | `mutate` | `` | Template only: Upload GCLID-based offline conversions. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `upload_call_conversions` | `mutate` | `` | Template only: Upload call conversions. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `upload_store_visit_conversions` | `unsupported` | `` | Unsupported by this MCP: Store visit conversion uploads are eligibility-gated and not available for most API users. Use google_ads_call_service if your account has the required service access. |
| `upload_enhanced_conversions` | `mutate` | `` | Template only: Upload enhanced conversion user data. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_conversion_attribution_settings` | `service` | `` | Get attribution settings. |
| `update_conversion_attribution_model` | `mutate` | `` | Template only: Update conversion attribution model. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |

## Extensions

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_extensions` | `service` | `` | List assets/extensions by type and level. |
| `get_extension` | `service` | `` | Get one extension or asset. |
| `create_sitelink` | `mutate` | `` | Create a sitelink asset. |
| `create_callout` | `mutate` | `` | Create a callout asset. |
| `create_structured_snippet` | `mutate` | `` | Template only: Create a structured snippet asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_call_extension` | `mutate` | `` | Template only: Create a call asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_price_extension` | `mutate` | `` | Template only: Create a price asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_promotion_extension` | `mutate` | `` | Template only: Create a promotion asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_app_extension` | `mutate` | `` | Template only: Create an app asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_image_extension` | `mutate` | `` | Template only: Create an image asset extension. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_lead_form_extension` | `mutate` | `` | Template only: Create a lead form asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_extension_scheduling` | `mutate` | `` | Template only: Set extension scheduling. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_extension_status` | `mutate` | `` | Template only: Pause or enable an extension asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_extension` | `mutate` | `` | Template only: Remove an extension asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_extension_approval_status` | `service` | `` | Get extension policy approval status. |

## Feeds

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `create_dsa_page_feed` | `mutate` | `` | Template only: Create a Dynamic Search Ads page feed. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_dsa_page_feed` | `mutate` | `` | Template only: Update DSA page feed rows. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `list_dsa_page_feeds` | `service` | `` | List DSA page feeds. |
| `create_ad_customizer_feed` | `mutate` | `` | Template only: Create ad customizer feed or attributes. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_ad_customizer_feed` | `mutate` | `` | Template only: Update ad customizer rows. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_custom_parameters` | `mutate` | `` | Template only: Set URL custom parameters. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |

## Keywords

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_keywords` | `query` | `keyword_view` | List keywords by campaign, ad group, match type, or status. |
| `get_keyword` | `query` | `keyword_view` | Get one keyword with bid and quality score fields. |
| `add_keywords` | `mutate` | `` | Add one or more keywords to an ad group. |
| `update_keyword_bid` | `mutate` | `` | Update CPC bid on a keyword. |
| `pause_keyword` | `mutate` | `` | Pause a keyword. |
| `enable_keyword` | `mutate` | `` | Enable a keyword. |
| `remove_keywords` | `mutate` | `` | Remove one or more keywords. |
| `apply_keyword_label` | `mutate` | `` | Attach a label to a keyword. |
| `remove_keyword_label` | `mutate` | `` | Detach a label from a keyword. |
| `list_negative_keywords_ad_group` | `negative_keyword` | `` | List ad group-level negative keywords. |
| `add_negative_keywords_ad_group` | `negative_keyword` | `` | Add ad group-level negative keywords. |
| `remove_negative_keywords_ad_group` | `negative_keyword` | `` | Remove ad group-level negative keywords. |
| `list_negative_keywords_campaign` | `negative_keyword` | `` | List campaign-level negative keywords. |
| `add_negative_keywords_campaign` | `negative_keyword` | `` | Add campaign-level negative keywords. |
| `remove_negative_keywords_campaign` | `negative_keyword` | `` | Remove campaign-level negative keywords. |
| `list_shared_negative_keyword_lists` | `negative_keyword` | `` | List account-level shared negative keyword lists. |
| `create_shared_negative_keyword_list` | `negative_keyword` | `` | Create a shared negative keyword list. |
| `add_keywords_to_shared_list` | `negative_keyword` | `` | Add keywords to a shared negative list. |
| `remove_keywords_from_shared_list` | `negative_keyword` | `` | Remove keywords from a shared negative list. |
| `apply_shared_list_to_campaign` | `negative_keyword` | `` | Attach a shared negative list to a campaign. |
| `remove_shared_list_from_campaign` | `negative_keyword` | `` | Detach a shared negative list from a campaign. |
| `get_keyword_bid_estimates` | `unsupported` | `` | Unsupported by this MCP: Keyword bid estimates are not mapped to a stable high-level helper. Use Keyword Planner idea and forecast services directly only after checking live service metadata. |
| `get_keyword_ideas` | `service` | `` | Get Keyword Planner ideas. |

## Labels

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_labels` | `query` | `label` | List account labels. |
| `create_label` | `mutate` | `` | Create a label. |
| `update_label` | `mutate` | `` | Update label name, color, or description. |
| `remove_label` | `mutate` | `` | Remove a label. |
| `apply_label_to_campaign` | `mutate` | `` | Attach label to campaigns. |
| `apply_label_to_ad_group` | `mutate` | `` | Attach label to ad groups. |
| `apply_label_to_ad` | `mutate` | `` | Attach label to ads. |
| `apply_label_to_keyword` | `mutate` | `` | Attach label to keywords. |
| `remove_label_from_campaign` | `mutate` | `` | Detach label from campaigns. |
| `remove_label_from_ad_group` | `mutate` | `` | Detach label from ad groups. |
| `remove_label_from_ad` | `mutate` | `` | Detach label from ads. |
| `remove_label_from_keyword` | `mutate` | `` | Detach label from keywords. |

## Planning

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `get_reach_forecast` | `service` | `` | Get Reach Planner forecast where available. |
| `get_ad_preview` | `unsupported` | `` | Unsupported by this MCP: Ad preview is not mapped to a stable Google Ads API service method in this MCP. Use Google Ads UI preview tools or live metadata before adding an API helper. |
| `get_ad_diagnosis` | `unsupported` | `` | Unsupported by this MCP: Ad diagnosis is not mapped to a stable Google Ads API service method in this MCP. Use policy and approval report tools plus live metadata for account-specific diagnosis. |

## Recommendations

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `list_recommendations` | `query` | `recommendation` | List pending Google recommendations. |
| `apply_recommendation` | `mutate` | `` | Template only: Apply a recommendation. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `dismiss_recommendation` | `mutate` | `` | Template only: Dismiss a recommendation. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_recommendation_types` | `service` | `` | List supported recommendation type metadata. |

## Reporting

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `get_campaign_metrics` | `report` | `campaign` | Campaign metrics with preset or custom date ranges. |
| `get_ad_group_metrics` | `report` | `ad_group` | Ad group metrics with preset or custom date ranges. |
| `get_ad_metrics` | `report` | `ad_group_ad` | Ad metrics with preset or custom date ranges. |
| `get_keyword_metrics` | `report` | `keyword_view` | Keyword metrics plus quality score fields. |
| `get_search_terms_report` | `report` | `search_term_view` | Search query performance report. |
| `get_auction_insights` | `unsupported` | `` | Unsupported by this MCP: Auction insight fields are version and account sensitive. Use live metadata and planning_plan_gaql_query before implementing this report. |
| `get_device_performance` | `report` | `campaign` | Performance by device. |
| `get_geo_performance` | `report` | `geographic_view` | Performance by geographic target id and readable name. |
| `get_hour_of_day_performance` | `report` | `campaign` | Performance by hour of day. |
| `get_day_of_week_performance` | `report` | `campaign` | Performance by day of week. |
| `get_age_range_report` | `report` | `age_range_view` | Performance by age range. |
| `get_gender_report` | `report` | `gender_view` | Performance by gender. |
| `get_parental_status_report` | `report` | `parental_status_view` | Performance by parental status. |
| `get_household_income_report` | `report` | `income_range_view` | Performance by household income. |
| `get_audience_performance_report` | `report` | `ad_group_audience_view` | Performance by audience segment. |
| `get_placement_report` | `report` | `group_placement_view` | Display placement performance. |
| `get_topic_report` | `unsupported` | `` | Unsupported by this MCP: Topic performance fields are version and campaign-type sensitive. Use live metadata and planning_plan_gaql_query to build a topic-compatible GAQL query for the target account. |
| `get_ad_schedule_report` | `report` | `campaign` | Performance by scheduled time block. |
| `get_asset_performance_report` | `report` | `asset_group_asset` | Asset performance for RSA and PMax. |
| `get_video_performance_report` | `report` | `video` | Video performance report. |
| `get_shopping_performance_report` | `report` | `shopping_performance_view` | Shopping product performance. |
| `get_display_performance_report` | `report` | `campaign` | Display network performance. |
| `get_landing_page_report` | `report` | `landing_page_view` | Landing page performance. |
| `get_call_details_report` | `report` | `call_view` | Call details report. |
| `get_change_history_report` | `report` | `change_event` | Change history report. |
| `get_reach_frequency_report` | `unsupported` | `` | Unsupported by this MCP: Reach and frequency reporting is not a universal GAQL view. Use live metadata to confirm compatible reach/frequency fields before querying. |
| `get_paid_organic_report` | `unsupported` | `` | Unsupported by this MCP: Paid and organic reporting depends on Search Console linkage and version-specific fields. Use live metadata before building this report. |
| `execute_gaql_query` | `raw_gaql` | `` | Execute raw GAQL for uncovered reporting needs. |

## Shopping Pmax

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `get_shopping_campaign_settings` | `service` | `` | Get Merchant Center and Shopping campaign settings. |
| `create_listing_group_tree` | `mutate` | `` | Template only: Create a Shopping listing group tree. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_listing_group` | `mutate` | `` | Template only: Update a listing group node. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_listing_group` | `mutate` | `` | Template only: Remove a listing group node. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `list_pmax_asset_groups` | `query` | `asset_group` | List PMax asset groups. |
| `get_pmax_asset_group` | `query` | `asset_group` | Get one PMax asset group. |
| `create_pmax_asset_group` | `mutate` | `` | Template only: Create a PMax asset group. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_pmax_asset_group` | `mutate` | `` | Template only: Update a PMax asset group. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_pmax_asset_group` | `mutate` | `` | Template only: Remove a PMax asset group. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_pmax_audience_signals` | `mutate` | `` | Template only: Set PMax audience signals and search themes. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_pmax_search_term_themes` | `service` | `` | Get PMax search term themes where exposed. |
| `get_pmax_asset_group_performance` | `report` | `asset_group` | Report PMax asset group performance. |
| `get_pmax_campaign_insights` | `service` | `` | Report PMax campaign insights. |

## Targeting

| Tool | Mode | Resource | Description |
|---|---|---|---|
| `add_audience_to_campaign` | `mutate` | `` | Template only: Add campaign audience targeting or observation. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_audience_to_ad_group` | `mutate` | `` | Template only: Add ad group audience targeting or observation. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_audience_from_campaign` | `mutate` | `` | Template only: Remove campaign audience targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_audience_from_ad_group` | `mutate` | `` | Template only: Remove ad group audience targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_demographic_targeting` | `mutate` | `` | Template only: Set age, gender, parental, or household targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_topic_targeting` | `mutate` | `` | Template only: Add GDN topic targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_topic_targeting` | `mutate` | `` | Template only: Remove GDN topic targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_placement_targeting` | `mutate` | `` | Template only: Add placement targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_placement_exclusions` | `mutate` | `` | Template only: Add placement exclusions. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_content_label_exclusions` | `mutate` | `` | Template only: Add sensitive content exclusions. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
