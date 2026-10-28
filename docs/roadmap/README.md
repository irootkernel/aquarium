# Aquarium Roadmap

This file alone owns Aquarium's adopted epic and task identity, ordering, dependencies, lifecycle vocabulary, and current delivery status. Linked work dossiers own detailed scope and acceptance criteria without becoming a second lifecycle authority.

## Identity Contract

- Epic IDs match `EPIC-[0-9]{3,}` and task IDs match `TASK-[0-9]{3,}`.
- Epic and task sequences are independent and monotonic in this roadmap namespace, including archives and migration records.
- Task numbering never restarts per epic, and no number is reused after deletion, deferral, completion, archival, or migration.
- IDs do not encode execution order; the task table and explicit dependencies define order.
- New IDs use the greatest number ever observed for the same kind in this namespace plus one.
- `EPIC-000` is the reserved standing home for independent tasks; it is outside the numbered delivery-epic sequence.

## Lifecycle

| Status | Meaning |
| --- | --- |
| Planned | Adopted but implementation has not started |
| In Progress | Implementation is active |
| In Review | Implementation is complete and acceptance evidence is under review |
| Completed | The work unit passed its explicit acceptance and closeout |
| Deferred | Adopted work is intentionally postponed with a re-entry condition |
| Cancelled | Adopted work is withdrawn; its ID and decision remain recorded, but completion is no longer required |
| Blocked | Progress cannot continue until a named condition changes |

Epic status is independent of child task status. Completing every child does not complete an epic without explicit epic acceptance.
`EPIC-000` stays `In Progress` and is never closed. Each member task has its own acceptance and lifecycle.

## Epic Summary

| Epic | Title | Status |
| --- | --- | --- |
| EPIC-000 | Independent tasks | In Progress |
| EPIC-001 | Adopt Podway v0.2.6 | Completed |
| EPIC-002 | Build the Aquarium development environment | Cancelled |
| EPIC-003 | Activate Dolgorae-backed Reviews | Completed |
| EPIC-004 | Release Aquarium v0.1.12 | Completed |
| EPIC-005 | Adopt Dolgorae v0.1.0 | Completed |
| EPIC-006 | Adopt Podway v0.2.7 | Completed |
| EPIC-007 | Adopt upstream document humanizers | Completed |
| EPIC-008 | Adopt Podway v0.2.8 | Completed |
| EPIC-009 | Adopt Sorage v0.1.x | Completed |
| EPIC-010 | Separate global and repository development setup | Completed |
| EPIC-011 | Harden release QA confirmation integrity | Completed |
| EPIC-012 | Modernize Aquarium Skills for GPT-6 Astra | Planned |
| EPIC-013 | Record and report production setup status | Completed |
| EPIC-014 | Align Procedure contracts and bound Low-finding convergence | Completed |
| EPIC-015 | Add intent-aware review and disable Independent Review temporarily | Completed |
| EPIC-016 | Add selectable workflow review routing | Completed |
| EPIC-017 | Add Web Pro Review | Planned |
| EPIC-018 | Correct Aquarium workflow and integration contracts | In Progress |
| EPIC-019 | Adopt Haepari VM verification for Aquarium | Completed |
| EPIC-020 | Migrate Orca review to Herdr | Completed |
| EPIC-021 | Adopt supervised agent orchestration | Completed |
| EPIC-022 | Adopt Podway v0.2.14 | Completed |
| EPIC-023 | Adopt Mulgae v0.1.25 | Completed |
| EPIC-024 | Restore native agent workflows and add manual VM release acceptance | Completed |
| EPIC-025 | Align review strategies with delivery goals | Completed |
| EPIC-026 | ADAPT: Goal-adaptive Procedure orchestration | Completed |
| EPIC-027 | Add native Epic Squad collaboration | In Progress |
| EPIC-028 | Extend Epic Squad with Herdr and mixed collaboration | Planned |
| EPIC-029 | Add directory AGENTS.md documentation indexes | Completed |
| EPIC-030 | Unify Aquarium delivery across five agent hosts | Planned |
| EPIC-031 | Adopt Coordinator, Evaluator and Executor roles in release workflows | Planned |
| EPIC-032 | Adopt Haepari across integrated tools | Planned |
| EPIC-033 | Qualify the combined environment and retire the development channel | Planned |
| EPIC-034 | Adopt Podway v0.2.15 and contract generation 2 | In Progress |

## EPIC-000: Independent Tasks

**Status:** `In Progress`

