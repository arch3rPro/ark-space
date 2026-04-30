# Metadata And Gotchas

## Local and global settings

The Kanban plugin supports both global settings and per-board settings.
If a board already contains a settings block, treat that board-local configuration as intentional and preserve it unless the user asks for changes.
Also preserve the board frontmatter key `kanban-plugin: board`; without it, the file may open as a normal Markdown note instead of a Kanban board.

Reference:
- https://publish.obsidian.md/kanban/Settings/Local%20vs.%20global%20settings

## Linked page metadata

When a card links to a note, the plugin can display frontmatter or Dataview metadata from the first linked page under the card.
This is useful when upgrading a simple card into a richer project note while keeping a concise board view.

Good fields to surface:

- owner
- status
- due
- next-review
- summary
- priority

For four-quadrant priority, a verified board-local settings shape is:

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

This lets the board render `priority` below the card without putting it into the title.

Reference:
- https://publish.obsidian.md/kanban/Settings/Linked%20page%20metadata

## Note templates

When creating notes from cards, the plugin can apply an Obsidian Templates or Templater template.
Use this when the board is expected to generate repeatable project or task notes with consistent structure.

Reference:
- https://publish.obsidian.md/kanban/Settings/Note%20template

## Note folder

If the board is configured to create notes from cards, check whether the board expects a specific note folder before creating linked notes.

Reference:
- https://raw.githubusercontent.com/obsidian-community/obsidian-kanban/main/docs/Settings/Note%20folder.md

## Frontmatter quoting pitfall

If linked-note metadata includes links or image embeds in frontmatter, they may need to be wrapped in quotes to render correctly in cards.
If the metadata contains HTML for colored priority text, invalid quoting can break the YAML entirely and the board will show nothing.
For styled priority, prefer a YAML block scalar:

```yaml
---
priority: |
  <span style="color:#dc2626;"><strong>Q1 重要且紧急</strong></span>
---
```

Example:

```yaml
---
delivery-notes: "![[LinkToImage.png]]"
---
```

If metadata is not displaying as expected, quoting is a good first fix to try.

Reference:
- https://raw.githubusercontent.com/obsidian-community/obsidian-kanban/main/docs/FAQs/Frontmatter%20limitations%20%26%20gotchas.md

## Archive formatting

Archive timestamps can be formatted by board settings.
If the user wants archived cards to carry timestamps, preserve the board's existing format or edit it deliberately rather than rewriting card text ad hoc.

Reference:
- https://publish.obsidian.md/kanban/Settings/Archive%20date%20time%20format
