#!/usr/bin/env python3
"""Exa MCP (zero-config) web_search provider helper for ArkSpace.

Implements the Model Context Protocol ``Streamable HTTP`` transport with only the
standard library (``urllib``, ``json``, and a minimal SSE parser) to reach Exa's
public MCP endpoint. Unlike the REST ``exa`` provider (``exa_search.py``), this
provider needs no API key or provider config: it talks to ``https://mcp.exa.ai/mcp``
directly, which makes it the zero-config default web-search provider.

Wire protocol (Streamable HTTP / JSON-RPC 2.0):

1. ``initialize``          -> establish session, capture ``Mcp-Session-Id`` header.
2. ``notifications/initialized`` -> signal the client is ready (non-fatal if it fails).
3. ``tools/call`` for ``web_search_exa`` -> perform the search.

The MCP endpoint may answer with a single JSON document (``application/json``) or an
SSE event stream (``text/event-stream``); both are decoded by :func:`parse_mcp_response`.

This helper shares the Task 1 failure protocol: on failure it writes a versioned
error record via :func:`provider_config.write_error_file` (a no-op unless
``ARKSPACE_ERROR_FILE`` is set by chain orchestration) and emits the Task 1
failure kinds (``quota``, ``network``, ``invalid-response``, ...) so the chain
runner in ``scripts/arkspace.py`` can fail over correctly.

The transport is injectable: ``run_search(..., request_mcp=...)`` accepts a callable
``(url, headers, body, timeout) -> (status, headers, body)`` so unit tests exercise the
full protocol against mocked responses without any live network.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Mapping, NoReturn

RUNTIME_DIR = Path(__file__).resolve().parents[2] / "provider-manager" / "scripts"
sys.path.insert(0, str(RUNTIME_DIR))

from arkspace_runtime import provider_config  # noqa: E402  # type: ignore[reportMissingImports]

MCP_URL = "https://mcp.exa.ai/mcp"
PROVIDER_ID = "exa-mcp"
CAPABILITY = "web_search"
MCP_PROTOCOL_VERSION = "2025-03-26"
MCP_CLIENT_NAME = "arkspace-exa-mcp"
MCP_CLIENT_VERSION = "1.0.0"
TOOL_NAME = "web_search_exa"

RequestMCP = Callable[[str, Mapping[str, str], bytes, int], tuple[int, Mapping[str, str], bytes]]


class MCPError(Exception):
    """A typed MCP failure carrying a Task 1 ``kind`` and optional HTTP status."""

    def __init__(self, kind: str, status: int | None = None, message: str = "") -> None:
        super().__init__(message)
        self.kind = kind
        self.status = status
        self.message = message


class MCPTransportError(Exception):
    """Raised when the transport itself fails (DNS, connection, timeout)."""


def _fail(kind: str, status: int | None, message: str) -> NoReturn:
    """Write a Task 1 error record (best-effort) and raise a typed MCPError."""
    provider_config.write_error_file(
        "exa-mcp", "web_search", kind=kind, status=status, message=message
    )
    raise MCPError(kind, status, message)


# ---------------------------------------------------------------------------
# JSON-RPC message builders
# ---------------------------------------------------------------------------


def _encode(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload).encode("utf-8")


def _headers(session_id: str | None) -> dict[str, str]:
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
        "User-Agent": f"{MCP_CLIENT_NAME}/{MCP_CLIENT_VERSION}",
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    return headers


def _initialize_request() -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "capabilities": {},
            "clientInfo": {"name": MCP_CLIENT_NAME, "version": MCP_CLIENT_VERSION},
        },
    }


def _initialized_notification() -> dict[str, Any]:
    return {"jsonrpc": "2.0", "method": "notifications/initialized"}


def _tool_call(query: str, max_results: int) -> dict[str, Any]:
    return {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": TOOL_NAME,
            "arguments": {
                "query": query,
                # max_results is typed int and bounded to [1, 100].
                "numResults": max(1, min(100, max_results)),
            },
        },
    }


def _extract_session_id(headers: Mapping[str, str]) -> str | None:
    value: Any = None
    for key, val in headers.items():
        if key.lower() == "mcp-session-id":
            value = val
            break
    if value is None:
        return None
    if isinstance(value, (list, tuple)):
        value = value[0] if value else None
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _header(headers: Mapping[str, str], name: str) -> str:
    """Case-insensitively read a response header value (e.g. ``content-type``).

    The standard-library transport returns ``dict(response.headers.items())``,
    whose keys are title-case (``Content-Type``), while mocks may use lowercase
    (``content-type``). Real HTTP header names are case-insensitive, so we match
    by lowercased key rather than relying on :meth:`Mapping.get`, which is
    case-sensitive. This mirrors the case-insensitive matching used by
    :func:`_extract_session_id` for ``Mcp-Session-Id``.
    """
    target = name.lower()
    for key, value in headers.items():
        if key.lower() != target:
            continue
        if isinstance(value, (list, tuple)):
            return str(value[0]) if value else ""
        return str(value or "")
    return ""


# ---------------------------------------------------------------------------
# Transport
# ---------------------------------------------------------------------------


def _default_request_mcp(
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout: int,
) -> tuple[int, Mapping[str, str], bytes]:
    """POST ``body`` to ``url`` over the standard library, returning a triple.

    The return shape ``(status, headers, body)`` matches the injectable
    ``request_mcp`` contract so tests can substitute a mocked transport.

    The URL is the hardcoded module constant :data:`MCP_URL` (https scheme,
    fixed host); no user-controlled input ever reaches the ``url`` argument, so
    the dynamic-urllib semgrep advisory is a false positive.
    """
    # nosemgrep: python.lang.security.audit.dynamic-urllib-use-detected.dynamic-urllib-use-detected
    request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, dict(response.headers.items()), response.read()
    except urllib.error.HTTPError as exc:
        # HTTP-level error (4xx/5xx): surface it as a normal triple so the
        # caller can classify the status (e.g. 429 -> quota).
        return exc.code, dict(exc.headers.items()), exc.read()
    except (urllib.error.URLError, OSError, TimeoutError) as exc:
        # Transport-level failure: no HTTP status to classify.
        raise MCPTransportError(str(exc)) from exc


# ---------------------------------------------------------------------------
# Response decoding
# ---------------------------------------------------------------------------


def _parse_sse(text: str) -> dict[str, Any] | None:
    """Decode the JSON payload of an SSE ``text/event-stream`` response.

    Collects ``data:`` lines (per the SSE spec, continuation lines are joined
    with a newline) and returns the decoded JSON object, or None if absent.
    """
    data_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("data:"):
            data_lines.append(stripped[5:].strip())
    if not data_lines:
        return None
    payload = "\n".join(data_lines)
    try:
        data = json.loads(payload)
    except (json.JSONDecodeError, ValueError):
        return None
    if not isinstance(data, dict):
        return None
    return data


def parse_mcp_response(body: bytes, content_type: str) -> dict[str, Any]:
    """Decode an MCP response body into a JSON-RPC object.

    Handles both ``application/json`` and ``text/event-stream`` bodies. Raises
    :class:`MCPError` with kind ``invalid-response`` when the body is not a
    decodable JSON-RPC object.
    """
    text = body.decode("utf-8", errors="replace")
    if "text/event-stream" in (content_type or "").lower():
        data = _parse_sse(text)
        if data is None:
            _fail("invalid-response", None, "malformed SSE response from MCP server")
        return data
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, ValueError):
        _fail("invalid-response", None, "malformed JSON-RPC response from MCP server")
    if not isinstance(data, dict):
        _fail("invalid-response", None, "malformed JSON-RPC response from MCP server")
    return data


# ---------------------------------------------------------------------------
# Tool result shaping
# ---------------------------------------------------------------------------


def _check_status(status: int, headers: Mapping[str, str], body: bytes, label: str) -> None:
    """Classify an HTTP status from the MCP endpoint and fail with a typed kind."""
    if status == 429:
        _fail("quota", status, f"{label}: HTTP 429 rate limited or quota exceeded")
    if status == 200:
        return
    kind = provider_config.classify_failure(
        status, body.decode("utf-8", errors="replace")
    )
    _fail(kind, status, f"{label}: HTTP {status}")


def _require_result(data: Mapping[str, Any], label: str) -> None:
    if "result" not in data:
        _fail("invalid-response", None, f"{label}: MCP response missing result")
    if "error" in data:
        _fail("invalid-response", None, f"{label}: MCP returned an error object")


def _try_json(text: str) -> Any:
    stripped = (text or "").strip()
    if not (stripped.startswith("{") or stripped.startswith("[")):
        return None
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return None


def _extract_items(parsed: Any) -> list[Any]:
    """Flatten a parsed tool payload into a list of result items."""
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        for key in ("results", "data", "items"):
            value = parsed.get(key)
            if isinstance(value, list):
                return value
    return []


def _normalize_item(item: Any) -> dict[str, Any] | None:
    """Map an MCP result item onto the existing-style Exa result shape."""
    if not isinstance(item, dict):
        return None
    return {
        "title": item.get("title") or "",
        "url": item.get("url") or "",
        "snippet": (
            item.get("text")
            or item.get("snippet")
            or item.get("summary")
            or ""
        ),
        "score": item.get("score"),
        "published": item.get("publishedDate"),
        "id": item.get("id"),
        "image": item.get("image"),
        "favicon": item.get("favicon"),
        "author": item.get("author"),
    }


def _build_result(query: str, data: Mapping[str, Any]) -> dict[str, Any]:
    """Build the provider-specific success dict from a tools/call JSON-RPC object."""
    result = data.get("result")
    if not isinstance(result, dict):
        _fail("invalid-response", None, "web_search_exa: MCP response missing result")
    if result.get("isError"):
        _fail("invalid-response", None, "web_search_exa: MCP tool returned isError")
    content = result.get("content")
    if content is None:
        content = []
    if not isinstance(content, list):
        _fail("invalid-response", None, "web_search_exa: MCP content is malformed")
    results: list[dict[str, Any]] = []
    for block in content:
        if not isinstance(block, dict) or block.get("type") != "text":
            continue
        parsed = _try_json(block.get("text", ""))
        if parsed is None:
            continue
        for item in _extract_items(parsed):
            normalized = _normalize_item(item)
            if normalized is not None:
                results.append(normalized)
    return {
        "provider": "exa-mcp",
        "capability": "web_search",
        "query": query,
        "results": results,
    }


# ---------------------------------------------------------------------------
# Public search entry point
# ---------------------------------------------------------------------------


def run_search(
    query: str,
    *,
    max_results: int = 5,
    timeout: int = 30,
    request_mcp: RequestMCP | None = None,
) -> dict[str, Any]:
    """Run a ``web_search_exa`` MCP search and return the standard result dict.

    ``request_mcp`` is injectable for tests; it must have the signature
    ``(url, headers, body, timeout) -> (status, headers, body)``. When omitted,
    the standard-library transport is used.
    """
    if max_results <= 0:
        _fail("invalid-request", None, "max_results must be a positive integer")
    if request_mcp is None:
        request_mcp = _default_request_mcp
    session_id: str | None = None
    try:
        # 1. initialize
        status, headers, body = request_mcp(
            MCP_URL, _headers(None), _encode(_initialize_request()), timeout
        )
        _check_status(status, headers, body, "initialize")
        init_resp = parse_mcp_response(body, _header(headers, "content-type"))
        _require_result(init_resp, "initialize")
        session_id = _extract_session_id(headers)

        # 2. notifications/initialized (best-effort per MCP spec)
        try:
            request_mcp(
                MCP_URL,
                _headers(session_id),
                _encode(_initialized_notification()),
                timeout,
            )
        except Exception:
            pass

        # 3. tools/call
        status, headers, body = request_mcp(
            MCP_URL, _headers(session_id), _encode(_tool_call(query, max_results)), timeout
        )
        _check_status(status, headers, body, "web_search_exa")
        tool_resp = parse_mcp_response(body, _header(headers, "content-type"))
        return _build_result(query, tool_resp)
    except MCPError:
        raise
    except Exception as exc:  # transport failure -> network
        _fail("network", None, f"transport error reaching MCP server: {exc}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Search through Exa's zero-config MCP provider."
    )
    parser.add_argument("query", nargs="?")
    parser.add_argument("--max-results", type=int, default=5)
    parser.add_argument("--timeout", type=int, default=30)
    parser.add_argument("--config-path")
    parser.add_argument("--state-path")
    parser.add_argument("--output", choices=["json", "markdown"], default="markdown")
    parser.add_argument("--check", action="store_true", help="verify configuration without a network call")
    return parser.parse_args()


def print_markdown(result: dict[str, Any]) -> None:
    for index, item in enumerate(result.get("results") or [], start=1):
        print(f"{index}. [{item['title']}]({item['url']})")
        if item.get("snippet"):
            print(f"   {item['snippet']}")


def main() -> int:
    args = parse_args()
    if args.check:
        # Exa MCP is keyless zero-config; check verifies availability only.
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
        return 0
    if not args.query:
        print("query is required", file=sys.stderr)
        return 2
    try:
        result = run_search(
            args.query,
            max_results=args.max_results,
            timeout=args.timeout,
        )
    except MCPError as exc:
        # The error record was already written by _fail() inside run_search().
        print(exc.message, file=sys.stderr)
        return 1
    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_markdown(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
