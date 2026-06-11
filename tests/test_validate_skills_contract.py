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
            "arxiv-search",
            "exa-search",
            "exa-contents",
            "exa-answer",
            "exa-context",
            "exa-similar",
            "firecrawl-search",
            "firecrawl-scrape",
            "firecrawl-map",
            "firecrawl-crawl",
            "firecrawl-agent",
            "firecrawl-browser",
            "firecrawl-interact",
            "firecrawl-monitor",
            "tavily-search",
            "tavily-extract",
            "tavily-map",
            "tavily-crawl",
            "tavily-research",
            "defuddle",
        ]:
            with self.subTest(name=name):
                item = active[name]
                self.assertTrue(is_public_true(item.get("public")))
                self.assertIn(f"/ark-space:{name}", item.get("directInvocation", ""))

    def test_routable_provider_skills_expose_orchestrator_invocation(self):
        skills = self.validate.parse_simple_yaml_list(ROOT / "registry" / "skills.yaml", "skills")
        by_name = {item["name"]: item for item in skills}

        for name in [
            "searxng-search",
            "arxiv-search",
            "exa-search",
            "exa-contents",
            "exa-answer",
            "exa-context",
            "exa-similar",
            "firecrawl-search",
            "firecrawl-scrape",
            "firecrawl-map",
            "firecrawl-crawl",
            "firecrawl-agent",
            "firecrawl-browser",
            "firecrawl-interact",
            "firecrawl-monitor",
            "tavily-search",
            "tavily-extract",
            "tavily-map",
            "tavily-crawl",
            "tavily-research",
            "defuddle",
        ]:
            with self.subTest(name=name):
                invocation = by_name[name].get("orchestratorInvocation", "")
                self.assertIn("/ark-space:orchestrator", invocation)
                self.assertRegex(invocation, r"/ark-space:orchestrator\s+\S+")

    def test_provider_registry_capabilities_match_skill_metadata(self):
        self.validate.validate_registry_files()

    def test_agent_registry_matches_frontmatter_and_role_ownership(self):
        agents = self.validate.parse_simple_yaml_list(ROOT / "registry" / "agents.yaml", "agents")
        agents_by_id = {item["id"]: item for item in agents}

        knowledge_skills = self.validate.split_csv(agents_by_id["arkspace-knowledge-manager"]["skills"])
        competitive_skills = self.validate.split_csv(agents_by_id["arkspace-competitive-analyst"]["skills"])
        doc_writer_skills = self.validate.split_csv(agents_by_id["arkspace-doc-writer"]["skills"])
        orchestrator_skills = self.validate.split_csv(agents_by_id["arkspace-orchestrator"]["skills"])

        for name in [
            "arxiv-search",
            "firecrawl-search",
            "firecrawl-scrape",
            "firecrawl-map",
            "firecrawl-crawl",
            "firecrawl-agent",
            "firecrawl-browser",
            "firecrawl-interact",
            "firecrawl-monitor",
        ]:
            with self.subTest(skill=name):
                self.assertIn(name, knowledge_skills)
                self.assertIn(name, competitive_skills)
                self.assertNotIn(name, orchestrator_skills)

        self.assertIn("obsidian-markdown", doc_writer_skills)
        self.validate.validate_registry_files()

    def test_tavily_extended_capabilities_are_provider_registered(self):
        expectations = {
            "search-providers.yaml": ("tavily-search", "web_search"),
            "web-fetch-providers.yaml": ("tavily-extract", "web_fetch"),
            "web-map-providers.yaml": ("tavily-map", "web_map"),
            "web-crawl-providers.yaml": ("tavily-crawl", "web_crawl"),
            "deep-research-providers.yaml": ("tavily-research", "deep_research"),
        }
        for registry_name, (skill, capability) in expectations.items():
            with self.subTest(registry=registry_name):
                providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / registry_name, "providers")
                tavily = next(item for item in providers if item.get("id") == "tavily")
                self.assertEqual(tavily.get("skill"), skill)
                self.assertEqual(tavily.get("capability"), capability)
                self.assertIn(f"--capability {capability}", tavily.get("checkCommand", ""))

        invocation = (ROOT / "docs" / "invocation.md").read_text(encoding="utf-8")
        self.assertIn("registry/web-map-providers.yaml", invocation)
        self.assertIn("registry/web-crawl-providers.yaml", invocation)
        self.assertIn("registry/deep-research-providers.yaml", invocation)
        self.assertIn("registry/code-context-providers.yaml", invocation)
        self.assertNotIn("Direct Tavily skill", invocation)

    def test_exa_capabilities_are_provider_registered(self):
        expectations = {
            "search-providers.yaml": ("exa-search", "web_search"),
            "web-fetch-providers.yaml": ("exa-contents", "web_fetch"),
            "deep-research-providers.yaml": ("exa-answer", "deep_research"),
            "code-context-providers.yaml": ("exa-context", "code_context"),
            "related-page-providers.yaml": ("exa-similar", "related_pages"),
        }
        for registry_name, (skill, capability) in expectations.items():
            with self.subTest(registry=registry_name):
                providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / registry_name, "providers")
                exa = next(item for item in providers if item.get("id") == "exa")
                self.assertEqual(exa.get("skill"), skill)
                self.assertEqual(exa.get("capability"), capability)
                self.assertIn(f"--capability {capability}", exa.get("checkCommand", ""))

    def test_arxiv_capability_is_provider_registered(self):
        providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / "search-providers.yaml", "providers")
        arxiv = next(item for item in providers if item.get("id") == "arxiv")

        self.assertEqual(arxiv.get("skill"), "arxiv-search")
        self.assertEqual(arxiv.get("capability"), "web_search")
        self.assertEqual(arxiv.get("configRequired"), "false")
        self.assertIn("--capability web_search", arxiv.get("checkCommand", ""))
        self.assertIn("docs/knowledge-manager", arxiv.get("roles", ""))

    def test_firecrawl_capabilities_are_provider_registered(self):
        expectations = {
            "search-providers.yaml": ("firecrawl-search", "web_search"),
            "web-fetch-providers.yaml": ("firecrawl-scrape", "web_fetch"),
            "web-map-providers.yaml": ("firecrawl-map", "web_map"),
            "web-crawl-providers.yaml": ("firecrawl-crawl", "web_crawl"),
            "structured-extract-providers.yaml": ("firecrawl-agent", "structured_extract"),
            "web-interact-providers.yaml": ("firecrawl-browser", "web_interact"),
            "web-monitor-providers.yaml": ("firecrawl-monitor", "web_monitor"),
        }
        for registry_name, (skill, capability) in expectations.items():
            with self.subTest(registry=registry_name):
                providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / registry_name, "providers")
                firecrawl = next(item for item in providers if item.get("id") == "firecrawl")
                self.assertEqual(firecrawl.get("skill"), skill)
                self.assertEqual(firecrawl.get("capability"), capability)
                self.assertIn(f"--capability {capability}", firecrawl.get("checkCommand", ""))
                self.assertIn("provider setup firecrawl --wizard", firecrawl.get("providerConfigCommand", ""))

    def test_runtime_instructions_use_installed_arkspace_path(self):
        runtime_paths = [
            ROOT / "registry" / "search-providers.yaml",
            ROOT / "registry" / "web-fetch-providers.yaml",
            ROOT / "registry" / "code-context-providers.yaml",
            ROOT / "registry" / "related-page-providers.yaml",
            ROOT / "skills" / "provider-manager" / "SKILL.md",
            ROOT / "skills" / "arxiv-search" / "SKILL.md",
            ROOT / "skills" / "searxng-search" / "SKILL.md",
            ROOT / "skills" / "exa-search" / "SKILL.md",
            ROOT / "skills" / "exa-contents" / "SKILL.md",
            ROOT / "skills" / "exa-answer" / "SKILL.md",
            ROOT / "skills" / "exa-context" / "SKILL.md",
            ROOT / "skills" / "exa-similar" / "SKILL.md",
            ROOT / "skills" / "firecrawl-search" / "SKILL.md",
            ROOT / "skills" / "firecrawl-scrape" / "SKILL.md",
            ROOT / "skills" / "firecrawl-map" / "SKILL.md",
            ROOT / "skills" / "firecrawl-crawl" / "SKILL.md",
            ROOT / "skills" / "firecrawl-agent" / "SKILL.md",
            ROOT / "skills" / "firecrawl-browser" / "SKILL.md",
            ROOT / "skills" / "firecrawl-interact" / "SKILL.md",
            ROOT / "skills" / "firecrawl-monitor" / "SKILL.md",
            ROOT / "skills" / "tavily-search" / "SKILL.md",
            ROOT / "skills" / "tavily-extract" / "SKILL.md",
            ROOT / "skills" / "tavily-map" / "SKILL.md",
            ROOT / "skills" / "tavily-crawl" / "SKILL.md",
            ROOT / "skills" / "tavily-research" / "SKILL.md",
        ]
        for path in runtime_paths:
            with self.subTest(path=path.relative_to(ROOT)):
                text = path.read_text(encoding="utf-8")
                self.assertNotIn("python3 scripts/arkspace.py", text)
                self.assertNotIn("python3 skills/", text)
                self.assertIn("<installed-arkspace-path>", text)

    def test_tavily_provider_registries_use_setup_first_metadata(self):
        for registry_name in [
            "search-providers.yaml",
            "web-fetch-providers.yaml",
            "web-map-providers.yaml",
            "web-crawl-providers.yaml",
            "deep-research-providers.yaml",
        ]:
            with self.subTest(registry=registry_name):
                providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / registry_name, "providers")
                tavily = next(item for item in providers if item.get("id") == "tavily")
                joined = " ".join(str(value) for value in tavily.values())
                self.assertIn("provider setup tavily --wizard", tavily.get("providerConfigCommand", ""))
                self.assertNotIn("provider configure tavily", joined)
                self.assertNotIn("provider add-key tavily", joined)

    def test_exa_provider_registries_use_setup_first_metadata(self):
        for registry_name in [
            "search-providers.yaml",
            "web-fetch-providers.yaml",
            "deep-research-providers.yaml",
            "code-context-providers.yaml",
            "related-page-providers.yaml",
        ]:
            with self.subTest(registry=registry_name):
                providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / registry_name, "providers")
                exa = next(item for item in providers if item.get("id") == "exa")
                joined = " ".join(str(value) for value in exa.values())
                self.assertIn("provider setup exa --wizard", exa.get("providerConfigCommand", ""))
                self.assertNotIn("provider configure exa", joined)
                self.assertNotIn("provider add-key exa", joined)

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
                self.assertIn("provider setup tavily --wizard", text)
                self.assertIn("host shell can provide interactive secret input", text)
                self.assertIn("do not run `--wizard` through that tool", text)
                self.assertIn("provider setup tavily --save-secret TAVILY_API_KEY --secret-stdin", text)
                self.assertIn(invocation, text)
                self.assertIn("Do not return Tavily", text)
                self.assertIn("declines, defers, or cannot complete setup", text)
                self.assertIn("clearly labeled non-ArkSpace fallback", text)

    def test_new_tavily_skills_use_setup_first_recovery(self):
        expectations = {
            "skills/tavily-map/SKILL.md": "provider check tavily --capability web_map",
            "skills/tavily-crawl/SKILL.md": "provider check tavily --capability web_crawl",
            "skills/tavily-research/SKILL.md": "provider check tavily --capability deep_research",
        }
        for skill_path, check_command in expectations.items():
            with self.subTest(skill=skill_path):
                text = (ROOT / skill_path).read_text(encoding="utf-8")
                self.assertIn("Missing Configuration Recovery", text)
                self.assertIn("Start setup wizard", text)
                self.assertIn("Not now", text)
                self.assertIn("provider setup tavily --wizard", text)
                self.assertIn(check_command, text)

    def test_exa_direct_skills_use_setup_first_recovery(self):
        expectations = {
            "skills/exa-search/SKILL.md": "provider check exa --capability web_search",
            "skills/exa-contents/SKILL.md": "provider check exa --capability web_fetch",
            "skills/exa-answer/SKILL.md": "provider check exa --capability deep_research",
            "skills/exa-context/SKILL.md": "provider check exa --capability code_context",
            "skills/exa-similar/SKILL.md": "provider check exa --capability related_pages",
        }
        for skill_path, check_command in expectations.items():
            with self.subTest(skill=skill_path):
                text = (ROOT / skill_path).read_text(encoding="utf-8")
                self.assertIn("Missing Configuration Recovery", text)
                self.assertIn("Start setup wizard", text)
                self.assertIn("Not now", text)
                self.assertIn("provider setup exa --wizard", text)
                self.assertIn(check_command, text)

    def test_provider_manager_guides_interactive_setup_before_manual_commands(self):
        text = (ROOT / "skills" / "provider-manager" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Ask whether to start setup now", text)
        self.assertIn("present exactly two choices", text)
        self.assertIn("Start setup wizard", text)
        self.assertIn("Not now", text)
        self.assertIn("provider setup tavily --wizard", text)
        self.assertIn("provider setup exa --wizard", text)
        self.assertIn("provider setup firecrawl --wizard", text)
        self.assertIn("can provide interactive secret input", text)
        self.assertIn("do not run `--wizard` through that tool", text)
        self.assertIn("provider setup tavily --save-secret TAVILY_API_KEY --secret-stdin", text)
        self.assertIn("provider setup exa --save-secret EXA_API_KEY --secret-stdin", text)
        self.assertIn("provider setup firecrawl --save-secret FIRECRAWL_API_KEY --secret-stdin", text)
        self.assertIn("rerun the original skill invocation", text)

    def test_provider_workflow_allows_fallback_only_after_setup_path(self):
        text = (ROOT / "workflows" / "provider-capabilities.md").read_text(encoding="utf-8")

        self.assertIn("the next action is provider setup", text)
        self.assertIn("declines, defers, or cannot complete setup", text)
        self.assertIn("clearly labeled non-ArkSpace fallback", text)
        self.assertIn("outside ArkSpace provider execution", text)
        self.assertIn("registry/code-context-providers.yaml", text)
        self.assertIn("registry/related-page-providers.yaml", text)


if __name__ == "__main__":
    unittest.main()
