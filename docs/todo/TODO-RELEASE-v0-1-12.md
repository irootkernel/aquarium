# Aquarium v0.1.12 Release Work Dossier

## Authority

**Roadmap epic:** `EPIC-004`

This dossier is the detailed scope and acceptance source of truth for `EPIC-004` and `TASK-004`. The [canonical roadmap](../roadmap/README.md) alone owns their identities, ordering, dependencies, lifecycle vocabulary, and current status. Checklist marks in this file are review evidence only and never change roadmap state.

The root `CHANGELOG.md` owns cumulative release notes and the open release version. Repository instructions and the release workflow own approval, verification, commit, tag, push, and publication behavior when they are stricter than this dossier.

## Goal and Purpose

Release Aquarium v0.1.12 from the exact candidate produced by the completed Podway v0.2.6 adoption epic after a new complete release-QA pass, the selected local release gate, and exact publication verification.

This work keeps release readiness, distribution state, and network publication separate from the completed development-contract evidence in EPIC-001. A development candidate, consumer-side claim, stale review, or partial publication observation is never release proof.

## Approach

1. Reconcile every material change after v0.1.11 with the open v0.1.12 CHANGELOG section.
2. Establish one clean exact candidate and run a new full release-QA pass without mutating user-global runtime state.
3. Correct every confirmed release blocker through its canonical owner and establish a new candidate when required.
4. Run the complete full release gate, including `PODWAY_BIN=<absolute-path> make test-podway-compat` with the verified official Podway v0.2.6 artifact.
5. Publish `main`, the annotated tag, and the GitHub Release in the required order and verify their exact identities.

## Cross-Cutting Boundaries

- EPIC-001 owns the completed Podway adoption result; EPIC-004 owns Aquarium release readiness and publication.
- Development binaries and branch tests do not satisfy a requirement for an official archive and checksum.
- No step may infer approval for installation, staging, commit, push, tag, publication, or user-global mutation from another effect.
- No step may include unrelated staged, unstaged, untracked, or ignored runtime work.
- A failed or incomplete release-QA pass grants no publication authority and cannot be reused as a passing baseline.

## Known Entry Findings

- Align the release gate convergence guidance with the publication inspector's supported v4 observation schema before establishing the next candidate.
- Reject empty or relative Orca repository identities before path resolution so provider terminals cannot be created from cwd-relative input.
- Treat the prior user-global Codex refresh as an isolation incident only; diagnosis or restoration requires separate explicit authority and is not part of EPIC-004 by default.

## TASK-004: Release Aquarium v0.1.12

### Objective

Prepare, validate, publish, and independently observe the exact Aquarium v0.1.12 release under the repository release policy.

### Do

- [ ] Invoke `$aquarium:release-handler` in `full` mode because the release contains functional runtime and Procedure contract changes.
- [ ] Inspect the worktree, local and remote `main`, exact candidate SHA, existing tag, and existing GitHub Release state.
- [ ] Reconcile every material change since the previous release with the open v0.1.12 CHANGELOG section and obtain approval for substantive entry changes.
- [ ] Resolve and verify every applicable Known Entry Finding through its canonical owner before establishing the release-QA candidate.
- [ ] Commit the exact preparation through the authorized commit workflow and run a new complete release-QA pass against the resulting clean candidate.
- [ ] Execute the complete selected local release gate and preserve its exact evidence.
- [ ] Create the exact `[REL] Release v0.1.12` commit, push `main`, create and push the annotated `v0.1.12` tag, and create the GitHub Release in the required order.
- [ ] Verify remote `main`, the peeled tag, and the GitHub Release resolve to the intended release commit.
- [ ] Treat opening the next empty Unreleased cycle as a separate non-release action requiring separate approval.

### Do Not

- [ ] Do not include unrelated work or proceed from an ambiguous or dirty release candidate.
- [ ] Do not reuse release QA after substantive release-note text or functional candidate content changes.
- [ ] Do not publish a tag before the intended release commit is settled on remote `main`.
- [ ] Do not rewrite or delete a published tag without explicit authorization.
- [ ] Do not touch user-global Codex or Ouroboros state during release QA.
- [ ] Do not treat local release completion as authorization to open or publish the next release cycle.

## Epic Acceptance

- [ ] `TASK-004` is `Completed` in the canonical roadmap.
- [ ] A new complete release-QA pass succeeds against the exact settled candidate.
- [ ] The full local release gate succeeds, including official Podway v0.2.6 artifact compatibility.
- [ ] The published v0.1.12 commit, peeled tag, and GitHub Release identity agree.
- [ ] Remaining independent work is recorded only in its proper roadmap, TODO, or deferred-feedback owner.
