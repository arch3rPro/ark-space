import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
TAVILY_CAPABILITIES = ["web_search", "web_fetch", "web_map", "web_crawl", "deep_research"]
EXA_CAPABILITIES = ["web_search", "web_fetch", "deep_research", "code_context", "related_pages"]
FIRECRAWL_CAPABILITIES = [
    "web_search",
    "web_fetch",
    "web_map",
    "web_crawl",
    "structured_extract",
    "web_interact",
    "web_monitor",
]
sys.path.insert(0, str(ROOT / "skills" / "provider-manager" / "scripts"))

from arkspace_runtime import provider_config  # type: ignore[reportMissingImports]


def load_provider_manager_module():
    script = ROOT / "skills" / "provider-manager" / "scripts" / "arkspace_provider.py"
    spec = importlib.util.spec_from_file_location("arkspace_provider_test_module", script)
    module = importlib.util.module_from_spec(spec)  # type: ignore[reportArgumentType]
    assert spec.loader is not None  # type: ignore[reportOptionalMemberAccess]
    spec.loader.exec_module(module)  # type: ignore[reportOptionalMemberAccess]
    return module


class ProviderConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.config_path = str(Path(self.tmpdir.name) / "providers.json")
        self.state_path = str(Path(self.tmpdir.name) / "state.json")
        self.secrets_path = str(Path(self.tmpdir.name) / "secrets.json")
        os.environ["ARKSPACE_PROVIDER_SECRETS"] = self.secrets_path
        self.addCleanup(os.environ.pop, "ARKSPACE_PROVIDER_SECRETS", None)

    def write_config(self, data):
        payload = {"version": 1, **data}
        with open(self.config_path, "w", encoding="utf-8") as handle:
            json.dump(payload, handle)

    def _set_error_env(self):
        self.error_path = str(Path(self.tmpdir.name) / "error.json")
        os.environ[provider_config.ERROR_FILE_ENV] = self.error_path
        self.addCleanup(os.environ.pop, provider_config.ERROR_FILE_ENV, None)

    def test_resolve_provider_accepts_capabilities_list(self):
        provider_config.set_provider_endpoint(
            "tavily",
            capability="web_search",
            capabilities=["web_search", "web_fetch"],
            base_url="https://api.tavily.com",
            config_path=self.config_path,
        )

        resolved = provider_config.resolve_provider(
            "tavily",
            capability="web_fetch",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=False,
        )

        self.assertEqual(resolved["capability"], "web_fetch")
        self.assertEqual(resolved["endpoint"]["base_url"], "https://api.tavily.com")

    def test_tavily_configure_command_writes_tavily_capabilities(self):
        module = load_provider_manager_module()

        args = type(
            "Args",
            (),
            {
                "provider": "tavily",
                "capability": None,
                "base_url": "https://api.tavily.com",
                "endpoint_id": "default",
                "config_path": self.config_path,
            },
        )()

        module.command_configure(args)
        data = provider_config.load_config(self.config_path)

        self.assertEqual(data["providers"]["tavily"]["capabilities"], TAVILY_CAPABILITIES)
        self.assertNotIn("capability", data["providers"]["tavily"])

    def test_exa_configure_command_writes_exa_capabilities(self):
        module = load_provider_manager_module()

        args = type(
            "Args",
            (),
            {
                "provider": "exa",
                "capability": None,
                "base_url": "https://api.exa.ai",
                "endpoint_id": "default",
                "config_path": self.config_path,
            },
        )()

        module.command_configure(args)
        data = provider_config.load_config(self.config_path)

        self.assertEqual(data["providers"]["exa"]["capabilities"], EXA_CAPABILITIES)
        self.assertNotIn("capability", data["providers"]["exa"])

    def test_firecrawl_setup_command_writes_endpoint_capabilities_and_key_ref(self):
        os.environ["FIRECRAWL_API_KEY"] = "fc-test-key"
        self.addCleanup(os.environ.pop, "FIRECRAWL_API_KEY", None)
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "firecrawl",
                "base_url": None,
                "env": ["FIRECRAWL_API_KEY"],
                "save_secret": [],
                "wizard": False,
                "key_count": 1,
                "prompt": False,
                "secret_stdin": False,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["firecrawl"]
        self.assertEqual(entry["capabilities"], FIRECRAWL_CAPABILITIES)
        self.assertEqual(entry["endpoints"][0]["base_url"], "https://api.firecrawl.dev")
        self.assertEqual(entry["auth"]["type"], "api_key")
        self.assertEqual(entry["auth"]["header"], "Authorization")
        self.assertEqual(entry["auth"]["prefix"], "Bearer ")
        self.assertEqual(entry["auth"]["key_refs"], ["env:FIRECRAWL_API_KEY"])
        self.assertNotIn("fc-test-key", json.dumps(data))
        self.assertIn("configured provider firecrawl", output.getvalue())

    def test_firecrawl_setup_wizard_generates_multiple_secret_names(self):
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "firecrawl",
                "base_url": None,
                "env": [],
                "save_secret": [],
                "wizard": True,
                "key_count": 2,
                "prompt": False,
                "secret_stdin": True,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with patch.object(sys, "stdin", io.StringIO("first-secret\nsecond-secret\n")):
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["firecrawl"]
        self.assertEqual(entry["auth"]["key_refs"], ["env:FIRECRAWL_API_KEY_1", "env:FIRECRAWL_API_KEY_2"])
        self.assertEqual(entry["auth"]["header"], "Authorization")
        self.assertEqual(entry["auth"]["prefix"], "Bearer ")

        secrets = provider_config.load_secrets(self.secrets_path)
        self.assertEqual(secrets["secrets"]["FIRECRAWL_API_KEY_1"], "first-secret")
        self.assertEqual(secrets["secrets"]["FIRECRAWL_API_KEY_2"], "second-secret")

    def test_brave_setup_command_writes_endpoint_capabilities_and_key_ref(self):
        os.environ["BRAVE_API_KEY"] = "brave-test-key"
        self.addCleanup(os.environ.pop, "BRAVE_API_KEY", None)
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "brave",
                "base_url": None,
                "env": ["BRAVE_API_KEY"],
                "save_secret": [],
                "wizard": False,
                "key_count": 1,
                "prompt": False,
                "secret_stdin": False,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["brave"]
        self.assertEqual(entry["capabilities"], ["web_search"])
        self.assertEqual(entry["endpoints"][0]["base_url"], "https://api.search.brave.com")
        self.assertEqual(entry["auth"]["type"], "api_key")
        self.assertEqual(entry["auth"]["header"], "X-Subscription-Token")
        self.assertEqual(entry["auth"]["prefix"], "")
        self.assertEqual(entry["auth"]["key_refs"], ["env:BRAVE_API_KEY"])
        self.assertNotIn("brave-test-key", json.dumps(data))
        self.assertIn("configured provider brave", output.getvalue())

    def test_brave_setup_wizard_generates_multiple_secret_names(self):
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "brave",
                "base_url": None,
                "env": [],
                "save_secret": [],
                "wizard": True,
                "key_count": 2,
                "prompt": False,
                "secret_stdin": True,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with patch.object(sys, "stdin", io.StringIO("first-secret\nsecond-secret\n")):
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["brave"]
        self.assertEqual(entry["capabilities"], ["web_search"])
        self.assertEqual(
            entry["auth"]["key_refs"],
            ["env:BRAVE_API_KEY_1", "env:BRAVE_API_KEY_2"],
        )
        self.assertEqual(entry["auth"]["header"], "X-Subscription-Token")

        secrets = provider_config.load_secrets(self.secrets_path)
        self.assertEqual(secrets["secrets"]["BRAVE_API_KEY_1"], "first-secret")
        self.assertEqual(secrets["secrets"]["BRAVE_API_KEY_2"], "second-secret")

    def test_brave_key_rotation_skips_key_in_cooldown(self):
        for name, value in {
            "BRAVE_API_KEY_1": "brave-key-1",
            "BRAVE_API_KEY_2": "brave-key-2",
        }.items():
            os.environ[name] = value
            self.addCleanup(os.environ.pop, name, None)

        provider_config.set_provider_endpoint(
            "brave",
            capability="web_search",
            base_url="https://api.search.brave.com",
            config_path=self.config_path,
        )
        provider_config.add_key_ref(
            "brave",
            key_ref="env:BRAVE_API_KEY_1",
            auth_header="X-Subscription-Token",
            config_path=self.config_path,
        )
        provider_config.add_key_ref(
            "brave",
            key_ref="env:BRAVE_API_KEY_2",
            auth_header="X-Subscription-Token",
            config_path=self.config_path,
        )

        first = provider_config.resolve_provider(
            "brave",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )
        provider_config.record_provider_result(
            "brave",
            key_ref=first["auth"]["key_ref"],
            ok=False,
            status=429,
            config_path=self.config_path,
            state_path=self.state_path,
        )

        second = provider_config.resolve_provider(
            "brave",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )

        self.assertEqual(second["auth"]["key_ref"], "env:BRAVE_API_KEY_2")
        self.assertEqual(second["auth"]["value"], "brave-key-2")


    def test_provider_hints_use_installed_package_absolute_command(self):
        command = f"python3 {ROOT / 'scripts' / 'arkspace.py'}"

        self.assertIn(command, provider_config.configure_hint("tavily"))
        self.assertIn(command, provider_config.configure_hint("exa"))
        self.assertIn(command, provider_config.configure_hint("firecrawl"))
        self.assertIn(command, provider_config.configure_hint("searxng"))
        self.assertIn(command, provider_config.add_key_hint("tavily"))
        self.assertIn(command, provider_config.add_key_hint("exa"))
        self.assertIn(command, provider_config.add_key_hint("firecrawl"))
        self.assertIn(command, provider_config.add_key_hint("brave-search"))
        self.assertNotIn("python3 scripts/arkspace.py", provider_config.configure_hint("tavily"))

    def test_resolve_api_key_auth_preserves_header_prefix_and_hides_secret(self):
        os.environ["TAVILY_API_KEY_1"] = "tvly-test-key"
        self.addCleanup(os.environ.pop, "TAVILY_API_KEY_1", None)

        provider_config.set_provider_endpoint(
            "tavily",
            capability="web_search",
            base_url="https://api.tavily.com",
            config_path=self.config_path,
        )
        provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_1",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )

        resolved = provider_config.resolve_provider(
            "tavily",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )

        self.assertEqual(resolved["auth"]["header"], "Authorization")
        self.assertEqual(resolved["auth"]["prefix"], "Bearer ")
        self.assertEqual(resolved["auth"]["value"], "tvly-test-key")
        self.assertNotIn("value", provider_config.public_view(resolved)["auth"])

    def test_key_rotation_skips_key_in_cooldown(self):
        for name, value in {
            "TAVILY_API_KEY_1": "first-key-value-1",
            "TAVILY_API_KEY_2": "second-key-value-2",
        }.items():
            os.environ[name] = value
            self.addCleanup(os.environ.pop, name, None)

        provider_config.set_provider_endpoint(
            "tavily",
            capability="web_search",
            base_url="https://api.tavily.com",
            config_path=self.config_path,
        )
        provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_1",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )
        provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_2",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )

        first = provider_config.resolve_provider(
            "tavily",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )
        provider_config.record_provider_result(
            "tavily",
            key_ref=first["auth"]["key_ref"],
            ok=False,
            status=429,
            config_path=self.config_path,
            state_path=self.state_path,
        )

        second = provider_config.resolve_provider(
            "tavily",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )

        self.assertEqual(second["auth"]["key_ref"], "env:TAVILY_API_KEY_2")
        self.assertEqual(second["auth"]["value"], "second-key-value-2")

    def test_key_rotation_fails_when_every_key_is_in_cooldown(self):
        os.environ["TAVILY_API_KEY_1"] = "first-key-value-1"
        self.addCleanup(os.environ.pop, "TAVILY_API_KEY_1", None)
        provider_config.set_provider_endpoint(
            "tavily",
            capability="web_search",
            base_url="https://api.tavily.com",
            config_path=self.config_path,
        )
        provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_1",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )
        first = provider_config.resolve_provider(
            "tavily",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )
        provider_config.record_provider_result(
            "tavily",
            key_ref=first["auth"]["key_ref"],
            ok=False,
            status=429,
            config_path=self.config_path,
            state_path=self.state_path,
        )

        with self.assertRaisesRegex(provider_config.ProviderConfigError, "all tavily keys are cooling down"):
            provider_config.resolve_provider(
                "tavily",
                capability="web_search",
                config_path=self.config_path,
                state_path=self.state_path,
                require_secret=True,
            )

    def test_key_rotation_skips_unavailable_env_refs(self):
        os.environ["TAVILY_API_KEY_AVAILABLE"] = "second-key-value-2"
        self.addCleanup(os.environ.pop, "TAVILY_API_KEY_AVAILABLE", None)
        provider_config.set_provider_endpoint(
            "tavily",
            capability="web_search",
            base_url="https://api.tavily.com",
            config_path=self.config_path,
        )
        provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_MISSING",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )
        provider_config.add_key_ref(
            "tavily",
            key_ref="env:TAVILY_API_KEY_AVAILABLE",
            auth_header="Authorization",
            auth_prefix="Bearer ",
            config_path=self.config_path,
        )

        resolved = provider_config.resolve_provider(
            "tavily",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )

        self.assertEqual(resolved["auth"]["key_ref"], "env:TAVILY_API_KEY_AVAILABLE")
        self.assertEqual(resolved["auth"]["value"], "second-key-value-2")

    def test_tavily_setup_command_writes_endpoint_capabilities_and_key_ref(self):
        os.environ["TAVILY_API_KEY"] = "tvly-test-key"
        self.addCleanup(os.environ.pop, "TAVILY_API_KEY", None)
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "tavily",
                "base_url": None,
                "env": ["TAVILY_API_KEY"],
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["tavily"]
        self.assertEqual(entry["capabilities"], TAVILY_CAPABILITIES)
        self.assertEqual(entry["endpoints"][0]["base_url"], "https://api.tavily.com")
        self.assertEqual(entry["auth"]["type"], "api_key")
        self.assertEqual(entry["auth"]["header"], "Authorization")
        self.assertEqual(entry["auth"]["prefix"], "Bearer ")
        self.assertEqual(entry["auth"]["key_refs"], ["env:TAVILY_API_KEY"])
        self.assertNotIn("tvly-test-key", json.dumps(data))
        self.assertIn("configured provider tavily", output.getvalue())

    def test_exa_setup_command_writes_endpoint_capabilities_and_key_ref(self):
        os.environ["EXA_API_KEY"] = "exa-test-key"
        self.addCleanup(os.environ.pop, "EXA_API_KEY", None)
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "exa",
                "base_url": None,
                "env": ["EXA_API_KEY"],
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["exa"]
        self.assertEqual(entry["capabilities"], EXA_CAPABILITIES)
        self.assertEqual(entry["endpoints"][0]["base_url"], "https://api.exa.ai")
        self.assertEqual(entry["auth"]["type"], "api_key")
        self.assertEqual(entry["auth"]["header"], "x-api-key")
        self.assertEqual(entry["auth"]["prefix"], "")
        self.assertEqual(entry["auth"]["key_refs"], ["env:EXA_API_KEY"])
        self.assertNotIn("exa-test-key", json.dumps(data))
        self.assertIn("configured provider exa", output.getvalue())

    def test_tavily_setup_command_is_idempotent_and_appends_new_env_refs(self):
        module = load_provider_manager_module()
        first = type(
            "Args",
            (),
            {
                "provider": "tavily",
                "base_url": None,
                "env": ["TAVILY_API_KEY_1", "TAVILY_API_KEY_2"],
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()
        second = type(
            "Args",
            (),
            {
                "provider": "tavily",
                "base_url": None,
                "env": ["TAVILY_API_KEY_2", "TAVILY_API_KEY_3"],
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        self.assertEqual(module.command_setup(first), 0)
        self.assertEqual(module.command_setup(second), 0)

        data = provider_config.load_config(self.config_path)
        self.assertEqual(
            data["providers"]["tavily"]["auth"]["key_refs"],
            ["env:TAVILY_API_KEY_1", "env:TAVILY_API_KEY_2", "env:TAVILY_API_KEY_3"],
        )
        self.assertEqual(len(data["providers"]["tavily"]["endpoints"]), 1)
        self.assertEqual(data["providers"]["tavily"]["endpoints"][0]["base_url"], "https://api.tavily.com")

    def test_tavily_setup_command_saves_multiple_private_secret_values(self):
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "tavily",
                "base_url": None,
                "env": [],
                "save_secret": ["TAVILY_API_KEY_1", "TAVILY_API_KEY_2"],
                "prompt": False,
                "secret_stdin": True,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with patch.object(sys, "stdin", io.StringIO("first-secret\nsecond-secret\n")), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["tavily"]
        self.assertEqual(entry["auth"]["key_refs"], ["env:TAVILY_API_KEY_1", "env:TAVILY_API_KEY_2"])
        self.assertNotIn("first-secret", json.dumps(data))
        self.assertNotIn("second-secret", json.dumps(data))
        self.assertIn("saved secret env:TAVILY_API_KEY_1", output.getvalue())

        secrets = provider_config.load_secrets(self.secrets_path)
        self.assertEqual(secrets["secrets"]["TAVILY_API_KEY_1"], "first-secret")
        self.assertEqual(secrets["secrets"]["TAVILY_API_KEY_2"], "second-secret")
        self.assertEqual(Path(self.secrets_path).stat().st_mode & 0o777, 0o600)

        resolved = provider_config.resolve_provider(
            "tavily",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )
        self.assertEqual(resolved["auth"]["key_ref"], "env:TAVILY_API_KEY_1")
        self.assertEqual(resolved["auth"]["value"], "first-secret")

        provider_config.record_provider_result(
            "tavily",
            key_ref=resolved["auth"]["key_ref"],
            ok=False,
            status=429,
            config_path=self.config_path,
            state_path=self.state_path,
        )
        second = provider_config.resolve_provider(
            "tavily",
            capability="web_search",
            config_path=self.config_path,
            state_path=self.state_path,
            require_secret=True,
        )
        self.assertEqual(second["auth"]["key_ref"], "env:TAVILY_API_KEY_2")
        self.assertEqual(second["auth"]["value"], "second-secret")

    def test_tavily_setup_wizard_generates_multiple_secret_names(self):
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "tavily",
                "base_url": None,
                "env": [],
                "save_secret": [],
                "wizard": True,
                "key_count": 2,
                "prompt": False,
                "secret_stdin": True,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with patch.object(sys, "stdin", io.StringIO("first-secret\nsecond-secret\n")):
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["tavily"]
        self.assertEqual(entry["auth"]["key_refs"], ["env:TAVILY_API_KEY_1", "env:TAVILY_API_KEY_2"])

        secrets = provider_config.load_secrets(self.secrets_path)
        self.assertEqual(secrets["secrets"]["TAVILY_API_KEY_1"], "first-secret")
        self.assertEqual(secrets["secrets"]["TAVILY_API_KEY_2"], "second-secret")

    def test_exa_setup_wizard_generates_multiple_secret_names(self):
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "exa",
                "base_url": None,
                "env": [],
                "save_secret": [],
                "wizard": True,
                "key_count": 2,
                "prompt": False,
                "secret_stdin": True,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with patch.object(sys, "stdin", io.StringIO("first-secret\nsecond-secret\n")):
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["exa"]
        self.assertEqual(entry["auth"]["key_refs"], ["env:EXA_API_KEY_1", "env:EXA_API_KEY_2"])
        self.assertEqual(entry["auth"]["header"], "x-api-key")
        self.assertEqual(entry["auth"]["prefix"], "")

        secrets = provider_config.load_secrets(self.secrets_path)
        self.assertEqual(secrets["secrets"]["EXA_API_KEY_1"], "first-secret")
        self.assertEqual(secrets["secrets"]["EXA_API_KEY_2"], "second-secret")

    def test_tavily_setup_wizard_requires_tty_before_writing_config(self):
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "tavily",
                "base_url": None,
                "env": [],
                "save_secret": [],
                "wizard": True,
                "key_count": 1,
                "prompt": False,
                "secret_stdin": False,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with patch.object(module, "can_collect_interactive_secret", return_value=False):
            with self.assertRaisesRegex(provider_config.ProviderConfigError, "interactive secret input requires a TTY"):
                module.command_setup(args)

        data = provider_config.load_config(self.config_path)
        self.assertNotIn("tavily", data.get("providers", {}))
        secrets = provider_config.load_secrets(self.secrets_path)
        self.assertEqual(secrets["secrets"], {})

    def test_tavily_setup_command_allows_endpoint_only_setup(self):
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "tavily",
                "base_url": None,
                "env": [],
                "save_secret": [],
                "prompt": False,
                "secret_stdin": False,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["tavily"]
        self.assertEqual(entry["capabilities"], TAVILY_CAPABILITIES)
        self.assertEqual(entry["endpoints"][0]["base_url"], "https://api.tavily.com")
        self.assertEqual(entry["auth"]["type"], "none")
        self.assertNotIn("key_refs", entry["auth"])
        self.assertIn("add and save an API key", output.getvalue())
        self.assertIn("--save-secret TAVILY_API_KEY --prompt", output.getvalue())

    def test_exa_setup_command_allows_endpoint_only_setup(self):
        module = load_provider_manager_module()
        args = type(
            "Args",
            (),
            {
                "provider": "exa",
                "base_url": None,
                "env": [],
                "save_secret": [],
                "prompt": False,
                "secret_stdin": False,
                "config_path": self.config_path,
                "state_path": self.state_path,
                "check": False,
            },
        )()

        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(module.command_setup(args), 0)

        data = provider_config.load_config(self.config_path)
        entry = data["providers"]["exa"]
        self.assertEqual(entry["capabilities"], EXA_CAPABILITIES)
        self.assertEqual(entry["endpoints"][0]["base_url"], "https://api.exa.ai")
        self.assertEqual(entry["auth"]["type"], "none")
        self.assertNotIn("key_refs", entry["auth"])
        self.assertIn("add and save an API key", output.getvalue())
        self.assertIn("--save-secret EXA_API_KEY --prompt", output.getvalue())

    def test_classify_failure_covers_retryable_and_terminal_kinds(self):
        cases = [
            (401, None, "auth"), (403, None, "auth"),
            (402, None, "quota"), (429, None, "quota"),
            (500, None, "transient"), (503, None, "transient"),
            (400, None, "invalid-request"), (404, None, "invalid-request"),
            (409, None, "invalid-request"), (422, None, "invalid-request"),
            (200, "invalid JSON", "invalid-response"),
            (None, "connection timed out", "network"),
            (None, "unrecognized provider failure", "unknown"),
        ]
        for status, error, expected in cases:
            with self.subTest(status=status, error=error):
                self.assertEqual(provider_config.classify_failure(status, error), expected)

    def test_exa_mcp_default_policy_allows_invalid_response(self):
        self.assertEqual(
            provider_config.fallback_policy("exa-mcp", str(self.config_path)),
            ["quota", "network", "transient", "invalid-response"],
        )

    def test_unrelated_default_policy_excludes_invalid_response(self):
        self.assertEqual(
            provider_config.fallback_policy("tavily", str(self.config_path)),
            ["quota", "network", "transient"],
        )

    def test_exa_mcp_explicit_empty_policy_disables_fallback(self):
        self.write_config({"providers": {"exa-mcp": {"fallback_on": []}}})
        self.assertEqual(provider_config.fallback_policy("exa-mcp", str(self.config_path)), [])

    def test_fallback_policy_defaults_when_provider_missing(self):
        self.write_config({})
        self.assertEqual(
            provider_config.fallback_policy("exa", str(self.config_path)),
            list(provider_config.DEFAULT_FALLBACK_ON),
        )

    def test_fallback_policy_defaults_when_field_missing(self):
        self.write_config({"providers": {"exa": {}}})
        self.assertEqual(
            provider_config.fallback_policy("exa", str(self.config_path)),
            list(provider_config.DEFAULT_FALLBACK_ON),
        )

    def test_fallback_policy_preserves_explicit_empty_list(self):
        self.write_config({"providers": {"exa": {"fallback_on": []}}})
        self.assertEqual(provider_config.fallback_policy("exa", str(self.config_path)), [])

    def test_fallback_policy_returns_valid_override(self):
        self.write_config({"providers": {"exa": {"fallback_on": ["network", "quota"]}}})
        self.assertEqual(provider_config.fallback_policy("exa", str(self.config_path)), ["network", "quota"])

    def test_fallback_policy_rejects_unknown_kind(self):
        self.write_config({"providers": {"exa": {"fallback_on": ["mystery"]}}})
        with self.assertRaisesRegex(provider_config.ProviderConfigError, "unknown failure kind"):
            provider_config.fallback_policy("exa", str(self.config_path))

    def test_fallback_policy_rejects_camelcase_field(self):
        # snake_case is authoritative; a camelCase ``fallbackOn`` key is not read.
        self.write_config({"providers": {"exa": {"fallbackOn": []}}})
        self.assertEqual(
            provider_config.fallback_policy("exa", str(self.config_path)),
            list(provider_config.DEFAULT_FALLBACK_ON),
        )

    def test_is_supported_key_ref_rejects_invalid_special_forms(self):
        invalid = ["", "env:", "$", "${}", "${UNFINISHED", "!"]
        for value in invalid:
            with self.subTest(value=value):
                self.assertFalse(provider_config.is_supported_key_ref(value))

    def test_is_supported_key_ref_allows_valid_forms_and_literals(self):
        valid = ["env:KEY", "$KEY", "${KEY}", "!op read op://vault/key", "short", "literal-value"]
        for value in valid:
            with self.subTest(value=value):
                self.assertTrue(provider_config.is_supported_key_ref(value))

    def test_placeholder_key_rejects_denylist_and_template_values(self):
        rejected = ["dummy", "your-api-key", "xxx", "CHANGE_ME"]
        for value in rejected:
            with self.subTest(value=value):
                self.assertTrue(provider_config.is_placeholder_key(value))

    def test_placeholder_key_allows_short_literal(self):
        # a legitimate short literal is not rejected solely by length
        self.assertFalse(provider_config.is_placeholder_key("short"))
        self.assertFalse(provider_config.is_placeholder_key("abc"))

    def test_error_file_not_written_without_env(self):
        os.environ.pop(provider_config.ERROR_FILE_ENV, None)
        provider_config.write_error_file("exa", "web_search", kind="network", message="timeout")
        self.assertFalse(Path(self.tmpdir.name).joinpath("error.json").exists())

    def test_error_file_writes_version_one_schema(self):
        self._set_error_env()
        provider_config.write_error_file("exa", "web_search", kind="quota", status=429, message="rate limited")
        record = provider_config.read_error_file(self.error_path)
        self.assertEqual(record["version"], 1)
        self.assertEqual(record["provider"], "exa")
        self.assertEqual(record["capability"], "web_search")
        self.assertEqual(record["kind"], "quota")
        self.assertEqual(record["status"], 429)

    def test_error_file_mode_is_0600(self):
        self._set_error_env()
        provider_config.write_error_file("exa", "web_search", kind="network", message="timeout")
        self.assertEqual(Path(self.error_path).stat().st_mode & 0o777, 0o600)

    def test_error_file_rejects_unknown_kind(self):
        self._set_error_env()
        with self.assertRaisesRegex(provider_config.ProviderConfigError, "unknown failure kind"):
            provider_config.write_error_file("exa", "web_search", kind="bogus", message="x")
        self.assertFalse(Path(self.error_path).exists())

    def test_error_file_redacts_and_bounds_message(self):
        self._set_error_env()
        provider_config.write_error_file(
            "exa", "web_search", kind="network", message="provider error " * 500
        )
        record = provider_config.read_error_file(self.error_path)
        self.assertLessEqual(len(record["message"]), provider_config.ERROR_MESSAGE_MAX_CHARS)

    def test_error_file_never_records_secrets(self):
        self._set_error_env()
        message = (
            "used key env:TAVILY_API_KEY via Authorization: Bearer secret-token-123, "
            "ran !op read op://vault/item, body aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789"
        )
        provider_config.write_error_file("exa", "web_search", kind="auth", message=message)
        record = provider_config.read_error_file(self.error_path)
        stored = record["message"]
        self.assertNotIn("TAVILY_API_KEY", stored)
        self.assertNotIn("secret-token-123", stored)
        self.assertNotIn("!op", stored)
        self.assertNotIn("aBcDeFgHiJkLmNoPqRsTuVwXyZ0123456789", stored)

    def test_safe_message_and_error_file_redact_short_labeled_credentials(self):
        self._set_error_env()
        message = (
            "HTTP 429 token=fc-123456 api_key=vkey apikey=vapi secret=vsecret password=vpass "
            "Authorization: Bearer auth; Bearer bearer-token status retry"
        )

        safe = provider_config.safe_message(message)
        provider_config.write_error_file("firecrawl", "web_map", kind="quota", status=429, message=message)
        stored = provider_config.read_error_file(self.error_path)["message"]

        for credential in ("fc-123456", "vkey", "vapi", "vsecret", "vpass", "auth", "bearer-token"):
            with self.subTest(credential=credential):
                self.assertNotIn(credential, safe)
                self.assertNotIn(credential, stored)
        self.assertIn("HTTP 429", safe)
        self.assertIn("status retry", safe)
        self.assertIn("HTTP 429", stored)
        self.assertIn("status retry", stored)

    def test_error_file_read_returns_none_for_corrupt_and_unknown_version(self):
        path = str(Path(self.tmpdir.name) / "bad.json")
        Path(path).write_text("{ not json", encoding="utf-8")
        self.assertIsNone(provider_config.read_error_file(path))
        Path(path).write_text(json.dumps({"version": 99, "kind": "network"}), encoding="utf-8")
        self.assertIsNone(provider_config.read_error_file(path))
        self.assertIsNone(provider_config.read_error_file(str(Path(self.tmpdir.name) / "nope.json")))


if __name__ == "__main__":
    unittest.main()
