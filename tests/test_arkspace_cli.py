import importlib.util
import io
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_arkspace_module():
    spec = importlib.util.spec_from_file_location("arkspace_cli_test_module", ROOT / "scripts" / "arkspace.py")
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
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
            [sys.executable, "skills/tavily-search/scripts/tavily_search.py", "--check"],
        )

    def test_provider_check_tavily_fetch_delegates_to_extract_check(self):
        status, calls = self.run_cli(["provider", "check", "tavily", "--capability", "web_fetch"])

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [sys.executable, "skills/tavily-extract/scripts/tavily_extract.py", "--check"],
        )

    def test_provider_check_tavily_extended_capabilities_delegate_to_helpers(self):
        expectations = {
            "web_map": [sys.executable, "skills/tavily-map/scripts/tavily_map.py", "--check"],
            "web_crawl": [sys.executable, "skills/tavily-crawl/scripts/tavily_crawl.py", "--check"],
            "deep_research": [sys.executable, "skills/tavily-research/scripts/tavily_research.py", "--check"],
        }
        for capability, expected in expectations.items():
            with self.subTest(capability=capability):
                status, calls = self.run_cli(["provider", "check", "tavily", "--capability", capability])
                self.assertEqual(status, 0)
                self.assertEqual(calls[0], expected)

    def test_provider_check_exa_capabilities_delegate_to_helpers(self):
        expectations = {
            "web_search": [sys.executable, "skills/exa-search/scripts/exa_search.py", "--check"],
            "web_fetch": [sys.executable, "skills/exa-contents/scripts/exa_contents.py", "--check"],
            "deep_research": [sys.executable, "skills/exa-answer/scripts/exa_answer.py", "--check"],
            "code_context": [sys.executable, "skills/exa-context/scripts/exa_context.py", "--check"],
            "related_pages": [sys.executable, "skills/exa-similar/scripts/exa_similar.py", "--check"],
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

    def test_web_search_tavily_delegates_to_tavily_search_helper(self):
        status, calls = self.run_cli(
            ["web", "search", "--provider", "tavily", "--max-results", "3", "--output", "json", "agent skills"]
        )

        self.assertEqual(status, 0)
        self.assertEqual(
            calls[0],
            [
                sys.executable,
                "skills/tavily-search/scripts/tavily_search.py",
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
                "skills/searxng-search/scripts/searxng_search.py",
                "agent skills",
                "--base-url",
                "https://searx.example.org",
                "--limit",
                "3",
            ],
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
                "skills/exa-search/scripts/exa_search.py",
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
                "skills/tavily-extract/scripts/tavily_extract.py",
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
                "skills/exa-contents/scripts/exa_contents.py",
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
                "skills/exa-similar/scripts/exa_similar.py",
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
                "skills/tavily-map/scripts/tavily_map.py",
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
                "skills/tavily-crawl/scripts/tavily_crawl.py",
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
                "skills/tavily-research/scripts/tavily_research.py",
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
                "skills/exa-answer/scripts/exa_answer.py",
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
                "skills/exa-context/scripts/exa_context.py",
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
                "skills/tavily-research/scripts/tavily_research.py",
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
            "[arkspace doctor] installed-host: unverified (run smoke-test --installed-host codex|claude-code)",
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


if __name__ == "__main__":
    unittest.main()
