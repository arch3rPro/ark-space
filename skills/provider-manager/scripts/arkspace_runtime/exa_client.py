"""Shared Exa HTTP helpers for ArkSpace provider scripts."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any, Callable

from arkspace_runtime import provider_config

DEFAULT_BASE_URL = "https://api.exa.ai"
KNOWN_CAPABILITIES = ["web_search", "web_fetch", "deep_research", "code_context", "related_pages"]


class ProviderRequestError(provider_config.ProviderConfigError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def endpoint_url(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def auth_headers(resolved: dict[str, Any]) -> dict[str, str]:
    auth = resolved.get("auth") or {}
    if auth.get("type") != "api_key" or not auth.get("value"):
        raise provider_config.ProviderConfigError("provider exa has no available API key")
    return {
        "Content-Type": "application/json",
        str(auth.get("header") or "x-api-key"): f"{auth.get('prefix', '')}{auth['value']}",
    }


def ensure_exa_capabilities(config_path: str | None = None) -> None:
    config = provider_config.load_config(config_path)
    entry = (config.get("providers") or {}).get("exa")
    if not isinstance(entry, dict) or entry.get("enabled") is False:
        return
    current = entry.get("capabilities")
    if current is None:
        single = entry.get("capability")
        current_values = [single] if isinstance(single, str) and single else []
    elif isinstance(current, list):
        current_values = [item for item in current if isinstance(item, str)]
    else:
        return
    merged = list(dict.fromkeys([*current_values, *KNOWN_CAPABILITIES]))
    if merged == current and "capability" not in entry:
        return
    entry["capabilities"] = merged
    entry.pop("capability", None)
    provider_config.save_config(config, config_path)


def resolve_exa(
    *,
    capability: str,
    config_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    ensure_exa_capabilities(config_path)
    return provider_config.resolve_provider(
        "exa",
        capability=capability,
        config_path=config_path,
        state_path=state_path,
        require_secret=True,
    )


def check_config(capability: str, config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    try:
        resolved = resolve_exa(capability=capability, config_path=config_path, state_path=state_path)
    except provider_config.ProviderConfigError as exc:
        return {"ok": False, "provider": "exa", "capability": capability, "error": str(exc)}
    return {"ok": True, "provider": "exa", "capability": capability, **provider_config.public_view(resolved)}


def post_json(url: str, headers: dict[str, str], payload: dict[str, Any], timeout: int, *, label: str) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ProviderRequestError(f"Exa {label} HTTP {exc.code}: {body}", status=exc.code) from exc
    except urllib.error.URLError as exc:
        raise ProviderRequestError(f"Exa {label} request failed: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise ProviderRequestError(f"Exa {label} returned invalid JSON: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise ProviderRequestError(f"Exa {label} request failed: {exc}") from exc


def safe_json_call(call: Callable[[], dict[str, Any]], *, label: str) -> dict[str, Any]:
    try:
        return call()
    except provider_config.ProviderConfigError:
        raise
    except json.JSONDecodeError as exc:
        raise ProviderRequestError(f"Exa {label} returned invalid JSON: {exc}") from exc
    except (TimeoutError, OSError) as exc:
        raise ProviderRequestError(f"Exa {label} request failed: {exc}") from exc


def record_success(
    resolved: dict[str, Any],
    *,
    config_path: str | None = None,
    state_path: str | None = None,
) -> None:
    endpoint = resolved.get("endpoint") or {}
    provider_config.record_provider_result(
        "exa",
        endpoint_id=endpoint.get("id"),
        key_ref=(resolved.get("auth") or {}).get("key_ref"),
        ok=True,
        status=200,
        config_path=config_path,
        state_path=state_path,
    )


def record_failure(
    resolved: dict[str, Any],
    exc: provider_config.ProviderConfigError,
    *,
    config_path: str | None = None,
    state_path: str | None = None,
) -> None:
    endpoint = resolved.get("endpoint") or {}
    status = getattr(exc, "status", None)
    endpoint_id = None if status in {401, 403, 429} else endpoint.get("id")
    key_ref = (resolved.get("auth") or {}).get("key_ref") if status in {401, 403, 429} else None
    if status is None or status >= 500:
        endpoint_id = endpoint.get("id")
        key_ref = None
    provider_config.record_provider_result(
        "exa",
        endpoint_id=endpoint_id,
        key_ref=key_ref,
        ok=False,
        status=status,
        config_path=config_path,
        state_path=state_path,
    )
