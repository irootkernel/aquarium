# Release Gate Convergence

Read this reference after release QA has passed and before executing a repository full release gate. It governs efficient diagnosis after a gate failure without weakening the repository's aggregate command or binding prior QA evidence to a candidate it did not directly assess.

## Delivery and gate order

The Coordinator assigns approved metadata edits and authorized gate commands to
a bounded Executor, consuming its actual diff, candidate identity, command/input/
environment records, original exits and outputs, tracked-state comparisons and
cleanup handoff. Assign an authorized correction to one mutating Executor; retain
its exact edits, focused results and diagnostic suffix evidence. The Coordinator
keeps approvals, `task-commit` handoffs and publication control. Readiness and
rework reports supply no execution, correction or Git authority.

Follow the repository's planned full/light or reduced-patch gate order. Aquarium's
own policy remains gate before commit. For that order, assess the gate-tested
metadata bytes and inputs, then inspect the actual post-hook release commit tree,
sole release-basis parent and authorized metadata-only delta. Bind the gate to
the release commit only when the comparison proves its applicability. Hook changes
invalidate affected evidence; the title or successful commit cannot prove binding.

For commit before gate, the Coordinator commits the approved metadata delta through
the unchanged leaf handoff and inspects the actual clean post-hook result. Record
the later gate as inapplicable to this commit boundary only, globally unverified
and still required before publication. The Executor then runs the authorized gate
on that exact commit. Independent publication readiness must cover the actual
commit, parent, tested bytes and all due results before the first publication
mutation. Keep separate pre-QA, installed, metadata and final distribution bindings.

If that commit-first gate fails, preserve the unpushed local release commit and
report its identity and failure. Diagnostics may continue within authority while
preserving it. Stop before a correction requiring history changes until the user
authorizes disposition of that exact commit. Do not reset, amend, automatically
restore metadata over it or replay publication. The disposition must establish
the resulting candidate and renew affected evidence; it grants no extra QA pass.

## Rebind Pre-QA Evidence

The clean committed candidate after changelog settlement owns pre-QA compatibility evidence and any light-mode test confirmation. Follow the repository policy to determine which gates are required and which exact distributed artifact and environment they must use. A development commit alone does not start a release gate.

A settlement or remediation commit changes that candidate. Before the next QA pass or metadata step, rerun required candidate-bound gates and obtain fresh light confirmation for the new SHA, or explicitly switch to full verification. Carry evidence forward only when repository policy explicitly allows that exact equivalence; a QA-neutral direct-child decision below does not transfer SHA-bound compatibility results or light confirmation. Keep direct-QA evidence, pre-QA gate evidence, and post-metadata release-gate evidence distinct.

## Freeze Public Checkpoints

Read the repository release policy, executable test authority, and `TESTING.md` when enrolled. Before the first gate command, freeze the ordered full-gate inventory and each objective pass condition, including commands whose successful check is an expected rejection rather than exit zero.

A resumable checkpoint must be an independently invocable stage declared by repository authority. The common test contract exposes prepare, unit, integration, and E2E handlers in that order. A distribution aggregate such as `make dist` is divisible only when repository authority names its ordered child targets and guarantees that each is independently invocable. Never split recipe lines, infer checkpoints from output, treat `make -n` as authority, or reconstruct shell state.

When no safe checkpoint exists, the aggregate itself is the only checkpoint. A change to the frozen gate commands, stage topology, pass conditions, or an earlier stage's outputs invalidates all suffix progress.

Show the aggregate commands and every possible suffix command before execution and obtain explicit authority for the bounded convergence cycle. Authority that named only one invocation does not authorize suffix or final reruns, and no execution authority survives a new handler invocation. A failed final aggregate ends the authorized cycle; obtain fresh explicit authority for the new bounded cycle before running any suffix or aggregate command again.

## Diagnose From the Failure

Run the authoritative aggregate first. When checkpoint `i` fails, establish whether the failure is a candidate defect, release-metadata defect, missing prerequisite, environment limitation, or evidence gap. Do not edit source, change an environment, install a dependency, or broaden authority merely to keep the gate moving.

After an authorized correction, rerun checkpoint `i` and every later frozen checkpoint in order. If checkpoint `j` then fails, correct it and rerun `j` through the end. A completed suffix is diagnostic evidence that the current failure frontier reached the end; it is never release-gate `PASS` evidence.

Once a suffix reaches the end, determine whether its corrections require a candidate commit. When they do, settle and bind that candidate under the sections below before the final aggregate. When no candidate commit is required, proceed directly to the final aggregate. A completed suffix never authorizes release or publication by itself.

## Settle One Correction Commit

