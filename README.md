# ArkSpace

ArkSpace is a creative workspace for orchestrating agent skills, callable roles, and workflows across Claude Code and Codex, with a standard `skills/` tree that can be reused by compatible hosts.

This repository packages reusable skills, callable agent roles, workflow protocols, generated host integrations, and source-governance metadata for agent work across coding, documentation, product, project, and knowledge-management tasks. The default entry point is a lightweight Orchestrator that routes work to the smallest useful role and workflow instead of forcing a heavy process on every request.

## Project Shape

```text
.
+-- skills/              # Canonical Agent Skills: skills/<name>/SKILL.md
+-- agents/              # Callable role sources shared by host adapters
+-- workflows/           # Routing, handoff, quality, and provider protocols
+-- integrations/        # Generated host-native agent outputs
+-- roles/               # Existing role metadata kept during migration
+-- registry/            # Skill, agent, workflow, provider, and source governance
+-- .agents/plugins/     # Codex marketplace catalog for GitHub marketplace add
+-- .claude-plugin/      # Claude Code plugin metadata
+-- .codex-plugin/       # Codex plugin metadata
+-- docs/                # Architecture and maintenance docs
+-- overlays/            # Public examples for private local customization
+-- scripts/             # Validate, convert, install, doctor, provider setup
+-- reference/           # Optional local or tracked upstream references
```

The canonical skill source is always `skills/<skill-name>/SKILL.md`. Callable role sources live in `agents/`. Platform manifests and generated integrations should point to shared sources instead of maintaining Claude-specific or Codex-specific skill bodies.

## Core Concepts

### Orchestrator

`orchestrator` is the default skill and `agents/orchestrator.md` is the default callable role. Together they perform lightweight routing:

- Identify the task domain: code, docs, product, project, skills, or knowledge management.
- Pick the smallest useful callable agent and skill set.
- Escalate to design-first work only when the task is cross-domain, structurally risky, or unclear.
- Hand skill-library maintenance to `skill-manager`.

### Skill Manager

`skill-manager` governs the package:

- Create skills under `skills/<skill-name>/SKILL.md`.
- Record upstream provenance in `registry/sources.yaml`.
- Assign skills to roles.
- Keep registries and manifests valid.
- Guide mirror, adapted, local, and reference-only update decisions.

### Callable Agents

Callable agents live under `agents/` and describe runtime role behavior. They compose skills and workflows without duplicating skill bodies. Existing `roles/` YAML files are retained as migration metadata.

| Agent | Purpose |
|---|---|
| `agents/orchestrator.md` | Default lightweight routing entry point |
| `agents/code/code-engineer.md` | Implementation, refactoring, testing, debugging |
| `agents/code/code-reviewer.md` | Bug, regression, and test-gap review |
| `agents/docs/doc-writer.md` | Documentation writing and improvement |
| `agents/docs/knowledge-manager.md` | Obsidian, notes, search, fetch, and knowledge work |
| `agents/product/prd-planner.md` | Requirements, scope, acceptance criteria |
| `agents/product/competitive-analyst.md` | Competitor, product, and market evidence |
| `agents/project/project-manager.md` | Milestones, tasks, risks, tracking |
| `agents/skills/skill-manager.md` | Skill and agent lifecycle governance |

### Workflows

Workflows live under `workflows/` and define reusable protocols for routing, handoffs, quality gates, and provider capabilities. Agents reference workflows when the task needs structure beyond a single direct response.

### Host Integrations

Host-native agent files are generated under `integrations/`:

```bash
python3 scripts/arkspace.py convert --host all
python3 scripts/arkspace.py install --host codex --dry-run
python3 scripts/arkspace.py install --host claude-code --dry-run
python3 scripts/arkspace.py doctor
```

Do not edit generated integration files by hand; update `agents/` and regenerate.

## Included Skills

| Skill | Purpose |
|---|---|
| `orchestrator` | Route work to the smallest useful role and workflow |
| `skill-manager` | Manage skill lifecycle, registries, sources, and role ownership |
| `provider-manager` | Configure and inspect provider URLs, key references, and readiness |
| `defuddle` | Extract clean Markdown from web pages |
| `searxng-search` | Query a configured self-hosted SearXNG instance |
| `json-canvas` | Create and edit JSON Canvas files |
| `obsidian-bases` | Create and edit Obsidian Bases |
| `obsidian-cli` | Interact with Obsidian through the CLI |
| `obsidian-kanban` | Create and maintain Obsidian Kanban boards |
| `obsidian-markdown` | Create and edit Obsidian-flavored Markdown |

The Obsidian-related skills are retained as documentation and knowledge-management tools. They no longer define the identity of the whole package.

## Installation

### Claude Code

Use the plugin metadata under `.claude-plugin/`.

For local development, install this repository as a Claude Code plugin according to Claude Code's local plugin workflow. The plugin uses the shared `skills/` directory.

Generate and dry-run install callable agents:

```bash
python3 scripts/arkspace.py convert --host claude-code
python3 scripts/arkspace.py install --host claude-code --dry-run
```

Personal provider configuration should live outside committed package files. The recommended ArkSpace setup is:

```bash
python3 scripts/arkspace_provider.py configure searxng --base-url "https://searx.example.org"
python3 skills/searxng-search/scripts/searxng_search.py --check
```

Claude Code can also pass provider variables from `.claude/settings.local.json`:

```json
{
  "env": {
    "SEARXNG_URL": "https://searx.example.org"
  }
}
```

### Codex

Use `.codex-plugin/plugin.json`. The Codex manifest points to:

```json
"skills": "./skills/"
```

Generate and dry-run install callable agents:

```bash
python3 scripts/arkspace.py convert --host codex
python3 scripts/arkspace.py install --host codex --dry-run
```

For Codex, use the same ArkSpace setup command, or export provider variables in the shell that launches Codex and make sure `shell_environment_policy` forwards them:

```bash
export SEARXNG_URL="https://searx.example.org"
codex
```

For the SearXNG skill, the persistent setup uses ArkSpace provider config:

```bash
python3 scripts/arkspace_provider.py configure searxng --base-url "https://searx.example.org"
python3 scripts/arkspace_provider.py resolve searxng --capability web_search
```

This writes `~/.config/ark-space/providers.json` by default. Use `ARKSPACE_PROVIDER_CONFIG` or `--config-path` for a custom location. `--base-url` and environment variables still override the saved value.

To add this repository as a Codex plugin marketplace:

```bash
codex plugin marketplace add arch3rPro/ark-space --ref main
```

Then restart Codex and install `ark-space` from the `ArkSpace` marketplace source. The Codex marketplace catalog lives at `.agents/plugins/marketplace.json`; `.codex-plugin/plugin.json` is the plugin manifest itself. The marketplace entry points at the repository root so Codex caches real plugin files rather than symlink wrappers.

If an older broken marketplace snapshot already exists, refresh it:

```bash
codex plugin marketplace upgrade ark-space
codex plugin list --marketplace ark-space
codex plugin add ark-space@ark-space
```

### Manual Skills Install

For any host that supports the standard Agent Skills layout, copy or link the `skills/` directory into the host's skills directory.

## Governance

Registries under `registry/` are the source of truth for package metadata:

- `registry/skills.yaml`: skills, paths, sync modes, categories, and role ownership.
- `registry/agents.yaml`: callable agent paths, domains, skills, workflows, and host targets.
- `registry/workflows.yaml`: workflow protocol paths and ownership.
- `registry/roles.yaml`: role IDs, paths, domains, and default role.
- `registry/sources.yaml`: upstream repositories and source policies.
- `registry/search-providers.yaml`: search-provider selection metadata for compatible search skills.
- `registry/web-fetch-providers.yaml`: URL fetch/extraction provider metadata for compatible fetch skills.

Provider registries should declare configuration metadata such as recommended environment variables, check commands, missing-configuration behavior, privacy posture, authentication modes, and key rotation support. Skills should check and explain configuration at runtime; host settings, environment variables, or ArkSpace user config store the actual values.

Use `provider-manager` and `scripts/arkspace_provider.py` for guided setup. For API-backed providers, ArkSpace config stores key references such as `env:BRAVE_API_KEY_1`; actual keys stay in the host environment or secret manager. See `docs/provider-configuration.md`.

Supported source policies:

| Mode | Meaning |
|---|---|
| `mirror` | Keep close to upstream |
| `adapted` | Selectively merge upstream changes after local adaptation |
| `local` | Maintain directly in this repository |
| `reference-only` | Use as design reference, not as a published local skill |

Run validation after changing skills, roles, registries, manifests, README, or agent guidance:

```bash
python3 scripts/arkspace.py doctor
```

## Project Documents

- `CHANGELOG.md`: notable project changes.
- `CONTRIBUTING.md`: contribution workflow and validation requirements.
- `CODE_OF_CONDUCT.md`: participation standards.
- `SECURITY.md`: vulnerability reporting and security scope.
- `SUPPORT.md`: support request guidance.
- `NOTICE.md`: upstream attribution and source notices.

## Personal Overlays

The public package should stay reusable. Personal workflows, private repositories, internal tools, and company-specific preferences belong in ignored overlay files:

```text
overlays/personal.yaml
overlays/private-skills.yaml
```

Commit only examples and documentation under `overlays/`. See `overlays/README.md`.

## Development Notes

- Keep skill bodies host-neutral when possible.
- Keep callable role behavior in `agents/`.
- Do not create separate Claude/Codex skill copies.
- Do not edit generated `integrations/` by hand; regenerate from `agents/`.
- Keep process specs and plans under ignored `docs/superpowers/` when needed locally; do not commit them.
- Do not publish, tag, push releases, or run version workflows unless explicitly requested.
- Preserve upstream attribution and license requirements when importing or adapting skills.
- Treat `reference/` as optional design/reference material; do not rely on it for runtime behavior.
