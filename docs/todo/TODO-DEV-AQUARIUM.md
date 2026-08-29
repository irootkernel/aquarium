# Aquarium Development Environment Work Dossier

## Authority

**Roadmap epic:** `EPIC-002`

This dossier is the detailed scope and acceptance source of truth for `EPIC-002`, `TASK-005` through `TASK-015`, and `TASK-024`. The [canonical roadmap](../roadmap/README.md) alone owns their identities, ordering, dependencies, lifecycle vocabulary, and current status. Checklist marks in this file are review evidence only and never change roadmap state.

The shipped `$aquarium:dev-aquarium` skill and its linked reference own implemented workflow behavior. This dossier continues to own the remaining cross-repository integration and cold-validation acceptance scope without presenting it as current or released behavior.

## Goal

Provide an explicit Aquarium development channel that continuously exposes exact local `main` artifacts from Aquarium, Podway, Mulgae, Gaori, Sanho, and Dolgorae to their canonical development checkouts. The channel must surface package, handler, skill, MCP, and cross-project integration failures before stable release preparation while preserving a stable global fallback for projects that have not enrolled.

## Purpose

The current workflow often discovers integration failures only after a downstream release or Aquarium update, producing avoidable patch releases and rapidly increasing version numbers. The development channel moves that feedback earlier without replacing stable installations, weakening release QA, or making development artifacts look like distribution evidence.

## Success Criteria

- A maintainer can invoke `$aquarium:dev-aquarium` from a supported canonical checkout and complete enrollment without manually editing PATH, hooks, paired skills, or MCP configuration.
- Every successful canonical `main` commit produces an exact-SHA development artifact and atomically makes it current for that project.
- An invocation pins one resolved artifact for its lifetime, so publication or cleanup cannot change the running tool beneath it.
- No canonical enrollment uses the global stable tool; an invalid existing enrollment fails closed instead of silently falling back.
- A newly published artifact replaces the prior current artifact, and the superseded artifact is removed as soon as no active lease references it.
- Aquarium, all four initial tool producers, and the first additional Dolgorae producer pass their scoped contract tests; the final cold validation covers the complete enrolled set.

## Non-Goals

- This epic does not own Dolgorae runtime behavior, roadmap IDs, release state, or Specialist Review semantics; external Dolgorae `TASK-035` owns its producer implementation.
- It does not publish stable releases, satisfy release distribution gates, or replace exact official artifacts required by release QA.
- It does not discover arbitrary repositories, enroll every worktree, or choose a canonical checkout implicitly.
- It does not create repository-local `.aquarium` state or make host-local development metadata a roadmap, Git, Procedure, or release authority.
- It does not vendor Podway, Mulgae, Gaori, Sanho, Codex, or other upstream implementations into Aquarium.

## System Approach

### Explicit Enrollment

`$aquarium:dev-aquarium` is explicit-only. Invocation from a supported checkout diagnoses repository identity, branch, producer support, existing enrollment, hooks, build prerequisites, and the isolated Codex environment before proposing effects. Enrollment, hook installation or transfer, initial build, native configuration, and login remain separate approval or user-action boundaries.

Each project has at most one canonical checkout. Invoking the skill from another checkout proposes re-enrollment; approval transfers canonical ownership and removes only the hook integration previously owned by Aquarium from the old checkout.

### Host-Local Layout

Development runtime data lives under `~/.aquarium/`. There is no top-level `~/.aquarium/bin/`; project artifacts retain their repository-produced internal layout, including any project-local `bin/` directory.

The implementation must separate:

- enrollment metadata identifying one canonical checkout per project;
- immutable exact-SHA artifact directories per project;
- one atomic current selector per project;
- publisher and artifact lease files;
- one isolated Codex home containing development plugin, paired skill, and MCP configuration state.

Exact path names below `~/.aquarium/` are frozen by `TASK-006` before implementation. No credential contents may be copied into Aquarium-managed metadata; the isolated Codex home owns its native login state.

### Producer Contract

Every enrolled repository owns two common Make interfaces:

