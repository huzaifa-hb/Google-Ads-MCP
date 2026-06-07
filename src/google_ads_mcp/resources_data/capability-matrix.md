# Google Ads MCP Capability Matrix

This file is generated from `src/google_ads_mcp/tool_catalog.py`, `src/google_ads_mcp/tool_config.py`, `src/google_ads_mcp/tool_implementation.py`, and `src/google_ads_mcp/capability_matrix.py`.

| Tool | Namespace | Mode | Implementation Status | Backend | Read/Write | Requires Eligibility | Notes |
|---|---|---|---|---|---|---|---|
| `create_account_budget_proposal` | `account` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create an account-level budget proposal. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `download_invoice_pdf` | `account` | `service` | `generic_routed` | Google Ads service bridge | `read` | yes | Return invoice PDF metadata or URL when available from the API. |
| `get_account_budget` | `account` | `service` | `generic_routed` | Google Ads service bridge | `read` | depends | Read account-level budgets and proposals. |
| `get_account_info` | `account` | `query` | `hand_implemented` | GoogleAdsService.Search FROM customer | `read` | no | Account name, currency, time zone, tracking, and auto-tagging status. |
| `get_account_settings` | `account` | `query` | `hand_implemented` | GoogleAdsService.Search FROM customer | `read` | no | Account-level tracking and conversion settings. |
| `get_billing_setup` | `account` | `service` | `generic_routed` | Google Ads service bridge | `read` | yes | Read billing setup details. |
| `get_mcc_hierarchy` | `account` | `query` | `hand_implemented` | GoogleAdsService.Search FROM customer_client | `read` | no | Traverse manager account hierarchy with parent and child links. |
| `list_accessible_customers` | `account` | `query` | `hand_implemented` | CustomerService.ListAccessibleCustomers | `read` | no | List customer resource names accessible to the configured OAuth user. |
| `list_customers` | `account` | `query` | `hand_implemented` | GoogleAdsService.Search FROM customer_client | `read` | no | List accessible leaf customer accounts. |
| `list_invoices` | `account` | `service` | `generic_routed` | Google Ads service bridge | `read` | yes | List billing invoices. Requires payload.billing_setup; call get_billing_setup first. |
| `list_linked_accounts` | `account` | `service` | `generic_routed` | Google Ads service bridge | `read` | depends | List Analytics, Merchant Center, Search Console, and product links. |
| `apply_ad_group_label` | `ad_groups` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach a label to an ad group. |
| `create_ad_group` | `ad_groups` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create an ad group. |
| `enable_ad_group` | `ad_groups` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Enable an ad group. |
| `get_ad_group` | `ad_groups` | `query` | `hand_implemented` | GoogleAdsService.Search FROM ad_group | `read` | no | Get one ad group. |
| `list_ad_groups` | `ad_groups` | `query` | `hand_implemented` | GoogleAdsService.Search FROM ad_group | `read` | no | List ad groups, optionally filtered by campaign. |
| `pause_ad_group` | `ad_groups` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Pause an ad group. |
| `remove_ad_group` | `ad_groups` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Remove an ad group. |
| `remove_ad_group_label` | `ad_groups` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Detach a label from an ad group. |
| `update_ad_group` | `ad_groups` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Update ad group name, status, or bids. |
| `apply_ad_label` | `ads` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach a label to an ad. |
| `create_app_ad` | `ads` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create an app ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_call_ad` | `ads` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a call ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_demand_gen_ad` | `ads` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a Demand Gen ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_dynamic_search_ad` | `ads` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a dynamic search ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_hotel_ad` | `ads` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a Hotel ad when supported. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_responsive_display_ad` | `ads` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a responsive display ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_responsive_search_ad` | `ads` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a responsive search ad. |
| `create_shopping_product_ad` | `ads` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a Shopping product ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_video_ad` | `ads` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a video ad. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `enable_ad` | `ads` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Enable an ad. |
| `get_ad` | `ads` | `query` | `hand_implemented` | GoogleAdsService.Search FROM ad_group_ad | `read` | no | Get one ad with approval status. |
| `get_ad_approval_status` | `ads` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Get policy review status and disapproval reasons. |
| `get_ad_asset_performance` | `ads` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM ad_group_ad_asset_view | `read` | no | Get RSA asset serving rate and performance labels. |
| `list_ads` | `ads` | `query` | `hand_implemented` | GoogleAdsService.Search FROM ad_group_ad | `read` | no | List ads by campaign, ad group, status, or type. |
| `pause_ad` | `ads` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Pause an ad. |
| `remove_ad` | `ads` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Remove an ad. |
| `remove_ad_label` | `ads` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Detach a label from an ad. |
| `create_text_asset` | `assets` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a text asset. |
| `create_video_asset` | `assets` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a YouTube video asset. |
| `get_asset` | `assets` | `query` | `hand_implemented` | GoogleAdsService.Search FROM asset | `read` | no | Get one asset with policy and performance data. |
| `get_asset_approval_status` | `assets` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Get asset policy approval status. |
| `get_asset_performance` | `assets` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM asset_group_asset | `read` | no | Get asset serving performance. |
| `list_assets` | `assets` | `query` | `hand_implemented` | GoogleAdsService.Search FROM asset | `read` | no | List reusable assets. |
| `remove_asset` | `assets` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove an asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `upload_image_asset` | `assets` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Upload or create an image asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `append_to_customer_match_audience` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Append hashed members to Customer Match. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_app_remarketing_list` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create app remarketing list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_combined_audience` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a combined audience. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_custom_segment` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a custom segment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_customer_match_audience` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a Customer Match audience. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_similar_audience` | `audiences` | `unsupported` | `deprecated` | n/a | `read` | no | Similar audiences are no longer a generally available creation path in Google Ads. Use audience signals, optimized targeting, Customer Match, or custom segments. |
| `create_website_remarketing_list` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create website remarketing list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_youtube_remarketing_list` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create YouTube remarketing list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_audience` | `audiences` | `query` | `hand_implemented` | GoogleAdsService.Search FROM user_list | `read` | no | Get one audience or user list. |
| `get_audience_size_estimate` | `audiences` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Estimate audience reach when available. |
| `list_audiences` | `audiences` | `query` | `hand_implemented` | GoogleAdsService.Search FROM user_list | `read` | no | List user lists and audience resources. |
| `remove_audience` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove audience or user list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_from_customer_match_audience` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove members from Customer Match. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_audience` | `audiences` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Update audience or user list. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `attach_bidding_strategy_to_campaign` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Attach portfolio strategy to campaign. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_bidding_strategy` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a portfolio bidding strategy. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_seasonal_bid_adjustment` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a seasonal conversion rate adjustment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_bidding_strategy` | `bidding` | `query` | `hand_implemented` | GoogleAdsService.Search FROM bidding_strategy | `read` | no | Get one bidding strategy. |
| `get_bidding_strategy_report` | `bidding` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM bidding_strategy | `read` | no | Report performance by bidding strategy. |
| `list_bidding_strategies` | `bidding` | `query` | `hand_implemented` | GoogleAdsService.Search FROM bidding_strategy | `read` | no | List portfolio bidding strategies. |
| `remove_bidding_strategy` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove an unused portfolio bidding strategy. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_ad_schedule_bid_adjustments` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set ad schedule bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_audience_bid_adjustments` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set audience bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_campaign_inline_bid_strategy` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set campaign-level inline bid strategy. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_demographic_bid_adjustments` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set demographic bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_bidding_strategy` | `bidding` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Update a portfolio bidding strategy. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_budget` | `budgets` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a campaign budget. |
| `create_shared_budget` | `budgets` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a budget shared by campaigns. |
| `get_budget` | `budgets` | `query` | `hand_implemented` | GoogleAdsService.Search FROM campaign_budget | `read` | no | Get one campaign budget. |
| `link_budget_to_campaign` | `budgets` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach a shared budget to a campaign. |
| `list_budgets` | `budgets` | `query` | `hand_implemented` | GoogleAdsService.Search FROM campaign_budget | `read` | no | List campaign budgets. |
| `list_shared_budgets` | `budgets` | `query` | `hand_implemented` | GoogleAdsService.Search FROM campaign_budget | `read` | no | List shared campaign budgets. |
| `remove_budget` | `budgets` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Remove an unattached budget. |
| `update_budget` | `budgets` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Update a campaign budget. |
| `update_shared_budget` | `budgets` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Update a shared budget. |
| `batch_mutate` | `bulk` | `mutate` | `generic_routed` | GoogleAdsService.Mutate | `write` | no | Run up to 5,000 mixed mutate operations. |
| `bulk_add_keywords` | `bulk` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Add keywords in bulk. |
| `bulk_add_negative_keywords` | `bulk` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Add negative keywords in bulk. |
| `bulk_enable_campaigns` | `bulk` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Enable campaigns in bulk. |
| `bulk_pause_campaigns` | `bulk` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Pause campaigns in bulk. |
| `bulk_update_bids` | `bulk` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Update keyword bids in bulk. |
| `apply_campaign_label` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach a label to a campaign. |
| `create_app_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create an App campaign from mutate operations. |
| `create_campaign_draft` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a campaign draft. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_campaign_experiment` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a campaign experiment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_demand_gen_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a Demand Gen campaign from mutate operations. |
| `create_display_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a Display campaign from Google Ads mutate operations. |
| `create_pmax_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a Performance Max campaign from mutate operations. |
| `create_search_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a Search campaign from Google Ads mutate operations. |
| `create_shopping_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a Shopping campaign from Google Ads mutate operations. |
| `create_smart_campaign` | `campaigns` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Direct Smart campaign creation is not exposed because SmartCampaignSetting cannot be validated with validate_only in the current Google Ads API surface. Use the Google Ads UI or a raw API flow only after explicit real-write approval. |
| `create_video_campaign` | `campaigns` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Direct VIDEO campaign creation is not supported through this MCP's GoogleAdsService mutate path in the current Google Ads API surface. Use Demand Gen, Performance Max, or the Google Ads UI for video-first campaign setup. |
| `enable_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Enable a campaign. |
| `end_campaign_experiment` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: End an experiment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_campaign` | `campaigns` | `query` | `hand_implemented` | GoogleAdsService.Search FROM campaign | `read` | no | Get one campaign by id or resource name. |
| `graduate_campaign_experiment` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Graduate an experiment. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `list_campaigns` | `campaigns` | `query` | `hand_implemented` | GoogleAdsService.Search FROM campaign | `read` | no | List campaigns with status, type, budget, and bidding strategy. |
| `pause_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Pause a campaign. |
| `promote_campaign_draft` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Promote a campaign draft. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Remove a campaign. |
| `remove_campaign_label` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Detach a label from a campaign. |
| `set_ad_scheduling` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set campaign dayparting criteria and bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_device_bid_adjustments` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set campaign device bid modifiers. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_geo_targeting` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Add or remove targeted and excluded campaign locations. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_language_targeting` | `campaigns` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Add or remove campaign language criteria. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_campaign` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Update campaign name, status, dates, tracking, or URL options. |
| `update_network_settings` | `campaigns` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Update search/display/search partner network settings. |
| `create_conversion_action` | `conversions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a conversion action. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_conversion_action` | `conversions` | `query` | `hand_implemented` | GoogleAdsService.Search FROM conversion_action | `read` | no | Get one conversion action. |
| `get_conversion_attribution_settings` | `conversions` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Get attribution settings. |
| `list_conversion_actions` | `conversions` | `query` | `hand_implemented` | GoogleAdsService.Search FROM conversion_action | `read` | no | List conversion actions. |
| `pause_conversion_action` | `conversions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Pause conversion action. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_conversion_action` | `conversions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove conversion action. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_conversion_action` | `conversions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Update conversion action settings. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_conversion_attribution_model` | `conversions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Update conversion attribution model. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `upload_call_conversions` | `conversions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Upload call conversions. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `upload_enhanced_conversions` | `conversions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Upload enhanced conversion user data. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `upload_offline_conversions` | `conversions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Upload GCLID-based offline conversions. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `upload_store_visit_conversions` | `conversions` | `unsupported` | `eligibility_gated` | n/a | `read` | yes | Store visit conversion uploads are eligibility-gated and not available for most API users. Use google_ads_call_service if your account has the required service access. |
| `create_app_extension` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create an app asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_call_extension` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a call asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_callout` | `extensions` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a callout asset. |
| `create_image_extension` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create an image asset extension. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_lead_form_extension` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a lead form asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_price_extension` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a price asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_promotion_extension` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a promotion asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_sitelink` | `extensions` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a sitelink asset. |
| `create_structured_snippet` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a structured snippet asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_extension` | `extensions` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Get one extension or asset. |
| `get_extension_approval_status` | `extensions` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Get extension policy approval status. |
| `list_extensions` | `extensions` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | List assets/extensions by type and level. |
| `remove_extension` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove an extension asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_extension_scheduling` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set extension scheduling. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_extension_status` | `extensions` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Pause or enable an extension asset. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_ad_customizer_feed` | `feeds` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create ad customizer feed or attributes. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_dsa_page_feed` | `feeds` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a Dynamic Search Ads page feed. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `list_dsa_page_feeds` | `feeds` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | List DSA page feeds. |
| `set_custom_parameters` | `feeds` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set URL custom parameters. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_ad_customizer_feed` | `feeds` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Update ad customizer rows. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_dsa_page_feed` | `feeds` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Update DSA page feed rows. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `google_ads_call_service` | `generic` | `service` | `generic_routed` | Generic Google Ads service bridge | `generic` | depends | Call any Google Ads API service method exposed by the client. |
| `google_ads_mutate` | `generic` | `mutate` | `generic_routed` | GoogleAdsService.Mutate | `write` | depends | Run GoogleAdsService.mutate against arbitrary operations. |
| `google_ads_search` | `generic` | `raw_gaql` | `hand_implemented` | GoogleAdsService.Search | `read` | no | Run a GAQL search query. |
| `google_ads_search_stream` | `generic` | `raw_gaql_stream` | `hand_implemented` | GoogleAdsService.SearchStream | `read` | no | Run a GAQL SearchStream query. |
| `add_keywords` | `keywords` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Add one or more keywords to an ad group. |
| `add_keywords_to_shared_list` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Add keywords to a shared negative list. |
| `add_negative_keywords_ad_group` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Add ad group-level negative keywords. |
| `add_negative_keywords_campaign` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Add campaign-level negative keywords. |
| `apply_keyword_label` | `keywords` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach a label to a keyword. |
| `apply_shared_list_to_campaign` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Attach a shared negative list to a campaign. |
| `create_shared_negative_keyword_list` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Create a shared negative keyword list. |
| `enable_keyword` | `keywords` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Enable a keyword. |
| `get_keyword` | `keywords` | `query` | `hand_implemented` | GoogleAdsService.Search FROM keyword_view | `read` | no | Get one keyword with bid and quality score fields. |
| `get_keyword_bid_estimates` | `keywords` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Keyword bid estimates are not mapped to a stable high-level helper. Use Keyword Planner idea and forecast services directly only after checking live service metadata. |
| `get_keyword_ideas` | `keywords` | `service` | `generic_routed` | Google Ads service bridge | `read` | depends | Get Keyword Planner ideas. |
| `list_keywords` | `keywords` | `query` | `hand_implemented` | GoogleAdsService.Search FROM keyword_view | `read` | no | List keywords by campaign, ad group, match type, or status. |
| `list_negative_keywords_ad_group` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `read` | no | List ad group-level negative keywords. |
| `list_negative_keywords_campaign` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `read` | no | List campaign-level negative keywords. |
| `list_shared_negative_keyword_lists` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `read` | no | List account-level shared negative keyword lists. |
| `pause_keyword` | `keywords` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Pause a keyword. |
| `remove_keyword_label` | `keywords` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Detach a label from a keyword. |
| `remove_keywords` | `keywords` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Remove one or more keywords. |
| `remove_keywords_from_shared_list` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Remove keywords from a shared negative list. |
| `remove_negative_keywords_ad_group` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Remove ad group-level negative keywords. |
| `remove_negative_keywords_campaign` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Remove campaign-level negative keywords. |
| `remove_shared_list_from_campaign` | `keywords` | `negative_keyword` | `hand_implemented` | GoogleAdsService.Search or GoogleAdsService.Mutate | `write` | no | Detach a shared negative list from a campaign. |
| `update_keyword_bid` | `keywords` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Update CPC bid on a keyword. |
| `apply_label_to_ad` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach label to ads. |
| `apply_label_to_ad_group` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach label to ad groups. |
| `apply_label_to_campaign` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach label to campaigns. |
| `apply_label_to_keyword` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Attach label to keywords. |
| `create_label` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Create a label. |
| `list_labels` | `labels` | `query` | `hand_implemented` | GoogleAdsService.Search FROM label | `read` | no | List account labels. |
| `remove_label` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Remove a label. |
| `remove_label_from_ad` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Detach label from ads. |
| `remove_label_from_ad_group` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Detach label from ad groups. |
| `remove_label_from_campaign` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Detach label from campaigns. |
| `remove_label_from_keyword` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Detach label from keywords. |
| `update_label` | `labels` | `mutate` | `hand_implemented` | GoogleAdsService.Mutate | `write` | no | Update label name, color, or description. |
| `describe_google_ads_resource` | `metadata` | `metadata` | `hand_implemented` | GoogleAdsFieldService.SearchGoogleAdsFields | `read` | no | Describe fields for a Google Ads API resource. |
| `describe_google_ads_service` | `metadata` | `metadata` | `hand_implemented` | Local metadata/introspection | `read` | no | Describe callable methods for a Google Ads service. |
| `get_capability_matrix` | `metadata` | `metadata` | `hand_implemented` | Local tool registry | `read` | no | Return implementation status for the currently exposed tools. |
| `get_google_ads_resource_metadata` | `metadata` | `metadata` | `hand_implemented` | GoogleAdsFieldService.SearchGoogleAdsFields | `read` | no | Return selectable fields, filters, metrics, and segments for a resource. |
| `get_server_status` | `metadata` | `metadata` | `hand_implemented` | Local metadata/introspection | `read` | no | Return server mode, auth mode, config source, and exposed tool count. |
| `get_tool_catalog` | `metadata` | `metadata` | `hand_implemented` | Local metadata/introspection | `read` | no | Return the currently exposed Google Ads MCP tool catalog. |
| `list_google_ads_services` | `metadata` | `metadata` | `hand_implemented` | Local metadata/introspection | `read` | no | List service classes available in the installed Google Ads API client. |
| `query_google_ads_docs` | `metadata` | `kb_lookup` | `hand_implemented` | Offline GAQL knowledge base | `read` | no | Query the offline GAQL knowledge base. |
| `suggest_gaql_fields` | `metadata` | `metadata` | `hand_implemented` | GoogleAdsFieldService.SearchGoogleAdsFields | `read` | no | Suggest GAQL fields from live resource metadata. |
| `validate_gaql_fields` | `metadata` | `validation` | `hand_implemented` | GoogleAdsFieldService.SearchGoogleAdsFields | `read` | no | Validate GAQL SELECT fields against live resource metadata. |
| `validate_google_ads_payload` | `metadata` | `validation` | `hand_implemented` | Protobuf JSON parser | `read` | no | Validate a protobuf JSON payload against a Google Ads message type. |
| `explain_gaql_error` | `planning` | `query_planning` | `hand_implemented` | Static GAQL error helper | `read` | no | Explain common GAQL errors and suggest safe next steps. |
| `get_ad_diagnosis` | `planning` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Ad diagnosis is not mapped to a stable Google Ads API service method in this MCP. Use policy and approval report tools plus live metadata for account-specific diagnosis. |
| `get_ad_preview` | `planning` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Ad preview is not mapped to a stable Google Ads API service method in this MCP. Use Google Ads UI preview tools or live metadata before adding an API helper. |
| `get_reach_forecast` | `planning` | `service` | `generic_routed` | Google Ads service bridge | `read` | yes | Get Reach Planner forecast where available. |
| `plan_gaql_query` | `planning` | `query_planning` | `hand_implemented` | Metadata-backed GAQL planner | `read` | no | Build a validated GAQL query plan without executing it. |
| `apply_recommendation` | `recommendations` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Apply a recommendation. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `dismiss_recommendation` | `recommendations` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Dismiss a recommendation. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_recommendation_types` | `recommendations` | `service` | `generic_routed` | Google Ads service bridge | `read` | depends | List supported recommendation type metadata. |
| `list_recommendations` | `recommendations` | `query` | `hand_implemented` | GoogleAdsService.Search FROM recommendation | `read` | no | List pending Google recommendations. |
| `execute_gaql_query` | `reporting` | `raw_gaql` | `generic_routed` | GoogleAdsService.Search | `read` | no | Execute raw GAQL for uncovered reporting needs. |
| `get_ad_group_metrics` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM ad_group | `read` | no | Ad group metrics with preset or custom date ranges. |
| `get_ad_metrics` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM ad_group_ad | `read` | no | Ad metrics with preset or custom date ranges. |
| `get_ad_schedule_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM campaign | `read` | no | Performance by scheduled time block. |
| `get_age_range_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM age_range_view | `read` | no | Performance by age range. |
| `get_asset_performance_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM asset_group_asset | `read` | no | Asset performance for RSA and PMax. |
| `get_auction_insights` | `reporting` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Auction insight fields are version and account sensitive. Use live metadata and planning_plan_gaql_query before implementing this report. |
| `get_audience_performance_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM ad_group_audience_view | `read` | no | Performance by audience segment. |
| `get_call_details_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM call_view | `read` | no | Call details report. |
| `get_campaign_metrics` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM campaign | `read` | no | Campaign metrics with preset or custom date ranges. |
| `get_change_history_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM change_event | `read` | no | Change history report. |
| `get_day_of_week_performance` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM campaign | `read` | no | Performance by day of week. |
| `get_device_performance` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM campaign | `read` | no | Performance by device. |
| `get_display_performance_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM campaign | `read` | no | Display network performance. |
| `get_gender_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM gender_view | `read` | no | Performance by gender. |
| `get_geo_performance` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM geographic_view | `read` | no | Performance by geographic target id and readable name. |
| `get_hour_of_day_performance` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM campaign | `read` | no | Performance by hour of day. |
| `get_household_income_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM income_range_view | `read` | no | Performance by household income. |
| `get_keyword_metrics` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM keyword_view | `read` | no | Keyword metrics plus quality score fields. |
| `get_landing_page_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM landing_page_view | `read` | no | Landing page performance. |
| `get_paid_organic_report` | `reporting` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Paid and organic reporting depends on Search Console linkage and version-specific fields. Use live metadata before building this report. |
| `get_parental_status_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM parental_status_view | `read` | no | Performance by parental status. |
| `get_placement_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM group_placement_view | `read` | no | Display placement performance. |
| `get_reach_frequency_report` | `reporting` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Reach and frequency reporting is not a universal GAQL view. Use live metadata to confirm compatible reach/frequency fields before querying. |
| `get_search_terms_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM search_term_view | `read` | no | Search query performance report. |
| `get_shopping_performance_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM shopping_performance_view | `read` | no | Shopping product performance. |
| `get_topic_report` | `reporting` | `unsupported` | `unsupported_by_design` | n/a | `read` | no | Topic performance fields are version and campaign-type sensitive. Use live metadata and planning_plan_gaql_query to build a topic-compatible GAQL query for the target account. |
| `get_video_performance_report` | `reporting` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM video | `read` | no | Video performance report. |
| `create_listing_group_tree` | `shopping_pmax` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a Shopping listing group tree. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `create_pmax_asset_group` | `shopping_pmax` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Create a PMax asset group. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `get_pmax_asset_group` | `shopping_pmax` | `query` | `hand_implemented` | GoogleAdsService.Search FROM asset_group | `read` | no | Get one PMax asset group. |
| `get_pmax_asset_group_performance` | `shopping_pmax` | `report` | `hand_implemented` | GoogleAdsService.Search report FROM asset_group | `read` | no | Report PMax asset group performance. |
| `get_pmax_campaign_insights` | `shopping_pmax` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Report PMax campaign insights. |
| `get_pmax_search_term_themes` | `shopping_pmax` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Get PMax search term themes where exposed. |
| `get_shopping_campaign_settings` | `shopping_pmax` | `service` | `generic_routed` | Google Ads service bridge | `generic` | depends | Get Merchant Center and Shopping campaign settings. |
| `list_pmax_asset_groups` | `shopping_pmax` | `query` | `hand_implemented` | GoogleAdsService.Search FROM asset_group | `read` | no | List PMax asset groups. |
| `remove_listing_group` | `shopping_pmax` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove a listing group node. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_pmax_asset_group` | `shopping_pmax` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove a PMax asset group. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_pmax_audience_signals` | `shopping_pmax` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set PMax audience signals and search themes. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_listing_group` | `shopping_pmax` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Update a listing group node. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `update_pmax_asset_group` | `shopping_pmax` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Update a PMax asset group. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_audience_to_ad_group` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Add ad group audience targeting or observation. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_audience_to_campaign` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Add campaign audience targeting or observation. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_content_label_exclusions` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Add sensitive content exclusions. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_placement_exclusions` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Add placement exclusions. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_placement_targeting` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Add placement targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `add_topic_targeting` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Add GDN topic targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_audience_from_ad_group` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove ad group audience targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_audience_from_campaign` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove campaign audience targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `remove_topic_targeting` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Remove GDN topic targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
| `set_demographic_targeting` | `targeting` | `mutate` | `operation_template` | GoogleAdsService.Mutate | `write` | no | Template only: Set age, gender, parental, or household targeting. Supply raw GoogleAdsService MutateOperation payloads in payload.operations. |
