# Workflow review routing

This specification describes the selectable routing contract delivered by
`EPIC-016` and updated by `EPIC-020`. The shared
[workflow review routing contract](../../plugins/aquarium/references/review-routing-contract.md)
defines route selection, evidence, switching, waiver, and Low-settlement
semantics for Task delivery, Epic member delivery, whole-Epic review, and cold
validation. The managed Procedures record route-specific recovery
evidence; provider dispatch and report wording still require observed-agent
acceptance.

The [migration contract](../../plugins/aquarium/references/herdr-migration.md)
defines selected-route setup and preserved Orca-era state. Prior source identity,
native validity, handler compatibility and route membership are distinct.
An active or uncertain legacy worker blocks a replacement review until its owner
establishes safe state; the current package never invokes Orca to settle it.
Completed evidence keeps its provenance, findings and consumed ordinals, while
an incomplete checkpoint keeps its pending ordinal. Source updates affect only
successors, and a snapshot that cannot record a required decision takes its
supported stop and separately authorized lifecycle path.

## Purpose and authority

Completion review and review execution are separate concerns. A workflow may
require review evidence without requiring one particular backend. Aquarium will
keep Mulgae as the default while allowing the user to select another supported
route or explicitly waive delegated review for one workflow.

The selected route owns its native execution, storage, recovery, and lifecycle.
Aquarium owns route selection, the Review Brief, local adjudication, completion
assessment, review budgets, and the decision to advance or stop. A route does not
inherit another backend's guarantees.

The workflow plan or validation envelope records the effective review policy.
Repository instructions and higher-priority authority may require a narrower
choice. Aquarium will not create repository-local or user-global state for a
preferred route.

## Routes

| Route | Availability and behavior |
| --- | --- |
| `mulgae` | Default route. It owns live-source admission, selected-role execution, provider-free publication reconciliation, findings, CI and retention under the Mulgae contract. A new root after terminal failure requires explicit authority; historical composites remain readable. |
| `herdr` | Requires an explicitly selected reviewer and a Herdr-supported target. Herdr supervises one fresh static reviewer in the current local session; admission requires submission/activity correlation and the complete purpose-specific report. |
| `independent-review` | Requires explicit selection and three fresh host delegations. The subagents review one target and Brief with separate focus; Aquarium aggregates their static reports. |
| `waived` | Launches no delegated reviewer. The coordinator performs the required criterion assessment from current authorized evidence and records `review waived`, its authority, reason, and assurance limitation. |

Independent Review uses host-native Codex subagents. A future Dolgorae review
would have a separate route and admission contract.

## Selection and authorization

One route is selected for the workflow during plan or validation-envelope
approval. That choice remains the default for every later assessment checkpoint.
Herdr selection records the reviewer kind in the selection summary and carries
any requested native model and effort in the Review Brief. Each delegated route
records its source scope and transmission boundary. Selecting `waived` records
the target, the explicit waiver, its reason, and the resulting assurance limitation.

A Task follow-up checkpoint on the same route uses `continue-current` after an
exact `complete` or `waived` operation. It preserves the completed ordinal,
finding lineage, and correction authority, then consumes the next ordinal for
the fresh assessment. Task `resume-current` is reserved for an `incomplete` or
`failed` operation that has not consumed an ordinal. Goal and validation retain
their existing route-direction vocabulary.

When no alternative is requested, Aquarium selects Mulgae. If the selected route
is unavailable or cannot represent the target, the workflow stops before another
provider call and asks the user to choose one of these actions:

- resume the current invocation or supported publication reconciliation, or repeat preflight and first execution under the unused review grant when native evidence establishes that no invocation or run started;
- explicitly authorize one fresh same-route Mulgae review after terminal incomplete/failed settlement, preserving the pending ordinal and findings;
- switch to one supported route;
- waive delegated review; or
- stop the workflow.

Aquarium never applies an automatic fallback chain. A bounded route change does
not reopen the complete implementation plan when the requirements, candidate,
and effect boundary remain unchanged. A changed source scope, new transmission,
different requirement set, or wider repository effect requires the approval
owned by that change.

## Target eligibility

Each route keeps its native target vocabulary. Route selection cannot silently
stage files, commit work, copy a checkout, broaden the source scope, or include
unrelated changes.

Task delivery may use Herdr's `staged` target only when the complete task candidate
can be isolated from unrelated index entries. Epic completion and cold validation
may use an exact `HEAD`, commit, or range target when the candidate is committed.
An unsupported `workspace` or `dirty` target makes Herdr unavailable for that
checkpoint. Independent Review receives the exact bounded candidate that the host can
present without inventing backend guarantees. Mulgae retains its current target
rules.

The owning handler prepares the complete staged Task candidate under approved
staging authority before delegating Herdr review. It includes new files and
documentation, preserves unrelated index entries, and stops when they prevent
safe isolation. Report-only review does not prepare the index.

## Common evidence

The Procedures and handlers record these route-neutral facts:

