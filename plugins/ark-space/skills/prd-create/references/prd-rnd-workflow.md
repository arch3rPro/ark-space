# R&D PRD Workflow Reference

## Bundled Templates And Tools

Use these bundled resources instead of recreating templates or validators:

| Resource | Purpose |
|---|---|
| `assets/prd-template.md` | Full R&D PRD shell |
| `assets/module-workflow-template.md` | Module workflow confirmation and implementation spec |
| `assets/decision-checklist-template.md` | Review conflict and product decision tracking |
| `references/evidence-levels.md` | Evidence limits for local app, demo, staging, prototype, static screenshots, or requirements-only work |
| `scripts/validate-prd-images.js` | Markdown image link validation |
| `scripts/audit-prd-portability.js` | Portability scan; accepts product-specific leftover terms with `--terms=...` |
| `scripts/package-prd.js` | PRD package creation with referenced screenshots |
| `assets/prd-execution-checklist.md` | Required execution, decision, and module-gate record |
| `scripts/verify-prd-gates.js` | Module and final readiness validation |


## Document Skeleton

Use this structure for large R&D-facing PRDs:

```md
# PRD title

> Audience: R&D, QA, integration.
> Method: confirm one workflow, write one module.

## 1. Summary
## 2. Contacts
## 3. Background
## 4. Objective
## 5. Users
## 6. Value
## 7. Solution
## 7.1 Writing Rules
## 7.2 Role: Module A
## 7.3 Role: Module B
## 7.x Technical Contracts
## 7.x Pending Modules
## 8. Release
```

The generic `create-prd` skill's 8 sections can be reused as the outer shell, but the Solution section must contain detailed R&D module specs, not marketing or concept prose.

## Product Access Modes

The PRD workflow requires an accessible product or prototype. It does not require source code.

| Access mode | Can use for screenshots | Can verify | Must not claim |
|---|---|---|---|
| Local source/app | Yes | UI, interactions, async states, persistence if backend works | Production readiness unless tested end to end |
| Demo/staging URL | Yes | UI, workflows exposed by the environment, visible success/failure states | Internal data model unless documented |
| Interactive prototype | Yes | UI layout, navigation, control presence, intended states | Backend behavior, persistence, generated content correctness |
| Static screenshots only | Limited supporting evidence | Visual reference only | Product workflow, button behavior, data writes |
| No product/prototype access | No | Requirements only | Functional screenshots or detailed page states |

When only an interactive prototype is available, label evidence clearly:

- Observed in prototype.
- Required by PRD.
- Not verifiable from prototype.
- Needs product or R&D decision.

Do not invent screenshots. Do not turn prototype assumptions into verified behavior.

## Decision Gate Before Product Access

Before local-app, demo/staging, or prototype access, create the execution checklist and classify every decision affecting the active module as `confirmed`, `non-blocking`, or `blocking`.

- `blocking`: stop. It prevents product access, screenshots, and detailed specifications for the affected module.
- `non-blocking`: may continue only when it cannot alter the active module's confirmed workflow, ownership, or acceptance criteria.
- `confirmed`: record the confirming user or authoritative product source.

For any active-module decision, create `assets/decision-checklist-template.md` before product access. Record its path, blocking IDs, and explicit product-access authorization in the execution checklist.

`requirements-only` is not a shortcut to product access. When the user asks to continue or start from this state, the next action is workflow/decision confirmation. It may transition to an accessible-product mode only after workflow confirmation, blocking-decision resolution, and explicit authorization are recorded.

Before a browser, dev server, or screenshot action, run the Action Preflight in `assets/prd-execution-checklist.md`. If it reports an unconfirmed workflow, blocking decision, or unauthorized access, stop.

If screenshots were captured before the Decision Gate passed, delete or quarantine them outside PRD assets and do not cite them in the PRD or package.

## Module Template

```md
## 7.x Role: Module Name

### 7.x.1 Module Goal

State what this module produces and what it does not produce.

### 7.x.2 Page Entry

| Entry | User action | Page response | R&D requirement |
|---|---|---|---|

### 7.x.3 Main Workflow A: Name

#### A1 Step name

![short alt](assets/product-screenshots/example.png)

- Precondition:
- Operation:
- Page:
- Controls:
- R&D:
- Constraint:
- Exception:

### 7.x.4 Interaction Constraints

| Stage | Allowed | Forbidden | R&D handling |
|---|---|---|---|

### 7.x.5 Page Flow

| Order | Page state | Trigger | Must show | Next |
|---|---|---|---|---|

### 7.x.6 Data Writes

| Object | Timing | Required fields | Forbidden |
|---|---|---|---|

### 7.x.7 Error Recovery

| Scenario | Page behavior | Recovery |
|---|---|---|

### 7.x.8 Acceptance Checklist

| Group | Acceptance item |
|---|---|

### 7.x.9 Design Closure Check

| Check | Result | R&D note |
|---|---|---|
```

## Screenshot Rules

Use only screenshots captured from an accessible product, demo, staging site, or interactive prototype:

- Browser screenshot, not desktop screenshot.
- Isolated browser context or headless browser preferred.
- Do not disturb the user's active browser.
- Wait for async completion.
- Screenshot the actual page reached by the workflow.
- Do not use meeting videos, old screenshots, static design mockups, or screenshots from incomplete flows as functional evidence.
- Do not reuse the same image multiple times.
- Short alt text only.
- Use relative paths.

If the prototype cannot execute an async action, do not fake a completion screenshot. Write the expected completion behavior as a requirement and mark it unverified by prototype.

Run image validation with the bundled script:

```bash
node scripts/validate-prd-images.js docs/product/PRD.md
```

Required result:

- missing: 0
- duplicateImages: 0
- absoluteImages: 0
- emptyLinks: 0

