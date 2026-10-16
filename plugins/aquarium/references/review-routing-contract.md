# Workflow Review Routing Contract

Use this contract when an approved Task, Epic, or cold-validation workflow
requires completion review. It separates Aquarium's completion decision from the
native system that supplies reviewer evidence. Read
[review-intent-contract.md](review-intent-contract.md) for the Review Brief and
criterion assessment, [finding-disposition.md](finding-disposition.md) for local
adjudication, and the selected route's native contract before execution.

## Select One Route

Read [review strategies](review-strategy-contract.md). At workflow startup,
recommend from the original goal, scope, difficulty, consequences and
uncertainty, then record Master's choice through the existing plan or envelope.
Honor an explicit selection without repeating the question at every checkpoint.
Use [result handoff](review-result-handoff.md) for native output collection and
same-operation recovery; a missing guessed report file does not justify review.

The workflow plan selects exactly one route and, where required, its reviewer:

| Route | Selection and native ownership |
| --- | --- |
| `mulgae` | Starting recommendation for small, bounded work. Mulgae owns source admission, provider execution, publication reconciliation, publication, CI, findings, and retention. |
| `herdr` | Requires an explicit reviewer kind and a supported target; honors any requested native model and effort. Herdr owns the local pane, agent, submission, observation, output and recovery. |
| `independent-review` | Requires explicit selection, three fresh base reviewers in the Primary harness and an additional UI/UX specialist when applicable. Aquarium coordinates their static reports; the host owns delegation lifecycle and provenance. |
| `waived` | Requires an explicit delegated-review waiver. It launches no reviewer; the coordinator assesses the same complete Review Brief from current authorized evidence. |

The selected route remains effective at later checkpoints until the user
explicitly authorizes a bounded route change. Do not create a repository or
user-global preference.

Check only the selected route's prerequisites. A missing Mulgae installation,
project MCP, provider, or paired skill does not block Herdr, Independent Review,
or a waiver. Herdr requires its upstream skill, requested reviewer, supported
target and caller context under [herdr-supervision.md](herdr-supervision.md).
Independent Review requires fresh host delegation for its expected team and any
explicitly requested model or effort. A waiver requires no backend readiness.

## Preserve Route-Specific Targets and Guarantees

Current Task v32, Goal v35 and Validation v34 sources carry the strategy and
team-delivery contract. Earlier session snapshots keep their admitted topology:
three base Independent reviewers and one Herdr reviewer, unless their actual
contract already supplies more. Do not claim the new UI/team behavior from
route membership or generic handler readiness alone. Use an authorized managed
update and compatible successor when the admitted source cannot support the
selected topology; preserve customized files and historical evidence.

Route selection never stages files, creates a commit, copies a checkout,
broadens source scope, or includes unrelated state. Preserve the native target
vocabulary and report the exact included and excluded state.

Before delegating a staged Task review, the owning handler uses its approved staging authority to stage the complete Task candidate, including new files and documentation. Reconcile the index with the intended candidate and preserve unrelated entries; if those entries prevent isolation, stop for a concrete target or staging decision. The report-only reviewer never prepares or repairs the index. Repeat this preparation after authorized corrections before a later staged checkpoint.

- Mulgae uses workspace, stage, head, commit or diff through its native live-source contract. Keep workspace/index unchanged through completion, preserve resolved Git operands and record source identity and consistency without claiming a content snapshot.
- Herdr uses `staged`, `head`, `commit`, or `range` through the static review
  contract. A Task may use `staged` only when the complete candidate is isolated
  from unrelated index entries. Epic and validation checkpoints may use an
  exact committed target.
- Independent Review uses the six common target scopes through its target
  inspector and gives the same exact target and Review Brief to every expected
  fresh static, report-only reviewer. A mutable target is checked again after review;
  a matching fingerprint is not an immutable capture guarantee.
- A waiver binds the exact target assessed by the coordinator and records the
  absence of delegated review.

Never describe Herdr, Independent Review, or a waiver as a Mulgae capture,
publication, CI result, findings query, or recovery guarantee. Independent
Review does not use Dolgorae or inherit Herdr lifecycle guarantees.

## Procedure Route Compatibility

On the Podway path, check the selected Procedure's route readiness under [podway-integration.md](podway-integration.md#check-readiness-on-the-default-path) before starting a new session or dispatching a resumed checkpoint. A recognized historical snapshot may support peer routes while retaining retired Orca labels or lacking Independent Review. Historical `orca` evidence remains Orca evidence; it does not authorize dispatch through the retired route. Never relabel it as Herdr or invoke Orca to settle it. Never equate generic handler compatibility with every route being executable, record `independent-review` as `native-codex`, or revive retired single-agent dispatch.

Preserve an in-flight `native-codex` snapshot and its earlier evidence. For a new checkpoint on that route, record the failed prerequisite without inventing a delegation. Offer an explicitly authorized switch to a supported route, a waiver where that snapshot admits it, or stop and a separately authorized successor after native lifecycle settlement. If the snapshot cannot record the desired route or disposition, leave that decision unset and use its supported stop path; installing new Procedure bytes does not migrate the session. Existing completed evidence keeps its original route and provenance.

