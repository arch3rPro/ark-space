import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]

ADAPTERS = {
    "scrape": {
        "path": "skills/web-fetch/scripts/firecrawl_scrape.py",
        "capability": "web_fetch",
        "run": "run_scrape",
        "kwargs": {
            "urls": ["https://example.com", "https://example.com/docs"],
            "formats": "markdown,links",
            "only_main_content": True,
            "query": "pricing",
            "wait_for": 250,
            "timeout": 45,
            "config_path": "providers.json",
            "state_path": "state.json",
        },
        "command": [
            "scrape", "https://example.com", "https://example.com/docs", "--json",
            "--format", "markdown,links", "--only-main-content", "--query", "pricing", "--wait-for", "250",
        ],
        "envelope": {"provider": "firecrawl", "capability": "web_fetch", "urls": ["https://example.com", "https://example.com/docs"]},
        "argv": [
            "https://example.com", "https://example.com/docs", "--format", "markdown,links", "--only-main-content",
            "--query", "pricing", "--wait-for", "250", "--timeout", "45", "--output", "json",
        ],
    },
    "map": {
        "path": "skills/web-site/scripts/firecrawl_map.py",
        "capability": "web_map",
        "run": "run_map",
        "kwargs": {"url": "https://docs.example.com", "search": "authentication", "limit": 20, "timeout": 45, "config_path": "providers.json", "state_path": "state.json"},
        "command": ["map", "https://docs.example.com", "--json", "--search", "authentication", "--limit", "20"],
        "envelope": {"provider": "firecrawl", "capability": "web_map", "url": "https://docs.example.com"},
        "argv": ["https://docs.example.com", "--search", "authentication", "--limit", "20", "--timeout", "45", "--output", "json"],
    },
    "crawl": {
        "path": "skills/web-site/scripts/firecrawl_crawl.py",
        "capability": "web_crawl",
        "run": "run_crawl",
        "kwargs": {"url": "https://docs.example.com", "include_paths": "/docs", "exclude_paths": "/blog", "max_depth": 3, "limit": 20, "timeout": 210, "config_path": "providers.json", "state_path": "state.json"},
        "command": ["crawl", "https://docs.example.com", "--wait", "--json", "--include-paths", "/docs", "--exclude-paths", "/blog", "--max-depth", "3", "--limit", "20"],
        "envelope": {"provider": "firecrawl", "capability": "web_crawl", "url": "https://docs.example.com"},
        "argv": ["https://docs.example.com", "--include-paths", "/docs", "--exclude-paths", "/blog", "--max-depth", "3", "--limit", "20", "--timeout", "210", "--output", "json"],
    },
    "browser": {
        "path": "skills/web-automation/scripts/firecrawl_browser.py",
        "capability": "web_interact",
        "run": "run_browser",
        "kwargs": {"instruction": "open the pricing page", "profile": "research", "save_changes": False, "timeout": 210, "config_path": "providers.json", "state_path": "state.json"},
        "command": ["browser", "open the pricing page", "--json", "--profile", "research", "--no-save-changes"],
        "envelope": {"provider": "firecrawl", "capability": "web_interact", "mode": "browser", "instruction": "open the pricing page"},
        "argv": ["open the pricing page", "--profile", "research", "--no-save-changes", "--timeout", "210", "--output", "json"],
    },
    "monitor": {
        "path": "skills/web-automation/scripts/firecrawl_monitor.py",
        "capability": "web_monitor",
        "run": "run_monitor",
        "kwargs": None,
        "command": ["monitor", "create", "--name", "Docs", "--schedule", "every 30 minutes", "--page", "https://example.com/docs", "--goal", "alert on changes", "--limit", "10"],
        "envelope": {"provider": "firecrawl", "capability": "web_monitor", "action": "create"},
        "argv": ["create", "--name", "Docs", "--schedule", "every 30 minutes", "--page", "https://example.com/docs", "--goal", "alert on changes", "--limit", "10", "--timeout", "210", "--output", "json"],
    },
}


class FirecrawlAdapterTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)

    def load_adapter(self, name):
        spec = importlib.util.spec_from_file_location(
            f"firecrawl_{name}_adapter_test", ROOT / ADAPTERS[name]["path"]
        )
        if spec is None or spec.loader is None:
            self.fail(f"could not load {name} adapter")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _monitor_args(self, module):
        return module.argparse.Namespace(
            monitor_action="create", monitor_id=None, check_id=None, file=None,
            name="Docs", cron=None, schedule="every 30 minutes", timezone=None,
            page="https://example.com/docs", scrape_urls=None, crawl_url=None,
            webhook_url=None, webhook_events=None, email=None, retention_days=None,
            goal="alert on changes", state=None, limit=10, offset=None, skip=None,
            page_status=None, pretty=False, timeout=210, config_path="providers.json",
            state_path="state.json",
        )

    def test_adapters_delegate_exact_commands_and_preserve_success_envelopes(self):
        response = {"data": ["result"]}
        for name, expected in ADAPTERS.items():
            with self.subTest(adapter=name):
                module = self.load_adapter(name)
                with patch.object(module.firecrawl_cli, "run_capability_command", return_value=response) as run, \
                     patch.object(module.firecrawl_cli, "resolve_firecrawl", return_value={}), \
                     patch.object(module.firecrawl_cli, "run_cli", return_value='{"unused": true}'), \
                     patch.object(module.firecrawl_cli, "parse_json_or_text", return_value={"unused": True}):
                    if name == "monitor":
                        result = module.run_monitor(self._monitor_args(module))
                    else:
                        result = getattr(module, expected["run"])(**expected["kwargs"])

                run.assert_called_once_with(
                    expected["capability"], expected["command"], timeout=expected["kwargs"]["timeout"] if name != "monitor" else 210,
                    config_path="providers.json", state_path="state.json",
                )
                self.assertEqual({key: result[key] for key in expected["envelope"]}, expected["envelope"])
                self.assertEqual(result["response"], response)
                self.assertNotIn("ok", result)

    def test_main_success_json_contract_remains_unwrapped(self):
        response = {"data": ["result"]}
        for name, expected in ADAPTERS.items():
            with self.subTest(adapter=name):
                module = self.load_adapter(name)
                with patch.object(module.firecrawl_cli, "run_capability_command", return_value=response), \
                     patch.object(module.firecrawl_cli, "resolve_firecrawl", return_value={}), \
                     patch.object(module.firecrawl_cli, "run_cli", return_value='{"unused": true}'), \
                     patch.object(module.firecrawl_cli, "parse_json_or_text", return_value={"unused": True}), \
                     patch.object(sys, "argv", ["prog", *expected["argv"]]):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        rc = module.main()

                self.assertEqual(rc, 0)
                self.assertEqual(stderr.getvalue(), "")
                result = json.loads(stdout.getvalue())
                self.assertEqual({key: result[key] for key in expected["envelope"]}, expected["envelope"])
                self.assertEqual(result["response"], response)
                self.assertNotIn("ok", result)

    def test_main_hides_provider_supplied_configured_secret_from_stderr(self):
        secret = "fc_adapter_test_secret_0123456789"
        config_path = str(Path(self.tmpdir.name) / "providers.json")
        state_path = str(Path(self.tmpdir.name) / "state.json")
        os.environ["FIRECRAWL_ADAPTER_TEST_KEY"] = secret
        self.addCleanup(os.environ.pop, "FIRECRAWL_ADAPTER_TEST_KEY", None)

        for name, expected in ADAPTERS.items():
            with self.subTest(adapter=name):
                module = self.load_adapter(name)
                module.provider_config.set_provider_endpoint(
                    "firecrawl",
                    capability=expected["capability"],
                    capabilities=[expected["capability"]],
                    base_url="https://api.firecrawl.dev",
                    config_path=config_path,
                )
                module.provider_config.add_key_ref(
                    "firecrawl",
                    key_ref="env:FIRECRAWL_ADAPTER_TEST_KEY",
                    auth_header="x-api-key",
                    auth_prefix="",
                    config_path=config_path,
                )
                error_path = Path(self.tmpdir.name) / f"{name}-secret.json"
                provider_message = f"HTTP 429 provider rejected token {secret}"
                with patch.dict(os.environ, {"ARKSPACE_ERROR_FILE": str(error_path)}, clear=False), \
                     patch.object(
                         module.firecrawl_cli,
                         "run_capability_command",
                         side_effect=module.firecrawl_cli.FirecrawlCliError(provider_message, status=429),
                     ), \
                     patch.object(sys, "argv", [
                         "prog", *expected["argv"], "--config-path", config_path, "--state-path", state_path,
                     ]):
                    stdout, stderr = io.StringIO(), io.StringIO()
                    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                        rc = module.main()

                self.assertEqual(rc, 2)
                self.assertEqual(stdout.getvalue(), "")
                self.assertIn("HTTP 429", stderr.getvalue())
                self.assertNotIn(secret, stderr.getvalue())
                self.assertNotIn("Traceback", stderr.getvalue())
                self.assertNotIn(secret, json.loads(error_path.read_text(encoding="utf-8"))["message"])

    def test_main_writes_typed_records_for_controlled_failures(self):
        failures = (
            ("config", "missing configuration", lambda module: module.provider_config.ProviderConfigError("missing configuration")),
            ("quota", "HTTP 429 rate limited", lambda module: module.firecrawl_cli.FirecrawlCliError("HTTP 429 rate limited", status=429)),
            ("network", "connection timed out", lambda module: module.firecrawl_cli.FirecrawlCliError("connection timed out")),
            ("invalid-response", "received invalid JSON body", lambda module: module.firecrawl_cli.FirecrawlCliError("received invalid JSON body", status=200)),
        )
        for name, expected in ADAPTERS.items():
            for kind, message, make_exception in failures:
                with self.subTest(adapter=name, kind=kind):
                    module = self.load_adapter(name)
                    error_path = Path(self.tmpdir.name) / f"{name}-{kind}.json"
                    with patch.dict(os.environ, {"ARKSPACE_ERROR_FILE": str(error_path)}, clear=False), \
                         patch.object(module.firecrawl_cli, "run_capability_command", side_effect=make_exception(module)) as run, \
                         patch.object(module.firecrawl_cli, "resolve_firecrawl", side_effect=module.provider_config.ProviderConfigError("legacy resolution should not run")), \
                         patch.object(sys, "argv", ["prog", *expected["argv"]]):
                        stdout, stderr = io.StringIO(), io.StringIO()
                        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                            rc = module.main()

                    self.assertEqual(rc, 2)
                    self.assertEqual(stdout.getvalue(), "")
                    self.assertIn(message, stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())
                    self.assertEqual(run.call_count, 1)
                    record = json.loads(error_path.read_text(encoding="utf-8"))
                    self.assertEqual(record["version"], 1)
                    self.assertEqual(record["provider"], "firecrawl")
                    self.assertEqual(record["capability"], expected["capability"])
                    self.assertEqual(record["kind"], kind)

    def test_agent_delegates_job_lifecycle_command_to_shared_helper(self):
        agent_path = ROOT / "skills/web-extract/scripts/firecrawl_agent.py"
        spec = importlib.util.spec_from_file_location("firecrawl_agent_adapter_test", agent_path)
        if spec is None or spec.loader is None:
            self.fail("could not load firecrawl agent adapter")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        response = {"jobId": "job_123", "status": "completed"}
        command = [
            "agent", "extract pricing", "--json", "--urls", "https://example.com/pricing",
            "--schema", '{"type":"object"}', "--schema-file", "schema.json", "--model", "spark-1-mini",
            "--max-credits", "5", "--webhook", "https://example.com/hook", "--poll-interval", "1.5",
            "--timeout", "30.0", "--status", "--cancel", "--wait",
        ]
        with patch.object(module.firecrawl_cli, "run_capability_command", return_value=response) as run, \
             patch.object(module.firecrawl_cli, "resolve_firecrawl", side_effect=AssertionError("legacy resolution should not run")), \
             patch.object(module.firecrawl_cli, "run_cli", side_effect=AssertionError("legacy execution should not run")):
            result = module.run_agent(
                "extract pricing",
                urls="https://example.com/pricing",
                schema='{"type":"object"}',
                schema_file="schema.json",
                model="spark-1-mini",
                max_credits=5,
                webhook="https://example.com/hook",
                status=True,
                cancel=True,
                wait=True,
                poll_interval=1.5,
                timeout=30.0,
                run_timeout=240,
                config_path="providers.json",
                state_path="state.json",
            )

        run.assert_called_once_with(
            "structured_extract", command, timeout=240, config_path="providers.json", state_path="state.json"
        )
        self.assertEqual(result, {
            "provider": "firecrawl",
            "capability": "structured_extract",
            "prompt": "extract pricing",
            "response": response,
        })


if __name__ == "__main__":
    unittest.main()