When a candidate correction commit is required and release metadata is still
uncommitted under gate-before-commit policy, have the authorized Executor restore
only that metadata to the exact release-basis state, including the open
`Unreleased` heading, without changing settled entry text. The commit-first stop
above takes precedence when a release commit already exists. Collect the verified
corrections from one suffix cycle into one exact reviewed commit after the suffix
reaches the end. Include required regression coverage and any release-note entry
whose shipped outcome changed. Obtain the normal exact diff, release-note decision
and `$aquarium:task-commit` authority through its direct-commit flow, not a
release-handler commit handoff operation; do not amend an earlier correction
commit or hide functional work in the release commit.

Repository-authorized release metadata remains outside that correction commit: published version, pinned validation expectation, the release heading's date transition, and deterministic release links. A correction limited to that allowlist may remain in the later metadata-only release commit when entry text is unchanged.

A correction to product or runtime code, skills, Procedures, public documentation, Design Gates, release-note entry text, dependencies or locks, build, packaging, installation, or release contracts changes QA scope. It requires a new full release-qa pass because a release-gate finding is not a finding from the previous release-qa pass and cannot enter its confirmation exception. Stop after the correction commit and obtain explicit authority for that new pass; the original handler invocation cannot start it automatically.

## Reuse QA Once for a Neutral Direct Child

The handler may reuse one prior release-qa `PASS` for exactly one direct-child correction commit only when every condition below is proven and the user approves the exact diff and equivalence decision:

- the prior PASS candidate SHA, retained evidence root, and complete frozen scenario record are available;
- the current clean candidate is the direct child of that PASS candidate, and this is the first QA-reuse attempt for that evidence;
- repository authority proves every changed surface is non-distributed test-harness or internal support material;
- no changed path or semantic contract participates in a retained scenario's source, procedure, command, input, expected result, Design Gate, or release-delta inspection;
- tests are not removed, skipped, weakened, or relaxed, and no product expectation changes; and
- no candidate surface listed as QA-affecting above changes.

Before the Coordinator seeks that exact equivalence approval, the independent
Evaluator assesses all six conditions against the original PASS/frozen record,
exact clean direct-child diff, distribution authority, affected scenario inputs
and first-and-only reuse fact. Return eligibility as a nonfinal checkpoint within
publication readiness. A negative or inconclusive result stops the dependent
equivalence request; a passing eligibility result supplies neither actual approval
nor final readiness. Keep all remaining global obligations in their actual state.

Diff size, commit title, file location alone, formatting claims, or a successful focused check cannot establish equivalence. Missing evidence, an ambiguous classification, a candidate that is not the direct child, or a second correction commit requires a new full release-qa pass.

Record the prior release-qa result against its actual SHA and record the current SHA separately as an approved QA-neutral release-basis candidate. Never claim that release QA directly passed the direct child. Re-establish the release from live Git and hosting state on handler restart; retained evidence grants no test, commit, push, tag, or publication authority.

For publication, bind the metadata-only release commit and final gate evidence to the release-basis candidate while retaining the distinct direct-QA evidence SHA. Supply both through the v5 publication observation. Publication recovery is `unproven` when either binding or the one-attempt equivalence fact is unavailable.

After a QA-neutral reuse, any further candidate commit requires new full release QA. A metadata-only correction may still use the existing release-basis candidate, but the complete final gate must pass again from the beginning.

## Prove the Final Gate

After the corrected release-basis candidate has direct QA or one approved QA-neutral
binding, apply only the previously authorized metadata and follow the selected
order above: for gate-before-commit, run on those identified bytes before the
release commit; for commit-before-gate, run on the actual clean release commit
after any required authorized disposition and preparation. Require every pass
condition in one uninterrupted authoritative gate from its first command, comparing tracked
state before and after. Complete applicable independent publication readiness
with the actual post-hook binding and every other due obligation.

Any candidate edit, unexpected tracked mutation, missing command, or new failure discards that full-run evidence and begins a new bounded cycle from the observed failure. Publication remains blocked until one complete run passes without changing the candidate.

## Report

Return the frozen checkpoint inventory and pass conditions, initial aggregate result, each failure and suffix range, corrections, tracked-state comparisons, correction commit and release-note decision, direct-QA SHA and result, QA-reuse classification and approval, release-basis SHA, final uninterrupted aggregate result, and remaining gaps.

Retain Executor deliveries, policy order, actual release commit/tree/parent/delta,
tested-byte/input binding, independent eligibility and final readiness evidence,
any failed commit-first disposition stop and remaining grants. Diagnostic suffixes
and unchanged bookkeeping add no Evaluator cycle.
