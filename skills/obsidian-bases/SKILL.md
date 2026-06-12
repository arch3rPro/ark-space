---
name: obsidian-bases
description: Create and edit Obsidian Bases (.base files) with views, filters, formulas, and summaries. Use when working with .base files, creating database-like views of notes, or when the user mentions Bases, table views, card views, filters, or formulas in Obsidian.
---

# Obsidian Bases Skill

## Workflow

1. Create or open the target `.base` file and keep it valid YAML.
2. Define scope with the smallest useful `filters`.
3. Prefer existing file metadata and note properties before inventing new schema.
4. Add formulas only when the requested view cannot be expressed with raw properties.
5. Add one or more views with a clear `order` and optional grouping or summaries.
6. Validate YAML syntax, formula references, and quoted strings before finishing.

## Property Discipline

Prefer Obsidian-native file properties and existing note properties before introducing new frontmatter fields.

- Use `file.name`, `file.basename`, `file.folder`, `file.path`, `file.ext`, `file.ctime`, `file.mtime`, `file.tags`, `file.links`, `file.backlinks`, `file.embeds`, and `file.properties` when they satisfy the request.
- Prefer `file.hasTag(...)`, `file.inFolder(...)`, and `file.hasLink(...)` for scope filters instead of adding duplicate custom metadata.
- Do not add custom properties such as `status`, `priority`, `due`, `category`, `type`, `author`, `pages`, or `cover` unless the user asks for them, the vault already uses them, or the requested view cannot be built from native metadata.
- When custom note properties are needed, keep them minimal and make the Base consume the existing schema rather than inventing extra fields.

## Minimal Schema

Base files use the `.base` extension and contain valid YAML.

```yaml
filters:
  and: []

formulas:
  age_days: '(now() - file.ctime).days'

properties:
  formula.age_days:
    displayName: "Age (days)"

views:
  - type: table
    name: "All Notes"
    order:
      - file.name
      - formula.age_days
```

## Filters

Use string expressions for simple cases and nested `and` / `or` / `not` objects when the logic needs structure.

```yaml
filters:
  and:
    - 'file.ext == "md"'
    - file.hasTag("project")
```

```yaml
filters:
  or:
    - file.hasTag("book")
    - and:
        - file.inFolder("Reading")
        - 'status != "done"'
```

Prefer global filters for the overall dataset and per-view filters only when one view needs a narrower slice.

## Formulas

Formulas are shared computed properties. Keep them null-safe and easy to read.

```yaml
formulas:
  days_until_due: 'if(due_date, (date(due_date) - today()).days, "")'
  day_of_week: 'date(file.basename).format("dddd")'
```

Common rules:

- Date subtraction returns a Duration, so access `.days`, `.hours`, or another numeric field before rounding.
- Guard optional properties with `if()` instead of assuming every note has the field.
- Every `formula.X` used in `properties`, `order`, or `summaries` must exist in `formulas`.

## Views

Supported view types are `table`, `cards`, `list`, and `map`.

- Use `table` for sortable indexes and status views.
- Use `cards` for gallery-style browsing with cover or summary fields.
- Use `list` for compact navigation.
- Use `map` only when the vault already has latitude and longitude style properties and the Maps plugin is relevant.

Example:

```yaml
views:
  - type: table
    name: "Active Tasks"
    filters:
      and:
        - 'status != "done"'
    order:
      - file.name
      - status
      - due_date
    groupBy:
      property: status
      direction: ASC
    summaries:
      due_date: Latest
```

## Common Pitfalls

- Quote strings that contain YAML-special characters such as `:`, `#`, `[`, `]`, `{`, `}`, or `,`.
- Wrap formulas containing double quotes in single quotes.
- Do not reference `formula.X` unless `X` is defined in `formulas`.
- Reuse existing note properties when possible instead of creating a new tracking schema for every view.

## References

- [Bases Syntax](https://help.obsidian.md/bases/syntax)
- [Functions](https://help.obsidian.md/bases/functions)
- [Views](https://help.obsidian.md/bases/views)
- [Formulas](https://help.obsidian.md/formulas)
- [Complete Functions Reference](references/FUNCTIONS_REFERENCE.md)
