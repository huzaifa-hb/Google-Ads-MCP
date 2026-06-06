# GAQL Knowledge Base

This file is generated from `src/google_ads_mcp/knowledge_base.py`.

## Assets

### `asset-performance`

**Question:** How do I get RSA or PMax asset performance?

Use asset_group_asset for PMax asset group assets. performance_label values include BEST, GOOD, LOW, PENDING, and UNRATED.

| Example | Primary Field | GAQL |
|---|---|---|
| Asset group asset performance | `asset.id` | `SELECT asset.id, asset_group.id, asset_group_asset.field_type, asset_group_asset.primary_status, metrics.impressions, metrics.clicks, metrics.conversions FROM asset_group_asset WHERE segments.date DURING LAST_30_DAYS` |
| Limited assets | `asset.id` | `SELECT asset.id, asset_group.id, asset_group_asset.field_type, asset_group_asset.primary_status FROM asset_group_asset WHERE asset_group_asset.primary_status = LIMITED AND segments.date DURING LAST_30_DAYS` |

## Audiences

### `audience-performance`

**Question:** How do I get audience performance?

Use ad_group_audience_view and include user_list.id in SELECT.

| Example | Primary Field | GAQL |
|---|---|---|
| Audience performance | `user_list.id` | `SELECT user_list.id, user_list.name, campaign.id, ad_group.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM ad_group_audience_view WHERE segments.date DURING LAST_30_DAYS` |
| Audience conversions | `user_list.id` | `SELECT user_list.id, user_list.name, campaign.id, metrics.conversions, metrics.conversions_value FROM ad_group_audience_view WHERE segments.date DURING LAST_30_DAYS` |

**See also:** `manager-account-limits`

## Change History

### `change-history`

**Question:** How do I get change history?

Use change_event. It has a hard 30-day maximum lookback regardless of date filter.

| Example | Primary Field | GAQL |
|---|---|---|
| Recent changes | `change_event.resource_name` | `SELECT change_event.resource_name, change_event.change_date_time, change_event.user_email, change_event.change_resource_name, change_event.change_resource_type, change_event.resource_change_operation FROM change_event WHERE change_event.change_date_time DURING LAST_14_DAYS LIMIT 500` |
| Campaign changes | `change_event.resource_name` | `SELECT change_event.resource_name, change_event.change_date_time, change_event.change_resource_name, change_event.resource_change_operation FROM change_event WHERE change_event.change_resource_type = CAMPAIGN AND change_event.change_date_time DURING LAST_30_DAYS LIMIT 500` |

**Notes**

- Do not use ALL_TIME. Keep LIMIT around 100-500.

**See also:** `common-errors`

## Conversions

### `conversion-fields`

**Question:** What is the difference between conversions and all_conversions?

metrics.conversions counts only conversion actions with include_in_conversions_metric = TRUE. metrics.all_conversions counts broader conversion activity including actions excluded from the main conversions column. Value fields follow the same split.

| Example | Primary Field | GAQL |
|---|---|---|
| Conversion action settings | `conversion_action.id` | `SELECT conversion_action.id, conversion_action.name, conversion_action.include_in_conversions_metric, conversion_action.category, conversion_action.status FROM conversion_action` |

**See also:** `metric-field-names`

## Errors

### `primary-field-requirement`

**Question:** Why do I get EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE?

