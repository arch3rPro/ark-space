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


if __name__ == "__main__":
    unittest.main()
