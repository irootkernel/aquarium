# Aquarium v0.1.12 Release Work Dossier

## Authority

This dossier is the detailed scope and acceptance source of truth for `EPIC-001` and `TASK-001` through `TASK-004`. The [canonical roadmap](../roadmap/README.md) alone owns their identities, ordering, dependencies, lifecycle vocabulary, and current status. Checklist marks in this file are review evidence only and never change roadmap state.

The root `CHANGELOG.md` owns cumulative release notes and the open release version. Repository instructions and the release workflow own approval, verification, commit, tag, push, and publication behavior when they are stricter than this dossier.

## Goal and Purpose

Release Aquarium v0.1.12 from one exact candidate after completing the project-owned Procedure contract, independently qualifying Podway v0.2.6, reconciling Aquarium-owned integration requirements, and verifying the published commit, tag, and GitHub Release.

This work exists to prevent a development-branch result, consumer-side claim, stale review, or partial publication observation from being promoted to release proof.

## Approach

1. Establish the project-owned Procedure boundary without weakening Aquarium-managed canonical validation.
2. Obtain Podway's exact independently released v0.2.6 artifact and verify Aquarium compatibility against it.
3. Reconcile all material Aquarium-owned integration requirements and validate the final exact candidate.
4. Execute the selected release mode and verify every publication surface resolves to the intended release commit.

## Cross-Cutting Boundaries

- Aquarium does not implement, tag, publish, or rewrite Podway-owned release work.
- Development binaries and branch tests do not satisfy a requirement for an official archive and checksum.
- No task may infer approval for another effect such as installation, staging, commit, push, tag, or publication.
- No task may include unrelated staged, unstaged, untracked, or ignored runtime work.
- A task result does not advance roadmap state until the owning workflow records accepted evidence through the roadmap authority.

## TASK-001: Support Project-Owned Procedure Customization

### Objective

Provide an explicit and separately approved transition from Aquarium-managed canonical Procedure bytes to project-owned compatible customization while retaining a safe upstream-update path.

### Do

- [ ] Preserve exact byte equality as the rule for Aquarium-managed canonical Procedure files.
- [ ] Require an explicit ownership transition; never infer project ownership from an arbitrary mismatch.
- [ ] Record non-secret source provenance and the current digest for project-owned Procedure content.
- [ ] Validate required nodes, item types, routes, evidence handoffs, lifecycle ownership, and terminal behavior for the selected Aquarium workflow.
- [ ] Permit compatible project-specific changes only outside the required Aquarium interface.
- [ ] Present reviewable base, current, and incoming evidence before an approved upstream merge or replacement.
- [ ] Cover canonical, unexplained mismatch, compatible customization, incompatible workflow, direct-Podway-only validity, no-overwrite, and upstream-update scenarios.
- [ ] Run focused tests and the repository-standard verification justified by the changed surfaces.

### Do Not

- [ ] Do not treat any byte mismatch as consent to adopt project ownership.
- [ ] Do not overwrite a project-owned Procedure during setup, update, validation, or migration.
- [ ] Do not accept direct Podway validity as proof of Aquarium workflow compatibility.
- [ ] Do not hide an incompatible required node, route, type, handoff, or terminal behavior behind a warning.

## TASK-002: Qualify the Official Podway v0.2.6 Release

### Objective

Establish exact distribution evidence for Podway v0.2.6 and independently prove Aquarium compatibility with the official Apple Silicon artifact.

### Do

- [ ] Obtain the exact Podway release commit and evidence that its complete release and distribution gate passed.
- [ ] Resolve the official Apple Silicon archive and its published checksum from Podway-owned release surfaces.
- [ ] Verify the downloaded archive against the published checksum before execution.
- [ ] Run `PODWAY_BIN=<absolute-path> make test-podway-compat` against the extracted exact binary and exact Aquarium candidate.
- [ ] Confirm the released list-scale declaration and runtime enforcement required by Aquarium.
- [ ] Confirm strict unknown-field rejection, phase-aware daemon installation readiness, explicit verified-readiness state, and state-preserving retry behavior.
- [ ] Record the exact Podway SHA, archive identity, checksum result, Aquarium SHA, command, exit status, and bounded evidence location.

