# Aquarium Roadmap

This file alone owns Aquarium's adopted epic and task identity, ordering, dependencies, lifecycle vocabulary, and current delivery status. Linked work dossiers own detailed scope and acceptance criteria without becoming a second lifecycle authority.

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
| EPIC-001 | Adopt Podway v0.2.6 | Completed |
| EPIC-002 | Build the Aquarium development environment | Planned |
| EPIC-003 | Introduce Dolgorae | Planned |
| EPIC-004 | Release Aquarium v0.1.12 | Planned |

## EPIC-001: Adopt Podway v0.2.6

**Status:** `Completed`

Adopt the released Podway v0.2.6 runtime contract, preset-informed canonical Procedures, preserved local Procedure customization, exact official-artifact qualification, and complete predecessor-acceptance validation.

Podway owns its v0.2.6 implementation, release QA, distribution gate, and publication. Aquarium may consume that result only after it obtains the exact Podway release commit and independently verifies the official artifact; an Aquarium consumer claim alone cannot complete the dependency.

**Canonical Outcomes:** [Tool integrations](../specs/tool-integrations.md), [Local interfaces](../specs/local-interfaces.md), [Changing Procedures](../implementation-tips/changing-procedures.md)

**Design Gate impact:** `Not required` — Member-task acceptance owns every identified local requirement. Focused task checks, exact external-artifact and development qualification, and epic validation verify those requirements and outcomes without defining another epic invariant.

| Task | Title | Summary | Status | Depends On | Design Gate impact | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| TASK-016 | Align the Podway v0.2.6 runtime contract | Adopt the released observation, lifecycle, evidence-read, skill, and daemon-readiness interfaces. | Completed | External Podway v0.2.6 release | Not required | Task acceptance owns its versioned runtime and inspection contracts, and the task's consumer, fixture, and focused interface checks will verify them without defining an additional gate invariant. |
| TASK-017 | Reauthor the delivery Procedures | Rebuild the task, goal, and validation Procedures from the applicable v0.2.6 preset patterns. | Completed | TASK-016 | Not required | Task acceptance owns its delivery Procedure contracts, and Podway authoring checks and focused delivery-path scenarios will verify them without defining an additional gate invariant. |
| TASK-018 | Reauthor the analysis Procedures | Rebuild the design and war-room Procedures from the applicable v0.2.6 analysis and bug-fix patterns. | Completed | TASK-016 | Not required | Task acceptance owns its analysis Procedure contracts, and Podway authoring checks and focused design and war-room scenarios will verify them without defining an additional gate invariant. |
| TASK-001 | Preserve local Procedure customization | Accept Podway-valid same-ID local Procedure content and replace it only after an explicit reviewed choice. | Completed | TASK-017, TASK-018 | Not required | Task acceptance owns its local-customization and no-overwrite contracts, and focused setup and update scenarios will verify them without defining an additional gate invariant. |
| TASK-002 | Qualify the official Podway v0.2.6 release | Independently verify the exact released artifact against the final canonical Procedures and runtime paths. | Completed | TASK-001, TASK-016, TASK-017, TASK-018; external Podway v0.2.6 release | Not required | Task acceptance owns its official-artifact and bounded-daemon qualification requirements, and the exact external-artifact gate will verify them without defining an additional Design Gate invariant. |
| TASK-003 | Validate the complete Aquarium v0.1.12 candidate | Reconcile every predecessor acceptance requirement and prove the final exact development candidate. | Completed | TASK-001, TASK-002, TASK-016, TASK-017, TASK-018 | Not required | Task acceptance owns predecessor reconciliation and current-candidate requirements, and the development gate will verify them without defining a new invariant. Any newly discovered eligible seam invariant must be reclassified as Pending before implementation. |

## EPIC-002: Build the Aquarium Development Environment

**Status:** `Planned`

Build the `dev-aquarium` development channel planned for v0.1.13 so Aquarium, Podway, Mulgae, Gaori, and Sanho can exercise exact local-main artifacts early, discover cross-project integration failures before release preparation, and preserve stable global tools when no project is enrolled.

This epic begins after the v0.1.12 publication task in EPIC-004. It does not open the v0.1.13 CHANGELOG cycle or present the planned behavior as shipped.

**Detailed SOT:** [`TODO-DEV-AQUARIUM.md`](../todo/TODO-DEV-AQUARIUM.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-005 | Prove development-channel feasibility | Validate host locks, hook coexistence, atomic publication, and isolated Codex operation before implementation. | Planned | TASK-004 |
| TASK-006 | Define the shared development contract | Freeze producer, artifact, enrollment, resolver, version, and failure contracts. | Planned | TASK-005 |
| TASK-007 | Implement enrollment and hook lifecycle | Add the explicit skill workflow, canonical checkout enrollment, re-enrollment, and hook ownership transfer. | Planned | TASK-006 |
| TASK-008 | Implement build scheduling and publication | Build exact local-main candidates, serialize publishers, and atomically advance the current artifact. | Planned | TASK-006 |
| TASK-009 | Implement resolution, leases, and cleanup | Resolve development versus stable tools, pin invocations, protect active artifacts, and remove superseded binaries. | Planned | TASK-006, TASK-008 |
| TASK-010 | Isolate Aquarium and Codex development runtime | Install the development plugin, paired skills, MCP configuration, and separate Codex home under the shared contract. | Planned | TASK-007, TASK-008, TASK-009 |
| TASK-011 | Integrate Podway | Add and verify Podway's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-012 | Integrate Mulgae | Add and verify Mulgae's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-013 | Integrate Gaori | Add and verify Gaori's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-014 | Integrate Sanho | Add and verify Sanho's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-015 | Cold-validate the integrated environment | Prove setup, update, fallback, failure, concurrency, and cross-project behavior from clean state. | Planned | TASK-011, TASK-012, TASK-013, TASK-014 |

## EPIC-003: Introduce Dolgorae

**Status:** `Planned`

Introduce Dolgorae as the second v0.1.13 development epic and the next Aquarium-managed package and handler after the shared development environment is established. This placeholder reserves the epic identity and dependency only; detailed scope, SOT, task IDs, and acceptance criteria have not yet been adopted.

EPIC-003 depends on EPIC-002. No child task identity or implementation authority is allocated by this placeholder.

## EPIC-004: Release Aquarium v0.1.12

**Status:** `Planned`

Publish Aquarium v0.1.12 from the exact candidate produced by EPIC-001 after a new complete release-QA pass, the selected local release gate, ordered publication, and exact remote verification.

EPIC-004 depends on the completed EPIC-001 adoption result. Release QA owns release readiness and may return defects to their canonical owners without reopening adoption merely because publication remains incomplete.

**Detailed SOT:** [`TODO-RELEASE-v0-1-12.md`](../todo/TODO-RELEASE-v0-1-12.md)

**Design Gate impact:** `Not required` — TASK-004 owns the release and publication contract, while release QA and ordered publication observation verify network- and remote-state-dependent outcomes outside the Design Gate contract.

| Task | Title | Summary | Status | Depends On | Design Gate impact | Reason |
| --- | --- | --- | --- | --- | --- | --- |
| TASK-004 | Release Aquarium v0.1.12 | Complete release QA, publication, and exact remote verification. | Planned | TASK-003 | Not required | Task acceptance owns its publication requirements, while release QA and ordered publication observation verify network- and remote-state-dependent outcomes outside the Design Gate contract. |
