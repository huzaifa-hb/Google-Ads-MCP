# Write Safety

The server starts in `safe_read_only` mode by default. In that mode, mutating
tools and generic service bridge tools are not exposed.

Supported modes:

- `safe_read_only`: read/reporting/docs/metadata tools only.
- `validation_only`: configured mutation tools are exposed, but every write is
  forced to `validate_only=true`.
- `write_enabled`: configured mutation tools can commit real writes only after
  explicit confirmation.
- `admin_debug`: generic bridge tools can be exposed by config; real writes
  still require explicit confirmation.

All mutating tools default to `validate_only=true`.

To commit a write, every write path requires:

- `execute=true`
- `validate_only=false`
- `confirmation_phrase="CONFIRM_GOOGLE_ADS_WRITE"`
- explicit `customer_id`

This applies to:

- `google_ads_mutate`
- `google_ads_call_service` when `is_write=true` or the method name looks mutating
- `google_ads_call_service` for unknown read methods unless the method is allowlisted
  or `admin_debug` plus `GOOGLE_ADS_MCP_ENABLE_GENERIC_SERVICE_BRIDGE=true` is used
- friendly campaign/budget/ad/ad group/keyword/asset/audience/conversion tools
- negative keyword helpers
- bulk mutation helpers

Validation-only requests still call Google Ads in validation mode and may consume API quota, but they do not commit external changes.

Every write attempt emits a structured audit event with the mode, tool name,
operation count, result, and a hashed customer ID. Audit events must not include
developer tokens, refresh tokens, bearer tokens, raw payloads, audience upload
data, invoice files, or raw customer data.

Bulk writes can set:

- `partial_failure=false` to roll back the whole request when one operation fails
- `partial_failure=true` to allow successful operations and return per-operation failures

