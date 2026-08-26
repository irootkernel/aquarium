# Aquarium v0.1.12 Release Work Dossier

## Authority

**Roadmap epic:** `EPIC-001`

This dossier is the detailed scope and acceptance source of truth for `EPIC-001`, `TASK-001` through `TASK-004`, and `TASK-016` through `TASK-018`. The [canonical roadmap](../roadmap/README.md) alone owns their identities, ordering, dependencies, lifecycle vocabulary, and current status. Checklist marks in this file are review evidence only and never change roadmap state.

The root `CHANGELOG.md` owns cumulative release notes and the open release version. Repository instructions and the release workflow own approval, verification, commit, tag, push, and publication behavior when they are stricter than this dossier.

## Goal and Purpose

Release Aquarium v0.1.12 from one exact candidate after adopting the released Podway v0.2.6 runtime contract, reauthoring Aquarium's canonical Procedures from the released preset patterns, preserving valid local customization, independently qualifying the official artifact, reconciling Aquarium-owned integration requirements, and verifying the published commit, tag, and GitHub Release.

This work exists to prevent a development-branch result, consumer-side claim, stale review, or partial publication observation from being promoted to release proof.

## Approach

1. Align Aquarium's runtime, lifecycle, evidence, skill, and daemon-readiness contracts with the released Podway v0.2.6 interfaces.
2. Reauthor the five canonical Aquarium Procedures from the applicable v0.2.6 preset patterns while retaining Aquarium-owned workflow and approval semantics.
3. Preserve a Podway-valid same-ID local Procedure unless the user explicitly selects reviewed canonical replacement.
4. Obtain Podway's exact independently released v0.2.6 artifact and qualify the final canonical Procedures and runtime paths against it.
5. Reconcile all material Aquarium-owned integration requirements, validate the final exact candidate, and execute a full release with exact publication verification.

## Cross-Cutting Boundaries

- Aquarium does not implement, tag, publish, or rewrite Podway-owned release work.
- Development binaries and branch tests do not satisfy a requirement for an official archive and checksum.
- No task may infer approval for another effect such as installation, staging, commit, push, tag, or publication.
- No task may include unrelated staged, unstaged, untracked, or ignored runtime work.
- A task result does not advance roadmap state until the owning workflow records accepted evidence through the roadmap authority.
- Aquarium does not impose a second structural compatibility schema on a local Procedure that has the expected Aquarium filename and Procedure ID; Podway v0.2.6 owns document validity.
- A local byte mismatch never authorizes replacement, normalization, merge, or persistent Aquarium ownership metadata.

## TASK-016: Align the Podway v0.2.6 Runtime Contract

### Objective

Adopt the released Podway v0.2.6 observation, lifecycle, evidence-read, paired-skill, and daemon-readiness interfaces before changing the canonical Procedures.

### Do

- [ ] Require `podway.observation-result/v3` for managed observation and consume bounded previews without treating them as complete values.
- [ ] Read complete selected evidence through digest-bound `evidence read` pagination and restart from a fresh observation when a page token becomes stale.
- [ ] Replace removed start and replacement flags with the current start policy, disposed-terminal automatic archival, explicit prepared or running preservation and deletion, and the 32-session inactive-history limit.
- [ ] Derive lifecycle mutations from the latest observation templates and current `podway help <route>` grammar rather than hard-coded argv.
- [ ] Update the supported `use-podway` file inventory to `SKILL.md`, `references/lifecycle.md`, `references/goal.md`, and `references/recovery.md`.
- [ ] Keep `create-podway-procedure` as a maintainer authoring dependency, not a `dev-setup` installation, freshness, or readiness requirement.
- [ ] Add bounded `daemon wait-ready` inspection and accept a ready completed recovery inventory even when quarantined worktrees are counted as failed.
- [ ] Version every changed Aquarium inspection result and update its consumers, fixtures, and current documentation in the same task.

### Do Not

- [ ] Do not retain `start --replace-eligible`, require observation v2, or invent replacement flags from an internal mutation-template name.
- [ ] Do not treat a bounded evidence preview as the complete recorded item.
- [ ] Do not require `worktree_recovery.failed == 0` after Podway reports ready state and completed recovery.
- [ ] Do not install, update, or require `create-podway-procedure` in target repositories through Aquarium setup.

