---
name: migration-conflict
description: Resolve a Django migration conflict on this repo by renumbering your own files, never by merging. Use when migrations-check reports two leaf nodes, a migration number that clashes with origin/main, or django-safe-migrations SM027.
---

# Resolve a migration conflict

The policy is in [AGENTS.md](../../../AGENTS.md#migrations); this is the
procedure.

1. **Reproduce.** Run `make migrations-check`. It fails under `leaf` or `lint`
   (SM027: several leaves) or because a number already exists on
   `origin/main`.
2. **Refresh the base.** Fetch `origin/main`; the renumber script compares
   against it and cannot plan without it.
3. **Plan.** Run `make migrations-renumber` (dry run). It lists the files it
   would rename after the latest migration on `origin/main`.
4. **Apply.** Run `make migrations-renumber ARGS=--apply`. It renames only
   your own migration files, fixes their dependencies, re-runs the checks and
   migrates a scratch database.
5. **Escalate when told.** If the output contains `escalate to owner`
   (`RunPython`, `RunSQL`, `RemoveField`, `RenameField`, `DeleteModel`,
   `replaces`, or a clashing `AlterField`), stop and report the file and the
   message. Do not hand-edit dependencies or delete migrations to get past it.
6. **Confirm.** Run `make migrations-check` again, then the suite.

The scripts are `scripts/db/check_migrations.py` and
`scripts/db/renumber_migrations.py`; run them directly only when you need
`--base` or `--only`.
