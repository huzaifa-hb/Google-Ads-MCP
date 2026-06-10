"""Local OS keyring helpers for setup-time secret references."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

KEYRING_SERVICE = "google-ads-mcp"
KEYRING_REF_PREFIX = f"keyring://{KEYRING_SERVICE}/"


class LocalSecretError(RuntimeError):
    """Raised when a local secret reference cannot be stored or resolved."""


def local_secret_namespace(path: Path | str) -> str:
    expanded = Path(path).expanduser()
    try:
        normalized = str(expanded.resolve())
    except OSError:
        normalized = str(expanded.absolute())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:16]


def is_local_secret_reference(value: str | None) -> bool:
    return bool(value and value.strip().startswith(KEYRING_REF_PREFIX))


def local_secret_reference(namespace: str, name: str) -> str:
    return f"{KEYRING_REF_PREFIX}{namespace}/{name}"


def store_local_secret(namespace: str, name: str, value: str) -> str:
    try:
        _load_keyring().set_password(KEYRING_SERVICE, _keyring_account(namespace, name), value)
    except Exception as exc:  # pragma: no cover - backend-specific failures vary.
        raise LocalSecretError(
            "Unable to store local secret in the OS keyring. Install a working keyring backend "
            "or use --print-refresh-token and store secrets outside the env file."
        ) from exc
    return local_secret_reference(namespace, name)


def resolve_local_secret_reference(value: str) -> str:
    if not is_local_secret_reference(value):
        return value
    namespace, name = _parse_reference(value)
    try:
        secret = _load_keyring().get_password(KEYRING_SERVICE, _keyring_account(namespace, name))
    except Exception as exc:  # pragma: no cover - backend-specific failures vary.
        raise LocalSecretError(
            f"Unable to read local secret reference {value!r} from the OS keyring."
        ) from exc
    if not secret:
        raise LocalSecretError(f"Local secret reference {value!r} was not found in the OS keyring.")
    return secret


def _parse_reference(value: str) -> tuple[str, str]:
    parsed = urlparse(value)
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.scheme != "keyring" or parsed.netloc != KEYRING_SERVICE or len(parts) != 2:
        raise LocalSecretError(f"Invalid local secret reference: {value!r}.")
    return parts[0], parts[1]


def _keyring_account(namespace: str, name: str) -> str:
    return f"{namespace}:{name}"


def _load_keyring() -> Any:
    try:
        import keyring
    except ImportError as exc:  # pragma: no cover - covered by packaging metadata.
        raise LocalSecretError(
            "keyring is required for local secret references. Install setup extras or use "
            "--print-refresh-token."
        ) from exc
    return keyring
