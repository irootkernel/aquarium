# Aquarium Roadmap

This file alone owns Aquarium's adopted epic and task identity, ordering, dependencies, lifecycle vocabulary, and current delivery status.

## Identity Contract

- Epic IDs match `EPIC-[0-9]{3,}` and task IDs match `TASK-[0-9]{3,}`.
- Epic and task sequences are independent and monotonic in this roadmap namespace, including archives and migration records.
- Task numbering never restarts per epic, and no number is reused after deletion, deferral, completion, archival, or migration.
- IDs do not encode execution order; the task table and explicit dependencies define order.
- New IDs use the greatest number ever observed for the same kind in this namespace plus one.

## Lifecycle

| Status | Meaning |
| --- | --- |
| Planned | Adopted but implementation has not started |
| In Progress | Implementation is active |
| In Review | Implementation is complete and acceptance evidence is under review |
| Completed | The work unit passed its explicit acceptance and closeout |
| Deferred | Adopted work is intentionally postponed with a re-entry condition |
| Blocked | Progress cannot continue until a named condition changes |

Epic status is independent of child task status. Completing every child does not complete an epic without explicit epic acceptance.

## Epic Summary

| Epic | Title | Status |
| --- | --- | --- |
| EPIC-001 | Release Aquarium v0.1.12 | Planned |

## EPIC-001: Release Aquarium v0.1.12

**Status:** `Planned`

Deliver Aquarium v0.1.12 with explicit project-owned Procedure support, independently qualified Podway v0.2.6 compatibility, complete Sudal integration-request validation, and verified publication.

Podway owns its v0.2.6 implementation, release QA, distribution gate, and publication. Aquarium may consume that result only after it obtains the exact Podway release commit and independently verifies the official artifact; an Aquarium consumer claim alone cannot complete the dependency.

| Task | Title | Status | Depends On |
| --- | --- | --- | --- |
| TASK-001 | Support project-owned Procedure customization | Planned | None |
| TASK-002 | Qualify the official Podway v0.2.6 release | Planned | External Podway v0.2.6 release |
| TASK-003 | Validate the complete Aquarium v0.1.12 candidate | Planned | TASK-001, TASK-002 |
| TASK-004 | Release Aquarium v0.1.12 | Planned | TASK-003 |

### TASK-001 Acceptance

- Provide an explicit, separately approved transition from Aquarium-managed canonical mode to project-owned Procedure mode; never infer ownership from an arbitrary byte mismatch.
- Record non-secret source provenance and current digest, validate the selected Aquarium workflow's required nodes, items, types, routes, evidence handoffs, lifecycle ownership, and terminal behavior, and permit compatible project-specific changes outside that interface.
- Keep exact byte equality for Aquarium-managed canonical files, never overwrite project-owned files, and present reviewable base/current/incoming evidence before an approved upstream merge or replacement.
- Cover canonical, unexplained mismatch, compatible customization, incompatible workflow, direct-Podway-only validity, no-overwrite, and upstream-update scenarios with focused tests and repository-standard verification.

### TASK-002 Acceptance

- Obtain the exact Podway release commit and independent evidence that its complete release/distribution gate passed for v0.2.6; development-branch tests alone are insufficient.
- Verify the official Apple Silicon archive against its published checksum and run `PODWAY_BIN=<absolute-path> make test-podway-compat` against the extracted exact binary.
- Confirm the released list-scale declaration and runtime enforcement, strict unknown-field rejection, phase-aware daemon installation readiness, explicit verified-readiness state, and state-preserving retry behavior required by Aquarium's integration.
- Keep all Podway source changes, release QA, tags, assets, and publication in the Podway repository's ownership boundary.

### TASK-003 Acceptance

- Map every Aquarium-owned requirement from the two Sudal integration requests to current code, tests, and exact external-release evidence, distinguishing already satisfied behavior from remaining gaps without creating retroactive Completed tasks.
- Require stable Podway v0.2.6 through v0.2.x, canonical Procedure validation with the exact released binary, supported project-owned Procedure behavior, the canonical Ouroboros 0.51.x isolated Codex launcher, and a single full-setup Codex artifact mutation.
- Correct every confirmed Aquarium-owned release blocker, update the exact owning specification and release-note surfaces, and run focused checks plus the complete applicable Aquarium development gate.
- Require the latest exact Aquarium candidate after all accepted changes; stale request analysis or cross-repository claims cannot satisfy acceptance.

### TASK-004 Acceptance

- Use `$aquarium:release-handler` and select `full` or `light` under the repository release policy when execution begins; preserve every separate approval boundary.
- Reconcile all material changes with the open v0.1.12 CHANGELOG section, commit the exact preparation, and run a fresh release QA pass against the resulting clean candidate.
- Create the exact `[REL] Release v0.1.12` commit, push `main`, create and push the annotated tag, publish the GitHub Release, and verify remote main, the peeled tag, and the Release all resolve to the intended commit.
- Treat opening the next Unreleased cycle as a separate non-release action after publication.

The epic is accepted only after all four tasks are `Completed` and an explicit epic-level review confirms the published v0.1.12 outcome. Child completion alone does not change the epic status.
