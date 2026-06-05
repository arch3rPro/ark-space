# General Agent Skills Package Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the repository into a general-purpose Agent Skills package with lightweight role routing, skill governance, Claude Code support, and Codex plugin support.

**Architecture:** Keep `skills/<skill-name>/SKILL.md` as the canonical skill source shared by all platforms. Add role YAML files and registry YAML files as governance metadata, then update platform manifests and docs to present the package as a general skills hub instead of an Obsidian-only collection.

**Tech Stack:** Markdown, YAML, JSON plugin manifests, Bash, Python 3 standard library for validation.

---

## File Structure

- Create `skills/orchestrator/SKILL.md`: lightweight routing behavior and escalation rules.
- Create `skills/skill-manager/SKILL.md`: skill lifecycle, registry, and source governance workflow.
- Create `roles/orchestrator.yaml`: default route table and supported domains.
- Create `roles/code/code-engineer.yaml`: coding implementation role.
- Create `roles/code/code-reviewer.yaml`: code review role.
- Create `roles/code/repo-maintainer.yaml`: repository maintenance role.
- Create `roles/docs/doc-writer.yaml`: documentation writing role.
- Create `roles/docs/doc-editor.yaml`: documentation editing role.
- Create `roles/docs/knowledge-manager.yaml`: Obsidian and knowledge-management role.
- Create `roles/product/prd-planner.yaml`: product requirements role.
- Create `roles/product/demo-designer.yaml`: demo and prototype role.
- Create `roles/product/competitive-analyst.yaml`: competitive analysis role.
- Create `roles/project/project-manager.yaml`: planning and tracking role.
- Create `roles/project/delivery-coordinator.yaml`: delivery coordination role.
- Create `roles/skills/skill-manager.yaml`: role wrapper for the Skill Manager skill.
- Create `registry/sources.yaml`: upstream source records.
- Create `registry/skills.yaml`: skill inventory, sync mode, and role ownership.
- Create `registry/roles.yaml`: role inventory and default role.
- Create `.codex-plugin/plugin.json`: Codex plugin manifest pointing at `./skills/`.
- Modify `.claude-plugin/plugin.json`: rename/reposition the Claude plugin.
- Modify `.claude-plugin/marketplace.json`: rename marketplace package.
- Modify `README.md`: general Agent Skills package overview and installation instructions.
- Create `docs/architecture.md`: architecture and boundary explanation.
- Create `docs/platform-support.md`: Claude Code and Codex support notes.
- Create `docs/adding-skills.md`: workflow for adding, adapting, and governing skills.
- Create `overlays/README.md`: public/private overlay model.
- Create `overlays/personal.example.yaml`: safe example overlay config.
- Modify `.gitignore`: ignore local personal overlay files.
- Create `scripts/validate-skills.py`: validation for manifests, registries, roles, and skill frontmatter.

### Shared Conventions

Use these sync modes exactly:

```text
mirror
adapted
local
reference-only
```

Use these initial role IDs exactly:

```text
orchestrator
code/code-engineer
code/code-reviewer
code/repo-maintainer
docs/doc-writer
docs/doc-editor
docs/knowledge-manager
product/prd-planner
product/demo-designer
product/competitive-analyst
project/project-manager
project/delivery-coordinator
skills/skill-manager
```

## Task 1: Add Validation Script

**Files:**
- Create: `scripts/validate-skills.py`

- [ ] **Step 1: Create the validation script**

Create `scripts/validate-skills.py` with this content:

