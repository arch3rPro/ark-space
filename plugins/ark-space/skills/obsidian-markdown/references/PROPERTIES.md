# Properties (Frontmatter) Reference

Properties use YAML frontmatter at the start of a note. Prefer Obsidian-native properties and file metadata before adding custom fields.

Do not add custom properties by default. Use the file name instead of a duplicated `title`, Obsidian file metadata instead of duplicated date/path fields, links/backlinks instead of manual relationship fields, and tags instead of custom category fields when tags satisfy the request. Add custom properties only when the user asks for them, the vault already has a matching schema, or a requested workflow needs structured data that Obsidian cannot infer natively.

```yaml
---
tags:
  - project
  - important
aliases:
  - My Note
  - Alternative Name
cssclasses:
  - custom-class
# Custom fields below are examples only; add them only when needed.
status: in-progress
rating: 4.5
completed: false
due: 2024-02-01T14:30:00
---
```

## Property Types

| Type | Example |
|------|---------|
| Text | `title: My Title` |
| Number | `rating: 4.5` |
| Checkbox | `completed: true` |
| Date | `date: 2024-01-15` |
| Date & Time | `due: 2024-01-15T14:30:00` |
| List | `tags: [one, two]` or YAML list |
| Links | `related: "[[Other Note]]"` |

## Default Properties

- `tags` - Note tags (searchable, shown in graph view)
- `aliases` - Alternative names for the note (used in link suggestions)
- `cssclasses` - CSS classes applied to the note in reading/editing view

## Tags

```markdown
#tag
#nested/tag
#tag-with-dashes
#tag_with_underscores
```

Tags can contain: letters (any language), numbers (not first character), underscores `_`, hyphens `-`, forward slashes `/` (for nesting).

In frontmatter:

```yaml
---
tags:
  - tag1
  - nested/tag2
---
```
