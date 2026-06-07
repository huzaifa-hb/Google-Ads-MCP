# Live Metadata

The main guide is `docs/live-metadata-and-gaql-planning.md`.

Use `metadata_get_google_ads_resource_metadata` before writing raw GAQL. It
calls GoogleAdsFieldService, caches by API version and resource, and returns
selectable fields, filterable fields, sortable fields, compatible metrics, and
compatible segments.

Cache controls:

- `GOOGLE_ADS_METADATA_CACHE_TTL_SECONDS` defaults to `3600`.
- `GOOGLE_ADS_METADATA_CACHE_MAX_ENTRIES` defaults to `64`.
- `GOOGLE_ADS_METADATA_SNAPSHOT_PATH` can point to a reviewed JSON fallback used
  only when live metadata is unavailable.