## TASK-017: Reauthor the Delivery Procedures

### Objective

Rebuild the task, goal, and validation Procedures from the applicable released v0.2.6 preset patterns while preserving Aquarium's delivery, review, approval, and closeout responsibilities.

### Do

- [ ] Reauthor `aquarium-task-v2` from the `sw-dev-v2` typed verification and phase-owner review patterns, retain explicit final approval, and increase its Procedure version from `3` to `4`.
- [ ] Place refinement before the verification evidence it can invalidate, use guarded external check results, preserve the confirmation-only review hold, and select only required evidence items.
- [ ] Reauthor `aquarium-goal-v2` from goal-tracked delivery patterns and increase its Procedure version from `4` to `5`.
- [ ] Record and verify hardening-deferral evidence before the semantic deferral decision instead of creating its evidence after the decision.
- [ ] Reauthor `aquarium-validation-v2` from the `analysis-v2` audit and guarded-review patterns and increase its Procedure version from `5` to `6`.
- [ ] Route clean, remediation, re-audit, final review, explicit user direction, incomplete outcome, assessment, and closeout without bypassing required fresh evidence.
- [ ] Use `check_result`, `required_when`, decision guards, non-negative counters, positive ordinals, and item-selected evidence only where the recorded requirement supports them.
- [ ] Keep external work, user approval, semantic truth, Git state, and review adjudication outside Podway's trust claim.

### Do Not

- [ ] Do not copy a preset unchanged or add a v0.2.6 feature solely to demonstrate it.
- [ ] Do not guard user approval, risk acceptance, goal outcome, or another semantic judgment that Podway cannot establish.
- [ ] Do not change the three stable Procedure IDs or rewrite existing session snapshots.

## TASK-018: Reauthor the Analysis Procedures

### Objective

Rebuild the design and war-room Procedures from the released `analysis-v2` and applicable bug-fix patterns while keeping Aquarium's explicit diff approval and diagnostic ownership.

### Do

- [ ] Reauthor `aquarium-design-v2` around bounded context, discovery, drafting, challenge, phase-owner quality rework, explicit diff approval, application, assessment, and closeout; increase its version from `1` to `2`.
- [ ] Reauthor `aquarium-war-room-v2` around baseline or reproduction, investigation, semantic cause and scope decisions, task or epic or incomplete proposal, quality rework, explicit approval, documentation, assessment, and closeout; increase its version from `1` to `2`.
- [ ] Use structurally bound quality results and conditional findings while leaving root-cause, scope, and user decisions unguarded.
- [ ] Select the minimum fresh evidence each consumer needs and keep provider outputs, source contents, transcripts, and generated documents outside Podway.
- [ ] Preserve `new-project`, `new-feature`, `refactor`, `design-qa`, and `war-room` as the sole workflow owners of these sessions.

### Do Not

- [ ] Do not let Ouroboros or Podway apply repository changes, approve a diff, or establish diagnostic truth.
- [ ] Do not turn war-room into fix implementation or let a terminal route bypass an approved task, epic, or incomplete-investigation artifact.
- [ ] Do not change either stable Procedure ID or reinterpret an admitted historical session.

## TASK-001: Preserve Local Procedure Customization

### Objective

Preserve a Podway-valid local Procedure with the expected Aquarium filename and Procedure ID, and replace it with current canonical bytes only after an explicit reviewed choice.

### Do

- [ ] Match each managed location by its expected filename and Procedure ID, then use the selected Podway v0.2.6 binary as the document-validity authority.
- [ ] Report canonical bytes, valid local customization, invalid content, missing content, and unsafe filesystem state without introducing a second Aquarium compatibility judgment.
- [ ] Treat a valid local customization as configured even when its bytes, graph, items, prompts, bounds, or routes differ from Aquarium's bundled source.
- [ ] During an approved setup or update, show the exact current-to-canonical diff and ask whether to preserve the local file or replace it with canonical bytes.
- [ ] Preserve the selected local file without writing metadata when the user chooses to keep it; replace only the exact reviewed file when the user chooses canonical restoration.
- [ ] Keep known prior canonical and v0.2.5 workaround identities as bounded update explanations without making them a separate validity or readiness class.
- [ ] Cover canonical, valid customization, invalid content, unsafe paths, preserve, canonical restoration, no-overwrite, and active-snapshot scenarios.
- [ ] Run focused tests and the repository-standard verification justified by the changed surfaces.

