---
name: prd-create
description: Create or revise R&D-facing PRDs from product screenshots, prototypes, confirmed requirements, and review decisions. Keep the standard PRD document structure and preserve every functional-page field and field restriction; write clear workflows as a screenshot followed by concise requirements, and add branches, interaction constraints, or page flows only when they change implementation.
---

# PRD Create

Keep the standard PRD document structure. Preserve every functional-page field and its restriction: field name, control/type, required state, default value, format, range, validation, linkage, editability, visibility, permission, and persistence rule when applicable. Simplify only redundant workflow prose; do not mistake product fields for PRD template fields.

## Default PRD Format

1. Start from `assets/prd-template.md`; retain its standard PRD sections.
2. In each Solution module, use the screenshot-first form in `assets/module-workflow-template.md`.
3. Put a screenshot under a short screen or scenario heading.
4. Put `需求描述` immediately below the screenshot.
5. For a screen with functional fields, put its `页面字段与限制` table directly below the description. Preserve all known field rules in that table.
6. Add branch flows, interaction constraints, page flows, data writes, error recovery, or technical contracts only when the screenshot, requirement description, and field table cannot express behavior R&D needs to implement.
7. Mark an unknown as `待确认`; never invent behavior or omit a known field restriction.

One screenshot may support several clear requirements. Do not require a screenshot for every click. Use relative image paths and short alt text. When screenshots are design references rather than executable product evidence, describe their behavior as requirements, not observed facts.

## Page Field Rules

- Treat a page field as any input, selector, switch, upload, displayed value, editable item, or generated field that affects behavior or data.
- Keep its validation and restriction with the field: required/default, length or range, allowed format/value, uniqueness, dependency, editability, visibility, permission, save timing, and error message when known.
- Write `不适用` only for a restriction that genuinely does not apply. Do not use it to hide an unknown; use `待确认` instead.
- Do not duplicate field rules in branch/flow sections. Reference the field table when a later workflow section depends on it.

## Add Workflow Detail Only When Needed

Add an expanded section when it changes implementation or QA, including: a meaningful branch or recovery path; an async state; a permission difference; a data write not covered by a field; coupled page transitions; or cross-module ownership, versioning, snapshot, idempotency, or integration rules.

Use `references/prd-rnd-workflow.md` and the execution checklist when producing a detailed R&D-ready or package-ready PRD. Run the readiness verifier before making either claim:

```bash
node <skill-path>/scripts/verify-prd-gates.js PRD.md PRD_EXECUTION_CHECKLIST.md
```

## Resources

- `assets/prd-template.md`: standard R&D PRD shell.
- `assets/module-workflow-template.md`: screenshot-first module template with functional-page fields and optional expanded workflow sections.
- `references/prd-rnd-workflow.md`: detailed workflow, evidence, decision, and technical-contract controls.
- `scripts/validate-prd-images.js`: validate Markdown image links.
- `scripts/package-prd.js`: package a PRD and referenced screenshots.
