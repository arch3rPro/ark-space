# General Agent Skills Package Design

## Status

Approved for design documentation on 2026-06-05.

## Goal

Transform this repository from an Obsidian-focused skills collection into a general-purpose Agent Skills package that supports multiple agent roles, multiple host tools, and long-term skill source governance.

The package should serve both public reuse and personal extension:

- Public core: reusable skills, roles, registries, platform manifests, and documentation that can be published.
- Personal overlay: local/private configuration for personal preferences, private skills, and internal tools without mixing them into the public core.

## Non-Goals

Phase 1 will not:

- Implement full GitHub upstream sync automation.
- Split every role into a separate plugin.
- Migrate to multiple repositories.
- Delete existing Obsidian skills.
- Publish, tag, push releases, or run version workflows.
- Promise complete support for OpenCode, Gemini, Cursor, or other future hosts.

## Design Principles

Keep one canonical skill source. Skills remain in the standard `skills/<skill-name>/SKILL.md` shape and are shared by all supported hosts.

Keep platform logic thin. Claude Code and Codex manifests are responsible for installation and presentation, not business logic.

Route lightly. The default Orchestrator role should choose the smallest useful role and workflow instead of forcing a heavy process on every task.

Separate source governance from skill content. Registries track upstream repositories, sync policies, role ownership, and status without duplicating the skill bodies.

Preserve existing value. Current Obsidian skills stay available, but they become part of the documentation and knowledge-management area instead of defining the whole repository identity.

## Target Repository Structure

```text
.
+-- README.md
+-- LICENSE
+-- .claude-plugin/
|   +-- plugin.json
|   +-- marketplace.json
+-- .codex-plugin/
|   +-- plugin.json
+-- skills/
|   +-- orchestrator/
|   +-- skill-manager/
|   +-- defuddle/
|   +-- obsidian-markdown/
|   +-- ...
+-- roles/
|   +-- orchestrator.yaml
|   +-- code/
|   +-- docs/
|   +-- product/
|   +-- project/
+-- registry/
|   +-- skills.yaml
|   +-- roles.yaml
|   +-- sources.yaml
+-- overlays/
|   +-- README.md
|   +-- personal.example.yaml
+-- scripts/
|   +-- validate-skills.sh
|   +-- generate-readme.sh
|   +-- sync-upstreams.sh
+-- docs/
|   +-- architecture.md
|   +-- adding-skills.md
|   +-- platform-support.md
+-- reference/
    +-- superpowers/
```

## Core Role: Orchestrator

The Orchestrator is the default entry role. It is a lightweight router, not a super-role that performs all work itself.

Responsibilities:

- Identify whether a task belongs to code, documents, product, project, knowledge management, skill management, or multiple domains.
- Select the smallest useful role set.
- Decide whether the task can be handled directly or needs design-first handling.
- Hand off to `skill-manager` for skill library maintenance tasks.
- Ask one focused question when the routing decision is unclear.

Default rule:

```text
Use the lightest role and workflow that can safely complete the task.

Route first by user intent, then by artifact type, then by risk.
Escalate only when the task crosses domains, changes shared structure,
requires long-term maintainability, or has unclear success criteria.
```

The Orchestrator has two artifacts:

- `roles/orchestrator.yaml`: role metadata, routes, default mode, and supported domains.
- `skills/orchestrator/SKILL.md`: routing behavior, escalation rules, handoff formats, and host-neutral instructions.

## Role Model

Roles describe reusable bundles of skills and routing intent. They do not copy skill content.

Initial role tree:

```text
Orchestrator
+-- Code Roles
|   +-- code-engineer
|   +-- code-reviewer
|   +-- repo-maintainer
+-- Docs Roles
|   +-- doc-writer
|   +-- doc-editor
|   +-- knowledge-manager
+-- Product Roles
|   +-- prd-planner
|   +-- demo-designer
|   +-- competitive-analyst
+-- Project Roles
    +-- project-manager
    +-- delivery-coordinator
```

Example role file:

```yaml
name: code-engineer
description: Build, refactor, test, and debug software projects.
skills:
  - orchestrator
  - systematic-debugging
  - verification-before-completion
platforms:
  claude-code: true
  codex: true
```

## Skill Source Governance

The project supports four source strategies:

| syncMode | Meaning |
|---|---|
| `mirror` | High-quality external skill, kept as close to upstream as possible. |
| `adapted` | External skill modified for this repository, updated selectively. |
| `local` | Skill created and maintained in this repository. |
| `reference-only` | Upstream used as design reference, not published as a local skill. |

Source types:

- Reused high-quality skills: record GitHub upstream and current imported state, use `mirror` when practical.
- Adapted project skills: record GitHub upstream, but mark `adapted` and merge selectively.
- Locally created skills: mark `local` and maintain directly.

## Registry Model

`registry/skills.yaml` records skill identity, path, source strategy, categories, and role membership.