| Field | Meaning |
| --- | --- |
| `review-route` | `mulgae`, `herdr`, `independent-review`, or `waived` |
| `assessment-ordinal` | Positive ordinal of each completed delegated review or completed waiver assessment for the current goal revision |
| `assessment-kind` | `work-unit` for ordinals one through three; `remediation-confirmation` for ordinal four and any explicitly authorized later checkpoint |
| `review-operation` | `complete`, `incomplete`, `failed`, or `waived` |
| `review-evidence-reference` | Native run, lifecycle, delegation, or waiver evidence needed to recover the checkpoint |
| `backend-check-result` | `pass`, `fail`, or `not-provided`; absence of a backend check never replaces workflow verification |
| `assessment-provenance` | Reviewer evidence or `coordinator-waiver` evidence |
| `waiver-summary` | Required only for `waived`; records authority, target, reason, and limitations |
| `prior-review-route` and `prior-review-operation` | The immediately preceding route and operation used for recovery or follow-up. Retain historical `orca` in `prior-review-route` without authorizing current dispatch, preserve a completed waiver as `waived`/`waived`, and use the declared not-applicable state only when no predecessor exists. |
| `route-binding-result` | Caller-recorded check that binds the effective route to the immediately preceding operation, current direction and authority, lifecycle settlement, findings, ordinal, goal revision, and remaining authority; Podway does not execute or attest it |

The following combinations are valid for a completed checkpoint:

| Route and operation | Required evidence |
| --- | --- |
| `mulgae` and `complete` | An exact live-source root or verified historical composite reference, reviewer provenance, and `backend-check-result` set to `pass` or `fail`. Mulgae CI cannot be omitted as `not-provided`. |
| `herdr` and `complete` | Fresh requested identity, submission/activity correlation, applicable target and Brief, complete report and native operation references under Herdr supervision, reviewer provenance, and `backend-check-result=not-provided`. Idle or done alone is insufficient. |
| `independent-review` and `complete` | Three completed host delegations for one target and Brief, required criterion coverage, reviewer provenance, and `backend-check-result=not-provided`. The group consumes one ordinal. |
| `waived` and `waived` | Waiver authority, `assessment-provenance=coordinator-waiver`, a waiver summary, and `backend-check-result=not-provided`. |

An `incomplete` or `failed` operation preserves every available native reference
but never supports completion. Its backend check cannot compensate for the
operation state.

Existing finding, priority, disposition, Review Brief, criterion assessment, and
verification facts remain separate. An incomplete or failed attempt does not
consume an assessment ordinal. Continuing or switching after a completed
checkpoint uses the next ordinal and preserves every prior evidence reference
and finding.

The initial workflow envelope permits at most three `work-unit` assessments and
one `remediation-confirmation`, but a clean or locally settled result ends the
sequence early. Each work-unit brief identifies the named Task, Epic, or explicit
objective, its requirements and authorities, the exact candidate, relevant work
or correction commits, changed paths and artifacts, verification evidence, and
excluded state. This package is the review boundary; Aquarium does not leave the
target implicit or invite a repository-wide audit.

Ordinal four and any later checkpoint inspect only the frozen prior finding
IDs, correction commits or exact source delta, invalidated criteria, directly
affected callers, contracts and tests, and regressions caused by the correction.
If work requiring another provider assessment remains after ordinal
four, the workflow stops for user direction. Each explicit `fix-and-review`
choice authorizes one correction and one next-ordinal remediation confirmation.
A broader objective, requirement set, or changed surface requires an approved
new goal revision.

Backend readiness is conditional. A Mulgae installation, skill, CLI, or project
MCP gap blocks only the Mulgae route. Herdr readiness blocks only Herdr. Missing
host delegation blocks only `independent-review`. The workflow must still report the
selected route's exact prerequisite failure.

Podway readiness also depends on the selected route in the exact Procedure
snapshot. The setup inspector reports `review_route_readiness` for current routes,
but routine session admission checks the installed Procedure declarations directly
after native and handler-contract checks. General readiness alone cannot admit a
route absent from a prior-canonical snapshot. Active sessions retain their own
declarations and evidence. A retired `native-codex` checkpoint takes an explicit
failed-prerequisite disposition,
supported route change or waiver, or stop and successor; it never dispatches the
retired reviewer or relabels Independent Review evidence.

Host wait timeouts leave Independent Review delegations pending. Resume the
same references until every agent has an authoritative terminal state. Explicit
`resume-current` after a settled incomplete operation may start a fresh group
with the same target, Brief, model and effort, preserving earlier reports and
the pending ordinal. Herdr waiting and exact retry follow its live native
contract without an Aquarium deadline or retry cap. Both routes report reviewer
violations separately and withhold a final verdict when target integrity,
identity, source scope, coverage, or lifecycle evidence is compromised or unknown.

## Native evidence-dependent deferral

All routes support the ordinary Low dispositions in the shared finding contract.
A Low finding may receive a self-evident fix, a bounded fix, a canonical
deferred-feedback entry, or a TODO candidate when it meets that disposition's
requirements.