```python
#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALID_SYNC_MODES = {"mirror", "adapted", "local", "reference-only"}


def fail(message):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_text(path):
    return path.read_text(encoding="utf-8")


def parse_simple_yaml_list(path, top_key):
    text = read_text(path)
    lines = text.splitlines()
    try:
        start = next(index for index, line in enumerate(lines) if line.strip() == f"{top_key}:")
    except StopIteration:
        fail(f"{path} must contain '{top_key}:'")

    items = []
    current = None
    for raw in lines[start + 1:]:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.endswith(":") and not line.startswith("  "):
            break
        if line.startswith("  - "):
            if current:
                items.append(current)
            current = {}
            rest = line[4:]
            if ": " in rest:
                key, value = rest.split(": ", 1)
                current[key] = clean_scalar(value)
        elif current is not None and line.startswith("    ") and ": " in stripped:
            key, value = stripped.split(": ", 1)
            current[key] = clean_scalar(value)
    if current:
        items.append(current)
    return items


def clean_scalar(value):
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    return value


def validate_skill_frontmatter():
    skill_files = sorted((ROOT / "skills").glob("*/SKILL.md"))
    if not skill_files:
        fail("no skills/*/SKILL.md files found")

    for path in skill_files:
        text = read_text(path)
        if not text.startswith("---\n"):
            fail(f"{path} is missing YAML frontmatter")
        end = text.find("\n---\n", 4)
        if end == -1:
            fail(f"{path} has unterminated YAML frontmatter")
        frontmatter = text[4:end]
        if not re.search(r"^name:\s*.+$", frontmatter, re.MULTILINE):
            fail(f"{path} frontmatter is missing name")
        if not re.search(r"^description:\s*.+$", frontmatter, re.MULTILINE):
            fail(f"{path} frontmatter is missing description")


def validate_json(path):
    try:
        json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        fail(f"{path} is invalid JSON: {exc}")


def validate_registry_files():
    registry_dir = ROOT / "registry"
    for filename in ["sources.yaml", "skills.yaml", "roles.yaml"]:
        path = registry_dir / filename
        if not path.exists():
            fail(f"missing {path}")

    skills = parse_simple_yaml_list(registry_dir / "skills.yaml", "skills")
    roles = parse_simple_yaml_list(registry_dir / "roles.yaml", "roles")
    sources = parse_simple_yaml_list(registry_dir / "sources.yaml", "sources")

    source_ids = {item.get("id") for item in sources if item.get("id")}
    role_ids = {item.get("id") for item in roles if item.get("id")}

    roles_text = read_text(registry_dir / "roles.yaml")
    if not re.search(r"^defaultRole:\s*orchestrator$", roles_text, re.MULTILINE):
        fail("registry/roles.yaml must set defaultRole: orchestrator")

    if "orchestrator" not in role_ids:
        fail("registry/roles.yaml must include id: orchestrator")

    for item in skills:
        name = item.get("name")
        path_value = item.get("path")
        sync_mode = item.get("syncMode")
        if not name:
            fail("registry/skills.yaml contains a skill without name")
        if sync_mode not in VALID_SYNC_MODES:
            fail(f"skill {name} has invalid syncMode {sync_mode}")
        if path_value and not (ROOT / path_value).exists():
            fail(f"skill {name} path does not exist: {path_value}")
        upstream_id = item.get("upstreamId")
        if upstream_id and upstream_id not in source_ids:
            fail(f"skill {name} references unknown upstreamId {upstream_id}")

    for item in roles:
        role_id = item.get("id")
        path_value = item.get("path")
        if not role_id:
            fail("registry/roles.yaml contains a role without id")
        if path_value and not (ROOT / path_value).exists():
            fail(f"role {role_id} path does not exist: {path_value}")


def validate_platform_manifests():
    validate_json(ROOT / ".claude-plugin" / "plugin.json")
    validate_json(ROOT / ".claude-plugin" / "marketplace.json")
    validate_json(ROOT / ".codex-plugin" / "plugin.json")

    codex = json.loads(read_text(ROOT / ".codex-plugin" / "plugin.json"))
    if codex.get("skills") != "./skills/":
        fail(".codex-plugin/plugin.json must set skills to ./skills/")


def main():
    validate_skill_frontmatter()
    validate_registry_files()
    validate_platform_manifests()
    print("skills package validation passed")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make the script executable**

Run:

```bash
chmod +x scripts/validate-skills.py
```

- [ ] **Step 3: Run validation and confirm the expected initial failure**

Run:

```bash
python3 scripts/validate-skills.py
```

Expected: FAIL with an error like `missing registry/sources.yaml` or `missing .codex-plugin/plugin.json`.

- [ ] **Step 4: Commit**

```bash
git add scripts/validate-skills.py
git commit -m "test: add skills package validation"
```

## Task 2: Add Registries

**Files:**
- Create: `registry/sources.yaml`
- Create: `registry/skills.yaml`
- Create: `registry/roles.yaml`

- [ ] **Step 1: Create registry directory**

Run:

```bash
mkdir -p registry
```

- [ ] **Step 2: Create sources registry**

Create `registry/sources.yaml`:

```yaml
sources:
  - id: obsidian-skills
    type: github
    repo: arch3rPro/obsidian-skills
    upstreamRepo: kepano/obsidian-skills
    license: MIT
    syncPolicy: adapted
    notes: "Existing Obsidian skills retained as knowledge-management tools."

  - id: defuddle-cli
    type: github
    repo: kepano/defuddle-cli
    license: MIT
    syncPolicy: adapted
    notes: "Referenced by the defuddle skill for clean web content extraction."

  - id: superpowers
    type: github
    repo: obra/superpowers
    license: MIT
    syncPolicy: reference-only
    localPath: reference/superpowers
    notes: "Reference for multi-platform plugin structure and agent workflow skills."
