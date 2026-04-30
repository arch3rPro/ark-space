---
name: obsidian-kanban
description: Create and maintain Obsidian Kanban boards stored in Markdown, with a GTD-friendly workflow for capturing tasks, adding cards, organizing lists, and maintaining task details such as priority, due dates, tags, and subtasks. Use when working with Obsidian Kanban board files, when the user asks to add or manage cards, or when a lightweight task card should be upgraded into a linked note for more complex project tracking.
---

# Obsidian Kanban

## Overview

Create and maintain Obsidian Kanban boards as durable task systems rather than one-off lists.
Default to a mixed task model: capture simple work as lightweight cards, then upgrade complex work into linked notes when the task needs more context, history, or attachments.

## Workflow

1. Identify the target board file and read the current structure before editing.
2. Preserve the existing board format, list names, and `kanban:settings` block unless the user asks for structural changes.
3. Decide whether each task should remain a lightweight card or be upgraded to a linked note.
4. Apply the task conventions below consistently so future edits remain predictable.
5. Validate the board after editing: headings still align with lists, cards still sit under the intended list, indentation remains valid Markdown, and the settings block is still intact.

## Task Model

### Lightweight card

Use a lightweight card when the task is actionable without extra documentation.
Prefer this shape:

```markdown
- [ ] Prepare quarterly planning draft
  - priority: P1
  - due: 2026-05-02
  - tags: #planning #work
  - [ ] Pull current metrics
  - [ ] Draft agenda
```

Use this model for fast capture, inbox triage, and routine task maintenance.

### Linked-note card

Upgrade a task to a linked note when any of these are true:

- The description is becoming long or unstable
- The task needs research notes, meeting notes, or attachments
- The task will stay active for multiple sessions
- The task is really a project with multiple outcomes or decision points

Prefer this shape:

```markdown
- [ ] [[Quarterly Planning Draft]]
  - priority: P1
  - due: 2026-05-02
  - tags: #planning #project
  - [ ] Pull current metrics
  - [ ] Draft agenda
```

Keep the card concise and move long-form details into the linked note.
When the board uses linked page metadata, make sure the note structure remains compatible with the board's expectations. See [references/METADATA_AND_GOTCHAS.md](references/METADATA_AND_GOTCHAS.md).

## Common Operations

### Create a new GTD board

When the user asks for a new board, default to the GTD structure in [references/GTD_TEMPLATE.md](references/GTD_TEMPLATE.md) unless they ask for a custom workflow.
New tasks should normally start in `Inbox` unless the user has already provided enough information to place them elsewhere.

### Add cards

When adding cards:

1. Preserve the board's existing card style if it is already consistent.
2. If the board has no clear style yet, use the task convention from this skill.
3. Add missing task details only when the user provided them or when they are implied strongly enough to be useful.
4. Prefer ISO dates (`YYYY-MM-DD`) for due dates to keep them sortable and unambiguous.

### Maintain task details

When the user asks to manage tasks, support these edits directly in the board:

- Set or change priority
- Add or adjust due dates
- Add tags
- Add, remove, or reorder subtasks
- Move cards between lists
- Mark tasks or subtasks complete
- Split large cards into several smaller cards
- Upgrade a task into a linked note

### Triage the board

When reorganizing a GTD board, use these default meanings:

- `Inbox`: newly captured work that still needs clarification
- `Next Actions`: the next concrete tasks that can be done now
- `Waiting`: blocked tasks that depend on other people or external input
- `Scheduled`: tasks driven by a date or near-term time window
- `Projects`: multi-step outcomes that need ongoing decomposition
- `Someday`: intentionally deferred ideas
- `Done`: recently completed work
- `Archive`: historical items the user no longer needs to see regularly

## Editing Rules

- Treat the board file as the source of truth. Do not rewrite it into another system.
- Keep list headings, card indentation, and checkbox structure stable.
- Do not invent plugin settings unless the user asked for them or the board clearly depends on them.
- Preserve the `%% kanban:settings` block and any JSON keys inside it unless you are deliberately editing board settings.
- When the board already uses linked notes, do not silently switch back to pure cards.
- When a task becomes complex, prefer upgrading it rather than overloading a single card with paragraphs of text.

## References

- Use [references/BOARD_FORMAT.md](references/BOARD_FORMAT.md) for board anatomy, card conventions, and validation checks.
- Use [references/GTD_TEMPLATE.md](references/GTD_TEMPLATE.md) for the default GTD board template and list semantics.
- Use [references/METADATA_AND_GOTCHAS.md](references/METADATA_AND_GOTCHAS.md) for linked page metadata, note templates, archive settings, and frontmatter pitfalls.
