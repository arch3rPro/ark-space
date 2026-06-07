import importlib.util
import sys
import unittest
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


if __name__ == "__main__":
    unittest.main()
