import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_validate_module():
    spec = importlib.util.spec_from_file_location(
        "validate_skills_contract_module",
        ROOT / "scripts" / "validate-skills.py",
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def is_public_true(value):
    return value is True or value == "true"


class ValidateSkillsContractTests(unittest.TestCase):
    def setUp(self):
        self.validate = load_validate_module()

    def test_core_active_skills_expose_public_invocation_metadata(self):
        skills = self.validate.parse_simple_yaml_list(ROOT / "registry" / "skills.yaml", "skills")
        active = {item["name"]: item for item in skills if item.get("status") == "active"}

        for name in [
            "orchestrator",
            "skill-manager",
            "provider-manager",
            "searxng-search",
            "tavily-search",
            "tavily-extract",
            "defuddle",
        ]:
            with self.subTest(name=name):
                item = active[name]
                self.assertTrue(is_public_true(item.get("public")))
                self.assertIn(f"$ark-space:{name}", item.get("directInvocation", ""))

    def test_routable_provider_skills_expose_orchestrator_invocation(self):
        skills = self.validate.parse_simple_yaml_list(ROOT / "registry" / "skills.yaml", "skills")
        by_name = {item["name"]: item for item in skills}

        for name in ["searxng-search", "tavily-search", "tavily-extract", "defuddle"]:
            with self.subTest(name=name):
                invocation = by_name[name].get("orchestratorInvocation", "")
                self.assertIn("$ark-space:orchestrator", invocation)
                self.assertRegex(invocation, r"\$ark-space:orchestrator\s+\S+")

    def test_provider_registry_capabilities_match_skill_metadata(self):
        self.validate.validate_registry_files()

    def test_tavily_provider_registries_use_setup_first_metadata(self):
        for registry_name in ["search-providers.yaml", "web-fetch-providers.yaml"]:
            with self.subTest(registry=registry_name):
                providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / registry_name, "providers")
                tavily = next(item for item in providers if item.get("id") == "tavily")
                joined = " ".join(str(value) for value in tavily.values())
                self.assertIn("provider setup tavily --wizard", tavily.get("providerConfigCommand", ""))
                self.assertNotIn("provider configure tavily", joined)
                self.assertNotIn("provider add-key tavily", joined)

    def test_tavily_direct_skills_handle_missing_config_before_fallback(self):
        expectations = {
            "skills/tavily-search/SKILL.md": "/ark-space:tavily-search <query>",
            "skills/tavily-extract/SKILL.md": "/ark-space:tavily-extract <url>",
        }
        for skill_path, invocation in expectations.items():
            with self.subTest(skill=skill_path):
                text = (ROOT / skill_path).read_text(encoding="utf-8")
                self.assertIn("Missing Configuration Recovery", text)
                self.assertIn("Should I start the ArkSpace setup wizard now?", text)
                self.assertIn("Present exactly two choices", text)
                self.assertIn("Start setup wizard", text)
                self.assertIn("Not now", text)
                self.assertIn("! python3 <installed-arkspace-path>/scripts/arkspace.py provider setup tavily --wizard", text)
                self.assertIn("provider setup tavily --wizard", text)
                self.assertIn("user chooses setup", text)
                self.assertIn(invocation, text)
                self.assertIn("Do not return Tavily", text)
                self.assertIn("declines, defers, or cannot complete setup", text)
                self.assertIn("clearly labeled non-ArkSpace fallback", text)

    def test_provider_manager_guides_interactive_setup_before_manual_commands(self):
        text = (ROOT / "skills" / "provider-manager" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Ask whether to start setup now", text)
        self.assertIn("present exactly two choices", text)
        self.assertIn("Start setup wizard", text)
        self.assertIn("Not now", text)
        self.assertIn("provider setup tavily --wizard", text)
        self.assertIn("user chooses setup", text)
        self.assertIn("rerun the original skill invocation", text)

    def test_provider_workflow_allows_fallback_only_after_setup_path(self):
        text = (ROOT / "workflows" / "provider-capabilities.md").read_text(encoding="utf-8")

        self.assertIn("the next action is provider setup", text)
        self.assertIn("declines, defers, or cannot complete setup", text)
        self.assertIn("clearly labeled non-ArkSpace fallback", text)
        self.assertIn("outside ArkSpace provider execution", text)


if __name__ == "__main__":
    unittest.main()
