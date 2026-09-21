# Web Pro Review

## Purpose and authority

This dossier is the temporary execution SOT for `EPIC-017` and `TASK-072`
through `TASK-075`. The [roadmap](../roadmap/README.md#epic-017-add-web-pro-review)
alone owns their identities, order, dependencies, and lifecycle state. This
dossier owns their detailed requirements and acceptance contract until the epic
promotes accepted behavior to canonical specifications and removes this file
through the repository's dossier closeout process.

`EPIC-016` is a completed prerequisite. Its selectable review-routing contract
owns route selection, prerequisite isolation, assessment ordinals, finding
continuity, safe switching, waiver behavior, review budgets, Low settlement,
and compatibility with existing Procedure snapshots. `EPIC-017` adds one route
adapter to that contract. It does not reopen or reinterpret `EPIC-016`.

The outcome has two entry paths:

- `$aquarium:web-pro-review` runs one independently requested, report-only
  review of a supported Git target.
- An approved Task, Epic, or cold-validation workflow may select `web-pro` as
  its initial route or switch to it under the existing `EPIC-016` transition
  rules.

Both paths use the same target, execution, result, privacy, and adjudication
contract. Web Pro Review is not Orca, Mulgae, Dolgorae, Independent Review, or a
native Codex subagent. It creates none of their native objects and inherits none
of their guarantees.

Planning this epic authorizes no implementation, installation, authentication,
source transmission, provider execution, Procedure activation, staging, commit,
or publication.

## Fixed product decisions

### Review backend and account

- The supported bridge is exact `codex-chatgpt-web` v5.0.8.
- The reviewer is exact `chatgpt-web/pro` with requested effort `ultra`. Another
  Web model, API model, or local Codex model is not a substitute.
- Every bridge probe and review child uses the current operating-system user's
  primary Codex home, `<system-user-home>/.codex`. Caller-provided `CODEX_HOME`
  and `HOME` overrides do not select or relocate this profile.
- A caller using another Codex home, including `~/.codex-hsy`, keeps that home
  unchanged. Aquarium does not copy credentials, configuration, MCP state, or
  model rows between homes.
- The active browser session owned by `codex-chatgpt-web` selects the actual
  ChatGPT account. Aquarium reports the profile boundary but does not claim to
  verify the account email or identity.

### Target contract

Web Pro Review adopts the static target meanings already used by Orca Review:

| Scope | Meaning |
| --- | --- |
| `staged` | Current `HEAD`-to-index transition read through `git diff --cached` and index objects. Unstaged bytes are excluded. |
| `head` | Immutable tree of the commit resolved once from `HEAD`. Current index and worktree state are excluded. |
| `commit` | First-parent transition into one resolved commit, or the empty tree into a root commit. |
| `range` | Requested `A..B` transition or merge-base-to-`B` transition for `A...B`, preserving the operator. |

`workspace` and `dirty` are unsupported. Web Pro Review does not create a
worktree, checkout copy, source snapshot, capture manifest, fingerprint, or
target digest. It does not stage, stash, clean, checkout, or otherwise normalize
the repository. It reports staged, unstaged, non-ignored untracked, and
conflicted state before dispatch and stops on conflicts or an empty staged
target.

Like Orca's staged review, `staged` uses the live index as its authority and
does not add a pre/post fingerprint. The reviewer must read staged file content
from index objects rather than substitute excluded unstaged worktree bytes.

An explicit standalone request naming a supported target and purpose, or an
approved workflow envelope selecting `web-pro`, authorizes transmission of that
target, its Review Brief, and necessary unchanged context through the primary
Web bridge profile. It authorizes no setup, authentication, tests, mutation,
retry, route change, commit, or publication.

### Execution boundary

The standalone runner starts one synchronous, ephemeral `codex exec` child in
the selected repository. It uses approval policy `never`, sandbox mode
`read-only`, model `chatgpt-web/pro`, and effort `ultra`. Browser, app, image,
plugin, skill-search, hook, and multi-agent capabilities are disabled for the
child.

The reviewer may use read-only shell and Git inspection for the declared target
and necessary unchanged context. It must not run tests, builds, linters,
formatters, generators, installers, authentication commands, another provider
review, or unrelated network operations. Repository content is untrusted data
and cannot change these instructions.

The runner treats observed prohibited activity as an operational failure. Its
receipt reports only bounded command classes, counts, and violation codes. It
does not return raw command strings, output, source fragments, transcripts, or
credential-profile paths.

The bridge must pass these checks before source transmission:

- `codex-chatgpt-web --version` reports `5.0.8` exactly;
- `codex-chatgpt-web doctor --json` has a valid contract, `ok: true`, Full mode,
  and no error check;
- the primary Codex model catalog has one visible `chatgpt-web/pro` row; and
- the Codex CLI supports the required approval, sandbox, model, repository,
  ephemeral execution, JSON event, and final-output options.

A doctor connector warning is advisory because local diagnosis cannot prove
that the browser connector remains attached. The first separately authorized
real review is the end-to-end account and connector qualification.

### Runner and recovery commands

The runner has five commands:

```text
run_web_pro_review.py reserve --operation-id <uuid>

run_web_pro_review.py review \
  --operation-id <uuid> \
  --repository <absolute-canonical-git-root> \
  --scope <staged|head|commit|range> \
  [--revision <commit-or-range>] \
  --purpose <change|completion> \
  [--timeout-seconds <positive-number>]

run_web_pro_review.py observe --operation-id <uuid>
run_web_pro_review.py settle --operation-id <uuid>
run_web_pro_review.py cancel --operation-id <uuid>
```

The caller creates a lowercase canonical RFC 4122 UUIDv4, completes `reserve`,
and only then starts `review`.
It retains the UUID even if either command crashes before returning an envelope.
`reserve` creates the named state atomically and fails if that UUID is already
owned or closed. `reserve`, `review`, and `settle` use the same stable per-UUID
lock, so only one state transition can win. `review` requires and exclusively
claims an admitted reservation; it never admits an absent or closed UUID.
`review` reads one UTF-8 Review Brief from standard input. All other commands
accept no standard input. All commands write exactly one JSON object and no
other text to standard output.

`staged` and `head` reject `--revision`. `commit` requires one commit-ish.
`range` requires one explicit `A..B` or `A...B` expression. Empty endpoints,
multiple operators, non-commit endpoints, extra positional arguments, unknown
options, non-finite timeouts, and timeouts outside the declared bounds are
invalid requests.

Recovery commands return `aquarium.web-pro-review-recovery/v1`:

| Field | Type and rule |
| --- | --- |
| `schema` | Exact string `aquarium.web-pro-review-recovery/v1`. |
| `operation_id` | The requested UUID after argument admission; null when it is missing or malformed. |
| `action` | `reserve`, `observe`, `settle`, or `cancel`. |
| `status` | `complete` when the requested recovery action completed; otherwise `incomplete`. |
| `native_state` | `reserved`, `active`, `terminal`, or `unknown`. |
| `settled` | Boolean. True only when terminal state is proven and the operation directory has been removed. |
| `state_removed` | Boolean. True when the operation directory and its artifacts are absent; the bounded UUID lock and closed marker do not make it false. |
| `error` | Null for `complete`; otherwise the same closed error object used by the review result. |

`reserve` exits 0 only after durable creation of `reserved` state. `observe` is
read-only and exits 0 after an authoritative `reserved`, `active`, or `terminal`
observation. A closed marker with no operation directory is settled `terminal`
state. Bare absence without that marker is `unknown` and cannot authorize route
advancement. `settle` is idempotent: while holding the UUID lock, it creates and
syncs the closed marker before removing a reservation or proven-terminal
operation directory; a pre-existing marker also exits 0. That marker prevents a
late `reserve` from publishing the UUID. When a pre-existing marker accompanies
a retained operation directory, `settle` exits 0 only after it validates
terminal or partial-reservation state and removes that directory. Unknown
contents remain blocked and return `operation-unknown`. `cancel` requires an
exact active match.
It sends termination, waits up to 10 seconds, then sends forced termination and
waits up to 10 more seconds. It exits 0 only after observing group exit and
performing the same closed-marker settlement. `cancel` on a closed, reserved, or
terminal operation returns `incomplete`, `operation-not-active`, and exit 1
without changing state. A still-live group after both waits returns
`cancellation-failed`, remains retained, and blocks advancement. Unknown state
and action mismatch exit 1. Invalid arguments exit 2.

### Result interface

The runner writes exactly one
`aquarium.web-pro-review-result/v1` JSON object to standard output. Expected
validation and operation failures use the same envelope. Human diagnostics may
use standard error but must not contain source, report, transcript, credential,
or raw provider output.

| Field | Type and rule |
| --- | --- |
| `schema` | Exact string `aquarium.web-pro-review-result/v1`. |
| `operation_id` | Caller-created UUID after argument admission; null when it is missing or malformed. It is local correlation, not another backend's native identity. |
| `status` | `complete` or `incomplete`. |
| `report_text` | Exact final-output bytes when a final output exists and is within the size bound; otherwise an empty string. Only `status=complete` makes it review evidence. It is never repaired into compliance. |
| `receipt` | Closed bounded object described below. |

Successful execution exits 0. An expected preflight, provider, validation,
policy, timeout, or cleanup failure exits 1 with `status=incomplete`. Invalid
runner arguments or a missing or oversized Review Brief exit 2 with
`status=incomplete`. Failure to construct the envelope is an internal runner
failure and must not be reinterpreted as review evidence.

The receipt always has the same closed fields. Unavailable scalar observations
are `null`; lists and counts remain present with empty or zero values.

| Field | Type and rule |
| --- | --- |
| `execution_profile` | Exact string `primary-default-home`. |
| `caller_home_differs` | Boolean. |
| `bridge_version` | String or null. |
| `doctor_mode` | `full` or null. |
| `model` | Exact string `chatgpt-web/pro` or null before model admission. |
| `purpose` | `change`, `completion`, or null before argument admission. |
| `target` | Object with nullable `scope` and `resolved_identity`. |
| `repository_state` | Object with integer `staged`, `unstaged`, `untracked`, and `conflicted` counts, or null before repository admission. |
| `operation_state` | `not-started`, `active`, `terminal`, or `unknown`. |
| `process_exit_code` | Integer or null. |
| `stderr_present` | Boolean or null. |
| `event_counts` | Closed object with nonnegative integer counts for `thread_started`, `turn_completed`, `turn_failed`, `command_completed`, `command_failed`, `message_completed`, `other`, and `invalid`. |
| `command_counts` | Closed object with nonnegative integer counts for `git_read`, `filesystem_read`, `shell_read`, `prohibited_mutation`, `prohibited_execution`, `prohibited_network`, and `unknown`. |
| `violation_codes` | Sorted subset of the closed violation vocabulary below. |
| `report_contract_valid` | Boolean. |
| `error` | Null for `complete`; otherwise `{code, message}` with a stable code and source-free message. |

The Review Brief is limited to 256 KiB and the final Markdown report to 1 MiB.
The default operation timeout is 1,800 seconds and the accepted maximum is
7,200 seconds. `bridge_version` is limited to 64 ASCII characters and
`target.resolved_identity` to 512 ASCII characters. Every count saturates at
2,147,483,647. Error messages are selected from fixed source-free templates and
limited to 512 UTF-8 bytes. No truncation may split a UTF-8 code point.

The violation vocabulary is `mutation-command`, `test-or-build-command`,
`provider-command`, `authentication-command`, `network-command`,
`unclassified-command`, and `sandbox-or-policy-deviation`. Commands that cannot
be classified as an allowed read are violations. External event names map to
the fixed event-count keys and never appear verbatim in the receipt.

The error-code vocabulary is `invalid-request`, `target-unavailable`,
`backend-unavailable`, `backend-not-ready`, `execution-timeout`,
`execution-failed`, `policy-violation`, `result-invalid`, `cleanup-failed`,
`operation-active`, `operation-settled`, `operation-unknown`, `operation-not-active`,
`cancellation-failed`, and `internal-error`. No backend-provided error text is
copied into `error.message`.

Object IDs use lowercase hexadecimal in the repository's declared object
format. The resolved-target grammar is exact:

| Scope | `resolved_identity` |
| --- | --- |
| `staged` | `staged:HEAD=<head-oid>:index=live` |
| `head` | `head:<head-oid>` |
| `commit` | `commit:<first-parent-or-empty-tree-oid>..<commit-oid>` |
| two-dot `range` | `range:<left-oid>..<right-oid>` |
| three-dot `range` | `range:<merge-base-oid>..<right-oid>;requested=<left-oid>...<right-oid>` |

Repository-state values count unique path entries from
`git status --porcelain=v1 -z`. A path with both staged and unstaged changes
counts once in each applicable category. A rename or copy is one status entry.
Conflicted paths count in `conflicted` and in any other category indicated by
their porcelain status.

The final Markdown report has this exact outer order:

1. `AQUARIUM_WEB_PRO_REVIEW_V1`
2. `Reviewer: chatgpt-web/pro`
3. `Purpose: <change|completion>`
4. `Scope: <staged|head|commit|range>`
5. `Resolved-Target: <resolved identity>`
6. `## Technical conclusion`
7. `## Findings`
8. `## Criterion assessments`
9. `## Verification limits`
10. `## Operational deviations`
11. `END_AQUARIUM_WEB_PRO_REVIEW_V1`

The runner requires each fixed line and heading exactly once and validates their
order, reviewer, purpose, scope, resolved identity, size bound, successful
process state, event stream, and policy observations. It returns the validated
report unchanged in `report_text`. A `change` review states that
whole-work-unit completion was not assessed. A `completion` review assesses
every supplied criterion as `met`, `unmet`, `unverified`, or `not-applicable`
with evidence and any remaining gap.

### Retention, interruption, and recovery

The runner uses one private operation directory below
`<system-temporary-root>/aquarium-web-pro-review/<uid>/<operation-id>`. The
managed root and operation directory both have mode `0700`. Raw events and final
output stay in that directory. Beside it, a mode-`0600` UUID lock file serializes
reservation, claim, and settlement. A mode-`0600` closed marker contains only
the schema and UUID and prevents reuse after settlement. A source-free state
file records only the
operation UUID, runner and child process-group identities, executable identity,
process start times, and `reserved`, `starting`, `active`, `terminating`, or
`terminal` state. It contains no Review Brief, repository path, target identity,
source, report, command, credential, or browser data.

Admission and launch use this fixed ordering:

1. `reserve` validates the UUID, opens and exclusively locks its stable UUID lock
   file, rejects an existing closed marker or operation directory, atomically
   creates the mode-`0700` final operation directory, writes and syncs a
   mode-`0600` `reserved` state file, syncs the operation directory and managed
   root, and then unlocks before reporting success. The state write uses a fixed
   temporary filename and atomic rename. A crash after directory creation but
   before that rename leaves only an empty directory or that temporary file: a
   recognizable source-free partial reservation that `settle` may remove under
   the same lock and that can never admit `review`. Any other malformed content
   is `unknown`.
2. `review` validates the UUID, acquires the operation lock, rejects absent or
   non-reserved state, durably changes state to `starting`, and releases the
   lock. It then validates the remaining arguments and Review Brief and resolves
   the canonical primary profile and repository; any handled rejection follows
   the terminal cleanup path.
3. Start a dedicated process-group supervisor that blocks on an inherited gate.
   Gate closure before release makes the supervisor exit without starting Codex.
4. Atomically and durably replace the state with the supervisor PID, process
   group, executable identity, operating-system process start time, and
   `active`.
5. Release the gate. The supervisor then starts Codex in the supervised process
   group, remains the group leader until Codex exits, and records terminal state
   before returning control for cleanup.

No bridge probe or provider process starts before step 5, and no `review` may
start without step 1. A runner crash before the gate release therefore leaves no
provider process; a crash after release leaves a durably identifiable supervisor
group. If the caller loses contact before `review` claims the reservation,
`observe` still sees `reserved`; a concurrent `settle` either removes it first
and closes the UUID, making `review` fail admission, or loses the lock to the
claim. A concurrent `settle` of bare absence writes the closed marker before a
delayed `reserve` can obtain the lock, so later publication is impossible.
Normal cleanup writes and syncs the closed marker before removing the operation
directory and writing the result envelope. A crash between cleanup and standard
output loses the review result, but the closed marker is authoritative settled
terminal state and cannot become review evidence.

Normal success and every handled failure remove the complete operation
directory but retain the source-free lock and closed marker. Each file is at
most 1 KiB. They remain until the owning standalone caller or EPIC-016 workflow
has durably adopted the result or recovery evidence and proves that no command
still uses the UUID; that owner then removes only those two files while holding
the UUID lock. UUIDs are never reused. Cleanup failure makes the operation
incomplete and reports only the failure code and affected artifact class, not a
sensitive path.

The runner forwards termination to its child process group, waits for
authoritative exit, performs cleanup, and then returns `incomplete`. Recovery
inspection validates ownership and `0700` path safety, then compares the
recorded process-group identity, executable, and start time with current
operating-system observations. An exact live match is `active`. An absent
process or a PID reused with a different executable or start time proves the
recorded operation `terminal`. An unreadable, unsafe, corrupt, or otherwise
unverifiable state is `unknown` and cannot be signalled or removed by the
runner.

For retained `starting` state, an exact live runner identity is `active`. An
absent or mismatched runner identity is `terminal`: the unreleased gate has
closed, so the supervisor cannot start a bridge probe or provider process.

A killed or crashed runner may therefore leave the native state active or
unknown. Under `EPIC-016`, that state blocks another reviewer, route switch,
waiver, and successful closeout until read-only recovery inspection proves
terminal state and `settle` removes retained state, or the user explicitly
authorizes exact `cancel` and it succeeds. An `unknown` result is an operational
gap. The runner does not guess, signal an unverified process, remove unsafe
state, or permit route advancement. This condition intentionally has no forced
runner cleanup. Resolution requires an explicitly authorized operator to prove
the exact process group terminal through operating-system evidence, repair or
remove only the named operation directory outside Aquarium, and record that
manual settlement in the owning workflow. Until then the route remains blocked.

Web Pro has no resumable provider operation. After authoritative terminal
settlement, `resume-current` means a newly authorized Web Pro invocation on the
same pending assessment ordinal. A preflight rejection before provider launch
has no live provider identity; after handled cleanup proves terminal state, it
may switch routes under the existing rule. A completed invocation consumes its
ordinal. An incomplete or failed invocation consumes none.

There is no automatic retry, model substitution, route fallback, waiver,
installation, authentication, or cleanup of unrelated native browser state.

## EPIC-016 adapter

`web-pro` joins `mulgae`, `orca`, `native-codex`, and `waived` as an explicit
peer route. Mulgae remains the default when the user selects no alternative.
Only the selected route's prerequisites are checked.

A completed Web Pro checkpoint records:

- `review-route=web-pro`;
- `review-operation=complete`;
- the validated bounded receipt as `review-evidence-reference`;
- reviewer provenance for `chatgpt-web/pro`; and
- `backend-check-result=not-provided`.

The adapter maps the runner result to the EPIC-016 operation vocabulary as
follows:

- `status=complete` with `operation_state=terminal` records `complete`;
- `status=incomplete` with `operation_state=active` or `unknown` records
  `incomplete`; and
- `status=incomplete` with `operation_state=not-started` or `terminal` records
  `failed`.

Incomplete and failed checkpoints preserve the bounded preflight, operation,
or recovery receipt and cannot support completion. Web Pro does not create
Mulgae CI, publication, findings-query, target-digest, or promoted hardening
evidence.
Ordinary Low dispositions remain available; promoted `hardening-deferral`
remains Mulgae-only.

All shared routing remains unchanged:

- ordinals one and two are `work-unit` assessments;
- ordinal three is the last `remediation-confirmation` authorized by the initial
  envelope;
- later correction and confirmation each require a fresh explicit user
  decision;
- clean or settled Low-only evidence ends early;
- a switch preserves every prior ordinal, finding, disposition, evidence
  reference, goal revision, and remaining authority; and
- automatic fallback is forbidden in both directions.

Existing active and archived Procedure snapshots keep their exact declared
route vocabulary and evidence meaning. Web Pro support requires new compatible
Procedure versions and the normal terminal successor-session path. Aquarium
does not mutate or reinterpret an admitted snapshot in place.

## Task requirements

### TASK-072: Define the Web Pro Review contract

Promote this dossier's accepted target, account, source-transmission,
execution, result, retention, failure, and routing rules to their canonical
owners. Resolve every stale statement that describes Web Pro as standalone-only
or outside selectable routing. Keep all current-behavior documentation in the
future or planned state until implementation evidence exists.

Acceptance:

- Standalone and embedded entry paths share one contract.
- The primary-home and browser-account boundary is explicit.
- The v1 result and Markdown contracts are closed and source-safe.
- EPIC-016 remains the authority for route lifecycle and review budgets.
- No document claims that the planned capability is already available.

### TASK-073: Implement primary-profile Web Pro execution

Add the `web-pro-review` skill, deterministic runner, and scoped global
inspection for the bridge version, Full-mode doctor, exact model row, and
alternate-caller-home observation. Keep diagnosis, installation, browser login,
connector setup, restart, source transmission, and review execution as separate
effects.

Acceptance:

- Every bridge and Codex child uses the system user's primary Codex home.
- Alternate caller homes remain unchanged and expose no copied account state.
- All four targets resolve with the shared static-review meanings.
- The runner emits only the closed v1 envelope and removes private output on
  every handled path.
- Prohibited activity, malformed output, interruption, and cleanup failure fail
  closed without retry or fallback.

### TASK-074: Add Web Pro to selectable review routing

Add `web-pro` to Task, Epic, and Validation handler contracts and new Procedure
versions. Carry its receipt and reviewer provenance through review, closeout,
and commit handoffs while preserving existing serial decisions, option limits,
assessment budgets, route continuity, Low settlement, and snapshot
compatibility.

Acceptance:

- Initial selection, current-route recovery, same-route continuation, and
  explicit switching work for Web Pro under the existing lifecycle rules.
- Switching before execution, after terminal incomplete work, and after a
  completed checkpoint preserves the correct pending or next ordinal.
- Prior findings and remaining authority survive every route change.
- Web Pro never admits Mulgae-only evidence or a fabricated backend check.
- Canonical Procedure sources and repository-local copies remain identical.

### TASK-075: Qualify and document Web Pro Review

Run deterministic unit and integration checks, Procedure graph regression,
official Podway compatibility required by the repository, and one separately
authorized real account-bound review. Master performs the required manual skill
acceptance after automated verification. Promote accepted current behavior to
canonical specifications, public privacy and terms, local interfaces,
capabilities, tool integration status, and the open changelog only after the
implementation evidence exists.

Acceptance scenarios:

| Area | Required evidence |
| --- | --- |
| Account isolation | A caller under an alternate Codex home uses the system user's primary bridge profile without changing either home. |
| Backend readiness | Wrong version, invalid doctor, Browser-only mode, doctor error, missing Codex, hidden or absent Pro model, and missing CLI options all fail before transmission. |
| Targets | Staged excludes unstaged bytes; head excludes index and worktree; root commit, ordinary commit, two-dot range, and three-dot range resolve correctly. |
| Result validation | Missing, duplicate, reordered, oversized, wrong-reviewer, wrong-purpose, wrong-scope, and wrong-target report elements are rejected. |
| Execution safety | Mutation, tests, builds, provider chaining, unrelated network work, nonzero exit, malformed events, timeout, interruption, and cleanup failure return incomplete evidence. A lost reserve response, partial reservation, and concurrent absent-state settlement prove that a late reserve cannot publish or launch. |
| Privacy | No raw transcript, source fragment, full command, credential path, or alternate-home account state appears in the receipt or diagnostics. |
| Routing | Initial selection, failed preflight switch, terminal incomplete switch, active or unknown rejection, completed-route continuation, cross-route change, waiver, and stop preserve EPIC-016 semantics. |
| Compatibility | New Procedures validate, respect declaration limits, pass focused graph cases, and qualify against the repository-required official Podway artifact. |
| Live route | With separate source-transmission authority, one real review from an alternate caller home returns valid direct `report_text` and a complete bounded receipt. |
| Manual acceptance | Master confirms standalone invocation, embedded selection, prerequisite isolation, no fallback, provider continuity, and report delivery. |

## Exclusions

This epic does not:

- re-enable or modify Independent Review;
- change Mulgae, Orca, native Codex, waiver, or Dolgorae ownership;
- add automatic fallback, retry, persistent route preference, or route priority;
- copy browser credentials or install Web models into another Codex home;
- add `workspace` or `dirty` targets;
- create a worktree, checkout copy, capture manifest, fingerprint, or target
  digest;
- make Web Pro evidence eligible for Mulgae-only promoted hardening deferral;
- weaken verification, completion assessment, finding disposition, or final
  approval requirements; or
- authorize implementation, installation, provider execution, commit, push,
  release, or publication through this planning change.