Include the primary field for the resource you query or reference. Common primaries: campaign -> campaign.id; ad_group -> ad_group.id; ad_group_ad -> ad_group_ad.ad.id; keyword_view -> ad_group_criterion.criterion_id; ad_group_criterion -> ad_group_criterion.criterion_id; search_term_view -> search_term_view.search_term; geographic_view -> campaign.id; age_range_view -> ad_group_criterion.criterion_id; gender_view -> ad_group_criterion.criterion_id; income_range_view -> ad_group_criterion.criterion_id; parental_status_view -> ad_group_criterion.criterion_id; ad_group_audience_view -> user_list.id; group_placement_view -> group_placement_view.placement; asset_group_asset -> asset.id; video -> video.id; shopping_performance_view -> campaign.id; landing_page_view -> landing_page_view.unexpanded_final_url; call_view -> call_view.resource_name; change_event -> change_event.resource_name; bidding_strategy -> bidding_strategy.id; campaign_budget -> campaign_budget.id; label -> label.id; user_list -> user_list.id; conversion_action -> conversion_action.id; asset -> asset.id; asset_group -> asset_group.id; recommendation -> recommendation.resource_name.

| Example | Primary Field | GAQL |
|---|---|---|
| Correct campaign query with primary field | `campaign.id` | `SELECT campaign.id, campaign.name, metrics.clicks FROM campaign WHERE segments.date DURING LAST_7_DAYS` |

**Notes**

- This is the most common GAQL error when an LLM writes queries from memory.

**See also:** `common-errors`, `available-resources`

### `common-errors`

**Question:** What are the most common GAQL errors and how do I fix them?

EXPECTED_REFERENCED_FIELD_IN_SELECT_CLAUSE means add the primary field. INVALID_FIELD_NAME usually means typo or wrong resource. FIELD_NOT_SELECTABLE/FILTERABLE means the field exists but cannot be used in that clause. PROHIBITED_FIELD_COMBINATION means incompatible fields or segments. RESOURCE_EXHAUSTED means quota/rate limits. QUERY_ERROR means malformed GAQL.

**Notes**

- Use describe_google_ads_resource to check selectable and filterable flags.
- String literals use single quotes; enum values are unquoted.

**See also:** `primary-field-requirement`, `segment-compatibility`, `no-metrics-resources`

## Filters

### `date-range-custom`

**Question:** How do I use a custom date range?

Use WHERE segments.date BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'. Both dates are required and the range is inclusive.

| Example | Primary Field | GAQL |
|---|---|---|
| January campaign metrics | `campaign.id` | `SELECT campaign.id, campaign.name, metrics.clicks, metrics.cost_micros FROM campaign WHERE segments.date BETWEEN '2025-01-01' AND '2025-01-31'` |

**Notes**

- Date strings must be real calendar dates in YYYY-MM-DD format.

**See also:** `date-range-presets`

### `resource-name-format`

**Question:** What is the format of a resource_name?

Common formats: customers/{customer_id}/campaigns/{campaign_id}; customers/{customer_id}/adGroups/{ad_group_id}; customers/{customer_id}/adGroupAds/{ad_group_id}~{ad_id}; customers/{customer_id}/adGroupCriteria/{ad_group_id}~{criterion_id}; customers/{customer_id}/campaignBudgets/{budget_id}; customers/{customer_id}/labels/{label_id}.

**Notes**

- Customer IDs are digits only, no dashes.

**See also:** `primary-field-requirement`, `filters-operators`

### `filters-operators`

**Question:** How do filters and operators work in GAQL?

WHERE supports equality, comparisons, IN lists, BETWEEN ranges, DURING date presets, LIKE, CONTAINS ANY, CONTAINS ALL, and CONTAINS NONE where a field allows it. String literals use single quotes; enum values such as ENABLED are unquoted.

| Example | Primary Field | GAQL |
|---|---|---|
| Enabled campaigns in a set | `campaign.id` | `SELECT campaign.id, campaign.name FROM campaign WHERE campaign.status = ENABLED AND campaign.id IN (111, 222)` |

**Notes**

- Use describe_google_ads_resource to verify filterable=true before adding a field to WHERE.

## Limitations

### `no-metrics-resources`

**Question:** Which resources do not support metrics?

Do not add metrics fields to customer_client, product_link, account_budget, billing_setup, shared_set, label, shared_criterion, or campaign_shared_set.

**Notes**

- Use these resources for structure/configuration, not performance reporting.

