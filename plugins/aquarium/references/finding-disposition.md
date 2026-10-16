# Review Finding Disposition

Use this contract whenever Aquarium consumes findings from Mulgae Review, Herdr Review, Independent Review, or a workflow review waiver. Read [review-intent-contract.md](review-intent-contract.md) when the review carries change or completion intent and [review-routing-contract.md](review-routing-contract.md) when an embedded workflow selects or changes routes. A reviewer or coordinator finding is an advisory hypothesis. The coordinator checks it against the exact reviewed target, repository authority, production callers, persistence and concurrency boundaries, and existing tests before deciding what it means or what happens next.

## Adjudicate before acting

Apply [review strategies](review-strategy-contract.md): establish the applicable
due requirement and concrete impact before assigning blocker status. Preserve
a valid defect when rejecting an excessive remedy; seek a goal-preserving
correction. Optional hardening and preferences do not create completion gaps.

For every finding, preserve the provider's reported severity and independently record:

- validity as `Valid`, `Invalid`, or `Needs confirmation`;
- effective priority as `Blocker`, `Critical`, `High`, `Medium`, or `Low`;
- the current requirement owner and affected repository-relative paths;
- the disposition and the authority required for it.

Record acceptance, partial acceptance or rejection with reasons and evidence,
the actual correction and checks, remaining disagreement and effect on the
original goal. Carry the response with source finding IDs into the next
authorized Review Brief under [review intent](review-intent-contract.md).

Effective priority records impact; it does not by itself require another review. A valid finding with an established effect on current correctness, acceptance criteria, security, privacy, public API behavior, schema, migration, persistence, lifecycle safety, or required evidence is at least `Medium`. Preserve that priority when its correction qualifies for local settlement below. Invalid findings require no remediation. `Needs confirmation` cannot support completion. Resolve it from existing authorized evidence or checks covered by the owning execution envelope. Otherwise report the exact missing evidence and authority. Confirmation consumes no provider-review round unless the provider review itself runs again.

## Apply the authority envelope

An explicitly selected `$aquarium:independent-review` route uses three fresh base reviewers and, for UI-related work, one UI/UX specialist for one report-only operation. A direct `$aquarium:task-review`, standalone `$aquarium:mulgae-review`, standalone `$aquarium:herdr-review`, or standalone `$aquarium:independent-review` is report-only. It does not edit source files, run checks, stage changes, commit, or start another provider review. Reviewer-owned output follows the selected backend's contract. Report adjudicated findings and the exact bounded continuation that would authorize remediation.

An approved `$aquarium:task-handler`, `$aquarium:epic-handler`, or `$aquarium:epic-validator` execution envelope covers in-scope local corrections, affected checks and authorized staging without another user prompt. Report the correction afterward. A necessary provider reassessment uses the same selected route and remaining approved review budget automatically. Changing routes never erases findings or resets that budget. Stop only for effects outside the envelope, a new product or authority choice, unsafe isolation, or a necessary provider reassessment with no remaining grant. Name the uncovered effect or exhausted grant instead of asking for a generic re-review approval.

Confirmation-only authority includes eligible local correction and ordinary Low settlement within the existing effect boundary. Neither consumes another provider ordinal. A finding that needs further independent judgment requires bounded remediation-and-review authority when no approved round remains. Do not accept or defer a current defect.

## Decide whether a correction needs another review

Use `local-verified-fix` when the correction restores an already approved requirement, has an isolated and understood effect, and authorized direct verification can establish the result. Documentation corrections, including an unambiguous missing detail, must follow their existing authority. A simple behavioral correction needs a focused deterministic regression test. File type, diff size and the word "obvious" alone do not establish eligibility.

Read back non-behavioral corrections and run required documentation and integrity checks. Behavioral corrections require a test of the affected behavior and relevant failure paths, plus every affected required check. Reassess invalidated criteria against the final bytes; carry unaffected rows only with a current applicability basis. A previously `unmet` criterion may become `met` through this evidence without another provider operation. A covered local check may resolve an `unverified` row, but missing reviewer coverage, unread original authority or an incomplete operation cannot be replaced by coordinator assertions.