```

- [ ] **Step 3: Create skills registry**

Create `registry/skills.yaml`:

```yaml
skills:
  - name: orchestrator
    path: skills/orchestrator
    status: active
    syncMode: local
    categories: meta,routing
    roles: orchestrator

  - name: skill-manager
    path: skills/skill-manager
    status: active
    syncMode: local
    categories: meta,governance
    roles: skills/skill-manager

  - name: defuddle
    path: skills/defuddle
    status: active
    syncMode: adapted
    upstreamId: defuddle-cli
    categories: docs,research,web
    roles: docs/knowledge-manager,product/competitive-analyst

  - name: json-canvas
    path: skills/json-canvas
    status: active
    syncMode: adapted
    upstreamId: obsidian-skills
    categories: docs,knowledge,canvas
    roles: docs/knowledge-manager

  - name: obsidian-bases
    path: skills/obsidian-bases
    status: active
    syncMode: adapted
    upstreamId: obsidian-skills
    categories: docs,knowledge,obsidian
    roles: docs/knowledge-manager

  - name: obsidian-cli
    path: skills/obsidian-cli
    status: active
    syncMode: adapted
    upstreamId: obsidian-skills
    categories: docs,knowledge,obsidian
    roles: docs/knowledge-manager

  - name: obsidian-kanban
    path: skills/obsidian-kanban
    status: active
    syncMode: adapted
    upstreamId: obsidian-skills
    categories: project,knowledge,obsidian
    roles: docs/knowledge-manager,project/project-manager

  - name: obsidian-markdown
    path: skills/obsidian-markdown
    status: active
    syncMode: adapted
    upstreamId: obsidian-skills
    categories: docs,knowledge,obsidian
    roles: docs/knowledge-manager,docs/doc-writer,docs/doc-editor
```

- [ ] **Step 4: Create roles registry**

Create `registry/roles.yaml`:

```yaml
defaultRole: orchestrator

roles:
  - id: orchestrator
    path: roles/orchestrator.yaml
    domain: meta
    default: true

  - id: code/code-engineer
    path: roles/code/code-engineer.yaml
    domain: code

  - id: code/code-reviewer
    path: roles/code/code-reviewer.yaml
    domain: code

  - id: code/repo-maintainer
    path: roles/code/repo-maintainer.yaml
    domain: code

  - id: docs/doc-writer
    path: roles/docs/doc-writer.yaml
    domain: docs

  - id: docs/doc-editor
    path: roles/docs/doc-editor.yaml
    domain: docs

  - id: docs/knowledge-manager
    path: roles/docs/knowledge-manager.yaml
    domain: docs

  - id: product/prd-planner
    path: roles/product/prd-planner.yaml
    domain: product

  - id: product/demo-designer
    path: roles/product/demo-designer.yaml
    domain: product

  - id: product/competitive-analyst
    path: roles/product/competitive-analyst.yaml
    domain: product

  - id: project/project-manager
    path: roles/project/project-manager.yaml
    domain: project

  - id: project/delivery-coordinator
    path: roles/project/delivery-coordinator.yaml
    domain: project

  - id: skills/skill-manager
    path: roles/skills/skill-manager.yaml
    domain: skills