`EPIC-000` groups tasks with independent scope and acceptance. Its status stays `In Progress` even when every current task is complete. Use task workflows for its members; do not run epic-wide execution, validation, or closeout. Link any detailed scope from the task row and settle that task's dossier at task closeout.

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-076 | Implement target-specific bundle setup intent | Replace bundle v1 with v2 MCP scope lists, Sorage Project slug, and Mulgae artist intent; route and verify the selected setup scopes. [Bundle manifest](../../plugins/aquarium/skills/dev-setup-bundle/references/manifest.md). | Completed | TASK-037 |
| TASK-103 | Use worktree observation for Podway session admission | Replace routine global readiness polling with worktree observation while keeping setup diagnostics and session safeguards. [Podway integration](../../plugins/aquarium/references/podway-integration.md). | Completed | — |
| TASK-104 | Adopt Sanho v0.2.9 | Raise the supported release floor and align setup with the release-matched CLI, skill, diagnostics, and build prerequisites. [Tool catalog](../../plugins/aquarium/references/tool-catalog.md#sanho). | Completed | External Sanho v0.2.9 release |
| TASK-105 | Adopt Sorage v0.1.2 | Raise the release floor, route explicit Project Memo requests through the paired skill, align Project commands, and protect the format-1 upgrade before native diagnosis. [Tool catalog](../../plugins/aquarium/references/tool-catalog.md#sorage). | Completed | External Sorage v0.1.2 release |

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

**Status:** `Cancelled`

The remaining development-channel expansion is withdrawn in favor of the EPIC-019 -> EPIC-031 -> EPIC-032 -> EPIC-033 delivery chain. Completed tasks retain their historical acceptance. Cancellation changes the delivery plan only; installed workers, hooks, services, launchers, and `~/.aquarium-dev/` remain until the staged retirement is implemented and its host effects are explicitly authorized.

The historical objective was to build the `aquarium-dev` development channel for exact local-main integration while keeping production tools and state separate.

`TASK-031` completed the corrected Aquarium-owned runtime: all development state lives under `~/.aquarium-dev`, foreground producers are preferred through its `bin` directory with independent global fallback when absent, managed services require an exact active development generation without production fallback, and the launcher inherits the caller's environment. Dolgorae is an enrollable foreground producer with no missing-binary exception. Sanho is explicitly optional. `TASK-011` accepted Podway's exact clean local-`main` v0.2.8 handoff and verified its persistent `podwayd --dev` service, explicit workspace mode support, canonical enrollment, immutable publication, approved activation, stable command resolution, and production isolation. Master confirmed that Dolgorae development-channel setup is complete on 2026-09-08; it no longer blocks producer integration. Master confirmed that Gaori development-channel setup is complete on 2026-09-09; TASK-013 is complete. Sanho's clean local-`main` producer candidate, canonical enrollment, development resolution, and production isolation have also been verified; TASK-014 is complete. The uncompleted Mulgae and Seongge integrations and final channel validation are now withdrawn. Their replacement VM work belongs to TASK-092 and TASK-098 in EPIC-032, followed by final EPIC-033 qualification and retirement. The retained producer contracts describe the old installed channel until its actual retirement; they are not new Haepari acceptance requirements.

**Detailed SOT:** [`TODO-AQUARIUM-DEV.md`](../todo/TODO-AQUARIUM-DEV.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-005 | Prove development-channel feasibility | Validate host locks, hook coexistence, atomic publication, and the original isolated runtime assumptions before implementation. | Completed | TASK-004 |
| TASK-006 | Define the shared development contract | Freeze producer, artifact, enrollment, resolver, version, and failure contracts. | Completed | TASK-005 |
| TASK-007 | Implement enrollment and hook lifecycle | Add the explicit skill workflow, canonical checkout enrollment, re-enrollment, and hook ownership transfer. | Completed | TASK-006 |
| TASK-008 | Implement build scheduling and publication | Build exact local-main candidates, serialize publishers, and atomically advance the current artifact. | Completed | TASK-006 |
| TASK-009 | Implement resolution, leases, and cleanup | Implement the original generation-resolution and cleanup contract, later simplified by TASK-031. | Completed | TASK-006, TASK-008 |
| TASK-010 | Isolate Aquarium and Codex development runtime | Implement the original isolated Codex environment, later superseded by TASK-031. | Completed | TASK-007, TASK-008, TASK-009 |
| TASK-011 | Integrate Podway | Add and verify Podway's shared producer contract and development resolution. | Completed | TASK-010 |
| TASK-012 | Integrate Mulgae | Withdraw legacy producer integration; project-owned Haepari VM adoption replaces it under TASK-092. | Cancelled | TASK-010 |
| TASK-013 | Integrate Gaori | Integrate Gaori's shared producer contract and development resolution; Master confirmed setup completion on 2026-09-09. | Completed | TASK-010 |
| TASK-014 | Integrate Sanho | Add and verify Sanho's shared producer contract and development resolution. | Completed | TASK-010 |
| TASK-024 | Integrate Dolgorae | Integrate the Dolgorae producer with the development channel corrected by TASK-031; Master confirmed setup completion on 2026-09-08. | Completed | TASK-010; external Dolgorae TASK-035 |
| TASK-031 | Separate development and production environments | Rename the channel and root to `aquarium-dev`, inherit the caller's environment, give foreground producers per-tool global fallback, require managed services to match an active development generation, admit optional Dolgorae enrollment, and decouple Orca Review from Dolgorae. | Completed | TASK-010, TASK-028 |
| TASK-041 | Integrate Sorage | Withdraw development-channel integration: Sorage exchanges development requirements across projects, so separating production and development adds unnecessary complexity. | Cancelled | None |
| TASK-042 | Integrate Seongge | Withdraw legacy consumer/producer expansion; project-owned Haepari VM adoption replaces it under TASK-098. | Cancelled | TASK-031; external Seongge producer handoff |
| TASK-015 | Cold-validate the integrated environment | Withdraw final legacy-channel validation; TASK-100 through TASK-102 qualify and close the replacement after safe retirement. | Cancelled | TASK-011, TASK-012, TASK-013, TASK-014, TASK-024, TASK-031, TASK-042 |

## EPIC-003: Activate Dolgorae-backed Reviews

**Status:** `Completed`

Adopt and activate the Aquarium-side contract for immutable Dolgorae-backed independent review. The historical implementation also coupled `orca-review` target capture and settlement to Dolgorae while preserving Orca lifecycle ownership. `TASK-031` superseded that Orca-side coupling by restoring native Orca execution while Independent Review retained the complete Dolgorae guarantees. The released v0.1.18 [Orca review workflow](https://github.com/irootkernel/aquarium/blob/v0.1.18/plugins/aquarium/skills/orca-review/SKILL.md) records that native requested-reviewer contract in the registered worktree.

EPIC-003 completed against the then-current exact Dolgorae development generation and did not depend on EPIC-002's unfinished original producer tasks. Current production execution is governed by EPIC-005 and the global-release correction in `TASK-031`.

**Canonical Outcomes:** [Dolgorae review contract](../../plugins/aquarium/references/dolgorae-review-contract.md), [common review contract](../../plugins/aquarium/references/review-contract.md), [development-channel contract](../../plugins/aquarium/references/development-contract.md), [current host-native review](../../plugins/aquarium/skills/subagent-review/SKILL.md)

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

**Canonical Outcomes:** [Dolgorae review contract](../../plugins/aquarium/references/dolgorae-review-contract.md), [tool integrations](../specs/tool-integrations.md), [local interfaces](../specs/local-interfaces.md), [global development setup](../../plugins/aquarium/skills/dev-setup-global/SKILL.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-025 | Adopt the official Dolgorae v0.1.0 distribution | Pin the release tag, source commit, platform, archive, executable checksum, maturity, and ownership boundaries. | Completed | External Dolgorae v0.1.0 release |
| TASK-026 | Implement stable Dolgorae admission and setup | Add exact stable inspection, bundle selection, and fail-closed identity checks; private execution is later removed by TASK-031. | Completed | TASK-025 |
| TASK-027 | Activate stable Dolgorae-backed reviews | Historically moved both review paths to the pinned stable release; TASK-031 retained it only for Independent Review and restored native Orca reviewer execution. EPIC-015 later disables the Independent route. | Completed | TASK-026; EPIC-003 |
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

## EPIC-007: Adopt Upstream Document Humanizers

**Status:** `Completed`

Adopt exact upstream Humanizer and im-not-ai releases as independently installed Codex skills, then let each repository opt into an evidence-preserving English and Korean documentation pass through `dev-setup-global`, `dev-setup`, and `dev-setup-bundle`.

**Canonical Outcomes:** [Tool integrations](../specs/tool-integrations.md), [global development setup](../../plugins/aquarium/skills/dev-setup-global/SKILL.md), [repository development setup](../../plugins/aquarium/skills/dev-setup/SKILL.md), [bundle manifest](../../plugins/aquarium/skills/dev-setup-bundle/references/manifest.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-032 | Integrate upstream document humanizers | Add exact-release installation, structural diagnosis, project guidance, bundle selection, public disclosures, and regression coverage for Humanizer and im-not-ai. | Completed | None |

## EPIC-008: Adopt Podway v0.2.8

**Status:** `Completed`

Adopt the official Podway v0.2.8 release as Aquarium's minimum stable runtime. The v0.2.8 contract adds named-mode daemon readiness v3 and keeps workspace runtime-mode changes behind explicit authorization. Qualification covers the revised task, goal, and validation Procedures together with the official artifact's fenced workspace-removal behavior.

Podway owns its release, distribution, runtime-mode implementation, and source-distributed `use-podway` lifecycle guidance. Aquarium independently verifies the official artifact and diagnoses runtime-mode mismatches without changing modes. Verification of the official Podway v0.2.9 artifact confirmed successful workspace-removal replay and preservation of the Git worktree, closing the v0.2.8 replay exception.

**Canonical Outcomes:** [Tool integrations](../specs/tool-integrations.md), [Local interfaces](../specs/local-interfaces.md), [Podway integration](../../plugins/aquarium/references/podway-integration.md), [Changing Procedures](../implementation-tips/changing-procedures.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-033 | Align the Podway v0.2.8 support contract | Raise the stable runtime floor, adopt named-mode daemon readiness, preserve explicit workspace-mode authorization, and update the managed Procedure review and rework seams. | Completed | External Podway v0.2.8 release |
| TASK-034 | Qualify and close Podway v0.2.8 adoption | Verify the official artifact against the managed Procedures, lifecycle guards, runtime cleanup, fenced workspace removal, and final exact Aquarium candidate. | Completed | TASK-033 |

## EPIC-009: Adopt Sorage v0.1.x

**Status:** `Completed`

Adopt Sorage as an optional local document-handoff integration. Aquarium diagnoses and installs the supported CLI and paired skill, initializes the local installation with a minimal profile, and registers each selected Git repository through an explicitly approved Project creation or binding. Sorage retains authority over Project identity, the managed Vault, Handoffs, reviews, retention, deletion, backup, and derived inbox state.

The supported line is official stable v0.1.x on native Apple Silicon macOS, starting at v0.1.2 after TASK-105. This stable adoption excludes the production-binary baseline, managed Procedures, and MCP scope. Master cancelled development-channel integration under TASK-041 on 2026-09-09. Sorage exchanges development requirements across projects and does not need separate production and development instances; that separation would make the system substantially more complex. Existing stable Sorage setup and Project registration remain in scope.

Master explicitly accepted EPIC-009 and TASK-047 closeout on 2026-09-09. The later cross-skill regression scenarios remain with TASK-046 and are not claimed by this closeout.

**Canonical Outcomes:** [Tool integrations](../specs/tool-integrations.md), [local interfaces](../specs/local-interfaces.md), [capabilities](../specs/capabilities.md), [tool catalog](../../plugins/aquarium/references/tool-catalog.md), [global development setup](../../plugins/aquarium/skills/dev-setup-global/SKILL.md), [repository development setup](../../plugins/aquarium/skills/dev-setup/SKILL.md), [repository guidance](../../plugins/aquarium/skills/dev-setup/references/agents-guidance.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-035 | Add Sorage setup and Project registration | Add bounded Sorage inspection, exact-release and paired-skill setup, minimal initialization, approved Project creation or binding, ignore safety, bundle selection, and agent guidance. | Completed | External Sorage v0.1.0 release |
| TASK-036 | Qualify Sorage integration | Verify version, initialization, Project resolution, privacy, documentation, bundle, and failure contracts against isolated fixtures and the official v0.1.0 CLI. | Completed | TASK-035 |
| TASK-047 | Adopt Sorage v0.1.1 workflow contracts | Align explicitly requested broker operations, Review Note reads, optional event timelines, and Project setup through `.gitignore` with the official v0.1.1 CLI and paired skill. | Completed | TASK-035, TASK-036; external Sorage v0.1.1 release |

## EPIC-010: Separate Global and Repository Development Setup

**Status:** `Completed`

EPIC-010 separated user-global installation and updates from repository setup. `dev-setup-global` owned exact-upstream CLI and skill maintenance, global MCP and services, writing and Lore skills, and Ouroboros updates. `dev-setup` automatically diagnosed evidenced repository configuration and owned root AGENTS.md and CLAUDE.md guidance without inspecting global skill contents.

At this epic's completion, the bundle manifest used `aquarium.dev-setup-bundle/v1`: it prepared the global union once and delegated repository configuration to `dev-setup` in target order. `TASK-076` under `EPIC-000` owns its v2 replacement.

**Canonical Outcomes:** [Capabilities](../specs/capabilities.md), [tool integrations](../specs/tool-integrations.md), [local interfaces](../specs/local-interfaces.md), [global development setup](../../plugins/aquarium/skills/dev-setup-global/SKILL.md), [repository development setup](../../plugins/aquarium/skills/dev-setup/SKILL.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-037 | Split global development setup from repository setup | Add automatic global diagnosis and updates, narrow repository setup to local configuration and root guidance, preserve bundle v1 routing, and enforce the boundary with deterministic inspectors and regression coverage. | Completed | None |

## EPIC-011: Harden Release QA Confirmation Integrity

**Status:** `Completed`

Make the sole post-remediation release QA confirmation a fail-closed, immutable, and exactly-once settlement. Bind every confirmation to the exact frozen full-pass record, remediation manifest, candidate, evidence root, claim, attempt, and original finding-to-scenario relationship so replacement, replay, inconsistent evidence, or concurrent settlement cannot produce a trusted verdict.

The hardened path applies only after a complete full-mode `FINDINGS` result. A normal full-mode `PASS`, release metadata handling, release publication, and the scenario execution policy remain unchanged.

**Canonical Outcomes:** [Release QA workflow](../../plugins/aquarium/skills/release-qa/SKILL.md), [local interfaces](../specs/local-interfaces.md), [workflow contracts](../specs/workflow-contracts.md), [privacy disclosure](../../PRIVACY.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-038 | Freeze exact confirmation identity | Make the full record, remediation manifest, claim, and finding-to-scenario inventory create-once artifacts bound by exact digests and candidate identity. | Completed | None |
| TASK-039 | Enforce one-shot confirmation settlement | Admit one finish operation per exact claim, persist an immutable terminal PASS, FINDINGS, INCOMPLETE, or REJECTED attempt record, and fail closed on replay, concurrency, or interrupted settlement. | Completed | TASK-038 |
| TASK-040 | Qualify confirmation integrity | Cover valid settlement, artifact replacement, claim replay, finding-scenario mismatch, rejected evidence, concurrency, and interruption with focused tests and align the release QA contract. | Completed | TASK-038, TASK-039 |

## EPIC-012: Modernize Aquarium Skills for GPT-6 Astra

**Status:** `Planned`

Reduce unnecessary instruction loading, repeated investigation, redundant
verification, and repeated questions in Aquarium skills while preserving native
tool contracts, workflow behavior outside the approved changes, and distinct
authorization boundaries. Master intends to execute this epic after completing
the paired tool skill updates in their owning repositories.

**Detailed SOT:** [`TODO-ASTRA-SKILLS.md`](../todo/TODO-ASTRA-SKILLS.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-043 | Shorten Aquarium discovery descriptions | Adopt SKILL-01: simplify descriptions while preserving activation semantics and workflow behavior. | Planned | TASK-085 |
| TASK-044 | Restructure Aquarium entrypoints and conditional reading | Adopt SKILL-02: move conditional detail to reachable references and preserve transition contracts. | Planned | TASK-043 |
| TASK-045 | Remove redundant Aquarium rechecks and questions | Extend SKILL-03 with confirmed Sanho non-use guidance; align setup guidance and callers while preserving task and Git boundaries. | Planned | TASK-044 |
| TASK-046 | Validate skill integration and complete manual acceptance | Extend SKILL-09 to reconcile local sources, resource contracts, Sanho setup transitions, explicit Sorage discovery, and applicable manual scenarios. | Blocked | TASK-043, TASK-044, TASK-045, TASK-047, TASK-085; external SKILL-04 through SKILL-08 |

Gaori (`SKILL-04`) source work is `Completed`, as confirmed by Master on
2026-09-10. Aquarium's local source inspection and integration acceptance remain
pending.

Sanho (`SKILL-07`) source work is `Completed`, as confirmed by Master on
2026-09-09. Aquarium's local source inspection and integration acceptance remain
pending.

Sorage (`SKILL-08`) source work is `Completed` in the official v0.1.1 release,
as confirmed by Master on 2026-09-09. `TASK-047` owns Aquarium's immediate
adoption; `TASK-046` retains the later cross-skill regression scenarios.

`TASK-046` is blocked pending the Mulgae (`SKILL-05`) and Podway (`SKILL-06`)
source work.
These are external work labels from the modernization proposal, not Aquarium
task IDs. Each tool repository owns its implementation and lifecycle.

Unblock `TASK-046` after Master's completion handoff and inspection of the current
local source trees establish the external acceptance requirements in the dossier,
and `TASK-043`, `TASK-044`, and `TASK-045` are complete. Tool release or installation
is not a prerequisite. At epic intake, inspect the updated local skill sources
and their references before planning Aquarium edits; retain the exact source
identity in native execution evidence. Required manual acceptance remains a
completion gate after the task is unblocked.

## EPIC-013: Record and report production setup status

**Status:** `Completed`

Store one production ledger at `~/.aquarium/status.yaml` for Git worktree roots
that have finished `$aquarium:dev-setup` or received a terminal bundle result.
The owning setup workflow records the settled outcome before its final report.
`aquarium-status show` reads the file from a shell without Codex, Grok, or a
plugin cache, while `$aquarium:status` uses the same reporting contract. The LLM
must not write the YAML.

ADR-0008 already reserves `~/.aquarium/` for production state.
`aquarium-dev` still writes only under `~/.aquarium-dev/`. A repository-local
`.aquarium` file remains forbidden. `dev-setup-bundle` still must not persist
its input manifest.

**Canonical Outcomes:** [Production status](../specs/production-status.md), [Capabilities](../specs/capabilities.md), [Local interfaces](../specs/local-interfaces.md), [Architecture](../architecture/README.md), [Production status operations](../ops/production-status.md), [README](../../README.md), [Privacy](../../PRIVACY.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-048 | Freeze the production status contract | Define schema `aquarium-production-status/v1`, sourced version and freshness observations, full versus scoped attempt meaning, component unknown states, terminal-record ownership, locked revision-safe writes, output and exit contracts, Git identity, retention, privacy, and explicit row removal. | Completed | None |
| TASK-049 | Ship `aquarium-status` and wire setup/status skills | Implement `show`, closed-JSON `record`, and exact `forget`; install the cache-independent versioned runtime and receipt-bound exact-interpreter launcher through `dev-setup-global`; wire `dev-setup`, bundle-owned early outcomes, and `$aquarium:status` without duplicate records. Security review re-froze only the pre-publication launcher detail; public v1 schemas remain unchanged. | Completed | TASK-048 |
| TASK-050 | Qualify status persistence and reporting | Prove independent offline and refreshed reporting, JSON-only output, scoped then unscoped promotion, unknown and corrupt observations, concurrent merge and conflict behavior, storage-failure recovery, Git-root retention, approved launcher replacement, and execution after plugin-cache removal. Master verifies skill behavior separately. | Completed | TASK-049 |

## EPIC-014: Align Procedure contracts and bound Low-finding convergence

**Status:** `Completed`

Align the five managed Podway Procedures with their owning skills, shared review
rules, closeout, and commit handoffs. A completed review or audit may retain its
historical Low findings after every eligible Low item has a supported disposition
and the required local verification. Additional provider reviews or broad
re-audits cannot be started solely to reduce that historical count.

The change preserves required first reviews, confirmation owed after a
Medium-or-higher correction, exact native recovery, immutable admitted sessions,
and separate approval boundaries for installation, commits, and publication. It
does not change the Podway engine or built-in presets.

Master accepted the separately observed agent behavior on 2026-09-14. Canonical
and repository-local Procedure sources are synchronized for later starts; this
does not replace or reinterpret an admitted session and establishes no runtime
activation, installation, or publication.

**Canonical Outcomes:** [Finding disposition](../../plugins/aquarium/references/finding-disposition.md), [Procedure node contracts](../../plugins/aquarium/references/procedure-node-contracts.md), [Podway integration](../../plugins/aquarium/references/podway-integration.md), [Local interfaces](../specs/local-interfaces.md), [Changing Procedures](../implementation-tips/changing-procedures.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-051 | Adopt the workflow contract and freeze regression cases | Register the approved scope, baseline, identifiers, requirements, and finite routing fixtures without claiming the reported incident was reproduced. | Completed | None |
| TASK-052 | Define finite Low settlement and review admission policy | Separate immutable review facts from pending dispositions, blockers, coverage, and authority for another review. | Completed | TASK-051 |
| TASK-053 | Align task Procedure inputs, boundaries, and Low gates | Connect task phase inputs and add a verified finite Low-settlement route. | Completed | TASK-052 |
| TASK-054 | Add typed goal evidence and a general Low-settlement route | Gate goal success on verification and review readiness independently of finding counts. | Completed | TASK-053 |
| TASK-055 | Make validation severity-aware and align wait and rework boundaries | Remove Low-only audit recursion while preserving required confirmation and explicit user direction. | Completed | TASK-054 |
| TASK-056 | Complete five-Procedure node guidance and non-implementation boundaries | Map each node to its capability, inputs, prohibited effects, evidence, and rework owner. | Completed | TASK-055 |
| TASK-057 | Reconcile handlers, resume, closeout, and commit composition | Carry accepted Low-only deltas through exact final-target verification without another review. | Completed | TASK-056 |
| TASK-058 | Qualify customization and immutable-version compatibility | Distinguish native validity from handler compatibility and preserve old snapshots and local customizations. | Completed | TASK-057 |
| TASK-059 | Implement and run native graph regression qualification | Exercise the revised canonical graphs, rejection paths, cleanup, and official Podway artifact compatibility. | Completed | TASK-058 |
| TASK-060 | Observe agent behavior and context-recovery acceptance | Confirm review dispatch, wait, resume, and forbidden-effect behavior through separately authorized scenarios. | Completed | TASK-059; Master's separate observed-agent verification |
| TASK-061 | Promote durable documentation and prepare an unactivated handoff | Publish implemented behavior to canonical owners and report evidence without installation, commit, or release claims. | Completed | TASK-060 |

## EPIC-015: Add intent-aware review and disable Independent Review temporarily

**Status:** `Completed`

Give enabled Mulgae and Orca reviews enough authoritative context to assess the
selected change or the completion of a named Task or Epic. Apply the same Review
Brief semantics when Master explicitly chooses an available native Codex
subagent, while preserving each route's native lifecycle and action boundaries.

Temporarily disable Aquarium's Dolgorae-based Independent Review before setup,
target capture, source transmission, or dispatch. The entrypoint guides Master
to available alternatives without launching one automatically. Dolgorae remains
an optional supported global component for explicit setup and operations; its
absence does not fail common production readiness while this route is disabled.
Dolgorae changes and future Independent Review re-enablement are outside this
epic.

**Canonical Outcomes:** [Review intent](../../plugins/aquarium/references/review-intent-contract.md), [Static review](../../plugins/aquarium/references/review-contract.md), [Mulgae review](../../plugins/aquarium/references/mulgae-review-contract.md), [Finding disposition](../../plugins/aquarium/references/finding-disposition.md), [Workflow contracts](../specs/workflow-contracts.md), [Capability catalog](../specs/capabilities.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-062 | Disable Independent Review and relax common Dolgorae readiness | Refuse every Independent Review request before Dolgorae work, guide alternatives without automatic fallback, and make Dolgorae optional in common production readiness while preserving explicit setup and operations. | Completed | None |
| TASK-063 | Define the shared review-intent contract | Define Review Brief semantics, criterion responsibility and aggregation, requirement provenance, candidate boundaries, completion checkpoints, and the completion conditions consumed by handlers and Procedures. | Completed | TASK-062 |
| TASK-064 | Add intent-aware embedded Mulgae completion review | Deliver approved handler context, aggregate accepted Markdown role reports, preserve safe criterion handoffs, and connect completion gaps to Task and Epic approval decisions. | Completed | TASK-063 |
| TASK-065 | Add standalone Mulgae change and completion review | Add the report-only `mulgae-review` entrypoint for staged changes and named Task or Epic completion without duplicating native lifecycle or starting remediation. | Completed | TASK-064 |
| TASK-066 | Align Orca and explicit native Codex subagent guidance | Carry the shared brief through Orca Dispatch and result handling, and describe explicitly chosen host-native subagent reviews without claiming unsupported guarantees. | Completed | TASK-063 |
| TASK-067 | Qualify and document the review contract | Verify integrated approval decisions and routing, align canonical and public documentation, and complete deterministic checks plus Master's separate manual acceptance. | Completed | TASK-064, TASK-065, TASK-066 |

## EPIC-016: Add selectable workflow review routing

**Status:** `Completed`

Separate the requirement for completion review from the choice of review
backend. Keep Mulgae as the default while allowing an approved Task, Epic, or
cold-validation workflow to use Orca, a fresh native Codex subagent, or an
explicit delegated-review waiver. Backend failure stops for user direction and
never selects another route automatically.

Every route retains its own target, execution, storage, recovery, and evidence
guarantees. A waiver launches no reviewer and may support completion only after
the coordinator assesses the complete requirement set from current authorized
evidence. Reports must preserve the reduced assurance and every earlier finding.
Independent Review remains disabled; its re-enablement is outside this epic.

This epic builds on the bounded Procedure and review-intent contracts delivered
by `EPIC-014` and `EPIC-015`.

Master accepted the separately observed route selection, prerequisite isolation,
failure recovery, provider continuity, legacy-session, and waiver behavior on
2026-09-20. The accepted implementation keeps review execution and evidence
native to the selected route and does not imply release or installation.

**Canonical Outcomes:** [Review routing](../specs/review-routing.md), [Workflow contracts](../specs/workflow-contracts.md), [Capability catalog](../specs/capabilities.md), [Local interfaces](../specs/local-interfaces.md), [Review routing contract](../../plugins/aquarium/references/review-routing-contract.md), [Procedure node contracts](../../plugins/aquarium/references/procedure-node-contracts.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-068 | Generalize review routing and evidence contracts | Define route-neutral evidence combinations, lifecycle-safe switching, waiver semantics, route-specific readiness, and the Mulgae-only promoted hardening-deferral boundary. | Completed | EPIC-014; EPIC-015 |
| TASK-069 | Integrate selectable review into Task delivery | Deliver Task routing with its skills, Procedure copies, inspector contract, digests, fixtures, and focused tests as one compatible unit. | Completed | TASK-068 |
| TASK-070 | Integrate selectable review into Epic delivery and validation | Deliver Epic and validation routing with compatible Procedures, commit handoff, hardening-deferral limits, evidence consumption, and focused tests. | Completed | TASK-068; TASK-069 |
| TASK-071 | Qualify review routing and promote documentation | Run cross-route regression, timeout and switching scenarios, legacy-session and manual acceptance, then promote the reserved contract to shipped documentation. | Completed | TASK-069; TASK-070 |

## EPIC-017: Add Web Pro Review

**Status:** `Planned`

Add an independently callable Web Pro Review backed by `codex-chatgpt-web` and
the exact `chatgpt-web/pro` model. Extend the selectable routing contract from
`EPIC-016` with a `web-pro` peer route so Task, Epic, and cold-validation
workflows can select it initially or switch to it after the preceding route
reaches an authoritative safe state.

Web Pro Review does not depend on or join Herdr, Mulgae, Dolgorae, or Independent
Review. It never runs as an automatic fallback. Calls from another Codex home,
including `~/.codex-hsy`, use the primary Codex Web bridge profile without
copying account state into the caller's home.

**Detailed SOT:** [`TODO-WEB-PRO-REVIEW.md`](../todo/TODO-WEB-PRO-REVIEW.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-072 | Define the Web Pro Review contract | Freeze target, account, transmission, execution, result, recovery, and EPIC-016 adapter requirements. | Planned | EPIC-015; EPIC-016 |
| TASK-073 | Implement primary-profile Web Pro execution | Add the standalone skill, deterministic runner, and global readiness inspection without copying a checkout or account state. | Planned | TASK-072 |
| TASK-074 | Add Web Pro to selectable review routing | Extend Task, Epic, and validation handlers and new Procedure versions with route-specific Web Pro evidence and recovery. | Planned | TASK-072; TASK-073 |
| TASK-075 | Qualify and document Web Pro Review | Complete deterministic, integration, compatibility, account-bound runtime, manual acceptance, and canonical documentation checks. | Planned | TASK-073; TASK-074 |

## EPIC-018: Correct Aquarium workflow and integration contracts

**Status:** `In Progress`

Correct the Aquarium-owned findings from the 2026-09-25 static skill review before
modernizing the affected entrypoints under `EPIC-012`. Six requests have been
sent through Sorage for the tool-owned findings. Each producer retains its own
source, roadmap, verification, release, and installation decisions. This epic does not
claim that a sent request or an Aquarium-side correction fixes a producer.

**Detailed SOT:** [`TODO-WORKFLOW-REVIEW-CORRECTIONS.md`](../todo/TODO-WORKFLOW-REVIEW-CORRECTIONS.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-077 | Settle findings and record producer requests | Freeze the deduplicated review inventory, verify plausible claims, and record the already-sent tool-specific Sorage request scope without resending. | Completed | None |
| TASK-078 | Correct external effects and plugin entry | Fix unintended reviewer or clipboard effects and the Aquarium plugin MCP declaration. | Completed | TASK-077 |
| TASK-079 | Correct review-route readiness and recovery | Align legacy Procedure readiness, Independent Review and Orca recovery, staged-candidate preparation, and Aquarium-side tool handoffs. | Completed | TASK-078 |
| TASK-080 | Correct Task, Goal, and Validation Procedure routing | Repair blocker, plan-resume, rework, and closeout paths across managed Procedure sources, mirrors, and qualification. | Completed | TASK-079 |
| TASK-081 | Correct Task closeout and commit handoff | Align Task decision records, dossier settlement, prose pass timing, and commit authority with the revised Procedure. | Completed | TASK-080 |
| TASK-082 | Correct release helpers and gate sequencing | Support first releases and repository-specific commit titles; bind pre-QA gates, light confirmation, Design Gates, and publication recovery. | Completed | TASK-081 |
| TASK-083 | Correct installed-package and setup contracts | Keep plugin resources reachable and align tool inventory, network and installer disclosures, timeout, and Sorage setup routing. | Completed | TASK-082 |
| TASK-084 | Correct design and status workflows | Align quality-result decisions, design-document ownership, war-room notes, and status-forget recovery. | Completed | TASK-083 |
| TASK-085 | Qualify Aquarium corrections and hand off integration | Verify the exact Aquarium-owned changes, report manual evidence separately, and pass producer-response gaps to TASK-046. | Completed | TASK-084 |

## EPIC-019: Adopt Haepari VM verification for Aquarium

**Status:** `Completed`

Published Haepari v0.1.0 CLI/skill setup and Aquarium's managed persistent-VM adapter are qualified. TASK-086 through TASK-090 established exact artifact/backend acceptance, shared controller/resource identity, sealed input/profile/skill and migration contracts, one uninterrupted manual release Job, same-Job recovery and both consumer and native cleanup. External leases and VM power/reset remain excluded.

TASK-090 qualified the exact installed release-VM policy cutover and promoted the adapter, profiles, recovery and release handoff into the Canonical Outcomes below. The VM guide preserves the observed qualification limits. EPIC-002 history and shared legacy infrastructure remain available to their remaining consumers. Host activation and publication retain separate authority.

The complete delivery order is EPIC-019 -> EPIC-031 -> EPIC-032 -> EPIC-033. Each Epic completes its own acceptance and documentation closeout before the next starts; Task IDs remain stable. EPIC-019 does not wait for release-role implementation, producer returns, Mulgae integration or common retirement. Promote reusable outcomes before deleting its sole-consumer dossier.

**Canonical Outcomes:** [Haepari integration and setup](../specs/tool-integrations.md#haepari), [adapter interfaces](../specs/local-interfaces.md#inspectors-and-helpers), [release workflow](../specs/workflow-contracts.md#release-a-stable-version), [verification architecture](../architecture/verification.md), [ADR-0010](../architecture-decision-records/0010-haepari-vm-verification-and-advisory-locks.md), [VM operations](../ops/haepari-vm-verification.md), [testing authority](../../TESTING.md#host-submitted-managed-vm-suites), and [qualified profiles and pilot limits](../../tests/vm/README.md#qualified-pilot-and-limits).

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-086 | Accept Haepari and freeze the consumer contract | Verify the published artifact, complete paired skill, managed/lock capabilities, native schemas and actual backend evidence; freeze the consumer and authority boundaries without deferred external leases or VM reset. | Completed | Published Haepari v0.1.0 release available; exact-artifact and backend-evidence acceptance required |
| TASK-087 | Register Haepari and define fixed test profiles | Add formal CLI/skill setup and native readiness, shared installation/resource selection, fixed combinations, whole-tree checks and starting/cleanup inventories without a shadow registry. | Completed | TASK-086 |
| TASK-088 | Implement Aquarium's project-owned VM suites | Add a host wrapper over EPIC-024's guest scenarios, sealed inputs and same-Job recovery; stage evidence and finish consumer cleanup before manual completion or automatic workload exit within one release transaction. | Completed | TASK-087; EPIC-024 |
| TASK-089 | Integrate skills, hands-on and the VM release gate | Connect managed occupancy and original candidate-bound results to the release VM path for the existing release workflow and the later EPIC-031 handoff, preserving offline QA, full/light rules and native authority. | Completed | TASK-088 |
| TASK-090 | Qualify the Aquarium pilot and prepare Epic closeout | Accept the exact installed policy-cutover candidate; promote adapter/profile/recovery outcomes, prepare whole-Epic acceptance and dossier settlement, and preserve remaining shared legacy consumers. | Completed | TASK-089 |

## EPIC-020: Migrate Orca review to Herdr

**Status:** `Completed`

Replace Aquarium's Orca-backed static review with Herdr for the open `v0.1.19`
release. Add `herdr-review`, migrate the Task, Epic, and validation review paths,
and remove executable Orca routes, aliases, and runtime prerequisites from the
new package. Keep Mulgae as the default and preserve the shared target, Review
Brief, finding-disposition, verification, and acceptance contracts.

Herdr owns reviewer execution and native pane/agent control. Aquarium admits
completion only from the requested reviewer's complete result for the exact
target and Brief; `idle` or `done` alone is insufficient. Preserve historical
Orca evidence, custom Procedures, and active snapshots without relabeling them
or invoking Orca through the new package. An unsupported legacy checkpoint
needs a safe, explicitly authorized transition or successor.

Implementation follows the approved Epic execution envelope. Live Herdr
qualification, installation, activation in other repositories, host-tool
removal and release publication retain their separate authority. `EPIC-019`
is not a prerequisite, and no producer engine change or broker handoff is required.

**Canonical Outcomes:** [Review routing](../specs/review-routing.md), [tool integrations](../specs/tool-integrations.md), [Herdr migration runbook](../ops/herdr-migration.md), [qualification guidance](../implementation-tips/qualifying-herdr-review.md), [testing contract](../../TESTING.md)

Master accepted completion of this Epic with the disclosed verification limits.
Whole-skill Task, Epic, and validation scenarios, complete peer-route recovery
and acceptance, and Master's separate functional checks remain unverified.
Native incompatibility, active or unknown legacy-worker settlement, a genuine
waiver predecessor, spontaneous stalls, agent replacement, and completed-output
loss were not observed. This acceptance applies only to `EPIC-020`; future
workflows retain their functional-verification requirements. Installation,
cross-repository activation, host cleanup, and release publication remain
separately authorized actions.

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-106 | Implement Herdr static review | Add the standalone skill and native supervision contract with exact targets, explicit reviewer identity, complete report evidence, and safe recovery. | Completed | EPIC-016; TASK-085 |
| TASK-107 | Integrate Herdr workflow routing | Replace active Orca dispatch and handoffs; update handlers, three Procedure sources and mirrors, readiness inspection, and routing qualification as one compatible unit. | Completed | TASK-106 |
| TASK-108 | Support migration from Orca workflow state | Implement Herdr prerequisites and legacy-source readiness; preserve evidence, customizations, and snapshots while providing safe refusal, transition, and separately authorized rollout guidance. | Completed | TASK-107 |
| TASK-109 | Qualify Herdr migration and promote documentation | Qualify the candidate through local and native checks under the accepted verification limits; remove current Orca dependencies and promote canonical outcomes. | Completed | TASK-106; TASK-107; TASK-108 |

## EPIC-021: Adopt supervised agent orchestration

**Status:** `Completed`

Adopt an Orchestrator, Judge, and Workers model across the Task, Goal,
Validation, Design, and War-room Procedures after `EPIC-020`. The main agent
allocates work, manages agent lifecycles and authority, and records Podway
progression. Workers perform bounded research, analysis, implementation, and
checks. A persistent Judge assesses node, Task, and Epic goals from canonical
criteria and original evidence; Worker delivery alone cannot establish success.

Use Codex and Claude host-native subagents first. Preserve technical review
routes and their native reviewer topology, budgets, finding dispositions, and
correction authority. The Primary accepts complete native Worker deliveries and
Judge reports under their placement checks and authority, then completes their
Actions. Semantic progression uses the applicable Judge verdict without
repeating the assessment or recursively judging the report. Reconnect existing agents
when possible; otherwise reconcile uncertain work and restore goals, evidence,
and assessment state before replacement. Allow parallel research and sequential
implementation on a shared checkout.

The candidate implements native mappings and all five workflow integrations for
the planned v0.1.19 release with EPIC-020. No Podway core change is planned.
Preserve the Herdr migration, existing approval boundaries, admitted session
snapshots and repository customizations. Installation, activation, commits and
publication retain their applicable authority.

**Canonical Outcomes:** [Agent orchestration](../specs/agent-orchestration.md), [Workflow runtime](../architecture/workflow-runtime.md), [ADR-0009](../architecture-decision-records/0009-supervised-agent-orchestration.md), [Orchestration contract](../../plugins/aquarium/references/agent-orchestration.md), [Native mappings](../../plugins/aquarium/references/native-agent-mappings.md), [Procedure node contracts](../../plugins/aquarium/references/procedure-node-contracts.md)

All five candidate Procedures require Worker delivery and report-only Judge
assessment before Primary semantic Decisions. Recorded bounded Codex and Claude
scenarios cover delivery, separate Action completion, phase Decisions and the
supported recovery boundaries. Their qualification applies only to the original
operative inputs; changed role snapshots require fresh native acknowledgement.
Initial Agent, inner-model and Codex dispatch-ACK loss and arbitrary outliving
descendants remain unqualified. Installed snapshots retain their admitted rules.
Exact candidate upgrade in UTM remains a separate pre-release gate.

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-110 | Define orchestration contracts | Define roles, Judge lifetime and authority, canonical criterion coverage, technical review boundaries, handoffs, and recovery. | Completed | EPIC-020 |
| TASK-111 | Integrate native delegation | Add report-only Judge and Worker guidance; qualify actual Codex and Claude dispatch, configuration, result acceptance, settlement, and recovery against Podway delegation. | Completed | TASK-110 |
| TASK-112 | Rebuild Task execution | Rebuild the Task Procedure, handler, and phase contracts around Worker candidates, Judge assessments, and verdict-driven rework while preserving authority and commit handoffs. | Completed | TASK-111 |
| TASK-113 | Rebuild Epic execution | Rebuild the Goal Procedure and epic-handler with Judge continuity across member Tasks, integration criteria, internal validation, and final overall acceptance. | Completed | TASK-112 |
| TASK-114 | Rebuild Epic validation | Rebuild the Validation Procedure and independent validator with a fresh Judge, direct evidence, technical review aggregation, and scoped corrections. | Completed | TASK-113 |
| TASK-115 | Rebuild design and diagnosis | Rebuild Design and War-room role handoffs while preserving the Ouroboros leaf contract, exact document approval, and product implementation boundaries. | Completed | TASK-111 |
| TASK-116 | Align compatibility and recovery | Align all five sources, versioning, inspectors, observation contracts, reconnect and restoration, immutable snapshots, and customized Procedure compatibility. | Completed | TASK-112; TASK-113; TASK-114; TASK-115 |
| TASK-117 | Qualify and promote outcomes | Qualify the combined candidate's local, native, and bounded both-host workflow outcomes; complete delegated functional verification and promote canonical contracts for subsequent Epic validation and closeout. | Completed | TASK-111; TASK-116 |

All member Tasks and Epic validation are complete. Master accepted
the overall Epic outcome. The [agent orchestration specification](../specs/agent-orchestration.md)
owns the qualified candidate behavior and its limits; Git history retains the
settled execution dossier.

## EPIC-022: Adopt Podway v0.2.14

**Status:** `Completed`

Raise the Podway floor to stable v0.2.14 with no version upper bound for Aquarium v0.1.19. Adopt Direct execution, native identity and outcome recovery, update setup inspection and preserve the full Procedure qualification inventory. This is breaking: existing users need the new CLI and paired skill, original-writer retirement where applicable, and an explicitly confirmed fresh-runtime reset for incompatible workspaces. Exact candidate installation and functional verification must pass in UTM before release.

**Canonical Outcomes:** [Tool integrations](../specs/tool-integrations.md#podway-readiness), [Local interfaces](../specs/local-interfaces.md), [Podway integration](../../plugins/aquarium/references/podway-integration.md), [Tool catalog](../../plugins/aquarium/references/tool-catalog.md#podway), [Testing contract](../../TESTING.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-118 | Align the released Direct contract | Compare v0.2.12, v0.2.13 and v0.2.14; adopt the lower-bound-only support and upgrade contracts. | Completed | External Podway v0.2.14 release; EPIC-021 |
| TASK-119 | Update setup inspection | Validate single-CLI identity, workspace health and native contracts without service or mode assumptions. | Completed | TASK-118 |
| TASK-120 | Replace the compatibility runtime | Run the official v0.2.14 CLI against disposable fixtures, preserving Procedure scenarios and checking outcomes and removal replay. | Completed | TASK-119 |
| TASK-121 | Qualify and promote the combination | Verify exact artifacts, local checks, selected Herdr review and UTM installed workflows; promote documents and settle closeout after actual acceptance. | Completed | TASK-120 |

Master accepted the overall Podway support outcome after agent-operated verification.
The canonical contracts retain the installed qualification limits and separate
pre-release requirements; Git history retains the settled execution dossier.

## EPIC-023: Adopt Mulgae v0.1.25

**Status:** `Completed`

Raise the Mulgae floor to stable v0.1.25 and align setup, live-source review, failure handling and promoted evidence. This is breaking: users need the matching CLI and skill, deliberate Config v5 migration and compatible managed Procedures. Historical artifacts and admitted snapshots retain their original meaning. Exact candidate upgrade and skill functional verification in UTM remain required before release.

**Canonical Outcomes:** [Tool integrations](../specs/tool-integrations.md), [Mulgae review contract](../../plugins/aquarium/references/mulgae-review-contract.md), [review routing](../specs/review-routing.md), [evidence residency](../../plugins/aquarium/references/evidence-residency.md), and [testing contract](../../TESTING.md#mulgae-v0125-adoption).

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-122 | Adopt release and configuration contracts | Raise the release and envelope floors, align Config v5 setup and preserve private diagnostic boundaries. | Completed | External Mulgae v0.1.25 release |
| TASK-123 | Adopt live-source review | Replace capture/replay execution with native targets, source evidence, project binding and explicit failed-review continuation. | Completed | TASK-122 |
| TASK-124 | Add promoted evidence v2 | Preserve native source identity and consistency in durable packages and align hardening and commit handoffs. | Completed | TASK-123 |
| TASK-125 | Align and verify Mulgae adoption | Align Procedure sources and documentation, verify scoped UTM integration, and retain separate combined-release qualification. | Completed | TASK-122; TASK-123; TASK-124 |

Master directed completion of the scoped Mulgae adoption after Opus/Sonnet review, correction verification and agent-operated UTM checks. The canonical contracts retain the verification limits and the separate pre-release requirements.

## EPIC-024: Restore native agent workflows and add manual VM release acceptance

**Status:** `Completed`

Remove the native-qualification startup blocker from ordinary Aquarium workflows, group harness-native Worker and independent Judge work at meaningful boundaries, and add reusable manual UTM release-acceptance scenarios. Complete functional verification during development; release acceptance checks whether the existing installed system can upgrade and start real work. This Epic verifies Codex only and has no Haepari or Podway producer-change dependency.

This is a breaking managed-Procedure update. Preserve existing custom files and immutable session snapshots; apply new sources through authorized managed updates and compatible successor sessions. Existing formal delegation retains its native receipt requirements.

**Canonical Outcomes:** [Native orchestration](../specs/agent-orchestration.md), [ordinary roles and recovery](../../plugins/aquarium/references/ordinary-agent-orchestration.md), [Procedure node contracts](../../plugins/aquarium/references/procedure-node-contracts.md), [production status](../../plugins/aquarium/references/production-status.md), [testing](../../TESTING.md#manual-vm-release-acceptance), and [VM scenarios](../../tests/vm/release-acceptance.md).

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-126 | Define harness-native role and recovery contracts | Define grouped roles, ordinary v2 evidence contracts, recovery and breaking-update boundaries. | Completed | EPIC-023 |
| TASK-127 | Implement grouped roles and remove startup qualification blockers | Align all five Procedure sources, handlers, report consumers, renderers, validators and setup diagnostics without weakening formal delegation. | Completed | TASK-126 |
| TASK-128 | Add manual VM release acceptance and reusable scenarios | Implement the guest-side test-vm entrypoint, fixed fixtures, truthful outcomes and release-handler guidance using tests/vm. | Completed | TASK-127 |
| TASK-129 | Verify workflow recovery and release readiness | Verify development functionality, keep release acceptance separate, and promote accepted canonical outcomes. | Completed | TASK-127; TASK-128 |

## EPIC-025: Align review strategies with delivery goals

**Status:** `Completed`

Use review to deliver usable software that satisfies the original Epic and
Task goals. Define separate strategies for scoped, economical Mulgae review,
similar-capability Independent Review, and cross-AI Herdr review teams.
Recommend a route from work size, difficulty, impact and uncertainty, preserve
Master's selection, and add UI/UX expertise when the work affects user
interaction. Carry finding decisions, reasons, corrections and verification
into the next authorized review.
Establish result handoffs for each supported transport: confirm production and
submission at the sender, readback at the receiver, and same-operation recovery
when delivery fails instead of repeating the review.

Build on the completed EPIC-024 ordinary v2 contracts and existing local
settlement. This is a breaking managed-Procedure update: preserve existing
custom files and session snapshots, and use authorized updates and compatible
successors. Focus verification on result discovery, collection and handoff;
this Epic adds no dedicated VM E2E suite or review-quality benchmark. Existing
candidate-installation and release-verification policy still applies.
Master accepted the source implementation after static reviews and verified
local corrections. Installed functional results remain separate from this
source closeout and subject to the existing pre-release policy.

**Canonical Outcomes:** [Review strategies](../../plugins/aquarium/references/review-strategy-contract.md), [result handoffs](../../plugins/aquarium/references/review-result-handoff.md), [review routing](../specs/review-routing.md), [finding disposition](../../plugins/aquarium/references/finding-disposition.md), [Herdr supervision](../../plugins/aquarium/references/herdr-supervision.md), [skill verification guidance](../implementation-tips/changing-skills.md#review-result-handoffs), and [testing contract](../../TESTING.md).

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-130 | Define goal-centered review strategies | Apply ordinary goal-preserving assessment to common review inputs and finding admission; define the three strategies and capability-preserving correction. | Completed | EPIC-024 |
| TASK-131 | Recommend and select review routes | Recommend a route at handler or validator startup from scope and judgment cost; record Master's choice through the existing plan or envelope approval. | Completed | TASK-130 |
| TASK-132 | Align scoped Mulgae review | Connect focused native roles and their aggregate coverage to the original goal while preserving provider configuration and artist coverage. | Completed | TASK-130 |
| TASK-133 | Add UI coverage to Independent Review | Retain three fresh base reviewers and add a UI/UX specialist for UI-related work; collect the complete participant set as one review operation. | Completed | TASK-130 |
| TASK-134 | Enable cross-agent Herdr review teams | Let a fresh cross-AI main reviewer use multiple native subagents, including a UI/UX specialist when applicable, and return their evidence with its synthesis. | Completed | TASK-130 |
| TASK-135 | Establish review-result and decision handoffs | Define transport-specific production, submission and receiver readback; recover existing results before considering fresh review, and carry finding decisions and correction evidence into subsequent Briefs. | Completed | TASK-131; TASK-132; TASK-133; TASK-134 |
| TASK-136 | Verify review workflows and promote documentation | Review delivery, readback and same-operation recovery contracts; use focused fixtures where executable interfaces own the behavior, and promote canonical outcomes without a dedicated VM E2E suite. | Completed | TASK-135 |

## EPIC-026: ADAPT: Goal-adaptive Procedure orchestration

**Status:** `Completed`

**Canonical Outcomes:** [Adaptive contracts](../../plugins/aquarium/references/adaptive-procedures.md), [mapped execution and recovery](../../plugins/aquarium/references/adaptive-execution.md), [consented preservation](../../plugins/aquarium/references/procedure-promotion.md), [local interfaces](../specs/local-interfaces.md#activated-adaptive-execution-consumer), [architecture](../architecture/README.md), [acceptance scenarios](../../TESTING.md#adaptive-acceptance-scenarios), and [installed verification](../../tests/vm/README.md#adaptive-development-verification).

Let `task-handler`, `epic-handler`, `epic-validator`, `new-feature`,
`new-project`, `refactor` and `war-room` select, author and compose Procedures
for their actual goals. Reuse suitable complete definitions or fragments while
preserving original requirements, independent assessment, current review
strategies, native result delivery and each workflow's effect boundaries.

The approved execution envelope covers automatic selection, bounded authoring,
validation, local retention and adoption. After successful use and assessment
of future reuse value, ask Master whether to preserve the whole definition or a
useful fragment in the repository's reusable library. Specific promotion consent
is required even when broad file-editing or commit authority exists. A declined
promotion changes no tracked file and does not request local recovery deletion.
Present preservation candidates at closeout, then apply tracked promotion after
the original result and Podway finalization, with its own explicit commit scope
when committing. Content consent and commit authority may be requested together.
Use the native atomic preserve-start path only after consent to an unexpected
running-session topology replacement. Declared rework and approved normal
successor sessions continue without repeated questions.

Build on completed EPIC-024 and EPIC-025 source contracts. The planning baseline
is `4840434b80da08e8f18302d80515a880947ecca8`; later improvements must be preserved.
Edit Aquarium only and use supported released Podway Procedure v2. No Podway
producer change, optimization completion, live graph mutation, Haepari service,
central catalog or new native-authentication system is required.

This is a breaking Aquarium workflow/admission update, not a release assignment.
Preserve legacy/custom/formal sources and immutable sessions. Keep candidate
installation and observed handler verification in the dedicated UTM VM under
separately applicable authority. Reuse the existing VM driver and keep complete
development functionality separate from release upgrade/startup smoke.

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-137 | Establish adaptive contracts and preservation baseline | Define native success and capability obligations, conditional Task phases, source authority, binding/fragment identities and exact recovery, suitability and promotion policies; preserve EPIC-024/025. | Completed | EPIC-024; EPIC-025 |
| TASK-138 | Admit selected Procedure definitions | Separate adaptive session/route admission from five-ID and five-file coupling; ship the minimal atomic writer and exact-key resolver, preserve adopted customization, and prove the known-source native start/resume slice. | Completed | TASK-137 |
| TASK-139 | Select and author work-specific Procedures | Implement fit-based reuse and bounded generation, original-source coverage, approved preparation and selected-review preservation without new native qualification prerequisites. | Completed | TASK-138 |
| TASK-140 | Compose reusable Procedures and fragments | Resolve typed ports and namespaces without changing operation identities; materialize self-contained Procedure v2 candidates and validate work-fragment versus session-control responsibilities. | Completed | TASK-139 |
| TASK-141 | Qualify structure and independent plan suitability | Verify native achieved outcomes, assessment/effect order, review control and acceptance provenance with positive/negative/not-established cases; integrate exact suitability without duplicate Judge cycles. | Completed | TASK-140 |
| TASK-142 | Integrate adaptive delivery and validation | Activate Task/Goal/Validation with mapped conditional phases and working recovery; preserve reviewer teams, in-session route control, local settlement, native outcomes and acceptance/finalization boundaries. | Completed | TASK-141 |
| TASK-143 | Integrate adaptive design workflows | Adapt new-feature, new-project and refactor with upstream QA, exact-diff approval, non-implementation and non-Git/opt-out boundaries. | Completed | TASK-142 |
| TASK-144 | Integrate adaptive diagnosis | Activate diagnosis with safe reproduction and truthful incomplete/no-work delivery; implement shared consented atomic supersede and amend conflicting lifecycle rules without resetting authority. | Completed | TASK-143 |
| TASK-145 | Complete promotion, recovery and installed-test preparation | Finish cross-family recovery, post-finalization consent-based promotion and guidance compatibility; complete and commit VM driver/fixtures, source-pinned regressions and adaptive checkpoints for TASK-146. | Completed | TASK-144 |
| TASK-146 | Verify adaptive orchestration and promote outcomes | Observe integrated functionality across seven handlers on committed predecessor implementation/test artifacts; verify failure, recovery and promotion, route defects to their owners, and prepare actual Epic acceptance. | Completed | TASK-145 |

Each Task includes focused verification and affected documentation.
[TESTING](../../TESTING.md#adaptive-acceptance-scenarios) owns durable scenario IDs
and requirements; this table alone owns ordering, dependencies and lifecycle.
Task-local helper/native checks remain distinct from official compatibility and
installed checks. Installed observations use committed candidate and verification
artifacts. Master accepted completion using the full local checks on `1d82d7b`,
focused correction checks and bounded installed native and manual observations
for Task, Goal, Validation, Design and Diagnosis. The installed runtime and
VM-driver sources match the current candidate. Supplemental manual observations
do not constitute whole-collector passes. Earlier Project and Refactor
observations apply only to unchanged behavior; their full paths were not rerun
for the later candidate. Codex was the observed harness. Other harnesses,
official distribution compatibility and release QA remain unverified. Git
history retains the settled implementation dossier.

The revised acceptance covers native goal outcomes instead of terminal labels,
minimal semantic capability signatures, forward changes after assessment,
review control and user-versus-delegated acceptance, and exact binding recovery.
Equivalent noncanonical graphs and approved custom roots remain supported.
Optional library files do not become repository obligations by existing, and
preservation does not require new native authentication or extra routine review.

## EPIC-027: Add native Epic Squad collaboration

**Status:** `In Progress`

Add explicitly invoked `epic-squad` delivery through the current Coordinator's
native subagents as the first phase of one role-configurable workflow. Deliver
correct, maintainable, extensible and responsive software through bounded plans,
independent assessment and proportionate verification. Product behavior and
architectural quality take priority over validators, harnesses and process
artifacts. Deliver each Task with an authorized local commit, then independently
assess the assembled Epic before asking for overall user acceptance.

The Task Evaluator owns detailed plan review; the Epic Evaluator checks every
Task plan's direction, prior-output use and downstream handoff. Standard first
plan/result reviews use TE plus one independent Task Operator; elevated work uses TE
plus two. Both plan scopes precede implementation without a third routine plan
review. First completion assessments, Coordinator review and due checks may run
concurrently on the same fixed candidate. Final Epic review remains independent.

Resolve current defects and mandatory evidence gaps before affected acceptance;
record independent future improvements in the canonical deferred-work owner.
Separate test scope from review scope. Eligible prose, expectation and locally
verifiable corrections use focused checks and closure without full re-review.
Other changes refresh only affected judgments; re-engage EE for cross-Task impact
or its outstanding finding. Preserve first assessments, mandatory repository
gates and honest evidence applicability. Support tooling needs a current purpose
and a sufficient stopping point, including work proposed by the Coordinator.

Assess missing requirements and unjustified additions in both plans and results.
Every role, including reviewers and the Coordinator, must justify material
additions. Allow internal work needed to fulfill existing requirements. Product
scope expansion or material changes to the design direction need the user's
decision, reusing existing authority when applicable. Start each Task with new
Task Operator and Task Evaluator instances and fresh conversations where supported.
Keep same-Task contexts recoverable through verified completion and retain the
Epic Evaluator's context across Tasks.

Unify human-facing role names across `epic-squad` and `epic-handler` as Coordinator,
Epic Evaluator, Task Evaluator, Task Operator and Support Operator. Handler's
single logical evaluator becomes Epic Evaluator and its Worker/Executor becomes
Task Operator. Do not introduce a separate Task Evaluator, mandatory support
participant or Squad review panel into Handler. Preserve both workflows' actual
role duties, machine identifiers and admitted sessions; `epic-validator` keeps its
own contract. Squad has its own completion procedure; a separate cold-validator
session remains an explicitly selected additional check. Reuse existing
adaptive Goal/Validation and commit contracts under Squad's actual workflow
owner, with Podway enabled by default and explicit opt-out supported. Aquarium
owns Squad Procedure/binding changes and role dispatch; no Podway engine, CLI or
API extension is a prerequisite. Expose plan readiness, candidate assessment,
correction routes and finalization, with multiple assignments inside one active
node where useful. Preserve native rework invalidation and record current evidence
compositions explicitly. Optional Support Operators gather facts or run assigned
checks, never supply verdicts or add an approval stage.
Omitted role profiles select native execution. Recognize explicit CLI/model
profiles but report their execution as unsupported until their required
Herdr/mixed execution, commit and recovery integration from EPIC-028 is complete.
Changing the selected route requires user direction. Preserve native-only
delivery while the extension develops.

**Detailed SOT:** [Epic collaboration dossier](../todo/TODO-EPIC-COLLABORATION.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-147 | Establish collaboration contracts and native readiness | Define product quality, shared Squad/Handler role names and mapping, optional support, risk-based first assessments, purpose-bound work, correction/deferral and evidence reuse, node mapping and native readiness; preserve existing handler behavior. | Completed | EPIC-026 |
| TASK-148 | Implement native Squad collaboration | Implement Task teams, both plan scopes, independent/concurrent result intake, One Active Writer, bounded support and focused correction/deferral; align Handler role wording without adding roles or checkpoints; preserve first assessments and block unimplemented explicit routes. | Completed | TASK-147 |
| TASK-149 | Integrate Squad execution and commit authority | Qualify Squad Goal/Validation definitions and bindings, map shared role names to retained machine contracts, expose plan/correction boundaries and carry original assessments plus verified deltas to commit; support no additional technical review and preserve old callers/snapshots. | Completed | TASK-148 |
| TASK-150 | Complete Squad integration and recovery | Deliver Epic integration, scoped seam correction, post-commit inspection and user-accepted closeout; recover evidence applicability, closures, deferred work and pending operations without blanket reassessment or effect replay. | Planned | TASK-149 |
| TASK-151 | Verify Squad and promote documentation | Observe native delivery, scoped corrections, evidence reuse/recovery and necessary support; verify shared role names with Handler's single evaluator and behavior preserved; measure repeated work from existing records and promote implemented contracts with assurance limits. | Planned | TASK-150 |

## EPIC-028: Extend Epic Squad with Herdr and mixed collaboration

**Status:** `Planned`

Extend the existing `epic-squad` skill and workflow owner after EPIC-027 is
complete. Resolve each role independently: omitted profiles use the Coordinator's
native agents; explicit CLI/model profiles use Herdr even when they match the
Coordinator. An effort omitted from an explicit profile defaults to `high`,
while native roles match the Coordinator's current model and effort.

Use the same five role names for native, Herdr and mixed delivery. Support common
or scoped Evaluator profiles, Task Operator pools and optional Support Operator
profiles. The Coordinator directly manages distinct Epic and Task
Evaluators. Reuse the same first/correction assessment, support-work, deferral,
verification, Writer, Podway and commit policies for native, external and mixed
roles. Execution routes do not create separate Procedure policies or extra reviews.
Verify available model/effort/permission effects on launch, resume and transfer;
report unsupported settings without inventing enforcement harnesses or editing
host defaults. Profile or route changes need user direction. Retain original
results, current applicability, configurations and pending work across recovery.
Do not add a second skill or owner.

**Detailed SOT:** [Epic collaboration dossier](../todo/TODO-EPIC-COLLABORATION.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-152 | Resolve Squad profiles and capabilities | Resolve omitted/explicit profiles, common/scoped Evaluators, Task Operator and optional Support Operator pools, and native CLI/model/effort controls; preserve requested inputs and report unsupported settings without probe frameworks. | Planned | EPIC-027 |
| TASK-153 | Implement Squad Herdr and mixed execution | Extend the same entrypoint with verified helper allocation, distinct Evaluators, optional support and same/cross-CLI combinations; retrieve independent original results and verify supported launch/resume/Writer controls. | Planned | TASK-152 |
| TASK-154 | Extend Squad delivery and commit flow | Reuse Squad's owner, shared role names, first assessments, correction closure, bounded support, deferred work and evidence applicability for mixed roles; preserve Writer/commit authority, native-only bindings and no additional technical review. | Planned | TASK-153 |
| TASK-155 | Complete Squad mixed recovery and configuration reporting | Recover native/external operations and settled correction evidence without replay, settle modifying descendants, retain role routes and observed configuration limits, and clean up only owned helpers without host-wide audits. | Planned | TASK-154 |
| TASK-156 | Verify Squad mixed delivery and promote documentation | Observe named installed mixed delivery with scoped corrections, cross-Task escalation, support and resumed-control limits; verify native-only/legacy preservation and recovery, then promote implemented contracts without overstating unobserved routes. | Planned | TASK-155 |

## EPIC-029: Add directory AGENTS.md documentation indexes

**Status:** `Completed`

Connect implementation features to their canonical requirements, architecture,
decisions and development guidance through scoped directory `AGENTS.md` files.
Keep the root documentation-discovery and update rules with `dev-setup`.
Make `docs-setup` own directory guidance structure, initial adoption and
migration for both greenfield and brownfield projects. Delivery workflows
maintain the affected guidance before candidate review and commit.

Large existing repositories require an explicitly scoped documentation-adoption
job. Ordinary development setup does not perform a repository-wide feature
analysis. Preserve existing guidance and canonical paths, distinguish initial
coverage from ongoing maintenance, and keep documentation checks separate from
observed agent behavior.

The shared directory-guidance contract and root/new-project source boundaries
are defined. Documentation setup now defines source-grounded guide mappings,
explicit coverage, preservation and migration. Task and Epic delivery now maintain
affected canonical documents and guides before review and preserve the accepted
composition through commit. Cross-workflow path regressions and manual VM
scenarios are prepared under [the testing authority](../../TESTING.md#directory-guidance-verification).
Installed Codex observations cover root setup, scoped adoption, migration and
affected Task/Epic delivery with Podway opted out in the dedicated UTM VM.
Native automatic loading, partial-write recovery, production-scale behavior,
the Podway-backed handler path and complete standalone cold validation
remain unverified.
Structural checks and agent-run observations do not replace Master's functional
verification or release acceptance. Existing projects remain usable before
explicit adoption; a missing directory guide alone adds no workflow blocker.
Source changes do not install the candidate, adopt guidance here or roll it out
to other projects.

**Canonical Outcomes:** [Workflow specification](../specs/workflow-contracts.md#directory-agent-guidance), [component ownership](../architecture/components.md#directory-documentation-flow), [maintenance guidance](../implementation-tips/changing-skills.md#maintain-directory-guidance), [shared contract](../../plugins/aquarium/references/directory-agent-guidance.md), [verification scenarios](../../tests/vm/directory-agent-guidance.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-157 | Define directory guidance ownership and lifecycle | Define scoped guidance, canonical links, root-versus-directory ownership, declared adoption coverage, maintenance and compatibility; verify any executable changes within this Task. | Completed | None |
| TASK-158 | Add directory guidance to documentation setup | Extend audit, bootstrap, adopt and migrate with source-grounded discovery, exact proposals, recorded coverage and preserved rules; include focused tests for this Task's executable changes. | Completed | TASK-157 |
| TASK-159 | Maintain guidance during Task and Epic delivery | Read applicable guidance, update affected canonical documents and indexes before review, and preserve exact reviewed content through acceptance and commit. | Completed | TASK-158 |
| TASK-160 | Add cross-workflow regressions and verification scenarios | Add integration regressions across adoption, migration and delivery; prepare testing-authority updates, manual scenarios and fixtures for installed verification. Earlier Tasks retain their own acceptance tests. | Completed | TASK-159 |
| TASK-161 | Verify installed workflows and promote canonical documentation | Observe candidate-bound setup and delivery in the dedicated UTM VM, record actual verification limits and promote implemented outcomes before Epic closeout. | Completed | TASK-160 |

## EPIC-030: Unify Aquarium delivery across five agent hosts

**Status:** `Planned`

Deliver Codex, Claude Code, Grok, ZCode/GLM and AGY packages from one Aquarium
development and distribution repository. Share workflow meaning, role instructions,
authority and evidence contracts; keep native invocation, configuration, agent
lifecycle and package layout in host-specific implementations. Each generated
package must be self-contained and reproducible without an installation-time
generator or a separately maintained edition source repository.

This is a breaking migration for existing edition users. Preserve existing Codex
behavior, public workflow names, retained Procedure bytes and admitted sessions;
verify those requirements against exact candidates. Initial qualification covers
all five hosts in the dedicated UTM VM. Model agreement and source checks do not
prove installed support or grant publication and legacy-repository archival.
Existing EPIC-019, EPIC-027 and EPIC-028 keep their own scope and status; none is
an automatic prerequisite. Each Task owns its focused verification before the
integrated qualification Task. Final completion includes the authorized distribution
cutover and Master's overall acceptance.

**Detailed SOT:** [Multi-host unification dossier](../todo/TODO-MULTI-HOST-UNIFICATION.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-162 | Freeze host capabilities and migration acceptance | Record exact sources and native versions, capability and paired-tool availability, installation/authentication feasibility, edition differences and required migration evidence; expose blocking gaps. | Planned | None |
| TASK-163 | Separate shared instructions from host invocation | Define host-neutral entrypoint, implicit-selection and delegation semantics; factor reusable role/phase instructions while preserving public names, native permissions, Procedure bytes and recovery. | Planned | TASK-162 |
| TASK-164 | Build host packages and preserve Codex behavior | Allocate all five package identities and roots, implement deterministic self-contained packaging, preserve Codex behavior and extend version/full-light release contracts across outputs. | Planned | TASK-163 |
| TASK-165 | Integrate Claude Code | Implement and verify native skill gates, delegation, agents, MCP, hooks and host-scoped discovery without imposing edition workarounds on shared workflows. | Planned | TASK-164 |
| TASK-166 | Integrate Grok | Implement and verify native invocation, setup, hooks, agent lifecycle and scoped discovery, including Claude auto-discovery and name collisions. | Planned | TASK-164 |
| TASK-167 | Integrate ZCode | Implement and verify native packaging, setup, discoverability and supported roles; apply the Herdr ZCode Executor policy only within its integration scope. | Planned | TASK-164 |
| TASK-168 | Integrate AGY | Implement and verify version-grounded native plugin, staging, hooks, configuration, delegation and skill-limit behavior without assuming Claude parity. | Planned | TASK-164 |
| TASK-169 | Qualify five-host installation and recovery | Observe all five exact candidate packages in the dedicated UTM VM, covering discovery, workflow progression, authority failures, coexistence, prior-edition upgrade, state preservation and recovery. | Planned | TASK-165, TASK-166, TASK-167, TASK-168 |
| TASK-170 | Cut over single-repository distribution | Extend installed release acceptance, publish through the authorized release lifecycle and migrate legacy distribution to temporary mirrors or redirects followed by authorized archival or read-only retention. | Planned | TASK-169 |
| TASK-171 | Promote canonical documentation and close the Epic | Promote accepted contracts and migration guidance, obtain Master's overall acceptance, replace temporary links and delete the dossier only within the approved last-consumer closeout. | Planned | TASK-170 |

## EPIC-031: Adopt Coordinator, Evaluator and Executor roles in release workflows

**Status:** `Planned`

Extend ordinary v3 orchestration to `release-handler`. The Coordinator retains
scope, actual approvals, commit and publication control; Executors deliver
bounded preparation, edits, checks and corrections; an independent report-only
Evaluator assesses original release requirements and current evidence at plan,
QA readiness, publication readiness and publication completion boundaries.

Preserve repository release policy, full/light distinctions, release-QA scenario
agents and original verdicts, exact candidate bindings, gate convergence and
publication recovery. Evaluator passage supplies no execution or publication
authority. Publication readiness follows repository-defined gate/commit order and
must hold before the first publication mutation. Treat the mandatory continuation
contract change as breaking: finish active releases before updating, and run
installation-dependent verification only in the dedicated UTM VM. Each
implementation Task owns its focused checks. Integrated verification does not
replace them or Master's overall acceptance.

Begin after EPIC-019 completes its pilot and canonical adapter handoff, and build
on completed EPIC-024 and EPIC-026 contracts. EPIC-030 retains ownership of
multi-host packaging and distribution and is not a prerequisite.
Between EPIC-030 and this Epic, whichever lands second reconciles the current output inventory, shared
release contracts and verification scenarios without assuming new host support.
This registration changes documentation only and establishes no implemented or
installed release-role support.

EPIC-019 supplies the completed Haepari setup, VM adapter and policy cutover through Canonical Outcomes. This Epic requires those inputs and verifies their integration with release roles using original Job/result/cleanup evidence and native queue/recovery; there is no pre-adoption manual qualification route within this Epic. EPIC-032 follows this Epic and separately owns producer rollout and Mulgae advisory integration. No second scheduler, report schema or review-lock wrapper is introduced. Assessment success, native outcome and resource return remain separate states.

**Detailed SOT:** [Release orchestration dossier](../todo/TODO-RELEASE-ORCHESTRATION.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-172 | Define release orchestration and authority boundaries | Reuse ordinary v3 roles and four assessments; identify applicable VM path, resource, occupancy and cleanup ownership alongside gate order, evidence and preserved approvals. | Planned | EPIC-019; EPIC-024; EPIC-026 |
| TASK-173 | Integrate release preparation and QA handoffs | Delegate bounded preparation and corrections, assess exact QA-ready candidates and any policy-due original VM evidence without changing QA verdicts or confirmation authority. | Planned | TASK-172 |
| TASK-174 | Integrate release gates, publication and recovery assessments | Support both gate/commit orders and original result binding; reconcile an existing Haepari Job before Executor replacement or redispatch and preserve cleanup evidence, convergence and publication authority. | Planned | TASK-173 |
| TASK-175 | Prepare integrated regressions and manual verification scenarios | Prepare native-role scenarios for both gate orders, bounded release-handler startup, and applicable VM queue/manual hold/cancel/reconnect/cleanup failures without duplicate dispatch. Earlier Tasks retain focused checks. | Planned | TASK-174 |
| TASK-176 | Verify installed release orchestration and promote outcomes | Observe native role progression against the exact installed candidate and applicable VM path, retain original Job/result/cleanup facts when adopted, promote outcomes and settle the dossier after actual acceptance. | Planned | TASK-175 |

## EPIC-032: Adopt Haepari across integrated tools

**Status:** `Planned`

Begin after completed EPIC-031, consuming the completed EPIC-019 adapter and release-role Canonical Outcomes. TASK-091 through TASK-099 keep their existing IDs and fixed producer order: Podway -> Mulgae -> Gaori -> Sorage -> Sanho -> Dolgorae -> Gul -> Seongge -> Gaebokchi. Each producer owns its implementation, local work IDs, skills, migration and native legacy detachment; Aquarium accepts a correlated real implementation return before dispatching the next.

TASK-092 requires Mulgae's released native CLI/MCP advisory-lock implementation and complete skill, not merely a Haepari fixture or request acknowledgement. Preserve native authority, exact installed evidence, shared-VM identity, original Job recovery, advisory limits and host isolation. Shared legacy infrastructure remains until EPIC-033. This planning registration sends no messages or starts implementation.

Close this Epic after independent validation of all nine returns, promotion of accepted per-product contracts/identity/profile/detachment inventories, Master's overall acceptance and its own dossier deletion. EPIC-033 consumes those durable outcomes and performs full-combination verification and common retirement; it does not retain this dossier or inherit unfinished producer criteria.

**Detailed SOT:** [Integrated-tool rollout dossier](../todo/TODO-HAEPARI-TOOL-ROLLOUT.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-091 | Freeze producer packets and accept Podway | Freeze packets from completed EPIC-019/031 outcomes, send the authorized Podway request and accept its real implementation, skill/migration and native detachment evidence. | Planned | EPIC-031; TASK-090; external Podway implementation return |
| TASK-092 | Delegate and accept Mulgae | Accept a released producer-owned CLI/MCP advisory-lock implementation with acquisition before live qualification, renewal, terminal release, borrower checks, native recovery and installed VM/skill/migration evidence; then adopt its released floor without an outer lock wrapper. | Planned | TASK-091; external Mulgae implementation and released CLI/skill return |
| TASK-093 | Delegate and accept Gaori | Request and accept Gaori-owned VM tests, both native skills, waiting/output and migration evidence, and legacy detachment through Sorage. | Planned | TASK-092; external Gaori implementation return |
| TASK-094 | Delegate and accept Sorage | Request and accept guest-only broker/Vault/configuration migration and skill tests while stable host Sorage remains the rollout control plane. | Planned | TASK-093; external Sorage implementation return |
| TASK-095 | Delegate and accept Sanho | Request and accept native commit/push/configuration tests using disposable remotes, full skill verification and safe legacy detachment. | Planned | TASK-094; external Sanho implementation return |
| TASK-096 | Delegate and accept Dolgorae | Request and accept current native lifecycle/configuration migration, skill and failure-recovery tests while preserving independent Haepari supervision. | Planned | TASK-095; external Dolgorae implementation return |
| TASK-097 | Delegate and accept Gul | Request and accept installed UI/backend compatibility, configuration migration, applicable skill inventory and representative hands-on evidence. | Planned | TASK-096; external Gul implementation return |
| TASK-098 | Delegate and accept Seongge | Request and accept current skill-evaluation/package/backend tests, migration and explicitly scoped live/manual evidence without reviving legacy expansion. | Planned | TASK-097; external Seongge implementation return |
| TASK-099 | Delegate and accept Gaebokchi | Request and accept provider/account/output and configuration migration tests with guest-only identities and evidence-backed skill/legacy applicability. | Planned | TASK-098; external Gaebokchi implementation return |

## EPIC-033: Qualify the combined environment and retire the development channel

**Status:** `Planned`

Begin after completed EPIC-032 and consume EPIC-019, EPIC-031 and EPIC-032 Canonical Outcomes. Existing TASK-100 through TASK-102 own exact whole-combination installed/upgrade verification, shared VM and released Mulgae lock behavior, original Job evidence consumed by release assessments, common legacy source cleanup and separately approved final host removal. Individual producer passes do not establish combined compatibility. TASK-100 owns bounded Aquarium corrections and producer correction requests through EPIC-032's promoted Sorage protocol, accepts corrected returns and re-verifies the exact combination. Preserve native outcomes, manual gaps, meaningful prior state and production/history boundaries.

This Epic also simplifies the accumulated Haepari integration before final acceptance. TASK-100 identifies redundant Aquarium layers, validators and harness code; TASK-101 removes or simplifies them and their obsolete tests, retaining code with a concrete consumer requirement. Delegate native Job and lock behavior to Haepari. TASK-102 verifies the final simplified combination, including recovery and cleanup; earlier passes do not qualify changed code. This planned work does not claim that EPIC-019 already delivered a minimal implementation or authorize immediate host activation.

The retained legacy development dossier is this Epic's historical/migration reference. After required independent validation and Master's actual overall acceptance, promote durable outcomes, replace this Epic's Detailed SOT and resolve EPIC-002's historical dossier references without changing its Cancelled status or completed history. Delete only this Epic's dossier and the settled legacy dossier under their exact closeout envelope. Earlier Epic dossiers are already settled; no earlier Epic is reopened merely to finish this sequence.

**Detailed SOT:** [Combination qualification and retirement dossier](../todo/TODO-HAEPARI-COMBINATION-RETIREMENT.md)

The [legacy dossier](../todo/TODO-AQUARIUM-DEV.md) remains a retirement reference until this Epic's approved reference reconciliation and settlement.

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-100 | Reconcile the full combination and upgrade path | Verify the exact installed/upgrade combination, shared VM, native review lock, release assessment inputs and cleanup; identify redundant integration layers and own bounded corrections and corrected producer returns. | Planned | EPIC-032; TASK-099 |
| TASK-101 | Retire shared legacy source and simplify Haepari integration | Remove redundant layers, validators, harness code and obsolete tests alongside common legacy dependencies; preserve required behavior and production history, with final host cleanup separately approved. | Planned | TASK-100 |
| TASK-102 | Cold-validate, promote documentation and close out | Verify the final simplified combination's managed VM, released Mulgae lock, recovery and cleanup behavior; obtain actual overall/manual acceptance, promote durable contracts and settle dossiers at last-consumer closeout. | Planned | TASK-101 |


## EPIC-034: Adopt Podway v0.2.15 and contract generation 2

**Status:** `In Progress`

Raise the supported stable release floor to v0.2.15 without an upper bound, pin the official runtime skill, and select contract generation 2 throughout current Aquarium integrations. This is breaking: existing v0.2.14 runtime state requires its original writer and an explicitly authorized fresh-runtime reset before use with the new writer. Candidate installation and functional verification must pass in the dedicated UTM VM before support is accepted.

**Detailed SOT:** [Podway v0.2.15 adoption](../todo/TODO-PODWAY-0215.md)

| Task | Title | Summary | Status | Depends On |
| --- | --- | --- | --- | --- |
| TASK-177 | Align the released generation-2 contract | Update the supported floor, release-pinned skill, command rules and original-writer upgrade guidance. | In Review | External Podway v0.2.15 release |
| TASK-178 | Adopt generation 2 in native consumers | Select generation 2 in setup and shared native calls, require observation v6, preserve status v5 and native recovery details. | In Review | TASK-177 |
| TASK-179 | Qualify the exact official release | Preserve all five Procedure scenarios and add generation-2 lifecycle, stale-fence, replay and v0.2.14 writer-refusal coverage. | In Review | TASK-178 |
| TASK-180 | Verify the installed upgrade and promote outcomes | Prepare separate released/candidate VM identities, verify the installed combination under explicit VM authority, complete independent review and promote durable contracts. | In Progress | TASK-179 |
