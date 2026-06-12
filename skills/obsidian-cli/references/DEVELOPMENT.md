# Plugin and Theme Development Reference

Use these commands when the task is plugin, theme, or Obsidian UI debugging work rather than ordinary vault management.

## Develop/Test Cycle

1. Reload the plugin or theme after code changes:

```bash
obsidian plugin:reload id=my-plugin
```

2. Check for app errors and fix them before continuing:

```bash
obsidian dev:errors
```

3. Verify behavior visually with screenshots or DOM inspection:

```bash
obsidian dev:screenshot path=screenshot.png
obsidian dev:dom selector=".workspace-leaf" text
```

4. Check console output for warnings or unexpected logs:

```bash
obsidian dev:console level=error
```

## Additional Developer Commands

Run JavaScript in the app context:

```bash
obsidian eval code="app.vault.getFiles().length"
```

Inspect CSS values:

```bash
obsidian dev:css selector=".workspace-leaf" prop=background-color
```

Toggle mobile emulation:

```bash
obsidian dev:mobile on
```

Run `obsidian help` for any newer developer commands, including debugger and CDP-related actions.
