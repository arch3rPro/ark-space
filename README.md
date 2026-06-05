# ArkSpace

ArkSpace is a creative workspace for orchestrating agent skills, roles, and workflows across Claude Code and Codex, with a standard `skills/` tree that can be reused by compatible hosts.

This repository packages reusable skills, role definitions, and source-governance metadata for agent work across coding, documentation, product, project, and knowledge-management tasks. The default entry point is a lightweight Orchestrator role that routes work to the smallest useful role and workflow instead of forcing a heavy process on every request.

## Project Shape

```text
.
+-- skills/              # Canonical Agent Skills: skills/<name>/SKILL.md
+-- roles/               # Role definitions that compose skills by work type
+-- registry/            # Skill, role, and upstream source governance
+-- .claude-plugin/      # Claude Code plugin metadata
+-- .codex-plugin/       # Codex plugin metadata
+-- docs/                # Architecture and maintenance docs
+-- overlays/            # Public examples for private local customization
+-- scripts/             # Validation and maintenance scripts
+-- reference/           # Optional local or tracked upstream references
```

The canonical skill source is always `skills/<skill-name>/SKILL.md`. Platform manifests should point to that shared `skills/` tree instead of maintaining Claude-specific or Codex-specific skill copies.

## Core Concepts

### Orchestrator

`orchestrator` is the default role. It performs lightweight routing:

- Identify the task domain: code, docs, product, project, skills, or knowledge management.
- Pick the smallest useful role and skill set.
- Escalate to design-first work only when the task is cross-domain, structurally risky, or unclear.
- Hand skill-library maintenance to `skill-manager`.

### Skill Manager

`skill-manager` governs the package:

- Create skills under `skills/<skill-name>/SKILL.md`.
- Record upstream provenance in `registry/sources.yaml`.
- Assign skills to roles.
- Keep registries and manifests valid.
- Guide mirror, adapted, local, and reference-only update decisions.

### Roles

Roles live under `roles/` and describe reusable bundles of skills. They do not duplicate skill content.

| Role | Purpose |
|---|---|
| `orchestrator` | Default lightweight routing entry point |
| `code/code-engineer` | Implementation, refactoring, testing, debugging |
| `code/code-reviewer` | Bug, regression, and test-gap review |
| `code/repo-maintainer` | Repository hygiene and release-adjacent checks |
| `docs/doc-writer` | New documentation |
| `docs/doc-editor` | Documentation improvement |
| `docs/knowledge-manager` | Obsidian, notes, Bases, Canvas, Kanban, web extraction |
| `product/prd-planner` | Requirements, scope, acceptance criteria |
| `product/demo-designer` | Product demos and realistic demo flows |
| `product/competitive-analyst` | Competitor and market comparison |
| `project/project-manager` | Milestones, tasks, risks, tracking |
| `project/delivery-coordinator` | Handoffs, status, and delivery coordination |
| `skills/skill-manager` | Skill lifecycle and registry governance |

## Included Skills

| Skill | Purpose |
|---|---|
| `orchestrator` | Route work to the smallest useful role and workflow |
| `skill-manager` | Manage skill lifecycle, registries, sources, and role ownership |
| `defuddle` | Extract clean Markdown from web pages |
| `searxng-search` | Query self-hosted SearXNG or public fallback instances |
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

### Codex

Use `.codex-plugin/plugin.json`. The Codex manifest points to:

```json
"skills": "./skills/"
```

### Manual Skills Install

For any host that supports the standard Agent Skills layout, copy or link the `skills/` directory into the host's skills directory.

## Governance

Registries under `registry/` are the source of truth for package metadata:

- `registry/skills.yaml`: skills, paths, sync modes, categories, and role ownership.
- `registry/roles.yaml`: role IDs, paths, domains, and default role.
- `registry/sources.yaml`: upstream repositories and source policies.
- `registry/search-providers.yaml`: search-provider selection metadata for compatible search skills.
- `registry/web-fetch-providers.yaml`: URL fetch/extraction provider metadata for compatible fetch skills.

Supported source policies:

| Mode | Meaning |
|---|---|
| `mirror` | Keep close to upstream |
| `adapted` | Selectively merge upstream changes after local adaptation |
| `local` | Maintain directly in this repository |
| `reference-only` | Use as design reference, not as a published local skill |

Run validation after changing skills, roles, registries, manifests, README, or agent guidance:

```bash
python3 scripts/validate-skills.py
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
- Do not create separate Claude/Codex skill copies.
- Do not publish, tag, push releases, or run version workflows unless explicitly requested.
- Preserve upstream attribution and license requirements when importing or adapting skills.
- Treat `reference/` as optional design/reference material; do not rely on it for runtime behavior.
