# Production Setup Status

This specification owns the shipped `aquarium-production-status/v1` contract.
`TASK-048` froze its delivery shape and `TASK-049` added the executable and skill
wiring. Availability still depends on an installed, verified user-global
runtime.

TASK-049 security review re-froze one installation detail before publication:
the launcher is generated from the verified receipt and starts its exact
interpreter with `-B -I -S`. This supersedes TASK-048's unsafe copied-entrypoint
wording, which would have started an ambient Python before verifying the
receipt. The ledger and public JSON schemas did not change.

## Purpose and authority

Aquarium keeps one user-global ledger of terminal repository setup attempts at
`~/.aquarium/status.yaml`. It records setup history and bounded observations for
canonical Git worktree roots. It is not repository authority, a live-health
probe, an enrollment database, or proof that an integrated tool currently works.
A repository-local `.aquarium` path remains forbidden.

The bundled `aquarium-status` source owns ledger bytes. Setup skills submit one
closed JSON document to the recorder and never write YAML themselves.
`dev-setup-global` and `aquarium-dev` never record setup attempts.

## Ledger schema

The canonical YAML document has exactly these top-level fields:

```yaml
schema: aquarium-production-status/v1
file_revision: 1
repositories: []
```

`file_revision` is a positive integer. `repositories` is sorted by bytewise
canonical `git_root`. Every row has exactly:

- `git_root`: canonical absolute worktree root;
- `git_common_dir`: canonical absolute common Git directory;
- `project`: non-empty display label, never row identity;
- `row_revision`: positive integer;
- optional `last_full_ready`, absent until an unscoped attempt ends `ready`;
- `last_attempt`; and
- `components`, a mapping with optional `sanho` and `aquarium_dev` observations.

An attempt contains `attempt_id`, `input_sha256`, `expected_row_revision`,
`aquarium_version`, `started_at`, `completed_at`, `outcome`, `scope`,
`recorded_file_revision`, and `recorded_row_revision`. Attempt IDs are canonical
lowercase UUIDv4 strings. Timestamps are UTC RFC 3339 values ending in `Z`, and
completion cannot precede start. The stored input digest is lowercase SHA-256 of
the canonical record request.

`aquarium_version` and every other version observation have exactly `value`,
`source`, and `status`. `status` is `observed`, `unknown`, or `not_checked`;
`value` is stable `vMAJOR.MINOR.PATCH` only for `observed` and is otherwise null.
`source` is one of `bundled_plugin_manifest`, `installed_runtime_receipt`,
`recorded_attempt`, `official_github_release`, `source_root_manifest`,
`source_root_changelog`, `not_requested`, or `unavailable`. An observed value
cannot use `not_requested` or `unavailable`; `not_checked` uses `not_requested`.

Attempt outcomes are `ready`, `partial`, `failed`, or `declined`. `skipped`, an
abandoned run, Plan Mode, diagnosis-only work, and any non-terminal execution are
not record requests. Scope is either `{kind: full}` or `{kind: scoped,
components: [...]}`. A scoped component list is non-empty, sorted, unique, and
closed to `sanho`, `dolgorae`, `mulgae`, `gaori`, `sorage`, `podway`,
`ouroboros`, `lora`, `deslop`, `humanizer`, `im-not-ai`, `aquarium-dev`, and
`agents-guidance`.

A component observation contains the producing `attempt_id`, `outcome`, and a
sourced `version`. Its outcome is `ready`, `partial`, `failed`, `declined`, or
`unknown`. Only a settled in-scope observation replaces that component. Omission
preserves the previous observation and never means false, absent, or
`not_in_scope`.

## Record contract

`record` reads exactly one `aquarium-production-status-record/v1` JSON document
from standard input. Its exact shape is:

```json
{
  "schema": "aquarium-production-status-record/v1",
  "attempt_id": "00000000-0000-4000-8000-000000000000",
  "expected_row_revision": 0,
  "git_root": "/absolute/worktree",
  "project": "display label",
  "started_at": "2026-09-18T00:00:00Z",
  "completed_at": "2026-09-18T00:01:00Z",
  "outcome": "ready",
  "scope": {"kind": "full"},
  "components": {}
}
```