```

- [ ] **Step 5: Run validation and confirm the expected role path failure**

Run:

```bash
python3 scripts/validate-skills.py
```

Expected: FAIL with an error like `skill orchestrator path does not exist: skills/orchestrator` or `role orchestrator path does not exist: roles/orchestrator.yaml`.

- [ ] **Step 6: Commit**

```bash
git add registry/sources.yaml registry/skills.yaml registry/roles.yaml
git commit -m "feat: add skill and role registries"
```

## Task 3: Add Orchestrator and Skill Manager Skills

**Files:**
- Create: `skills/orchestrator/SKILL.md`
- Create: `skills/skill-manager/SKILL.md`

- [ ] **Step 1: Create skill directories**

Run:

```bash
mkdir -p skills/orchestrator skills/skill-manager
```

- [ ] **Step 2: Create Orchestrator skill**

Create `skills/orchestrator/SKILL.md`:

```markdown
---
name: orchestrator
description: Lightweightly route agent work to the smallest useful role, workflow, and skill set. Use when the user asks for general help, a cross-domain task, role selection, skill selection, or when the task scope is unclear.
---

# Orchestrator

Route work before expanding process.

Use the lightest role and workflow that can safely complete the task. Route first by user intent, then by artifact type, then by risk. Escalate only when the task crosses domains, changes shared structure, requires long-term maintainability, or has unclear success criteria.

## Routing Workflow

1. Identify the primary task domain: code, docs, product, project, skills, knowledge management, or cross-domain.
2. Select the smallest useful role set from `roles/`.
3. Use one role for simple work.
4. Use multiple roles only when the task naturally crosses domains.
5. Ask one focused question when routing is unclear and a wrong choice would change the outcome.
6. Hand off skill-library maintenance to `skill-manager`.

## Default Routes

| User intent | Route |
|---|---|
| Implement, refactor, test, debug | `code/code-engineer` |
| Review code or assess regressions | `code/code-reviewer` |
| CI, PR, release-prep discussion, repository hygiene | `code/repo-maintainer` |
| Write new documentation | `docs/doc-writer` |
| Improve existing documentation | `docs/doc-editor` |
| Work with Obsidian, notes, Bases, Canvas, or knowledge files | `docs/knowledge-manager` |
| Shape requirements or PRDs | `product/prd-planner` |
| Build or evaluate a product demo | `product/demo-designer` |
| Compare products, competitors, or market claims | `product/competitive-analyst` |
| Plan milestones, tasks, ownership, or delivery | `project/project-manager` |
| Coordinate handoffs, status, or multi-step delivery | `project/delivery-coordinator` |
| Create, adapt, validate, or sync skills | `skills/skill-manager` |

## Escalation Rules

Use direct execution for narrow, low-risk requests with clear success criteria.

Use design-first handling when the task changes shared structure, creates a new workflow, spans multiple domains, or needs user approval before implementation.

Use a multi-role flow when each role has a distinct artifact. Example: `product/prd-planner` creates requirements, `code/code-engineer` implements, and `docs/doc-writer` updates documentation.

Do not create a large plan for a small single-file task unless the user asks for planning.

## Handoff Format

When handing off to a role, include:

```text
Role: <role id>
Reason: <why this role is the smallest useful fit>
Inputs: <files, user request, constraints>
Expected output: <artifact or decision>
Escalation: <when to return to Orchestrator>
```
```

- [ ] **Step 3: Create Skill Manager skill**

Create `skills/skill-manager/SKILL.md`:

```markdown
---
name: skill-manager
description: Manage this Agent Skills package by creating skills, recording upstream sources, assigning roles, validating registries, and guiding mirror, adapted, local, and reference-only skill updates.
---

# Skill Manager

Manage skills as durable package assets, not one-off prompt snippets.

Use this skill when creating a skill, adapting an external skill, recording upstream provenance, assigning a skill to a role, validating the skills package, or preparing a selective upstream update.

## Workflow

1. Classify the request: create, adapt, mirror, validate, assign role, document, or review upstream changes.
2. Check `registry/skills.yaml`, `registry/sources.yaml`, and `registry/roles.yaml` before editing.
3. Keep skill bodies under `skills/<skill-name>/SKILL.md`.
4. Record source provenance for every reused or adapted skill.
5. Assign each active skill to at least one role unless it is intentionally standalone.
6. Run `python3 scripts/validate-skills.py` after registry, role, manifest, or skill changes.

