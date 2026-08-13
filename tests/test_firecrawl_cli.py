import contextlib
import importlib
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

    def test_run_capability_command_resolves_runs_and_parses_once(self):
        resolved = {"provider": "firecrawl"}
        payload = {"links": ["https://example.com/about"]}
        command = ["map", "https://example.com", "--json"]
        with patch.object(self.firecrawl_cli, "resolve_firecrawl", return_value=resolved) as resolve, patch.object(
            self.firecrawl_cli, "run_cli", return_value='{"links": ["https://example.com/about"]}'
        ) as run, patch.object(self.firecrawl_cli, "parse_json_or_text", return_value=payload) as parse:
            result = self.firecrawl_cli.run_capability_command(
                "web_map", command, timeout=90, config_path="providers.json", state_path="state.json"
            )

        self.assertEqual(result, payload)
        resolve.assert_called_once_with(
            capability="web_map", config_path="providers.json", state_path="state.json"
        )
        run.assert_called_once_with(
            resolved, command, timeout=90, config_path="providers.json", state_path="state.json"
        )
        parse.assert_called_once_with('{"links": ["https://example.com/about"]}')

    def test_run_capability_command_preserves_text_payload(self):
        with patch.object(self.firecrawl_cli, "resolve_firecrawl", return_value={"provider": "firecrawl"}), patch.object(
            self.firecrawl_cli, "run_cli", return_value="plain text response"
        ), patch.object(self.firecrawl_cli, "parse_json_or_text", return_value="plain text response") as parse:
            result = self.firecrawl_cli.run_capability_command("web_fetch", ["scrape", "https://example.com"], timeout=30)

        self.assertEqual(result, "plain text response")
        parse.assert_called_once_with("plain text response")

    def test_classify_exception_uses_existing_failure_taxonomy(self):
        cases = (
            (self.firecrawl_cli.provider_config.ProviderConfigError("missing config"), ("config", None)),
            (self.firecrawl_cli.FirecrawlCliError("rate limited", status=429), ("quota", 429)),
            (self.firecrawl_cli.FirecrawlCliError("received invalid JSON body", status=200), ("invalid-response", 200)),
            (self.firecrawl_cli.FirecrawlCliError("connection timed out"), ("network", None)),
        )

        for exc, expected in cases:
            with self.subTest(exc=exc):
                self.assertEqual(self.firecrawl_cli.classify_exception(exc), expected)


class FirecrawlSearchErrorTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.config_path = str(Path(self.tmpdir.name) / "providers.json")
        self.state_path = str(Path(self.tmpdir.name) / "state.json")
        self.secrets_path = str(Path(self.tmpdir.name) / "secrets.json")
        os.environ["ARKSPACE_PROVIDER_SECRETS"] = self.secrets_path
        self.addCleanup(os.environ.pop, "ARKSPACE_PROVIDER_SECRETS", None)
        spec = importlib.util.spec_from_file_location(
            "firecrawl_search_test_module",
            ROOT / "skills" / "web-search" / "scripts" / "firecrawl_search.py",
        )
        if spec is None or spec.loader is None:
            raise RuntimeError("could not load firecrawl_search module")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.search = module

    def _configure(self):
        os.environ["FIRECRAWL_API_KEY_TEST"] = "fc-test-key"
        self.addCleanup(os.environ.pop, "FIRECRAWL_API_KEY_TEST", None)
        self.search.provider_config.set_provider_endpoint(
            "firecrawl",
            capability="web_search",
            capabilities=["web_search"],
            base_url="https://api.firecrawl.dev",
            config_path=self.config_path,
        )
        self.search.provider_config.add_key_ref(
            "firecrawl",
            key_ref="env:FIRECRAWL_API_KEY_TEST",
            auth_header="x-api-key",
            auth_prefix="",
            config_path=self.config_path,
        )

    def _run_main(self, argv, run_cli):
        old_argv = sys.argv
        sys.argv = ["prog"] + argv
        try:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch.object(self.search.firecrawl_cli, "run_cli", run_cli):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    rc = self.search.main()
            return rc, stdout.getvalue(), stderr.getvalue()
        finally:
            sys.argv = old_argv

    def _error_file(self):
        path = str(Path(self.tmpdir.name) / "err.json")
        os.environ["ARKSPACE_ERROR_FILE"] = path
        self.addCleanup(os.environ.pop, "ARKSPACE_ERROR_FILE", None)
        return path

    def test_main_success_json_shape_unchanged(self):
        self._configure()
        errfile = self._error_file()

        def ok_run(resolved, command, **kwargs):
            return json.dumps({"results": [{"title": "R", "url": "https://f.com"}]})

        rc, out, err = self._run_main(
            ["agent skills", "--output", "json", "--config-path", self.config_path, "--state-path", self.state_path],
            ok_run,
        )

        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertEqual(data["provider"], "firecrawl")
        self.assertEqual(data["capability"], "web_search")
        self.assertNotIn("ok", data)  # results are not wrapped in an envelope
        self.assertFalse(os.path.exists(errfile))  # success writes no error record

    def test_main_config_failure_writes_config_error_record(self):
        # web_search is keyless, so "not configured" no longer fails. Use a
        # config that does not support web_search to exercise the config-failure
        # emission path (which still matters for the key-required capabilities).
        self.search.provider_config.set_provider_endpoint(
            "firecrawl",
            capability="web_fetch",
            capabilities=["web_fetch"],
            base_url="https://api.firecrawl.dev",
            config_path=self.config_path,
        )
        errfile = self._error_file()

        def no_run(resolved, command, **kwargs):
            raise AssertionError("no request expected")

        rc, _out, err = self._run_main(["agent skills", "--config-path", self.config_path], no_run)

        self.assertEqual(rc, 2)
        self.assertIn("does not support capability web_search", err)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["version"], 1)
        self.assertEqual(record["provider"], "firecrawl")
        self.assertEqual(record["capability"], "web_search")
        self.assertEqual(record["kind"], "config")

    def test_main_http_429_writes_quota_error_record(self):
        self._configure()
        errfile = self._error_file()

        def fail(resolved, command, **kwargs):
            raise self.search.firecrawl_cli.FirecrawlCliError("HTTP 429 rate limited", status=429)

        rc, _out, err = self._run_main(
            ["agent skills", "--config-path", self.config_path, "--state-path", self.state_path],
            fail,
        )

        self.assertEqual(rc, 2)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["kind"], "quota")
        self.assertEqual(record["status"], 429)

    def test_main_connection_failure_writes_network_error_record(self):
        self._configure()
        errfile = self._error_file()

        def fail(resolved, command, **kwargs):
            raise self.search.firecrawl_cli.FirecrawlCliError("connection timed out")

        rc, _out, err = self._run_main(
            ["agent skills", "--config-path", self.config_path, "--state-path", self.state_path],
            fail,
        )

        self.assertEqual(rc, 2)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["kind"], "network")
        self.assertNotIn("status", record)

    def test_main_malformed_body_writes_invalid_response_error_record(self):
        self._configure()
        errfile = self._error_file()

        def fail(resolved, command, **kwargs):
            raise self.search.firecrawl_cli.FirecrawlCliError("received invalid JSON body", status=200)

        rc, _out, err = self._run_main(
            ["agent skills", "--config-path", self.config_path, "--state-path", self.state_path],
            fail,
        )

        self.assertEqual(rc, 2)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["kind"], "invalid-response")

    def test_main_without_error_file_preserves_stderr_and_exit(self):
        self._configure()
        os.environ.pop("ARKSPACE_ERROR_FILE", None)

        def fail(resolved, command, **kwargs):
            raise self.search.firecrawl_cli.FirecrawlCliError("HTTP 429 rate limited", status=429)

        rc, _out, err = self._run_main(
            ["agent skills", "--config-path", self.config_path, "--state-path", self.state_path],
            fail,
        )

        self.assertEqual(rc, 2)
        self.assertIn("HTTP 429", err)


