# Release QA Confirmation Integrity Work Dossier

## Authority

**Roadmap epic:** `EPIC-011`

This dossier is the detailed execution source of truth for `EPIC-011` and `TASK-038` through `TASK-040`. The [canonical roadmap](../roadmap/README.md) alone owns their identities, ordering, dependencies, lifecycle vocabulary, and status. Checklist state here is review evidence only.

The shipped [release QA skill](../../plugins/aquarium/skills/release-qa/SKILL.md), its confirmation helper, and the [workflow contract](../specs/workflow-contracts.md) own implemented behavior after delivery. This dossier owns the approved work definition until epic closeout promotes durable requirements to those canonical owners.

## Goal

Make the single post-remediation release QA confirmation produce a trustworthy verdict from one immutable, exact, and non-replayable attempt while preserving the existing full-pass and release boundaries.

## User Outcome

A maintainer can tell that a confirmation verdict belongs to the exact frozen full pass and remediated candidate, that every original finding was rerun through its exact scenario, and that neither artifact replacement nor a second submission could change the settled outcome.

## Current Problem

The current helper creates the attempt claim exclusively, but `finish-confirmation` accepts only its path, does not require the returned claim digest, and does not consume the claim after settlement. A caller can therefore submit the same claim more than once.

The prepared reproduction list proves that each finding and scenario identity exists, but it does not require each `finding_id` to retain the exact `scenario_id` recorded for that finding in the frozen full-pass record. A valid finding can be paired with the wrong retained scenario.

The full record, manifest, and final result use replace-capable atomic writes. Rejection is returned as a CLI error but does not freeze a terminal attempt record that proves which exact admitted submission was rejected. These gaps prevent the one-confirmation policy from being an independently auditable integrity boundary.

## Success Criteria

- The frozen full-pass record, confirmation manifest, claim, settlement admission, and terminal attempt result are create-once regular non-symlink files under their validated evidence roots.
- Every artifact is bound to the exact applicable record digest, manifest digest, claim digest, full candidate, remediated candidate, confirmation root, and attempt number.
- The canonical reproduction inventory is derived from the frozen findings and preserves every exact `(finding_id, scenario_id)` pair once.
- Exactly one finish operation can consume a valid claim. Sequential replay and concurrent contenders fail closed without replacing the admitted or terminal record.
- Once an exact claim is admitted for settlement, PASS, FINDINGS, INCOMPLETE, and evidence rejection all terminate and consume the attempt.
- Malformed input that cannot identify and authenticate an exact claim is rejected before consumption. After settlement admission, a changed or new submission cannot produce a trusted verdict; only the identical admitted request with unchanged evidence digests may deterministically finish settlement or read back its immutable terminal record.
- Every failure returns the versioned structured error envelope with a stable diagnostic code and no traceback or partially trusted verdict.
- The valid confirmation path still reruns the complete frozen inventory against one clean exact remediated candidate and returns the existing verdict precedence.

## Non-Goals

- Do not add another confirmation attempt, automatic retry, automatic remediation loop, or operator override.
- Do not change full-pass scenario selection, worker supervision, finding severity, remediation authority, release metadata, publication ordering, or release-mode selection.
- Do not turn same-user files into an authentication or hostile-process security boundary.
- Do not retain compatibility code for disposable v1 confirmation attempts. An in-progress attempt created under the older contract must restart from a new full release QA pass.
- Do not promote runtime evidence into tracked repository evidence.

## Design

### Immutable Artifact Chain

Use create-once writes for all authority-bearing confirmation artifacts. Refuse an existing output path even when its bytes appear identical; idempotent command recovery must inspect and report the existing immutable artifact rather than overwrite it.

Bind the chain by canonical SHA-256 digests:

```text
frozen full record
        |
        v
remediation manifest + exact finding/scenario pairs
        |
        v
claim + exact confirmation root
        |
        v
settlement admission
        |
        v
terminal attempt record: PASS | FINDINGS | INCOMPLETE | REJECTED
```

The finish input supplies the exact claim path and digest. Validation recomputes every upstream digest and candidate identity before admitting settlement.

### Exact Finding Reproduction

Derive a closed mapping from every frozen verified finding to the `scenario_id` stored on that finding. Preparation rejects missing, duplicate, additional, or differently paired entries. Finish revalidates the same ordered canonical mapping and requires every referenced scenario in the fresh cluster inventory.

A fresh scenario may resolve its original finding and therefore need not emit that finding again. The integrity rule binds what was rerun, not an expectation that the defect remains.

### One-Shot Settlement

Use a create-once settlement-admission artifact keyed by the exact claim. It freezes the canonical finish-request digest and the submitted evidence inventory and digests. Exactly one finisher can create it. After admission, validate that frozen submission and write one create-once terminal attempt record:

