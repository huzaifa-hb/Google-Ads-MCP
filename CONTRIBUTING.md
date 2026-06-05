# Contributing

Keep changes small, testable, and safe by default.

## Local Checks

```powershell
python -m compileall src scripts tests
python -m unittest discover -s tests
python scripts/check_generated_docs.py
python scripts/scan_for_secrets.py
```

Regenerate docs after changing tool metadata:

```powershell
python scripts/generate_tool_catalog.py
python scripts/generate_kb_docs.py
python scripts/generate_capability_matrix.py
```

## Safety Rules

- Do not make real writes easier to execute.
- Keep `safe_read_only` as the default.
- Route every write path through `guard_google_ads_write`.
- Do not log raw payloads, secrets, customer data, invoice data, or audience data.
- Add tests for new config, mode, metadata, and write-gate behavior.
