# Aquarium Development Environment Work Dossier

## Authority

**Roadmap epic:** `EPIC-002`

This dossier is the detailed scope and acceptance source of truth for `EPIC-002`, `TASK-005` through `TASK-015`, `TASK-024`, and corrective `TASK-031`. The [canonical roadmap](../roadmap/README.md) alone owns identity, ordering, dependencies, lifecycle vocabulary, and current status. Checklist marks here are review evidence only.

The shipped `$aquarium:aquarium-dev` skill and its linked reference own implemented workflow behavior. ADR-0008 supersedes the isolated-Codex and Dolgorae-development portions of the original design while preserving completed historical work.

## Goal

Provide an explicit development channel that exposes exact local-`main` artifacts from Aquarium, Podway, Mulgae, Gaori, and Sanho through `~/.aquarium-dev/bin` without changing production state, production tools, or the caller's selected Codex environment.

Dolgorae is not a development producer. Independent Review uses the globally installed official release and validates its exact version, executable checksum, and capabilities immediately before use. Orca Review launches Codex directly through Orca without Dolgorae.

## Success Criteria

- `$aquarium:aquarium-dev` diagnoses and enrolls one named canonical checkout without repository-local Aquarium state.
- All development metadata and artifacts live below `~/.aquarium-dev`; `~/.aquarium` remains production-only.
- Every successful canonical local-`main` build publishes one immutable exact-SHA generation and atomically advances its current selector.
- Executable producers are exposed through stable `~/.aquarium-dev/bin` indirections backed by one atomic generation selector.
- `aquarium-dev <tool> [args...]` admits only supported executable producers, resolves them through that directory without global fallback, and otherwise inherits the caller's environment, including `CODEX_HOME`.
- Aquarium does not create or own a Codex home, authentication, plugin installation, or MCP configuration for the development channel.
- Dolgorae is absent from producer identity, enrollment, artifact, selector, resolver, and launcher state.
- Development evidence remains distinct from stable installation, release, distribution, and release-QA evidence.

## Non-Goals

- This epic does not own external producer build implementations or releases.
- It does not discover repositories, enroll worktrees implicitly, or select a canonical checkout without approval.
- It does not configure Codex, authenticate users, install production tools, publish releases, or replace distribution gates.
- It does not delete preserved production audit records or legacy Codex data merely because an older development design referenced them.

## Current System Approach

### Explicit Enrollment

Invocation diagnoses repository identity, branch, clean committed state, producer support, enrollment, hook ownership, build prerequisites, current generation, and executable selector before proposing effects. Enrollment, hook installation, checkout transfer or same-checkout legacy-path migration, build, and launcher installation each have a separate approval boundary.

Each supported project has at most one canonical checkout. Approved re-enrollment transfers or migrates only the exact recorded Aquarium-owned hook block. Foreign hook bytes and executable mode are preserved, and failure restores all touched files.

### Host-Local Layout

All development state is rooted at `~/.aquarium-dev/`:

- `enrollments/` records one canonical checkout per supported producer;
- `artifacts/` contains immutable exact-SHA generations;
- `current/` atomically selects one validated generation per project;
- `bin/` stably resolves each executable producer through its atomic current generation;
- `locks/`, `requests/`, and `diagnostics/` support bounded publication and recovery.

The separately approved launcher is installed at `~/.local/bin/aquarium-dev`. It preserves the caller's environment while changing only the child PATH and exact executable selection. There is no development Codex home and no Aquarium-owned authentication, plugin, or MCP configuration.

### Producer and Publication Contract

Every enrolled repository owns two common Make interfaces:

- `make aquarium-dev-describe` performs no mutation and emits the versioned project description.
- `make aquarium-dev-build AQUARIUM_DEV_OUTPUT=<absolute-empty-directory>` builds committed bytes into the supplied staging directory and emits the versioned exact-SHA manifest.

The manager validates project identity, canonical Git root, local `main`, clean exact HEAD, version, output containment, artifact kind, canonical checksum, and manifest consistency. It builds from an isolated copy of the admitted commit, promotes a completed generation immutably, validates the stable executable indirection, and advances one current selector atomically. Executable consumers hold shared generation leases through process exit, so cleanup defers while old bytes are in use; plugin generations remain retained until their consumer path is lease-aware. Failures preserve the previously selected generation and write bounded diagnostics.

## Historical Tasks and Corrective Ownership