For a retired Orca checkpoint, an active or uncertain legacy worker prevents a
replacement review until its owner establishes a safe state. The new package
never invokes Orca for settlement. Preserve terminal references, completed
findings and dispositions, consumed ordinals and remaining correction authority;
an incomplete operation keeps the pending ordinal. If the snapshot cannot
record a required route, evidence or acceptance decision, stop through its
supported contract before a separately authorized successor. Follow
[herdr-migration.md](herdr-migration.md) for diagnosis and exact update handling.

## Record Route-Neutral Evidence

The current Task, Goal and Validation Procedures admit `orca` only in
`prior-review-route`, to preserve an exact historical predecessor. It is absent
from current route selectors and dispatch branches. An eligible successor carries
the predecessor session and goal revision, native evidence, consumed ordinal,
finding lineage and remaining authority; it never uses `not-applicable` for an
existing predecessor or resets the count. Switching from Orca requires explicit
route-change authority and verified safe settlement under this contract.

Keep the following facts separate from finding, completion, verification, and
workflow-lifecycle decisions:

| Field | Contract |
| --- | --- |
| `review-route` | `mulgae`, `herdr`, `independent-review`, or `waived`. |
| `assessment-ordinal` | Positive ordinal assigned only after a delegated review completes or a waiver assessment completes for the current goal revision. |
| `assessment-kind` | `work-unit` for the first three assessments or `remediation-confirmation` for ordinal four and later. |
| `review-operation` | `complete`, `incomplete`, `failed`, or `waived`. |
| `review-evidence-reference` | Bounded native lifecycle, delegation, or waiver evidence sufficient to recover the checkpoint. |
| `backend-check-result` | `pass`, `fail`, or `not-provided`. It never replaces workflow verification. |
| `assessment-provenance` | Reviewer evidence for delegated routes or `coordinator-waiver` for a waiver. |
| `waiver-summary` | For `waived` only: authority, target, reason, and assurance limitation. |

Admit only these completed combinations:

- `mulgae` plus `complete` requires an exact live-source root, or verified historical composite,
  reviewer provenance, committed publication, complete coverage, a successful
  findings query, and `backend-check-result` of `pass` or `fail`. Mulgae CI may
  not be `not-provided`.
- `herdr` plus `complete` requires the fresh requested reviewer identity,
  correlated submission and observed activity, the applicable exact target and
  Brief, every expected child report and the main reviewer's complete purpose-specific
  synthesis under [herdr-supervision.md](herdr-supervision.md). Retain native
  operation references, child roles, statuses and available report references,
  UI coverage when applicable, reviewer provenance and
  `backend-check-result=not-provided`. A missing required child report leaves the
  operation incomplete. Idle or done status alone is insufficient.
- `independent-review` plus `complete` requires completed host delegations for all three base reviewers and the UI specialist when applicable, for the same target
  and Brief, all required criterion assessments, reviewer provenance, and
  `backend-check-result=not-provided`. The complete team consumes one ordinal.
- `waived` plus `waived` requires explicit waiver authority,
  `assessment-provenance=coordinator-waiver`, a complete waiver summary, and
  `backend-check-result=not-provided`.

For operations that do not complete, admit only these combinations:

- `mulgae` plus `incomplete` or `failed` retains Mulgae operation provenance,
  every issued native reference, and the observed backend check. Use
  `not-provided` only when no authoritative CI result exists.
- `herdr` or `independent-review` plus `incomplete` or `failed` retains the
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
  its owner, or restart a settled incomplete Independent Review as specified below. For Mulgae, an authoritatively not-started preflight or prerequisite failure returns to preflight and first execution under the still-unconsumed review grant. Once native work started, resume continues the existing invocation or provider-free publication reconciliation and never replaces its root;
- `new-review-current-route`: authorize one fresh Mulgae root only after the previous operation is terminally failed or incomplete and safely settled; refresh current-source preflight, preserve findings and the pending ordinal, and cover the full selected arrangement without rerun or composition;
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
| Not started because preflight or a prerequisite failed | `resume-current` repeats preflight and admits first execution on the same route under remaining review authority, preserving the pending ordinal. An explicit route change or waiver is also safe. |
| Active or terminal state unknown | Record intent only. Resume, await, or explicitly cancel through the native owner before another route starts or waiver can close. |
| Terminal failed or incomplete | Complete native settlement and retain evidence. Explicit same-route new Mulgae review, route change or waiver preserves the pending ordinal; none starts automatically. |
| Terminal complete | Retain its ordinal, findings, dispositions, and remaining authority; use the new route only at the next authorized checkpoint. |