class FirecrawlKeylessTests(unittest.TestCase):
    """Keyless Firecrawl access for the official web_search / web_fetch capabilities.

    The official Firecrawl CLI supports keyless search and scrape, so those two
    capabilities must resolve (and run) without any provider config or key. Every
    other Firecrawl capability stays key-required. Keyed mode must keep working
    with credential selection and rotation state unchanged.
    """

    KEYLESS = {"web_search", "web_fetch"}
    KEY_REQUIRED = {"web_map", "web_crawl", "structured_extract", "web_interact", "web_monitor"}

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.config_path = str(Path(self.tmpdir.name) / "providers.json")
        self.state_path = str(Path(self.tmpdir.name) / "state.json")
        self.secrets_path = str(Path(self.tmpdir.name) / "secrets.json")
        os.environ["ARKSPACE_PROVIDER_SECRETS"] = self.secrets_path
        self.addCleanup(os.environ.pop, "ARKSPACE_PROVIDER_SECRETS", None)
        sys.path.insert(0, str(RUNTIME_ROOT))
        self.firecrawl_cli = importlib.import_module("arkspace_runtime.firecrawl_cli")
        self.provider_config = self.firecrawl_cli.provider_config

    def tearDown(self):
        try:
            sys.path.remove(str(RUNTIME_ROOT))
        except ValueError:
            pass

    def _load_script(self, rel):
        name = "fc_" + Path(rel).stem.replace(".", "_")
        spec = importlib.util.spec_from_file_location(name, ROOT / rel)
        if spec is None or spec.loader is None:
            raise RuntimeError(f"could not load {rel}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def _run_main(self, module, argv, run_cli):
        old_argv = sys.argv
        sys.argv = ["prog"] + argv
        try:
            stdout = io.StringIO()
            stderr = io.StringIO()
            with patch.object(module.firecrawl_cli, "run_cli", run_cli):
                with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                    rc = module.main()
            return rc, stdout.getvalue(), stderr.getvalue()
        finally:
            sys.argv = old_argv

    def _error_file(self):
        path = str(Path(self.tmpdir.name) / "err.json")
        os.environ["ARKSPACE_ERROR_FILE"] = path
        self.addCleanup(os.environ.pop, "ARKSPACE_ERROR_FILE", None)
        return path

    # -- Step 1: keyless capability resolution ---------------------------------

    def test_keyless_web_search_resolves_without_config(self):
        resolved = self.firecrawl_cli.resolve_firecrawl(
            capability="web_search", config_path=self.config_path, state_path=self.state_path
        )
        self.assertEqual(resolved["capability"], "web_search")
        self.assertEqual(resolved["endpoint"]["base_url"], "https://api.firecrawl.dev")
        self.assertEqual(resolved["auth"], {"type": "none"})
        self.assertNotIn("value", resolved["auth"])

    def test_keyless_web_fetch_resolves_without_config(self):
        resolved = self.firecrawl_cli.resolve_firecrawl(
            capability="web_fetch", config_path=self.config_path, state_path=self.state_path
        )
        self.assertEqual(resolved["capability"], "web_fetch")
        self.assertEqual(resolved["endpoint"]["base_url"], "https://api.firecrawl.dev")
        self.assertEqual(resolved["auth"], {"type": "none"})

    def test_key_required_capabilities_fail_without_config(self):
        for capability in sorted(self.KEY_REQUIRED):
            with self.subTest(capability=capability):
                with self.assertRaises(self.provider_config.ProviderConfigError):
                    self.firecrawl_cli.resolve_firecrawl(
                        capability=capability, config_path=self.config_path, state_path=self.state_path
                    )

    # -- Step 2: env_for -------------------------------------------------------

    def test_env_for_keyless_does_not_insert_api_key(self):
        resolved = self.firecrawl_cli.resolve_firecrawl(
            capability="web_search", config_path=self.config_path, state_path=self.state_path
        )
        env = self.firecrawl_cli.env_for(resolved)
        self.assertNotIn("FIRECRAWL_API_KEY", env)

    def test_env_for_keyless_inherits_normal_environment(self):
        os.environ["ARKSPACE_TEST_INHERITED"] = "yes"
        self.addCleanup(os.environ.pop, "ARKSPACE_TEST_INHERITED", None)
        resolved = self.firecrawl_cli.resolve_firecrawl(
            capability="web_search", config_path=self.config_path, state_path=self.state_path
        )
        env = self.firecrawl_cli.env_for(resolved)
        self.assertEqual(env["ARKSPACE_TEST_INHERITED"], "yes")

    def test_env_for_preserves_configured_api_url(self):
        self.provider_config.set_provider_endpoint(
            "firecrawl",
            capability="web_search",
            capabilities=["web_search"],
            base_url="https://fc.example.com",
            config_path=self.config_path,
        )
        resolved = self.firecrawl_cli.resolve_firecrawl(
            capability="web_search", config_path=self.config_path, state_path=self.state_path
        )
        env = self.firecrawl_cli.env_for(resolved)
        self.assertEqual(env["FIRECRAWL_API_URL"], "https://fc.example.com")
        self.assertNotIn("FIRECRAWL_API_KEY", env)

    def test_env_for_keyed_inserts_selected_credential(self):
        os.environ["FIRECRAWL_API_KEY_TEST"] = "fc-test-key"
        self.addCleanup(os.environ.pop, "FIRECRAWL_API_KEY_TEST", None)
        self.provider_config.set_provider_endpoint(
            "firecrawl",
            capability="web_search",
            capabilities=["web_search"],
            base_url="https://api.firecrawl.dev",
            config_path=self.config_path,
        )
        self.provider_config.add_key_ref(
            "firecrawl", key_ref="env:FIRECRAWL_API_KEY_TEST",
            auth_header="x-api-key", auth_prefix="", config_path=self.config_path,
        )
        resolved = self.firecrawl_cli.resolve_firecrawl(
            capability="web_search", config_path=self.config_path, state_path=self.state_path
        )
        env = self.firecrawl_cli.env_for(resolved)
        self.assertEqual(env["FIRECRAWL_API_KEY"], "fc-test-key")

    # -- keyed rotation preserved ----------------------------------------------

    def test_keyed_mode_continues_key_rotation(self):
        os.environ["FIRECRAWL_API_KEY_1"] = "fc-key-1"
        os.environ["FIRECRAWL_API_KEY_2"] = "fc-key-2"
        self.addCleanup(os.environ.pop, "FIRECRAWL_API_KEY_1", None)
        self.addCleanup(os.environ.pop, "FIRECRAWL_API_KEY_2", None)
        self.provider_config.set_provider_endpoint(
            "firecrawl", capability="web_search", capabilities=["web_search"],
            base_url="https://api.firecrawl.dev", config_path=self.config_path,
        )
        self.provider_config.add_key_ref(
            "firecrawl", key_ref="env:FIRECRAWL_API_KEY_1",
            auth_header="x-api-key", auth_prefix="", config_path=self.config_path,
        )
        self.provider_config.add_key_ref(
            "firecrawl", key_ref="env:FIRECRAWL_API_KEY_2",
            auth_header="x-api-key", auth_prefix="", config_path=self.config_path,
        )
        first = self.firecrawl_cli.resolve_firecrawl(
            capability="web_search", config_path=self.config_path, state_path=self.state_path
        )
        self.assertEqual(first["auth"]["key_ref"], "env:FIRECRAWL_API_KEY_1")
        self.firecrawl_cli.record_failure(
            first,
            self.firecrawl_cli.FirecrawlCliError("HTTP 429 rate limited", status=429),
            config_path=self.config_path, state_path=self.state_path,
        )
        second = self.firecrawl_cli.resolve_firecrawl(
            capability="web_search", config_path=self.config_path, state_path=self.state_path
        )
        self.assertEqual(second["auth"]["key_ref"], "env:FIRECRAWL_API_KEY_2")
        self.assertEqual(second["auth"]["value"], "fc-key-2")

    # -- Step 3: keyless execution / failure -----------------------------------

    def test_keyless_search_succeeds_without_config(self):
        search = self._load_script("skills/web-search/scripts/firecrawl_search.py")

        def ok_run(resolved, command, **kwargs):
            return json.dumps({"results": [{"title": "R", "url": "https://f.com"}]})

        rc, out, err = self._run_main(
            search,
            ["agent skills", "--output", "json", "--config-path", self.config_path, "--state-path", self.state_path],
            ok_run,
        )
        self.assertEqual(rc, 0)
        self.assertEqual(err, "")
        data = json.loads(out)
        self.assertEqual(data["provider"], "firecrawl")
        self.assertEqual(data["capability"], "web_search")
        self.assertNotIn("ok", data)

    def test_keyless_scrape_succeeds_without_config(self):
        scrape = self._load_script("skills/web-fetch/scripts/firecrawl_scrape.py")

        def ok_run(resolved, command, **kwargs):
            return json.dumps({"success": True, "markdown": "# hi"})

        rc, out, err = self._run_main(
            scrape,
            ["https://example.com", "--output", "json", "--config-path", self.config_path, "--state-path", self.state_path],
            ok_run,
        )
        self.assertEqual(rc, 0)
        data = json.loads(out)
        self.assertEqual(data["provider"], "firecrawl")
        self.assertEqual(data["capability"], "web_fetch")
        self.assertNotIn("ok", data)

    def test_keyless_429_writes_quota_error_record(self):
        search = self._load_script("skills/web-search/scripts/firecrawl_search.py")
        errfile = self._error_file()

        def fail(resolved, command, **kwargs):
            raise self.firecrawl_cli.FirecrawlCliError("HTTP 429 rate limited", status=429)

        rc, _out, err = self._run_main(
            search,
            ["agent skills", "--config-path", self.config_path, "--state-path", self.state_path],
            fail,
        )
        self.assertEqual(rc, 2)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["provider"], "firecrawl")
        self.assertEqual(record["capability"], "web_search")
        self.assertEqual(record["kind"], "quota")
        self.assertEqual(record["status"], 429)

    def test_keyless_scrape_429_writes_quota_error_record(self):
        scrape = self._load_script("skills/web-fetch/scripts/firecrawl_scrape.py")
        errfile = self._error_file()

        def fail(resolved, command, **kwargs):
            raise self.firecrawl_cli.FirecrawlCliError("HTTP 429 rate limited", status=429)

        rc, _out, err = self._run_main(
            scrape,
            ["https://example.com", "--config-path", self.config_path, "--state-path", self.state_path],
            fail,
        )
        self.assertEqual(rc, 2)
        record = json.loads(Path(errfile).read_text(encoding="utf-8"))
        self.assertEqual(record["capability"], "web_fetch")
        self.assertEqual(record["kind"], "quota")
        self.assertEqual(record["status"], 429)


if __name__ == "__main__":
    unittest.main()
