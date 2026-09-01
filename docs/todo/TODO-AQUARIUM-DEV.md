# Aquarium Development Environment Work Dossier

## Authority

**Roadmap epic:** `EPIC-002`

This dossier is the detailed scope and acceptance source of truth for `EPIC-002`, `TASK-005` through `TASK-015`, `TASK-024`, and corrective `TASK-031`. The [canonical roadmap](../roadmap/README.md) alone owns identity, ordering, dependencies, lifecycle vocabulary, and current status. Checklist marks here are review evidence only.

The shipped `$aquarium:aquarium-dev` skill and its linked reference own implemented workflow behavior. ADR-0008 supersedes the isolated-Codex and Dolgorae-development portions of the original design while preserving completed historical work.

## Goal

Provide an explicit development channel that exposes exact local-`main` artifacts from Aquarium, Podway, Mulgae, Gaori, Sanho, and Dolgorae through `~/.aquarium-dev/bin` without changing production state, production tools, or the caller's selected Codex environment.

Dolgorae is an enrollable development producer whose repository owns enrollment when its approved producer commit is created. It has no missing-binary exception: before enrollment the required global binary must exist, or the command fails closed and requests dev-setup. Independent Review still uses only the globally installed official release and validates its exact version, executable checksum, and capabilities immediately before use. Orca Review launches Codex directly through Orca without Dolgorae.

## Success Criteria

- `$aquarium:aquarium-dev` diagnoses and enrolls one named canonical checkout without repository-local Aquarium state.
- All development metadata and artifacts live below `~/.aquarium-dev`; `~/.aquarium` remains production-only.
- Every successful canonical local-`main` build publishes one immutable exact-SHA generation. Foreground tools advance current immediately; managed services remain pending until approved activation.
- Foreground and activated managed-service commands are exposed through stable `~/.aquarium-dev/bin` indirections backed by one atomic current selector.
- `aquarium-dev <tool> [args...]` admits only supported tools, falls back only an absent foreground tool to the caller's global PATH outside both Aquarium roots, and requires exact ready service identity without fallback for managed services. It otherwise inherits the caller's environment, including `CODEX_HOME`.
- Aquarium does not create or own a Codex home, authentication, plugin installation, or MCP configuration for the development channel.
- Dolgorae may be absent from enrollment, artifact, and selector state until its repository registers an approved producer commit, but its required global installation must exist for fallback. Podway is the first required managed service and fails closed without an exact active development generation instead of using production fallback; Sanho is explicitly optional.
- Development evidence remains distinct from stable installation, release, distribution, and release-QA evidence.

## Non-Goals

- This epic does not own external producer build implementations or releases.
- It does not discover repositories, enroll worktrees implicitly, or select a canonical checkout without approval.
- It does not configure Codex, authenticate users, install production tools, publish releases, or replace distribution gates.
- It does not delete preserved production audit records or legacy Codex data merely because an older development design referenced them.

## Current System Approach

### Explicit Enrollment

Invocation diagnoses repository identity, branch, clean committed state, producer support, enrollment, hook ownership, build prerequisites, current or pending generation, command selector, and managed-service status before proposing effects. Enrollment, hook installation, checkout transfer or same-checkout legacy-path migration, build, managed-service activation, and launcher installation each have a separate approval boundary.

Each supported project has at most one canonical checkout. Approved re-enrollment transfers or migrates only the exact recorded Aquarium-owned hook block. Foreign hook bytes and executable mode are preserved, and failure restores all touched files.

### Host-Local Layout

All development state is rooted at `~/.aquarium-dev/`:

- `enrollments/` records one canonical checkout per supported producer;
- `artifacts/` contains immutable exact-SHA generations;
- `current/` atomically selects one validated generation per project;
- `pending/` retains one validated managed-service target until activation;
- `bin/` stably resolves each foreground or activated managed-service command through its atomic current generation;
- `runtime/` contains opaque producer-owned managed-service state beneath one project root;
- `locks/`, `requests/`, and `diagnostics/` support bounded publication and recovery.

The separately approved launcher is installed at `~/.local/bin/aquarium-dev`. It preserves the caller's environment while changing only the child PATH and exact command selection. It resolves only an absent foreground command from the caller's global PATH. A managed-service command requires a matching ready or busy controller status and never falls back to production. There is no development Codex home and no Aquarium-owned authentication, plugin, or MCP configuration.

### Producer and Publication Contract

Every enrolled repository owns two common Make interfaces:

- `make aquarium-dev-describe` performs no mutation and emits the versioned project description.
- `make aquarium-dev-build AQUARIUM_DEV_OUTPUT=<absolute-empty-directory>` builds committed bytes into the supplied staging directory and emits the versioned exact-SHA manifest.

The manager validates project identity, canonical Git root, local `main`, clean exact HEAD, version, output containment, artifact kind, entrypoints, canonical checksum, and manifest consistency. It builds from an isolated copy of the admitted commit and promotes a completed generation immutably. Foreground producers advance current atomically. Managed services use a generic producer-owned controller with read-only `status` and `plan` plus approved exact-token `apply`; a new generation remains pending while busy and advances current only after exact readiness. Consumers hold shared generation leases through process exit, managed-service consumers also hold the service lock, and cleanup defers while old bytes are in use or selected as pending. Failures preserve the previous current generation and write bounded diagnostics.

