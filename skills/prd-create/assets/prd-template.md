# {Product Name} R&D PRD

> Audience: R&D, QA, integration, and implementation stakeholders.
> Evidence mode: {local app | demo/staging URL | interactive prototype | static screenshots | requirements only}

## 1. Summary

## 2. Contacts

| Area | Owner | Notes |
|---|---|---|
| Product decision |  |  |
| R&D implementation |  |  |
| QA validation |  |  |
| Design/prototype |  |  |

## 3. Background

## 4. Objective

## 5. Users And Roles

| Role | Description | Included modules | Excluded modules |
|---|---|---|---|

## 6. Value

## 7. Solution

### 7.1 Writing Rules

- Keep the standard PRD sections concise.
- Use one module section for each scoped product area.
- For every clear workflow, put the screenshot first and the requirement description immediately below it.
- Put a `页面字段与限制` table below every screenshot that contains functional fields. Preserve field name, control/type, required/default state, validation, linkage, permission, and persistence rules. Add branch flows, interaction constraints, page flows, data writes, error recovery, or technical contracts only when they add behavior the screenshot, requirement description, and field table cannot express.
- Mark unresolved requirements as `待确认`; do not invent behavior.

### 7.2 Module Specs

Use `module-workflow-template.md` for each module. Put the screenshot, requirement description, and functional-page field table first in every step; add its later workflow sections only when needed.

## 8. Cross-Module Technical Contracts

Add when cross-module ownership, versions, snapshots, integrations, or idempotency need an explicit rule.

## 9. Error And Recovery Standards

Record shared rules that cannot be expressed clearly in the affected screenshot requirement.

## 10. Release Scope

| Module | Current phase | Later phase | Notes |
|---|---|---|

## 11. Acceptance Summary

| Area | Acceptance item | Evidence |
|---|---|---|

## 12. Open Decisions

| ID | Decision needed | Options | Owner | Status |
|---|---|---|---|---|