- `make aquarium-dev-describe` performs no mutation and emits one versioned JSON description of the project, next development version, artifact kind, and declared build output.
- `make aquarium-dev-build AQUARIUM_DEV_OUTPUT=<absolute-staging-directory>` builds only from the invoking repository's exact checked-out commit, writes only below the supplied staging directory, and emits one versioned JSON manifest containing project identity, exact Git SHA, development version, artifact-relative path, and checksum.

The manager validates both documents, the canonical Git root, branch, exact local `main` SHA, output containment, artifact existence, checksum, and project identity. It never guesses a repository-specific build command or artifact path.

### Publication and Resolution

A native post-commit integration requests a build only after a commit lands on the enrolled canonical checkout's local `main`. Requests are serialized per project. A failed build leaves the previous current artifact unchanged and returns durable bounded diagnostic evidence without rolling back the Git commit.

Publication builds into a staging directory, validates the manifest, atomically promotes the immutable exact-SHA artifact, and atomically advances the project's current selector. Concurrent or duplicate requests for the same SHA converge on one artifact.

Resolution follows this matrix:

| Enrollment state | Canonical checkout | Current artifact | Result |
| --- | --- | --- | --- |
| No enrollment | Not applicable | Not applicable | Use the global stable tool or plugin |
| Valid enrollment | Present and valid | Present and valid | Use and lease the exact current development artifact |
| Valid enrollment | Missing or identity mismatch | Any | Fail closed with repair guidance |
| Valid enrollment | Present and valid | Missing, corrupt, or SHA/version mismatch | Fail closed with rebuild guidance |

Each invocation acquires a shared artifact lease before launch and holds it until the child process exits. Publication and cleanup use the corresponding exclusive lease. The old artifact is removed immediately after a newer artifact becomes current when no shared lease remains; otherwise cleanup completes as soon as the last lease is released. Historical binaries do not accumulate as a cache.

### Isolated Codex Environment

Aquarium development uses a dedicated Codex home below `~/.aquarium/`, separate from the user's stable Codex home and login. It contains the development Aquarium plugin snapshot, paired skills, and MCP configuration needed to resolve enrolled development tools. The skill may diagnose and configure this home with approval but cannot authenticate as the user; first login is a one-time user action.

## Task Composition

| Task | Outcome |
| --- | --- |
| `TASK-005` | Feasibility evidence for the risky host, hook, locking, publication, and Codex assumptions |
| `TASK-006` | One frozen shared producer, storage, resolution, version, and error contract |
| `TASK-007` | Explicit skill enrollment and safe canonical hook lifecycle |
| `TASK-008` | Exact-main build scheduling and atomic publication |
| `TASK-009` | Stable fallback, fail-close resolution, invocation leases, and prompt cleanup |
| `TASK-010` | Aquarium plugin production and isolated Codex development environment |
| `TASK-011` | Podway producer and consumer integration |
| `TASK-012` | Mulgae producer and consumer integration |
| `TASK-013` | Gaori producer and consumer integration |
| `TASK-014` | Sanho producer and consumer integration |
| `TASK-024` | Dolgorae executable producer and guarded consumer integration |
| `TASK-015` | Clean-state cross-project validation of the complete development channel |

## TASK-005: Prove Development-Channel Feasibility

### Do

- [x] Prove shared and exclusive operating-system lease behavior on every supported host platform.
- [x] Prove atomic directory promotion and current-selector replacement on the supported filesystem.
- [x] Inspect existing hook strategies in Aquarium and the four initial tool repositories and prove coexistence without replacing unrelated hooks.
- [x] Prove that a post-commit request can report failure without changing or rolling back the completed Git commit.
- [x] Prove dedicated Codex-home isolation for plugin, paired skills, MCP configuration, and login state.
- [x] Prove that a child process can remain pinned to an acquired artifact while a newer artifact is published.
- [x] Record bounded evidence, rejected alternatives, platform limitations, and every contract decision required by `TASK-006`.

### Do Not

- [x] Do not persist production enrollment or install permanent hooks.
- [x] Do not modify consumer repositories merely to make the feasibility probe pass.
- [x] Do not treat a single happy-path prototype as cross-project acceptance.
- [x] Do not begin full implementation while a core lock, hook, atomicity, or Codex-isolation assumption remains unproven.