Another review is required when the correction needs a new design, contract, security, privacy, data-integrity, migration or concurrency judgment, or direct verification cannot establish its effect. Keep corrections requiring that judgment in the existing rework path. A mixed issue set uses local settlement only when every current blocking obligation can be resolved locally. Otherwise remediate within existing authority and review the affected surface under the applicable assessment kind.

For an admitted completed review, record `local-correction-count` and the caller-recorded `local-correction-eligibility` result. `pass` binds the finite correction set, original requirements, source findings and negative criterion rows, exact target, all current blocking obligations, required checks and available effect authority. `fail` retains the original rework, evidence or incomplete route; `inconclusive` means the local basis is unproven. Zero candidates take the ordinary path. These source fields are provisional: reconcile them with the latest retained Judge report at classification. A source pass never forces local selection when that report establishes a new nonlocal obligation. For a positive candidate count, ordinary routing remains selectable when the latest Judge establishes an obligation outside local eligibility. These fields neither authenticate authority nor attest to tests.

Current Task, Goal and Validation snapshots use `classify-local-corrections` before provider-rework authority. Eligible corrections reuse `record-low-disposition`; its retained name does not classify a Medium finding as Low. Preserve `pending-low-dispositions` for actual Low obligations and record `pending-local-corrections` separately. Record each local correction, exact delta and check in the settlement summary, and use `review-predates-local-correction` when applicable. Local verification records its own check axis; current blockers and criterion gaps have explicit owner routes even when dispositions are complete. Validation separately records and gates current missing mandatory evidence prerequisites. The final required Judge assesses the corrected candidate and every original applicable criterion. Local settlement removes neither that assessment nor actual final user acceptance.

## Remediate by effective priority

A valid `Blocker`, `Critical`, `High`, or `Medium` finding must be corrected and verified. Settle an eligible `local-verified-fix` without another provider review. Otherwise assess the corrected target again using the same route, reviewer configuration, purpose and approved source scope. Native storage, transport and mandatory backend checks remain backend-owned; a local correction cannot turn a failing native CI result into a passing result.

Classify a valid `Low` finding into exactly one disposition:

1. `low-self-evident-fix`: Documentation-only or self-evident non-behavioral correction. Apply it, read it back, run required documentation checks and `git --no-pager diff --check`, then continue without product tests or another provider review.
2. `low-bounded-fix`: Small behavioral correction that needs proof. Apply it and run a focused deterministic test plus required integrity checks, then continue without another provider review.
3. `low-deferred-feedback`: Small independent future risk that does not affect current correctness or acceptance. Add it to the repository's canonical deferred-feedback owner with impact or reason and a concrete re-entry condition, then continue.
4. `low-todo-candidate`: Structural or epic-sized future work. Add a candidate to the canonical TODO owner. Roadmap adoption and a roadmap ID require separate authorization.

If no canonical deferred-feedback or TODO owner exists, report the proposed entry and obtain approval before creating one. Never use a Low disposition to postpone work required for current correctness or acceptance; reprioritize that finding to at least `Medium`.

## Settle one finite Low set

Keep the source review facts separate from settlement state. Preserve the
selected route, authoritative completed operation or waiver assessment, review
evidence reference, reviewed target, finding identities and provenance, and
reported severities. Mulgae additionally preserves its original root and
effective result identity. Freeze the complete admitted set of eligible Low
findings for the current work-unit and goal revision. Track effective priority,
disposition, pending disposition count, current blocker count, final target,
local verification, and coverage relationship independently. Historical Low
counts never decrease merely because their required work is complete.

Enter ordinary Low settlement only after the selected route has an authoritative
completed operation or waiver assessment under the workflow review routing
contract, every route-specific prerequisite is satisfied, required workflow
verification passes, no finding needs confirmation, and no current blocker or
effective Medium-or-higher finding remains. Mulgae additionally requires its
complete findings query, coverage, committed publication, and CI evidence. The
admitted completion assessment must also have zero `unmet` and zero `unverified`
criteria. Bind each finding by route, review evidence reference, source identity,
and reviewer or coordinator provenance. Retain separate namespaces for direct
audit findings and waiver-assessment findings. Do not collapse findings because
their prose is similar.

