# Workflow Review Routing Contract

Use this contract when an approved Task, Epic, or cold-validation workflow
requires completion review. It separates Aquarium's completion decision from the
native system that supplies reviewer evidence. Read
[review-intent-contract.md](review-intent-contract.md) for the Review Brief and
criterion assessment, [finding-disposition.md](finding-disposition.md) for local
adjudication, and the selected route's native contract before execution.

## Select One Route

The workflow plan selects exactly one route and, where required, its reviewer:

| Route | Selection and native ownership |
| --- | --- |
| `mulgae` | Default when no alternative is selected. Mulgae owns capture, provider execution, recovery, publication, CI, findings, and retention. |
| `orca` | Requires an explicit reviewer and an Orca-supported target. Orca owns its Run, Task, Dispatch, worker, Delivery, acknowledgement, settlement, and recovery. |
| `independent-review` | Requires explicit selection and three fresh host subagents. Aquarium coordinates their static reports; the host owns delegation lifecycle and provenance. |
| `waived` | Requires an explicit delegated-review waiver. It launches no reviewer; the coordinator assesses the same complete Review Brief from current authorized evidence. |

The selected route remains effective at later checkpoints until the user
explicitly authorizes a bounded route change. Do not create a repository or
user-global preference.

Check only the selected route's prerequisites. A missing Mulgae installation,
project MCP, provider, or paired skill does not block Orca, Independent Review,
or a waiver. Orca requires its requested reviewer and supported target.
Independent Review requires fresh host delegation for three subagents and any
explicitly requested model or effort. A waiver requires no backend readiness.

## Preserve Route-Specific Targets and Guarantees

Route selection never stages files, creates a commit, copies a checkout,
broadens source scope, or includes unrelated state. Preserve the native target
vocabulary and report the exact included and excluded state.

Before delegating a staged Task review, the owning handler uses its approved staging authority to stage the complete Task candidate, including new files and documentation. Reconcile the index with the intended candidate and preserve unrelated entries; if those entries prevent isolation, stop for a concrete target or staging decision. The report-only reviewer never prepares or repairs the index. Repeat this preparation after authorized corrections before a later staged checkpoint.

- Mulgae retains its supported target meanings and immutable-capture contract.
- Orca uses `staged`, `head`, `commit`, or `range` through the static review
  contract. A Task may use `staged` only when the complete candidate is isolated
  from unrelated index entries. Epic and validation checkpoints may use an
  exact committed target.
- Independent Review uses the six common target scopes through its target
  inspector and gives the same exact target and Review Brief to three fresh
  static, report-only subagents. A mutable target is checked again after review;
  a matching fingerprint is not an immutable capture guarantee.
- A waiver binds the exact target assessed by the coordinator and records the
  absence of delegated review.

Never describe Orca, Independent Review, or a waiver as a Mulgae capture,
publication, CI result, findings query, or recovery guarantee. Independent
Review does not use Dolgorae or inherit Orca lifecycle guarantees.

## Procedure Route Compatibility

On the Podway path, check the selected Procedure's route readiness under [podway-integration.md](podway-integration.md#check-readiness-on-the-default-path) before starting a new session or dispatching a resumed checkpoint. A recognized historical snapshot may support Mulgae or Orca while lacking Independent Review. Never equate generic handler compatibility with every route being executable, record `independent-review` as `native-codex`, or revive retired single-agent dispatch.

Preserve an in-flight `native-codex` snapshot and its earlier evidence. For a new checkpoint on that route, record the failed prerequisite without inventing a delegation. Offer an explicitly authorized switch to a supported route, a waiver where that snapshot admits it, or stop and a separately authorized successor after native lifecycle settlement. If the snapshot cannot record the desired route or disposition, leave that decision unset and use its supported stop path; installing new Procedure bytes does not migrate the session. Existing completed evidence keeps its original route and provenance.

## Record Route-Neutral Evidence

Keep the following facts separate from finding, completion, verification, and
workflow-lifecycle decisions:

| Field | Contract |
| --- | --- |
| `review-route` | `mulgae`, `orca`, `independent-review`, or `waived`. |
| `assessment-ordinal` | Positive ordinal assigned only after a delegated review completes or a waiver assessment completes for the current goal revision. |
| `assessment-kind` | `work-unit` for the first three assessments or `remediation-confirmation` for ordinal four and later. |
| `review-operation` | `complete`, `incomplete`, `failed`, or `waived`. |
| `review-evidence-reference` | Bounded native lifecycle, delegation, or waiver evidence sufficient to recover the checkpoint. |
| `backend-check-result` | `pass`, `fail`, or `not-provided`. It never replaces workflow verification. |
| `assessment-provenance` | Reviewer evidence for delegated routes or `coordinator-waiver` for a waiver. |
| `waiver-summary` | For `waived` only: authority, target, reason, and assurance limitation. |

Admit only these completed combinations:

- `mulgae` plus `complete` requires an exact root or verified composite,
  reviewer provenance, committed publication, complete coverage, a successful
  findings query, and `backend-check-result` of `pass` or `fail`. Mulgae CI may
  not be `not-provided`.
- `orca` plus `complete` requires authoritative native lifecycle, reviewer
  provenance, and `backend-check-result=not-provided`. `independent-review`
  plus `complete` requires three completed host delegations for the same target
  and Brief, all required criterion assessments, reviewer provenance, and
  `backend-check-result=not-provided`. The three reports consume one ordinal.
- `waived` plus `waived` requires explicit waiver authority,
  `assessment-provenance=coordinator-waiver`, a complete waiver summary, and
  `backend-check-result=not-provided`.

For operations that do not complete, admit only these combinations:

- `mulgae` plus `incomplete` or `failed` retains Mulgae operation provenance,
  every issued native reference, and the observed backend check. Use
  `not-provided` only when no authoritative CI result exists.
- `orca` or `independent-review` plus `incomplete` or `failed` retains the
  matching native lifecycle or host-delegation provenance and every available
  reference, with `backend-check-result=not-provided`.
- `waived` admits only `review-operation=waived`; it never records `complete`,
  `incomplete`, or `failed`. Delegated routes never use
  `assessment-provenance=coordinator-waiver`.

When failure occurs before a native identity exists, the evidence reference is a
bounded preflight-failure record for the selected route, not an invented run or
delegation identity. An `incomplete` or `failed` operation cannot support
completion and consumes no assessment ordinal. A completed checkpoint consumes
one ordinal even when it reports findings or a failing backend check. Recovery
internal to one native operation does not create another ordinal. Switching
after a completed checkpoint uses the next ordinal and preserves the earlier
result.

## Change or Recover a Route

A route failure stops for user direction. Never start another route or apply a
waiver automatically. Offer only the actions supported by current authority:

- `resume-current`: continue or recover the current native operation through
  its owner, or restart a settled incomplete Independent Review as specified below;
- `continue-current` (Task only): run the next authorized assessment on the
  same route after an exact completed delegated review or waiver assessment;
- `switch-route`: select one supported route after the prior operation reaches
  an authoritative safe state;
- `waive`: record an explicit waiver after the prior operation reaches an
  authoritative safe state;
- `stop`: stop workflow advancement without claiming successful completion.

Apply the requested transition according to the prior operation state:

| Prior state | Admission rule |
| --- | --- |
| Not started because preflight or a prerequisite failed | Apply the explicit route change or waiver immediately. |
| Active or terminal state unknown | Record intent only. Resume, await, or explicitly cancel through the native owner before another route starts or waiver can close. |
| Terminal failed or incomplete | Complete native settlement, retain available evidence, then change route without consuming an ordinal. |
| Terminal complete | Retain its ordinal, findings, dispositions, and remaining authority; use the new route only at the next authorized checkpoint. |

A timeout is not terminal evidence. An uncertain mutation or missing native
identity is an operational gap, not permission to launch another reviewer.
Changing route does not reset the goal revision, remediation budget, findings,
or corrected-target confirmation obligation.

## Bound assessment convergence

For Independent Review, a host wait timeout leaves the same delegations pending. Resume those references through the host while any worker is active or its state is unknown. Once all three are authoritatively settled, explicit `resume-current` may authorize one fresh three-agent operation for the same target, Brief, model and effort; retain every earlier report and finding, and reuse the unconsumed ordinal. Recheck mutable target identity first. Changed bytes require a refreshed authorized Brief and affected verification, never an assertion that the old review covered them. An embedded restart remains subject to the owning workflow's scope and remaining authority; standalone restart needs explicit authority. Do not silently substitute a provider or reuse successful agents as a replacement for the required fresh three-agent operation.