- `PASS` when coverage is complete and no finding or gap remains;
- `FINDINGS` when coverage is complete and a verified finding remains;
- `INCOMPLETE` when an otherwise valid submitted scenario reports a gap;
- `REJECTED` when the admitted evidence or identity is inconsistent.

A rejected attempt consumes the claim. A corrected or otherwise changed resubmission is replay and must not become trusted. An exact retry of the already admitted request may only finish deterministic validation of the same frozen bytes or return the existing terminal record; it cannot admit another attempt. Concurrent execution must converge on the same immutable admission and terminal result.

If execution stops after admission but before a terminal record is written, later inspection reports an incomplete consumed attempt. Recovery accepts only the exact admitted request with unchanged evidence digests and resumes deterministic settlement without creating another attempt. If those bytes are unavailable or changed, release QA restarts from a new full pass.

### Failure Contract

Use stable structured diagnostics for at least:

- an existing immutable output target;
- a claim path or digest mismatch;
- a missing, duplicate, additional, or differently paired finding reproduction;
- a changed request for an already admitted or settled claim;
- inconsistent fresh inventory or evidence;
- an admitted attempt without a terminal record.

No rejected path may emit a success schema, trusted verdict, Python traceback, or replace an earlier artifact.

## Migration and Rollout

Introduce new versioned confirmation schemas where the closed shape changes. Do not reinterpret or upgrade existing runtime evidence in place. A release QA invocation that has not entered confirmation remains unaffected; an older prepared or started confirmation must be abandoned and restarted with a new full pass.

Ship the hardened contract before the next release QA confirmation. The change does not by itself authorize a release, candidate commit, or publication.

## Task Ownership

### TASK-038: Freeze Exact Confirmation Identity

- [ ] Replace overwrite-capable authority outputs with create-once writes and explicit existing-target diagnostics.
- [ ] Bind the manifest and claim to exact upstream digests, candidate identities, evidence roots, and attempt number.
- [ ] Derive and enforce the canonical exact finding-to-scenario mapping.
- [ ] Version changed schemas and update focused preparation and begin coverage.

### TASK-039: Enforce One-Shot Confirmation Settlement

- [ ] Atomically admit one finish operation for the exact claim.
- [ ] Persist one immutable PASS, FINDINGS, INCOMPLETE, or REJECTED terminal attempt record.
- [ ] Consume claims on every admitted outcome, converge exact-request recovery, and reject changed replay or divergent concurrent settlement.
- [ ] Fail closed on interrupted settlement while allowing only exact-input deterministic recovery or readback of an already written terminal record.
- [ ] Return stable structured diagnostics for every rejection boundary.

### TASK-040: Qualify Confirmation Integrity

- [ ] Exercise the valid end-to-end confirmation path with exact artifact and digest assertions.
- [ ] Cover record, manifest, claim, admission, and result replacement attempts.
- [ ] Cover empty, oversized, wrong-type, missing, duplicate, additional, and boundary-value fields for every changed schema; run the complete matrix twice consecutively offline and assert identical structured pre-admission rejection, artifact state, no claim consumption when exact identity cannot be established, and no traceback.
- [ ] Cover wrong finding-scenario pairing, sequential replay, concurrent finish, and rejected-then-corrected replay.
- [ ] Synchronize concurrency cases with deterministic barriers rather than timing sleeps, enumerate both contender orderings, run the focused concurrency command twice consecutively offline, and require the same admission and terminal bytes in every run.
- [ ] Interrupt deterministically before admission, after admission, during exact-request recovery, and after terminal creation; exercise every boundary twice and assert respectively no admission, one consumed admission, deterministic convergence, or immutable terminal readback.
- [ ] Verify clean exact-candidate enforcement, verdict precedence, structured output, permissions, and source-worktree preservation.
- [ ] Align the release QA skill, workflow contract, test authority, and release notes when user-visible behavior warrants an entry.
- [ ] Run focused checks, `git --no-pager diff --check`, and the broader repository gate justified by the final changed surface.

## Epic Acceptance

- [ ] `TASK-038` through `TASK-040` are `Completed` in the canonical roadmap.
- [ ] One exact claim admits no more than one settlement and has one immutable terminal or visibly incomplete attempt record.
- [ ] Every original finding is bound to its exact frozen scenario throughout preparation and settlement.
- [ ] Replacement, replay, concurrency, mismatch, rejection, and interruption scenarios fail closed with stable structured diagnostics.
- [ ] The valid confirmation path and unchanged full-pass path pass their applicable regression and repository-standard checks.
- [ ] Durable behavior is promoted to canonical release QA and workflow documentation, this epic links those `Canonical Outcomes`, and this temporary dossier is removed under the documented closeout lifecycle.
