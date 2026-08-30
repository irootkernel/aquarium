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

Build the `dev-aquarium` development channel planned for v0.1.14 so Aquarium and its explicitly enrolled tool producers can exercise exact local-main artifacts early, discover cross-project integration failures before release preparation, and preserve stable global tools when no project is enrolled.

The Aquarium-owned runtime is complete. Further progress requires exact clean local-`main` producer handoffs from Podway, Mulgae, Gaori, Sanho, and the separately adopted Dolgorae producer. Each handoff must name the producer commit SHA and include both Make-target outputs, the artifact checksum, embedded runtime version and SHA diagnostics, and focused producer tests. A local `main` ahead of its remote is acceptable development evidence; a dirty checkout is not. The original four integrations and their cold validation remain blocked on their own handoffs; Dolgorae integration may complete independently once external Dolgorae `TASK-035` delivers its producer.

**Detailed SOT:** [`TODO-DEV-AQUARIUM.md`](../todo/TODO-DEV-AQUARIUM.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-005 | Prove development-channel feasibility | Validate host locks, hook coexistence, atomic publication, and isolated Codex operation before implementation. | Completed | TASK-004 |
| TASK-006 | Define the shared development contract | Freeze producer, artifact, enrollment, resolver, version, and failure contracts. | Completed | TASK-005 |
| TASK-007 | Implement enrollment and hook lifecycle | Add the explicit skill workflow, canonical checkout enrollment, re-enrollment, and hook ownership transfer. | Completed | TASK-006 |
| TASK-008 | Implement build scheduling and publication | Build exact local-main candidates, serialize publishers, and atomically advance the current artifact. | Completed | TASK-006 |
| TASK-009 | Implement resolution, leases, and cleanup | Resolve development versus stable tools, pin invocations, protect active artifacts, and remove superseded binaries. | Completed | TASK-006, TASK-008 |
| TASK-010 | Isolate Aquarium and Codex development runtime | Install the development plugin, paired skills, MCP configuration, and separate Codex home under the shared contract. | Completed | TASK-007, TASK-008, TASK-009 |
| TASK-011 | Integrate Podway | Add and verify Podway's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-012 | Integrate Mulgae | Add and verify Mulgae's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-013 | Integrate Gaori | Add and verify Gaori's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-014 | Integrate Sanho | Add and verify Sanho's shared producer contract and development resolution. | Planned | TASK-010 |
| TASK-024 | Integrate Dolgorae | Add and verify Dolgorae's executable producer, exact-generation resolution, guarded launch, and isolated Codex visibility. | Completed | TASK-010; external Dolgorae TASK-035 |
| TASK-015 | Cold-validate the integrated environment | Prove setup, update, fallback, failure, concurrency, and cross-project behavior from clean state. | Planned | TASK-011, TASK-012, TASK-013, TASK-014, TASK-024 |

## EPIC-003: Activate Dolgorae-backed Reviews

**Status:** `Completed`

Adopt and activate the Aquarium-side contract for immutable Dolgorae-backed independent review. The design preserves Orca supervision for `orca-review`, aligns Mulgae only on common source-scope and target-identity semantics, and requires exact candidate, capture, lifecycle, and settlement evidence before runtime activation.

EPIC-003 does not depend on completing EPIC-002 or its unfinished original producer tasks. It depends only on `TASK-024`, which extends the completed `TASK-010` foundation with an exact Dolgorae development generation. External Dolgorae `TASK-015` remains the checked runtime-contract prerequisite, while external `TASK-035` owns producer delivery through `TASK-024`.

**Canonical Outcomes:** [Dolgorae review contract](../../plugins/aquarium/references/dolgorae-review-contract.md), [common review contract](../../plugins/aquarium/references/review-contract.md), [development-channel contract](../../plugins/aquarium/skills/dev-aquarium/references/development-contract.md), [independent-review workflow](../../plugins/aquarium/skills/independent-review/SKILL.md), [Orca review workflow](../../plugins/aquarium/skills/orca-review/SKILL.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-019 | Adopt the Dolgorae candidate contract | Freeze generation acquisition, identity, capability, schema, bounds, guarded launch, and pre-launch revalidation contracts. | Completed | TASK-024 |
| TASK-020 | Adopt immutable review targets | Implement the six captured source scopes, immutable manifests, source identity, safety boundaries, and owner-bound settlement identities. | Completed | TASK-019 |
| TASK-021 | Implement Dolgorae independent-review supervision | Run one fresh Codex Reviewer through Dolgorae without Orca objects and settle only from authoritative terminal evidence. | Completed | TASK-020 |
| TASK-022 | Preserve Orca review and align Mulgae semantics | Retain Orca lifecycle ownership and prove common target semantics across Orca and Mulgae without lifecycle coupling. | Completed | TASK-020 |
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

Adopt the exact official Dolgorae v0.1.0 Apple Silicon release as Aquarium's stable review runtime while retaining the development producer for maintainer testing. Stable admission binds the published source commit, archive, executable checksum, machine version, capabilities, immutable execution copy, and setup approval boundaries without vendoring Dolgorae or requiring an end-user source checkout.

This adoption succeeds EPIC-003 without reopening it and does not complete the unrelated Podway, Mulgae, Gaori, or Sanho producer work still blocking EPIC-002.

**Canonical Outcomes:** [Dolgorae review contract](../../plugins/aquarium/references/dolgorae-review-contract.md), [tool integrations](../specs/tool-integrations.md), [local interfaces](../specs/local-interfaces.md), [development setup](../../plugins/aquarium/skills/dev-setup/SKILL.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-025 | Adopt the official Dolgorae v0.1.0 distribution | Pin the release tag, source commit, platform, archive, executable checksum, maturity, and ownership boundaries. | Completed | External Dolgorae v0.1.0 release |
| TASK-026 | Implement stable Dolgorae admission and setup | Add exact stable inspection, bundle selection, guarded private execution, and fail-closed identity checks. | Completed | TASK-025 |
| TASK-027 | Activate stable Dolgorae-backed reviews | Move Independent Review and Orca Review production paths from the development generation to the pinned stable guard. | Completed | TASK-026; EPIC-003 |
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
