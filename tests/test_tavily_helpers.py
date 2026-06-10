import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class TavilyHelperTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.config_path = str(Path(self.tmpdir.name) / "providers.json")
        self.state_path = str(Path(self.tmpdir.name) / "state.json")
        self.secrets_path = str(Path(self.tmpdir.name) / "secrets.json")
        os.environ["ARKSPACE_PROVIDER_SECRETS"] = self.secrets_path
        self.addCleanup(os.environ.pop, "ARKSPACE_PROVIDER_SECRETS", None)
        self.search = load_module(
            ROOT / "skills" / "tavily-search" / "scripts" / "tavily_search.py",
            "tavily_search_test_module",
        )
        self.extract = load_module(
            ROOT / "skills" / "tavily-extract" / "scripts" / "tavily_extract.py",
            "tavily_extract_test_module",
        )
        self.map = load_module(
            ROOT / "skills" / "tavily-map" / "scripts" / "tavily_map.py",
            "tavily_map_test_module",
        )
        self.crawl = load_module(
            ROOT / "skills" / "tavily-crawl" / "scripts" / "tavily_crawl.py",
            "tavily_crawl_test_module",
        )
        self.research = load_module(
            ROOT / "skills" / "tavily-research" / "scripts" / "tavily_research.py",
            "tavily_research_test_module",
        )

    def configure_tavily(self):
        os.environ["TAVILY_API_KEY_TEST"] = "tvly-test-key"
        self.addCleanup(os.environ.pop, "TAVILY_API_KEY_TEST", None)
        self.search.provider_config.set_provider_endpoint(
            "tavily",
            capability="web_search",
            base_url="https://api.tavily.com",
            config_path=self.config_path,
        )
        data = self.search.provider_config.load_config(self.config_path)
        data["providers"]["tavily"]["capabilities"] = [
            "web_search",
            "web_fetch",
            "web_map",
            "web_crawl",
            "deep_research",
        ]
        self.search.provider_config.save_config(data, self.config_path)
        self.search.provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_TEST",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )

    def test_search_builds_tavily_payload(self):
        self.configure_tavily()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {
                "query": payload["query"],
                "results": [{"title": "Result", "url": "https://example.com", "content": "Snippet", "score": 0.9}],
                "usage": {"credits": 1},
                "request_id": "req-test",
            }

        result = self.search.run_search(
            "agent skills",
            max_results=3,
            search_depth="basic",
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.tavily.com/search")
        self.assertEqual(requests[0]["headers"]["Authorization"], "Bearer tvly-test-key")
        self.assertEqual(requests[0]["payload"]["max_results"], 3)
        self.assertEqual(requests[0]["payload"]["search_depth"], "basic")
        self.assertEqual(result["provider"], "tavily")
        self.assertEqual(result["results"][0]["snippet"], "Snippet")

    def test_search_records_http_status_for_rotation_failures(self):
        self.configure_tavily()

        def fake_post(url, headers, payload, timeout):
            raise self.search.ProviderRequestError("rate limited", status=429)

        with self.assertRaises(self.search.ProviderRequestError):
            self.search.run_search(
                "agent skills",
                config_path=self.config_path,
                state_path=self.state_path,
                post_json=fake_post,
            )

        state = self.search.provider_config.load_state(self.state_path)
        key_state = state["tavily"]["keys"]["env:TAVILY_API_KEY_TEST"]
        self.assertEqual(key_state["last_status"], 429)
        self.assertGreater(key_state["cooldown_until"], 0)

    def test_search_429_cools_key_without_blocking_endpoint_rotation(self):
        self.configure_tavily()
        os.environ["TAVILY_API_KEY_SECOND"] = "tvly-second-key"
        self.addCleanup(os.environ.pop, "TAVILY_API_KEY_SECOND", None)
        self.search.provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_SECOND",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )

        def fake_post(url, headers, payload, timeout):
            raise self.search.ProviderRequestError("rate limited", status=429)

        with self.assertRaises(self.search.ProviderRequestError):
            self.search.run_search(
                "agent skills",
                config_path=self.config_path,
                state_path=self.state_path,
                post_json=fake_post,
            )

        state = self.search.provider_config.load_state(self.state_path)
        self.assertNotIn("endpoints", state["tavily"])
        resolved = self.search.provider_config.resolve_provider(
            "tavily",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )
        self.assertEqual(resolved["auth"]["key_ref"], "env:TAVILY_API_KEY_SECOND")

    def test_search_records_malformed_json_failure_for_rotation(self):
        self.configure_tavily()

        def fake_post(url, headers, payload, timeout):
            raise json.JSONDecodeError("bad json", "not-json", 0)

        with self.assertRaises(self.search.ProviderRequestError):
            self.search.run_search(
                "agent skills",
                config_path=self.config_path,
                state_path=self.state_path,
                post_json=fake_post,
            )

        state = self.search.provider_config.load_state(self.state_path)
        endpoint_state = state["tavily"]["endpoints"]["default"]
        self.assertNotIn("keys", state["tavily"])
        self.assertIsNone(endpoint_state["last_status"])
        self.assertGreater(endpoint_state["cooldown_until"], 0)

    def test_extract_builds_tavily_payload(self):
        self.configure_tavily()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {"results": [{"url": payload["urls"][0], "raw_content": "# Page"}], "request_id": "req-extract"}

        result = self.extract.run_extract(
            ["https://example.com"],
            query="auth",
            timeout=45,
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.tavily.com/extract")
        self.assertEqual(requests[0]["headers"]["Authorization"], "Bearer tvly-test-key")
        self.assertEqual(requests[0]["payload"]["urls"], ["https://example.com"])
        self.assertEqual(requests[0]["payload"]["query"], "auth")
        self.assertEqual(requests[0]["payload"]["timeout"], 45)
        self.assertEqual(requests[0]["timeout"], 50)
        self.assertEqual(result["results"][0]["raw_content"], "# Page")

    def test_extract_records_unexpected_request_failure_for_rotation(self):
        self.configure_tavily()

        def fake_post(url, headers, payload, timeout):
            raise TimeoutError("timed out")

        with self.assertRaises(self.extract.ProviderRequestError):
            self.extract.run_extract(
                ["https://example.com"],
                config_path=self.config_path,
                state_path=self.state_path,
                post_json=fake_post,
            )

        state = self.extract.provider_config.load_state(self.state_path)
        endpoint_state = state["tavily"]["endpoints"]["default"]
        self.assertNotIn("keys", state["tavily"])
        self.assertIsNone(endpoint_state["last_status"])
        self.assertGreater(endpoint_state["cooldown_until"], 0)

    def test_map_builds_tavily_payload(self):
        self.configure_tavily()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {"base_url": "docs.example.com", "results": ["https://docs.example.com/auth"], "request_id": "req-map"}

        result = self.map.run_map(
            "https://docs.example.com",
            instructions="Find auth docs",
            max_depth=2,
            limit=100,
            select_paths=["/docs/.*"],
            allow_external=False,
            timeout=30,
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.tavily.com/map")
        self.assertEqual(requests[0]["headers"]["Authorization"], "Bearer tvly-test-key")
        self.assertEqual(requests[0]["payload"]["url"], "https://docs.example.com")
        self.assertEqual(requests[0]["payload"]["instructions"], "Find auth docs")
        self.assertEqual(requests[0]["payload"]["max_depth"], 2)
        self.assertEqual(requests[0]["payload"]["limit"], 100)
        self.assertEqual(requests[0]["payload"]["select_paths"], ["/docs/.*"])
        self.assertFalse(requests[0]["payload"]["allow_external"])
        self.assertEqual(result["capability"], "web_map")
        self.assertEqual(result["results"], ["https://docs.example.com/auth"])

    def test_crawl_builds_tavily_payload(self):
        self.configure_tavily()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {
                "base_url": "docs.example.com",
                "results": [{"url": "https://docs.example.com/auth", "raw_content": "# Auth"}],
                "request_id": "req-crawl",
            }

        result = self.crawl.run_crawl(
            "https://docs.example.com",
            instructions="Find auth docs",
            chunks_per_source=3,
            max_depth=2,
            limit=10,
            extract_depth="advanced",
            content_format="markdown",
            timeout=45,
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.tavily.com/crawl")
        self.assertEqual(requests[0]["headers"]["Authorization"], "Bearer tvly-test-key")
        self.assertEqual(requests[0]["payload"]["chunks_per_source"], 3)
        self.assertEqual(requests[0]["payload"]["extract_depth"], "advanced")
        self.assertEqual(requests[0]["payload"]["format"], "markdown")
        self.assertEqual(result["capability"], "web_crawl")
        self.assertEqual(result["results"][0]["raw_content"], "# Auth")

    def test_research_builds_payload_and_can_poll(self):
        self.configure_tavily()
        post_requests = []
        get_requests = []

        def fake_post(url, headers, payload, timeout):
            post_requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {"request_id": "req-research", "status": "pending", "input": payload["input"], "model": payload["model"]}

        def fake_get(url, headers, timeout):
            get_requests.append({"url": url, "headers": headers, "timeout": timeout})
            return {
                "request_id": "req-research",
                "status": "completed",
                "content": "Report",
                "sources": [{"title": "Source", "url": "https://example.com"}],
            }

        result = self.research.run_research(
            "AI coding agents market",
            model="pro",
            citation_format="numbered",
            include_domains=["github.com"],
            wait=True,
            poll_interval=1,
            timeout=30,
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
            get_json=fake_get,
        )

        self.assertEqual(post_requests[0]["url"], "https://api.tavily.com/research")
        self.assertEqual(post_requests[0]["headers"]["Authorization"], "Bearer tvly-test-key")
        self.assertEqual(post_requests[0]["payload"]["input"], "AI coding agents market")
        self.assertEqual(post_requests[0]["payload"]["model"], "pro")
        self.assertEqual(post_requests[0]["payload"]["citation_format"], "numbered")
        self.assertEqual(post_requests[0]["payload"]["include_domains"], ["github.com"])
        self.assertEqual(get_requests[0]["url"], "https://api.tavily.com/research/req-research")
        self.assertEqual(result["capability"], "deep_research")
        self.assertEqual(result["content"], "Report")

    def test_check_reports_missing_key_without_network(self):
        output = self.search.check_config(config_path=self.config_path, state_path=self.state_path)
        self.assertFalse(output["ok"])
        self.assertIn("provider tavily is not configured", output["error"])
        self.assertIn("provider setup tavily --wizard", output["error"])

    def test_check_reports_endpoint_only_setup_needs_key_ref(self):
        self.search.provider_config.set_provider_endpoint(
            "tavily",
            capability="web_search",
            capabilities=["web_search", "web_fetch"],
            base_url="https://api.tavily.com",
            config_path=self.config_path,
        )

        output = self.search.check_config(config_path=self.config_path, state_path=self.state_path)

        self.assertFalse(output["ok"])
        self.assertIn("provider tavily has no key refs", output["error"])
        self.assertIn("provider setup tavily --wizard", output["error"])

    def test_extended_capability_check_migrates_existing_tavily_config(self):
        self.search.provider_config.set_provider_endpoint(
            "tavily",
            capability="web_search",
            capabilities=["web_search", "web_fetch"],
            base_url="https://api.tavily.com",
            config_path=self.config_path,
        )
        self.search.provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_TEST",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )
        os.environ["TAVILY_API_KEY_TEST"] = "tvly-test-key"
        self.addCleanup(os.environ.pop, "TAVILY_API_KEY_TEST", None)

        output = self.map.check_config(config_path=self.config_path, state_path=self.state_path)
        data = self.search.provider_config.load_config(self.config_path)

        self.assertTrue(output["ok"])
        self.assertEqual(output["capability"], "web_map")
        self.assertIn("web_map", data["providers"]["tavily"]["capabilities"])
        self.assertIn("deep_research", data["providers"]["tavily"]["capabilities"])

    def test_search_check_markdown_prints_success_message(self):
        result = {"ok": True, "provider": "tavily", "capability": "web_search"}
        with self.capture_stdout() as output:
            self.search.print_markdown(result)

        self.assertIn("Tavily web_search provider is configured.", output.getvalue())

    def test_extract_check_markdown_prints_success_message(self):
        result = {"ok": True, "provider": "tavily", "capability": "web_fetch"}
        with self.capture_stdout() as output:
            self.extract.print_markdown(result)

        self.assertIn("Tavily web_fetch provider is configured.", output.getvalue())

    def test_new_tavily_check_markdown_prints_success_messages(self):
        expectations = [
            (self.map, {"ok": True, "provider": "tavily", "capability": "web_map"}, "Tavily web_map provider is configured."),
            (self.crawl, {"ok": True, "provider": "tavily", "capability": "web_crawl"}, "Tavily web_crawl provider is configured."),
            (
                self.research,
                {"ok": True, "provider": "tavily", "capability": "deep_research"},
                "Tavily deep_research provider is configured.",
            ),
        ]
        for module, result, message in expectations:
            with self.subTest(message=message):
                with self.capture_stdout() as output:
                    module.print_markdown(result)
                self.assertIn(message, output.getvalue())

    def capture_stdout(self):
        import contextlib
        import io

        return contextlib.redirect_stdout(io.StringIO())


if __name__ == "__main__":
    unittest.main()