The top-level keys above are all required. A scoped `scope` has exactly `kind`
and `components`; a full scope has only `kind`. `components` has zero or more
`sanho` and `aquarium_dev` keys. Each value has exactly `outcome` and `version`,
and `version` has exactly `value`, `source`, and `status` under the version rules
above. Component keys must belong to the declared scoped list when scope is
scoped. A full attempt may settle either component.

The input accepts only:

- `schema`, `attempt_id`, `expected_row_revision`, `git_root`, `project`,
  `started_at`, `completed_at`, `outcome`, `scope`, and `components`;
- `expected_row_revision: 0` for a new row and the current positive revision for
  an existing row; and
- optional component observations only for `sanho` and `aquarium_dev`.

Unknown fields, trailing JSON, a non-canonical root, invalid Git identity,
caller-supplied Aquarium version, invalid enum, malformed time, or inconsistent
scope is invalid input. The recorder resolves the canonical Git root and common
directory itself with repository-scoping Git environment variables removed. Its
Aquarium version comes from the executing bundle's adjacent plugin manifest.

Before hashing, the recorder validates the input, replaces `git_root` with the
resolved canonical absolute root, normalizes every string to Unicode NFC, sorts
the scoped component list, and serializes the closed object as UTF-8 JSON with
lexicographically sorted keys, no insignificant whitespace, unescaped Unicode,
finite values only, and a trailing newline. Integers are decimal integers and
booleans are never accepted as integers. `input_sha256` is the lowercase digest
of those bytes. `expected_row_revision` remains part of the digest.

The first changed write creates file and row revision 1. Adding a new root to an
existing ledger increments `file_revision` once and creates that row at revision
1. Updating an existing row increments both revisions exactly once. Different
roots merge under the lock. A new common directory at an already recorded path
is a conflict until that row is explicitly forgotten.

Replay comparison precedes the ordinary expected-revision check. An exact replay
is idempotent only while the same `attempt_id` remains the row's `last_attempt`
and its canonical request digest matches, including its original now-stale
`expected_row_revision`. It returns a replay receipt with the original recorded
revisions, `status: replayed`, and `changed: false` without writing or changing
mtime. The first receipt has `status: recorded` and `changed: true`; the two
receipts are semantically linked but are not byte-identical.

An attempt ID present in any retained `last_attempt`, `last_full_ready`, or
component observation may identify only that same root and canonical request.
Another use is a conflict. The ledger intentionally keeps no complete attempt
history, so an ID that has aged out of every retained slot is no longer
detectable; callers remain responsible for UUIDv4 uniqueness. A changed payload,
ordinary stale revision, or replay after a newer attempt is a conflict.

Every accepted attempt replaces `last_attempt` and its settled component
observations. Only unscoped `ready` also replaces `last_full_ready`; unscoped
`partial`, `failed`, and `declined`, plus every scoped outcome, preserve the
previous `last_full_ready`. A scoped success report recommends one later
unscoped pass. If setup succeeds but record fails, setup remains successful,
`status_recording` is `failed`, the enclosing workflow result is `partial`, and
retry returns the identical attempt without repeating setup mutations.

## Show and forget contracts

`show --format text|json [--refresh] [--source-root <absolute-path>]` reads the
ledger without changing it. JSON output uses
`aquarium-production-status-report/v1` and reports ledger state, reporter and
source versions, independent configuration and release freshness, recorded
rows, live root identity, and current `aquarium-dev` enrollment observations.

A missing ledger is an `absent` report. Invalid schema or unsafe owned paths stop
the report. Live root state is `present`, `missing`, `identity_mismatch`, or
`unreadable`. Enrollment state is independently `enrolled`, `absent`, `invalid`,
`unreadable`, or `not_checked`; a bad enrollment never discards a valid row.