## Sync Modes

| syncMode | Meaning | Update behavior |
|---|---|---|
| `mirror` | External skill kept close to upstream | Prefer direct sync, preserve upstream behavior, record version or commit when available |
| `adapted` | External skill changed for this package | Compare upstream changes and merge selectively |
| `local` | Skill created here | Maintain directly |
| `reference-only` | Upstream used only as design reference | Do not publish it as a local skill unless explicitly promoted |

## Creating a Skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add YAML frontmatter with `name` and `description`.
3. Keep instructions host-neutral unless the skill is intentionally platform-specific.
4. Add the skill to `registry/skills.yaml`.
5. Add or update any needed source in `registry/sources.yaml`.
6. Assign the skill to one or more roles.
7. Run validation.

## Adapting an External Skill

1. Record the upstream in `registry/sources.yaml`.
2. Add the skill with `syncMode: adapted`.
3. Keep a concise note about why it diverges from upstream.
4. Preserve license and attribution requirements.
5. Review upstream updates manually before merging.

## Validation

Run:

```bash
python3 scripts/validate-skills.py
```

Validation must pass before committing registry, role, skill, or manifest changes.
```

- [ ] **Step 4: Run validation and confirm the expected role path failure**

Run:

```bash
python3 scripts/validate-skills.py
```

Expected: FAIL with an error like `role orchestrator path does not exist: roles/orchestrator.yaml`.

- [ ] **Step 5: Commit**

```bash
git add skills/orchestrator/SKILL.md skills/skill-manager/SKILL.md
git commit -m "feat: add orchestrator and skill manager skills"
```

## Task 4: Add Role Definitions

**Files:**
- Create all files under `roles/`

- [ ] **Step 1: Create role directories**

Run:

```bash
mkdir -p roles/code roles/docs roles/product roles/project roles/skills
```

- [ ] **Step 2: Create Orchestrator role**

Create `roles/orchestrator.yaml`:

```yaml
id: orchestrator
name: Orchestrator
mode: lightweight-routing
default: true
description: Route work to the smallest useful agent role and workflow.
skills:
  - orchestrator
routes:
  code:
    - code/code-engineer
    - code/code-reviewer
    - code/repo-maintainer
  docs:
    - docs/doc-writer
    - docs/doc-editor
    - docs/knowledge-manager
  product:
    - product/prd-planner
    - product/demo-designer
    - product/competitive-analyst
  project:
    - project/project-manager
    - project/delivery-coordinator
  skills:
    - skills/skill-manager
escalation:
  ask_one_question_when_unclear: true
  use_design_first_for_cross_domain: true
  avoid_full_process_for_simple_tasks: true
platforms:
  claude-code: true
  codex: true
```

- [ ] **Step 3: Create code roles**

Create `roles/code/code-engineer.yaml`:

```yaml
id: code/code-engineer
name: Code Engineer
domain: code
description: Implement, refactor, test, and debug software projects.
skills:
  - orchestrator
platforms:
  claude-code: true
  codex: true
```

Create `roles/code/code-reviewer.yaml`:

```yaml
id: code/code-reviewer
name: Code Reviewer
domain: code
description: Review code for bugs, regressions, missing tests, and maintainability risks.
skills:
  - orchestrator
platforms:
  claude-code: true
  codex: true
```

Create `roles/code/repo-maintainer.yaml`:

```yaml
id: code/repo-maintainer
name: Repo Maintainer
domain: code
description: Maintain repository health, CI readiness, PR hygiene, and release-adjacent checks without publishing unless explicitly requested.
skills:
  - orchestrator
platforms:
  claude-code: true
  codex: true
```

- [ ] **Step 4: Create docs roles**

Create `roles/docs/doc-writer.yaml`:

```yaml
id: docs/doc-writer
name: Doc Writer
domain: docs
description: Create clear documentation, guides, READMEs, and manuals.
skills:
  - orchestrator
platforms:
  claude-code: true
  codex: true
```

Create `roles/docs/doc-editor.yaml`:

```yaml
id: docs/doc-editor
name: Doc Editor
domain: docs
description: Improve structure, clarity, consistency, and usefulness of existing documentation.
skills:
  - orchestrator
