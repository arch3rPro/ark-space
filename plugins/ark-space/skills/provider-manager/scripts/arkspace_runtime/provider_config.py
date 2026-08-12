#!/usr/bin/env python3
"""Provider configuration and credential rotation helpers for ArkSpace."""

from __future__ import annotations

import json
import os
import re
import subprocess
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
        try:
            data = json.load(handle)
        except json.JSONDecodeError as exc:
            # Report filename + line/column only; never echo the file content (it may hold
            # credentials / secrets).
            raise ProviderConfigError(
                f"{path} is not valid JSON at line {exc.lineno}, column {exc.colno}"
            ) from exc
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
    if not is_supported_key_ref(key_ref):
        raise ProviderConfigError(
            "unsupported key reference; use env:VAR, $VAR, ${VAR}, !command, or a literal value"
        )
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


# Typed failure categories used across provider fallback. ``config`` and ``unknown``
# are never returned by :func:`classify_failure`; helpers set them explicitly.
FAILURE_KINDS: frozenset[str] = frozenset({
    "auth", "config", "invalid-request", "invalid-response",
    "network", "quota", "transient", "unknown",
})

# Failure kinds that trigger cross-provider fallback by default. ``invalid-response``
# is excluded to avoid burning paid calls on unparseable-but-200 responses.
DEFAULT_FALLBACK_ON: tuple[str, ...] = ("quota", "network", "transient")