Default show makes no network request. `--refresh` alone authorizes a read of
`https://api.github.com/repos/irootkernel/aquarium/releases/latest`. Lookup failure
keeps exit 0, returns an unknown release observation, and marks the report
partial. `--source-root` must resolve to the exact root of an Aquarium checkout
whose manifest names `aquarium`; it reads that manifest and CHANGELOG only. No
source root yields `not_checked`; an invalid explicit root exits 2; a valid root
without exactly one stable Unreleased target yields `unknown`.

The physical source root must be a directory. Each component from it to the
manifest and CHANGELOG must remain contained, owned only as an external read,
and contain no symbolic link; each final target must be a regular file no larger
than 1 MiB. Enrollment joins inspect only the six allowlisted project-ID files
below `~/.aquarium-dev/enrollments/` and select a valid file whose checkout is
the exact stored Git root; an unrelated malformed file cannot poison another
row. Every path component must be a non-symbolic directory, and each final JSON
must be a non-symbolic regular file no larger than 1 MiB. Violations attributable
to the selected row yield the corresponding invalid or unreadable state without
following the target.

The report's top-level `status` is `complete` or `partial`. A failed optional
refresh, unreadable or invalid enrollment, or unavailable requested source
observation makes it `partial` and adds a closed warning code without changing
exit 0. An absent enrollment, missing recorded root, unknown optional version,
or omitted optional observation does not by itself make the report partial.

Configuration freshness compares `last_full_ready` with the reporter. Release
freshness compares the reporter with the refreshed stable release. Each result
is independently `current`, `behind`, `ahead`, `unknown`, or `not_checked`.
Comparison accepts only numeric stable `vMAJOR.MINOR.PATCH` values and compares
their integer triples; prerelease or build metadata is never admitted. The
reporter uses the installed runtime receipt. `source_plugin` uses the selected
source root's manifest, and `source_unreleased` uses its one stable Unreleased
CHANGELOG target.

`forget --git-root <absolute-path> [--if-file-revision <positive-integer>
--if-row-revision <positive-integer> --if-row-sha256 <lowercase-sha256>]`
removes exactly one row and returns
`aquarium-production-status-forget-receipt/v1`. A missing row is an exit-0
no-change result with unchanged bytes and revisions. The status skill always
shows the exact row plus its file revision and row digest, obtains deletion
approval, re-reads it, and supplies all three preconditions. The row digest is
lowercase SHA-256 over the row serialized by the record canonical-JSON algorithm.
All three options are required together to remove an existing row; a changed
file revision, row revision, digest, root, or common-directory identity is a
conflict. The CLI never scans for moved or deleted repositories and never
removes rows automatically.

Forget resolves an existing path physically but accepts an absent path only when
it is absolute, Unicode-normalized, contains no `.` or `..` segments after
normalization, and exactly matches a stored `git_root`. It never resolves an
absent path through its parent. Removing an existing row increments
`file_revision` once, reports the removed `previous_row_revision`, and retains an
empty ledger when the last row is removed. It does not assign a new row revision.
A missing row returns the current file revision, or null when no ledger exists.

Successful stdout contains only the selected text or one versioned JSON
envelope. Errors leave stdout empty and write one
`aquarium-production-status-error/v1` envelope to stderr. Exit 0 is success,
including absent state and failed optional observations; exit 1 is unsafe,
unreadable, corrupt, or unwritable owned state; exit 2 is invalid arguments,
input, or explicit source root; exit 3 is an attempt or row revision conflict.

Text output uses fixed English labels. Every project name and path is rendered
as an ASCII-only JSON string, escaping all non-ASCII code points as well as
control characters, newlines, backslashes, terminal escapes, and Unicode
bidirectional or format controls; it never writes an untrusted string as raw
terminal text.

## JSON envelopes

`aquarium-production-status-record-receipt/v1` has exactly `schema`, `status`,
`changed`, `attempt_id`, `git_root`, `file_revision`, and `row_revision`.
`status` is `recorded` or `replayed`; the other fields have the meanings and
types declared above.

