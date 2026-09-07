---
name: new-project
description: "Shape a greenfield project into an approved PRD and initial roadmap with Ouroboros, without implementing it. Use when the user explicitly invokes $aquarium:new-project."
---

# New Project

Create a PRD and initial roadmap for one new project. Do not implement code, initialize Git, stage, commit, or publish.

Always read [evidence-residency.md](../../references/evidence-residency.md), then read [ouroboros-integration.md](../../references/ouroboros-integration.md), [documentation-governance.md](../../references/documentation-governance.md), and [epic-execution-sot.md](../../references/epic-execution-sot.md). For a Git-backed project, use the default `aquarium-design-v2` Podway path. For a non-Git project, skip Podway completely without skipping the evidence-residency contract.

Establish the project identity, users, problem, outcomes, exclusions, constraints, risks, dependencies, delivery slices, acceptance evidence, and implementation ownership. Use installed upstream `$interview` and `$pm` only after the approved execution envelope.

Select `single-scope` when one implementation owner has one roadmap. Select `multi-scope` when independently delivered surfaces need separate roadmaps; ask only when ownership remains ambiguous. Produce a user-facing root README, maintainer-facing `docs/README.md`, a PRD, one initial roadmap per delivery scope, and every role index including operations. Apply the shared execution-SOT threshold to each initial epic and create its scope-local dossier only when required.

The PRD owns product intent; each created dossier owns temporary implementation scope and acceptance until closeout. Use the shared default `EPIC-NNN` and per-roadmap `TASK-NNN` contract. Do not add a repository-local Aquarium state file or documentation validator.

Include a testing-foundation work unit that establishes `aquarium-test-contract/v1` through a later explicit `$aquarium:test-setup` invocation. Read the shared [setup prerequisites](../test-setup/references/contract.md#setup-prerequisites) and make the work unit depend on the implementation that supplies them. If `EPIC-001` delivers a testable walking skeleton, place this work unit as its final task. Otherwise place it immediately after the earliest vertical slice that supplies the prerequisites and before broader feature expansion.

Record the tasks that establish the prerequisites and the evidence required to accept them in the roadmap. Make subsequent feature expansion depend on the testing-foundation work unit. Planning documents alone do not satisfy those dependencies. Keep tests needed to verify the preceding implementation in its own tasks. A new project is not eligible for a legacy waiver.

Run upstream `$qa` on the draft, adjudicate every issue, then present the exact paths and complete proposed diff. Apply documents only after explicit approval and snapshot recheck. Report resulting paths, validation, unresolved decisions, and the exact next explicit skill; do not begin delivery.
