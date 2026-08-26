# Release Gate Convergence

Read this reference after release QA has passed and before executing a repository full release gate. It governs efficient diagnosis after a gate failure without weakening the repository's aggregate command or binding prior QA evidence to a candidate it did not directly assess.

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

When a candidate correction commit is required, first restore only the applied release metadata to the exact release-basis state, including the open `Unreleased` heading, without changing settled entry text. Then collect the verified candidate corrections from one suffix cycle into one exact reviewed commit after the suffix reaches the end. Include required regression coverage and any release-note entry whose shipped outcome changed. Obtain the normal exact diff, release-note decision, and `$aquarium:task-commit` authority through its direct-commit flow, not a release-handler commit handoff operation; do not amend an earlier correction commit or hide functional work in the `[REL]` commit.

Repository-authorized release metadata remains outside that correction commit: published version, pinned validation expectation, the release heading's date transition, and deterministic release links. A correction limited to that allowlist may remain in the later metadata-only `[REL]` commit when entry text is unchanged.

A correction to product or runtime code, skills, Procedures, public documentation, Design Gates, release-note entry text, dependencies or locks, build, packaging, installation, or release contracts changes QA scope. It requires a new full release-qa pass because a release-gate finding is not a finding from the previous release-qa pass and cannot enter its confirmation exception. Stop after the correction commit and obtain explicit authority for that new pass; the original handler invocation cannot start it automatically.

## Reuse QA Once for a Neutral Direct Child

The handler may reuse one prior release-qa `PASS` for exactly one direct-child correction commit only when every condition below is proven and the user approves the exact diff and equivalence decision:

- the prior PASS candidate SHA, retained evidence root, and complete frozen scenario record are available;
- the current clean candidate is the direct child of that PASS candidate, and this is the first QA-reuse attempt for that evidence;
- repository authority proves every changed surface is non-distributed test-harness or internal support material;
- no changed path or semantic contract participates in a retained scenario's source, procedure, command, input, expected result, Design Gate, or release-delta inspection;
- tests are not removed, skipped, weakened, or relaxed, and no product expectation changes; and
- no candidate surface listed as QA-affecting above changes.

Diff size, commit title, file location alone, formatting claims, or a successful focused check cannot establish equivalence. Missing evidence, an ambiguous classification, a candidate that is not the direct child, or a second correction commit requires a new full release-qa pass.

Record the prior release-qa result against its actual SHA and record the current SHA separately as an approved QA-neutral release-basis candidate. Never claim that release QA directly passed the direct child. Re-establish the release from live Git and hosting state on handler restart; retained evidence grants no test, commit, push, tag, or publication authority.

For publication, bind the metadata-only release commit and final gate evidence to the release-basis candidate while retaining the distinct direct-QA evidence SHA. Supply both through the v3 publication observation. Publication recovery is `unproven` when either binding or the one-attempt equivalence fact is unavailable.

After a QA-neutral reuse, any further candidate commit requires new full release QA. A metadata-only correction may still use the existing release-basis candidate, but the complete final gate must pass again from the beginning.

## Prove the Final Gate

After the corrected release-basis candidate has direct QA or one approved QA-neutral binding, reapply only the previously authorized release metadata and run the complete authoritative release gate from its first command. Require every pass condition in one uninterrupted run and compare tracked state before and after.

Any candidate edit, unexpected tracked mutation, missing command, or new failure discards that full-run evidence and begins a new bounded cycle from the observed failure. Publication remains blocked until one complete run passes without changing the candidate.

## Report

Return the frozen checkpoint inventory and pass conditions, initial aggregate result, each failure and suffix range, corrections, tracked-state comparisons, correction commit and release-note decision, direct-QA SHA and result, QA-reuse classification and approval, release-basis SHA, final uninterrupted aggregate result, and remaining gaps.
