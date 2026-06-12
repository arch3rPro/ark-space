---
name: obsidian-cli
description: Interact with Obsidian vaults using the Obsidian CLI to read, create, search, and manage notes, tasks, properties, and more. Also supports plugin and theme development with commands to reload plugins, run JavaScript, capture errors, take screenshots, and inspect the DOM. Use when the user asks to interact with their Obsidian vault, manage notes, search vault content, perform vault operations from the command line, or develop and debug Obsidian plugins and themes.
---

# Obsidian CLI

Use the `obsidian` CLI to interact with a running Obsidian instance. Requires Obsidian to be open.

## Command Reference

Run `obsidian help` to see the current command set. Full docs: https://help.obsidian.md/cli

## Syntax

- Parameters take a value with `=`.
- Flags are boolean switches with no value.
- Quote values with spaces.
- Use `\n` for multiline content and `\t` for tabs.

```bash
obsidian create name="My Note" content="# Hello"
obsidian create name="My Note" silent overwrite
```

## Targeting

Many commands accept `file` or `path`:

- `file=<name>` resolves like a wikilink.
- `path=<path>` uses an exact vault-relative path such as `folder/note.md`.

Commands target the most recently focused vault by default. Use `vault=<name>` as the first parameter to select another vault.

```bash
obsidian vault="My Vault" search query="project alpha"
```

## Common Patterns

```bash
obsidian read file="My Note"
obsidian create name="New Note" content="# Hello" template="Template" silent
obsidian append file="My Note" content="New line"
obsidian search query="search term" limit=10
obsidian daily:read
obsidian daily:append content="- [ ] New task"
obsidian property:set name="status" value="done" file="My Note"
obsidian tasks daily todo
obsidian tags sort=count counts
obsidian backlinks file="My Note"
```

Use `--copy` to copy output to the clipboard. Use `silent` to prevent files from opening. Use `total` on list-style commands to get a count.

## Development Work

When the task is plugin, theme, or UI debugging work, keep the main skill light and load the extra workflow only when needed:

- [Plugin and Theme Development Reference](references/DEVELOPMENT.md)

## Guidance

- Prefer the narrowest command that answers the request instead of reaching for `eval` first.
- For note content changes, target an exact file or path when ambiguity would be risky.
- For development tasks, reload the plugin or theme and check for errors before claiming success.
