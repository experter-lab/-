# Repository Guidelines

## Codex App / CLI Shared Context

This repository uses a safe file-based workflow to make Codex App and Codex CLI share context.

Before starting substantial work:

1. Read `.codex/context.md` for the current shared context.
2. Read `docs/codex-worklog.md` for curated cross-client notes.
3. If CLI history is relevant, read `docs/codex-cli-history.md` after it has been regenerated.

After completing meaningful work:

1. Add a concise dated note to `docs/codex-worklog.md`.
2. Update `.codex/context.md` if the active project direction, constraints, or setup changed.
3. Keep generated exports readable and do not hand-edit `%USERPROFILE%\.codex\sessions`.

To refresh CLI history for Codex App, run from the repository root:

```powershell
powershell -ExecutionPolicy Bypass -File tools/export-codex-cli-history.ps1 -ProjectOnly
```

Use `-AllProjects` only when you intentionally want CLI sessions from other folders included.

## Safety Rules

- Treat `%USERPROFILE%\.codex\sessions` as read-only source data.
- Do not edit private Codex app databases or unsupported internal state files.
- Prefer Markdown summaries for portable context between tools.
