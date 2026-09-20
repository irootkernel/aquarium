# Workflow review routing

This specification describes the selectable routing contract delivered by
`EPIC-016`. The shared
[workflow review routing contract](../../plugins/aquarium/references/review-routing-contract.md)
defines route selection, evidence, switching, waiver, and Low-settlement
semantics for Task delivery, Epic member delivery, whole-Epic review, and cold
validation. The managed Procedures record route-specific recovery
evidence; provider dispatch and report wording still require observed-agent
acceptance.

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
| `mulgae` | Default route. It retains immutable capture, selected-role execution, recovery, publication, findings, CI, and retention under the Mulgae contract. |
| `orca` | Requires an explicitly selected reviewer and an Orca-supported target. Orca supervises one fresh static reviewer in the current registered worktree. |
| `native-codex` | Requires explicit selection and fresh delegation supplied by the current host. The subagent performs one static, report-only review with host-owned provenance. |
| `waived` | Launches no delegated reviewer. The coordinator performs the required criterion assessment from current authorized evidence and records `review waived`, its authority, reason, and assurance limitation. |

The Dolgorae-backed Independent Review route remains disabled. The shared model
must leave room for a future adapter, but `independent` is not a selectable route
in this epic.

## Selection and authorization

One route is selected for the workflow during plan or validation-envelope
approval. That choice remains the default for every later assessment checkpoint.
Selecting Orca also records its reviewer. Each delegated route records its source
scope and transmission boundary. Selecting `waived` records the target, the
explicit waiver, its reason, and the resulting assurance limitation.

A Task follow-up checkpoint on the same route uses `continue-current` after an
exact `complete` or `waived` operation. It preserves the completed ordinal,
finding lineage, and correction authority, then consumes the next ordinal for
the fresh assessment. Task `resume-current` is reserved for an `incomplete` or
`failed` operation that has not consumed an ordinal. Goal and validation retain
their existing route-direction vocabulary.

When no alternative is requested, Aquarium selects Mulgae. If the selected route
is unavailable or cannot represent the target, the workflow stops before another
provider call and asks the user to choose one of these actions:

- resume or recover the current route;
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

Task delivery may use Orca's `staged` target only when the complete task candidate
can be isolated from unrelated index entries. Epic completion and cold validation
may use an exact `HEAD`, commit, or range target when the candidate is committed.
An unsupported `workspace` or `dirty` target makes Orca unavailable for that
checkpoint. Native Codex receives the exact bounded candidate that the host can
present without inventing backend guarantees. Mulgae retains its current target
rules.

## Common evidence

The Procedures and handlers record these route-neutral facts:

| Field | Meaning |
| --- | --- |
| `review-route` | `mulgae`, `orca`, `native-codex`, or `waived` |
| `assessment-ordinal` | Positive ordinal of each completed delegated review or completed waiver assessment for the current goal revision |
| `assessment-kind` | `work-unit` for ordinals one and two; `remediation-confirmation` for ordinal three and any explicitly authorized later checkpoint |
| `review-operation` | `complete`, `incomplete`, `failed`, or `waived` |
| `review-evidence-reference` | Native run, lifecycle, delegation, or waiver evidence needed to recover the checkpoint |
| `backend-check-result` | `pass`, `fail`, or `not-provided`; absence of a backend check never replaces workflow verification |
| `assessment-provenance` | Reviewer evidence or `coordinator-waiver` evidence |
| `waiver-summary` | Required only for `waived`; records authority, target, reason, and limitations |
| `prior-review-route` and `prior-review-operation` | The immediately preceding review route and operation used for recovery or follow-up; a completed waiver is preserved as `waived`/`waived`, while both fields use their declared not-applicable state before any review operation starts |
| `route-binding-result` | Caller-recorded check that binds the effective route to the immediately preceding operation, current direction and authority, lifecycle settlement, findings, ordinal, goal revision, and remaining authority; Podway does not execute or attest it |

