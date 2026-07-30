# PRD Execution Checklist

Copy this file beside the PRD before writing a detailed R&D-ready PRD. Keep unchecked items as evidence of a blocker; do not check an item based on intent alone.

- PRD: `path/to/PRD.md`
- Evidence mode: `local-app | demo-staging | interactive-prototype | requirements-only`
- Product access: `URL, local command, or prototype link`
- Screenshot directory: `relative/path/from/PRD`
- Active module: `none`
- Decision checklist: `path/to/decision-checklist.md | none`
- Blocking decisions: `none | D-01, D-02`
- Product access authorized: `yes | no`

## Decision Gate Before Product Access

Before starting a local app, opening a browser, capturing screenshots, or writing detailed workflow specifications:

1. List every decision that affects the active module in `assets/decision-checklist-template.md`.
2. Mark each decision `confirmed`, `non-blocking`, or `blocking`.
3. Record the decision-checklist path and blocking IDs above.
4. Set `Product access authorized` to `yes` only after an authoritative product source or the user confirms the active module workflow and every blocking decision is resolved.

`blocking` means stop. It prohibits screenshots and detailed specifications; “marked as open” is not permission to continue. `non-blocking` means the decision is recorded but cannot alter the active module's confirmed workflow, ownership, or acceptance criteria.

## Action Preflight

Before any browser, dev-server, or screenshot tool action, write this exact status in the working response or execution log:

```text
Gate check:
- Active module: …
- Workflow confirmed: yes/no
- Blocking decisions: none / IDs
- Product access authorized: yes/no
- Allowed next action: …
```

If any value is `no` or any blocking ID remains, the only allowed next action is decision/workflow confirmation. Do not start product access.


## Non-Bulk Drafting Rule

Write and verify exactly one module at a time. Before drafting a module, set `Active module` to its exact module name and leave every later module untouched. Do not generate a complete PRD body, an all-module outline with detailed steps, or speculative next-module text “for speed.”

For each module, complete this loop before starting another:

1. Complete the Decision Gate and confirm its workflow record.
2. Perform Action Preflight; if product access is not authorized, stop for decision/workflow confirmation.
3. Execute its steps in the accessible product or prototype and capture its screenshots.
4. Write only that module's detailed section.
5. Check its three module gates below.
6. Run `node scripts/verify-prd-gates.js <prd.md> <checklist.md> --module "<module name>"`.
7. Record the successful result, then set the next module as active.


Set `Active module` to `none` only after every scoped module is verified. The full readiness verifier rejects a PRD while any module remains active.

## Active Module Gates

- [ ] Module workflow record is complete for the active module.
- [ ] Screenshots are captured for every active-module workflow step.
- [ ] The active module is written and checked before any next module begins.

## Verified Module Log

| Module | Module verifier result | Evidence or blocker |
|---|---|---|
|  | `verified` / `blocked` |  |


## Module Workflow Records

Create one record for every module before writing its detailed section.

| Module | Role | Included scope | Excluded scope | Entry points | Main workflow confirmed | Data result | Open questions status | Confirmation source |
|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  | Yes / No |  | confirmed / non-blocking / blocking | user / authoritative source |


Do not mark a workflow as confirmed from source code, mock responses, static design, old screenshots, or another module's behavior. Its evidence must come from the active module's confirmed product decision or authoritative product source. `blocking` means the module cannot start screenshots or detailed specifications.

## Completion Gates

- [ ] Sources, meeting decisions, and conflict lists were read; conflicts were treated as questions until confirmed.
- [ ] Product access and evidence mode were recorded before drafting detailed behavior.
- [ ] Every module workflow record was completed before its detailed PRD section was written.
- [ ] Every detailed workflow uses explicit step headings with operation, page response, controls, R&D requirements, constraints, exceptions, and evidence status.
- [ ] Each workflow step has a browser screenshot captured from the accessible product or prototype; screenshots are not static design, desktop, meeting, or historical images.
- [ ] Observed UI, required behavior, unverified behavior, and decision-needed gaps are labeled instead of inferred.
- [ ] `node scripts/validate-prd-images.js <prd.md>` passed with no missing, duplicate, absolute, or empty links.
- [ ] `node scripts/verify-prd-gates.js <prd.md> <checklist.md>` passed.
- [ ] Review decisions were synchronized into the PRD, or no review decision was applicable.

## Requirements-Only Exception

If no accessible product or interactive prototype exists, set the evidence mode to `requirements-only`, leave the detailed workflow and screenshot gates unchecked, and deliver a **requirements draft** only. It cannot pass the ready gate or be described as an R&D-ready PRD.

## Screenshot Quarantine

If screenshots were captured before the Decision Gate passed, delete them or move them outside the PRD asset directory into a clearly named quarantine location. Do not reference quarantined screenshots in the PRD, inventory, or package. Record the discard reason in the decision checklist or execution log.
