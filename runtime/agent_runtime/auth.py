from __future__ import annotations

import os


DEFAULT_DEV_TENANT = "local-dev"
DEFAULT_DEV_KEY = "local-dev-key"


def load_api_key_map() -> dict[str, str]:
    raw = os.getenv("AGENT_RUNTIME_API_KEYS", "").strip()
    if not raw:
        return {DEFAULT_DEV_TENANT: DEFAULT_DEV_KEY}

    mapping: dict[str, str] = {}
    for pair in raw.split(","):
        tenant_key = pair.strip()
        if not tenant_key:
            continue
        if ":" not in tenant_key:
            continue
        tenant, key = tenant_key.split(":", 1)
        tenant = tenant.strip()
        key = key.strip()
        if tenant and key:
            mapping[tenant] = key

    if not mapping:
        return {DEFAULT_DEV_TENANT: DEFAULT_DEV_KEY}
    return mapping


def validate_tenant_api_key(tenant_id: str, api_key: str, keys: dict[str, str]) -> bool:
    expected = keys.get(tenant_id)
    return bool(expected and expected == api_key)
