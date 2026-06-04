# Write Safety

All mutating tools default to `validate_only=true`.

To commit a write, every write path requires:

- `execute=true`
- `validate_only=false`
- `confirmation_phrase="CONFIRM_GOOGLE_ADS_WRITE"`
- explicit `customer_id`

This applies to:

- `google_ads_mutate`
- `google_ads_call_service` when `is_write=true` or the method name looks mutating
- friendly campaign/budget/ad/ad group/keyword/asset/audience/conversion tools
- negative keyword helpers
- bulk mutation helpers

Validation-only requests still call Google Ads in validation mode and may consume API quota, but they do not commit external changes.

Bulk writes can set:

- `partial_failure=false` to roll back the whole request when one operation fails
- `partial_failure=true` to allow successful operations and return per-operation failures