### Do Not

- [ ] Do not create an ownership manifest, Aquarium Procedure interface schema, provenance registry, or hidden project state.
- [ ] Do not degrade a same-ID local Procedure merely because it differs from Aquarium's canonical graph.
- [ ] Do not overwrite, merge, normalize, or reformat local Procedure content without the exact replacement approval.
- [ ] Do not imply that Podway validity proves the external work, Aquarium approval, review, Git, roadmap, or release result recorded by the Procedure.

## TASK-002: Qualify the Official Podway v0.2.6 Release

### Objective

Establish exact distribution evidence for Podway v0.2.6 and independently prove Aquarium compatibility with the official Apple Silicon artifact.

### Do

- [ ] Obtain the exact Podway release commit and evidence that its complete release and distribution gate passed.
- [ ] Resolve the official Apple Silicon archive and its published checksum from Podway-owned release surfaces.
- [ ] Verify the downloaded archive against the published checksum before execution.
- [ ] Run the complete authoring sequence against all five exact canonical Procedure bytes: format check, validate, vet, lint with warnings as errors, check with warnings as errors, and preview.
- [ ] Require preview's exact digest-fenced start suggestion and the official binary's v0.2.6 build identity rather than reconstructing either value.
- [ ] Run `PODWAY_BIN=<absolute-path> make test-podway-compat` against the extracted exact binary and exact Aquarium candidate.
- [ ] Under separate runtime authorization, exercise the versioned accepted-path inventory through the public CLI, official matching daemon binary, an isolated non-production socket, and disposable worktrees.
- [ ] Confirm the released list-scale declaration and runtime enforcement required by Aquarium.
- [ ] Confirm strict unknown-field rejection, conditional items, guarded decisions, structured external results, evidence pagination, stale-evidence behavior, immutable old snapshots, and phase-aware verified readiness.
- [ ] Record the exact Podway SHA, archive and binary identities, checksum result, Aquarium SHA, commands, exit statuses, bounded runtime proof, and limitations separately.

### Do Not

- [ ] Do not substitute Podway `main`, a locally built binary, development tests, or a consumer claim for the official release artifact.
- [ ] Do not perform Podway source changes, release QA, tagging, asset publication, or release publication from Aquarium ownership.
- [ ] Do not claim Aquarium distribution readiness solely because Podway's release gate passed.
- [ ] Do not reuse compatibility evidence after either the Podway artifact or Aquarium candidate changes.
- [ ] Do not start, stop, install, replace, or reuse the production Podway daemon for runtime qualification.

## TASK-003: Validate the Complete Aquarium v0.1.12 Candidate

### Objective

Reconcile Aquarium-owned integration requirements and validate one final exact candidate after every accepted release-affecting change.

### Do

- [ ] Map every Aquarium-owned requirement from the two Sudal integration requests to current code, tests, documentation, and exact external-release evidence.
- [ ] Distinguish already satisfied behavior, confirmed gaps, external ownership, and unverifiable claims without creating retroactive Completed tasks.
- [ ] Require stable Podway v0.2.6 through v0.2.x and validate the v0.2.6 runtime interfaces and all canonical Procedure behavior with the exact released binary.
- [ ] Validate Podway-valid same-ID local Procedure preservation, explicit canonical replacement, and the no-overwrite boundary without an Aquarium structural compatibility layer.
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

- [ ] Invoke `$aquarium:release-handler` in `full` mode because this epic changes functional runtime and Procedure contracts.
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

- [ ] `TASK-001` through `TASK-004` and `TASK-016` through `TASK-018` are `Completed` in the canonical roadmap.
- [ ] An explicit epic-level review confirms the v0.2.6 runtime contract, canonical Procedures, local-customization boundary, exact Podway evidence, final Aquarium candidate, and publication observations remain mutually consistent.
- [ ] The published v0.1.12 commit, peeled tag, and GitHub Release identity agree.
- [ ] Remaining independent work is recorded only in its proper roadmap, TODO, or deferred-feedback owner.
