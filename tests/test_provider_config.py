import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills" / "provider-manager" / "scripts"))

from arkspace_runtime import provider_config


class ProviderConfigTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmpdir.cleanup)
        self.config_path = str(Path(self.tmpdir.name) / "providers.json")
        self.state_path = str(Path(self.tmpdir.name) / "state.json")

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

    def test_tavily_configure_command_writes_search_and_fetch_capabilities(self):
        import importlib.util

        script = ROOT / "skills" / "provider-manager" / "scripts" / "arkspace_provider.py"
        spec = importlib.util.spec_from_file_location("arkspace_provider_test_module", script)
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)

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

        self.assertEqual(data["providers"]["tavily"]["capabilities"], ["web_search", "web_fetch"])
        self.assertNotIn("capability", data["providers"]["tavily"])

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


if __name__ == "__main__":
    unittest.main()
