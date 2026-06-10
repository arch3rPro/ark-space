import importlib.util
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


class ExaHelperTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.config_path = str(Path(self.tmpdir.name) / "providers.json")
        self.state_path = str(Path(self.tmpdir.name) / "state.json")
        self.secrets_path = str(Path(self.tmpdir.name) / "secrets.json")
        os.environ["ARKSPACE_PROVIDER_SECRETS"] = self.secrets_path
        self.addCleanup(os.environ.pop, "ARKSPACE_PROVIDER_SECRETS", None)
        self.search = load_module(
            ROOT / "skills" / "exa-search" / "scripts" / "exa_search.py",
            "exa_search_test_module",
        )
        self.contents = load_module(
            ROOT / "skills" / "exa-contents" / "scripts" / "exa_contents.py",
            "exa_contents_test_module",
        )
        self.answer = load_module(
            ROOT / "skills" / "exa-answer" / "scripts" / "exa_answer.py",
            "exa_answer_test_module",
        )
        self.context = load_module(
            ROOT / "skills" / "exa-context" / "scripts" / "exa_context.py",
            "exa_context_test_module",
        )
        self.similar = load_module(
            ROOT / "skills" / "exa-similar" / "scripts" / "exa_similar.py",
            "exa_similar_test_module",
        )

    def configure_exa(self):
        os.environ["EXA_API_KEY_TEST"] = "exa-test-key"
        self.addCleanup(os.environ.pop, "EXA_API_KEY_TEST", None)
        self.search.provider_config.set_provider_endpoint(
            "exa",
            capability="web_search",
            capabilities=["web_search", "web_fetch", "deep_research", "code_context", "related_pages"],
            base_url="https://api.exa.ai",
            config_path=self.config_path,
        )
        self.search.provider_config.add_key_ref(
            "exa",
            key_ref="env:EXA_API_KEY_TEST",
            auth_header="x-api-key",
            auth_prefix="",
            config_path=self.config_path,
        )

    def test_search_builds_exa_payload(self):
        self.configure_exa()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {
                "results": [
                    {
                        "title": "Result",
                        "url": "https://example.com",
                        "summary": "Snippet",
                        "score": 0.9,
                    }
                ],
                "requestId": "req-search",
            }

        result = self.search.run_search(
            "agent skills",
            max_results=3,
            search_type="deep-reasoning",
            include_domains=["docs.example.com"],
            start_crawl_date="2026-01-01T00:00:00Z",
            include_summary=True,
            include_highlights=True,
            highlight_num_sentences=3,
            additional_queries=["agent workflows"],
            user_location="US",
            moderation=True,
            output_schema={"type": "object"},
            system_prompt="Return structured projects.",
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.exa.ai/search")
        self.assertEqual(requests[0]["headers"]["x-api-key"], "exa-test-key")
        self.assertEqual(requests[0]["payload"]["numResults"], 3)
        self.assertEqual(requests[0]["payload"]["type"], "deep-reasoning")
        self.assertEqual(requests[0]["payload"]["includeDomains"], ["docs.example.com"])
        self.assertEqual(requests[0]["payload"]["startCrawlDate"], "2026-01-01T00:00:00Z")
        self.assertEqual(
            requests[0]["payload"]["contents"],
            {"highlights": {"numSentences": 3}, "summary": True},
        )
        self.assertEqual(requests[0]["payload"]["additionalQueries"], ["agent workflows"])
        self.assertEqual(requests[0]["payload"]["userLocation"], "US")
        self.assertTrue(requests[0]["payload"]["moderation"])
        self.assertEqual(requests[0]["payload"]["outputSchema"], {"type": "object"})
        self.assertEqual(requests[0]["payload"]["systemPrompt"], "Return structured projects.")
        self.assertEqual(result["provider"], "exa")
        self.assertEqual(result["results"][0]["snippet"], "Snippet")

    def test_search_rejects_people_filters_before_request(self):
        self.configure_exa()

        with self.assertRaisesRegex(self.search.provider_config.ProviderConfigError, "people search"):
            self.search.run_search(
                "senior ML engineers",
                category="people",
                include_domains=["linkedin.com"],
                config_path=self.config_path,
                state_path=self.state_path,
                post_json=lambda url, headers, payload, timeout: {},
            )

    def test_contents_builds_exa_payload(self):
        self.configure_exa()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {
                "results": [
                    {
                        "title": "Page",
                        "url": payload["urls"][0],
                        "text": "# Page",
                        "summary": "Summary",
                        "subpages": [{"url": "https://example.com/docs"}],
                        "extras": {"links": ["https://example.com/docs"]},
                    }
                ],
                "statuses": [{"id": payload["urls"][0], "status": "success", "source": "cached"}],
                "requestId": "req-contents",
            }

        result = self.contents.run_contents(
            ["https://example.com"],
            include_summary=True,
            include_highlights=True,
            text_max_characters=1000,
            highlight_query="setup",
            max_age_hours=24,
            subpages=2,
            subpage_target=["docs"],
            include_links=True,
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.exa.ai/contents")
        self.assertEqual(requests[0]["headers"]["x-api-key"], "exa-test-key")
        self.assertEqual(requests[0]["payload"]["urls"], ["https://example.com"])
        self.assertEqual(requests[0]["payload"]["text"], {"maxCharacters": 1000})
        self.assertTrue(requests[0]["payload"]["summary"])
        self.assertEqual(requests[0]["payload"]["highlights"], {"query": "setup"})
        self.assertEqual(requests[0]["payload"]["maxAgeHours"], 24)
        self.assertEqual(requests[0]["payload"]["subpages"], 2)
        self.assertEqual(requests[0]["payload"]["subpageTarget"], ["docs"])
        self.assertEqual(requests[0]["payload"]["extras"], {"links": True})
        self.assertEqual(result["capability"], "web_fetch")
        self.assertEqual(result["results"][0]["raw_content"], "# Page")
        self.assertEqual(result["statuses"][0]["status"], "success")

    def test_similar_builds_exa_payload(self):
        self.configure_exa()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {
                "results": [
                    {
                        "title": "Similar",
                        "url": "https://similar.example.com",
                        "summary": "Related page",
                    }
                ],
                "requestId": "req-similar",
            }

        result = self.similar.run_similar(
            "https://example.com",
            max_results=4,
            search_type="deep",
            include_domains=["github.com"],
            include_summary=True,
            include_highlights=True,
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.exa.ai/findSimilar")
        self.assertEqual(requests[0]["headers"]["x-api-key"], "exa-test-key")
        self.assertEqual(requests[0]["payload"]["url"], "https://example.com")
        self.assertEqual(requests[0]["payload"]["numResults"], 4)
        self.assertEqual(requests[0]["payload"]["type"], "deep")
        self.assertEqual(requests[0]["payload"]["includeDomains"], ["github.com"])
        self.assertEqual(requests[0]["payload"]["contents"], {"highlights": True, "summary": True})
        self.assertEqual(result["capability"], "related_pages")
        self.assertEqual(result["results"][0]["summary"], "Related page")

    def test_answer_builds_exa_payload(self):
        self.configure_exa()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {
                "answer": "Short answer",
                "sources": [{"title": "Source", "url": "https://example.com"}],
                "requestId": "req-answer",
            }

        result = self.answer.run_answer(
            "What changed?",
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.exa.ai/answer")
        self.assertEqual(requests[0]["headers"]["x-api-key"], "exa-test-key")
        self.assertEqual(requests[0]["payload"], {"query": "What changed?"})
        self.assertEqual(result["capability"], "deep_research")
        self.assertEqual(result["answer"], "Short answer")

    def test_context_builds_exa_payload(self):
        self.configure_exa()
        requests = []

        def fake_post(url, headers, payload, timeout):
            requests.append({"url": url, "headers": headers, "payload": payload, "timeout": timeout})
            return {
                "query": payload["query"],
                "response": "## React hooks examples",
                "resultsCount": 12,
                "outputTokens": 5000,
                "requestId": "req-context",
            }

        result = self.context.run_context(
            "React hooks state management examples",
            tokens=5000,
            config_path=self.config_path,
            state_path=self.state_path,
            post_json=fake_post,
        )

        self.assertEqual(requests[0]["url"], "https://api.exa.ai/context")
        self.assertEqual(requests[0]["headers"]["x-api-key"], "exa-test-key")
        self.assertEqual(
            requests[0]["payload"],
            {"query": "React hooks state management examples", "tokensNum": 5000},
        )
        self.assertEqual(result["capability"], "code_context")
        self.assertEqual(result["response"], "## React hooks examples")
        self.assertEqual(result["results_count"], 12)

    def test_unexpected_failure_cools_endpoint(self):
        self.configure_exa()
        os.environ["EXA_API_KEY_SECOND"] = "exa-second-key"
        self.addCleanup(os.environ.pop, "EXA_API_KEY_SECOND", None)
        self.search.provider_config.add_key_ref(
            "exa",
            key_ref="env:EXA_API_KEY_SECOND",
            auth_header="x-api-key",
            auth_prefix="",
            config_path=self.config_path,
        )

        def fake_post(url, headers, payload, timeout):
            raise self.search.provider_config.ProviderConfigError("rate limited")

        with self.assertRaises(self.search.provider_config.ProviderConfigError):
            self.search.run_search(
                "agent skills",
                config_path=self.config_path,
                state_path=self.state_path,
                post_json=fake_post,
            )

        state = self.search.provider_config.load_state(self.state_path)
        endpoint_state = state["exa"]["endpoints"]["default"]
        self.assertGreater(endpoint_state["cooldown_until"], 0)

    def test_429_status_cools_key_and_allows_next_key(self):
        self.configure_exa()
        os.environ["EXA_API_KEY_SECOND"] = "exa-second-key"
        self.addCleanup(os.environ.pop, "EXA_API_KEY_SECOND", None)
        self.search.provider_config.add_key_ref(
            "exa",
            key_ref="env:EXA_API_KEY_SECOND",
            auth_header="x-api-key",
            auth_prefix="",
            config_path=self.config_path,
        )

        def fake_post(url, headers, payload, timeout):
            raise self.search.exa_client.ProviderRequestError("rate limited", status=429)

        with self.assertRaises(self.search.exa_client.ProviderRequestError):
            self.search.run_search(
                "agent skills",
                config_path=self.config_path,
                state_path=self.state_path,
                post_json=fake_post,
            )

        state = self.search.provider_config.load_state(self.state_path)
        key_state = state["exa"]["keys"]["env:EXA_API_KEY_TEST"]
        self.assertEqual(key_state["last_status"], 429)
        self.assertGreater(key_state["cooldown_until"], 0)
        resolved = self.search.provider_config.resolve_provider(
            "exa",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )
        self.assertEqual(resolved["auth"]["key_ref"], "env:EXA_API_KEY_SECOND")


if __name__ == "__main__":
    unittest.main()