The member-task `hardening-deferral` promotion path has stronger evidence needs.
It requires an exact Mulgae run and finding membership, committed publication,
a successful findings query, and a verified schema-specific native target binding
that matches the promoted manifest: a v1 content digest, or a v2 preflight identity
whose recomputed metadata digest matches the completed run, with scope-derived
consistency and the caller source-consistency observation. Only Mulgae supplies
that contract in this epic.

Herdr, Independent Review, and `waived` must not invent a Mulgae run, finding ID,
capture, or target digest. Their Low findings use the ordinary dispositions. If
a downstream requirement specifically needs promoted native evidence and no
selected route can provide it, the workflow reports an evidence gap and stops.
It does not launch Mulgae automatically. Another backend may support promotion
only after a later contract defines and verifies equivalent producer evidence.

## Waiver and completion

`waived` removes delegated review, not verification or acceptance. The
coordinator must assess the same Review Brief and every applicable completion
criterion against the exact current target. It may use only evidence already
authorized by the workflow. It records direct findings under coordinator
provenance and applies the shared finding-disposition rules.

A waived workflow may reach its successful roadmap state only when:

- every required workflow check has current passing evidence;
- every criterion is `met` or legitimately `not-applicable`;
- no finding remains valid and unresolved or needs confirmation;
- every admitted Low finding has a complete disposition and passing local
  verification; and
- all ordinary lifecycle, target, documentation, and residue conditions pass.

Reports must say `review waived`. They must not call the result independently
reviewed, provider-reviewed, or a clean delegated review.

A route change or waiver never erases an earlier finding. A valid Medium-or-higher finding must still be corrected and verified. Ordinary Low dispositions retain their shared contract. Eligible corrections use
local settlement; other corrected targets receive the next authorized delegated
review or waiver assessment under the
assessment-kind boundary above. The existing bounded rework policy still applies,
including fresh user direction when its authority is exhausted.

A blocker first discovered during Low settlement retains its current target and
source finding identity and enters the applicable rework-authority gate. Task
phase ownership comes from a fresh correction record; the original review
counts remain historical evidence. Implementation re-entry records the native rework cause before
work resumes. A completed Low delta composes with its reviewed basis and local
checks without consuming another assessment.

Validation corrects an admitted audit or review blocker before its next audit
and provider assessment. The original envelope refreshes the complete Epic audit
before work-unit assessments one through three. After the third assessment, or
under a separate one-shot correction grant, it confirms only the frozen
correction set and direct regression surface. Current audit evidence remains
separate from stale attempts and provider findings.

## Recovery and compatibility

The effective route, prior operations, evidence references, assessment ordinals,
findings, and remaining authority are part of workflow recovery. Selecting a
different route records user intent; it does not prove that the prior operation
is safe to leave.

| Prior operation state | Route-change behavior |
| --- | --- |
| No execution started because preflight or a prerequisite failed | Apply the explicit route change or waiver immediately. |
| Active or terminal state unknown | Record the requested change, but start no reviewer and permit no successful closeout. Resume, await, explicitly cancel when authorized, and reconcile through the native owner first. |
| Terminal failed or incomplete | Complete required native settlement and preserve available evidence. Then apply the explicit route change without consuming an assessment ordinal. |
| Terminal complete | Preserve the consumed ordinal, findings, dispositions, and authority. Apply the new route at the next authorized checkpoint. |

An observer timeout does not make an operation terminal. An active or uncertain
Mulgae invocation remains with `$use-mulgae`; an active or unproven Herdr reviewer
remains with the same native Herdr operation. When no exact identity or native evidence can
resolve an uncertain mutation, the workflow stops with an operational gap rather
than launching another reviewer or closing through a waiver.

Pre-routing Procedure snapshots keep their immutable Mulgae-only meaning.
Admitted selectable-routing snapshots keep the exact routes, fields, and graph
semantics recorded by their own version. Aquarium does not rewrite either kind
of evidence, reinterpret a Mulgae run field as another backend, or migrate an
active session in place. A workflow that needs a newer contract uses the
supported terminal and successor-session path.

## Non-goals

Current routing does not add automatic fallback, create a persistent route
preference, make route guarantees equivalent, or weaken required verification.
Historical `native-codex` Procedure snapshots retain their original meaning;
new checkpoints select `independent-review` only in a snapshot that supports it.

## Local corrections and compatibility

Current Task `30`, Goal `33` and Validation `32` snapshots classify eligible local corrections before provider-rework authority. The admitted completed source record carries `local-correction-count` and `local-correction-eligibility`. A positive count and passing eligibility permit `local-verified-fix` under the shared disposition contract regardless of retained source priority. The existing settlement record carries `pending-local-corrections`, exact before/after targets, checks and current completion; `review-predates-local-correction` distinguishes this delta from provider coverage. Original reports and criterion rows remain unchanged. The final required Judge verifies current achievement.

This is a breaking managed-Procedure update: existing users need an authorized file update and compatible successor sessions. Active and archived snapshots retain their original meanings. Candidate installation, upgrade and affected agent behavior require exact-candidate UTM qualification before release; source tests alone do not establish that result. Design and War-room graph behavior is unchanged; their next versions refresh the shared operative role bindings.
