import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = ROOT / "skills" / "provider-manager" / "scripts"


class FirecrawlCliTests(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(RUNTIME_ROOT))
        self.firecrawl_cli = importlib.import_module("arkspace_runtime.firecrawl_cli")

    def tearDown(self):
        try:
            sys.path.remove(str(RUNTIME_ROOT))
        except ValueError:
            pass

    def test_custom_firecrawl_cli_uses_shell_like_quoting(self):
        with patch.dict(os.environ, {"FIRECRAWL_CLI": '"/tmp/Firecrawl CLI" --profile "team research"'}, clear=False):
            self.assertEqual(
                self.firecrawl_cli.cli_command(),
                ["/tmp/Firecrawl CLI", "--profile", "team research"],
            )

    def test_firecrawl_cli_prefers_installed_binary_before_npx(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            self.firecrawl_cli.shutil,
            "which",
            side_effect=lambda name: "/usr/local/bin/firecrawl" if name == "firecrawl" else "/usr/local/bin/npx",
        ):
            self.assertEqual(self.firecrawl_cli.cli_command(), ["firecrawl"])

    def test_firecrawl_cli_uses_npx_when_binary_is_missing(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(
            self.firecrawl_cli.shutil,
            "which",
            side_effect=lambda name: "/usr/local/bin/npx" if name == "npx" else None,
        ):
            self.assertEqual(self.firecrawl_cli.cli_command(), ["npx", "-y", "firecrawl-cli@latest"])

    def test_firecrawl_cli_extracts_http_status_from_error_message(self):
        self.assertEqual(self.firecrawl_cli.http_status_from_message("request failed with 429 rate limited"), 429)
        self.assertEqual(self.firecrawl_cli.http_status_from_message("HTTP 500 from upstream"), 500)
        self.assertIsNone(self.firecrawl_cli.http_status_from_message("invalid CLI argument"))


if __name__ == "__main__":
    unittest.main()