```yaml
skills:
  - name: orchestrator
    path: skills/orchestrator
    status: active
    source:
      type: local
    syncMode: local
    categories: [meta, routing]
    roles: [orchestrator]

  - name: obsidian-markdown
    path: skills/obsidian-markdown
    status: active
    source:
      type: adapted
      upstreamId: obsidian-skills
      upstreamPath: skills/obsidian-markdown
    syncMode: adapted
    categories: [docs, knowledge]
    roles: [docs/knowledge-manager]
```

`registry/sources.yaml` records upstream repositories once.

```yaml
sources:
  - id: obsidian-skills
    type: github
    repo: arch3rPro/obsidian-skills
    upstreamRepo: kepano/obsidian-skills
    license: MIT
    syncPolicy: adapted
    notes: "Existing Obsidian skills retained as knowledge-management tools."

  - id: superpowers
    type: github
    repo: obra/superpowers
    license: MIT
    syncPolicy: reference-only
    localPath: reference/superpowers
```

`registry/roles.yaml` records the role tree and default entry role.

```yaml
defaultRole: orchestrator

roles:
  - id: orchestrator
    path: roles/orchestrator.yaml
    domain: meta
    default: true
    routes:
      - code/code-engineer
      - docs/doc-writer
      - product/prd-planner
      - project/project-manager
      - skills/skill-manager

  - id: docs/knowledge-manager
    path: roles/docs/knowledge-manager.yaml
    domain: docs
    skills:
      - obsidian-markdown
      - obsidian-bases
      - json-canvas
      - obsidian-kanban
      - defuddle
```

## Skill Manager

`skills/skill-manager/SKILL.md` is the governance skill for this repository.

Responsibilities:

- Create a new skill under `skills/<name>/SKILL.md`.
- Validate required skill frontmatter, especially `name` and `description`.
- Add or update entries in `registry/skills.yaml`.
- Add or update upstream references in `registry/sources.yaml`.
- Assign skills to roles.
- Detect missing files, missing registry entries, and broken role references.
- Help generate README skill and role summaries.
- Guide upstream update decisions for `mirror`, `adapted`, `local`, and `reference-only` skills.

Phase 1 behavior is advisory and validation-oriented. It should not attempt complex automatic GitHub synchronization.

## Platform Support

Phase 1 targets Claude Code and Codex.

Claude Code:

- Keep `.claude-plugin/plugin.json`.
- Update plugin identity from Obsidian-specific to general Agent Skills.
- Keep a single plugin package rather than splitting roles into separate plugins.

Codex:

- Add `.codex-plugin/plugin.json`.
- Point `"skills"` to `"./skills/"`.
- Include Codex interface metadata for display name, category, prompts, and capabilities.
- Use Orchestrator as the recommended default entry point.

Skill content should remain host-neutral. It should avoid hard-coded tool names when a general instruction is enough. Host-specific tool mappings belong in platform support docs or references.

## Public Core and Personal Overlay

The public core includes:

- Standard skills.
- Role definitions.
- Registries.
- Claude Code and Codex manifests.
- Public documentation.
- Example overlay configuration.

The personal overlay includes local-only files such as:

```text
overlays/personal.yaml
overlays/private-skills.yaml
```

These files may enable or disable roles, add personal preferences, point to private skills, or reference internal tools. Real personal overlay files should be ignored by git. The repository should commit only examples and documentation for the overlay mechanism.

## Phase 1 Scope

Phase 1 delivers the general package skeleton:

- Rewrite README positioning from Obsidian-specific to general Agent Skills package.
- Add `skills/orchestrator/SKILL.md`.
- Add `skills/skill-manager/SKILL.md`.
- Add the initial role tree under `roles/`.
- Add `registry/skills.yaml`, `registry/roles.yaml`, and `registry/sources.yaml`.
- Add `.codex-plugin/plugin.json`.
- Update `.claude-plugin/` metadata.
- Add architecture, platform support, adding-skills, and overlay documentation.
- Preserve and reclassify existing Obsidian skills as knowledge-management/documentation tooling.

## Acceptance Criteria

Phase 1 is complete when:

- README no longer presents the repository as Obsidian-only.
- Claude Code plugin metadata reflects the general skills package.
- Codex plugin metadata exists and points to `./skills/`.
- Orchestrator skill describes lightweight routing rules.
- Skill Manager skill describes skill lifecycle and registry governance.
- Roles exist for Orchestrator, code, documents, product, and project work.
- Registry files can describe skill sources, sync modes, and role ownership.
- Existing Obsidian skills remain available and are classified under knowledge management or documentation.
- Personal overlay documentation exists without committing private configuration.

## Implementation Notes

Implementation should be incremental:

1. Add registries and roles first so existing skills have a new home.
2. Add Orchestrator and Skill Manager skills.
3. Update platform manifests.
4. Rewrite README and supporting docs.
5. Add lightweight validation scripts only after the registry shape is stable.

The implementation should not push, tag, release, or publish the plugin unless that work is explicitly requested later.
