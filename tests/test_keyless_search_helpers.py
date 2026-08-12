"""Mocked tests for the zero-config Exa MCP web_search helper.

These tests exercise the full Streamable HTTP / JSON-RPC protocol flow against a
scripted in-memory transport (``request_mcp=...``). No live network is used: every
HTTP exchange is a mocked ``(status, headers, body)`` triple. The Task 1 failure
protocol (error-file records) is verified via ``ARKSPACE_ERROR_FILE``.
"""

import importlib.util
import http.client
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
import urllib.parse
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ExaMCPHelperTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_module(
            ROOT / "skills" / "web-search" / "scripts" / "exa_mcp_search.py",
            "exa_mcp_search_test_module",
        )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.error_path = str(Path(self.tmp.name) / "err.json")
        self.error_env = patch.dict(os.environ, {"ARKSPACE_ERROR_FILE": self.error_path})
        self.error_env.start()
        self.addCleanup(self.error_env.stop)

    # -- scripted transport helpers -----------------------------------------

    def _transport(self, responses):
        """Build a mock ``request_mcp`` returning each triple in order.

        Records every call as ``(url, headers, json_body)`` on ``transport.calls``.
        """
        class Transport:
            def __init__(self) -> None:
                self.calls: list[tuple[str, dict[str, str], dict]] = []

            def __call__(self, url, headers, body, timeout):
                self.calls.append((url, dict(headers), json.loads(body)))
                status, hdrs, resp = responses[len(self.calls) - 1]
                return status, hdrs, resp

        return Transport()

    def _init_response(self):
        return (
            200,
            {"content-type": "application/json", "mcp-session-id": "sess-1"},
            json.dumps(
                {"jsonrpc": "2.0", "id": 1, "result": {"serverInfo": {"name": "exa"}}}
            ).encode(),
        )

    def _notification_response(self):
        return 202, {}, b""

    def _tool_response(self, items=None, is_error=False):
        if items is None:
            items = [{"title": "T", "url": "https://e.example", "text": "snippet"}]
        result = {
            "content": [{"type": "text", "text": json.dumps(items)}],
            "isError": is_error,
        }
        return (
            200,
            {"content-type": "application/json"},
            json.dumps({"jsonrpc": "2.0", "id": 2, "result": result}).encode(),
        )

    def _sse_tool_response(self, items):
        result = {
            "content": [{"type": "text", "text": json.dumps(items)}],
            "isError": False,
        }
        payload = json.dumps({"jsonrpc": "2.0", "id": 2, "result": result})
        body = f"event: message\ndata: {payload}\n\n".encode()
        return 200, {"content-type": "text/event-stream"}, body

    def _text_tool_response(self, text):
        result = {"content": [{"type": "text", "text": text}], "isError": False}
        return (
            200,
            {"content-type": "application/json"},
            json.dumps({"jsonrpc": "2.0", "id": 2, "result": result}).encode(),
        )

    def _read_error_record(self):
        return json.loads(Path(self.error_path).read_text(encoding="utf-8"))

    # -- protocol sequence ---------------------------------------------------

    def test_protocol_sequence_initialize_notification_tool_call(self):
        t = self._transport(
            [self._init_response(), self._notification_response(), self._tool_response()]
        )
        self.m.run_search("agent skills", request_mcp=t)

        methods = [c[2]["method"] for c in t.calls]
        self.assertEqual(methods, ["initialize", "notifications/initialized", "tools/call"])

    def test_tool_call_targets_web_search_exa_with_query_and_num_results(self):
        t = self._transport(
            [self._init_response(), self._notification_response(), self._tool_response()]
        )
        self.m.run_search("agent skills", max_results=7, request_mcp=t)

        tool = t.calls[2][2]
        self.assertEqual(tool["method"], "tools/call")
        self.assertEqual(tool["params"]["name"], "web_search_exa")
        self.assertEqual(tool["params"]["arguments"]["query"], "agent skills")
        self.assertEqual(tool["params"]["arguments"]["numResults"], 7)

    def test_num_results_is_bounded(self):
        t = self._transport(
            [self._init_response(), self._notification_response(), self._tool_response()]
        )
        self.m.run_search("q", max_results=500, request_mcp=t)
        self.assertEqual(t.calls[2][2]["params"]["arguments"]["numResults"], 100)

    def test_nonpositive_max_results_is_invalid_request_before_transport(self):
        t = self._transport([])

        with self.assertRaises(self.m.MCPError) as ctx:
            self.m.run_search("q", max_results=0, request_mcp=t)

        self.assertEqual(ctx.exception.kind, "invalid-request")
        self.assertEqual(t.calls, [])
        self.assertEqual(self._read_error_record()["kind"], "invalid-request")

    def test_cli_nonpositive_max_results_is_controlled_and_writes_error_record(self):
        with patch.object(
            sys, "argv", ["exa_mcp_search.py", "--max-results", "0", "q"]
        ), patch("sys.stderr", new=io.StringIO()) as err:
            code = self.m.main()

        self.assertEqual(code, 1)
        self.assertIn("max_results must be a positive integer", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self._read_error_record()["kind"], "invalid-request")

    def test_initialize_session_id_propagates_to_followup_requests(self):
        t = self._transport(
            [self._init_response(), self._notification_response(), self._tool_response()]
        )
        self.m.run_search("q", request_mcp=t)

        # First (initialize) request carries no session header yet.
        self.assertNotIn("Mcp-Session-Id", t.calls[0][1])
        self.assertNotIn("mcp-session-id", {k.lower(): v for k, v in t.calls[0][1].items()})
        # Notification and tools/call both echo the session id.
        self.assertEqual(t.calls[1][1].get("Mcp-Session-Id"), "sess-1")
        self.assertEqual(t.calls[2][1].get("Mcp-Session-Id"), "sess-1")

    # -- response decoding ---------------------------------------------------

    def test_json_response_shapes_existing_style_results(self):
        items = [
            {
                "title": "Alpha",
                "url": "https://a.example",
                "text": "first snippet",
                "score": 0.91,
                "publishedDate": "2024-01-02",
                "author": "ann",
            },
            {"title": "Beta", "url": "https://b.example", "text": "second"},
        ]
        t = self._transport(
            [
                self._init_response(),
                self._notification_response(),
                self._tool_response(items=items),
            ]
        )
        res = self.m.run_search("agent skills", request_mcp=t)

        self.assertEqual(res["provider"], "exa-mcp")
        self.assertEqual(res["capability"], "web_search")
        self.assertEqual(res["query"], "agent skills")
        self.assertEqual(len(res["results"]), 2)
        self.assertEqual(res["results"][0]["title"], "Alpha")
        self.assertEqual(res["results"][0]["url"], "https://a.example")
        self.assertEqual(res["results"][0]["snippet"], "first snippet")
        self.assertEqual(res["results"][0]["score"], 0.91)
        self.assertEqual(res["results"][0]["published"], "2024-01-02")
        self.assertEqual(res["results"][0]["author"], "ann")
        # No generic success envelope.
        self.assertNotIn("ok", res)

    def test_real_text_response_normalizes_multiple_results(self):
        text = """Title: ArkSpace agent skills
URL: https://arkspace.example/skills
Published: 2026-08-12
Author: ArkSpace Team
Highlights:
Build reusable skills for agents.
Keep this second highlight line.

Title: Exa MCP protocol guide
URL: https://docs.exa.example/mcp
Published: 2026-08-11
Author: Exa
Highlights:
Use Streamable HTTP for MCP tools.
"""
        t = self._transport(
            [self._init_response(), self._notification_response(), self._text_tool_response(text)]
        )

        res = self.m.run_search("agent skills", request_mcp=t)

        self.assertEqual(
            res["results"],
            [
                {
                    "title": "ArkSpace agent skills",
                    "url": "https://arkspace.example/skills",
                    "snippet": "Build reusable skills for agents.\nKeep this second highlight line.",
                    "score": None,
                    "published": "2026-08-12",
                    "id": None,
                    "image": None,
                    "favicon": None,
                    "author": "ArkSpace Team",
                },
                {
                    "title": "Exa MCP protocol guide",
                    "url": "https://docs.exa.example/mcp",
                    "snippet": "Use Streamable HTTP for MCP tools.",
                    "score": None,
                    "published": "2026-08-11",
                    "id": None,
                    "image": None,
                    "favicon": None,
                    "author": "Exa",
                },
            ],
        )

    def test_indented_record_fields_in_highlights_do_not_start_a_result(self):
        text = """Title: Parent result
URL: https://parent.example/result
Highlights:
This highlight quotes a nested result:
  Title: Quoted result title
  URL: https://quoted.example/result
The quoted fields belong to this snippet.

Title: Second result
URL: https://second.example/result
Highlights:
Second result snippet.
"""
        t = self._transport(
            [self._init_response(), self._notification_response(), self._text_tool_response(text)]
        )

        res = self.m.run_search("q", request_mcp=t)

        self.assertEqual(
            [(item["title"], item["url"], item["snippet"]) for item in res["results"]],
            [
                (
                    "Parent result",
                    "https://parent.example/result",
                    "This highlight quotes a nested result:\n"
                    "  Title: Quoted result title\n"
                    "  URL: https://quoted.example/result\n"
                    "The quoted fields belong to this snippet.",
                ),
                ("Second result", "https://second.example/result", "Second result snippet."),
            ],
        )

    def test_real_text_response_tolerates_missing_optional_fields(self):
        text = """Title: URL-only Exa result
URL: https://exa.example/valid
"""
        t = self._transport(
            [self._init_response(), self._notification_response(), self._text_tool_response(text)]
        )

        res = self.m.run_search("q", request_mcp=t)

        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["title"], "URL-only Exa result")
        self.assertEqual(res["results"][0]["url"], "https://exa.example/valid")
        self.assertEqual(res["results"][0]["snippet"], "")
        self.assertIsNone(res["results"][0]["published"])
        self.assertIsNone(res["results"][0]["author"])

    def test_unrecognizable_nonempty_content_is_invalid_response(self):
        t = self._transport(
            [
                self._init_response(),
                self._notification_response(),
                self._text_tool_response("Exa returned a human-readable message without result records."),
            ]
        )

        with self.assertRaises(self.m.MCPError) as ctx:
            self.m.run_search("q", request_mcp=t)

        self.assertEqual(ctx.exception.kind, "invalid-response")
        record = self._read_error_record()
        self.assertEqual(record["version"], 1)
        self.assertEqual(record["kind"], "invalid-response")

    def test_sse_response_decoding(self):
        items = [{"title": "FromSSE", "url": "https://s.example", "text": "sse"}]
        t = self._transport(
            [
                self._init_response(),
                self._notification_response(),
                self._sse_tool_response(items),
            ]
        )
        res = self.m.run_search("q", request_mcp=t)

        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["title"], "FromSSE")
        self.assertEqual(res["results"][0]["url"], "https://s.example")

    def test_sse_response_decoding_with_title_case_content_type(self):
        # The real ``urllib`` transport returns ``dict(response.headers.items())``,
        # whose keys are title-case (``Content-Type``), not lowercase. Content-type
        # detection must be case-insensitive, otherwise a real SSE response would
        # be mis-detected as JSON and fail with ``invalid-response``. Both the
        # initialize and tools/call responses use title-case headers here.
        init = self._init_response()
        init = (
            init[0],
            {"Content-Type": "application/json", "Mcp-Session-Id": "sess-1"},
            init[2],
        )
        tool = self._sse_tool_response(
            [{"title": "TitleCaseSSE", "url": "https://t.example", "text": "sse"}]
        )
        tool = (tool[0], {"Content-Type": "text/event-stream"}, tool[2])
        t = self._transport([init, self._notification_response(), tool])

        res = self.m.run_search("q", request_mcp=t)

        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["title"], "TitleCaseSSE")
        self.assertEqual(res["results"][0]["url"], "https://t.example")

    def test_parse_mcp_response_json(self):
        data = self.m.parse_mcp_response(
            b'{"jsonrpc":"2.0","id":1,"result":{"serverInfo":{}}}', "application/json"
        )
        self.assertEqual(data["id"], 1)
        self.assertIn("result", data)

    def test_parse_mcp_response_sse(self):
        body = b'event: message\ndata: {"jsonrpc":"2.0","id":2,"result":{"content":[]}}\n\n'
        data = self.m.parse_mcp_response(body, "text/event-stream")
        self.assertEqual(data["id"], 2)
        self.assertEqual(data["result"]["content"], [])

    def test_notification_failure_is_non_fatal(self):
        def fake(url, headers, body, timeout):
            req = json.loads(body)
            method = req.get("method")
            if method == "initialize":
                return self._init_response()
            if method == "notifications/initialized":
                raise self.m.MCPTransportError("notification dropped")
            return self._tool_response()

        res = self.m.run_search("q", request_mcp=fake)
        self.assertEqual(len(res["results"]), 1)

    # -- failure protocol ----------------------------------------------------

    def test_http_429_maps_to_quota_and_writes_error_record(self):
        t = self._transport([(429, {}, b"")])
        with self.assertRaises(self.m.MCPError) as ctx:
            self.m.run_search("q", request_mcp=t)

        self.assertEqual(ctx.exception.kind, "quota")
        self.assertEqual(ctx.exception.status, 429)
        record = self._read_error_record()
        self.assertEqual(record["kind"], "quota")
        self.assertEqual(record["provider"], "exa-mcp")
        self.assertEqual(record["capability"], "web_search")

    def test_transport_exception_maps_to_network(self):
        def boom(url, headers, body, timeout):
            raise self.m.MCPTransportError("connection refused")

        with self.assertRaises(self.m.MCPError) as ctx:
            self.m.run_search("q", request_mcp=boom)

        self.assertEqual(ctx.exception.kind, "network")
        self.assertIsNone(ctx.exception.status)

    def test_malformed_jsonrpc_maps_to_invalid_response(self):
        t = self._transport([(200, {"content-type": "application/json"}, b"not-json")])
        with self.assertRaises(self.m.MCPError) as ctx:
            self.m.run_search("q", request_mcp=t)

        self.assertEqual(ctx.exception.kind, "invalid-response")

    def test_missing_result_maps_to_invalid_response(self):
        # A valid JSON-RPC envelope without a ``result`` (or with an ``error``).
        t = self._transport(
            [
                (200, {"content-type": "application/json"}, b'{"jsonrpc":"2.0","id":1}'),
                self._notification_response(),
                self._tool_response(),
            ]
        )
        with self.assertRaises(self.m.MCPError) as ctx:
            self.m.run_search("q", request_mcp=t)

        self.assertEqual(ctx.exception.kind, "invalid-response")

    def test_tool_is_error_maps_to_invalid_response(self):
        t = self._transport(
            [
                self._init_response(),
                self._notification_response(),
                self._tool_response(is_error=True),
            ]
        )
        with self.assertRaises(self.m.MCPError) as ctx:
            self.m.run_search("q", request_mcp=t)

        self.assertEqual(ctx.exception.kind, "invalid-response")

    def test_tool_missing_result_content_maps_to_invalid_response(self):
        t = self._transport(
            [
                self._init_response(),
                self._notification_response(),
                (
                    200,
                    {"content-type": "application/json"},
                    b'{"jsonrpc":"2.0","id":2,"result":{"content":"not-a-list"}}',
                ),
            ]
        )
        with self.assertRaises(self.m.MCPError) as ctx:
            self.m.run_search("q", request_mcp=t)

        self.assertEqual(ctx.exception.kind, "invalid-response")

    # -- CLI ----------------------------------------------------------------

    def test_cli_query_required(self):
        with patch.object(sys, "argv", ["exa_mcp_search.py"]):
            code = self.m.main()
        self.assertEqual(code, 2)

    def test_cli_json_output_returns_zero(self):
        with patch.object(sys, "argv", ["exa_mcp_search.py", "--output", "json", "q"]), patch(
            "sys.stdout", new=io.StringIO()
        ) as out, patch.object(
            self.m,
            "run_search",
            return_value={"provider": "exa-mcp", "query": "q", "results": []},
        ):
            code = self.m.main()
        self.assertEqual(code, 0)
        payload = json.loads(out.getvalue())
        self.assertEqual(payload["provider"], "exa-mcp")

    def test_cli_markdown_output_lists_results(self):
        result = {
            "provider": "exa-mcp",
            "query": "q",
            "results": [{"title": "A", "url": "https://a.example", "snippet": "s"}],
        }
        with patch.object(sys, "argv", ["exa_mcp_search.py", "q"]), patch(
            "sys.stdout", new=io.StringIO()
        ) as out, patch.object(self.m, "run_search", return_value=result):
            code = self.m.main()
        self.assertEqual(code, 0)
        self.assertIn("[A](https://a.example)", out.getvalue())


