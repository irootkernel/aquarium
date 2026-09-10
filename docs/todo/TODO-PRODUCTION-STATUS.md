# Production setup status dossier

## Authority

**Roadmap epic:** `EPIC-013`

This dossier is the temporary execution SOT for `EPIC-013`, `TASK-048`,
`TASK-049`, and `TASK-050`. The [roadmap](../roadmap/README.md#epic-013-record-and-report-production-setup-status)
owns IDs, ordering, dependencies, and lifecycle state. Specifications,
architecture, skills, and `PRIVACY.md` own shipped behavior after closeout.

## Goal

Record which Git worktree roots `$aquarium:dev-setup` has configured, the
Aquarium version used for each attempt, and the latest settled Sanho and
`aquarium-dev` results. Report those records with sourced version observations
and the current `aquarium-dev` enrollment when it can be read. A status report
describes setup history and bounded observations; it does not prove that an
integrated tool currently works.

## Status model

The ledger schema is `aquarium-production-status/v1`. It has one monotonically
increasing file revision and a repository list sorted by canonical `git_root`.
Each repository row contains:

- canonical absolute `git_root`, canonical absolute `git_common_dir`, display
  `project`, and a monotonically increasing `row_revision`
- `last_full_ready`, which is absent until an unscoped setup finishes `ready`
- `last_attempt`, which identifies the most recent recorded terminal attempt
- the latest settled Sanho and `aquarium-dev` component observations, each bound
  to the attempt that produced it

Each attempt has a unique `attempt_id`, the `expected_row_revision` read before
setup, the Aquarium version, start and completion times, terminal outcome, and
scope. Scope is either `full` or `scoped` with a closed component list.
Component observations distinguish the result of that attempt from the state it
observed. A component omitted from scope is not recorded as a current state.

## Write timing

Starting the skill or ending the conversation is not a write. Plan Mode,
diagnose-only, a proposal that was never applied, inspection failure, and an
abandoned run have no terminal outcome and leave the previous row unchanged.

`$aquarium:dev-setup` may call `aquarium-status record` only after it determines
a terminal setup outcome for that Git root and before it emits its final report.
The report includes both the setup outcome and the recording result.

When a bundle target enters `dev-setup`, that skill owns its record and returns
the recording receipt to the bundle. If a shared global result makes the bundle
settle a target without entering `dev-setup`, the bundle records that target.
Both paths use the bundle target's shared `attempt_id`; the bundle never records
a target again after receiving a valid receipt. `$aquarium:dev-setup-global`
and the `aquarium-dev` manager do not write the ledger. A target whose canonical
Git identity was not established has no recordable row.

Use the bundle outcomes: `ready`, `partial`, `failed`, `declined`, `skipped`.

| Outcome | `last_full_ready` | Other fields |
| --- | --- | --- |
| Unscoped setup ends `ready` (already ready, or ready after approved changes) | Replace with this attempt | `last_attempt` and component observations settled by this attempt |
| Scoped continuation ends `ready` | Leave unchanged | `last_attempt`, its exact scope, and component observations settled in that scope |
| `partial`, `failed`, or a missing global prerequisite | Leave unchanged | `last_attempt`, its exact scope, and any component observations settled before the terminal outcome |
| `declined` | Leave unchanged | `last_attempt` and the declined component result when known |
| `skipped`, diagnose-only, Plan Mode, or no terminal outcome | Do not write | Do not write |

Sanho and `aquarium-dev` observations change only when that component is in
scope and settled. An absent observation means unrecorded, not false. Execution
scope uses `full` or `scoped`; `not_in_scope` is not a component state.

A scoped `ready` attempt never advances `last_full_ready`. Its final report
instructs the user to run one unscoped `$aquarium:dev-setup` pass. That later
pass may advance `last_full_ready` when it verifies the full setup as `ready`.

If setup succeeds but recording fails, preserve the setup result and report
`setup_outcome: ready`, `status_recording: failed`, and the enclosing workflow
or bundle target as `partial`. Return the exact same attempt for a recording
retry; do not repeat setup mutations.

## Version observations

Every version value has `value`, `source`, and `status`. An unavailable or
ambiguous value is `unknown`; the CLI never chooses one installation from a set
of candidates.

- The recording Aquarium version comes from the current bundled recorder's
  adjacent plugin manifest. Setup does not trust a caller-supplied replacement.
- `show` identifies its reporter from the current plugin bundle when invoked by
  `$aquarium:status`, or from the installed runtime receipt when invoked through
  the PATH launcher. The latter is the launcher source version, not proof of the
  active Codex plugin version.
- Default `show` performs no network request. `show --refresh` reads the latest
  non-draft, non-prerelease stable version from the official Aquarium GitHub
  Releases endpoint. The flag authorizes only that read. Lookup failure returns
  a partial report with an unknown release observation.
- Without `--source-root`, the Unreleased observation is `not_checked`. When the
  option names the exact canonical Aquarium Git root, `show` reads its plugin
  manifest and CHANGELOG. An invalid explicit root exits `2`; a valid Aquarium
  root with no single open target reports `unknown`.

Report configuration freshness (`last_full_ready` versus the reporter) and
release freshness (reporter versus the refreshed stable release) separately.
Use `current`, `behind`, `ahead`, `unknown`, or `not_checked` as applicable. Do
not describe the PATH launcher as current merely because it can parse the
ledger.

## CLI ownership

The plugin tool `plugins/aquarium/tools/aquarium-status/` owns the file bytes.
Skills pass closed JSON to `record` and must not Write or Edit
`~/.aquarium/status.yaml`.

- Install `~/.local/bin/aquarium-status`. It runs from a shell without Codex,
  Grok, or a plugin cache.
- `show --format text|json [--refresh] [--source-root <absolute-path>]` reads the
  report. Its default format is `text`.
- `record` reads one closed JSON document from stdin and writes one JSON receipt
  to stdout.
- `forget --git-root <absolute-path>` removes exactly one row and returns a JSON
  receipt. A missing row is a successful no-change result. A skill acting for
  the user must display the exact row and obtain approval for this deletion.
- Successful stdout contains only the selected text or one versioned JSON
  envelope. Errors write one structured envelope to stderr and leave stdout
  empty.
- Exit `0` means success, including a missing ledger or a report with failed
  optional observations. Exit `1` covers unsafe, unreadable, corrupt, or
  unwritable owned state. Exit `2` covers invalid arguments, input, or explicit
  source paths. Exit `3` reports an attempt or row revision conflict.
- The on-disk file is canonical YAML.
- `show` reads `~/.aquarium/status.yaml` and, when present,
  `~/.aquarium-dev/enrollments/`. It does not need Codex, Grok, or a plugin
  host.
- A missing ledger is an empty `absent` report. Invalid ledger schema or path
  safety stops the report. Each live enrollment observation is independently
  `enrolled`, `absent`, `invalid`, `unreadable`, or `not_checked`; an enrollment
  failure does not discard a valid ledger report.
- Reject unknown JSON, outcomes, or a non-canonical `git_root` without changing
  the file.
- Setup `record` uses the current plugin bundle, not a PATH copy. A stale PATH
  launcher may read a supported schema but reports its own receipt version and
  fails closed on an unknown schema.
- This CLI writes only under `~/.aquarium/`. `aquarium-dev` stays under
  `~/.aquarium-dev/`.

## Storage and concurrency

`record` and `forget` hold an exclusive process lock at
`~/.aquarium/status.lock` across read, schema validation, revision validation,
merge, temporary-file fsync, atomic replacement, and parent-directory fsync.
`show` takes a shared lock while reading the ledger. Reject symbolic or
non-regular owned paths. Use mode `0700` for owned directories and `0600` for
the ledger, lock, receipts, and runtime metadata.

Different Git roots merge under the lock. For the same root, the caller's
`expected_row_revision` must match the stored row. A canonical replay of the
same `attempt_id` and payload returns the original receipt without writing;
another stale or conflicting result exits `3`. A validation, lock, fsync, or
replacement failure preserves the previous valid ledger.

## Installation and retention

`aquarium-status` is a default component of an unscoped
`$aquarium:dev-setup-global` diagnosis. Installation and update still require
their own approval. The installer creates a versioned Python 3.11 or newer
runtime under `~/.aquarium/status-runtime/`, installs hash-pinned PyYAML in its
private environment, and selects it through an atomic `current` link. The
regular launcher contains no plugin-cache path.

Global diagnosis compares the installed receipt and launcher with the current
bundle. An unknown existing launcher, symbolic target, or non-regular target
fails closed. An approved update may replace only a verified managed launcher
and restores the prior launcher and selector if activation fails. Plugin updates
do not update this runtime automatically.

The row identity is the canonical absolute worktree root. Linked worktrees have
separate rows even when they share a `git_common_dir`. A moved checkout records
a new row after setup; the old row remains visibly missing. A deleted checkout
also remains until the user runs `forget`. Reusing a recorded path with a
different `git_common_dir` is a conflict and requires explicit removal of the
old row. The CLI never scans for moved repositories or removes rows
automatically.

## Reported fields

`show` reports the ledger state, sourced version observations, separate
freshness comparisons, and each recorded worktree. A worktree report keeps
`last_full_ready`, `last_attempt`, and the latest settled component observations
separate. It also reports whether the Git root is present and still matches its
recorded identity.

The live `aquarium-dev` join reports its own observation state and project ID
when valid. It never changes the ledger or turns the YAML into a second
enrollment store. `project` is display metadata rather than row identity.
Versions in this feature are Aquarium plugin or reporter versions, not the
consumer repository's product version.

## Task map

| Task | Owner after closeout | Notes |
| --- | --- | --- |
| TASK-048 | specs, local interfaces, PRIVACY.md | Freeze state meaning, version sources, concurrency, output, ownership, identity, retention, and privacy. Do not ship the CLI while the contract is open. |
| TASK-049 | `plugins/aquarium/tools/aquarium-status/`, `dev-setup-global`, `dev-setup`, `dev-setup-bundle`, `$aquarium:status` | Ship the independent runtime and wire every terminal-record owner. |
| TASK-050 | tests plus Master's skill verification | Cover executable storage, reporting, installation, failure, and concurrency scenarios. `make test` does not prove skill behavior. |

TASK-050 must exercise at least:

- concurrent records for different roots, same-root revision conflicts, and
  identical attempt replay
- JSON-only parsing, text output, exit classes, absent and corrupt ledgers, and
  a storage failure that preserves setup success and the previous file
- scoped `ready` followed by unscoped promotion, and bundle targets settled
  before and after `dev-setup` entry without duplicate records
- default offline output, successful and failed `--refresh`, unavailable or
  ambiguous local versions, and an invalid Unreleased source root
- absent, corrupt, and unreadable enrollment data without converting unknown
  state to false
- linked worktrees, moved and deleted roots, path reuse with a different Git
  identity, and exact `forget`
- launcher install, managed replacement rollback, dependency isolation, unknown
  launcher rejection, and execution after the plugin cache is removed

## Exclusions

- Do not auto-run `dev-setup` on stale rows.
- Do not scan the filesystem for repositories that never ran setup.
- Do not attach status to the `aquarium-dev` manager, venv, or MCP server.
- Do not treat setup history or enrollment presence as live tool health.
- Do not mix this epic with `EPIC-012` or `EPIC-002`.
