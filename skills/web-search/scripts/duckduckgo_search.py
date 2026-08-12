#!/usr/bin/env python3
"""Keyless DuckDuckGo HTML web_search provider helper for ArkSpace.

Queries ``https://html.duckduckgo.com/html/`` and parses organic results with the
standard library's ``html.parser``. Ads are excluded; ``uddg`` redirect URLs are
decoded back to their real destinations. No cookies are persisted and no
CAPTCHA/anti-bot challenge is bypassed: a block page or a page whose result
structure has drifted is treated as a typed failure (Task 1 error record), never
as an empty success. Standard library only.
"""

from __future__ import annotations

import argparse
import html.parser
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

PROVIDER_ID = "duckduckgo"
CAPABILITY = "web_search"
SEARCH_URL = "https://html.duckduckgo.com/html/"
_USER_AGENT = "ArkSpace-duckduckgo-search/0.1"

# Anti-bot / challenge markers that indicate a block page rather than results.
_BLOCK_MARKERS = (
    "anomaly",
    "captcha",
    "challenge",
    "unusual traffic",
    "verify you are human",
    "please enable javascript",
)


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


def decode_result_url(url: str) -> str:
    """Decode a DDG ``uddg`` redirect URL back to its real destination.

    Organic results in the HTML endpoint are redirects of the form
    ``//duckduckgo.com/l/?uddg=<urlencoded>&rut=<...>``. If ``url`` is such a
    redirect its ``uddg`` parameter is decoded and returned; otherwise the URL
    is returned unchanged.
    """
    if not url:
        return url
    parsed = urllib.parse.urlsplit(url)
    if parsed.netloc.endswith("duckduckgo.com") and parsed.path.rstrip("/").endswith("/l"):
        query = urllib.parse.parse_qs(parsed.query)
        uddg = query.get("uddg")
        if uddg:
            return urllib.parse.unquote(uddg[0])
    return url


class _ResultParser(html.parser.HTMLParser):
    """Collect non-ad results from DDG's ``div.result`` markup."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.results: list[dict[str, str]] = []
        self._stack: list[set[str]] = []
        self._current: dict[str, str] | None = None
        self._result_depth: int | None = None
        self._ad = False
        self._in_title = False
        self._in_snippet = False
        self._href = ""
        self._title_buf: list[str] = []
        self._snippet_buf: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr_map = {key: (value or "") for key, value in attrs}
        classes = set(attr_map.get("class", "").split())
        self._stack.append(classes)
        depth = len(self._stack)
        if tag == "div" and "result" in classes and self._current is None:
            self._current = {"title": "", "url": "", "snippet": ""}
            self._result_depth = depth
            self._ad = "result--ad" in classes
        if self._current is not None:
            if tag == "a" and "result__a" in classes:
                self._in_title = True
                self._href = attr_map.get("href", "")
            elif tag == "a" and "result__snippet" in classes:
                self._in_snippet = True

    def handle_endtag(self, tag: str) -> None:
        if not self._stack:
            return
        self._stack.pop()
        depth = len(self._stack)
        if tag == "a" and self._in_title:
            self._in_title = False
            if self._current is not None:
                self._current["title"] = "".join(self._title_buf).strip()
                self._current["url"] = self._href or ""
            self._title_buf = []
        elif tag == "a" and self._in_snippet:
            self._in_snippet = False
            if self._current is not None:
                self._current["snippet"] = "".join(self._snippet_buf).strip()
            self._snippet_buf = []
        if (
            tag == "div"
            and self._current is not None
            and self._result_depth is not None
            and depth < self._result_depth
        ):
            if not self._ad:
                self.results.append(self._current)
            self._current = None
            self._result_depth = None
            self._ad = False

    def handle_data(self, data: str) -> None:
        if self._in_title:
            self._title_buf.append(data)
        elif self._in_snippet:
            self._snippet_buf.append(data)


def parse_results(html: str) -> list[dict[str, str]]:
    """Parse organic results from DDG HTML, excluding ads and decoding URLs."""
    parser = _ResultParser()
    parser.feed(html)
    for result in parser.results:
        result["url"] = decode_result_url(result["url"])
    return parser.results


def _looks_like_block(html: str) -> bool:
    lowered = html.lower()
    return any(marker in lowered for marker in _BLOCK_MARKERS)


def _default_post(url: str, data: bytes, headers: dict[str, str], timeout: int) -> bytes:
    # The host is the hardcoded module constant SEARCH_URL (https, fixed host);
    # only the form body carries the query, so no user-controlled scheme/host
    # reaches urllib.
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def run_search(
    query: str,
    *,
    max_results: int = 5,
    timeout: int = 30,
    post: Callable[..., bytes] | None = None,
) -> dict[str, Any]:
    """Search DuckDuckGo HTML. Returns a flat provider-specific dict (no envelope)."""
    if max_results <= 0:
        _fail("invalid-request", "max_results must be a positive integer")
    if post is None:
        post = _default_post
    data = urllib.parse.urlencode({"q": query}).encode("utf-8")
    headers = {
        "User-Agent": _USER_AGENT,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    try:
        body = post(SEARCH_URL, data, headers, int(timeout))
    except urllib.error.HTTPError as exc:
        kind = provider_config.classify_failure(exc.code)
        _fail(kind, f"DuckDuckGo HTTP {exc.code}: {exc.reason}", exc.code)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        _fail("network", f"DuckDuckGo request failed: {exc}")
    except Exception as exc:  # noqa: BLE001 - defensive classification
        _fail("unknown", f"DuckDuckGo request failed: {exc}")

    html = body.decode("utf-8", errors="replace")
    if _looks_like_block(html):
        _fail("invalid-response", "DuckDuckGo returned an anomaly/CAPTCHA challenge page")
    results = parse_results(html)
    if not results:
        _fail("invalid-response", "DuckDuckGo response contained no recognizable results")
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
    parser = argparse.ArgumentParser(description="Search DuckDuckGo (HTML endpoint).")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=30)
    # Accepted for dispatch parity; DDG is keyless so they are no-ops.
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