**See also:** `available-resources`, `common-errors`

### `manager-account-limits`

**Question:** What cannot be done from a manager or MCC account?

Metric queries must use a leaf customer ID. Manager accounts are mainly for customer_client hierarchy traversal. Mutate operations require the target leaf account.

**Notes**

- Customer IDs should be digits only, without dashes.

**See also:** `primary-field-requirement`

### `impression-share-null`

**Question:** Why are impression share fields returning null?

Search impression share fields require enough auction volume. Below Google's privacy or minimum-data thresholds, they return null.

**Notes**

- Impression share should not be segmented by hour or day of week.

**See also:** `auction-insights`, `metric-field-names`

## Metrics

### `metric-field-names`

**Question:** What are the exact field names for common metrics?

Common fields: metrics.impressions, clicks, cost_micros, average_cpc, average_cost, ctr, conversions, all_conversions, conversions_value, all_conversions_value, cost_per_conversion, conversion_rate, engagements, video_views, view_rate, search_impression_share, search_budget_lost_impression_share, search_rank_lost_impression_share, search_top_impression_share, search_absolute_top_impression_share. Keyword quality fields live under ad_group_criterion.quality_info.

**Notes**

- Cost fields are micros; divide by 1,000,000 for account currency.
- CTR and impression share fields are fractions. Impression share can be null with low volume.

**See also:** `keyword-metrics`, `impression-share-null`, `conversion-fields`

## Pagination

### `pagination-patterns`

**Question:** How does GAQL pagination work?

Google Ads search supports page_size and page_token for API paging. GAQL has LIMIT but no OFFSET clause. This MCP returns has_more and next_page_token when available.

| Example | Primary Field | GAQL |
|---|---|---|
| Small first page | `campaign.id` | `SELECT campaign.id, campaign.name FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY campaign.id LIMIT 100` |

**Notes**

- For large reports, use page_token rather than trying to emulate OFFSET.

## Reporting

### `campaign-metrics`

**Question:** How do I get campaign performance metrics?

Use the campaign resource with campaign.id in SELECT and a date filter.

| Example | Primary Field | GAQL |
|---|---|---|
| Last 30 days all campaigns | `campaign.id` | `SELECT campaign.id, campaign.name, campaign.status, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.ctr, metrics.average_cpc, metrics.conversions, metrics.cost_per_conversion, metrics.search_impression_share FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC` |
| Specific campaign by ID | `campaign.id` | `SELECT campaign.id, campaign.name, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE campaign.id = 1234567890 AND segments.date DURING LAST_7_DAYS` |
| Enabled only this month | `campaign.id` | `SELECT campaign.id, campaign.name, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE campaign.status = ENABLED AND segments.date DURING THIS_MONTH` |
| Daily breakdown | `campaign.id` | `SELECT campaign.id, campaign.name, segments.date, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY segments.date DESC` |

**See also:** `ad-group-metrics`, `device-performance`, `auction-insights`

### `ad-group-metrics`

**Question:** How do I get ad group performance metrics?

Use FROM ad_group and include ad_group.id plus campaign.id for context.

| Example | Primary Field | GAQL |
|---|---|---|
| Last 30 days ad groups | `ad_group.id` | `SELECT ad_group.id, ad_group.name, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM ad_group WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC` |
| Ad groups in one campaign | `ad_group.id` | `SELECT ad_group.id, ad_group.name, campaign.id, metrics.impressions, metrics.clicks FROM ad_group WHERE campaign.id = 1234567890 AND segments.date DURING LAST_7_DAYS` |

**See also:** `campaign-metrics`, `keyword-metrics`

### `keyword-metrics`

**Question:** How do I get keyword performance including Quality Score?

Use keyword_view and include ad_group_criterion.criterion_id. Quality Score fields are on ad_group_criterion.quality_info and may be absent when volume is too low.

