# Review Finding Disposition

Use this contract whenever Aquarium consumes findings from Mulgae or Orca Review, and with the dormant Independent Review contract if that route is re-enabled. Read [review-intent-contract.md](review-intent-contract.md) when the review carries change or completion intent. A provider finding is an advisory hypothesis. The coordinator checks it against the exact reviewed target, repository authority, production callers, persistence and concurrency boundaries, and existing tests before deciding what it means or what happens next.

## Adjudicate before acting

For every finding, preserve the provider's reported severity and independently record:

- validity as `Valid`, `Invalid`, or `Needs confirmation`;
- effective priority as `Blocker`, `Critical`, `High`, `Medium`, or `Low`;
- the current requirement owner and affected repository-relative paths;
- the disposition and the authority required for it.

The effective priority, not the provider label, controls remediation. A finding that affects current correctness, acceptance criteria, security, privacy, public API behavior, schema, migration, persistence, lifecycle safety, or required evidence is at least `Medium`. Invalid findings require no remediation. `Needs confirmation` is a temporary state that cannot support a clean verdict or a downstream review decision. Resolve it to `Valid` or `Invalid` from existing authorized evidence when possible. A standalone review may use only read-only evidence already available under its contract; an approved task or epic envelope may gather missing evidence only when its existing check authority covers that work. Otherwise leave the decision unset, report the missing evidence, and obtain bounded confirmation authority. After gathering the evidence, update the same adjudication record through the owning review action and evaluate the decision again. This confirmation step does not consume a provider-review round unless the provider review itself runs again.

## Apply the authority envelope

A standalone `$aquarium:independent-review`, direct `$aquarium:task-review`, or standalone `$aquarium:orca-review` is report-only. It does not edit source files, run checks, stage changes, commit, or start another provider review. Reviewer-owned output follows the selected backend's contract. Report adjudicated findings and the exact bounded continuation that would authorize remediation.

An approved `$aquarium:task-handler`, `$aquarium:epic-handler`, or `$aquarium:epic-validator` execution envelope authorizes finding remediation only inside its existing work-unit, repository, behavior, check, staging, and review budget. Within that envelope, remediate without another user prompt and report the correction afterward. Stop first when a finding needs a product or authority choice, adds a requirement, expands scope or repository ownership, creates a new file not covered by the plan, requires a destructive or external action, cannot be isolated safely, or exceeds the remaining review budget.

Confirmation-only review authority covers adjudication, reporting, and eligible local `Low` handling. It does not include another provider-review round. A valid `Medium` or higher finding therefore requires a new bounded remediation-and-review authorization when no approved round remains. Do not accept its risk, defer it, or claim completion.

## Remediate by effective priority

A valid `Blocker`, `Critical`, `High`, or `Medium` finding must be fixed, verified with every affected authorized check, and reviewed again on the corrected complete target. Keep the same backend, reviewer, focus, and user-facing source scope where feasible. Independent Review and Mulgae create fresh native captures. Orca reads the corrected live target. Native storage and transport remain backend-owned; no digest equivalence across backends is required.

Classify a valid `Low` finding into exactly one disposition:

1. `low-self-evident-fix`: Documentation-only or self-evident non-behavioral correction. Apply it, read it back, run required documentation checks and `git --no-pager diff --check`, then continue without product tests or another provider review.
2. `low-bounded-fix`: Small behavioral correction that needs proof. Apply it and run a focused deterministic test plus required integrity checks, then continue without another provider review.
3. `low-deferred-feedback`: Small independent future risk that does not affect current correctness or acceptance. Add it to the repository's canonical deferred-feedback owner with impact or reason and a concrete re-entry condition, then continue.
4. `low-todo-candidate`: Structural or epic-sized future work. Add a candidate to the canonical TODO owner. Roadmap adoption and a roadmap ID require separate authorization.