class JinaHelperTests(unittest.TestCase):
    """Mocked tests for the keyless Jina s.jina.ai web_search helper.

    The ``get`` transport is injected so no live network is used. Success
    output is a flat provider-specific dict (no generic ``ok`` envelope);
    failures write a Task 1 error record and raise a typed ``SearchError``.
    """

    @classmethod
    def setUpClass(cls):
        cls.m = load_module(
            ROOT / "skills" / "web-search" / "scripts" / "jina_search.py",
            "jina_search_test_module",
        )

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.error_path = str(Path(self.tmp.name) / "err.json")
        self.error_env = patch.dict(os.environ, {"ARKSPACE_ERROR_FILE": self.error_path})
        self.error_env.start()
        self.addCleanup(self.error_env.stop)

    def _markdown(self):
        return (
            b"# Search\n\n"
            b"## Results\n\n"
            b"- [First Result](https://a.example/page)\n"
            b"  This is the first snippet.\n\n"
            b"- [Second Result](https://b.example/x)\n"
            b"  Second snippet here.\n"
        )

    def _read_error_record(self):
        return json.loads(Path(self.error_path).read_text(encoding="utf-8"))

    def _recording_get(self, body):
        calls = []

        def fake_get(url, headers, timeout):
            calls.append((url, dict(headers), timeout))
            return body

        return fake_get, calls

    def test_no_key_required_and_flat_success_shape(self):
        fake_get, calls = self._recording_get(self._markdown())
        res = self.m.run_search("agent skills", get=fake_get)

        self.assertEqual(res["provider"], "jina")
        self.assertEqual(res["capability"], "web_search")
        self.assertEqual(res["query"], "agent skills")
        self.assertEqual(len(res["results"]), 2)
        self.assertEqual(res["results"][0]["title"], "First Result")
        self.assertEqual(res["results"][0]["url"], "https://a.example/page")
        self.assertEqual(res["results"][0]["snippet"], "This is the first snippet.")
        # No generic success envelope.
        self.assertNotIn("ok", res)

        url, headers, _timeout = calls[0]
        self.assertIn("s.jina.ai", url)
        self.assertNotIn("Authorization", headers)

    def test_optional_key_sent_only_when_present(self):
        fake_get, calls = self._recording_get(self._markdown())
        with patch.dict(os.environ, {"JINA_API_KEY": "sk-test-key"}):
            self.m.run_search("q", get=fake_get)
        _url, headers, _timeout = calls[0]
        self.assertEqual(headers.get("Authorization"), "Bearer sk-test-key")

    def test_no_key_when_env_absent(self):
        fake_get, calls = self._recording_get(self._markdown())
        # Ensure no key leaks in from the environment (cleared by patch below).
        with patch.dict(os.environ, {"JINA_API_KEY": ""}):
            self.m.run_search("q", get=fake_get)
        _url, headers, _timeout = calls[0]
        self.assertNotIn("Authorization", headers)

    def test_max_results_and_timeout_honored(self):
        fake_get, calls = self._recording_get(self._markdown())
        self.m.run_search("q", max_results=1, timeout=12, get=fake_get)
        _url, _headers, timeout = calls[0]
        self.assertEqual(timeout, 12)
        res = self.m.run_search("q", max_results=1, get=fake_get)
        self.assertEqual(len(res["results"]), 1)

    def test_nonpositive_max_results_is_invalid_request_before_network(self):
        fake_get, calls = self._recording_get(self._markdown())

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", max_results=0, get=fake_get)

        self.assertEqual(ctx.exception.kind, "invalid-request")
        self.assertEqual(calls, [])
        self.assertEqual(self._read_error_record()["kind"], "invalid-request")

    def test_cli_nonpositive_max_results_is_controlled_and_writes_error_record(self):
        with patch.object(sys, "argv", ["jina_search.py", "--max-results", "0", "q"]), patch.object(
            self.m, "_default_get", side_effect=AssertionError("network must not run")
        ), patch("sys.stderr", new=io.StringIO()) as err:
            code = self.m.main()

        self.assertEqual(code, 1)
        self.assertIn("max_results must be a positive integer", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self._read_error_record()["kind"], "invalid-request")

    def test_main_network_failure_is_controlled_and_writes_error_record(self):
        with patch.object(sys, "argv", ["jina_search.py", "q"]), patch.object(
            self.m, "_default_get", side_effect=urllib.error.URLError("connection refused")
        ), patch("sys.stderr", new=io.StringIO()) as err:
            code = self.m.main()

        self.assertEqual(code, 1)
        self.assertIn("Jina request failed", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self._read_error_record()["kind"], "network")

    def test_main_parser_failure_is_controlled_and_writes_error_record(self):
        with patch.object(sys, "argv", ["jina_search.py", "q"]), patch.object(
            self.m, "_default_get", return_value=b"not markdown"
        ), patch("sys.stderr", new=io.StringIO()) as err:
            code = self.m.main()

        self.assertEqual(code, 1)
        self.assertIn("no recognizable results", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self._read_error_record()["kind"], "invalid-response")

    def test_http_429_maps_to_quota_and_writes_error_record(self):
        def rate_limited(url, headers, timeout):
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", http.client.HTTPMessage(), None)

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", get=rate_limited)
        self.assertEqual(ctx.exception.kind, "quota")
        self.assertEqual(ctx.exception.status, 429)
        record = self._read_error_record()
        self.assertEqual(record["kind"], "quota")
        self.assertEqual(record["provider"], "jina")
        self.assertEqual(record["capability"], "web_search")

    def test_network_failure_classified_as_network(self):
        def unreachable(url, headers, timeout):
            raise urllib.error.URLError("connection refused")

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", get=unreachable)
        self.assertEqual(ctx.exception.kind, "network")
        self.assertIsNone(ctx.exception.status)
        record = self._read_error_record()
        self.assertEqual(record["kind"], "network")

    def test_unparseable_body_maps_to_invalid_response(self):
        fake_get, _calls = self._recording_get(b"<html>not markdown with any links</html>")
        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", get=fake_get)
        self.assertEqual(ctx.exception.kind, "invalid-response")


