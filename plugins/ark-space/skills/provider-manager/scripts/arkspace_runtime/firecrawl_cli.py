"""Firecrawl CLI provider helpers for ArkSpace."""

from __future__ import annotations

import json
import os
import re
import shlex
import shutil
import subprocess
from typing import Any

from . import provider_config

DEFAULT_BASE_URL = "https://api.firecrawl.dev"


class FirecrawlCliError(provider_config.ProviderConfigError):
    def __init__(self, message: str, status: int | None = None):
        super().__init__(message)
        self.status = status


def resolve_firecrawl(
    *,
    capability: str,
    config_path: str | None = None,
    state_path: str | None = None,
) -> dict[str, Any]:
    return provider_config.resolve_provider(
        "firecrawl",
        capability=capability,
        config_path=config_path,
        state_path=state_path,
        require_secret=True,
    )


def cli_command() -> list[str]:
    configured = os.environ.get("FIRECRAWL_CLI")
    if configured:
        return shlex.split(configured)
    if shutil.which("firecrawl"):
        return ["firecrawl"]
    if shutil.which("npx"):
        return ["npx", "-y", "firecrawl-cli@latest"]
    raise FirecrawlCliError("Firecrawl CLI is not installed; install with `npm install -g firecrawl-cli`")


def env_for(resolved: dict[str, Any]) -> dict[str, str]:
    auth = resolved.get("auth") or {}
    if auth.get("type") != "api_key" or not auth.get("value"):
        raise provider_config.ProviderConfigError("provider firecrawl has no available API key")
    env = os.environ.copy()
    env["FIRECRAWL_API_KEY"] = str(auth["value"])
    endpoint = resolved.get("endpoint") or {}
    if endpoint.get("base_url"):
        env["FIRECRAWL_API_URL"] = str(endpoint["base_url"])
    return env


def check_config(capability: str, config_path: str | None = None, state_path: str | None = None) -> dict[str, Any]:
    try:
        resolved = resolve_firecrawl(capability=capability, config_path=config_path, state_path=state_path)
        command = cli_command()
    except provider_config.ProviderConfigError as exc:
        return {"ok": False, "provider": "firecrawl", "capability": capability, "error": str(exc)}
    return {
        "ok": True,
        "provider": "firecrawl",
        "capability": capability,
        "cli": " ".join(command),
        **provider_config.public_view(resolved),
    }


def record_success(resolved: dict[str, Any], *, config_path: str | None, state_path: str | None) -> None:
    endpoint = resolved.get("endpoint") or {}
    auth = resolved.get("auth") or {}
    provider_config.record_provider_result(
        "firecrawl",
        endpoint_id=endpoint.get("id"),
        key_ref=auth.get("key_ref"),
        ok=True,
        status=200,
        config_path=config_path,
        state_path=state_path,
    )


def record_failure(
    resolved: dict[str, Any],
    exc: BaseException,
    *,
    config_path: str | None,
    state_path: str | None,
) -> None:
    endpoint = resolved.get("endpoint") or {}
    auth = resolved.get("auth") or {}
    status = getattr(exc, "status", None)
    key_ref = auth.get("key_ref") if status in {401, 403, 429} else None
    endpoint_id = endpoint.get("id") if status and status not in {401, 403, 429} else None
    provider_config.record_provider_result(
        "firecrawl",
        endpoint_id=endpoint_id,
        key_ref=key_ref,
        ok=False,
        status=status,
        config_path=config_path,
        state_path=state_path,
    )


def http_status_from_message(message: str) -> int | None:
    match = re.search(r"\b(401|403|429|5\d\d)\b", message)
    return int(match.group(1)) if match else None


def run_cli(
    resolved: dict[str, Any],
    args: list[str],
    *,
    timeout: int,
    config_path: str | None,
    state_path: str | None,
) -> str:
    command = [*cli_command(), *args]
    try:
        completed = subprocess.run(
            command,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env_for(resolved),
        )
    except subprocess.TimeoutExpired as exc:
        error = FirecrawlCliError(f"Firecrawl CLI timed out after {timeout} seconds")
        record_failure(resolved, error, config_path=config_path, state_path=state_path)
        raise error from exc
    except OSError as exc:
        error = FirecrawlCliError(f"Firecrawl CLI failed to start: {exc}")
        record_failure(resolved, error, config_path=config_path, state_path=state_path)
        raise error from exc

    if completed.returncode != 0:
        message = completed.stderr.strip() or completed.stdout.strip() or f"Firecrawl CLI exited with {completed.returncode}"
        error = FirecrawlCliError(message, status=http_status_from_message(message))
        record_failure(resolved, error, config_path=config_path, state_path=state_path)
        raise error

    record_success(resolved, config_path=config_path, state_path=state_path)
    return completed.stdout


def parse_json_or_text(text: str) -> Any:
    value = text.strip()
    if not value:
        return ""
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value
