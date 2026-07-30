---
name: prd-create
description: Use when writing or revising an R&D-facing PRD from accessible product prototypes, confirmed workflows, review decisions, conflict resolution, and implementation-ready module specs.
---

# PRD Create

## Purpose

Create implementation-ready PRDs for R&D, QA, and integration work. This is an agent-agnostic skill: it can be used by any agent that can read source material, inspect an accessible product prototype, write Markdown, and manage referenced screenshots.

For detailed templates, product-access paths, checklists, and screenshot rules, read `references/prd-rnd-workflow.md` when starting substantial PRD work or revising an existing PRD. Use the bundled assets and scripts instead of recreating templates or validators.

Reusable resources:

- `assets/prd-template.md`: full R&D PRD shell.
- `assets/module-workflow-template.md`: one-module workflow confirmation and spec template.
- `assets/decision-checklist-template.md`: review conflict and decision checklist template.
- `references/evidence-levels.md`: what each product access mode can and cannot prove.
- `scripts/validate-prd-images.js`: validate Markdown image links.
- `scripts/audit-prd-portability.js`: scan PRDs or skill files for generic portability issues; pass product-specific leftover terms with `--terms=...` when needed.
- `scripts/package-prd.js`: package the PRD and referenced screenshots.
- `assets/prd-execution-checklist.md`: per-PRD execution gate record.
- `scripts/verify-prd-gates.js`: validate one active module or final readiness; block readiness unless the checklist, step structure, evidence labels, screenshots, and image validation all pass.

## Non-Negotiable Execution Gates

Treat this skill as a gated procedure, not background guidance. Do not draft detailed workflow prose, claim an R&D-ready PRD, package a PRD, or say it is complete by relying on familiarity with PRD writing, source code, mock data, static design, or an existing prototype record.

Before editing detailed PRD content:

1. Copy `assets/prd-execution-checklist.md` beside the target PRD.
2. Record one evidence mode and the actual local command, accessible URL, or interactive-prototype link.
3. Complete a module workflow record for every module in scope.
4. Leave every unproven item unchecked. A checked box represents completed evidence or verification, never an intended future action.

The gates are sequential:

```text
sources and evidence mode
  -> module workflow confirmation
  -> accessible-product/prototype screenshots
  -> step-by-step R&D specification
  -> image validation and readiness gate
  -> only then: R&D-ready / package-ready claim
```

Stop at the first unmet gate. Do not patch an already-written PRD section around the missing evidence; return to the checklist, repair the earliest failed gate, then re-review the whole affected module from the checklist forward.

`requirements-only` is an explicit exception for missing product access. It permits a requirements draft only. It cannot pass the readiness verifier and must never be called an R&D-ready PRD.

## One-Module-at-a-Time Control

Accuracy is more important than speed. Never generate detailed content for multiple modules in one drafting pass. Do not produce an all-module “first draft,” pre-write the next module while validating the current one, or fill gaps with generic boilerplate to make the document look complete.

For a PRD with multiple modules, repeat this closed loop exactly:

1. Set `Active module` in `PRD_EXECUTION_CHECKLIST.md` to one module name.
2. Confirm only that module's role, boundary, entry points, workflow, data result, and unknowns.
3. Execute only that workflow in the accessible product or prototype; capture its screenshots.
4. Write only that module's detailed section using the step template.
5. Check the three Active Module Gates and run:

   ```bash
   node <skill-path>/scripts/verify-prd-gates.js PRD.md PRD_EXECUTION_CHECKLIST.md --module "<module name>"
   ```

6. Record `verified` or `blocked` in the checklist. If blocked, repair this module only; do not start another.
7. Only after a zero exit and a `verified` log entry, select the next module.

After the final module, set `Active module` to `none` and run the full readiness command. The full command rejects a PRD while a module remains active.

The execution checklist and module verifier are control points, not paperwork. Never mark a module as confirmed or verified without the actual workflow evidence and command result.

## Core Rule

Do not write detailed PRD body until the module workflow is confirmed.

For every module, first identify:

- Role: the product's actual actor, such as end user, operator, reviewer, creator, manager, or another named role.
- Module boundary: what this module includes and excludes.
- Entry points: menu, list, card, detail page, button, dialog.
- Main workflow: exact user steps and system responses.
- Subpages and controls: tabs, dialogs, menus, upload, generate, save, delete, preview, terminal.
- Data result: created object, updated object, reference, snapshot, version, deletion behavior.
- Unknowns: anything not known from confirmed user input, product behavior, or meeting decisions.

If the workflow or data ownership is unclear, ask before writing that module.

## Product Access Requirement

The product must be inspectable through an accessible product, demo, staging site, or interactive prototype. Source code is helpful but not required.

