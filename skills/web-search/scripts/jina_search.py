#!/usr/bin/env python3
"""Keyless Jina Reader (s.jina.ai) web_search provider helper for ArkSpace.

Queries Jina's official ``https://s.jina.ai/<query>`` endpoint, which returns
search results as Markdown. No API key is required; if a key is configured
(``JINA_API_KEY`` env or the ArkSpace ``jina`` provider's api_key) it is sent
only when present. Standard library only.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, NoReturn

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import provider_config  # noqa: E402  # type: ignore[reportMissingImports]

PROVIDER_ID = "jina"
CAPABILITY = "web_search"
BASE_URL = "https://s.jina.ai"
_USER_AGENT = "ArkSpace-jina-search/0.1"


class SearchError(provider_config.ProviderConfigError):
    """Typed failure carrying a Task 1 ``kind`` and an optional HTTP ``status``."""

    def __init__(self, kind: str, message: str, status: int | None = None):
        super().__init__(message)
        self.kind = kind
        self.status = status


_LINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def _fail(kind: str, message: str, status: int | None = None) -> NoReturn:
    provider_config.write_error_file(
        PROVIDER_ID, CAPABILITY, kind=kind, status=status, message=message
    )
    raise SearchError(kind, message, status)


def parse_markdown(text: str) -> list[dict[str, str]]:
    """Extract ``[title](url)`` links plus a nearby snippet line from Markdown.

    Jina's ``s.jina.ai`` search responses are Markdown documents; every result
    is a link (often a list item) optionally followed by an indented description
    line. This returns one dict per link with ``title``, ``url`` and ``snippet``.
    """
    results: list[dict[str, str]] = []
    lines = text.splitlines()
    for index, line in enumerate(lines):
        for match in _LINK_RE.finditer(line):
            title = match.group(1).strip()
            url = match.group(2).strip()
            snippet = ""
            for nxt in lines[index + 1 : index + 4]:
                stripped = nxt.strip()
                if not stripped:
                    continue
                if stripped.startswith(("[", "#", "- ", "http", "> ")):
                    break
                snippet = stripped[:300]
                break
            results.append({"title": title, "url": url, "snippet": snippet})
    return results


def _resolve_key(config_path: str | None, state_path: str | None) -> str | None:
    """Return an optional configured Jina key, or None to search keylessly."""
    env_key = os.environ.get("JINA_API_KEY") or os.environ.get("JINA_KEY")
    if env_key:
        return env_key
    try:
        resolved = provider_config.resolve_provider(
            PROVIDER_ID,
            capability=CAPABILITY,
            config_path=config_path,
            state_path=state_path,
            require_endpoint=False,
            require_secret=False,
        )
    except provider_config.ProviderConfigError as exc:
        # Optional key: a missing/unconfigured provider simply means keyless.
        del exc
        return None
    auth = resolved.get("auth") or {}
    value = auth.get("value")
    if (
        auth.get("type") == "api_key"
        and value
        and auth.get("available", True)
        and not provider_config.is_placeholder_key(str(value))
    ):
        return str(value)
    return None


def _default_get(url: str, headers: dict[str, str], timeout: int) -> bytes:
    # The host is the hardcoded module constant BASE_URL (https, fixed host); the
    # query is url-encoded, so no user-controlled scheme/host reaches urllib.
    request = urllib.request.Request(url, headers=headers)
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def run_search(
    query: str,
    *,
    max_results: int = 5,
    timeout: int = 30,
    config_path: str | None = None,
    state_path: str | None = None,
    get: Callable[..., bytes] | None = None,
) -> dict[str, Any]:
    """Search via Jina Reader. Returns a flat provider-specific dict (no envelope)."""
    if max_results <= 0:
        _fail("invalid-request", "max_results must be a positive integer")
    if get is None:
        get = _default_get
    url = f"{BASE_URL}/{urllib.parse.quote(query)}"
    headers = {"User-Agent": _USER_AGENT}
    key = _resolve_key(config_path, state_path)
    if key:
        headers["Authorization"] = f"Bearer {key}"

    try:
        body = get(url, headers, int(timeout))
    except urllib.error.HTTPError as exc:
        kind = provider_config.classify_failure(exc.code)
        _fail(kind, f"Jina HTTP {exc.code}: {exc.reason}", exc.code)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _fail("network", f"Jina request failed: {exc}")
    except Exception as exc:  # noqa: BLE001 - defensive classification
        _fail("unknown", f"Jina request failed: {exc}")

    results = parse_markdown(body.decode("utf-8", errors="replace"))
    if not results:
        _fail("invalid-response", "Jina response contained no recognizable results")
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
    parser = argparse.ArgumentParser(description="Search via Jina Reader (s.jina.ai).")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--check", action="store_true", help="verify configuration without a network call")
    args = parser.parse_args()
    if args.check:
        print(
            json.dumps(
                {
                    "ok": True,
                    "provider": PROVIDER_ID,
                    "capability": CAPABILITY,
                    "configRequired": False,
                    "auth": "none",
                },
                ensure_ascii=False,
            )
        )
        raise SystemExit(0)
    if not args.query:
        parser.error("query is required")
    return args


def main() -> int:
    args = parse_args()
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
        return 1
    except provider_config.ProviderConfigError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    if args.output == "json":
        emit_json(result)
    else:
        emit_markdown(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