class DuckDuckGoHelperTests(unittest.TestCase):
    """Mocked tests for the keyless DuckDuckGo HTML web_search helper.

    Parsing exercises real fixture HTML; network exchanges use an injected
    ``post`` transport. CAPTCHA/block pages and selector drift produce typed
    failures (Task 1 error record) rather than an empty success.
    """

    @classmethod
    def setUpClass(cls):
        cls.m = load_module(
            ROOT / "skills" / "web-search" / "scripts" / "duckduckgo_search.py",
            "duckduckgo_search_test_module",
        )
        cls.fixtures = ROOT / "tests" / "fixtures"

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.error_path = str(Path(self.tmp.name) / "err.json")
        self.error_env = patch.dict(os.environ, {"ARKSPACE_ERROR_FILE": self.error_path})
        self.error_env.start()
        self.addCleanup(self.error_env.stop)

    def _fixture(self, name):
        return (self.fixtures / name).read_text(encoding="utf-8")

    def _read_error_record(self):
        return json.loads(Path(self.error_path).read_text(encoding="utf-8"))

    def _recording_post(self, html):
        calls = []

        def fake_post(url, data, headers, timeout):
            calls.append((url, data, dict(headers), timeout))
            return html.encode("utf-8")

        return fake_post, calls

    def test_parse_results_excludes_ads_and_decodes_urls(self):
        results = self.m.parse_results(self._fixture("duckduckgo-results.html"))

        self.assertEqual(len(results), 2)
        titles = [r["title"] for r in results]
        self.assertNotIn("Sponsored Ad: Skill Courses", titles)
        self.assertEqual(results[0]["title"], "Agent Skills Guide")
        self.assertEqual(results[0]["url"], "https://example.com/agent-skills")
        self.assertNotIn("uddg", results[0]["url"])
        self.assertEqual(results[0]["snippet"], "A practical guide to building reusable agent skills for automation.")
        self.assertEqual(results[1]["title"], "Skills Documentation")
        self.assertEqual(results[1]["url"], "https://docs.example.com/skills")

    def test_decode_result_url_decodes_uddg_redirect(self):
        url = "//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpath%3Fa%3D1&rut=abc123"
        self.assertEqual(
            self.m.decode_result_url(url), "https://example.com/path?a=1"
        )

    def test_decode_result_url_non_redirect_unchanged(self):
        self.assertEqual(
            self.m.decode_result_url("https://plain.example/x"), "https://plain.example/x"
        )
        self.assertEqual(self.m.decode_result_url(""), "")

    def test_success_shape_no_envelope_and_max_results(self):
        fake_post, calls = self._recording_post(self._fixture("duckduckgo-results.html"))
        res = self.m.run_search("agent skills", max_results=1, post=fake_post)

        self.assertEqual(res["provider"], "duckduckgo")
        self.assertEqual(res["capability"], "web_search")
        self.assertEqual(res["query"], "agent skills")
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["url"], "https://example.com/agent-skills")
        self.assertNotIn("ok", res)

        url, data, _headers, _timeout = calls[0]
        self.assertIn("html.duckduckgo.com", url)
        self.assertEqual(data, b"q=agent+skills")

    def test_nonpositive_max_results_is_invalid_request_before_network(self):
        fake_post, calls = self._recording_post(self._fixture("duckduckgo-results.html"))

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", max_results=0, post=fake_post)

        self.assertEqual(ctx.exception.kind, "invalid-request")
        self.assertEqual(calls, [])
        self.assertEqual(self._read_error_record()["kind"], "invalid-request")

    def test_cli_nonpositive_max_results_is_controlled_and_writes_error_record(self):
        with patch.object(sys, "argv", ["duckduckgo_search.py", "--max-results", "0", "q"]), patch.object(
            self.m, "_default_post", side_effect=AssertionError("network must not run")
        ), patch("sys.stderr", new=io.StringIO()) as err:
            code = self.m.main()

        self.assertEqual(code, 1)
        self.assertIn("max_results must be a positive integer", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self._read_error_record()["kind"], "invalid-request")

    def test_main_network_failure_is_controlled_and_writes_error_record(self):
        with patch.object(sys, "argv", ["duckduckgo_search.py", "q"]), patch.object(
            self.m, "_default_post", side_effect=urllib.error.URLError("connection refused")
        ), patch("sys.stderr", new=io.StringIO()) as err:
            code = self.m.main()

        self.assertEqual(code, 1)
        self.assertIn("DuckDuckGo request failed", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self._read_error_record()["kind"], "network")

    def test_main_parser_failure_is_controlled_and_writes_error_record(self):
        with patch.object(sys, "argv", ["duckduckgo_search.py", "q"]), patch.object(
            self.m, "_default_post", return_value=b"<html>no results</html>"
        ), patch("sys.stderr", new=io.StringIO()) as err:
            code = self.m.main()

        self.assertEqual(code, 1)
        self.assertIn("no recognizable results", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self._read_error_record()["kind"], "invalid-response")

    def test_captcha_page_is_typed_failure_not_empty_success(self):
        fake_post, _calls = self._recording_post(self._fixture("duckduckgo-captcha.html"))
        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", post=fake_post)
        self.assertEqual(ctx.exception.kind, "invalid-response")
        record = self._read_error_record()
        self.assertEqual(record["kind"], "invalid-response")
        self.assertEqual(record["provider"], "duckduckgo")
        self.assertEqual(record["capability"], "web_search")

    def test_structure_drift_is_typed_failure_not_empty_success(self):
        fake_post, _calls = self._recording_post(
            self._fixture("duckduckgo-structure-change.html")
        )
        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", post=fake_post)
        self.assertEqual(ctx.exception.kind, "invalid-response")

    def test_http_429_maps_to_quota_and_writes_error_record(self):
        def rate_limited(url, data, headers, timeout):
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", http.client.HTTPMessage(), None)

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", post=rate_limited)
        self.assertEqual(ctx.exception.kind, "quota")
        self.assertEqual(ctx.exception.status, 429)
        record = self._read_error_record()
        self.assertEqual(record["kind"], "quota")

    def test_network_failure_classified_as_network(self):
        def unreachable(url, data, headers, timeout):
            raise urllib.error.URLError("connection refused")

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search("q", post=unreachable)
        self.assertEqual(ctx.exception.kind, "network")
        self.assertIsNone(ctx.exception.status)


