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
sys.path.insert(0, str(ROOT / "skills" / "provider-manager" / "scripts"))

from arkspace_runtime import provider_config


def load_provider_manager_module():
    script = ROOT / "skills" / "provider-manager" / "scripts" / "arkspace_provider.py"
    spec = importlib.util.spec_from_file_location("arkspace_provider_test_module", script)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
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

    def test_provider_hints_use_installed_package_absolute_command(self):
        command = f"python3 {ROOT / 'scripts' / 'arkspace.py'}"

        self.assertIn(command, provider_config.configure_hint("tavily"))
        self.assertIn(command, provider_config.configure_hint("exa"))
        self.assertIn(command, provider_config.configure_hint("searxng"))
        self.assertIn(command, provider_config.add_key_hint("tavily"))
        self.assertIn(command, provider_config.add_key_hint("exa"))
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
            "TAVILY_API_KEY_1": "first",
            "TAVILY_API_KEY_2": "second",
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
        self.assertEqual(second["auth"]["value"], "second")

    def test_key_rotation_fails_when_every_key_is_in_cooldown(self):
        os.environ["TAVILY_API_KEY_1"] = "first"
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
        os.environ["TAVILY_API_KEY_AVAILABLE"] = "second"
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
        self.assertEqual(resolved["auth"]["value"], "second")

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


if __name__ == "__main__":
    unittest.main()