platforms:
  claude-code: true
  codex: true
```

Create `roles/docs/knowledge-manager.yaml`:

```yaml
id: docs/knowledge-manager
name: Knowledge Manager
domain: docs
description: Work with Obsidian, Markdown notes, Bases, Canvas, Kanban boards, and clean web extraction.
skills:
  - orchestrator
  - obsidian-markdown
  - obsidian-bases
  - obsidian-cli
  - obsidian-kanban
  - json-canvas
  - defuddle
platforms:
  claude-code: true
  codex: true
```

- [ ] **Step 5: Create product roles**

Create `roles/product/prd-planner.yaml`:

```yaml
id: product/prd-planner
name: PRD Planner
domain: product
description: Clarify requirements, define scope, and write acceptance criteria.
skills:
  - orchestrator
platforms:
  claude-code: true
  codex: true
```

Create `roles/product/demo-designer.yaml`:

```yaml
id: product/demo-designer
name: Demo Designer
domain: product
description: Design product demos, realistic demo data, and end-to-end demo flows.
skills:
  - orchestrator
platforms:
  claude-code: true
  codex: true
```

Create `roles/product/competitive-analyst.yaml`:

```yaml
id: product/competitive-analyst
name: Competitive Analyst
domain: product
description: Compare products, competitors, claims, positioning, and market evidence.
skills:
  - orchestrator
  - defuddle
platforms:
  claude-code: true
  codex: true
```

- [ ] **Step 6: Create project and skills roles**

Create `roles/project/project-manager.yaml`:

```yaml
id: project/project-manager
name: Project Manager
domain: project
description: Plan milestones, tasks, risks, and project tracking structures.
skills:
  - orchestrator
  - obsidian-kanban
platforms:
  claude-code: true
  codex: true
```

Create `roles/project/delivery-coordinator.yaml`:

```yaml
id: project/delivery-coordinator
name: Delivery Coordinator
domain: project
description: Coordinate multi-step delivery, handoffs, status summaries, and follow-up actions.
skills:
  - orchestrator
platforms:
  claude-code: true
  codex: true
```

Create `roles/skills/skill-manager.yaml`:

```yaml
id: skills/skill-manager
name: Skill Manager
domain: skills
description: Create, adapt, validate, and govern skills in this package.
skills:
  - orchestrator
  - skill-manager
platforms:
  claude-code: true
  codex: true
