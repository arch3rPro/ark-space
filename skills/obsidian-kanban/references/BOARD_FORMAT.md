# Obsidian Kanban Board Format

## Purpose

Use this reference when creating or editing a board file.
The goal is to preserve a clean Markdown board that the Obsidian Kanban plugin can continue to render.

## Board anatomy

A typical board file contains:

1. YAML frontmatter with `kanban-plugin: board`
2. Markdown headings for lists
3. Checkbox cards under each list
4. Optional nested lines for metadata or subtasks
5. An optional plugin settings block at the end

Example:

~~~~markdown
---
kanban-plugin: board
---

## Inbox

- [ ] Capture conference ideas @{2026-05-10} @@{10:00} #events

## Next Actions

- [ ] [[Draft keynote outline]] @{2026-05-03} @@{09:30} #writing
  - [ ] Confirm audience
  - [ ] Collect references

***

## Archive

%% kanban:settings
```
{
  "kanban-plugin": "board"
}
```
%%
~~~~

## Card conventions for this skill

If the board does not already have a different house style, use these conventions:

- First line: task title as a checkbox item
- Keep tags inline as hashtags such as `#project`, `#phone`, or `#writing`
- Add tags only when they are provided by the user, clearly implied by the task, or already part of the board's house style
- Keep dates inline as `@{YYYY-MM-DD}`
- Keep times inline as `@@{HH:mm}`
- Do not put priority in the title
- If priority must be displayed separately from the title, prefer a linked-note card and linked page metadata instead of ad hoc body lines
- Nested checkboxes for subtasks

Example lightweight card:

```markdown
- [ ] Review onboarding checklist @{2026-05-06} @@{14:00} #ops #people
  - [ ] Confirm owners
  - [ ] Update gaps
```

Example linked-note card:

```markdown
- [ ] [[Customer Interview Sprint]] @{2026-05-08} @@{16:00} #research #project
  - [ ] Draft questions
  - [ ] Schedule participants
```

## Priority convention

When the user wants four-quadrant priority shown with colored text and not mixed into the task title, use linked-note metadata.
The board card stays concise:

```markdown
- [ ] [[Customer Interview Sprint]] @{2026-05-08} @@{16:00} #research #project
```

The linked note stores the priority:

```yaml
---
priority: |
  <span style="color:#dc2626;"><strong>Q1 重要且紧急</strong></span>
---
```

And the board settings expose it:

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

Use these labels:

- `Q1 重要且紧急`
- `Q2 重要不紧急`
- `Q3 紧急不重要`
- `Q4 不重要不紧急`

Suggested colors:

- `Q1`: `#dc2626`
- `Q2`: `#ea580c`
- `Q3`: `#2563eb`
- `Q4`: `#6b7280`

## When to upgrade a card into a note

Prefer a linked note when the task needs:

- more than a few metadata lines
- longer written context
- links, embeds, or meeting notes
- ongoing progress history
- reusable project documentation

Keep the board card short even after upgrade.

## Settings block

Many boards end with a settings block like this:

~~~~markdown
---
kanban-plugin: board
---

%% kanban:settings
```
{
  "kanban-plugin": "board",
  "list-collapse": [false, false, false]
}
```
%%
~~~~

Editing rules:

- Preserve the YAML frontmatter. The board should keep `kanban-plugin: board`.
- Preserve the block if it already exists
- Keep it at the end of the file unless the board clearly uses a different placement
- Do not drop unknown keys
- If you edit JSON values, keep the JSON valid

## Archive lane

The archive section is special.
If you want `## Archive` to be treated as the board archive, place a thematic break `***` immediately before it.

Example:

```markdown
***

## Archive

- [ ] Older completed task
```

## Validation checklist

After editing:

1. Confirm the file still contains YAML frontmatter with `kanban-plugin: board`
2. Confirm every list still has a heading
3. Confirm every card is indented consistently under the correct list
4. Confirm nested metadata lines still belong to the intended card
5. Confirm subtask indentation still forms valid Markdown
6. Confirm the settings block, if present, still opens with `%% kanban:settings` and closes with `%%`
7. Confirm JSON inside the settings block is valid
8. If linked priority metadata is used, confirm the linked note frontmatter is valid YAML and the board keeps the `metadata-keys` entry for `priority`

## Preferred date format

Use `@{YYYY-MM-DD}` for dates and `@@{HH:mm}` for times unless the board is explicitly configured with different triggers.
These are the plugin defaults and align with `move-dates=true` boards that render date and time in the card footer.
