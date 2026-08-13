import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def _write_error_record(path, record):
    """Write a version-1 error record to ``path`` for chain lifecycle tests.

    Mirrors the provider runtime's on-disk record shape so the real
    ``read_error_file`` can parse it.
    """
    try:
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(record, handle, ensure_ascii=False, sort_keys=True)
    except OSError:
        return False
    return True


def load_arkspace_module():
    spec = importlib.util.spec_from_file_location("arkspace_cli_test_module", ROOT / "scripts" / "arkspace.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ArkspaceCliTests(unittest.TestCase):
    def setUp(self):
        self.arkspace = load_arkspace_module()

    def run_cli(self, argv):
        calls = []

        def fake_run(args):
            calls.append(args)
            return 0

        with patch.object(sys, "argv", ["arkspace", *argv]), patch.object(self.arkspace, "run", fake_run):
            status = self.arkspace.main()
        return status, calls

    def test_provider_check_tavily_delegates_to_tavily_search_check(self):
        status, calls = self.run_cli(["provider", "check", "tavily"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "skills/web-search/scripts/tavily_search.py", "--check"],
        )

    def test_provider_check_arxiv_delegates_to_arxiv_search_check(self):
        status, calls = self.run_cli(["provider", "check", "arxiv"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "skills/web-search/scripts/arxiv_search.py", "--check"],
        )

    def test_provider_check_brave_forwards_custom_config_and_state_paths(self):
        status, calls = self.run_cli(
            [
                "provider",
                "check",
                "brave",
                "--config-path",
                "/tmp/providers.json",
                "--state-path",
                "/tmp/state.json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-search/scripts/brave_search.py",
                "--check",
                "--config-path",
                "/tmp/providers.json",
                "--state-path",
                "/tmp/state.json",
            ],
        )

    def test_provider_check_tavily_fetch_delegates_to_extract_check(self):
        status, calls = self.run_cli(["provider", "check", "tavily", "--capability", "web_fetch"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "skills/web-fetch/scripts/tavily_extract.py", "--check"],
        )

    def test_provider_check_tavily_extended_capabilities_delegate_to_helpers(self):
        expectations = {
            "web_map": [sys.executable, "skills/web-site/scripts/tavily_map.py", "--check"],
            "web_crawl": [sys.executable, "skills/web-site/scripts/tavily_crawl.py", "--check"],
            "deep_research": [sys.executable, "skills/web-research/scripts/tavily_research.py", "--check"],
        }
        for capability, expected in expectations.items():
            with self.subTest(capability=capability):
                status, calls = self.run_cli(["provider", "check", "tavily", "--capability", capability])
                self.assertEqual(status, 0)
                self.assertEqual(calls[0], expected)

    def test_provider_check_exa_capabilities_delegate_to_helpers(self):
        expectations = {
            "web_search": [sys.executable, "skills/web-search/scripts/exa_search.py", "--check"],
            "web_fetch": [sys.executable, "skills/web-fetch/scripts/exa_contents.py", "--check"],
            "deep_research": [sys.executable, "skills/web-research/scripts/exa_answer.py", "--check"],
            "code_context": [sys.executable, "skills/code-context/scripts/exa_context.py", "--check"],
            "related_pages": [sys.executable, "skills/web-search/scripts/exa_similar.py", "--check"],
        }
        for capability, expected in expectations.items():
            with self.subTest(capability=capability):
                status, calls = self.run_cli(
                    [
                        "provider",
                        "check",
                        "exa",
                        "--capability",
                        capability,
                        "--config-path",
                        "/tmp/providers.json",
                        "--state-path",
                        "/tmp/state.json",
                    ]
                )
                self.assertEqual(status, 0)
                self.assertEqual(
                    calls[0],
                    [*expected, "--config-path", "/tmp/providers.json", "--state-path", "/tmp/state.json"],
                )

    def test_provider_check_firecrawl_capabilities_delegate_to_helpers(self):
        expectations = {
            "web_search": [sys.executable, "skills/web-search/scripts/firecrawl_search.py", "--check"],
            "web_fetch": [sys.executable, "skills/web-fetch/scripts/firecrawl_scrape.py", "--check"],
            "web_map": [sys.executable, "skills/web-site/scripts/firecrawl_map.py", "--check"],
            "web_crawl": [sys.executable, "skills/web-site/scripts/firecrawl_crawl.py", "--check"],
            "structured_extract": [sys.executable, "skills/web-extract/scripts/firecrawl_agent.py", "--check"],
            "web_interact": [sys.executable, "skills/web-automation/scripts/firecrawl_browser.py", "--check"],
            "web_monitor": [sys.executable, "skills/web-automation/scripts/firecrawl_monitor.py", "--check"],
        }
        for capability, expected in expectations.items():
            with self.subTest(capability=capability):
                status, calls = self.run_cli(
                    [
                        "provider",
                        "check",
                        "firecrawl",
                        "--capability",
                        capability,
                        "--config-path",
                        "/tmp/providers.json",
                        "--state-path",
                        "/tmp/state.json",
                    ]
                )
                self.assertEqual(status, 0)
                self.assertEqual(
                    calls[0],
                    [*expected, "--config-path", "/tmp/providers.json", "--state-path", "/tmp/state.json"],
                )

    def test_provider_check_defuddle_delegates_to_cli_version(self):
        status, calls = self.run_cli(["provider", "check", "defuddle", "--capability", "web_fetch"])

        self.assertEqual(status, 0)
        self.assertEqual(calls[0], ["defuddle", "--version"])

    def test_provider_resolve_forwards_custom_config_and_state_paths(self):
        status, calls = self.run_cli(
            [
                "provider",
                "resolve",
                "tavily",
                "--capability",
                "web_search",
                "--config-path",
                "/tmp/providers.json",
                "--state-path",
                "/tmp/state.json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "scripts/arkspace_provider.py",
                "--config-path",
                "/tmp/providers.json",
                "--state-path",
                "/tmp/state.json",
                "resolve",
                "tavily",
                "--capability",
                "web_search",
            ],
        )

    def test_provider_configure_tavily_delegates_to_provider_manager(self):
        status, calls = self.run_cli(["provider", "configure", "tavily", "--base-url", "https://api.tavily.com"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "scripts/arkspace_provider.py",
                "configure",
                "tavily",
                "--base-url",
                "https://api.tavily.com",
            ],
        )

    def test_provider_add_key_tavily_delegates_prefix_to_provider_manager(self):
        status, calls = self.run_cli(
            [
                "provider",
                "add-key",
                "tavily",
                "--env",
                "TAVILY_API_KEY_1",
                "--header",
                "Authorization",
                "--prefix",
                "Bearer ",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "scripts/arkspace_provider.py",
                "add-key",
                "tavily",
                "--env",
                "TAVILY_API_KEY_1",
                "--header",
                "Authorization",
                "--prefix",
                "Bearer ",
            ],
        )

    def test_provider_setup_tavily_delegates_env_refs_to_provider_manager(self):
        status, calls = self.run_cli(
            [
                "provider",
                "setup",
                "tavily",
                "--env",
                "TAVILY_API_KEY_1",
                "--env",
                "TAVILY_API_KEY_2",
                "--check",
                "--config-path",
                "/tmp/providers.json",
                "--state-path",
                "/tmp/state.json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "scripts/arkspace_provider.py",
                "--config-path",
                "/tmp/providers.json",
                "--state-path",
                "/tmp/state.json",
                "setup",
                "tavily",
                "--env",
                "TAVILY_API_KEY_1",
                "--env",
                "TAVILY_API_KEY_2",
                "--check",
            ],
        )

    def test_provider_setup_tavily_forwards_private_secret_options(self):
        status, calls = self.run_cli(
            [
                "provider",
                "setup",
                "tavily",
                "--save-secret",
                "TAVILY_API_KEY_1",
                "--save-secret",
                "TAVILY_API_KEY_2",
                "--secret-stdin",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "scripts/arkspace_provider.py",
                "setup",
                "tavily",
                "--save-secret",
                "TAVILY_API_KEY_1",
                "--save-secret",
                "TAVILY_API_KEY_2",
                "--secret-stdin",
            ],
        )

    def test_provider_setup_tavily_forwards_wizard_options(self):
        status, calls = self.run_cli(["provider", "setup", "tavily", "--wizard", "--key-count", "2", "--secret-stdin"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "scripts/arkspace_provider.py",
                "setup",
                "tavily",
                "--wizard",
                "--key-count",
                "2",
                "--secret-stdin",
            ],
        )

    def test_provider_setup_exa_forwards_wizard_options(self):
        status, calls = self.run_cli(["provider", "setup", "exa", "--wizard", "--key-count", "2", "--secret-stdin"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "scripts/arkspace_provider.py",
                "setup",
                "exa",
                "--wizard",
                "--key-count",
                "2",
                "--secret-stdin",
            ],
        )

    def test_doctor_can_require_installed_host_gates(self):
        status, calls = self.run_cli(["doctor", "--installed-host", "all"])

        self.assertEqual(status, 0)
        self.assertIn([sys.executable, "scripts/smoke-test-installed-host.py", "--host", "codex"], calls)
        self.assertIn([sys.executable, "scripts/smoke-test-installed-host.py", "--host", "claude-code"], calls)

    def test_web_search_tavily_delegates_to_tavily_search_helper(self):
        status, calls = self.run_cli(
            ["web", "search", "--provider", "tavily", "--max-results", "3", "--output", "json", "agent skills"]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-search/scripts/tavily_search.py",
                "agent skills",
                "--max-results",
                "3",
                "--output",
                "json",
            ],
        )

    def test_web_search_searxng_passes_base_url_override(self):
        status, calls = self.run_cli(
            [
                "web",
                "search",
                "--provider",
                "searxng",
                "--base-url",
                "https://searx.example.org",
                "--max-results",
                "3",
                "agent skills",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-search/scripts/searxng_search.py",
                "agent skills",
                "--base-url",
                "https://searx.example.org",
                "--limit",
                "3",
            ],
        )

    def test_web_search_arxiv_delegates_to_arxiv_search_helper(self):
        status, calls = self.run_cli(
            [
                "web",
                "search",
                "--provider",
                "arxiv",
                "diffusion transformers",
                "--author",
                "William Peebles",
                "--category",
                "cs.CV",
                "--max-results",
                "3",
                "--sort-by",
                "submittedDate",
                "--output",
                "json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-search/scripts/arxiv_search.py",
                "diffusion transformers",
                "--max-results",
                "3",
                "--category",
                "cs.CV",
                "--author",
                "William Peebles",
                "--sort-by",
                "submittedDate",
                "--output",
                "json",
            ],
        )

    def test_web_search_arxiv_allows_id_list_without_query(self):
        status, calls = self.run_cli(["web", "search", "--provider", "arxiv", "--id-list", "1706.03762"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "skills/web-search/scripts/arxiv_search.py", "", "--id-list", "1706.03762"],
        )

    def test_web_search_exa_delegates_to_exa_search_helper(self):
        status, calls = self.run_cli(
            [
                "web",
                "search",
                "--provider",
                "exa",
                "--max-results",
                "3",
                "--search-type",
                "deep-reasoning",
                "--include-domains",
                "docs.example.com,github.com",
                "--freshness",
                "week",
                "--include-summary",
                "--include-highlights",
                "--highlight-num-sentences",
                "3",
                "--additional-queries",
                "skills frameworks,agent plugin systems",
                "--user-location",
                "US",
                "--output-schema",
                '{"type":"object"}',
                "--moderation",
                "--output",
                "json",
                "agent skills",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-search/scripts/exa_search.py",
                "agent skills",
                "--max-results",
                "3",
                "--search-type",
                "deep-reasoning",
                "--freshness",
                "week",
                "--include-domains",
                "docs.example.com,github.com",
                "--highlight-num-sentences",
                "3",
                "--additional-queries",
                "skills frameworks,agent plugin systems",
                "--user-location",
                "US",
                "--output-schema",
                '{"type":"object"}',
                "--output",
                "json",
                "--include-highlights",
                "--include-summary",
                "--moderation",
            ],
        )

    def test_web_search_firecrawl_delegates_to_firecrawl_search_helper(self):
        status, calls = self.run_cli(
            [
                "web",
                "search",
                "--provider",
                "firecrawl",
                "agent skills",
                "--max-results",
                "3",
                "--include-text",
                "--timeout",
                "45",
                "--output",
                "json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-search/scripts/firecrawl_search.py",
                "agent skills",
                "--max-results",
                "3",
                "--timeout",
                "45",
                "--output",
                "json",
                "--include-text",
            ],
        )

    def test_web_fetch_firecrawl_delegates_to_firecrawl_scrape_helper(self):
        status, calls = self.run_cli(
            [
                "web",
                "fetch",
                "--provider",
                "firecrawl",
                "https://example.com",
                "--only-main-content",
                "--format",
                "markdown,links",
                "--output",
                "json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-fetch/scripts/firecrawl_scrape.py",
                "https://example.com",
                "--format",
                "markdown,links",
                "--output",
                "json",
                "--only-main-content",
            ],
        )

    def test_web_fetch_defuddle_delegates_to_defuddle_parse(self):
        status, calls = self.run_cli(["web", "fetch", "--provider", "defuddle", "https://example.com"])

        self.assertEqual(status, 0)
        self.assertEqual(calls[0], ["defuddle", "parse", "https://example.com", "--md"])

    def test_web_fetch_defuddle_supports_json_output(self):
        status, calls = self.run_cli(["web", "fetch", "--provider", "defuddle", "https://example.com", "--output", "json"])

        self.assertEqual(status, 0)
        self.assertEqual(calls[0], ["defuddle", "parse", "https://example.com", "--json"])

    def test_site_firecrawl_map_and_crawl_delegate_to_helpers(self):
        map_status, map_calls = self.run_cli(
            ["site", "map", "--provider", "firecrawl", "https://docs.example.com", "--search", "auth", "--limit", "20"]
        )
        crawl_status, crawl_calls = self.run_cli(
            ["site", "crawl", "--provider", "firecrawl", "https://docs.example.com", "--include-paths", "/docs", "--limit", "10"]
        )

        self.assertEqual(map_status, 0)
        self.assertEqual(
            map_calls[0],
            [
                sys.executable,
                "skills/web-site/scripts/firecrawl_map.py",
                "https://docs.example.com",
                "--search",
                "auth",
                "--limit",
                "20",
            ],
        )
        self.assertEqual(crawl_status, 0)
        self.assertEqual(
            crawl_calls[0],
            [
                sys.executable,
                "skills/web-site/scripts/firecrawl_crawl.py",
                "https://docs.example.com",
                "--include-paths",
                "/docs",
                "--limit",
                "10",
            ],
        )

    def test_structured_extract_firecrawl_delegates_to_agent_helper(self):
        status, calls = self.run_cli(
            [
                "structured",
                "extract",
                "--provider",
                "firecrawl",
                "extract company pricing",
                "--urls",
                "https://example.com/pricing",
                "--schema",
                '{"type":"object"}',
                "--model",
                "spark-1-mini",
                "--max-credits",
                "5",
                "--wait",
                "--output",
                "json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-extract/scripts/firecrawl_agent.py",
                "extract company pricing",
                "--urls",
                "https://example.com/pricing",
                "--schema",
                '{"type":"object"}',
                "--model",
                "spark-1-mini",
                "--max-credits",
                "5",
                "--output",
                "json",
                "--wait",
            ],
        )

    def test_browser_firecrawl_run_delegates_to_browser_helper(self):
        status, calls = self.run_cli(
            [
                "browser",
                "run",
                "--provider",
                "firecrawl",
                "open https://example.com and snapshot",
                "--profile",
                "research",
                "--output",
                "json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-automation/scripts/firecrawl_browser.py",
                "open https://example.com and snapshot",
                "--profile",
                "research",
                "--output",
                "json",
            ],
        )

    def test_interact_firecrawl_run_delegates_to_interact_helper(self):
        status, calls = self.run_cli(
            [
                "interact",
                "run",
                "--provider",
                "firecrawl",
                "--scrape-id",
                "scrape_123",
                "--prompt",
                "click pricing",
                "--interaction-timeout",
                "45",
                "--output",
                "json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-automation/scripts/firecrawl_interact.py",
                "--scrape-id",
                "scrape_123",
                "--prompt",
                "click pricing",
                "--interaction-timeout",
                "45",
                "--output",
                "json",
            ],
        )

    def test_monitor_firecrawl_create_delegates_to_monitor_helper(self):
        status, calls = self.run_cli(
            [
                "monitor",
                "create",
                "--provider",
                "firecrawl",
                "--name",
                "Blog",
                "--schedule",
                "every 30 minutes",
                "--page",
                "https://example.com/blog",
                "--goal",
                "Alert when a new blog post is published.",
                "--output",
                "json",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-automation/scripts/firecrawl_monitor.py",
                "create",
                "--name",
                "Blog",
                "--schedule",
                "every 30 minutes",
                "--page",
                "https://example.com/blog",
                "--goal",
                "Alert when a new blog post is published.",
                "--output",
                "json",
            ],
        )

    def test_web_search_tavily_rejects_base_url_override_cleanly(self):
        with patch.object(
            sys,
            "argv",
            [
                "arkspace",
                "web",
                "search",
                "--provider",
                "tavily",
                "--base-url",
                "https://api.tavily.com",
                "agent skills",
            ],
        ):
            self.assertEqual(self.arkspace.main(), 2)

    def test_web_fetch_tavily_delegates_to_tavily_extract_helper(self):
        status, calls = self.run_cli(
            [
                "web",
                "fetch",
                "--provider",
                "tavily",
                "--timeout",
                "60",
                "--config-path",
                "/tmp/providers.json",
                "--state-path",
                "/tmp/state.json",
                "--output",
                "json",
                "https://example.com",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-fetch/scripts/tavily_extract.py",
                "https://example.com",
                "--timeout",
                "60",
                "--config-path",
                "/tmp/providers.json",
                "--state-path",
                "/tmp/state.json",
                "--output",
                "json",
            ],
        )

    def test_web_fetch_exa_delegates_to_exa_contents_helper(self):
        status, calls = self.run_cli(
            [
                "web",
                "fetch",
                "--provider",
                "exa",
                "--include-summary",
                "--include-highlights",
                "--text-max-characters",
                "1000",
                "--max-age-hours",
                "24",
                "--subpages",
                "2",
                "--subpage-target",
                "docs",
                "--include-links",
                "--timeout",
                "60",
                "--output",
                "json",
                "https://example.com",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-fetch/scripts/exa_contents.py",
                "https://example.com",
                "--text-max-characters",
                "1000",
                "--max-age-hours",
                "24",
                "--subpages",
                "2",
                "--subpage-target",
                "docs",
                "--timeout",
                "60",
                "--output",
                "json",
                "--include-summary",
                "--include-highlights",
                "--include-links",
            ],
        )

    def test_web_similar_exa_delegates_to_exa_similar_helper(self):
        status, calls = self.run_cli(
            [
                "web",
                "similar",
                "--provider",
                "exa",
                "--max-results",
                "4",
                "--search-type",
                "deep",
                "--include-domains",
                "github.com",
                "--include-summary",
                "--include-highlights",
                "--output",
                "json",
                "https://example.com",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-search/scripts/exa_similar.py",
                "https://example.com",
                "--max-results",
                "4",
                "--search-type",
                "deep",
                "--include-domains",
                "github.com",
                "--output",
                "json",
                "--include-highlights",
                "--include-summary",
            ],
        )

    def test_site_map_tavily_delegates_to_tavily_map_helper(self):
        status, calls = self.run_cli(
            [
                "site",
                "map",
                "--provider",
                "tavily",
                "--instructions",
                "Find auth docs",
                "--max-depth",
                "2",
                "--limit",
                "50",
                "--no-external",
                "--output",
                "json",
                "https://docs.example.com",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-site/scripts/tavily_map.py",
                "https://docs.example.com",
                "--instructions",
                "Find auth docs",
                "--max-depth",
                "2",
                "--limit",
                "50",
                "--output",
                "json",
                "--no-external",
            ],
        )

    def test_site_crawl_tavily_delegates_to_tavily_crawl_helper(self):
        status, calls = self.run_cli(
            [
                "site",
                "crawl",
                "--provider",
                "tavily",
                "--instructions",
                "Find auth docs",
                "--chunks-per-source",
                "3",
                "--extract-depth",
                "advanced",
                "--include-images",
                "--output",
                "json",
                "https://docs.example.com",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-site/scripts/tavily_crawl.py",
                "https://docs.example.com",
                "--instructions",
                "Find auth docs",
                "--chunks-per-source",
                "3",
                "--extract-depth",
                "advanced",
                "--output",
                "json",
                "--include-images",
            ],
        )

    def test_research_run_tavily_delegates_to_tavily_research_helper(self):
        status, calls = self.run_cli(
            [
                "research",
                "run",
                "--provider",
                "tavily",
                "--model",
                "pro",
                "--wait",
                "--timeout",
                "600",
                "--output",
                "json",
                "AI coding agents market",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-research/scripts/tavily_research.py",
                "AI coding agents market",
                "--model",
                "pro",
                "--timeout",
                "600",
                "--output",
                "json",
                "--wait",
            ],
        )

    def test_research_run_exa_delegates_to_exa_answer_helper(self):
        status, calls = self.run_cli(
            [
                "research",
                "run",
                "--provider",
                "exa",
                "--timeout",
                "60",
                "--output",
                "json",
                "AI coding agents market",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-research/scripts/exa_answer.py",
                "AI coding agents market",
                "--timeout",
                "60",
                "--output",
                "json",
            ],
        )

    def test_research_status_exa_fails_cleanly(self):
        with patch.object(
            sys,
            "argv",
            ["arkspace", "research", "status", "--provider", "exa", "req-123"],
        ):
            self.assertEqual(self.arkspace.main(), 2)

    def test_code_context_exa_delegates_to_exa_context_helper(self):
        status, calls = self.run_cli(
            [
                "code",
                "context",
                "--provider",
                "exa",
                "--tokens",
                "5000",
                "--timeout",
                "60",
                "--output",
                "json",
                "React hooks state management examples",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/code-context/scripts/exa_context.py",
                "React hooks state management examples",
                "--tokens",
                "5000",
                "--timeout",
                "60",
                "--output",
                "json",
            ],
        )

    def test_research_status_tavily_delegates_to_tavily_research_helper(self):
        status, calls = self.run_cli(
            [
                "research",
                "status",
                "--provider",
                "tavily",
                "--timeout",
                "60",
                "--output",
                "json",
                "req-123",
            ]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-research/scripts/tavily_research.py",
                "--status",
                "req-123",
                "--timeout",
                "60",
                "--output",
                "json",
            ],
        )

    def test_doctor_runs_gates_in_order_with_labels(self):
        expected_calls = [
            [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
            [sys.executable, "scripts/package-codex-plugin.py", "--check"],
            [sys.executable, "scripts/validate-skills.py"],
            [sys.executable, "scripts/convert-agents.py", "--host", "all", "--check"],
            [sys.executable, "scripts/smoke-test-callability.py", "--host", "codex", "--local"],
            [sys.executable, "scripts/smoke-test-callability.py", "--host", "claude-code", "--local"],
            [sys.executable, "scripts/smoke-test-orchestrator-routing.py"],
        ]
        expected_labels = [
            "[arkspace doctor] structure: unit tests",
            "[arkspace doctor] package: codex mirror",
            "[arkspace doctor] registry/docs: skill contract",
            "[arkspace doctor] integrations: generated agents",
            "[arkspace doctor] direct-invocation-contract: codex",
            "[arkspace doctor] direct-invocation-contract: claude-code",
            "[arkspace doctor] orchestrator-routing-contract: static",
            "[arkspace doctor] installed-host: unverified (run doctor --installed-host codex|claude-code|all)",
        ]
        output = io.StringIO()
        calls = []

        def fake_run(args):
            calls.append(args)
            return 0

        with patch.object(sys, "argv", ["arkspace", "doctor"]), patch.object(self.arkspace, "run", fake_run):
            with redirect_stdout(output):
                status = self.arkspace.main()

        self.assertEqual(status, 0)
        self.assertEqual(calls, expected_calls)
        self.assertEqual(output.getvalue().splitlines(), expected_labels)

    def test_smoke_test_installed_host_delegates_to_installed_cache_check(self):
        status, calls = self.run_cli(["smoke-test", "--installed-host", "codex"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "scripts/smoke-test-installed-host.py", "--host", "codex"],
        )

    # ------------------------------------------------------------------
    # Task 2: explicit provider-chain orchestration
    # ------------------------------------------------------------------

    def run_chain(self, argv, proc_results, error_records=None, policies=None):
        """Run a chain CLI invocation with mocked subprocess.run / error reader.

        ``proc_results`` may contain result objects (with .returncode/.stdout/
        .stderr) or an exception instance to raise. ``error_records`` are the
        per-provider values returned by ``read_error_file`` in order.
        """
        calls = []
        remaining_results = list(proc_results)
        remaining_records = (
            list(error_records) if error_records is not None else [None] * len(proc_results)
        )

        def fake_run(args, **kwargs):
            calls.append(args)
            if remaining_results:
                item = remaining_results.pop(0)
                if isinstance(item, BaseException):
                    raise item
                return item
            return SimpleNamespace(returncode=0, stdout=b"", stderr=b"")

        def fake_read(path):
            if remaining_records:
                return remaining_records.pop(0)
            return None

        def fake_policy(pid, config_path=None):
            if policies is not None:
                return list(policies.get(pid, ["quota", "network", "transient"]))
            return ["quota", "network", "transient"]

        stdout_buf = io.BytesIO()
        stderr_buf = io.StringIO()
        fake_stdout = SimpleNamespace(buffer=stdout_buf, write=stdout_buf.write)
        with patch.object(sys, "argv", ["arkspace", *argv]), \
            patch.object(self.arkspace.subprocess, "run", side_effect=fake_run), \
            patch.object(self.arkspace, "read_error_file", side_effect=fake_read), \
            patch.object(self.arkspace, "fallback_policy", side_effect=fake_policy), \
            patch("sys.stdout", fake_stdout), \
            patch("sys.stderr", stderr_buf):
            status = self.arkspace.main()
        return status, stdout_buf.getvalue(), stderr_buf.getvalue(), calls

    def test_web_search_no_provider_defaults_to_exa_mcp_helper(self):
        status, calls = self.run_cli(["web", "search", "query"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "skills/web-search/scripts/exa_mcp_search.py", "query"],
        )

    def test_web_search_explicit_single_provider_unchanged(self):
        status, calls = self.run_cli(["web", "search", "--provider", "exa", "query"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "skills/web-search/scripts/exa_search.py", "query"],
        )

    def test_web_search_explicit_single_provider_jina(self):
        status, calls = self.run_cli(
            ["web", "search", "--provider", "jina", "--max-results", "4", "--timeout", "20", "query"]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/web-search/scripts/jina_search.py",
                "query",
                "--max-results",
                "4",
                "--timeout",
                "20",
            ],
        )

    def test_web_search_explicit_single_provider_duckduckgo(self):
        status, calls = self.run_cli(["web", "search", "--provider", "duckduckgo", "query"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "skills/web-search/scripts/duckduckgo_search.py", "query"],
        )

    def test_web_search_explicit_chain_jina_duckduckgo_uses_public_args(self):
        jina_cmd = [
            sys.executable,
            "skills/web-search/scripts/jina_search.py",
            "query",
            "--max-results",
            "3",
            "--timeout",
            "15",
            "--output",
            "json",
        ]
        ddg_cmd = [
            sys.executable,
            "skills/web-search/scripts/duckduckgo_search.py",
            "query",
            "--max-results",
            "3",
            "--timeout",
            "15",
            "--output",
            "json",
        ]
        procs = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"e1"),
            SimpleNamespace(returncode=0, stdout=b'{"ok":true}', stderr=b""),
        ]
        records = [{"kind": "quota"}, None]
        status, out, err, calls = self.run_chain(
            [
                "web",
                "search",
                "--providers",
                "jina,duckduckgo",
                "--max-results",
                "3",
                "--timeout",
                "15",
                "--output",
                "json",
                "query",
            ],
            procs,
            records,
            policies={"jina": ["quota"]},
        )

        self.assertEqual(status, 0)
        self.assertEqual(calls, [jina_cmd, ddg_cmd])
        self.assertEqual(out, b'{"ok":true}')

    def test_web_search_chain_rejects_provider_only_flags_for_jina(self):
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "jina,duckduckgo", "--search-type", "neural", "q"],
            [],
            [],
        )
        self.assertEqual(status, 2)
        self.assertEqual(calls, [])
        self.assertIn("--search-type requires a single --provider", err)


    def test_web_search_chain_preserves_provider_order(self):
        exa_cmd = [sys.executable, "skills/web-search/scripts/exa_search.py", "query"]
        brave_cmd = [sys.executable, "skills/web-search/scripts/brave_search.py", "query"]
        jina_cmd = [sys.executable, "skills/web-search/scripts/jina_search.py", "query"]
        procs = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"e1"),
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"e2"),
            SimpleNamespace(returncode=0, stdout=b'{"ok":true}', stderr=b""),
        ]
        records = [{"kind": "quota"}, {"kind": "quota"}, None]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "exa,brave,jina", "query"],
            procs,
            records,
            policies={"exa": ["quota"], "brave": ["quota"]},
        )

        self.assertEqual(status, 0)
        self.assertEqual(calls, [exa_cmd, brave_cmd, jina_cmd])
        self.assertEqual(out, b'{"ok":true}')

    def test_web_search_chain_brave_uses_public_args(self):
        brave_cmd = [
            sys.executable,
            "skills/web-search/scripts/brave_search.py",
            "query",
            "--max-results",
            "3",
            "--timeout",
            "15",
            "--output",
            "json",
        ]
        jina_cmd = [
            sys.executable,
            "skills/web-search/scripts/jina_search.py",
            "query",
            "--max-results",
            "3",
            "--timeout",
            "15",
            "--output",
            "json",
        ]
        procs = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"e1"),
            SimpleNamespace(returncode=0, stdout=b'{"ok":true}', stderr=b""),
        ]
        records = [{"kind": "config"}, None]
        status, out, err, calls = self.run_chain(
            [
                "web",
                "search",
                "--providers",
                "brave,jina",
                "--max-results",
                "3",
                "--timeout",
                "15",
                "--output",
                "json",
                "query",
            ],
            procs,
            records,
        )

        self.assertEqual(status, 0)
        self.assertEqual(calls, [brave_cmd, jina_cmd])
        self.assertEqual(out, b'{"ok":true}')

    def test_chain_brave_config_skips_to_next_candidate(self):
        # A missing Brave key surfaces as a ``config`` failure; the explicit
        # chain must skip Brave and continue to the next candidate.
        brave_cmd = [sys.executable, "skills/web-search/scripts/brave_search.py", "query"]
        jina_cmd = [sys.executable, "skills/web-search/scripts/jina_search.py", "query"]
        procs = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"missing key"),
            SimpleNamespace(returncode=0, stdout=b'{"ok":true}', stderr=b""),
        ]
        records = [{"kind": "config"}, None]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "brave,jina", "query"], procs, records
        )

        self.assertEqual(status, 0)
        self.assertEqual(calls, [brave_cmd, jina_cmd])
        self.assertEqual(out, b'{"ok":true}')

    def test_chain_rejects_provider_only_flags_for_brave(self):
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "brave,jina", "--search-type", "neural", "q"],
            [],
            [],
        )
        self.assertEqual(status, 2)
        self.assertEqual(calls, [])
        self.assertIn("--search-type requires a single --provider", err)

    def test_provider_and_providers_are_mutually_exclusive(self):
        with self.assertRaises(SystemExit):
            with patch.object(
                sys,
                "argv",
                ["arkspace", "web", "search", "--provider", "exa", "--providers", "exa,tavily", "q"],
            ):
                self.arkspace.main()

    def test_empty_providers_uses_chain_validation_before_helper_execution(self):
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "", "query"], [], []
        )

        self.assertEqual(status, 2)
        self.assertEqual(out, b"")
        self.assertEqual(calls, [])
        self.assertIn("contains an empty provider id", err)

    def test_parse_provider_chain_rejects_empty_tokens(self):
        with self.assertRaises(self.arkspace.CliError):
            self.arkspace.parse_provider_chain("exa,,tavily")

    def test_parse_provider_chain_rejects_duplicates(self):
        with self.assertRaises(self.arkspace.CliError):
            self.arkspace.parse_provider_chain("exa,exa")

    def test_chain_unknown_provider_rejected_before_execution(self):
        status, calls = self.run_cli(["web", "search", "--providers", "exa,notreal", "q"])

        self.assertEqual(status, 2)
        self.assertEqual(calls, [])

    def test_chain_rejects_provider_only_flags(self):
        cases = [
            ["--search-type", "neural"],
            ["--category", "cs.CV"],
            ["--author", "Someone"],
            ["--base-url", "https://example.org"],
            ["--include-summary"],
            ["--freshness", "week"],
            ["--moderation"],
            ["--stream"],
        ]
        for flag_args in cases:
            flag = flag_args[0]
            with self.subTest(flag=flag):
                status, out, err, calls = self.run_chain(
                    ["web", "search", "--providers", "exa,tavily", *flag_args, "q"],
                    [],
                    [],
                )
                self.assertEqual(status, 2)
                self.assertEqual(calls, [])
                self.assertIn(
                    f"{flag} requires a single --provider; it cannot be used with --providers",
                    err,
                )

    def test_chain_first_success_emits_stdout_and_stops(self):
        procs = [SimpleNamespace(returncode=0, stdout=b'{"a":1}', stderr=b"")]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "exa,tavily", "query"], procs, [None]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls, [[sys.executable, "skills/web-search/scripts/exa_search.py", "query"]]
        )
        self.assertEqual(out, b'{"a":1}')

    def test_chain_config_skips_to_next_candidate(self):
        procs = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b""),
            SimpleNamespace(returncode=0, stdout=b'{"ok":true}', stderr=b""),
        ]
        records = [{"kind": "config"}, None]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "exa,tavily", "query"], procs, records
        )

        self.assertEqual(status, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(out, b'{"ok":true}')

    def test_chain_retryable_continues_only_if_in_policy(self):
        procs = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b""),
            SimpleNamespace(returncode=0, stdout=b"ok", stderr=b""),
        ]
        records = [{"kind": "quota"}, None]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "exa,tavily", "query"],
            procs,
            records,
            policies={"exa": ["quota"]},
        )

        self.assertEqual(status, 0)
        self.assertEqual(len(calls), 2)

    def test_chain_retryable_not_in_policy_stops(self):
        procs = [SimpleNamespace(returncode=1, stdout=b"", stderr=b"")]
        records = [{"kind": "quota"}]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "exa,tavily", "query"],
            procs,
            records,
            policies={"exa": []},
        )

        self.assertEqual(status, 1)
        self.assertEqual(len(calls), 1)
        self.assertIn("quota", err)

    def test_chain_terminal_kinds_stop(self):
        for kind in ["auth", "invalid-request", "invalid-response", "unknown"]:
            with self.subTest(kind=kind):
                procs = [SimpleNamespace(returncode=1, stdout=b"", stderr=b"")]
                records = [{"kind": kind}]
                status, out, err, calls = self.run_chain(
                    ["web", "search", "--providers", "exa,tavily", "query"],
                    procs,
                    records,
                )
                self.assertEqual(status, 1)
                self.assertEqual(len(calls), 1)
                self.assertIn(kind, err)

    def test_chain_absent_error_record_stops_conservatively(self):
        procs = [SimpleNamespace(returncode=1, stdout=b"", stderr=b"")]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "exa,tavily", "query"], procs, [None]
        )

        self.assertEqual(status, 1)
        self.assertEqual(len(calls), 1)
        self.assertEqual(out, b"")

    def test_chain_all_failures_redacted_summary_nonzero(self):
        procs = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"secret-token-here"),
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"other-secret"),
        ]
        records = [{"kind": "quota"}, {"kind": "unknown"}]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "exa,tavily", "query"],
            procs,
            records,
            policies={"exa": ["quota"]},
        )

        self.assertEqual(status, 1)
        self.assertEqual(out, b"")
        self.assertNotIn("secret-token-here", err)
        self.assertNotIn("other-secret", err)
        self.assertIn("web search", err)

    def test_chain_diagnostics_never_enter_stdout(self):
        procs = [
            SimpleNamespace(returncode=1, stdout=b"", stderr=b"err1"),
            SimpleNamespace(returncode=0, stdout=b'{"win":1}', stderr=b"err2"),
        ]
        records = [{"kind": "config"}, None]
        status, out, err, calls = self.run_chain(
            ["web", "search", "--providers", "exa,tavily", "query"], procs, records
        )

        self.assertEqual(status, 0)
        self.assertEqual(out, b'{"win":1}')
        self.assertNotIn(b"err1", out)

    def test_chain_temp_files_removed_after_success(self):
        created = []
        real_ntf = tempfile.NamedTemporaryFile

        def spy_ntf(*a, **k):
            f = real_ntf(*a, **k)
            created.append(f.name)
            return f

        with patch.object(self.arkspace.tempfile, "NamedTemporaryFile", side_effect=spy_ntf):
            status, out, err, calls = self.run_chain(
                ["web", "search", "--providers", "exa,tavily", "query"],
                [SimpleNamespace(returncode=0, stdout=b"x", stderr=b"")],
                [None],
            )

        self.assertEqual(status, 0)
        self.assertTrue(created)
        for path in created:
            self.assertFalse(os.path.exists(path))

    def test_chain_temp_files_removed_on_subprocess_exception(self):
        created = []
        real_ntf = tempfile.NamedTemporaryFile

        def spy_ntf(*a, **k):
            f = real_ntf(*a, **k)
            created.append(f.name)
            return f

        with patch.object(self.arkspace.tempfile, "NamedTemporaryFile", side_effect=spy_ntf):
            status, out, err, calls = self.run_chain(
                ["web", "search", "--providers", "exa,tavily", "query"],
                [OSError("boom")],
            )

        self.assertEqual(status, 1)
        self.assertTrue(created)
        for path in created:
            self.assertFalse(os.path.exists(path))

    def test_chain_real_error_file_lifecycle_config_continuation(self):
        """Real _make_error_file + real read_error_file must observe a real
        version-1 record written by the mocked child.

        Guards against the lifecycle bug where the temp file was unlinked in a
        ``finally`` before ``read_error_file`` ran, so every real failed
        candidate appeared as ``unknown`` and fallback never ran. Here a
        ``config`` record on the first candidate must skip to the second, which
        then succeeds; all temp files must be removed.
        """
        created = []
        real_ntf = tempfile.NamedTemporaryFile
        stdout_buf = io.BytesIO()
        stderr_buf = io.StringIO()
        fake_stdout = SimpleNamespace(buffer=stdout_buf, write=stdout_buf.write)
        calls = []
        count = [0]

        def spy_ntf(*a, **k):
            f = real_ntf(*a, **k)
            created.append(f.name)
            return f

        def fake_run(args, **kwargs):
            calls.append(args)
            env = kwargs.get("env", os.environ)
            count[0] += 1
            if count[0] == 1:
                _write_error_record(
                    env[self.arkspace.ERROR_FILE_ENV],
                    {
                        "version": 1,
                        "provider": "exa",
                        "capability": "web_search",
                        "kind": "config",
                        "message": "needs config",
                    },
                )
                return SimpleNamespace(returncode=1, stdout=b"", stderr=b"")
            return SimpleNamespace(returncode=0, stdout=b'{"ok":true}', stderr=b"")

        with patch.object(self.arkspace.tempfile, "NamedTemporaryFile", side_effect=spy_ntf), \
            patch.object(
                sys,
                "argv",
                ["arkspace", "web", "search", "--providers", "exa,tavily", "query"],
            ), \
            patch.object(self.arkspace.subprocess, "run", side_effect=fake_run), \
            patch("sys.stdout", fake_stdout), \
            patch("sys.stderr", stderr_buf):
            status = self.arkspace.main()

        self.assertEqual(status, 0)
        self.assertEqual(len(calls), 2)  # config skipped to the next candidate
        self.assertEqual(stdout_buf.getvalue(), b'{"ok":true}')
        self.assertIn("exa: skipped (config)", stderr_buf.getvalue())
        self.assertTrue(created)
        for path in created:
            self.assertFalse(os.path.exists(path))

    def test_chain_real_error_file_lifecycle_invalid_response_continuation(self):
        """An ``exa-mcp`` invalid response continues when its policy allows it.

        The fallback must preserve the winner's stdout bytes while reporting
        the prior candidate's retryable failure on stderr.
        """
        created = []
        real_ntf = tempfile.NamedTemporaryFile
        stdout_buf = io.BytesIO()
        stderr_buf = io.StringIO()
        fake_stdout = SimpleNamespace(buffer=stdout_buf, write=stdout_buf.write)
        calls = []
        count = [0]

        def spy_ntf(*a, **k):
            f = real_ntf(*a, **k)
            created.append(f.name)
            return f

        def fake_run(args, **kwargs):
            calls.append(args)
            env = kwargs.get("env", os.environ)
            count[0] += 1
            if count[0] == 1:
                _write_error_record(
                    env[self.arkspace.ERROR_FILE_ENV],
                    {
                        "version": 1,
                        "provider": "exa-mcp",
                        "capability": "web_search",
                        "kind": "invalid-response",
                        "message": "malformed MCP response",
                    },
                )
                return SimpleNamespace(returncode=1, stdout=b"", stderr=b"")
            return SimpleNamespace(returncode=0, stdout=b'{"win":1}', stderr=b"")

        def fake_policy(pid, config_path=None):
            return ["invalid-response"]

        with patch.object(self.arkspace.tempfile, "NamedTemporaryFile", side_effect=spy_ntf), \
            patch.object(
                sys,
                "argv",
                ["arkspace", "web", "search", "--providers", "exa-mcp,tavily", "query"],
            ), \
            patch.object(self.arkspace.subprocess, "run", side_effect=fake_run), \
            patch.object(self.arkspace, "fallback_policy", side_effect=fake_policy), \
            patch("sys.stdout", fake_stdout), \
            patch("sys.stderr", stderr_buf):
            status = self.arkspace.main()

        self.assertEqual(status, 0)
        self.assertEqual(len(calls), 2)
        self.assertEqual(stdout_buf.getvalue(), b'{"win":1}')
        self.assertIn(
            "exa-mcp: invalid-response; trying next provider", stderr_buf.getvalue()
        )
        self.assertTrue(created)
        for path in created:
            self.assertFalse(os.path.exists(path))


if __name__ == "__main__":
    unittest.main()