| Task | Outcome |
| --- | --- |
| `TASK-005` | Proved the original host, hook, locking, atomicity, and isolated-runtime assumptions. |
| `TASK-006` | Froze the original shared contract. The root and Codex portions are superseded by `TASK-031`. |
| `TASK-007` | Implemented explicit enrollment and safe hook lifecycle. |
| `TASK-008` | Implemented exact-main build scheduling and atomic publication. |
| `TASK-009` | Implemented the original resolver and lease model, simplified by `TASK-031`. |
| `TASK-010` | Implemented the original isolated Codex environment, superseded by `TASK-031`. |
| `TASK-024` | Implemented the historical Dolgorae producer path, removed by `TASK-031`. |
| `TASK-031` | Separates development and production roots, removes Codex ownership and Dolgorae production, adds uniform bin selection and launcher behavior, and removes Dolgorae coupling from Orca Review. |
| `TASK-011` through `TASK-014` | Integrate Podway, Mulgae, Gaori, and Sanho producers. |
| `TASK-015` | Cold-validates the complete corrected development channel. |

## TASK-031: Separate Development and Production Environments

### Do

- [x] Rename the public skill, CLI module, fixtures, tests, and documentation from `dev-aquarium` to `aquarium-dev`.
- [x] Move the default development root from `~/.aquarium` to `~/.aquarium-dev`.
- [x] Publish executable producers through stable `~/.aquarium-dev/bin/<project-id>` indirections backed by atomic current selectors.
- [x] Add a separately approved `~/.local/bin/aquarium-dev` launcher that inherits the caller's environment and prepends only the development bin directory.
- [x] Remove isolated Codex configuration, authentication, plugin installation, and MCP ownership from the manager and public workflow.
- [x] Remove Dolgorae from supported producer identities, resolution, launch, runtime-copy, diagnosis, and cleanup paths.
- [x] Route Independent Review to the globally installed official Dolgorae v0.1.0 executable with immediate identity and capability checks.
- [x] Route Orca Review directly to one fresh Orca-managed Codex worker without Dolgorae discovery, capture, launch, or settlement.
- [x] Preserve historical decisions by superseding ADR-0007 with ADR-0008 instead of rewriting the old record.
- [x] Pass focused unit, structural, and complete repository gates.
- [x] Install and verify the official global Dolgorae release and the user-local launcher on the approved host.
- [ ] Migrate Aquarium enrollment and artifacts only from a clean committed candidate capable of reproducing the corrected contract.

### Do Not

- [x] Do not modify tracked Dolgorae source.
- [x] Do not create a `$use-dolgorae` skill or another Aquarium-owned Dolgorae runtime.
- [x] Do not delete Dolgorae Application Support audit records or legacy `~/.aquarium/codex` data during migration.
- [x] Do not commit, push, release, or activate production Aquarium as part of this task without separate authority.

## Remaining Producer Integration

For each of Podway, Mulgae, Gaori, and Sanho:

- [ ] accept one exact clean local-`main` handoff with both producer target outputs, checksum proof, embedded runtime identity, and focused tests;
- [ ] verify canonical enrollment, first build, post-commit update, direct PATH selection, and the relevant Aquarium consumer;
- [ ] preserve the producer's native runtime, policy, evidence, and independent release ownership;
- [ ] reject development artifacts as official distribution evidence.

## TASK-015: Cold Validation

- [ ] Start from clean temporary user and repository state with no development enrollment.
- [ ] Enroll Aquarium and the four external producers only through the skill workflow.
- [ ] Prove initial build, exact-SHA isolation, subsequent update, atomic current advancement, stable bin resolution, and superseded-generation cleanup.
- [ ] Prove same-checkout idempotency and approved re-enrollment.
- [ ] Prove missing producer, rejected manifest, build failure, missing checkout, corrupt artifact, and selector-drift diagnostics.
- [ ] Prove the launcher preserves caller environment and selects only enrolled development executables.
- [ ] Prove Dolgorae remains globally resolved for Independent Review, absent from Orca Review, and absent from all development state.
- [ ] Run focused suites and the complete applicable Aquarium gate against the final exact candidates.

## Epic Acceptance

- [ ] `TASK-011` through `TASK-015` and `TASK-031` are `Completed` in the canonical roadmap.
- [ ] Cold validation uses final exact Aquarium and producer candidates after all accepted changes.
- [ ] Current specs, architecture, ADRs, implementation tips, operations, public documentation, privacy terms, and executable validation agree on the corrected contract.
- [ ] Development-contract evidence remains explicitly separate from production installation, stable release, and distribution evidence.