The following combinations are valid for a completed checkpoint:

| Route and operation | Required evidence |
| --- | --- |
| `mulgae` and `complete` | An exact root or composite reference, reviewer provenance, and `backend-check-result` set to `pass` or `fail`. Mulgae CI cannot be omitted as `not-provided`. |
| `orca` or `native-codex` and `complete` | The native lifecycle or delegation reference, reviewer provenance, and `backend-check-result=not-provided`. These static routes do not manufacture a backend CI result. |
| `waived` and `waived` | Waiver authority, `assessment-provenance=coordinator-waiver`, a waiver summary, and `backend-check-result=not-provided`. |

An `incomplete` or `failed` operation preserves every available native reference
but never supports completion. Its backend check cannot compensate for the
operation state.

Existing finding, priority, disposition, Review Brief, criterion assessment, and
verification facts remain separate. An incomplete or failed attempt does not
consume an assessment ordinal. Continuing or switching after a completed
checkpoint uses the next ordinal and preserves every prior evidence reference
and finding.

The initial workflow envelope permits at most two `work-unit` assessments and
one `remediation-confirmation`, but a clean or settled Low-only result ends the
sequence early. Each work-unit brief identifies the named Task, Epic, or explicit
objective, its requirements and authorities, the exact candidate, relevant work
or correction commits, changed paths and artifacts, verification evidence, and
excluded state. This package is the review boundary; Aquarium does not leave the
target implicit or invite a repository-wide audit.

Ordinal three and any later checkpoint inspect only the frozen prior finding
IDs, correction commits or captured delta, invalidated criteria, directly
affected callers, contracts and tests, and regressions caused by the correction.
If Medium-or-higher work or an affected completion gap remains after ordinal
three, the workflow stops for user direction. Each explicit `fix-and-review`
choice authorizes one correction and one next-ordinal remediation confirmation.
A broader objective, requirement set, or changed surface requires an approved
new goal revision or work-unit assessment.

Backend readiness is conditional. A Mulgae installation, skill, CLI, or project
MCP gap blocks only the Mulgae route. Orca readiness blocks only Orca. Missing
host delegation blocks only `native-codex`. The workflow must still report the
selected route's exact prerequisite failure.

## Native evidence-dependent deferral

All routes support the ordinary Low dispositions in the shared finding contract.
A Low finding may receive a self-evident fix, a bounded fix, a canonical
deferred-feedback entry, or a TODO candidate when it meets that disposition's
requirements.

The member-task `hardening-deferral` promotion path has stronger evidence needs.
It requires an exact Mulgae run and finding membership, committed publication,
a successful findings query, and an authoritative native target SHA-256 that
matches the promoted manifest. Only Mulgae supplies that contract in this epic.

Orca, native Codex, and `waived` must not invent a Mulgae run, finding ID,
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

A route change or waiver never erases an earlier finding. A valid Medium-or-higher
finding must still be corrected and verified. The corrected target then receives
the next authorized delegated review or waiver assessment under the
assessment-kind boundary above. The existing bounded rework policy still applies,
including fresh user direction when its authority is exhausted.

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
Mulgae invocation remains with `$use-mulgae`; an active or unproven Orca worker
remains with Orca supervision. When no exact identity or native evidence can
resolve an uncertain mutation, the workflow stops with an operational gap rather
than launching another reviewer or closing through a waiver.

Pre-routing Procedure snapshots keep their immutable Mulgae-only meaning.
Admitted selectable-routing snapshots keep the exact routes, fields, and graph
semantics recorded by their own version. Aquarium does not rewrite either kind
of evidence, reinterpret a Mulgae run field as another backend, or migrate an
active session in place. A workflow that needs a newer contract uses the
supported terminal and successor-session path.

## Non-goals

`EPIC-016` does not re-enable Independent Review, add automatic fallback, create
a persistent route preference, make route guarantees equivalent, weaken required
verification, or change standalone review entrypoints beyond the delegation
needed by the owning handlers.