## TASK-006: Define the Shared Development Contract

### Do

- [x] Freeze the `aquarium-dev-describe` and `aquarium-dev-build` JSON schemas, required fields, exit behavior, and stdout/stderr discipline.
- [x] Freeze the `AQUARIUM_DEV_OUTPUT` containment and staging rules.
- [x] Freeze project identifiers, exact-SHA identity, next-development-version authority, checksum requirements, and artifact kinds.
- [x] Freeze the `~/.aquarium/` directory layout without adding a top-level `bin/`.
- [x] Freeze enrollment, canonical checkout identity, re-enrollment, hook ownership, current-selector, lease, and cleanup contracts.
- [x] Freeze stable fallback versus broken-enrollment fail-close behavior and machine-readable error identities.
- [x] Define how the isolated Codex home pins a matching Aquarium plugin, paired skills, MCP configuration, and resolved tool artifacts.
- [x] Add schema fixtures and negative contract tests before downstream producer implementation.

### Do Not

- [x] Do not allow producer-specific undocumented flags or inferred artifact locations.
- [x] Do not accept branch names, working-tree bytes, or mutable paths as substitutes for exact commit identity.
- [x] Do not let enrollment metadata own project lifecycle, roadmap, Git, Procedure, or release state.
- [x] Do not add compatibility branches for impossible states instead of rejecting invalid contract data.

## TASK-007: Implement Enrollment and Hook Lifecycle

### Do

- [x] Introduce the explicit-only `$aquarium:dev-aquarium` skill with diagnosis before effects.
- [x] Validate one regular non-symlink Git root, supported project identity, canonical local `main`, and both producer targets.
- [x] Present separate approvals for enrollment, hook mutation, initial build, and native Codex configuration.
- [x] Enroll at most one canonical checkout per project and record only bounded non-secret host-local metadata.
- [x] Make same-checkout enrollment idempotent.
- [x] Require explicit approval before re-enrollment from another checkout and transfer only Aquarium-owned hook integration.
- [x] Preserve unrelated native hooks and report any hook ownership conflict instead of overwriting it.
- [x] Provide diagnosis and repair paths for missing checkouts, invalid identities, stale hooks, and incomplete setup.

### Do Not

- [x] Do not discover or enroll repositories implicitly.
- [x] Do not install hooks, build artifacts, change native configuration, or authenticate during read-only diagnosis.
- [x] Do not delete or rewrite unrelated hook content.
- [x] Do not silently change the canonical checkout because the skill was invoked elsewhere.

## TASK-008: Implement Build Scheduling and Publication

### Do

- [x] Trigger a build request only for a completed commit on the enrolled canonical checkout's local `main`.
- [x] Serialize publisher work per project and coalesce duplicate requests for the same SHA.
- [x] Invoke the repository-owned build target with a fresh contained staging directory.
- [x] Validate manifest schema, project identity, exact SHA, development version, output containment, artifact existence, and checksum.
- [x] Promote validated artifacts immutably and advance the current selector atomically.
- [x] Leave the prior current artifact unchanged on build, validation, or publication failure.
- [x] Record bounded diagnostics identifying the rejected SHA and failure stage.
- [x] Provide an explicit rebuild path for recovery without requiring another Git commit.

### Do Not

- [x] Do not build from a dirty working tree, a non-main commit, or a SHA different from the post-commit request.
- [x] Do not run repository-specific build commands outside the shared Make contract.
- [x] Do not expose partially written artifacts through the current selector.
- [x] Do not make a failed development build invalidate the completed Git commit or stable global tool.

## TASK-009: Implement Resolution, Leases, and Cleanup

### Do