## Workflow Confirmation Checklist

Before writing a module, confirm:

| Item | Question |
|---|---|
| Role | Which actual product actor is operating this module? |
| Module | Which exact module is being written? |
| Scope | What is included and excluded? |
| Entry | From which menu/page/button? |
| Main flow | What exact sequence does the user operate? |
| Branches | Upload, skip, cancel, delete, save, preview, retry? |
| Subpages | List, detail, tab, modal, terminal, console, editor? |
| Controls | Every button, card, tab, menu, upload, generate action? |
| Data | What object is created, edited, cloned, referenced, deleted? |
| Async | What task starts, how progress shows, what counts as done? |
| Recovery | What happens on failure? |
| Unclear | What must be asked before writing? |

## Prototype Closure Checklist

Before writing a module from a prototype, check whether the design is implementable and closed:

| Check | Question |
|---|---|
| Entry | Can the user reach the module from a known entry? |
| Return path | Can the user return to the previous page or list? |
| Action feedback | Does every button show a visible result? |
| Async state | Is there loading, success, failure, and retry? |
| Data result | What object is created, updated, cloned, linked, deleted, or generated? |
| Ownership | Is the object global, user-scoped, workspace-scoped, project-scoped, session-scoped, or content-item-scoped? |
| Version/snapshot | Does binding a reusable resource need a copied snapshot or version? |
| Permission | Can another role or user see or edit it? |
| Empty state | What happens when no data exists? |
| Error state | What happens when loading, upload, generation, save, delete, or preview fails? |

If any answer is missing, write it as a product/R&D gap, not as a guessed requirement.

## Conflict Review Checklist

When meeting notes and existing PRD disagree:

1. Back up the PRD.
2. Read meeting notes and conflict list.
3. Treat conflict list as questions, not truth.
4. Build a conflict review table.
5. Build a product decision checklist with checkbox options.
6. Ask the user to select options or write conclusions.
7. Sync decisions into PRD.
8. Mark decisions as synced.

Decision record table:

```md
| ID | Product decision | Notes | Synced to PRD |
|---|---|---|---|
| D-01 | Option A | ... | No |
```

## Common Pitfalls To Prevent

| Pitfall | Prevention |
|---|---|
| Scope drift | Write confirmed modules only |
| Missing role boundary | Separate each actual role into its own section |
| Concept instead of spec | Add controls, data writes, errors, acceptance |
| Fake screenshots | Use only screenshots captured from the accessible product or prototype |
| Incomplete async flow | Wait for final success state before screenshot |
| Repeated screenshots | One image reference only once |
| Wrong object | Distinguish workspace, project, session, resource, generated item, and bound item |
| Resource ownership unclear | Confirm global resource vs workspace-bound resource vs snapshot |
| Meeting conflict blindly applied | Ask product to decide high-impact conflicts |
| Current vs phase 2 unclear | Mark phase clearly in Release and module notes |
| No source code | Use demo/staging/prototype evidence and mark backend gaps |
| Static design only | Do not claim workflow completion from static images |
| One-product assumptions | Keep role names, object names, and module names replaceable |

## Adaptability Checks

Before considering the skill output complete, check that the PRD method is not overfit to one product:

| Check | Requirement |
|---|---|
| Roles | Use the product's actual roles; do not hardcode a role pair unless that is the domain |
| Objects | Use actual domain objects; keep generic concepts such as draft/formal object, workspace, project, resource only when relevant |
| Screenshots | Support local app, demo URL, staging URL, or interactive prototype |
| Evidence | Separate observed UI from required backend behavior |
| Phasing | Mark current phase vs later phase without assuming a fixed release model |
| Conflict handling | Treat review notes and R&D conflict lists as evidence to verify, not commands to obey |
| Packaging | Package current docs and referenced screenshots regardless of product domain |

Run portability audit on final PRDs and reusable skill files:

```bash
node scripts/audit-prd-portability.js docs/product/PRD.md
```

When a previous product domain may have leaked into a new PRD, pass the suspected terms explicitly:

```bash
node scripts/audit-prd-portability.js --terms=term1,term2,term3 docs/product/PRD.md
```

## Technical Contract Patterns

Use these patterns when relevant:

### Draft vs Formal Object

| Object | Meaning |
|---|---|
| Draft | Temporary pre-confirmation state |
| Formal object | Created only after explicit confirm and backend success |

Example:

- DraftObject exists during configuration or generation.
- FormalObject exists only after Confirm returns objectId.

### Version Chain

Track versions for generated or edited content:

- structureVersion
- resourceVersion
- contentVersion
- generatedItemSetVersion

Only the current effective version should be used for final create, bind, or publish actions.

### Snapshot Reference

Use snapshots when global resources are bound to another object or workspace:

- Store source resource ID.
- Store source version.
- Store copied fields needed for learning.
- Later global edits do not mutate the bound snapshot.

### Idempotency

Define request IDs or object locks for:

- Confirm generate.
- Start generation.
- Upload and process file.
- Generate item sets.
- Generate artifacts.
- Delete file.

Repeated clicks must not create duplicate formal objects, duplicate tasks, or duplicate generated item sets.

## Packaging Checklist

When the user asks to package:

1. Copy current PRD.
2. Copy conflict review, decision checklist, recap docs.
3. Copy only screenshots referenced by the current PRD.
4. Add package manifest.
5. Zip the package.
6. Validate package-local image references.

Use the bundled package script:

```bash
node scripts/package-prd.js docs/product/PRD.md dist/prd-package docs/product/decision-checklist.md
```

Package manifest should include:

```md
# PRD Package

- Package time:
- Main PRD:
- Referenced screenshots:
- Included docs:
```
