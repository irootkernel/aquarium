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
| EPIC-002 | Build the Aquarium development environment | Blocked |
| EPIC-003 | Activate Dolgorae-backed Reviews | Completed |
| EPIC-004 | Release Aquarium v0.1.12 | Completed |
| EPIC-005 | Adopt Dolgorae v0.1.0 | Completed |
| EPIC-006 | Adopt Podway v0.2.7 | Completed |

## EPIC-001: Adopt Podway v0.2.6

**Status:** `Completed`

Adopt the released Podway v0.2.6 runtime contract, preset-informed canonical Procedures, preserved local Procedure customization, exact official-artifact qualification, and complete predecessor-acceptance validation.

Podway owns its v0.2.6 implementation, release QA, distribution gate, and publication. Aquarium may consume that result only after it obtains the exact Podway release commit and independently verifies the official artifact; an Aquarium consumer claim alone cannot complete the dependency.

**Canonical Outcomes:** [Tool integrations](../specs/tool-integrations.md), [Local interfaces](../specs/local-interfaces.md), [Changing Procedures](../implementation-tips/changing-procedures.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-016 | Align the Podway v0.2.6 runtime contract | Adopt the released observation, lifecycle, evidence-read, skill, and daemon-readiness interfaces. | Completed | External Podway v0.2.6 release |
| TASK-017 | Reauthor the delivery Procedures | Rebuild the task, goal, and validation Procedures from the applicable v0.2.6 preset patterns. | Completed | TASK-016 |
| TASK-018 | Reauthor the analysis Procedures | Rebuild the design and war-room Procedures from the applicable v0.2.6 analysis and bug-fix patterns. | Completed | TASK-016 |
| TASK-001 | Preserve local Procedure customization | Accept Podway-valid same-ID local Procedure content and replace it only after an explicit reviewed choice. | Completed | TASK-017, TASK-018 |
| TASK-002 | Qualify the official Podway v0.2.6 release | Independently verify the exact released artifact against the final canonical Procedures and runtime paths. | Completed | TASK-001, TASK-016, TASK-017, TASK-018; external Podway v0.2.6 release |
| TASK-003 | Validate the complete Aquarium v0.1.12 candidate | Reconcile every predecessor acceptance requirement and prove the final exact development candidate. | Completed | TASK-001, TASK-002, TASK-016, TASK-017, TASK-018 |

## EPIC-002: Build the Aquarium Development Environment

**Status:** `Blocked`

Build the `aquarium-dev` development channel planned for v0.1.14 so Aquarium and its explicitly enrolled tool producers can exercise exact local-main artifacts early, discover cross-project integration failures before release preparation, and keep production tools and state separate.

The Aquarium-owned runtime is being corrected by `TASK-031`: all development state moves to `~/.aquarium-dev`, executable producers are preferred through its `bin` directory, each absent development command falls back independently to the caller's global PATH, and the launcher inherits the caller's environment. Dolgorae is an enrollable producer with no exception: if neither development nor global binary exists, its command fails closed and requests dev-setup. Podway, Mulgae, Gaori, and Dolgorae are required global binaries; Sanho is explicitly optional. Further progress requires exact clean local-`main` producer handoffs from Podway, Mulgae, Gaori, Sanho, and Dolgorae. Each handoff must name the producer commit SHA and include both Make-target outputs, the artifact checksum, embedded runtime version and SHA diagnostics, and focused producer tests. A local `main` ahead of its remote is acceptable development evidence; a dirty checkout is not.

**Detailed SOT:** [`TODO-AQUARIUM-DEV.md`](../todo/TODO-AQUARIUM-DEV.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-005 | Prove development-channel feasibility | Validate host locks, hook coexistence, atomic publication, and the original isolated runtime assumptions before implementation. | Completed | TASK-004 |
| TASK-006 | Define the shared development contract | Freeze producer, artifact, enrollment, resolver, version, and failure contracts. | Completed | TASK-005 |
| TASK-007 | Implement enrollment and hook lifecycle | Add the explicit skill workflow, canonical checkout enrollment, re-enrollment, and hook ownership transfer. | Completed | TASK-006 |
| TASK-008 | Implement build scheduling and publication | Build exact local-main candidates, serialize publishers, and atomically advance the current artifact. | Completed | TASK-006 |
| TASK-009 | Implement resolution, leases, and cleanup | Implement the original generation-resolution and cleanup contract, later simplified by TASK-031. | Completed | TASK-006, TASK-008 |
| TASK-010 | Isolate Aquarium and Codex development runtime | Implement the original isolated Codex environment, later superseded by TASK-031. | Completed | TASK-007, TASK-008, TASK-009 |
| TASK-011 | Integrate Podway | Add and verify Podway's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-012 | Integrate Mulgae | Add and verify Mulgae's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-013 | Integrate Gaori | Add and verify Gaori's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-014 | Integrate Sanho | Add and verify Sanho's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-024 | Integrate Dolgorae | Complete the historical development-producer integration, superseded for current operation by TASK-031. | Completed | TASK-010; external Dolgorae TASK-035 |
| TASK-031 | Separate development and production environments | Rename the channel and root to `aquarium-dev`, inherit the caller's environment, prefer executable producers through one bin directory with per-tool global fallback, admit optional Dolgorae enrollment without requiring it, and decouple Orca Review from Dolgorae. | In Progress | TASK-010, TASK-028 |
| TASK-015 | Cold-validate the integrated environment | Prove setup, update, failure, concurrency, launcher, and cross-project behavior from clean state. | Planned | TASK-011, TASK-012, TASK-013, TASK-014, TASK-031 |

## EPIC-003: Activate Dolgorae-backed Reviews

**Status:** `Completed`

Adopt and activate the Aquarium-side contract for immutable Dolgorae-backed independent review. The historical implementation also coupled `orca-review` target capture and settlement to Dolgorae while preserving Orca lifecycle ownership. `TASK-031` supersedes that Orca-side coupling: Independent Review retains the complete Dolgorae guarantees, while Orca Review uses Orca's native Codex worker lifecycle and a bounded exact-Git-target inspector.

EPIC-003 completed against the then-current exact Dolgorae development generation and did not depend on EPIC-002's unfinished original producer tasks. Current production execution is governed by EPIC-005 and the global-release correction in `TASK-031`.

**Canonical Outcomes:** [Dolgorae review contract](../../plugins/aquarium/references/dolgorae-review-contract.md), [common review contract](../../plugins/aquarium/references/review-contract.md), [development-channel contract](../../plugins/aquarium/skills/aquarium-dev/references/development-contract.md), [independent-review workflow](../../plugins/aquarium/skills/independent-review/SKILL.md), [Orca review workflow](../../plugins/aquarium/skills/orca-review/SKILL.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-019 | Adopt the Dolgorae candidate contract | Freeze generation acquisition, identity, capability, schema, bounds, guarded launch, and pre-launch revalidation contracts. | Completed | TASK-024 |
| TASK-020 | Adopt immutable review targets | Implement the six captured source scopes, immutable manifests, source identity, safety boundaries, and owner-bound settlement identities. | Completed | TASK-019 |
| TASK-021 | Implement Dolgorae independent-review supervision | Run one fresh Codex Reviewer through Dolgorae without Orca objects and settle only from authoritative terminal evidence. | Completed | TASK-020 |
| TASK-022 | Preserve Orca review and align Mulgae semantics | Historically retained Orca lifecycle ownership with Dolgorae capture; TASK-031 supersedes that capture coupling while preserving shared target semantics. | Completed | TASK-020 |
| TASK-023 | Activate and validate the exact candidate | Bind one exact enrolled Dolgorae generation, run the complete E2E campaign, and return the candidate-bound Completed Confirm. | Completed | TASK-021, TASK-022; external Dolgorae TASK-015 |

## EPIC-004: Release Aquarium v0.1.12

**Status:** `Completed`

Publish Aquarium v0.1.12 from the exact candidate produced by EPIC-001 after a new complete release-QA pass, the selected local release gate, ordered publication, and exact remote verification.

EPIC-004 depends on the completed EPIC-001 adoption result. Release QA owns release readiness and may return defects to their canonical owners without reopening adoption merely because publication remains incomplete.

**Canonical Outcomes:** [v0.1.12 release notes](../../CHANGELOG.md), [release workflow contract](../specs/workflow-contracts.md), [local exact-candidate verification](../architecture-decision-records/0006-local-exact-candidate-verification.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-004 | Release Aquarium v0.1.12 | Complete release QA, publication, and exact remote verification. | Completed | TASK-003 |

## EPIC-005: Adopt Dolgorae v0.1.0

**Status:** `Completed`

Adopt the exact official Dolgorae v0.1.0 Apple Silicon release as Aquarium's stable Independent Review runtime. Stable admission binds the published source commit, archive, executable checksum, machine version, capabilities, and setup approval boundaries without vendoring Dolgorae or requiring an end-user source checkout. `TASK-031` makes the globally installed release the sole current Dolgorae runtime, removes Aquarium's private execution copy, and removes Dolgorae from Orca Review.

This adoption succeeds EPIC-003 without reopening it and does not complete the unrelated Podway, Mulgae, Gaori, or Sanho producer work still blocking EPIC-002.

**Canonical Outcomes:** [Dolgorae review contract](../../plugins/aquarium/references/dolgorae-review-contract.md), [tool integrations](../specs/tool-integrations.md), [local interfaces](../specs/local-interfaces.md), [development setup](../../plugins/aquarium/skills/dev-setup/SKILL.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-025 | Adopt the official Dolgorae v0.1.0 distribution | Pin the release tag, source commit, platform, archive, executable checksum, maturity, and ownership boundaries. | Completed | External Dolgorae v0.1.0 release |
| TASK-026 | Implement stable Dolgorae admission and setup | Add exact stable inspection, bundle selection, and fail-closed identity checks; private execution is later removed by TASK-031. | Completed | TASK-025 |
| TASK-027 | Activate stable Dolgorae-backed reviews | Historically moved both review paths to the pinned stable release; TASK-031 retains it only for Independent Review and restores native Orca Codex execution. | Completed | TASK-026; EPIC-003 |
| TASK-028 | Qualify and close stable Dolgorae adoption | Verify the official artifact and complete code, workflow, documentation, privacy, and regression acceptance. | Completed | TASK-027 |

## EPIC-006: Adopt Podway v0.2.7

**Status:** `Completed`

Adopt the official Podway v0.2.7 release as Aquarium's minimum stable runtime, retain the existing Procedure v2 lifecycle contract, and qualify the new exact-workspace removal boundary without granting Aquarium setup or managed workflows automatic deletion authority.

Podway owns its release, distribution, workspace-removal implementation, and source-distributed `use-podway` lifecycle guidance. Aquarium independently verifies the official artifact and installs or invokes the paired skill only through its existing explicit approval boundaries. This adoption does not satisfy the separate Podway development-producer handoff required by `EPIC-002` and `TASK-011`.

**Canonical Outcomes:** [Tool integrations](../specs/tool-integrations.md), [Local interfaces](../specs/local-interfaces.md), [Podway integration](../../plugins/aquarium/references/podway-integration.md), [Changing Procedures](../implementation-tips/changing-procedures.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-029 | Align the Podway v0.2.7 support contract | Raise the stable runtime floor, preserve same-tag CLI, daemon, and skill identity, and define the explicit workspace-removal safety boundary. | Completed | External Podway v0.2.7 release |
| TASK-030 | Qualify and close Podway v0.2.7 adoption | Verify the official artifact against canonical Procedures, existing lifecycle seams, fenced workspace removal, replay convergence, and final exact Aquarium candidates. | Completed | TASK-029 |
