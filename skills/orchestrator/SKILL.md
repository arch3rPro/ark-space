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
