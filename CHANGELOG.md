# Changelog

## Unreleased

- Defaulted the server to `safe_read_only` with configurable tool exposure.
- Added namespaced tool registration and a filtered `get_tool_catalog`.
- Added shared write guard, validation-only forcing, and structured write audit events.
- Added live Google Ads resource metadata, GAQL field validation, suggestions, planning, and error explanation.
- Added read-only MCP resources for discovery references, metrics, segments, release notes, tool catalog, capability matrix, and GAQL knowledge base.
- Added generated capability matrix, stale generated-doc checks, secret scanning, and CI.
- Added optional OAuth proxy MCP auth mode while keeping bearer auth as default.
