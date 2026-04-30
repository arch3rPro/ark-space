---
name: obsidian-kanban
description: Create and maintain Obsidian Kanban boards stored in Markdown, with a GTD-friendly workflow for capturing tasks, adding cards, organizing lists, and maintaining task details such as inline tags, Kanban date and time tokens, linked-note priority metadata, and subtasks. Use when working with Obsidian Kanban board files, when the user asks to add or manage cards, or when a lightweight task card should be upgraded into a linked note for more complex project tracking.
---

# Obsidian Kanban

## Overview

Create and maintain Obsidian Kanban boards as durable task systems rather than one-off lists.
Default to a mixed task model: capture simple work as lightweight cards, then upgrade complex work into linked notes when the task needs more context, history, or attachments.
For GTD boards, prefer trusted list semantics over generic priority queues: the board should clarify what the task is, where it belongs, and what the next visible action is.

## Workflow

1. Identify the target board file and read the current structure before editing.
2. Preserve the existing board frontmatter, list names, archive separator, and `kanban:settings` block unless the user asks for structural changes.
3. Decide whether each task should remain a lightweight card or be upgraded to a linked note.
4. Apply the task conventions below consistently so future edits remain predictable.
5. Validate the board after editing: headings still align with lists, cards still sit under the intended list, indentation remains valid Markdown, and the settings block is still intact.

## Task Model

### Lightweight card

Use a lightweight card when the task is actionable without extra documentation.
Prefer this shape:

```markdown
- [ ] Prepare quarterly planning draft @{2026-05-02} @@{09:00} #planning #work #computer
  - [ ] Pull current metrics
  - [ ] Draft agenda
```

Use this model for fast capture, inbox triage, and routine task maintenance.
Treat `priority` as optional rather than foundational. In GTD boards, contexts and list placement should carry most of the organizational load.
Do not invent `tags:` or `due:` pseudo-fields. Prefer inline hashtags and the board's configured date/time triggers, which default to `@{date}` and `@@{time}`.
If the user wants visible priority that does not live in the title, do not fake it with extra card-body lines. The plugin renders those as ordinary body text. Upgrade the task to a linked note and surface `priority` through linked page metadata instead.

### Linked-note card

Upgrade a task to a linked note when any of these are true:

- The description is becoming long or unstable
- The task needs research notes, meeting notes, or attachments
- The task will stay active for multiple sessions
- The task is really a project with multiple outcomes or decision points

Prefer this shape:

```markdown
- [ ] [[Quarterly Planning Draft]] @{2026-05-02} @@{09:00} #planning #project #computer
  - [ ] Pull current metrics
  - [ ] Draft agenda
```

Keep the card concise and move long-form details into the linked note.
When the board uses linked page metadata, keep priority in linked-note frontmatter rather than in the card body. A verified pattern is:

```yaml
---
priority: |
  <span style="color:#ea580c;"><strong>Q2 重要不紧急</strong></span>
---
```

and a matching board setting:

```json
{
  "metadata-keys": [
    {
      "metadataKey": "priority",
      "label": "",
      "shouldHideLabel": true,
      "containsMarkdown": true
    }
  ]
}
```

See [references/METADATA_AND_GOTCHAS.md](references/METADATA_AND_GOTCHAS.md).
For GTD, any item in `Projects` should normally be a linked-note card and should correspond to at least one separate card in `Next Actions`.

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
5. For GTD boards, prefer context tags such as `#computer`, `#phone`, `#home`, or `#errands` over inventing numeric priority for every task.
6. Store tags inline as hashtags and dates inline as Kanban tokens instead of writing label-style metadata lines.
7. If the user needs four-quadrant priority displayed separately from the title, prefer a linked-note card with frontmatter-backed metadata.

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

On GTD boards, use these defaults:

- Use due dates only when the date is real and meaningful
- Use tags to encode context, area, or theme
- Use four-quadrant priority labels sparingly, mainly when the user already works that way
- When priority must be visible, prefer linked-note metadata instead of card-body text
- Avoid turning `Calendar` into a catch-all list for work that is merely important
- Prefer `@{YYYY-MM-DD}` and `@@{HH:mm}` for the board's own date and time metadata

### Triage the board

When reorganizing a GTD board, use these default meanings:

- `Inbox`: newly captured work that still needs clarification
- `Next Actions`: the next concrete tasks that can be done now
- `Waiting For`: blocked tasks that depend on other people or external input
- `Calendar`: tasks or reminders that belong on a specific date or should only appear at a specific time
- `Projects`: multi-step outcomes that need ongoing decomposition and at least one corresponding next action
- `Someday/Maybe`: intentionally deferred ideas and possible future work
- `Done`: recently completed work kept temporarily before archival
- `Archive`: historical items the user no longer needs to see regularly

## Editing Rules

- Treat the board file as the source of truth. Do not rewrite it into another system.
- Keep list headings, card indentation, and checkbox structure stable.
- Ensure the board keeps `kanban-plugin: board` in YAML frontmatter so Obsidian Kanban recognizes the file as a board.
- Do not invent plugin settings unless the user asked for them or the board clearly depends on them.
- Preserve the `%% kanban:settings` block and any JSON keys inside it unless you are deliberately editing board settings.
- If the board uses an archive lane, preserve the `***` separator immediately before `## Archive`.
- When the board already uses linked notes, do not silently switch back to pure cards.
- When a task becomes complex, prefer upgrading it rather than overloading a single card with paragraphs of text.
- Prefer one-line card metadata for board-native fields: inline hashtags for tags, `@{}` for dates, and `@@{}` for times.
- Do not put four-quadrant priority in the task title.
- When the user wants priority displayed separately from the title, store it in linked-note frontmatter and surface it with the board's `metadata-keys` setting.

## References

- Use [references/BOARD_FORMAT.md](references/BOARD_FORMAT.md) for board anatomy, card conventions, and validation checks.
- Use [references/GTD_TEMPLATE.md](references/GTD_TEMPLATE.md) for the default GTD board template and list semantics.
- Use [references/METADATA_AND_GOTCHAS.md](references/METADATA_AND_GOTCHAS.md) for linked page metadata, note templates, archive settings, and frontmatter pitfalls.