| Example | Primary Field | GAQL |
|---|---|---|
| All keywords with QS | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type, ad_group_criterion.quality_info.quality_score, ad_group_criterion.quality_info.search_predicted_ctr, ad_group_criterion.quality_info.creative_quality_score, ad_group_criterion.quality_info.post_click_quality_score, ad_group.id, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.average_cpc, metrics.conversions FROM keyword_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.impressions DESC` |
| Exact keywords only | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.keyword.text, ad_group.id, campaign.id, metrics.clicks, metrics.cost_micros FROM keyword_view WHERE ad_group_criterion.keyword.match_type = EXACT AND segments.date DURING LAST_30_DAYS` |

**Notes**

- Quality Score is 1-10 and can be missing for low-impression keywords.

**See also:** `search-terms-report`, `metric-field-names`

### `search-terms-report`

**Question:** How do I get the search terms report?

Use search_term_view. Include search_term_view.search_term, status, ad_group.id, and campaign.id.

| Example | Primary Field | GAQL |
|---|---|---|
| Search terms last 30 days | `search_term_view.search_term` | `SELECT search_term_view.search_term, search_term_view.status, ad_group.id, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM search_term_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC` |
| Search terms for one campaign | `search_term_view.search_term` | `SELECT search_term_view.search_term, search_term_view.status, ad_group.id, campaign.id, metrics.clicks FROM search_term_view WHERE campaign.id = 1234567890 AND segments.date DURING LAST_14_DAYS` |

**Notes**

- ALL_TIME is supported here but not on all resources.

**See also:** `keyword-metrics`, `campaign-metrics`

### `auction-insights`

**Question:** How do I get auction insights or impression share data?

Use campaign-level impression share metrics. Competitor names and overlap rates are not exposed by the API.

| Example | Primary Field | GAQL |
|---|---|---|
| Enabled campaigns impression share | `campaign.id` | `SELECT campaign.id, campaign.name, metrics.search_impression_share, metrics.search_budget_lost_impression_share, metrics.search_rank_lost_impression_share, metrics.search_top_impression_share, metrics.search_absolute_top_impression_share FROM campaign WHERE campaign.status = ENABLED AND segments.date DURING LAST_30_DAYS ORDER BY metrics.search_impression_share ASC` |
| Campaign IS last 7 days | `campaign.id` | `SELECT campaign.id, campaign.name, metrics.search_impression_share, metrics.search_rank_lost_impression_share FROM campaign WHERE segments.date DURING LAST_7_DAYS` |

**Notes**

- Competitor domains and overlap metrics are not available via Google Ads API GAQL.

**See also:** `impression-share-null`, `campaign-metrics`

### `device-performance`

**Question:** How do I get device performance?

Use segments.device on campaign or ad_group resources. Values include MOBILE, DESKTOP, TABLET, CONNECTED_TV, and OTHER.

| Example | Primary Field | GAQL |
|---|---|---|
| Campaign by device | `campaign.id` | `SELECT campaign.id, campaign.name, segments.device, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS` |
| Ad groups by device | `ad_group.id` | `SELECT ad_group.id, campaign.id, segments.device, metrics.clicks, metrics.cost_micros FROM ad_group WHERE segments.date DURING LAST_14_DAYS` |

**See also:** `campaign-metrics`

### `geo-performance`

**Question:** How do I get geo performance?

Use geographic_view. It returns criterion IDs, not readable names; map IDs through geo_target_constant or a local lookup.

| Example | Primary Field | GAQL |
|---|---|---|
| Geo by country criterion | `campaign.id` | `SELECT campaign.id, geographic_view.country_criterion_id, metrics.impressions, metrics.clicks, metrics.cost_micros FROM geographic_view WHERE segments.date DURING LAST_30_DAYS` |
| Geo for one campaign | `campaign.id` | `SELECT campaign.id, geographic_view.country_criterion_id, metrics.conversions, metrics.cost_micros FROM geographic_view WHERE campaign.id = 1234567890 AND segments.date DURING LAST_30_DAYS` |

