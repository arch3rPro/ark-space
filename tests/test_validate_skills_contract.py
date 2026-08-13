import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_validate_module():
    spec = importlib.util.spec_from_file_location(
        "validate_skills_contract_module",
        ROOT / "scripts" / "validate-skills.py",
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[reportArgumentType]
    assert spec.loader is not None  # type: ignore[reportOptionalMemberAccess]
    spec.loader.exec_module(module)  # type: ignore[reportOptionalMemberAccess]
    return module


def is_public_true(value):
    return value is True or value == "true"  # pi-lens-ignore: no-identity-operator-on-literals


def load_arkspace_module():
    spec = importlib.util.spec_from_file_location(
        "arkspace_contract_module",
        ROOT / "scripts" / "arkspace.py",
    )
    module = importlib.util.module_from_spec(spec)  # type: ignore[reportArgumentType]
    assert spec.loader is not None  # type: ignore[reportOptionalMemberAccess]
    spec.loader.exec_module(module)  # type: ignore[reportOptionalMemberAccess]
    return module


# Documented search-selection policy identifiers. Higher registry ``priority``
# breaks ties only; it never overrides an explicit provider request and never
# controls ``--providers`` order. ``explicit-only`` means the provider is used
# only when the caller names it.
SEARCH_POLICY_ALLOW_LIST = {"role-first-provider-second", "priority-first", "explicit-only"}
PRIORITY_RANGE = range(1, 1001)

# Zero-config/explicit web_search providers added in the fallback-providers plan.
KEYLESS_WEB_SEARCH_PROVIDERS = ("exa-mcp", "jina", "duckduckgo")
KEYED_WEB_SEARCH_PROVIDERS = ("brave",)


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
            "web-search",
            "web-fetch",
            "web-site",
            "web-research",
            "web-extract",
            "web-automation",
            "code-context",
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
            "web-search",
            "web-fetch",
            "web-site",
            "web-research",
            "web-extract",
            "web-automation",
            "code-context",
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

        web_skills = self.validate.split_csv(agents_by_id["web-researcher"]["skills"])
        knowledge_skills = self.validate.split_csv(agents_by_id["knowledge-manager"]["skills"])
        competitive_skills = self.validate.split_csv(agents_by_id["competitive-analyst"]["skills"])
        doc_writer_skills = self.validate.split_csv(agents_by_id["doc-writer"]["skills"])
        orchestrator_skills = self.validate.split_csv(agents_by_id["orchestrator"]["skills"])

        for name in [
            "web-search",
            "web-fetch",
            "web-site",
            "web-extract",
        ]:
            with self.subTest(skill=name):
                self.assertIn(name, web_skills)
                self.assertIn(name, competitive_skills)
                self.assertNotIn(name, knowledge_skills)
                self.assertNotIn(name, orchestrator_skills)

        self.assertIn("web-automation", web_skills)
        self.assertNotIn("web-automation", competitive_skills)

        self.assertIn("obsidian-markdown", doc_writer_skills)
        self.validate.validate_registry_files()

    def test_personal_assistant_registry_contract(self):
        agents = self.validate.parse_simple_yaml_list(ROOT / "registry" / "agents.yaml", "agents")
        roles = self.validate.parse_simple_yaml_list(ROOT / "registry" / "roles.yaml", "roles")
        agents_by_id = {item["id"]: item for item in agents}
        roles_by_id = {item["id"]: item for item in roles}

        self.assertIn("personal-assistant", agents_by_id)
        self.assertIn("personal/personal-assistant", roles_by_id)

        personal_agent = agents_by_id["personal-assistant"]
        personal_role = roles_by_id["personal/personal-assistant"]
        personal_skills = self.validate.split_csv(personal_agent["skills"])

        self.assertEqual(personal_agent["domain"], "personal")
        self.assertEqual(personal_role["domain"], "personal")
        self.assertIn("obsidian-kanban", personal_skills)
        self.assertIn("obsidian-cli", personal_skills)
        self.assertNotIn("obsidian-bases", personal_skills)
        self.assertNotIn("json-canvas", personal_skills)

        role_text = (ROOT / personal_role["path"]).read_text(encoding="utf-8")
        self.assertIn("Kanban-first workflow", role_text)

        orchestrator = (ROOT / "roles" / "orchestrator.yaml").read_text(encoding="utf-8")
        self.assertIn("personal:", orchestrator)
        self.assertIn("personal/personal-assistant", orchestrator)

    def test_personal_assistant_boundary_is_bidirectional(self):
        knowledge_manager = (ROOT / "agents" / "docs" / "knowledge-manager.md").read_text(encoding="utf-8")
        project_manager = (ROOT / "agents" / "project" / "project-manager.md").read_text(encoding="utf-8")
        doc_writer = (ROOT / "agents" / "docs" / "doc-writer.md").read_text(encoding="utf-8")
        orchestrator = (ROOT / "agents" / "orchestrator.md").read_text(encoding="utf-8")

        self.assertIn("personal-assistant", knowledge_manager)
        self.assertIn("personal-assistant", project_manager)
        self.assertIn("personal-assistant", doc_writer)
        self.assertIn("personal execution", orchestrator)

    def test_personal_assistant_exposes_default_board_and_invocation_examples(self):
        personal_agent = (ROOT / "agents" / "personal" / "personal-assistant.md").read_text(encoding="utf-8")
        invocation = (ROOT / "docs" / "invocation.md").read_text(encoding="utf-8")

        for column in ["Inbox", "Next", "Scheduled", "Projects", "Waiting", "Someday", "Done"]:
            with self.subTest(column=column):
                self.assertIn(column, personal_agent)

        self.assertIn("/ark-space:orchestrator help me run my weekly planning board", invocation)
        self.assertIn("/ark-space:orchestrator capture these personal tasks into my Obsidian Kanban", invocation)

    def test_personal_assistant_includes_first_session_example(self):
        personal_agent = (ROOT / "agents" / "personal" / "personal-assistant.md").read_text(encoding="utf-8")

        self.assertIn("## First Session Example", personal_agent)
        self.assertIn("I need to renew my passport next month", personal_agent)
        self.assertIn("Personal website refresh", personal_agent)
        self.assertIn("Recommended next action", personal_agent)

    def test_personal_assistant_includes_weekly_planning_and_inbox_triage_guides(self):
        personal_agent = (ROOT / "agents" / "personal" / "personal-assistant.md").read_text(encoding="utf-8")

        self.assertIn("## Weekly Planning", personal_agent)
        self.assertIn("## Inbox Triage", personal_agent)
        self.assertIn("move real projects into `Projects`", personal_agent)
        self.assertIn("turn at least one active project into a visible next action in `Next`", personal_agent)

    def test_embeds_reference_includes_base_embed_example(self):
        embeds = (ROOT / "skills" / "obsidian-markdown" / "references" / "EMBEDS.md").read_text(encoding="utf-8")

        self.assertIn("## Embed Bases", embeds)
        self.assertIn("![[Example.base]]", embeds)

    def test_tavily_extended_capabilities_are_provider_registered(self):
        expectations = {
            "search-providers.yaml": ("web-search", "web_search"),
            "web-fetch-providers.yaml": ("web-fetch", "web_fetch"),
            "web-map-providers.yaml": ("web-site", "web_map"),
            "web-crawl-providers.yaml": ("web-site", "web_crawl"),
            "deep-research-providers.yaml": ("web-research", "deep_research"),
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
            "search-providers.yaml": ("web-search", "web_search"),
            "web-fetch-providers.yaml": ("web-fetch", "web_fetch"),
            "deep-research-providers.yaml": ("web-research", "deep_research"),
            "code-context-providers.yaml": ("code-context", "code_context"),
            "related-page-providers.yaml": ("web-search", "related_pages"),
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

        self.assertEqual(arxiv.get("skill"), "web-search")
        self.assertEqual(arxiv.get("capability"), "web_search")
        self.assertEqual(arxiv.get("configRequired"), "false")
        self.assertIn("--capability web_search", arxiv.get("checkCommand", ""))
        self.assertIn("docs/web-researcher", arxiv.get("roles", ""))

    def test_firecrawl_capabilities_are_provider_registered(self):
        expectations = {
            "search-providers.yaml": ("web-search", "web_search"),
            "web-fetch-providers.yaml": ("web-fetch", "web_fetch"),
            "web-map-providers.yaml": ("web-site", "web_map"),
            "web-crawl-providers.yaml": ("web-site", "web_crawl"),
            "structured-extract-providers.yaml": ("web-extract", "structured_extract"),
            "web-interact-providers.yaml": ("web-automation", "web_interact"),
            "web-monitor-providers.yaml": ("web-automation", "web_monitor"),
        }
        for registry_name, (skill, capability) in expectations.items():
            with self.subTest(registry=registry_name):
                providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / registry_name, "providers")
                firecrawl = next(item for item in providers if item.get("id") == "firecrawl")
                self.assertEqual(firecrawl.get("skill"), skill)
                self.assertEqual(firecrawl.get("capability"), capability)
                self.assertIn(f"--capability {capability}", firecrawl.get("checkCommand", ""))
                self.assertIn("provider setup firecrawl --wizard", firecrawl.get("providerConfigCommand", ""))

    def test_firecrawl_search_and_fetch_are_keyless_other_capabilities_required(self):
        keyless = {"search-providers.yaml", "web-fetch-providers.yaml"}
        required = {
            "web-map-providers.yaml",
            "web-crawl-providers.yaml",
            "structured-extract-providers.yaml",
            "web-interact-providers.yaml",
            "web-monitor-providers.yaml",
        }
        for registry_name in keyless | required:
            with self.subTest(registry=registry_name):
                providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / registry_name, "providers")
                firecrawl = next(item for item in providers if item.get("id") == "firecrawl")
                if registry_name in keyless:
                    self.assertEqual(firecrawl.get("configRequired"), "false")
                else:
                    self.assertEqual(firecrawl.get("configRequired"), "true")

    def test_new_keyless_and_keyed_providers_are_provider_registered(self):
        providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / "search-providers.yaml", "providers")
        by_id = {item.get("id"): item for item in providers}
        for provider_id in KEYLESS_WEB_SEARCH_PROVIDERS:
            with self.subTest(provider=provider_id):
                item = by_id[provider_id]
                self.assertEqual(item.get("skill"), "web-search")
                self.assertEqual(item.get("capability"), "web_search")
                self.assertEqual(item.get("status"), "active")
                self.assertEqual(item.get("configRequired"), "false")
                self.assertIn("docs/web-researcher", item.get("roles", ""))
        for provider_id in KEYED_WEB_SEARCH_PROVIDERS:
            with self.subTest(provider=provider_id):
                item = by_id[provider_id]
                self.assertEqual(item.get("skill"), "web-search")
                self.assertEqual(item.get("capability"), "web_search")
                self.assertEqual(item.get("status"), "active")
                self.assertEqual(item.get("configRequired"), "true")
                self.assertEqual(item.get("explicitOnly"), "false")
                self.assertIn("docs/web-researcher", item.get("roles", ""))

    def test_new_search_providers_have_check_dispatch(self):
        arkspace = load_arkspace_module()
        for provider_id in KEYLESS_WEB_SEARCH_PROVIDERS + KEYED_WEB_SEARCH_PROVIDERS:
            with self.subTest(provider=provider_id):
                self.assertIn((provider_id, "web_search"), arkspace.PROVIDER_CHECK_COMMANDS)
                self.assertIn(provider_id, arkspace.WEB_SEARCH_COMMANDS)

    def test_new_search_providers_have_adapters_referencing_sources_and_files(self):
        adapters = self.validate.parse_simple_yaml_list(ROOT / "registry" / "provider-adapters.yaml", "adapters")
        sources = self.validate.parse_simple_yaml_list(ROOT / "registry" / "sources.yaml", "sources")
        source_ids = {item.get("id") for item in sources if item.get("id")}
        for provider_id in KEYLESS_WEB_SEARCH_PROVIDERS + KEYED_WEB_SEARCH_PROVIDERS:
            with self.subTest(provider=provider_id):
                matches = [a for a in adapters if a.get("provider") == provider_id and a.get("capability") == "web_search"]
                self.assertEqual(len(matches), 1, f"expected one adapter for {provider_id}/web_search")
                adapter = matches[0]
                self.assertIn(adapter.get("sourceId"), source_ids)
                self.assertTrue((ROOT / adapter["implementation"]).is_file())

    def test_default_search_policy_belongs_to_allow_list(self):
        text = (ROOT / "registry" / "search-providers.yaml").read_text(encoding="utf-8")
        match = re.search(r"^defaultSearchPolicy:\s*(\S+)$", text, re.MULTILINE)
        policy = match.group(1) if match else ""
        self.assertIn(policy, SEARCH_POLICY_ALLOW_LIST)

    def test_provider_priorities_are_integers_in_documented_range(self):
        providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / "search-providers.yaml", "providers")
        for item in providers:
            priority = str(item.get("priority", "")).strip()
            self.assertTrue(
                priority.isdigit(),
                f"provider {item.get('id')} priority must be an integer, got {item.get('priority')!r}",
            )
            self.assertIn(int(priority), PRIORITY_RANGE, f"provider {item.get('id')} priority {priority} out of range")

    def test_explicit_only_is_boolean_like_and_duckduckgo_is_true(self):
        providers = self.validate.parse_simple_yaml_list(ROOT / "registry" / "search-providers.yaml", "providers")
        by_id = {item.get("id"): item for item in providers}
        for item in providers:
            if "explicitOnly" in item:
                value = item["explicitOnly"]
                self.assertIn(str(value).strip().lower(), {"true", "false"}, f"explicitOnly must be boolean-like for {item.get('id')}")
        self.assertIn(str(by_id["duckduckgo"]["explicitOnly"]).strip().lower(), {"true"})

    def test_runtime_instructions_use_installed_arkspace_path(self):
        runtime_paths = [
            ROOT / "registry" / "search-providers.yaml",
            ROOT / "registry" / "web-fetch-providers.yaml",
            ROOT / "registry" / "code-context-providers.yaml",
            ROOT / "registry" / "related-page-providers.yaml",
            ROOT / "skills" / "provider-manager" / "SKILL.md",
            ROOT / "skills" / "web-search" / "SKILL.md",
            ROOT / "skills" / "web-fetch" / "SKILL.md",
            ROOT / "skills" / "web-site" / "SKILL.md",
            ROOT / "skills" / "web-research" / "SKILL.md",
            ROOT / "skills" / "web-extract" / "SKILL.md",
            ROOT / "skills" / "web-automation" / "SKILL.md",
            ROOT / "skills" / "code-context" / "SKILL.md",
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

    def test_canonical_provider_skills_delegate_setup_to_provider_manager(self):
        for skill_name in [
            "web-search",
            "web-fetch",
            "web-site",
            "web-research",
            "web-extract",
            "web-automation",
            "code-context",
        ]:
            with self.subTest(skill=skill_name):
                text = (ROOT / "skills" / skill_name / "SKILL.md").read_text(encoding="utf-8")
                self.assertIn("provider-manager", text)
                self.assertIn("<installed-arkspace-path>", text)

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

    def test_skill_description_quality_rejects_placeholders_and_generic_text(self):
        path = ROOT / "skills" / "example" / "SKILL.md"

        with self.assertRaises(SystemExit):
            self.validate.validate_skill_description_quality(path, "Use this skill.")

        with self.assertRaises(SystemExit):
            self.validate.validate_skill_description_quality(
                path,
                "Use when handling this placeholder skill for a future workflow that is TODO.",
            )

        with self.assertRaises(SystemExit):
            self.validate.validate_skill_description_quality(
                path,
                "This capability provides a reusable package of instructions for an assistant.",
            )

        self.validate.validate_skill_description_quality(
            path,
            "Use when searching technical documentation through ArkSpace routing and returning compact source evidence.",
        )

    def test_web_capability_routing_contract_is_authoritative_and_distinct(self):
        expected = {
            "web-fetch": ("supplied URL", "readable content"),
            "web-extract": ("fields", "schema"),
            "web-research": ("multiple public sources", "cited"),
            "web-site": ("known site", "map", "crawl"),
            "web-automation": ("interact", "monitor"),
        }
        for skill, terms in expected.items():
            with self.subTest(skill=skill):
                text = (ROOT / "skills" / skill / "SKILL.md").read_text(encoding="utf-8").lower()
                for term in terms:
                    self.assertIn(term.lower(), text)

        fetch = (ROOT / "skills" / "web-fetch" / "SKILL.md").read_text(encoding="utf-8").lower()
        extract = (ROOT / "skills" / "web-extract" / "SKILL.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("when extracting readable", fetch)
        self.assertIn("structured fields", extract)
        self.assertIn("schema", extract)

        workflow = (ROOT / "workflows" / "web-capability-routing.md").read_text(encoding="utf-8")
        decision_rows = [
            "find sources/pages -> web-search",
            "read supplied URL(s) -> web-fetch",
            "extract requested fields/schema from supplied URL(s) -> web-extract",
            "synthesize cited answer across sources -> web-research",
            "discover/crawl a known site -> web-site",
            "interact or manage monitors -> web-automation",
        ]
        for row in decision_rows:
            with self.subTest(row=row):
                self.assertEqual(workflow.count(row), 1)
        workflow_lower = workflow.lower()
        self.assertIn("skill-level provider omission is allowed after capability resolution", workflow_lower)
        self.assertIn("raw cli receives explicit `--provider`", workflow_lower)
        self.assertIn("monitor mutation requires confirmation", workflow_lower)

    def test_web_researcher_defers_capability_branches_to_authoritative_workflow(self):
        text = (ROOT / "agents" / "docs" / "web-researcher.md").read_text(encoding="utf-8")
        web_work = text.split("## Web Work", 1)[1].split("## Decision Rules", 1)[0]
        decision_rules = text.split("## Decision Rules", 1)[1].split("## Output", 1)[0]

        pointer = "For web capability routing, follow `workflows/web-capability-routing.md` before provider selection."
        self.assertEqual(web_work.count(pointer), 1)
        self.assertLess(web_work.index(pointer), web_work.index("Prefer arXiv"))
        self.assertNotIn("the workflow selects the distinct", web_work)
        self.assertNotRegex(decision_rules, r"Execute directly for .*source discovery")
        self.assertNotIn("Use a provider workflow before execution", decision_rules)
        decision_rule_lines = [line for line in decision_rules.splitlines() if line.startswith("- ")]
        self.assertTrue(
            all(line.startswith(("- Hand off", "- Stop and report")) for line in decision_rule_lines),
            "Decision Rules must contain role-specific exceptions, not capability execution branches.",
        )

    def test_public_skill_contract_requires_capabilities_and_categories(self):
        self.validate.find_readme_included_skill_names = lambda: {"example"}  # type: ignore[reportAttributeAccessIssue]

        missing_capabilities = [
            {
                "name": "example",
                "status": "active",
                "public": "true",
                "directInvocation": "/ark-space:example run",
                "categories": "meta",
                "roles": "orchestrator",
            }
        ]
        with self.assertRaises(SystemExit):
            self.validate.validate_public_skill_contract(missing_capabilities)

        missing_categories = [
            {
                "name": "example",
                "status": "active",
                "public": "true",
                "directInvocation": "/ark-space:example run",
                "capabilities": "routing",
                "orchestratorInvocation": "/ark-space:orchestrator run example",
                "roles": "orchestrator",
            }
        ]
        with self.assertRaises(SystemExit):
            self.validate.validate_public_skill_contract(missing_categories)


if __name__ == "__main__":
    unittest.main()