If no canonical deferred-feedback or TODO owner exists, report the proposed entry and obtain approval before creating one. Never use a Low disposition to postpone work required for current correctness or acceptance; reprioritize that finding to at least `Medium`.

## Settle one finite Low set

Keep the source review facts separate from settlement state. Preserve the native
original root or direct-audit basis, effective result identity, reviewed target,
source finding IDs, and reported severities. Freeze the complete admitted set of
eligible Low findings for the current work-unit and goal revision. Track effective
priority, disposition, pending disposition count, current blocker count, final
target, local verification, and coverage relationship independently. Historical
Low counts never decrease merely because their required work is complete.

Enter Low settlement only after the native invocation and finding query are
complete, required coverage and publication evidence is available, CI and required
verification pass, no finding needs confirmation, and no current blocker or
effective Medium-or-higher finding remains. Bind each provider finding by original
root, effective result, and source finding ID; retain separate namespaces for
direct-audit findings. Do not collapse findings because their prose is similar.

Settlement completes only when every frozen finding has exactly one supported
disposition, every required local check passes on the actual final target, the
pending disposition and current blocker counts are zero, and the reviewed basis
plus exact permitted delta accounts for the final target. A failed or inconclusive
local check, unavailable owner, changed requirement, unrelated delta, or repeated
unchanged disposition is a specific incomplete state. Route it to its owner or
wait; do not start another review to create a cleaner report.

The complete Low-settlement composition carries the exact reviewed or audited
basis and its native identities, the frozen eligible finding IDs and supported
dispositions, before and after target identities, the exact permitted Low-only
delta, required local check identities and current outcomes, zero pending
dispositions and current blockers, and the coverage relationship. A handoff must
carry that composition or state explicitly that no accepted Low-only delta applies.
Invalid findings retain their adjudication but do not require a Low remediation
disposition.

Before dispatching a new provider root or broad source audit, reconstruct the work
unit, goal revision, candidate, previous result and original-root lineage, pending
invocation, remaining review authority, and independent reason for the pass. Do not
dispatch when the only reason is eligible Low settlement, a completed Low
disposition, or the permitted Low-only target delta. Resume an exact pending native
invocation through its owning skill. Review budgets are maxima, not rounds that
must be consumed. Preserve a required first review and a confirmation already owed
after a Medium-or-higher correction. A goal revision or context label alone does
not reset consumed review authority. Only an explicitly approved new goal scope or
bounded additional pass creates new authority, with prior lineage preserved.

## Preserve candidate and staging integrity

Any correction makes prior verification for affected behavior stale. Run the checks required by the disposition. When no provider re-review is required, record that the preceding review predates the corrected bytes and do not call the correction review-covered.

The accepted final target may contain only the reviewed basis, the exact authorized
and locally verified Low-only delta, an already-authorized lifecycle-only delta,
and an independently validated promoted-evidence projection when required. Reject
stale, ambiguous, failed, or additional changes instead of broadening the Low
exception.

For a staged target, an approved remediation envelope includes modifying and exactly restaging already staged affected paths. Do not add a previously unstaged correction path, disturb unrelated index entries, or commit. A canonical deferred-feedback or TODO owner required by a Low disposition is separate post-review disposition output: add and stage that owner only when the remediation envelope already covers it, report it outside the reviewed target, and record that the review predates it; otherwise obtain authority first. Verify the resulting staged candidate and its separation from unrelated work. For `head`, `commit`, or `range`, never alter the original Git objects; create a separately authorized corrected candidate representation or stop when the workflow has no such authority. Never switch backend or source scope silently.

## Report the outcome

Return counts by reported severity, effective priority, validity, and disposition. For each valid or confirmation-needed finding, include its source ID, reported severity, effective priority, exact path, owner, disposition, verification state, whether the last provider review predates the current bytes, and any missing authority. A technical `APPROVE` requires no unresolved valid or confirmation-needed finding and an authoritative backend lifecycle result. Completion additionally requires the separate criterion assessment defined by the review-intent contract; neither result substitutes for the other.