def fallback_policy(provider_id: str, config_path: str | None = None) -> list[str]:
    """Return the ordered failure kinds that trigger fallback for a provider.

    Uses key presence rather than truthiness, so an explicit empty list means
    "never fall back" instead of silently reverting to the default. Unknown
    kinds and non-list values are rejected.
    """
    config = load_config(config_path)
    entry = provider_entry(config, provider_id)
    if entry is None or "fallback_on" not in entry:
        return list(DEFAULT_FALLBACK_ON)
    value = entry["fallback_on"]
    if not isinstance(value, list):
        raise ProviderConfigError(f"provider {provider_id} fallback_on must be a list")
    if not all(isinstance(item, str) for item in value):
        raise ProviderConfigError(f"provider {provider_id} fallback_on must be a list of strings")
    for item in value:
        if item not in FAILURE_KINDS:
            raise ProviderConfigError(
                f"provider {provider_id} fallback_on contains unknown failure kind: {item}"
            )
    return list(value)


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
    if entry is None or not entry.get("enabled", True):
        raise ProviderConfigError(
            f"provider {provider_id} is not configured; run {configure_hint(provider_id)}"
        )
    resolved_capability = resolve_capability(provider_id, entry, capability)

    endpoint = select_endpoint(provider_id, entry, load_state(state_path), require_endpoint)
    credential = select_credential(provider_id, entry, load_state(state_path), require_secret)
    fallback_on = fallback_policy(provider_id, config_path)
    return {
        "provider": provider_id,
        "capability": resolved_capability,
        "config_path": str(default_config_path(config_path)),
        "state_path": str(default_state_path(state_path)),
        "endpoint": endpoint,
        "auth": credential,
        "rotation": entry.get("rotation") or default_rotation(),
        "fallback_on": fallback_on,
        "explicit_only": bool(entry.get("explicit_only", False)),
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

    def _usable(key_ref: str) -> bool:
        value = read_key_ref(key_ref)
        return bool(value) and not is_placeholder_key(value)

    # A resolved placeholder/too-short key counts as unavailable rather than being
    # sent to the provider (which would otherwise loop on 401s).
    available_key_refs = [key_ref for key_ref in key_refs if _usable(str(key_ref))]
    if not available_key_refs:
        if require_secret:
            raise ProviderConfigError(f"provider {provider_id} has no available API key; run {add_key_hint(provider_id)}")
        available_key_refs = key_refs

    selected = select_round_robin(provider_id, "keys", available_key_refs, state, lambda item: str(item))
    secret = read_key_ref(str(selected))
    if require_secret and (not secret or is_placeholder_key(secret)):
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
        # State-derived float; safe by construction (recorded cooldown timestamps are trusted).
        # pi-lens-ignore: unchecked-throwing-call-python
        cooldown_until = float(item_state.get("cooldown_until") or 0)
        if cooldown_until <= now:
            active.append(item)
    if not active:
        # pi-lens-ignore: unchecked-throwing-call-python
        next_ready = min(
            # pi-lens-ignore: unchecked-throwing-call-python
            float(
                (bucket_state.get(identity(item), {}) if isinstance(bucket_state.get(identity(item), {}), dict) else {}).get(
                    "cooldown_until", 0
                )
                or 0
            )
            for item in items
        )
        # pi-lens-ignore: unchecked-throwing-call-python
        wait_seconds = max(0, int(next_ready - now))
        raise ProviderConfigError(f"all {provider_id} {bucket} are cooling down; retry after {wait_seconds}s")
    candidates = active
    return min(
        candidates,
        # pi-lens-ignore: unchecked-throwing-call-python
        key=lambda item: float(
            (bucket_state.get(identity(item), {}) if isinstance(bucket_state.get(identity(item), {}), dict) else {}).get(
                "last_used_at", 0
            )
        ),
    )


def is_supported_key_ref(key_ref: str) -> bool:
    """Return True if key_ref uses a supported credential source syntax.

    Accepts ``env:NAME``, ``$NAME``, ``${NAME}``, ``!command``, and any non-empty
    literal. Malformed special forms (``env:``, ``$``, ``${}``, an unclosed ``${``,
    or a bare ``!``) are rejected so they cannot be silently treated as literals.
    """
    if not key_ref:
        return False
    if key_ref.startswith("env:"):
        return len(key_ref) > len("env:")
    if key_ref.startswith("${"):
        return key_ref.endswith("}") and len(key_ref) > 3
    if key_ref.startswith("$"):
        return len(key_ref) > 1
    if key_ref.startswith("!"):
        return len(key_ref) > 1
    return True  # ordinary literal value


# Placeholder values that must never be treated as a real credential.
PLACEHOLDER_KEY_DENYLIST = {
    "your-key", "your-key-here", "your-api-key", "your-api-key-here",
    "api-key", "api_key", "dummy", "placeholder", "changeme",
    "insert-your-key", "insert-your-key-here", "xxx", "key", "secret",
}


# Template marker words that indicate an unfilled placeholder such as ``CHANGE_ME``.
_TEMPLATE_MARKER_WORDS = frozenset({
    "change", "replace", "your", "insert", "placeholder", "dummy",
    "example", "sample", "todo", "put", "add",
})


def _is_template_value(value: str) -> bool:
    """Return True if a value looks like an unfilled template placeholder."""
    if "<" in value or ">" in value:
        return True
    tokens = re.split(r"[^A-Za-z]+", value)
    return any(token.lower() in _TEMPLATE_MARKER_WORDS for token in tokens)


def is_placeholder_key(value: str) -> bool:
    """Return True if a resolved credential looks like a placeholder or template value.

    Denylisted values and unfilled templates (e.g. ``CHANGE_ME``) are rejected; a
    legitimate short literal is not rejected solely by length.
    """
    normalized = value.strip()
    if not normalized:
        return True
    return normalized.lower() in PLACEHOLDER_KEY_DENYLIST or _is_template_value(normalized)


def redact(value: str) -> str:
    """Mask a credential for error/status output. No prefix is retained."""
    if not value:
        return ""
    if len(value) <= 8:
        return "••••"
    return "••••" + value[-4:]


ERROR_FILE_ENV = "ARKSPACE_ERROR_FILE"
ERROR_FILE_VERSION = 1
ERROR_MESSAGE_MAX_CHARS = 1000

# Header names whose values are stripped before a failure message is recorded.
_SENSITIVE_HEADERS = frozenset({
    "authorization", "proxy-authorization", "x-api-key", "api-key",
    "x-subscription-token", "cookie", "set-cookie", "x-auth-token", "auth-token",
})


def _redact_message(message: str) -> str:
    """Bound length and strip common secrets from a failure message before recording.

    Removes key-ref syntax (``env:``, ``$``, ``!``), sensitive header values,
    URL-embedded credentials, and long opaque tokens (API keys / base64 / JWTs).
    The caller supplies a concise human message; this is a defensive last line.
    """
    if not message:
        return ""
    # Redact sensitive header values ("Authorization: Bearer x").
    text = re.sub(
        r"(?i)\b(authorization|proxy-authorization|x-api-key|api-key|x-subscription-token|"
        r"cookie|set-cookie|x-auth-token|auth-token):\s*[^,;]+",
        r"\1: [redacted]",
        message,
    )
    # Remove URL-embedded credentials: scheme://user:pass@host.
    text = re.sub(r"://([^/@\s]+):[^/@\s]*@", r"://\1@", text)
    # Remove key-ref / command syntax: env:NAME, ${NAME}, $NAME, !command.
    text = re.sub(r"\benv:[A-Za-z0-9_]+", "[redacted]", text)
    text = re.sub(r"\$\{[^}]*\}", "[redacted]", text)
    text = re.sub(r"\$[A-Za-z0-9_]+", "[redacted]", text)
    text = re.sub(r"![^\s]*", "[redacted]", text)
    # Remove long opaque tokens (API keys, base64, JWTs).
    text = re.sub(r"\b[A-Za-z0-9_\-=.]{20,}\b", "[redacted]", text)
    # Collapse whitespace and bound length.
    text = " ".join(text.split())
    if len(text) > ERROR_MESSAGE_MAX_CHARS:
        text = text[:ERROR_MESSAGE_MAX_CHARS]
    return text


def write_error_file(
    provider_id: str,
    capability: str,
    *,
    kind: str,
    status: int | None = None,
    message: str,
) -> None:
    """Write a versioned, permission-restricted failure record for the current run.

    Only writes when :data:`ERROR_FILE_ENV` is set (explicit chain mode). The record
    is a JSON object with mode 0600 containing a bounded, redacted message and no
    credentials. An unknown ``kind`` is rejected without writing a file.
    """
    path = os.environ.get(ERROR_FILE_ENV)
    if not path:
        return
    if kind not in FAILURE_KINDS:
        raise ProviderConfigError(f"unknown failure kind: {kind}")
    record: dict[str, Any] = {
        "version": ERROR_FILE_VERSION,
        "provider": provider_id,
        "capability": capability,
        "kind": kind,
        "message": _redact_message(message),
    }
    if status is not None:
        record["status"] = status
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        json.dump(record, handle, ensure_ascii=False, sort_keys=True)
    try:
        target.chmod(0o600)
    except OSError:
        pass


def read_error_file(path: str | Path) -> dict[str, Any] | None:
    """Read a failure record, returning None for missing, corrupt, or unsupported records."""
    try:
        with Path(path).open(encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("version") != ERROR_FILE_VERSION:
        return None
    if data.get("kind") not in FAILURE_KINDS:
        return None
    return data


def classify_failure(status: int | None, error: str | None = None) -> str:
    """Classify a failed request into a typed category for cross-provider fallback.

    Returns one of: ``auth``, ``quota``, ``network``, ``transient``,
    ``invalid-request``, ``invalid-response``, or ``unknown``.
    """
    if status is None:
        low = (error or "").lower()
        if any(token in low for token in ("timeout", "timed out", "connection", "refused", "unreachable", "resolve host", "ssl")):
            return "network"
        if "401" in low or "403" in low or "unauthorized" in low or "forbidden" in low:
            return "auth"
        if "429" in low or "402" in low or "rate limit" in low or "quota" in low:
            return "quota"
        return "unknown"
    if status in (401, 403):
        return "auth"
    if status in (402, 429):
        return "quota"
    if status == 200 and error:
        return "invalid-response"
    if status >= 500:
        return "transient"
    if 400 <= status < 500:
        return "invalid-request"
    return "unknown"


def _read_from_env_or_secrets(name: str) -> str | None:
    if os.environ.get(name):
        return os.environ[name]
    return load_secrets().get("secrets", {}).get(name)


_CREDENTIAL_COMMAND_TIMEOUT = 5
_CREDENTIAL_COMMAND_MAX_BYTES = 16 * 1024


def _run_credential_command(command: str) -> str:
    """Run a trusted local command to resolve one credential value.

    The command is executed at provider-request time with a minimized environment,
    a short timeout, and a bounded output. OP_SESSION_* variables are forwarded so
    shell-local 1Password sessions can be reused without storing them in config.
    """
    env = {key: value for key, value in os.environ.items() if key == "PATH" or key.startswith("OP_SESSION_")}
    try:
        # Trusted local configuration: `!command` intentionally executes a shell command
        # supplied by the (trusted) config file, never by untrusted input. shell=True is
        # the point of the feature (pipe/glob/arg support for secret-manager CLIs).
        # nosemgrep: python.lang.security.audit.subprocess-shell-true.subprocess-shell-true
        # pi-lens-ignore: python-command-injection
        proc = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=_CREDENTIAL_COMMAND_TIMEOUT,
            env=env,
        )
    except subprocess.TimeoutExpired as exc:
        raise ProviderConfigError(f"credential command timed out after {_CREDENTIAL_COMMAND_TIMEOUT}s") from exc
    except OSError as exc:
        raise ProviderConfigError(f"credential command could not run: {exc}") from exc
    if proc.returncode != 0:
        raise ProviderConfigError(f"credential command failed (exit {proc.returncode})")
    output = proc.stdout
    if len(output.encode("utf-8", errors="replace")) > _CREDENTIAL_COMMAND_MAX_BYTES:
        raise ProviderConfigError("credential command output exceeds 16 KiB")
    line = output.strip().splitlines()
    if not line or not line[0].strip():
        raise ProviderConfigError("credential command produced no output")
    return line[0].strip()


def read_key_ref(key_ref: str) -> str | None:
    """Resolve a credential from a supported source: env, $VAR, ${VAR}, !command, or literal.

    Precedence: explicit source > environment variable > secrets store > literal.
    Escapes: ``$$`` -> literal leading ``$``; ``$!`` -> literal leading ``!``.
    """
    if key_ref.startswith("env:"):
        return _read_from_env_or_secrets(key_ref.split(":", 1)[1])
    if key_ref.startswith("$$"):
        return key_ref[1:]
    if key_ref.startswith("$!"):
        return key_ref[1:]
    if key_ref.startswith("!"):
        return _run_credential_command(key_ref[1:].strip())
    if key_ref.startswith("${") and key_ref.endswith("}"):
        return _read_from_env_or_secrets(key_ref[2:-1])
    if key_ref.startswith("$") and len(key_ref) > 1:
        return _read_from_env_or_secrets(key_ref[1:])
    return key_ref


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
    # Config-derived integer; safe by construction (rotation values are trusted config).
    # pi-lens-ignore: unchecked-throwing-call-python
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
    # Config/state-derived integers; safe by construction (rotation + recorded status are trusted).
    # pi-lens-ignore: unchecked-throwing-call-python
    item_state["failures"] = int(item_state.get("failures") or 0) + 1
    item_state["last_status"] = status
    # pi-lens-ignore: unchecked-throwing-call-python
    retry_on = {int(value) for value in rotation.get("retry_on_status", [])}
    # pi-lens-ignore: unchecked-throwing-call-python
    disable_on = {int(value) for value in rotation.get("disable_on_status", [])}
    if status in retry_on or status in disable_on or status is None:
        item_state["cooldown_until"] = now + cooldown_seconds


def public_view(resolved: dict[str, Any]) -> dict[str, Any]:
    auth = dict(resolved.get("auth") or {})
    auth.pop("value", None)
    return {**resolved, "auth": auth}