A timeout is not terminal evidence. An uncertain mutation or missing native
identity is an operational gap, not permission to launch another reviewer.
Classify Mulgae as `not-started` only when its native result establishes a preflight or prerequisite failure before any invocation or run was created. An issued invocation with uncertain state remains `active-or-unknown`; a terminal diagnostic run remains terminal. Handle `review_preparation_failed` through the native diagnostic recovery contract. Before first execution, refresh the Brief, source preflight, applicable staged content binding and affected verification without changing the selected arrangement or transmission scope.
Changing route does not reset the goal revision, remediation budget, findings,
or corrected-target confirmation obligation.

## Bound assessment convergence

For Independent Review, a host wait timeout leaves the same delegations pending. Resume those references through the host while any worker is active or its state is unknown. Recover reports through the recorded handles before treating delivery as lost. Once every expected reviewer is authoritatively settled and native retrieval cannot recover the required result, explicit `resume-current` may authorize one fresh operation with the same expected team for the same target, Brief, model and effort; retain every earlier report and finding, and reuse the unconsumed ordinal. Recheck mutable target identity first. Changed bytes require a refreshed authorized Brief and affected verification, never an assertion that the old review covered them. An embedded restart remains subject to the owning workflow's scope and remaining authority; standalone restart needs explicit authority. Do not silently substitute a provider or reuse successful agents as a replacement for the required fresh team operation.

Assessment budgets are maxima, not rounds to consume. Stop after a clean result or completed local settlement. For one goal revision, ordinals one through three use `assessment-kind=work-unit` with the exact named objective, authority, candidate, work commits or exact candidate content binding, changed paths, artifacts, and verification evidence. Ordinal four uses `assessment-kind=remediation-confirmation` and is the last checkpoint authorized by the initial workflow envelope.

Ordinal four and every later checkpoint may inspect only the frozen prior findings, correction commits or exact source delta, invalidated criteria, directly affected callers, contracts and tests, and correction-caused regressions. A remaining finding or completion gap requiring provider reassessment after ordinal four stops for user direction. Each explicit `fix-and-review` choice authorizes one correction and one next-ordinal remediation confirmation. It does not authorize another work-unit assessment or a reusable review loop.

A material objective, requirement, or changed-surface expansion requires an explicitly approved new goal revision. Do not reset ordinals, silently broaden a remediation confirmation, or use unrelated observations to extend the current loop.

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
waiver never erases an earlier finding. A valid Medium-or-higher finding remains blocking until corrected and verified. Ordinary Low dispositions retain their shared contract. Eligible local
corrections settle through the shared composition without a new ordinal; other
corrections require the next authorized provider checkpoint. Preserve the existing bounded correction and confirmation budget.

All routes support the ordinary finite Low dispositions. The promoted
`hardening-deferral` path remains Mulgae-only because it requires exact run and
finding membership, committed publication, a successful findings query, and a
verified schema-specific native target binding. Herdr, Independent Review, and waiver evidence must
state that no promoted hardening evidence applies; never invent a Mulgae run,
finding identity, capture, publication, query, or target digest.

## Preserve Compatibility and Residency

New Procedure versions may record this route-neutral contract. Existing active
or archived Procedure snapshots keep their declared evidence meanings and are
never migrated or reinterpreted in place.

Runtime and orchestration references remain non-canonical. Do not place backend
run IDs, subagent identities, provider or model names, reports, transcripts, or
waiver execution logs in tracked roadmap or product documentation. A commit
handoff carries bounded provenance and the complete local-settlement composition,
or explicitly states that neither a local-settlement delta nor promoted evidence applies.

## Local correction and incident routing

After completed-operation admission, finding confirmation, mandatory backend checks and the existing review-evidence Judge, classify bounded local corrections before asking for provider-rework authority. `classify-local-corrections` uses the source record's count and caller-recorded eligibility. A positive count with `pass` permits `record-low-disposition` after reconciling the latest Judge report. Zero candidates, failed or inconclusive eligibility, or a Judge-established nonlocal obligation retain their original rework or evidence route. The record preserves original priorities, source negative criterion rows and consumed ordinals, and separately verifies current completion, zero pending local corrections and the exact permitted delta. Only this current composition and the final original-criteria Judge support advancement. Ordinary Low deferral is unchanged.

Neither a settled correction nor an execution incident consumes a provider ordinal. Incidents follow the shared [review contract](review-contract.md#reviewer-instruction-deviations). Backend failure, missing coverage or compromised evidence still uses its native owner; recovery within existing authority does not need a redundant approval. Prior snapshots keep their original Low-only contract.

Current Task v32, Goal v35 and Validation v34 sources record `review-source-contract` and `review-source-binding`. New Mulgae roots use `mulgae-live-source-v1`; existing captured results use `mulgae-historical-capture`; other routes and the closeout substitute use `not-applicable`. Bind identity, native consistency, receipt and caller source-consistency observation in runtime evidence, preserving unavailable facts explicitly. These records do not prove an atomic source view. A prior snapshot lacking the required evidence or direction stays unchanged and needs a separately authorized compatible successor before that checkpoint.
