#!/usr/bin/env python3
"""Provider configuration and credential rotation helpers for ArkSpace."""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any

CONFIG_ENV = "ARKSPACE_PROVIDER_CONFIG"
STATE_ENV = "ARKSPACE_PROVIDER_STATE"
SECRETS_ENV = "ARKSPACE_PROVIDER_SECRETS"
PACKAGE_ROOT = Path(__file__).resolve().parents[4]


class ProviderConfigError(ValueError):
    """Raised when provider configuration is missing or invalid."""


def default_config_path(config_path: str | None = None) -> Path:
    if config_path:
        return Path(config_path).expanduser()
    if os.environ.get(CONFIG_ENV):
        return Path(os.environ[CONFIG_ENV]).expanduser()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    return config_home / "ark-space" / "providers.json"


def default_state_path(state_path: str | None = None) -> Path:
    if state_path:
        return Path(state_path).expanduser()
    if os.environ.get(STATE_ENV):
        return Path(os.environ[STATE_ENV]).expanduser()
    state_home = Path(os.environ.get("XDG_STATE_HOME", "~/.local/state")).expanduser()
    return state_home / "ark-space" / "provider-state.json"


def default_secrets_path(secrets_path: str | None = None) -> Path:
    if secrets_path:
        return Path(secrets_path).expanduser()
    if os.environ.get(SECRETS_ENV):
        return Path(os.environ[SECRETS_ENV]).expanduser()
    config_home = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config")).expanduser()
    return config_home / "ark-space" / "secrets.json"


def normalize_base_url(url: str) -> str:
    value = url.strip()
    if not value:
        raise ProviderConfigError("empty base URL")
    if not value.startswith(("http://", "https://")):
        value = "https://" + value
    return value.rstrip("/")