```

- [ ] **Step 7: Run validation and confirm the expected Codex manifest failure**

Run:

```bash
python3 scripts/validate-skills.py
```

Expected: FAIL with an error like `No such file or directory: '.codex-plugin/plugin.json'`.

- [ ] **Step 8: Commit**

```bash
git add roles
git commit -m "feat: add initial agent role definitions"
```

## Task 5: Add Codex Manifest and Update Claude Metadata

**Files:**
- Create: `.codex-plugin/plugin.json`
- Modify: `.claude-plugin/plugin.json`
- Modify: `.claude-plugin/marketplace.json`

- [ ] **Step 1: Create Codex plugin manifest**

Run:

```bash
mkdir -p .codex-plugin
```

Create `.codex-plugin/plugin.json`:

```json
{
  "name": "agent-skills",
  "version": "0.1.0",
  "description": "A general-purpose Agent Skills collection with lightweight role routing, skill management, and roles for coding, documents, product, and project work.",
  "author": {
    "name": "arch3rPro",
    "url": "https://github.com/arch3rPro"
  },
  "homepage": "https://github.com/arch3rPro/agent-skills",
  "repository": "https://github.com/arch3rPro/agent-skills",
  "license": "MIT",
  "keywords": [
    "agent-skills",
    "orchestrator",
    "skill-manager",
    "coding",
    "documents",
    "product",
    "project"
  ],
  "skills": "./skills/",
  "interface": {
    "displayName": "Agent Skills",
    "shortDescription": "Lightweight role routing and reusable skills for general agents",
    "longDescription": "Use Agent Skills to route work through an Orchestrator role, manage reusable skills, and apply focused roles for coding, documents, product, project, and knowledge-management workflows.",
    "developerName": "arch3rPro",
    "category": "Productivity",
    "capabilities": [
      "Interactive",
      "Read",
      "Write"
    ],
    "defaultPrompt": [
      "Help me route this task to the right agent role.",
      "Help me create or improve a skill."
    ],
    "websiteURL": "https://github.com/arch3rPro/agent-skills",
    "brandColor": "#2563EB",
    "screenshots": []
  }
}
```

- [ ] **Step 2: Update Claude plugin manifest**

Replace `.claude-plugin/plugin.json` with:

```json
{
  "name": "agent-skills",
  "version": "0.1.0",
  "description": "A general-purpose Agent Skills collection with lightweight role routing, skill management, and domain roles for coding, documents, product, and project work.",
  "author": {
    "name": "arch3rPro",
    "url": "https://github.com/arch3rPro"
  },
  "repository": "https://github.com/arch3rPro/agent-skills",
  "license": "MIT",
  "keywords": [
    "skills",
    "agents",
    "claude-code",
    "codex",
    "orchestrator",
    "coding",
    "documents",
    "product",
    "project-management"
  ]
}
```

- [ ] **Step 3: Update Claude marketplace manifest**

Replace `.claude-plugin/marketplace.json` with:

```json
{
  "name": "agent-skills",
  "owner": {
    "name": "arch3rPro",
    "url": "https://github.com/arch3rPro"
  },
  "plugins": [
    {
      "name": "agent-skills",
      "source": "./",
      "description": "General-purpose Agent Skills with lightweight role routing",
      "version": "0.1.0"
    }
  ]
}
```

- [ ] **Step 4: Run validation and confirm it passes**

Run:

```bash
python3 scripts/validate-skills.py
```

Expected:

```text
skills package validation passed
```

- [ ] **Step 5: Commit**

```bash
git add .codex-plugin/plugin.json .claude-plugin/plugin.json .claude-plugin/marketplace.json
git commit -m "feat: add codex plugin metadata"
```

## Task 6: Add Public and Overlay Documentation

**Files:**
- Create: `docs/architecture.md`
- Create: `docs/platform-support.md`
- Create: `docs/adding-skills.md`
- Create: `overlays/README.md`
- Create: `overlays/personal.example.yaml`
- Modify: `.gitignore`

- [ ] **Step 1: Create docs and overlay directories**

Run:

```bash
mkdir -p docs overlays
```

- [ ] **Step 2: Create architecture doc**

Create `docs/architecture.md`:

```markdown
# Architecture

This repository is a general Agent Skills package.

The canonical skill source is `skills/<skill-name>/SKILL.md`. Claude Code, Codex, and future hosts should consume the same skill files instead of maintaining platform-specific copies.

## Layers

- `skills/`: executable skill instructions.
- `roles/`: role definitions that compose skills for common work types.
- `registry/`: governance metadata for skills, roles, and upstream sources.
- `.claude-plugin/`: Claude Code plugin metadata.
- `.codex-plugin/`: Codex plugin metadata.
- `overlays/`: examples and documentation for private local customization.
- `reference/`: upstream projects used for design reference.

## Default Entry

The default role is `orchestrator`. It uses lightweight routing to choose the smallest useful role and workflow for a task.

## Existing Obsidian Skills

The Obsidian skills remain active. They are now classified as documentation and knowledge-management tooling rather than the identity of the whole repository.
```

- [ ] **Step 3: Create platform support doc**

Create `docs/platform-support.md`:

```markdown
# Platform Support

Phase 1 supports Claude Code and Codex.

## Claude Code

Claude Code uses `.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json`.

The plugin ships one shared skills package. Roles are defined under `roles/`; they are not separate Claude plugins.

## Codex

Codex uses `.codex-plugin/plugin.json`.

The manifest points to:

```json
"skills": "./skills/"
```

Codex and Claude Code should consume the same `skills/` directory.

## Skill Content

Skill instructions should stay host-neutral when possible. Prefer wording such as "read the relevant files" over hard-coded tool names. Host-specific differences belong in platform documentation or references.

## Planned Later

OpenCode, Gemini, Cursor, and other hosts can be added later by adding platform manifests and documentation without changing the canonical skill bodies.
```

- [ ] **Step 4: Create adding-skills doc**

Create `docs/adding-skills.md`:

```markdown
# Adding Skills

Use `skill-manager` when adding, adapting, validating, or assigning skills.