`aquarium-production-status-forget-receipt/v1` has exactly `schema`, `status`,
`changed`, `git_root`, `file_revision`, and `previous_row_revision`. `status` is
`forgotten` or `absent`; the two revision fields are positive integers or null
only for an absent ledger or absent row as described above.

`aquarium-production-status-report/v1` has exactly:

- `schema` and `status`;
- `ledger`, with exactly `state` (`absent` or `present`) and `file_revision`;
- `reporter`, `latest_stable`, `source_plugin`, and `source_unreleased`, each a
  version observation;
- `release_freshness`;
- `repositories`, sorted by `git_root`; and
- `warnings`, a sorted unique list of objects containing only `code`.

Each report row contains the stored row fields plus `root_state`,
`configuration_freshness`, and `enrollment`. `root_state` is `present`,
`missing`, `identity_mismatch`, or `unreadable`. `enrollment` has exactly
`state` and `project_id`; the ID is a non-empty string only for `enrolled` and is
otherwise null. Warning codes are `release_refresh_failed`,
`source_observation_unavailable`, `enrollment_invalid`, and
`enrollment_unreadable`.

`aquarium-production-status-error/v1` has exactly `schema` and `error`; `error`
has only `code` and `message`. Exit-1 codes are `state_unsafe`,
`state_unreadable`, `state_corrupt`, `state_write_failed`, `lock_failed`,
`durability_failed`, and `runtime_unavailable`. Exit-2 codes are
`invalid_arguments`, `invalid_input`, `invalid_git_root`,
`invalid_source_root`, and `unsupported_schema`. Exit-3 codes are
`revision_conflict`, `attempt_conflict`, and `git_identity_conflict`.

## Storage, locking, and durability

`show` takes a shared lock whenever the owned state root and lock already exist.
When both the ledger and lock are absent, its read-only fast path returns the
absent snapshot without creating either path; a concurrent first record may
linearize immediately before or after that snapshot. A ledger without its lock
is unsafe. `record` and `forget` hold an exclusive
`~/.aquarium/status.lock` across safe-path validation, read, schema validation,
revision checks, merge, temporary-file write and fsync, atomic replacement, and
parent-directory fsync. Owned directories use mode `0700`; the ledger, lock,
runtime receipt, and metadata files use `0600`. Symbolic and non-regular owned
paths fail closed.

Validation, locking, write, fsync, replacement, or activation failure preserves
the previous valid ledger bytes. If failure happens after replacement but before
the parent fsync succeeds, the writer restores and fsyncs the previous bytes
before reporting failure. The canonical YAML emitter rejects aliases, duplicate
keys, unknown fields, non-UTF-8 input, and noncanonical scalar types.

## Runtime installation

An unscoped `dev-setup-global` diagnosis includes `aquarium-status`, but its
installation or update remains a distinct approved action. The installer uses
Python 3.11 or newer and exactly PyYAML 6.0.3 in a private environment under
`~/.aquarium/status-runtime/versions/`. The TASK-049 `requirements.txt` is the
exact package-and-hash authority. Installation invokes pip with
`--require-hashes --only-binary=:all:` and may contact only
`https://pypi.org/simple` and `https://files.pythonhosted.org`. A source lookup,
download, wheel, hash, or environment failure leaves the current runtime and
launcher untouched.

The installer invokes the selected Python in isolated mode and pip with
`--isolated`, the explicit single `--index-url https://pypi.org/simple`,
`--no-cache-dir`, `--disable-pip-version-check`, `--no-deps`,
`--require-hashes`, and `--only-binary=:all:`. It removes ambient `PIP_*` and
Python path variables and sets `PIP_CONFIG_FILE` to the null device. It neither
uses an extra index nor reads or writes a user/global pip cache or configuration.