def load_json_object(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ProviderConfigError(f"{path} must contain a JSON object")
    return data


def save_json_object(path: Path, data: dict[str, Any], private: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")
    if private:
        try:
            path.chmod(0o600)
        except OSError:
            pass


def load_config(config_path: str | None = None) -> dict[str, Any]:
    data = load_json_object(default_config_path(config_path))
    if not data:
        return {"version": 1, "providers": {}}
    if data.get("version") != 1:
        raise ProviderConfigError("provider config version must be 1")
    providers = data.setdefault("providers", {})
    if not isinstance(providers, dict):
        raise ProviderConfigError("provider config providers must be an object")
    return data


def save_config(data: dict[str, Any], config_path: str | None = None) -> Path:
    path = default_config_path(config_path)
    save_json_object(path, data, private=True)
    return path


def load_state(state_path: str | None = None) -> dict[str, Any]:
    data = load_json_object(default_state_path(state_path))
    return data if data else {}


def save_state(data: dict[str, Any], state_path: str | None = None) -> Path:
    path = default_state_path(state_path)
    save_json_object(path, data, private=True)
    return path


def load_secrets(secrets_path: str | None = None) -> dict[str, Any]:
    data = load_json_object(default_secrets_path(secrets_path))
    if not data:
        return {"version": 1, "secrets": {}}
    if data.get("version") != 1:
        raise ProviderConfigError("provider secrets version must be 1")
    secrets = data.setdefault("secrets", {})
    if not isinstance(secrets, dict):
        raise ProviderConfigError("provider secrets must contain a secrets object")
    return data


def save_secrets(data: dict[str, Any], secrets_path: str | None = None) -> Path:
    path = default_secrets_path(secrets_path)
    save_json_object(path, data, private=True)
    return path


def set_secret_value(name: str, value: str, secrets_path: str | None = None) -> Path:
    if not name or any(char.isspace() for char in name):
        raise ProviderConfigError("secret environment variable names must be non-empty and contain no whitespace")
    if not value:
        raise ProviderConfigError(f"secret value for {name} is empty")
    data = load_secrets(secrets_path)
    data.setdefault("secrets", {})[name] = value
    return save_secrets(data, secrets_path)


def arkspace_command() -> str:
    return f"python3 {PACKAGE_ROOT / 'scripts' / 'arkspace.py'}"


def configure_hint(provider_id: str) -> str:
    if provider_id in {"tavily", "exa", "firecrawl"}:
        return f"`{arkspace_command()} provider setup {provider_id} --wizard`"
    return f"`{arkspace_command()} provider configure {provider_id} --base-url <url>`"


def add_key_hint(provider_id: str) -> str:
    if provider_id in {"tavily", "exa", "firecrawl"}:
        return f"`{arkspace_command()} provider setup {provider_id} --wizard`"
    return f"`{arkspace_command()} provider add-key {provider_id} --env <ENV_NAME>`"


def provider_entry(config: dict[str, Any], provider_id: str) -> dict[str, Any] | None:
    providers = config.get("providers", {})
    if not isinstance(providers, dict):
        raise ProviderConfigError("provider config providers must be an object")
    entry = providers.get(provider_id)
    if entry is None:
        return None
    if not isinstance(entry, dict):
        raise ProviderConfigError(f"provider {provider_id} must be an object")
    return entry


def set_provider_endpoint(
    provider_id: str,
    *,
    capability: str,
    capabilities: list[str] | None = None,
    base_url: str,
    endpoint_id: str = "default",
    config_path: str | None = None,
) -> Path:
    config = load_config(config_path)
    providers = config.setdefault("providers", {})
    entry = providers.setdefault(provider_id, {})
    if capabilities:
        if not all(isinstance(item, str) and item for item in capabilities):
            raise ProviderConfigError("capabilities must be non-empty strings")
        entry["capabilities"] = capabilities
        entry.pop("capability", None)
    else:
        entry["capability"] = capability
        entry.pop("capabilities", None)
    entry["enabled"] = True
    entry.setdefault("auth", {"type": "none"})
    entry.setdefault("rotation", default_rotation())
    entry.setdefault("fallback", {})

    endpoints = entry.setdefault("endpoints", [])
    if not isinstance(endpoints, list):
        raise ProviderConfigError(f"provider {provider_id} endpoints must be a list")
    endpoint = next(
        (item for item in endpoints if isinstance(item, dict) and item.get("id") == endpoint_id),
        None,
    )
    if endpoint is None:
        endpoints.append({"id": endpoint_id, "base_url": normalize_base_url(base_url), "weight": 100})
    else:
        endpoint["base_url"] = normalize_base_url(base_url)
        endpoint.setdefault("weight", 100)
    return save_config(config, config_path)


def add_key_ref(
    provider_id: str,
    *,
    key_ref: str,
    auth_header: str | None = None,
    auth_prefix: str | None = None,
    config_path: str | None = None,
) -> Path:
    if not key_ref.startswith("env:"):
        raise ProviderConfigError("only env:<VARIABLE_NAME> key references are currently supported")
    config = load_config(config_path)
    providers = config.setdefault("providers", {})
    entry = providers.setdefault(provider_id, {})
    auth = entry.setdefault("auth", {})
    auth["type"] = "api_key"
    if auth_header:
        auth["header"] = auth_header
    if auth_prefix is not None:
        auth["prefix"] = auth_prefix
    key_refs = auth.setdefault("key_refs", [])
    if not isinstance(key_refs, list):
        raise ProviderConfigError(f"provider {provider_id} auth.key_refs must be a list")
    if key_ref not in key_refs:
        key_refs.append(key_ref)
    entry.setdefault("enabled", True)
    entry.setdefault("rotation", default_rotation())
    return save_config(config, config_path)


def default_rotation() -> dict[str, Any]:
    return {
        "strategy": "round_robin",
        "retry_on_status": [429, 500, 502, 503, 504],
        "disable_on_status": [401, 403],
        "cooldown_seconds": 300,
    }


def resolve_provider(
    provider_id: str,
    *,
    capability: str | None = None,
    config_path: str | None = None,
    state_path: str | None = None,
    require_endpoint: bool = True,
    require_secret: bool = False,
) -> dict[str, Any]:
    config = load_config(config_path)
    entry = provider_entry(config, provider_id)
    if entry is None or entry.get("enabled") is False:
        raise ProviderConfigError(
            f"provider {provider_id} is not configured; run {configure_hint(provider_id)}"
        )
    resolved_capability = resolve_capability(provider_id, entry, capability)

    endpoint = select_endpoint(provider_id, entry, load_state(state_path), require_endpoint)
    credential = select_credential(provider_id, entry, load_state(state_path), require_secret)
    return {
        "provider": provider_id,
        "capability": resolved_capability,
        "config_path": str(default_config_path(config_path)),
        "state_path": str(default_state_path(state_path)),
        "endpoint": endpoint,
        "auth": credential,
        "rotation": entry.get("rotation") or default_rotation(),
    }


def resolve_capability(provider_id: str, entry: dict[str, Any], requested: str | None) -> str | None:
    configured = entry.get("capability")
    capabilities = entry.get("capabilities")
    if capabilities is not None:
        if not isinstance(capabilities, list) or not all(isinstance(item, str) for item in capabilities):
            raise ProviderConfigError(f"provider {provider_id} capabilities must be a list of strings")
        if requested and requested not in capabilities:
            raise ProviderConfigError(f"provider {provider_id} does not support capability {requested}")
        return requested or (capabilities[0] if capabilities else configured)
    if configured and requested and configured != requested:
        raise ProviderConfigError(f"provider {provider_id} is configured for {configured}, not {requested}")
    return configured or requested


def select_endpoint(
    provider_id: str,
    entry: dict[str, Any],
    state: dict[str, Any],
    require_endpoint: bool,
) -> dict[str, Any] | None:
    endpoints = entry.get("endpoints") or []
    if not isinstance(endpoints, list):
        raise ProviderConfigError(f"provider {provider_id} endpoints must be a list")
    usable = [item for item in endpoints if isinstance(item, dict) and item.get("base_url")]
    if not usable:
        if require_endpoint:
            raise ProviderConfigError(
                f"provider {provider_id} has no endpoint; run {configure_hint(provider_id)}"
            )
        return None
    selected = select_round_robin(provider_id, "endpoints", usable, state, lambda item: item.get("id"))
    return {
        "id": selected.get("id", "default"),
        "base_url": normalize_base_url(str(selected["base_url"])),
        "weight": selected.get("weight", 100),
    }


def select_credential(
    provider_id: str,
    entry: dict[str, Any],
    state: dict[str, Any],
    require_secret: bool,
) -> dict[str, Any]:
    auth = entry.get("auth") or {"type": "none"}
    if not isinstance(auth, dict):
        raise ProviderConfigError(f"provider {provider_id} auth must be an object")
    auth_type = auth.get("type", "none")
    if auth_type == "none":
        if require_secret:
            raise ProviderConfigError(f"provider {provider_id} has no key refs; run {add_key_hint(provider_id)}")
        return {"type": "none"}
    if auth_type != "api_key":
        raise ProviderConfigError(f"provider {provider_id} auth type {auth_type} is not supported")

    key_refs = auth.get("key_refs") or []
    if not isinstance(key_refs, list):
        raise ProviderConfigError(f"provider {provider_id} auth.key_refs must be a list")
    if not key_refs:
        raise ProviderConfigError(f"provider {provider_id} has no key refs; run {add_key_hint(provider_id)}")
    available_key_refs = [key_ref for key_ref in key_refs if read_key_ref(str(key_ref))]
    if not available_key_refs:
        if require_secret:
            raise ProviderConfigError(f"provider {provider_id} has no available API key; run {add_key_hint(provider_id)}")
        available_key_refs = key_refs

    selected = select_round_robin(provider_id, "keys", available_key_refs, state, lambda item: str(item))
    secret = read_key_ref(str(selected))
    if require_secret and not secret:
        raise ProviderConfigError(f"provider {provider_id} key {selected} is not available in the environment")
    return {
        "type": "api_key",
        "header": auth.get("header", "Authorization"),
        "prefix": auth.get("prefix", ""),
        "key_ref": selected,
        "available": bool(secret),
        "value": secret,
    }


def select_round_robin(
    provider_id: str,
    bucket: str,
    items: list[Any],
    state: dict[str, Any],
    identity,
) -> Any:
    now = time.time()
    provider_state = state.get(provider_id, {}) if isinstance(state.get(provider_id, {}), dict) else {}
    bucket_state = provider_state.get(bucket, {}) if isinstance(provider_state.get(bucket, {}), dict) else {}
    active: list[Any] = []
    for item in items:
        item_id = identity(item)
        item_state = bucket_state.get(item_id, {}) if isinstance(bucket_state.get(item_id, {}), dict) else {}
        cooldown_until = float(item_state.get("cooldown_until") or 0)
        if cooldown_until <= now:
            active.append(item)
    if not active:
        next_ready = min(
            float(
                (bucket_state.get(identity(item), {}) if isinstance(bucket_state.get(identity(item), {}), dict) else {}).get(
                    "cooldown_until", 0
                )
                or 0
            )
            for item in items
        )
        wait_seconds = max(0, int(next_ready - now))
        raise ProviderConfigError(f"all {provider_id} {bucket} are cooling down; retry after {wait_seconds}s")
    candidates = active
    return min(
        candidates,
        key=lambda item: float(
            (bucket_state.get(identity(item), {}) if isinstance(bucket_state.get(identity(item), {}), dict) else {}).get(
                "last_used_at", 0
            )
        ),
    )


def read_key_ref(key_ref: str) -> str | None:
    if key_ref.startswith("env:"):
        name = key_ref.split(":", 1)[1]
        if os.environ.get(name):
            return os.environ[name]
        return load_secrets().get("secrets", {}).get(name)
    raise ProviderConfigError(f"unsupported key reference {key_ref}")


def record_provider_result(
    provider_id: str,
    *,
    endpoint_id: str | None = None,
    key_ref: str | None = None,
    ok: bool,
    status: int | None = None,
    config_path: str | None = None,
    state_path: str | None = None,
) -> Path:
    config = load_config(config_path)
    entry = provider_entry(config, provider_id) or {}
    rotation = entry.get("rotation") or default_rotation()
    cooldown_seconds = int(rotation.get("cooldown_seconds") or 300)
    now = time.time()
    state = load_state(state_path)
    provider_state = state.setdefault(provider_id, {})
    if endpoint_id:
        update_item_state(provider_state, "endpoints", endpoint_id, ok, status, now, cooldown_seconds, rotation)
    if key_ref:
        update_item_state(provider_state, "keys", key_ref, ok, status, now, cooldown_seconds, rotation)
    return save_state(state, state_path)


def update_item_state(
    provider_state: dict[str, Any],
    bucket: str,
    item_id: str,
    ok: bool,
    status: int | None,
    now: float,
    cooldown_seconds: int,
    rotation: dict[str, Any],
) -> None:
    bucket_state = provider_state.setdefault(bucket, {})
    item_state = bucket_state.setdefault(item_id, {})
    item_state["last_used_at"] = now
    if ok:
        item_state["failures"] = 0
        item_state["cooldown_until"] = None
        item_state["last_status"] = status
        return
    item_state["failures"] = int(item_state.get("failures") or 0) + 1
    item_state["last_status"] = status
    retry_on = {int(value) for value in rotation.get("retry_on_status", [])}
    disable_on = {int(value) for value in rotation.get("disable_on_status", [])}
    if status in retry_on or status in disable_on or status is None:
        item_state["cooldown_until"] = now + cooldown_seconds


def public_view(resolved: dict[str, Any]) -> dict[str, Any]:
    auth = dict(resolved.get("auth") or {})
    auth.pop("value", None)
    return {**resolved, "auth": auth}
