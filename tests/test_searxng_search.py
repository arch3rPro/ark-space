"""Regression tests for SearXNG's structured provider-failure records."""

import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


def load_module():
    spec = importlib.util.spec_from_file_location(
        "searxng_search_test_module",
        ROOT / "skills" / "web-search" / "scripts" / "searxng_search.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SearxngFailureProtocolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m = load_module()

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.error_path = Path(self.tmp.name) / "error.json"
        self.error_env = patch.dict(os.environ, {"ARKSPACE_ERROR_FILE": str(self.error_path)})
        self.error_env.start()
        self.addCleanup(self.error_env.stop)

    def _record(self):
        return json.loads(self.error_path.read_text(encoding="utf-8"))

    def test_missing_configuration_writes_config_error_record(self):
        with patch.object(sys, "argv", ["searxng_search.py", "query"]), patch.object(
            self.m,
            "resolve_base_url",
            side_effect=self.m.ProviderConfigError("missing endpoint"),
        ), patch("sys.stderr", new=io.StringIO()):
            status = self.m.main()

        self.assertEqual(status, 2)
        record = self._record()
        self.assertEqual(record["provider"], "searxng")
        self.assertEqual(record["capability"], "web_search")
        self.assertEqual(record["kind"], "config")
        self.assertNotIn("status", record)

    def test_network_failure_writes_network_error_record(self):
        with patch.object(sys, "argv", ["searxng_search.py", "query"]), patch.object(
            self.m,
            "resolve_base_url",
            return_value=("https://searx.example", "test"),
        ), patch.object(
            self.m,
            "search_instance",
            side_effect=urllib.error.URLError("connection refused"),
        ), patch("sys.stderr", new=io.StringIO()):
            status = self.m.main()

        self.assertEqual(status, 1)
        record = self._record()
        self.assertEqual(record["provider"], "searxng")
        self.assertEqual(record["capability"], "web_search")
        self.assertEqual(record["kind"], "network")
        self.assertNotIn("status", record)


if __name__ == "__main__":
    unittest.main()
