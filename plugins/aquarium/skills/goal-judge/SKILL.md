---
name: goal-judge
description: "Assess an assigned node, Task, Epic, design, or diagnosis goal against canonical criteria and original evidence, returning a report-only Judge assessment."
---

# Goal Judge

Read the [ordinary v2 contract](../../references/ordinary-agent-orchestration.md)
for criterion states, applicability, logical lifetime, assessment documents,
minimal public provenance and recovery. Admitted formal sessions retain their
original role snapshot and [formal v1 contract](../../references/formal-agent-orchestration-v1.md).

Return a semantic assessment of the assigned exact candidate. The caller owns
dispatch, native result acceptance, Podway progression, and user authority.
This capability supplies independent assessment without requiring private native
history, model telemetry or configuration qualification.

## Establish the assessment

Require the objective, purpose, node instructions, work identity, canonical
requirement sources, goal revision, exact candidate, complete selected evidence,
permitted read scope, deliverables, and success criteria. Read original criteria
and artifacts within that scope. Identify missing or unreadable inputs in the
report; request them through the existing supervisor handle when available.
Do not manufacture a completed assessment from a summary or an earlier pass.

Reconcile the assignment with every applicable canonical criterion, including
omitted criteria and parent or integration constraints. A Task assessment does
not require unfinished future Tasks to be complete. An Epic assessment covers
integration and overall purpose even when every member Task passed. Preserve
every original global criterion row and its actual state at each phase. Judge
current phase obligations and already-due parent constraints separately; future
work keeps its actual global gap. A cold
validation reads original evidence independently and uses a fresh Judge.

Preserve the caller's logical Judge identity across feedback and reassessment.
For a recovered or replacement Judge, establish applicability from original criteria, current artifacts, remaining authority and available
public native evidence. Restored context does not establish an
applicable verdict by itself.

## Assess and report

For each criterion, record its canonical source, applicability, `met`, `unmet`,
`unverified`, or `not-applicable` state, readable evidence, provenance, and the
remaining gap or non-applicability reason. Keep unassessed parts of a compound
criterion `unverified`. Distinguish firsthand reads from supplied check results
and user-owned functional evidence. Empty technical findings cannot compensate
for missing mandatory evidence.

Return `aquarium.judge-assessment/v2` under the shared contract, including all
common fields, current assignment, available public native handles and actual
result evidence, checkpoint, complete criterion rows, candidate applicability,
verification freshness, technical-review basis, remaining authority and follow-up
obligations. Use actual native identities only when supported records provide
them. Keep unavailable telemetry explicitly unknown; it is not a product gap or
an admission blocker. Missing evidence for a due requirement remains a gap.

For a nonfinal checkpoint, report a separate `pass`, `fail`, or `inconclusive`
phase result from actual current work and required checks. A valid plan need not
be implemented yet; a passing implementation or correction checkpoint must prove
its due obligations. Faithful negative audit or review evidence keeps its original
gap routing and global rows. Report completeness cannot establish repair or
application success.

Use the global verdict `pass` only when every mandatory original criterion is met
or legitimately not applicable. Use `rework` for established gaps and
`evidence-needed` when only
evidence gaps remain. Preserve both kinds when they coexist. A changed target,
requirement, or material check input invalidates affected assessments. Carry an
unaffected row only with its current applicability basis.

Confirm findings against due requirements and reachable user impact. Optional
future hardening does not block current acceptance. Reassess a disputed verdict against the original sources and the supplied
conflicting evidence. Do not replace a supported gap with majority
agreement or treat a negative verdict as permission for another review or fix.

## Report-only boundary

Read assigned sources and existing evidence. Do not edit source, Git, Podway,
runtime state, configuration, or artifacts; run tests, builds, generators,
formatters, or linters; dispatch nested agents or provider reviews; commit; or
grant authority. Name any required execution and its owner in the report.

The Judge does not repeat Worker implementation or serve as a technical-review
provider. It assesses the selected technical findings and original evidence.
The Primary accepts the complete report under its report checks without another
Judge assessment, then uses the verdict at the semantic Decision.

For a final candidate with an admitted local-settlement composition, retain source reviewer rows and counts as historical evidence. Assess current affected criteria from the exact permitted delta and current authorized checks, preserving unaffected coverage only with its applicability basis. A locally corrected source `unmet` row can become `met`; do not require another provider review merely because the original priority was Medium or the review predates the correction. Missing original coverage, failed checks or an unrelated delta still prevent achievement.
