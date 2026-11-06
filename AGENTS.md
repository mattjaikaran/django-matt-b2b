# Agent rules

## Migrations

- Migrations are linearized, never merged. **Never run
  `makemigrations --merge`** and never add a merge migration.
- Never edit a migration that is already on `main`. Add a new migration
  instead.
- After you add or change a model or a migration, and before you push, run
  `make migrations-check`.
- On a migration conflict (two leaf nodes, or the same number as `main`), run
  `make migrations-renumber` (dry run), then
  `make migrations-renumber ARGS=--apply`. It renames only your own files
  after the latest migration on `main`.
- When it prints `escalate to owner` (`RunPython`, `RunSQL`, `RemoveField`,
  `RenameField`, `DeleteModel`, `replaces`, or a clashing `AlterField`), stop
  and report it.
- Rule exceptions for django-safe-migrations go in
  `config/migration_lint.py`. Existing findings sit in
  `scripts/baselines/migration-safety.json`. Inline
  `# safe-migrations: ignore` comments are banned.
