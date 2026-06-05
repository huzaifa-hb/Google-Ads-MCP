# Live Metadata

The main guide is `docs/live-metadata-and-gaql-planning.md`.

Use `metadata_get_google_ads_resource_metadata` before writing raw GAQL. It
calls GoogleAdsFieldService, caches by API version and resource, and returns
selectable fields, filterable fields, sortable fields, compatible metrics, and
compatible segments.