Each admitted generation is named `<source_sha256>-py<major.minor>`; a
`-r<uuidhex>` suffix is allowed only when that exact name already exists with
different verified content. The atomic `current` selector contains exactly
`versions/<generation>`. Every generation has a private
`aquarium-status-runtime/v1` receipt containing exactly `schema`,
`plugin_version`, `source_sha256`, `python_version`, `python_executable`,
`python_executable_sha256`, `requirements_sha256`, `files`, and
`dependency_files`. Both file mappings are path-sorted relative names to
lowercase SHA-256. `files` covers the exact payload below;
`dependency_files` covers every admitted non-directory wheel member installed
under the generation. The selector, receipt, payload, interpreter, and private
dependency tree jointly define the installed identity.

The runtime payload is exactly `aquarium_status.py`, `status_contract.py`,
`status_store.py`, `status_report.py`, `runtime_entry.py`, and
`requirements.txt`. Each file digest is over its raw committed bytes.
`requirements_sha256` is the digest of the raw `requirements.txt` bytes.
`source_sha256` is the digest of the UTF-8 concatenation, in bytewise relative
path order, of one `<file-sha256>  <relative-path>\n` line per payload file. The
installer records the selected canonical regular interpreter path, its raw-byte
digest, and its queried major.minor.micro version before activation. It derives
`dependency_files` from the hash-admitted wheel and verifies every extracted
regular file without following links; missing, extra, symbolic, special, or
digest-mismatched dependency content is invalid.

Diagnosis first verifies containment, path types, the interpreter raw-byte
digest, every payload digest, and every dependency digest using only the
currently executing trusted inspector. It does not execute the generation
interpreter, import `yaml`, load package metadata, or process `.pth` files before
those checks pass. Only then may it execute that exact interpreter with `-I -S`
and an explicit verified dependency path to confirm the recorded Python version
and PyYAML 6.0.3. The runtime uses the same order and refuses extra distributions
or dependency files.

The launcher is a generated regular POSIX executable at
`~/.local/bin/aquarium-status` with no plugin-cache path. Its deterministic
bytes carry the Aquarium managed-launcher marker and invoke the receipt's
absolute interpreter with `-B -I -S` and the selected generation's verified
`runtime_entry.py`. A managed candidate must point directly below the owned
versions root. In normal state its exact bytes are derived from that
generation's closed receipt and bind the receipt's still-matching interpreter.
If the selected generation or receipt is missing or structurally corrupt, the
exact generated marker and argv are a repair candidate only when the safe
`current` selector names that same contained generation; marker shape alone is
never ownership evidence. A launcher is fully managed only when its generation
is selected and its receipt, payload, dependencies, and interpreter verify.
This distinction permits repair of interrupted or missing selected state without
treating an arbitrary marker-shaped file as owned. Any other regular launcher
is unknown and fails closed.

Diagnosis compares the bundled payload, installed receipt, selector, private
environment, and launcher independently. An unknown regular launcher, symbolic
target, non-regular target, invalid selector, or mismatched receipt fails closed.
An approved managed update prepares and verifies a generation before activation
and restores both launcher and selector if activation fails. Old admitted
generations remain available. Plugin updates never update this runtime
automatically.

The PATH launcher identifies its reporter from the installed runtime receipt.
Setup runs the current bundled source through the verified private runtime so
recording uses the current adjacent plugin manifest rather than a stale PATH
copy. A supported older launcher may show a known ledger schema but rejects an
unknown schema.

Runtime diagnosis returns `aquarium-status-runtime-inspection/v1` with exactly
`schema`, `status`, `bundled`, `installed`, `launcher`, `runtime_root`, and
`action`. `status` is `current`, `outdated`, `missing`, `broken`, or `unsafe`.
`bundled` has exactly `plugin_version` and `source_sha256`; `installed` is null
or those fields plus `python_version`; `launcher` has exactly `path` and `state`,
where state is `missing`, `managed_current`, `managed_outdated`, `unknown`, or
`unsafe`; and `action` is null or `install`, `update`, or `repair`. Runtime
failures return `aquarium-status-runtime-error/v1` with only `schema` and an
`error` containing only `code`, `message`, and `action`; code is
`runtime_install_failed` or `runtime_unavailable`.