Settlement completes only when every frozen finding has exactly one supported
disposition, every required local check passes on the actual final target, the
pending Low disposition, local correction and current blocker counts are zero, and the reviewed basis
plus exact permitted delta accounts for the final target. The settlement record
must carry the criterion-level completion summary and its zero unmet and unverified
counts; it may not depend on a parallel source record that could later diverge. A failed or inconclusive
local check, unavailable owner, changed requirement, unrelated delta, or repeated
unchanged disposition is a specific incomplete state. Route it to its owner or
wait; do not start another review to create a cleaner report.

The complete local-settlement composition, including ordinary Low settlement, carries the selected route, exact
reviewed, waived, or audited basis and its authoritative evidence reference,
route-specific native identities when applicable, finding provenance, the frozen
eligible finding IDs, original effective priorities and supported dispositions,
before and after target identities, the exact permitted local delta, required
local checks and current outcomes, zero pending Low dispositions, local corrections
and current blockers, the current completion summary with zero unmet and unverified
counts, and the coverage relationship. A handoff must carry that composition or state explicitly that no
accepted local delta applies. Preserve the source review's original criterion rows separately from the current settlement assessment. The local path may resolve affected criteria in the current settlement assessment; ordinary Low-only settlement carries unaffected source rows unchanged.
Invalid findings retain their adjudication but do not require a Low remediation
disposition.

Before dispatching a new provider operation, reconstruct the work unit, goal
revision, assessment kind, candidate, previous result and original-root lineage,
pending invocation, remaining review authority, and independent reason for the
pass. Do not dispatch or request approval when the only reason is eligible local settlement, a completed
disposition, or its verified target delta. Resume an exact pending
native invocation through its owning skill. Review budgets are maxima, not rounds
that must be consumed. The first three completed assessments may evaluate the exact
named work unit. Ordinal four and later assess only the frozen correction set and
its direct regression surface. A goal revision or context label alone does not
reset consumed review authority. Only an explicitly approved new goal scope or
one bounded additional remediation confirmation creates authority, with prior
lineage preserved.

## Preserve candidate and staging integrity

Any correction makes prior verification for affected behavior stale. Run the checks required by the disposition. When no provider re-review is required, record that the preceding review predates the corrected bytes and do not call the correction review-covered.

The accepted final target may contain only the reviewed basis, the exact authorized
and locally verified settlement delta, an already-authorized lifecycle-only delta,
and an independently validated promoted-evidence projection when required. Reject
stale, ambiguous, failed, or additional changes instead of broadening the local
settlement boundary.

For a staged target, an approved remediation envelope includes modifying and exactly restaging already staged affected paths. Do not add a previously unstaged correction path, disturb unrelated index entries, or commit. A canonical deferred-feedback or TODO owner required by a Low disposition is separate post-review disposition output: add and stage that owner only when the remediation envelope already covers it, report it outside the reviewed target, and record that the review predates it; otherwise obtain authority first. Verify the resulting staged candidate and its separation from unrelated work. For `head`, `commit`, or `range`, never alter the original Git objects; create a separately authorized corrected candidate representation or stop when the workflow has no such authority. Never switch backend or source scope silently.

## Report the outcome

Return counts by reported severity, effective priority, validity, and disposition. For each valid or confirmation-needed finding, include its source ID and exact path when the producer supplies them, reported severity, effective priority, owner, disposition, verification state, whether the last provider review predates the current bytes, and any missing authority. For omitted implementation, preserve the requirement identity, expected location, and inspected absence evidence instead of fabricating a producer ID or path. A technical `APPROVE` requires no unresolved valid or confirmation-needed finding and an authoritative backend lifecycle result. Completion additionally requires the separate criterion assessment defined by the review-intent contract; neither result substitutes for the other.