Assessment budgets are maxima, not rounds to consume. Stop after a clean result or completed Low-only settlement. For one goal revision, ordinals one through three use `assessment-kind=work-unit` with the exact named objective, authority, candidate, work commits or capture identity, changed paths, artifacts, and verification evidence. Ordinal four uses `assessment-kind=remediation-confirmation` and is the last checkpoint authorized by the initial workflow envelope.

Ordinal four and every later checkpoint may inspect only the frozen prior findings, correction commits or capture delta, invalidated criteria, directly affected callers, contracts and tests, and correction-caused regressions. A remaining Medium-or-higher finding or completion gap after ordinal four stops for user direction. Each explicit `fix-and-review` choice authorizes one correction and one next-ordinal remediation confirmation. It does not authorize another work-unit assessment or a reusable review loop.

A material objective, requirement, or changed-surface expansion requires an explicitly approved new goal revision or work-unit assessment. Do not reset ordinals, silently broaden a remediation confirmation, or use unrelated observations to extend the current loop.

For Task checkpoints, `continue-current` requires the effective route to equal
the immediately preceding `complete` or `waived` route. It retains that
checkpoint's consumed ordinal, findings, lineage, and remaining authority, then
assigns the next ordinal to the fresh assessment. Task `resume-current` admits
only an immediately preceding `incomplete` or `failed` operation and retains its
pending ordinal. Goal and validation keep their existing route-direction
vocabulary.

Each fresh Goal or validation checkpoint carries the immediately preceding
review route and operation. Its caller-recorded route-binding check must compare
those values with the effective route, requested direction, lifecycle settlement,
findings, ordinal, goal revision, and remaining authority. A `resume-current`
checkpoint fails that check when the effective provider differs from the
immediately preceding unsettled provider; earlier route-change authority cannot
authorize that mismatch.

For `stop`, preserve the prior operation rather than treating the choice as
native cancellation or settlement. If it is active or its terminal state is
unknown, report its identity and last authoritative state, leave it with its
native owner, and end only Aquarium advancement. Cancellation requires separate
explicit authority under that owner's contract. If the operation is terminal,
retain its evidence, consumed ordinal when complete, findings, and dispositions,
then end with an unsuccessful workflow assessment.

## Assess Waived Completion

A waiver removes delegated review only. The coordinator uses the complete Review
Brief, exact target, and evidence already authorized by the workflow. Record
direct findings under coordinator provenance and apply the ordinary finding
disposition contract.

A waived checkpoint supports completion only when every required workflow check
passes, every criterion is `met` or legitimately `not-applicable`, no finding is
valid and unresolved or needs confirmation, every admitted Low finding has a
complete disposition with current local verification, and ordinary lifecycle,
documentation, target, and residue conditions pass. Reports must say `review
waived` and must not claim independent, provider, or delegated review.

## Preserve Findings and Low Settlement

Every route uses the shared finding-disposition contract. A route change or
waiver never erases an earlier finding. A valid Medium-or-higher finding remains
blocking until corrected, verified, and assessed at the next authorized
checkpoint. Preserve the existing bounded correction and confirmation budget.

All routes support the ordinary finite Low dispositions. The promoted
`hardening-deferral` path remains Mulgae-only because it requires exact run and
finding membership, committed publication, a successful findings query, and an
authoritative native target SHA-256. Orca, Independent Review, and waiver evidence must
state that no promoted hardening evidence applies; never invent a Mulgae run,
finding identity, capture, publication, query, or target digest.

## Preserve Compatibility and Residency

New Procedure versions may record this route-neutral contract. Existing active
or archived Procedure snapshots keep their declared evidence meanings and are
never migrated or reinterpreted in place.

Runtime and orchestration references remain non-canonical. Do not place backend
run IDs, subagent identities, provider or model names, reports, transcripts, or
waiver execution logs in tracked roadmap or product documentation. A commit
handoff carries bounded provenance and the complete Low-settlement composition,
or explicitly states that neither a Low-only delta nor promoted evidence applies.