## Historical Tasks and Corrective Ownership

| Task | Outcome |
| --- | --- |
| `TASK-005` | Proved the original host, hook, locking, atomicity, and isolated-runtime assumptions. |
| `TASK-006` | Froze the original shared contract. The root and Codex portions are superseded by `TASK-031`. |
| `TASK-007` | Implemented explicit enrollment and safe hook lifecycle. |
| `TASK-008` | Implemented exact-main build scheduling and atomic publication. |
| `TASK-009` | Implemented the original resolver and lease model, simplified by `TASK-031`. |
| `TASK-010` | Implemented the original isolated Codex environment, superseded by `TASK-031`. |
| `TASK-024` | Implemented the historical Dolgorae producer path; current enrollment waits for the corrected tool-repository commit. |
| `TASK-031` | Separates development and production roots, removes Codex ownership, adds development-first foreground fallback plus fail-closed managed services, admits optional Dolgorae enrollment, and removes Dolgorae coupling from Orca Review. |
| `TASK-011` through `TASK-014` | Integrate Podway, Mulgae, Gaori, and Sanho producers. |
| `TASK-015` | Cold-validates the complete corrected development channel. |

## TASK-031: Separate Development and Production Environments

### Do

- [x] Rename the public skill, CLI module, fixtures, tests, and documentation from `dev-aquarium` to `aquarium-dev`.
- [x] Move the default development root from `~/.aquarium` to `~/.aquarium-dev`.
- [x] Publish executable producers through stable `~/.aquarium-dev/bin/<project-id>` indirections backed by atomic current selectors.
- [x] Add a separately approved `~/.local/bin/aquarium-dev` launcher that inherits the caller's environment and prepends only the development bin directory.
- [x] Prefer each available development command independently, fall back only an absent foreground tool to global PATH outside both Aquarium roots, and fail closed on invalid selected or managed-service state.
- [x] Remove isolated Codex configuration, authentication, plugin installation, and MCP ownership from the manager and public workflow.
- [x] Admit Dolgorae as an executable producer, require global fallback before registration, and request dev-setup when neither generation exists.
- [x] Route Independent Review to the globally installed official Dolgorae v0.1.0 executable with immediate identity and capability checks.
- [x] Route Orca Review directly to one fresh Orca-managed Codex worker without Dolgorae discovery, capture, launch, or settlement.
- [x] Preserve historical decisions by superseding ADR-0007 with ADR-0008 instead of rewriting the old record.
- [x] Pass focused unit, structural, and complete repository gates.
- [x] Install and verify the user-local launcher on the approved host; Dolgorae enrollment occurs only from its approved repository commit.
- [x] Migrate Aquarium enrollment and artifacts only from a clean committed candidate capable of reproducing the corrected contract.

### Do Not

- [x] Do not modify tracked Dolgorae source.
- [x] Do not create a `$use-dolgorae` skill or another Aquarium-owned Dolgorae runtime.
- [x] Do not delete Dolgorae Application Support audit records or legacy `~/.aquarium/codex` data during migration.
- [x] Do not commit, push, release, or activate production Aquarium as part of this task without separate authority.

## Remaining Producer Integration

`TASK-011` is blocked after Aquarium completed the generic managed-service consumer boundary. Podway must separately commit (1) its persistent Aquarium controller and `podwayd --dev` service and (2) explicit workspace production/development channel switching. Master owns the exact clean local-`main` handoff back to Aquarium. Until then, Podway enrollment and service activation remain unavailable and Aquarium does not simulate Podway's LaunchAgent, registry, database, or workspace transition.

For each of Podway, Mulgae, Gaori, Sanho, and Dolgorae:

- [ ] accept one exact clean local-`main` handoff with both producer target outputs, checksum proof, embedded runtime identity, and focused tests;
- [ ] verify canonical enrollment, first build, post-commit update, direct PATH selection, and the relevant Aquarium consumer;
- [ ] preserve the producer's native runtime, policy, evidence, and independent release ownership;
- [ ] reject development artifacts as official distribution evidence.

## TASK-015: Cold Validation

- [ ] Start from clean temporary user and repository state with no development enrollment.
- [ ] Enroll Aquarium and the five external producers only through the skill workflow.
- [ ] Prove initial build, exact-SHA isolation, subsequent update, atomic current advancement, stable bin resolution, and superseded-generation cleanup.
- [ ] Prove same-checkout idempotency and approved re-enrollment.
- [ ] Prove missing producer, rejected manifest, build failure, missing checkout, corrupt artifact, and selector-drift diagnostics.
- [ ] Prove the launcher preserves caller environment, prefers enrolled development executables, falls back missing tools independently, and rejects corrupt selected generations.
- [ ] Prove Dolgorae remains absent from Orca Review, its development generation is never used for production review, and its separate production review setup is validated only when that setup is in scope.
- [ ] Run focused suites and the complete applicable Aquarium gate against the final exact candidates.

## Epic Acceptance

- [ ] `TASK-011` through `TASK-015` and `TASK-031` are `Completed` in the canonical roadmap.
- [ ] Cold validation uses final exact Aquarium and producer candidates after all accepted changes.
- [ ] Current specs, architecture, ADRs, implementation tips, operations, public documentation, privacy terms, and executable validation agree on the corrected contract.
- [ ] Development-contract evidence remains explicitly separate from production installation, stable release, and distribution evidence.