Supported access paths:

- Source available: start the product locally and capture browser screenshots.
- Demo or staging available: use the accessible URL and capture browser screenshots.
- Prototype only: use the interactive prototype as UI evidence, but label gaps where backend behavior, persistence, async completion, or integrations cannot be verified.

If no accessible product or prototype exists, do not invent screenshots or detailed interaction states. Write only a requirements draft and list required prototype evidence.

When the evidence mode is `requirements-only`, “next step,” “continue,” or “start” means confirm the active module workflow and its decisions. It never means start a local app, open a browser, capture screenshots, or draft detailed R&D specifications.


## Workflow

### 0. Establish the execution record

Before writing the PRD body, copy `assets/prd-execution-checklist.md` next to the target PRD. Record the evidence mode, product access path, decision-checklist path, blocking decisions, and product-access authorization. Read `references/evidence-levels.md` when the evidence is mixed or uncertain.

This step is incomplete until the checklist exists. Source code, mocks, and prototype notes do not substitute for confirmed workflow, resolved blocking decisions, or the accessible-product/prototype evidence required by the selected mode.

### 1. Gather Sources

Read all user-provided files before drafting:

- Existing PRD or prototype-based PRD.
- Meeting notes and decision lists.
- R&D conflict lists.
- Product/prototype screenshots only if they were produced from an accessible product, demo, staging site, or interactive prototype.
- Recap or retrospective docs from previous PRD work.

Treat conflict lists as indexes of questions, not as truth. Verify each conflict against meeting notes and user decisions.

If the product access mode is unclear, read `references/evidence-levels.md` before deciding what can be verified or screenshot.

Do not begin the module scope plan until source review and evidence mode are recorded in the execution checklist.


### 2. Confirm Scope Before Writing

Write a short module scope plan before editing the PRD. Use `assets/module-workflow-template.md` for substantial modules.

```md
Role:
Module:
Included scope:
Excluded scope:
Entry points:
Main workflow:
Subpages:
Controls:
Data result:
Open questions:
```

Do not add unrequested roles or modules. Do not mix unrelated role workflows in the same section.

Record every completed scope plan in the checklist's Module Workflow Records table. A module may enter the Decision Gate only after its own role, boundary, entry points, main workflow, data result, and unknowns are recorded. “Open questions marked” is insufficient: each must be classified as `confirmed`, `non-blocking`, or `blocking`.

### 2.5 Decision Gate Before Product Access

Before starting a local app, opening a browser, capturing screenshots, or writing detailed workflow specifications:

1. Create or update `assets/decision-checklist-template.md` when any decision affects the active module.
2. List every active-module decision, its blocking module, recommended default, options, status, and confirmer.
3. Set each status to exactly one of `confirmed`, `non-blocking`, or `blocking`.
4. Record the decision checklist and blocking IDs in the execution checklist.
5. Set `Product access authorized` to `yes` only when an authoritative product source or the user has confirmed the active workflow and every blocking decision is resolved.
6. Perform the Action Preflight from `assets/prd-execution-checklist.md` immediately before any browser, dev-server, or screenshot action.

If any active-module decision is `blocking`, stop. The allowed next action is to obtain the decision or refine the workflow; product access, screenshots, and detailed specification are prohibited. A decision may be `non-blocking` only when it cannot change the active module's confirmed workflow, ownership, or acceptance criteria.

### 2.6 Transition From Requirements-Only

`requirements-only` may transition to `local-app`, `demo-staging`, or `interactive-prototype` only after all three conditions are recorded in the execution checklist:

1. The active module workflow is confirmed by the user or an authoritative product source.
2. Every blocking decision for the active module is resolved.
3. Product access is explicitly authorized.

Until then, the only valid deliverable is a requirements draft and a decision/workflow-confirmation request.


### 3. Capture Product Screenshots

When screenshots are required:

- Use the best available product access path: local product, demo/staging URL, or interactive prototype.
- Use browser screenshots from a headless, isolated, or non-disruptive browser context whenever possible.
- Do not use meeting video screenshots, design screenshots, old PRD screenshots, or desktop screenshots.
- Do not interfere with the user's active browser or desktop.
- Follow the confirmed workflow step by step in the accessible product/prototype.
- Wait for async work to finish before taking final-state screenshots.
- Put each screenshot immediately under the corresponding step, not in a screenshot table.
- Use short alt text.
- Use relative image paths from the Markdown file.
- Validate missing, duplicate, absolute, and empty image links with `scripts/validate-prd-images.js`.

Screenshot capture is a gate, not polish to add later. Capture the screenshot while executing each confirmed step; then place it immediately under that step. A source-code run, mock response, static design, prior screenshot, or written prototype record does not satisfy this gate.