## New Local Skill

1. Create `skills/<skill-name>/SKILL.md`.
2. Add frontmatter with `name` and `description`.
3. Add an entry to `registry/skills.yaml` with `syncMode: local`.
4. Assign the skill to one or more roles.
5. Run `python3 scripts/validate-skills.py`.

## Mirrored Skill

Use `syncMode: mirror` when the local copy should stay close to upstream.

Record the upstream in `registry/sources.yaml`.

## Adapted Skill

Use `syncMode: adapted` when the skill started from another project but has been changed for this package.

Review upstream updates selectively instead of applying them automatically.

## Reference-Only Source

Use `reference-only` for projects that guide the design but are not published as local skills.
```

- [ ] **Step 5: Create overlay docs and example**

Create `overlays/README.md`:

```markdown
# Personal Overlays

This directory documents local-only customization.

Commit examples and documentation only. Do not commit private overlay files that contain personal workflows, internal tools, private repositories, or company-specific instructions.

Suggested local files:

- `overlays/personal.yaml`
- `overlays/private-skills.yaml`
```

Create `overlays/personal.example.yaml`:

```yaml
enabledRoles:
  - orchestrator
  - code/code-engineer
  - docs/knowledge-manager

disabledRoles: []

privateSkillPaths: []

preferences:
  orchestratorMode: lightweight-routing
  askBeforeCrossDomainImplementation: true
```

- [ ] **Step 6: Ignore private overlays**

Append these lines to `.gitignore`:

```gitignore

# Local private overlays
overlays/personal.yaml
overlays/private-skills.yaml
```

- [ ] **Step 7: Run validation**

Run:

```bash
python3 scripts/validate-skills.py
```

Expected:

```text
skills package validation passed
```

- [ ] **Step 8: Commit**

```bash
git add docs/architecture.md docs/platform-support.md docs/adding-skills.md overlays/README.md overlays/personal.example.yaml .gitignore
git commit -m "docs: document skills package architecture"
```

## Task 7: Rewrite README

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Replace README with general package positioning**

Replace `README.md` with:

```markdown
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
```

- [ ] **Step 2: Run validation**

Run:

```bash
python3 scripts/validate-skills.py
```

Expected:

```text
skills package validation passed
```

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: reposition repository as agent skills package"
```

## Task 8: Final Verification

**Files:**
- Verify all modified files

- [ ] **Step 1: Run validation**

Run:

```bash
python3 scripts/validate-skills.py
```

Expected:

```text
skills package validation passed
```

- [ ] **Step 2: Validate JSON manifests**

Run:

```bash
python3 -m json.tool .claude-plugin/plugin.json >/dev/null
python3 -m json.tool .claude-plugin/marketplace.json >/dev/null
python3 -m json.tool .codex-plugin/plugin.json >/dev/null
```

Expected: all commands exit with status 0 and print no errors.

- [ ] **Step 3: Check for Obsidian-only positioning**

Run:

```bash
rg -n "Agent Skills for use with Obsidian|Claude Skills for Obsidian|obsidian@obsidian-skills|/plugin install obsidian|/plugin marketplace add arch3rPro/obsidian-skills" README.md .claude-plugin .codex-plugin docs/architecture.md docs/platform-support.md docs/adding-skills.md
```

Expected: no matches for old package positioning. References to Obsidian as a knowledge-management tool are acceptable when they refer to existing Obsidian skills.

- [ ] **Step 4: Check worktree state**

Run:

```bash
git status --short
```

Expected: no unstaged or staged Phase 1 files. Existing unrelated untracked files such as `reference/` may still appear if they predated implementation.

- [ ] **Step 5: Commit final verification note only if files changed**

If no files changed in Task 8, do not create an empty commit.

If a verification fix was required, commit only the fix:

```bash
git add <fixed-files>
git commit -m "chore: finalize agent skills package validation"
```

## Self-Review Checklist

- Spec coverage: every Phase 1 requirement has a task.
- Red-flag scan: every task includes concrete file content, commands, or expected output.
- Type consistency: role IDs, sync modes, and registry paths are consistent across examples.
- Boundary check: the plan does not publish, tag, push, release, delete Obsidian skills, or implement full upstream sync automation.