Diagnosis applies this precedence: an unsafe owned path yields `unsafe` with a
null action; otherwise an unknown regular launcher yields `unsafe` with a null
action and can never be replaced; otherwise no selected generation and no
managed candidate yields `missing` and `install`; a managed candidate without a
selected generation, or an invalid selector, selected receipt, payload,
environment, or managed-launcher relationship, yields `broken` and `repair`;
otherwise a verified installed source different from the bundled source yields
`outdated` and `update`; only a fully matching source yields `current` with a
null action. Launcher state is `unsafe` before all other launcher states, then
`unknown`, `missing`, `managed_outdated`, and `managed_current`.

The global inspector advances to
`aquarium-dev-setup-global-inspection.v4`. Its only incompatible addition is a
default-selected and explicitly selectable `tools.aquarium-status` member whose
value is the runtime inspection envelope above. The global skill consumes that
structured member and never infers runtime state from prose.

## Setup ownership and retry protocol

The setup workflows exchange an `aquarium-production-status-attempt/v1`
document with exactly `schema`, `attempt_id`, `expected_row_revision`,
`git_root`, `project`, `started_at`, and `scope`. `dev-setup` creates it after
canonical repository identity and scope are frozen and immediately before its
first persistent setup mutation. A terminal no-op execution creates it before
settlement and is recorded like any other terminal setup. Diagnosis, planning,
and work stopped before execution approval do not create an attempt.

For a bundle run, this direct-run creation rule is replaced by bundle ownership:
`dev-setup-bundle` creates one attempt per ready target after manifest
revalidation and identity freeze, then passes it unchanged to
`dev-setup`. Once `dev-setup` is entered, it exclusively owns completion and
recording. It returns `aquarium-production-status-recording-result/v1` with
exactly `schema`, `status`, `attempt_id`, `receipt`, `retry_request`, and
`problem_code`. `status` is `recorded`, `replayed`, `failed`, or
`not_recordable`; `receipt` is non-null only for the first two statuses;
`retry_request` is non-null only for `failed`; and `problem_code` is null on
success and otherwise one of `identity_unavailable`, `runtime_unavailable`,
`record_rejected`, or `record_conflict`. `attempt_id` is a UUIDv4 for every
status except `not_recordable` with `identity_unavailable`, where it is null.

A failed result's `retry_request` is the exact original closed record document.
The caller may only submit that document to `record` again; it must not repeat
setup mutation. The bundle accepts a returned receipt only when its attempt ID,
canonical root, and revisions match its attempt, and then performs no second
recording. For `recorded`, `row_revision` must equal
`expected_row_revision + 1`; for `replayed`, the receipt revisions must equal
the stored attempt's original recorded revisions after the recorder has matched
the original request digest. In either case, `file_revision` must be at least
`row_revision`. If a bundle target settles before entering `dev-setup`, the
bundle completes and records its own original attempt exactly once. A workflow
that cannot establish canonical Git identity
returns `not_recordable` and never creates a row. `dev-setup-global` and
`aquarium-dev` never create attempts or write the ledger.

## Retention and privacy

Rows retain canonical absolute worktree and common-directory paths, display
labels, attempt IDs and times, outcomes and scopes, sourced versions, and latest
settled component results. Linked worktrees have separate rows. Moving or
deleting a checkout retains the old row visibly; recording the new location adds
a new row. Exact `forget` is the only row-removal operation.

All state is local and user-private. Default reporting uploads nothing. Refresh
sends only the ordinary request needed to read official release metadata. The
source-root and enrollment joins are local reads. The ledger never stores
credentials, repository source, provider output, tool logs, or raw setup
diagnostics.

## Non-goals

- Do not auto-run setup for stale rows or scan for unknown repositories.
- Do not infer live tool health from setup history or enrollment presence.
- Do not attach the ledger to the `aquarium-dev` manager, virtual environment,
  or MCP server.
- Do not change the bundle manifest v1 tool vocabulary.
- Do not mix this contract with EPIC-002 or EPIC-012.