If screenshots were captured before the Decision Gate passed, delete them or move them outside the PRD asset directory into quarantine. Do not reference them in the PRD, screenshot inventory, or package; record the discard reason in the decision checklist or execution log. Do not “rescue” an invalid screenshot by adding explanatory prose.


### 4. Write Module Specs for R&D

For a new PRD, start from `assets/prd-template.md`. For each confirmed module, use this structure:

1. Module goal and boundary.
2. Page entry table.
3. Main workflows with step headings, screenshot, operation, page response, controls, R&D requirements, constraints, and exceptions.
4. Interaction constraints.
5. Page flow.
6. Data writes.
7. Error and recovery.
8. Acceptance checklist.
9. Prototype/product design closure check.

Never use an introduction paragraph as a substitute for button behavior, data rules, and failure states.

For every step, use the exact fields from `assets/module-workflow-template.md`: screenshot, precondition, operation, page response, controls, R&D requirements, constraints, exceptions, and evidence status. Do not replace these fields with a prose summary.


### 4.5 Adapt To Product Access

When source code or backend behavior is unavailable, separate evidence types instead of pretending everything was verified:

- Observed UI: what the accessible product or prototype actually shows.
- Required behavior: what R&D must implement.
- Unverified behavior: async tasks, persistence, permissions, generated output, integrations.
- Decision needed: unresolved product or technical choices.

### 5. Review Meeting Conflicts Before Revising

When revising after requirements review:

1. Back up the current PRD first.
2. Build a conflict review table.
3. Mark each item as confirmed, needs decision, second phase, or not adopted.
4. Create a product decision checklist for high-impact conflicts.
5. Wait for user decisions.
6. Update PRD body only after decisions are recorded.
7. Mark decision items as synced after PRD update.

Use `assets/decision-checklist-template.md` for conflict review and product decision tracking. The core conflict review columns are:

| ID | Conflict | Current PRD | Meeting evidence | R&D concern | Product decision needed | PRD action |
|---|---|---|---|---|---|---|

Use checkbox options for product decisions:

```md
| Option | Decision | PRD change |
|---|---|---|
| - [ ] A | Keep current scope | ... |
| - [ ] B | Move to phase 2 | ... |
```

### 6. Add Technical Contracts When Needed

For R&D PRDs, include cross-module technical contracts when decisions require them:

- Draft vs formal object, such as DraftObject vs FormalObject.
- Version chain, such as contentVersion and current effective version.
- Snapshot/reference rules, such as global resource vs bound snapshot.
- Stale content rules after source changes.
- Idempotency for repeated generate, create, upload, delete, and confirm actions.
- Permission and isolation rules, such as no cross-scope resource references.

### 7. Verify Before Packaging

Before saying the PRD is ready or packaging it:

- Validate image links.
- Search for known stale terms and out-of-scope modules with `scripts/audit-prd-portability.js`.
- Confirm screenshots are not duplicated.
- Confirm decision checklist items are marked synced when applicable.
- Package only the current PRD, supporting decision/review/recap docs, and referenced screenshots. Use `scripts/package-prd.js` when packaging is requested.

Run the readiness gate from the PRD directory:

```bash
node <skill-path>/scripts/verify-prd-gates.js PRD.md PRD_EXECUTION_CHECKLIST.md
```

It validates completion gates, product-access authorization, blocking-decision state, active-module workflow confirmation, workflow/step structure, screenshot links, and image validation. A non-zero exit means the PRD is not ready: stop, repair the earliest reported gate, then re-run the whole verifier.

Only report **R&D-ready**, **complete**, or **package-ready** after this command exits zero. Do not package a requirements-only draft.

## R&D PRD Writing Style

Write direct implementation requirements. Avoid author notes like:

- "This section does not repeat the main flow."
- "This PRD does not implement the out-of-scope role."
- "According to my analysis."

Prefer concrete requirements:

- "Clicking Confirm creates the formal object only after objectId is returned."
- "Upload stores the file record but does not start generation until the user clicks Start."
- "Deleting a source file removes only the file record; generated artifacts remain when the confirmed rule requires retention."

## When To Ask

Ask the user when any of these are unclear:

- Object ownership: global, workspace, project, session, content item, or user-specific scope.
- Whether a module is current phase or second phase.
- Whether prototype behavior still applies after meeting review.
- Whether a screenshot is required for an unavailable or not-yet-built flow.
- Whether a conflict list item is credible or only a concern.
- Whether the available product access is local source, demo/staging, or interactive prototype.
- Whether unverified prototype behavior should be specified as required behavior or left as a gap.

Do not guess in these cases.