class BraveHelperTests(unittest.TestCase):
    """Mocked tests for the keyed Brave Search API web_search helper.

    The ``get_json`` transport is injected so no live network is used. Success
    output is a flat provider-specific dict (no generic ``ok`` envelope); missing
    credentials and typed failures write a Task 1 error record and raise a typed
    ``SearchError``.
    """

    @classmethod
    def setUpClass(cls):
        cls.m = load_module(
            ROOT / "skills" / "web-search" / "scripts" / "brave_search.py",
            "brave_search_test_module",
        )
        import importlib
        import sys as _sys

        runtime_dir = ROOT / "skills" / "provider-manager" / "scripts"
        if str(runtime_dir) not in _sys.path:
            _sys.path.insert(0, str(runtime_dir))
        cls.pc = importlib.import_module("arkspace_runtime.provider_config")

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.config_path = str(Path(self.tmp.name) / "providers.json")
        self.state_path = str(Path(self.tmp.name) / "state.json")
        self.error_path = str(Path(self.tmp.name) / "err.json")
        self.error_env = patch.dict(os.environ, {"ARKSPACE_ERROR_FILE": self.error_path})
        self.error_env.start()
        self.addCleanup(self.error_env.stop)
        self._configure_brave()

    def _configure_brave(self):
        os.environ["BRAVE_API_KEY"] = "brave-test-key"
        self.addCleanup(os.environ.pop, "BRAVE_API_KEY", None)
        self.pc.set_provider_endpoint(
            "brave",
            capability="web_search",
            base_url="https://api.search.brave.com",
            config_path=self.config_path,
        )
        self.pc.add_key_ref(
            "brave",
            key_ref="env:BRAVE_API_KEY",
            auth_header="X-Subscription-Token",
            config_path=self.config_path,
        )

    def _read_error_record(self):
        return json.loads(Path(self.error_path).read_text(encoding="utf-8"))

    def _recording_get_json(self, payload):
        calls = []

        def fake_get_json(url, headers, timeout):
            calls.append((url, dict(headers), timeout))
            return payload

        return fake_get_json, calls

    def _brave_payload(self, results=None):
        if results is None:
            results = [
                {"title": "Alpha", "url": "https://a.example", "description": "first snippet"},
                {"title": "Beta", "url": "https://b.example", "description": "second"},
            ]
        return {"web": {"results": results}}

    def test_success_maps_web_results_and_query_params(self):
        fake_get_json, calls = self._recording_get_json(self._brave_payload())
        res = self.m.run_search(
            "agent skills",
            max_results=2,
            config_path=self.config_path,
            state_path=self.state_path,
            get_json=fake_get_json,
        )

        self.assertEqual(res["provider"], "brave")
        self.assertEqual(res["capability"], "web_search")
        self.assertEqual(res["query"], "agent skills")
        self.assertEqual(len(res["results"]), 2)
        self.assertEqual(res["results"][0]["title"], "Alpha")
        self.assertEqual(res["results"][0]["url"], "https://a.example")
        self.assertEqual(res["results"][0]["snippet"], "first snippet")
        # No generic success envelope.
        self.assertNotIn("ok", res)

        url, headers, _timeout = calls[0]
        parsed = urllib.parse.urlsplit(url)
        self.assertIn("api.search.brave.com", parsed.netloc)
        self.assertEqual(parsed.path, "/res/v1/web/search")
        query = urllib.parse.parse_qs(parsed.query)
        self.assertEqual(query["q"], ["agent skills"])
        self.assertEqual(query["count"], ["2"])
        self.assertEqual(headers.get("X-Subscription-Token"), "brave-test-key")

    def test_max_results_and_timeout_honored(self):
        fake_get_json, calls = self._recording_get_json(self._brave_payload())
        self.m.run_search(
            "q",
            max_results=1,
            timeout=12,
            config_path=self.config_path,
            state_path=self.state_path,
            get_json=fake_get_json,
        )
        _url, _headers, timeout = calls[0]
        self.assertEqual(timeout, 12)
        self.assertEqual(
            urllib.parse.parse_qs(urllib.parse.urlsplit(_url).query)["count"], ["1"]
        )

    def test_nonpositive_max_results_is_invalid_request_before_network(self):
        fake_get_json, calls = self._recording_get_json(self._brave_payload())

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search(
                "q",
                max_results=0,
                config_path=self.config_path,
                state_path=self.state_path,
                get_json=fake_get_json,
            )

        self.assertEqual(ctx.exception.kind, "invalid-request")
        self.assertEqual(calls, [])
        self.assertEqual(self._read_error_record()["kind"], "invalid-request")

    def test_cli_nonpositive_max_results_is_controlled_and_writes_error_record(self):
        with patch.object(sys, "argv", ["brave_search.py", "--max-results", "0", "q"]), patch.object(
            self.m, "_default_get_json", side_effect=AssertionError("network must not run")
        ), patch("sys.stderr", new=io.StringIO()) as err:
            code = self.m.main()

        self.assertEqual(code, 1)
        self.assertIn("max_results must be a positive integer", err.getvalue())
        self.assertNotIn("Traceback", err.getvalue())
        self.assertEqual(self._read_error_record()["kind"], "invalid-request")

    def test_http_401_maps_to_auth_and_writes_error_record(self):
        def unauthorized(url, headers, timeout):
            raise urllib.error.HTTPError(url, 401, "Unauthorized", http.client.HTTPMessage(), None)

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search(
                "q", config_path=self.config_path, state_path=self.state_path, get_json=unauthorized
            )
        self.assertEqual(ctx.exception.kind, "auth")
        self.assertEqual(ctx.exception.status, 401)
        record = self._read_error_record()
        self.assertEqual(record["kind"], "auth")
        self.assertEqual(record["provider"], "brave")
        self.assertEqual(record["capability"], "web_search")

    def test_http_429_maps_to_quota_and_writes_error_record(self):
        def rate_limited(url, headers, timeout):
            raise urllib.error.HTTPError(url, 429, "Too Many Requests", http.client.HTTPMessage(), None)

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search(
                "q", config_path=self.config_path, state_path=self.state_path, get_json=rate_limited
            )
        self.assertEqual(ctx.exception.kind, "quota")
        self.assertEqual(ctx.exception.status, 429)
        record = self._read_error_record()
        self.assertEqual(record["kind"], "quota")

    def test_network_failure_maps_to_network(self):
        def unreachable(url, headers, timeout):
            raise urllib.error.URLError("connection refused")

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search(
                "q", config_path=self.config_path, state_path=self.state_path, get_json=unreachable
            )
        self.assertEqual(ctx.exception.kind, "network")
        self.assertIsNone(ctx.exception.status)
        record = self._read_error_record()
        self.assertEqual(record["kind"], "network")

    def test_missing_web_results_maps_to_invalid_response(self):
        fake_get_json, _calls = self._recording_get_json({"web": {}})
        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search(
                "q", config_path=self.config_path, state_path=self.state_path, get_json=fake_get_json
            )
        self.assertEqual(ctx.exception.kind, "invalid-response")

    def test_unparseable_payload_maps_to_invalid_response(self):
        def bad_json(url, headers, timeout):
            raise ValueError("invalid JSON from Brave")

        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search(
                "q", config_path=self.config_path, state_path=self.state_path, get_json=bad_json
            )
        self.assertEqual(ctx.exception.kind, "invalid-response")

    def test_missing_key_fails_with_config_and_writes_error_record(self):
        os.environ.pop("BRAVE_API_KEY", None)
        # Unconfigured provider: no config entry at all.
        with self.assertRaises(self.m.SearchError) as ctx:
            self.m.run_search(
                "q", config_path="/nonexistent/providers.json", state_path=self.state_path
            )
        self.assertEqual(ctx.exception.kind, "config")
        record = self._read_error_record()
        self.assertEqual(record["kind"], "config")
        self.assertEqual(record["provider"], "brave")

    def test_cli_missing_key_stops_with_setup_guidance(self):
        os.environ.pop("BRAVE_API_KEY", None)
        with patch.object(sys, "argv", ["brave_search.py", "q"]), patch(
            "sys.stderr", new=io.StringIO()
        ) as err:
            code = self.m.main()
        self.assertEqual(code, 2)
        self.assertIn("setup", err.getvalue())
        self.assertIn("provider setup brave", err.getvalue())

    def test_check_missing_key_uses_setup_wizard_guidance(self):
        os.environ.pop("BRAVE_API_KEY", None)
        with patch.object(sys, "argv", ["brave_search.py", "--check"]), patch(
            "sys.stderr", new=io.StringIO()
        ) as err:
            code = self.m.main()
        self.assertEqual(code, 2)
        self.assertIn("provider setup brave --wizard", err.getvalue())
        self.assertNotIn("provider configure brave", err.getvalue())


if __name__ == "__main__":
    unittest.main()
