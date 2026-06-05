# Agent Skills

A general-purpose Agent Skills collection for lightweight role routing, skill management, and reusable workflows across coding, documentation, product, project, and knowledge-management work.

The repository follows the Agent Skills package shape with skills under `skills/<skill-name>/SKILL.md`. Claude Code and Codex use the same canonical `skills/` directory.

## What Is Included

- `orchestrator`: routes work to the smallest useful role and workflow.
- `skill-manager`: manages skill creation, source governance, role assignment, and validation.
- Code roles: engineering, review, and repository maintenance.
- Documentation roles: writing, editing, and knowledge management.
- Product roles: PRD planning, demo design, and competitive analysis.
- Project roles: planning and delivery coordination.
- Existing Obsidian skills retained as knowledge-management tools.

## Installation

### Claude Code

Use the Claude plugin files in `.claude-plugin/`.

For local development, install this repository as a Claude Code plugin according to Claude Code's local plugin workflow.

### Codex

Use the Codex plugin manifest in `.codex-plugin/plugin.json`.

The Codex manifest points to:

```json
"skills": "./skills/"
```

### Manual Skills Install

Copy or link the `skills/` directory into any Agent Skills-compatible host that supports the standard `skills/<skill-name>/SKILL.md` layout.

## Roles

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

## Skills

| Skill | Purpose |
|---|---|
| `orchestrator` | Lightweight role and workflow routing |
| `skill-manager` | Skill creation, registry, source, and role governance |
| `defuddle` | Extract clean Markdown from web pages |
| `json-canvas` | Create and edit JSON Canvas files |
| `obsidian-bases` | Create and edit Obsidian Bases |
| `obsidian-cli` | Interact with Obsidian through the CLI |
| `obsidian-kanban` | Create and maintain Obsidian Kanban boards |
| `obsidian-markdown` | Create and edit Obsidian-flavored Markdown |

## Governance

Skill source and role ownership are tracked in `registry/`.

Supported sync modes:

- `mirror`: keep close to upstream.
- `adapted`: selectively merge upstream changes.
- `local`: maintain directly in this repository.
- `reference-only`: use as design reference, not as a published local skill.

Run validation after changing skills, roles, registries, or plugin manifests:

```bash
python3 scripts/validate-skills.py
```

## Personal Overlays

The public package stays reusable. Personal and private configuration belongs in ignored overlay files under `overlays/`.

See `overlays/README.md` for details.