**Notes**

- This MCP contains a local geo target lookup for common IDs, an optional GOOGLE_ADS_GEO_TARGETS_CSV runtime override, and a refresh script.

**See also:** `resource-name-format`

### `hour-of-day`

**Question:** How do I get hour of day performance?

Use segments.hour, which returns values 0 through 23.

| Example | Primary Field | GAQL |
|---|---|---|
| Campaign by hour | `campaign.id` | `SELECT campaign.id, segments.hour, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY segments.hour` |
| Ad group by hour | `ad_group.id` | `SELECT ad_group.id, campaign.id, segments.hour, metrics.clicks, metrics.conversions FROM ad_group WHERE segments.date DURING LAST_7_DAYS ORDER BY segments.hour` |

**Notes**

- Do not combine segments.hour and segments.day_of_week in the same query.

**See also:** `day-of-week`, `segment-compatibility`

### `day-of-week`

**Question:** How do I get day of week performance?

Use segments.day_of_week. Values are MONDAY through SUNDAY.

| Example | Primary Field | GAQL |
|---|---|---|
| Campaign by day of week | `campaign.id` | `SELECT campaign.id, segments.day_of_week, metrics.impressions, metrics.clicks, metrics.cost_micros FROM campaign WHERE segments.date DURING LAST_30_DAYS ORDER BY segments.day_of_week` |
| Ad group by day of week | `ad_group.id` | `SELECT ad_group.id, campaign.id, segments.day_of_week, metrics.conversions FROM ad_group WHERE segments.date DURING LAST_30_DAYS` |

**Notes**

- Do not combine segments.hour and segments.day_of_week in the same query.

**See also:** `hour-of-day`

### `age-range`

**Question:** How do I get age range performance?

Use age_range_view and ad_group_criterion.age_range.type.

| Example | Primary Field | GAQL |
|---|---|---|
| Age range performance | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.age_range.type, ad_group.id, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros FROM age_range_view WHERE segments.date DURING LAST_30_DAYS` |
| Age conversions | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.age_range.type, campaign.id, metrics.conversions FROM age_range_view WHERE segments.date DURING LAST_30_DAYS` |

**Notes**

- Values include AGE_RANGE_18_24 through AGE_RANGE_65_UP and AGE_RANGE_UNDETERMINED.

### `gender`

**Question:** How do I get gender performance?

Use gender_view and ad_group_criterion.gender.type.

| Example | Primary Field | GAQL |
|---|---|---|
| Gender performance | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.gender.type, ad_group.id, campaign.id, metrics.impressions, metrics.clicks FROM gender_view WHERE segments.date DURING LAST_30_DAYS` |
| Gender conversions | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.gender.type, campaign.id, metrics.conversions FROM gender_view WHERE segments.date DURING LAST_30_DAYS` |

**Notes**

- Values include MALE, FEMALE, and UNDETERMINED.

### `parental-status`

**Question:** How do I get parental status performance?

Use parental_status_view and ad_group_criterion.parental_status.type.

| Example | Primary Field | GAQL |
|---|---|---|
| Parental status performance | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.parental_status.type, ad_group.id, campaign.id, metrics.impressions, metrics.clicks FROM parental_status_view WHERE segments.date DURING LAST_30_DAYS` |
| Parental status conversions | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.parental_status.type, campaign.id, metrics.conversions FROM parental_status_view WHERE segments.date DURING LAST_30_DAYS` |

**Notes**

- Values include PARENT, NOT_A_PARENT, and UNDETERMINED.

### `household-income`

**Question:** How do I get household income performance?

Use income_range_view and ad_group_criterion.income_range.type.

