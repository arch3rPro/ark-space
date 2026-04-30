# Obsidian Kanban Board Format

## Purpose

Use this reference when creating or editing a board file.
The goal is to preserve a clean Markdown board that the Obsidian Kanban plugin can continue to render.

## Board anatomy

A typical board file contains:

1. Markdown headings for lists
2. Checkbox cards under each list
3. Optional nested lines for metadata or subtasks
4. An optional plugin settings block at the end

Example:

~~~~markdown
## Inbox

- [ ] Capture conference ideas
  - priority: P2
  - due: 2026-05-10
  - tags: #events

## Next Actions

- [ ] [[Draft keynote outline]]
  - priority: P1
  - due: 2026-05-03
  - [ ] Confirm audience
  - [ ] Collect references

%% kanban:settings
```json
{
  "kanban-plugin": "board"
}
```
%%
~~~~

## Card conventions for this skill

If the board does not already have a different house style, use these conventions:

- First line: task title as a checkbox item
- Nested metadata lines:
  - `priority: P1`, `P2`, or `P3`
  - `due: YYYY-MM-DD`
  - `tags: #tag-one #tag-two`
- Nested checkboxes for subtasks

Example lightweight card:

```markdown
- [ ] Review onboarding checklist
  - priority: P2
  - due: 2026-05-06
  - tags: #ops #people
  - [ ] Confirm owners
  - [ ] Update gaps
```

Example linked-note card:

```markdown
- [ ] [[Customer Interview Sprint]]
  - priority: P1
  - due: 2026-05-08
  - tags: #research #project
  - [ ] Draft questions
  - [ ] Schedule participants
```

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
%% kanban:settings
```json
{
  "kanban-plugin": "board",
  "list-collapse": [false, false, false]
}
```
%%
~~~~

Editing rules:

- Preserve the block if it already exists
- Keep it at the end of the file unless the board clearly uses a different placement
- Do not drop unknown keys
- If you edit JSON values, keep the JSON valid

## Validation checklist

After editing:

1. Confirm every list still has a heading
2. Confirm every card is indented consistently under the correct list
3. Confirm nested metadata lines still belong to the intended card
4. Confirm subtask indentation still forms valid Markdown
5. Confirm the settings block, if present, still opens with `%% kanban:settings` and closes with `%%`
6. Confirm JSON inside the settings block is valid

## Preferred date format

Use `YYYY-MM-DD` by default.
This keeps the board easy to sort, search, and compare across tools.
