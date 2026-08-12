#!/usr/bin/env python3
"""Brave Search API web_search provider helper for ArkSpace.

Queries the official Brave Search API endpoint
``https://api.search.brave.com/res/v1/web/search`` over HTTPS with the
``X-Subscription-Token`` header. Requires a configured Brave API key (from the
process environment or ArkSpace's private secret store via the provider config);
rotation and cooldown reuse the existing provider-manager key store. Standard
library only.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, NoReturn

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import provider_config  # noqa: E402  # type: ignore[reportMissingImports]

PROVIDER_ID = "brave"
CAPABILITY = "web_search"
BRAVE_BASE_URL = "https://api.search.brave.com/res/v1/web/search"
_USER_AGENT = "ArkSpace-brave-search/0.1"


class SearchError(provider_config.ProviderConfigError):
    """Typed failure carrying a Task 1 ``kind`` and an optional HTTP ``status``."""

    def __init__(self, kind: str, message: str, status: int | None = None):
        super().__init__(message)
        self.kind = kind
        self.status = status


def _fail(kind: str, message: str, status: int | None = None) -> NoReturn:
    provider_config.write_error_file(
        PROVIDER_ID, CAPABILITY, kind=kind, status=status, message=message
    )
    raise SearchError(kind, message, status)


def _resolve_key(config_path: str | None, state_path: str | None) -> str:
    """Return the required Brave API key, or fail with a typed ``config`` error."""
    try:
        resolved = provider_config.resolve_provider(
            PROVIDER_ID,
            capability=CAPABILITY,
            config_path=config_path,
            state_path=state_path,
            require_endpoint=False,
            require_secret=True,
        )
    except provider_config.ProviderConfigError as exc:
        _fail("config", f"Brave search requires an API key: {exc}")
    auth = resolved.get("auth") or {}
    value = auth.get("value")
    if (
        auth.get("type") == "api_key"
        and value
        and auth.get("available", True)
        and not provider_config.is_placeholder_key(str(value))
    ):
        return str(value)
    _fail("config", "Brave search requires a configured API key")


def _default_get_json(url: str, headers: dict[str, str], timeout: int) -> dict[str, Any]:
    # The host is the hardcoded module constant BRAVE_BASE_URL (https, fixed
    # host); the query is url-encoded, so no user-controlled scheme/host reaches
    # urllib.
    request = urllib.request.Request(url, headers=headers)
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    with urllib.request.urlopen(request, timeout=timeout) as response:
        try:
            return json.loads(response.read().decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            # Surface decode/parse failures as a controlled ValueError so
            # ``run_search`` classifies them as ``invalid-response``.
            raise ValueError(f"invalid JSON from Brave: {exc}") from exc


def map_results(data: dict[str, Any]) -> list[dict[str, str]]:
    """Map Brave's ``web.results`` payload to ``{title, url, snippet}`` dicts."""
    web = data.get("web")
    results = web.get("results") if isinstance(web, dict) else None
    if not isinstance(results, list):
        return []
    return [
        {
            "title": item.get("title") or "",
            "url": item.get("url") or "",
            "snippet": item.get("description") or "",
        }
        for item in results
        if isinstance(item, dict)
    ]


def run_search(
    query: str,
    *,
    max_results: int = 5,
    timeout: int = 30,
    config_path: str | None = None,
    state_path: str | None = None,
    get_json: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Search the Brave API. Returns a flat provider-specific dict (no envelope)."""
    if max_results <= 0:
        _fail("invalid-request", "max_results must be a positive integer")
    if get_json is None:
        get_json = _default_get_json
    key = _resolve_key(config_path, state_path)
    params = {"q": query, "count": str(max(1, max_results))}
    url = f"{BRAVE_BASE_URL}?{urllib.parse.urlencode(params)}"
    headers = {
        "User-Agent": _USER_AGENT,
        "X-Subscription-Token": key,
        "Accept": "application/json",
    }

    try:
        data = get_json(url, headers, int(timeout))
    except urllib.error.HTTPError as exc:
        kind = provider_config.classify_failure(exc.code)
        _fail(kind, f"Brave HTTP {exc.code}: {exc.reason}", exc.code)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _fail("network", f"Brave request failed: {exc}")
    except (ValueError, TypeError) as exc:  # invalid JSON / non-dict payload
        _fail("invalid-response", f"Brave returned an unparseable response: {exc}")
    except Exception as exc:  # noqa: BLE001 - defensive classification
        _fail("unknown", f"Brave request failed: {exc}")

    results = map_results(data)
    if not results:
        _fail("invalid-response", "Brave response contained no recognizable results")
    return {
        "provider": PROVIDER_ID,
        "capability": CAPABILITY,
        "query": query,
        "results": results[: max(1, max_results)],
    }


def emit_json(result: dict[str, Any]) -> None:
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))


def emit_markdown(result: dict[str, Any]) -> None:
    for item in result.get("results") or []:
        title = item.get("title") or item.get("url") or "Untitled"
        url = item.get("url") or ""
        snippet = (item.get("snippet") or "").strip()
        print(f"- [{title}]({url})")
        if snippet:
            print(f"  {snippet}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Search the Brave Search API.")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--check", action="store_true", help="verify configuration without a network call")
    args = parser.parse_args()
    if not args.query and not args.check:
        parser.error("query is required")
    return args


def main() -> int:
    args = parse_args()
    if args.check:
        try:
            _resolve_key(args.config_path, args.state_path)
        except SearchError as exc:
            if exc.kind == "config":
                print("Brave search requires an API key.", file=sys.stderr)
                print(
                    f"setup: configure Brave with `{provider_config.arkspace_command()} "
                    "provider setup brave --wizard`",
                    file=sys.stderr,
                )
            else:
                print(str(exc), file=sys.stderr)
            return 2
        print(
            json.dumps(
                {
                    "ok": True,
                    "provider": PROVIDER_ID,
                    "capability": CAPABILITY,
                    "configRequired": True,
                    "auth": "api_key",
                },
                ensure_ascii=False,
            )
        )
        return 0
    try:
        result = run_search(
            args.query,
            max_results=args.max_results,
            timeout=args.timeout,
            config_path=args.config_path,
            state_path=args.state_path,
        )
    except SearchError as exc:
        print(str(exc), file=sys.stderr)
        if exc.kind == "config":
            setup = (
                f"`{provider_config.arkspace_command()} "
                f"provider setup brave --save-secret BRAVE_API_KEY --prompt`"
            )
            print(
                f"setup: Brave web search needs an API key; configure it with {setup}",
                file=sys.stderr,
            )
            return 2
        return 1
    if args.output == "json":
        emit_json(result)
    else:
        emit_markdown(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
