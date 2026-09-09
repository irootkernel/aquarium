# Production setup status dossier

## Authority

**Roadmap epic:** `EPIC-013`

This dossier is the temporary execution SOT for `EPIC-013`, `TASK-048`,
`TASK-049`, and `TASK-050`. The [roadmap](../roadmap/README.md#epic-013-record-and-report-production-setup-status)
owns IDs, ordering, dependencies, and lifecycle state. Specifications,
architecture, skills, and `PRIVACY.md` own shipped behavior after closeout.

## Goal

Record which Git roots `$aquarium:dev-setup` has configured, at which Aquarium
plugin version, with which Sanho choice, and whether the checkout takes part in
`aquarium-dev`. Compare that against the current released, installed, and
Unreleased plugin versions so stale directories are visible.

## Write timing

Starting the skill or ending the conversation is not a write. Plan Mode,
diagnose-only, a proposal that was never applied, inspection failure, and an
abandoned run have no terminal outcome and leave the previous row unchanged.

`$aquarium:dev-setup` may call `aquarium-status record` only after it reports a
terminal outcome for that Git root. A bundle target records after that target's
`dev-setup` returns. `$aquarium:dev-setup-global` and the `aquarium-dev`
manager do not write this file.

Use the bundle outcomes: `ready`, `partial`, `failed`, `declined`, `skipped`.

| Outcome | `last_configured_aquarium_version` | Other fields |
| --- | --- | --- |
| Unscoped setup ends `ready` (already ready, or ready after approved changes) | Set to the current plugin version | Sanho, `aquarium-dev-involved`, `last_setup_outcome: ready` |
| Scoped continuation ends `ready` | Leave unchanged | Only fields settled in that scope |
| `partial`, `failed`, or a missing global prerequisite | Leave unchanged | `last_setup_outcome` and `last_attempted_*` |
| `declined` | Leave unchanged | `last_setup_outcome: declined` |
| `skipped`, diagnose-only, Plan Mode, or no terminal outcome | Do not write | Do not write |

Sanho and `aquarium-dev-involved` change only when that component is settled.
If `aquarium-dev` was not configured before the run ended, keep the previous
value, or `false` when there is no previous value.

## CLI ownership

The plugin tool `plugins/aquarium/tools/aquarium-status/` owns the file bytes.
Skills pass closed JSON to `record` and must not Write or Edit
`~/.aquarium/status.yaml`.

- Install `~/.local/bin/aquarium-status`. It runs from a shell without Codex or
  Grok.
- Commands: `show` (independent read) and `record` (setup write).
- stdout is a versioned JSON envelope. `show` also prints the same facts as
  text. The on-disk file is canonical YAML.
- `show` reads `~/.aquarium/status.yaml` and, when present,
  `~/.aquarium-dev/enrollments/`. It does not need Codex, Grok, or a plugin
  host.
- Validate schema, replace the file atomically, keep the previous file on
  failure, and use user-only permissions.
- Reject unknown JSON, outcomes, or a non-canonical git_root without changing
  the file.
- After a plugin update, a stale PATH launcher may `show` the existing file and
  must fail closed on an unknown schema. Reinstall through an explicit
  `dev-setup-global` status-CLI update. Setup `record` uses the current plugin
  bundle, not a stale PATH copy.
- This CLI writes only under `~/.aquarium/`. `aquarium-dev` stays under
  `~/.aquarium-dev/`.

## Recorded fields

Computed at `show` time:

- released Aquarium plugin version
- Unreleased developing version, omitted when unknown
- installed plugin version used for freshness

Per Git root:

- canonical absolute `git_root`
- `project` (directory basename, or the `aquarium-dev` `project_id` for a known
  producer)
- `last_configured_aquarium_version` / `last_configured_at` only after unscoped
  `ready`
- `last_setup_outcome` / `last_attempted_aquarium_version` /
  `last_attempted_at` on each terminal outcome
- Sanho: `configured`, `not_in_scope`, or `declined` when that component is
  settled
- `aquarium-dev-involved`: `true` only when that setup settled `aquarium-dev`
  configuration

`show` live-joins `~/.aquarium-dev/enrollments/` so the report can show the
recorded flag and current enrollment together. The YAML is not a second
enrollment store. Versions here are Aquarium plugin versions, not a consumer
repository's own product version.

## Task map

| Task | Owner after closeout | Notes |
| --- | --- | --- |
| TASK-048 | specs, local interfaces, PRIVACY.md | Contract only. Do not ship the CLI in this task if the contract is still open. |
| TASK-049 | `plugins/aquarium/tools/aquarium-status/`, `dev-setup`, `$aquarium:status` | CLI and skill wiring. |
| TASK-050 | tests plus Master's skill verification | `make test` does not prove skill behavior. |

## Exclusions

- Do not auto-run `dev-setup` on stale rows.
- Do not scan the filesystem for repositories that never ran setup.
- Do not attach status to the `aquarium-dev` manager, venv, or MCP server.
- Do not mix this epic with `EPIC-012` or `EPIC-002`.