- [x] Resolve the global stable tool only when the project has no canonical enrollment.
- [x] Fail closed when enrollment exists but the canonical checkout or current artifact is missing, corrupt, or inconsistent.
- [x] Acquire and validate a shared artifact lease before launching a development tool.
- [x] Pin the resolved path, SHA, version, and checksum for the complete child-process lifetime.
- [x] Use an exclusive lease for publication and cleanup operations that affect artifact reachability.
- [x] Remove the superseded artifact immediately when no shared lease remains, or immediately after the last active lease exits.
- [x] Recover stale leases only through operating-system ownership semantics rather than elapsed-time guessing.
- [x] Test concurrent launch, publication, failure, interruption, and cleanup races.

### Do Not

- [x] Do not fall back to stable when a recorded development enrollment is broken.
- [x] Do not re-resolve current during a running invocation.
- [x] Do not delete an artifact while any process holds its shared lease.
- [x] Do not retain old binaries as an unbounded historical cache.

## TASK-010: Isolate Aquarium and Codex Development Runtime

### Do

- [x] Implement Aquarium's producer output for the development plugin snapshot and paired resources.
- [x] Create the dedicated Codex home below `~/.aquarium/` without reading or copying stable-home credentials.
- [x] Install or refresh the exact Aquarium development plugin, paired skills, and MCP configuration through explicit approval.
- [x] Ensure the development plugin and paired skills resolve the same enrolled artifact generation.
- [x] Detect missing first login and return exact user action without attempting authentication.
- [x] Keep stable Codex configuration and global Aquarium installation unchanged.
- [x] Provide one diagnostic report covering enrollment, plugin SHA, paired skill generation, MCP configuration, and resolved project artifacts.

### Do Not

- [x] Do not mutate the user's stable Codex home as a shortcut.
- [x] Do not copy tokens, sessions, credentials, or secret configuration into Aquarium-managed metadata.
- [x] Do not mix a development plugin with incompatible stable paired skills or MCP endpoints.
- [x] Do not present successful development setup as a stable Aquarium installation or release.

## TASK-011: Integrate Podway

### Do

- [ ] Add the shared describe and build targets using Podway-owned version and build authorities.
- [ ] Produce the exact local-main Podway binary in the declared project artifact layout.
- [ ] Embed or expose development version and exact SHA identity for runtime diagnosis.
- [ ] Verify canonical enrollment, post-commit update, direct resolution, and Aquarium consumer resolution.
- [ ] Preserve Podway's independent stable release, distribution, daemon, and Procedure ownership boundaries.

### Do Not

- [ ] Do not make Aquarium own Podway's native build implementation or release process.
- [ ] Do not accept a Podway development binary as evidence for an official-artifact compatibility gate.
- [ ] Do not change Podway behavior outside the shared producer and resolution requirement.

## TASK-012: Integrate Mulgae

### Do

- [ ] Add the shared describe and build targets using Mulgae-owned version and build authorities.
- [ ] Produce the exact local-main Mulgae binary in the declared project artifact layout.
- [ ] Embed or expose development version and exact SHA identity for runtime diagnosis.
- [ ] Verify canonical enrollment, post-commit update, direct resolution, and Aquarium review-consumer resolution.
- [ ] Preserve Mulgae provider, review-run, evidence, and independent release ownership.

### Do Not

- [ ] Do not make Aquarium own provider credentials, native review behavior, or Mulgae releases.
- [ ] Do not contact providers during producer-contract tests unless a separately authorized scenario requires it.
- [ ] Do not promote development review output to durable product or release proof.

## TASK-013: Integrate Gaori

### Do

- [ ] Add the shared describe and build targets using Gaori-owned version and build authorities.
- [ ] Produce the exact local-main Gaori binary in the declared project artifact layout.
- [ ] Embed or expose development version and exact SHA identity for runtime diagnosis.
- [ ] Verify canonical enrollment, post-commit update, direct resolution, and Aquarium test-consumer resolution.
- [ ] Preserve Gaori's native run, artifact, status, and independent release ownership.

### Do Not

- [ ] Do not replace attached Gaori MCP operation with an unrelated transport merely for convenience.
- [ ] Do not make Aquarium own Gaori test execution semantics or release publication.
- [ ] Do not interpret extractor or artifact status alone as pass or fail.

## TASK-014: Integrate Sanho

### Do