| Example | Primary Field | GAQL |
|---|---|---|
| Household income performance | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.income_range.type, ad_group.id, campaign.id, metrics.impressions, metrics.clicks FROM income_range_view WHERE segments.date DURING LAST_30_DAYS` |
| Household income cost | `ad_group_criterion.criterion_id` | `SELECT ad_group_criterion.criterion_id, ad_group_criterion.income_range.type, campaign.id, metrics.cost_micros, metrics.conversions FROM income_range_view WHERE segments.date DURING LAST_30_DAYS` |

**Notes**

- Values include INCOME_RANGE_0_50 through INCOME_RANGE_90_UP and UNDETERMINED.

### `placement-report`

**Question:** How do I get display placement performance?

Use group_placement_view for Display placements. The primary field is group_placement_view.placement.

| Example | Primary Field | GAQL |
|---|---|---|
| Placement report | `group_placement_view.placement` | `SELECT group_placement_view.placement, campaign.id, ad_group.id, metrics.impressions, metrics.clicks, metrics.cost_micros FROM group_placement_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC` |
| Placement conversions | `group_placement_view.placement` | `SELECT group_placement_view.placement, campaign.id, metrics.conversions FROM group_placement_view WHERE segments.date DURING LAST_30_DAYS` |

### `landing-page-performance`

**Question:** How do I get landing page performance?

Use landing_page_view and include landing_page_view.unexpanded_final_url plus campaign.id.

| Example | Primary Field | GAQL |
|---|---|---|
| Landing page report | `landing_page_view.unexpanded_final_url` | `SELECT landing_page_view.unexpanded_final_url, campaign.id, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM landing_page_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC` |
| Landing pages this month | `landing_page_view.unexpanded_final_url` | `SELECT landing_page_view.unexpanded_final_url, campaign.id, metrics.clicks FROM landing_page_view WHERE segments.date DURING THIS_MONTH` |

### `call-details`

**Question:** How do I get call details?

Use call_view. Date filter is required.

| Example | Primary Field | GAQL |
|---|---|---|
| Call details | `call_view.resource_name` | `SELECT call_view.resource_name, call_view.call_duration_seconds, call_view.call_status, call_view.call_tracking_display_location, campaign.id FROM call_view WHERE segments.date DURING LAST_30_DAYS` |
| Long calls | `call_view.resource_name` | `SELECT call_view.resource_name, call_view.call_duration_seconds, campaign.id FROM call_view WHERE call_view.call_duration_seconds > 60 AND segments.date DURING LAST_30_DAYS` |

### `bidding-strategy-report`

**Question:** How do I get bidding strategy performance?

Use campaign.bidding_strategy_type as the campaign-level segment/dimension.

| Example | Primary Field | GAQL |
|---|---|---|
| Bidding strategy by campaign | `campaign.id` | `SELECT campaign.id, campaign.name, campaign.bidding_strategy_type, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM campaign WHERE segments.date DURING LAST_30_DAYS` |
| Target CPA campaigns | `campaign.id` | `SELECT campaign.id, campaign.name, campaign.bidding_strategy_type, metrics.cost_per_conversion, metrics.conversions FROM campaign WHERE campaign.bidding_strategy_type = TARGET_CPA AND segments.date DURING LAST_30_DAYS` |

**Notes**

- Common values include TARGET_CPA, TARGET_ROAS, MAXIMIZE_CONVERSIONS, MAXIMIZE_CONVERSION_VALUE, MANUAL_CPC, and TARGET_IMPRESSION_SHARE. target_roas is a ratio, so 4.0 means 400%.

## Resources

### `available-resources`

**Question:** What resources are available in GAQL?

Core reporting: campaign, ad_group, ad_group_ad, keyword_view, ad_group_criterion, search_term_view. Segment views: geographic_view, age_range_view, gender_view, income_range_view, parental_status_view, ad_group_audience_view, group_placement_view. Entities: campaign_budget, bidding_strategy, label, asset, asset_group, asset_group_asset, user_list, conversion_action, recommendation. Other/special: shopping_performance_view, video, landing_page_view, call_view, change_event, product_link, account_budget, billing_setup.

**Notes**

- Not every resource supports metrics. Check no-metrics-resources before adding metric fields.

**See also:** `no-metrics-resources`, `primary-field-requirement`

## Segments

### `segment-compatibility`

**Question:** Which segments can I use together and what cannot be combined?

Common segments include segments.date, hour, day_of_week, week, month, device, slot, product_item_id, product_title, and network. Adding a segment changes the grain: one row per segment value rather than an aggregate total.

**Notes**

- segments.hour cannot combine with segments.date in many report queries.
- segments.slot is search-only. Shopping product segments belong on shopping resources.

**See also:** `common-errors`, `shopping-performance`, `hour-of-day`

## Shopping

### `shopping-performance`

**Question:** How do I get Shopping product performance?

Use shopping_performance_view and product segments such as product_item_id, product_title, product_brand, and product_category_level1.

| Example | Primary Field | GAQL |
|---|---|---|
| Shopping product report | `campaign.id` | `SELECT campaign.id, segments.product_item_id, segments.product_title, metrics.impressions, metrics.clicks, metrics.cost_micros, metrics.conversions FROM shopping_performance_view WHERE segments.date DURING LAST_30_DAYS ORDER BY metrics.cost_micros DESC` |
| Shopping brand report | `campaign.id` | `SELECT campaign.id, segments.product_brand, segments.product_category_level1, metrics.clicks, metrics.cost_micros FROM shopping_performance_view WHERE segments.date DURING LAST_30_DAYS` |

**Notes**

- Shopping product segments only belong on Shopping-compatible resources.

## Syntax

### `gaql-syntax`

**Question:** How does GAQL syntax work?

GAQL uses SELECT, FROM, WHERE, ORDER BY, and LIMIT, but it is not SQL. There are no JOINs or subqueries, and FROM always names one Google Ads resource. String literals use single quotes, enum literals are unquoted, and numeric filters use normal comparisons.

**Notes**

- Metrics are only available on compatible resources, and most metric queries need a date filter.
- Use AND/OR carefully; incompatible metrics and segments fail with query errors.

**See also:** `primary-field-requirement`, `common-errors`, `segment-compatibility`

### `date-range-presets`

**Question:** What date range presets are available?

Use segments.date DURING with TODAY, YESTERDAY, LAST_7_DAYS, LAST_14_DAYS, LAST_30_DAYS, LAST_90_DAYS, THIS_MONTH, LAST_MONTH, or ALL_TIME.

| Example | Primary Field | GAQL |
|---|---|---|
| Last 30 days clicks by campaign | `campaign.id` | `SELECT campaign.id, metrics.clicks FROM campaign WHERE segments.date DURING LAST_30_DAYS` |

**Notes**

- ALL_TIME does not work on all resources. change_event has a 30-day maximum lookback.

**See also:** `date-range-custom`, `change-history`

## Video

### `video-performance`

**Question:** How do I get video campaign performance?

Use the video resource with video.id and YouTube video fields. Duration is exposed as video.duration_millis.

| Example | Primary Field | GAQL |
|---|---|---|
| Video performance | `video.id` | `SELECT video.id, video.title, video.channel_id, video.duration_millis, metrics.video_trueview_views, metrics.video_trueview_view_rate, metrics.video_quartile_p25_rate, metrics.video_quartile_p50_rate, metrics.video_quartile_p100_rate FROM video WHERE segments.date DURING LAST_30_DAYS` |
| Video cost and conversions | `video.id` | `SELECT video.id, video.title, metrics.impressions, metrics.video_trueview_views, metrics.cost_micros, metrics.conversions FROM video WHERE segments.date DURING LAST_30_DAYS` |

**Notes**

- The current Google Ads field is video.duration_millis, not video.duration_seconds.