### Do Not

- [ ] Do not substitute Podway `main`, a locally built binary, development tests, or a consumer claim for the official release artifact.
- [ ] Do not perform Podway source changes, release QA, tagging, asset publication, or release publication from Aquarium ownership.
- [ ] Do not claim Aquarium distribution readiness solely because Podway's release gate passed.
- [ ] Do not reuse compatibility evidence after either the Podway artifact or Aquarium candidate changes.

## TASK-003: Validate the Complete Aquarium v0.1.12 Candidate

### Objective

Reconcile Aquarium-owned integration requirements and validate one final exact candidate after every accepted release-affecting change.

### Do

- [ ] Map every Aquarium-owned requirement from the two Sudal integration requests to current code, tests, documentation, and exact external-release evidence.
- [ ] Distinguish already satisfied behavior, confirmed gaps, external ownership, and unverifiable claims without creating retroactive Completed tasks.
- [ ] Require stable Podway v0.2.6 through v0.2.x and validate canonical Procedure behavior with the exact released binary.
- [ ] Validate supported project-owned Procedure behavior and its no-overwrite boundary.
- [ ] Validate the canonical Ouroboros 0.51.x isolated Codex launcher without probing or mutating the wrong environment.
- [ ] Require a single full-setup Codex artifact mutation where the enrolled contract requires it.
- [ ] Correct every confirmed Aquarium-owned release blocker at its exact owner and update affected specification and release-note surfaces.
- [ ] Run focused checks followed by the complete applicable Aquarium development gate against the latest exact candidate.
- [ ] Record residual uncertainty separately from passed development-contract evidence.

### Do Not

- [ ] Do not use stale integration-request analysis or evidence from an earlier candidate.
- [ ] Do not promote a cross-repository consumer claim to completion of producer-owned work.
- [ ] Do not claim release or distribution readiness from green static validators alone.
- [ ] Do not leave a current correctness or acceptance blocker as deferred feedback.

## TASK-004: Release Aquarium v0.1.12

### Objective

Prepare, validate, publish, and independently observe the exact Aquarium v0.1.12 release under the repository release policy.

### Do

- [ ] Invoke `$aquarium:release-handler` and establish `full` or `light` mode before release mutation.
- [ ] Inspect the worktree, local and remote `main`, exact candidate SHA, existing tag, and existing GitHub Release state.
- [ ] Reconcile every material change since the previous release with the open v0.1.12 CHANGELOG section and obtain approval for substantive entry changes.
- [ ] Commit the exact preparation through the authorized commit workflow and run a fresh release-QA pass against the resulting clean candidate.
- [ ] Execute the complete selected local release gate and preserve its exact evidence.
- [ ] Create the exact `[REL] Release v0.1.12` commit, push `main`, create and push the annotated `v0.1.12` tag, and create the GitHub Release in the required order.
- [ ] Verify remote `main`, the peeled tag, and the GitHub Release resolve to the intended release commit.
- [ ] Treat opening the next empty Unreleased cycle as a separate non-release action requiring separate approval.

### Do Not

- [ ] Do not include unrelated work or proceed from an ambiguous or dirty release candidate.
- [ ] Do not reuse release QA after substantive release-note text or functional candidate content changes.
- [ ] Do not publish a tag before the intended release commit is settled on remote `main`.
- [ ] Do not rewrite or delete a published tag without explicit authorization.
- [ ] Do not treat local release completion as authorization to open or publish the next release cycle.

## Epic Acceptance

- [ ] `TASK-001` through `TASK-004` are `Completed` in the canonical roadmap.
- [ ] An explicit epic-level review confirms the project-owned Procedure boundary, exact Podway evidence, final Aquarium candidate, and publication observations remain mutually consistent.
- [ ] The published v0.1.12 commit, peeled tag, and GitHub Release identity agree.
- [ ] Remaining independent work is recorded only in its proper roadmap, TODO, or deferred-feedback owner.