- [ ] Add the shared describe and build targets using Sanho-owned version and build authorities.
- [ ] Produce the exact local-main Sanho binary in the declared project artifact layout.
- [ ] Embed or expose development version and exact SHA identity for runtime diagnosis.
- [ ] Verify canonical enrollment, post-commit update, direct resolution, and Aquarium commit-consumer resolution.
- [ ] Preserve Sanho workspace, policy, warning, rejection, and independent release ownership.

### Do Not

- [ ] Do not initialize or adopt a Sanho workspace merely because development setup is requested.
- [ ] Do not bypass Sanho policy, commit gates, or explicit push approval.
- [ ] Do not make Aquarium own Sanho's native policy or release implementation.

## TASK-024: Integrate Dolgorae

### Do

- [ ] Accept one exact clean local-`main` producer handoff from external Dolgorae `TASK-035` through the frozen shared Make contract.
- [ ] Add `dolgorae` as an `executable` project identity without adding an MCP registration or global PATH entry.
- [ ] Resolve and report the canonical immutable generation path, exact Git SHA, development version, artifact kind, and SHA-256.
- [ ] Require the expected Git SHA, development version, and SHA-256 as one complete launch guard set when a consumer binds an exact development candidate.
- [ ] Hold the selected generation lease through executable replacement and preserve fail-closed behavior when current advances, enrollment breaks, or bytes drift.
- [ ] Include Dolgorae in isolated Codex diagnosis as a CLI integration and keep stable-home state unchanged.

### Do Not

- [ ] Do not make Aquarium own Dolgorae runtime, Specialist Review, profile, workspace, roadmap, or release behavior.
- [ ] Do not register Dolgorae as an MCP server or silently substitute a stable binary for a broken enrollment.
- [ ] Do not treat a successful producer build as Dolgorae release or distribution evidence.
- [ ] Do not make `TASK-024` wait for `TASK-011` through `TASK-014`; only `TASK-015` joins the complete producer set.

## TASK-015: Cold-Validate the Integrated Environment

### Do

- [ ] Start from clean temporary user and repository state with no development enrollment.
- [ ] Prove the global stable fallback before enrollment.
- [ ] Enroll Aquarium, each of the four initial tool producers, and Dolgorae only through the skill workflow.
- [ ] Prove initial build, exact-SHA selection, subsequent post-commit update, and atomic current advancement.
- [ ] Prove same-checkout idempotency and explicitly approved re-enrollment to another checkout.
- [ ] Prove missing producer, rejected manifest, build failure, missing canonical checkout, corrupt current artifact, and failed Codex-login diagnostics.
- [ ] Prove concurrent invocation pinning, lease-protected replacement, and prompt cleanup after the last lease exits.
- [ ] Prove the isolated Codex plugin, paired skills, MCP configuration, and all resolved binaries refer to compatible development generations.
- [ ] Exercise representative Aquarium integrations using Podway, Mulgae, Gaori, Sanho, and Dolgorae without provider or publication effects outside explicit authorization.
- [ ] Run focused suites followed by the complete applicable Aquarium development gate and record exact candidate SHAs.

### Do Not

- [ ] Do not reuse enrollment, build, login, or artifact state from the implementation environment.
- [ ] Do not skip failure and concurrency scenarios after happy-path success.
- [ ] Do not claim stable distribution readiness, publish v0.1.14, or open its CHANGELOG cycle from development-channel evidence.
- [ ] Do not complete the epic from cross-repository consumer claims without exact producer SHAs and independent revalidation.

## Epic Acceptance

- [ ] `TASK-005` through `TASK-015` and `TASK-024` are `Completed` in the canonical roadmap.
- [ ] The cold validation uses the final exact Aquarium and producer candidates after all accepted changes.
- [ ] Stable fallback, broken-enrollment fail-close, exact-SHA pinning, lease safety, and prompt cleanup are independently demonstrated.
- [ ] Current specs, architecture, ADRs, implementation tips, operations, public documentation, privacy terms, and executable validation reflect the shipped behavior without moving lifecycle status out of the roadmap.
- [ ] Development-contract evidence remains explicitly separate from stable release and distribution evidence.
