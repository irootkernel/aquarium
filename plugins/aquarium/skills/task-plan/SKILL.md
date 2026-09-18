---
name: task-plan
description: "Plan one named roadmap task without mutation. Use when $aquarium:task-handler delegates its planning phase or when the user explicitly invokes $aquarium:task-plan to resume that phase with a repository, roadmap path, and exactly one task ID."
---

# Task Plan

Plan only one task. Require the repository, canonical roadmap path, and exact task ID established by `$aquarium:task-handler`; when invoked directly, reconstruct and validate those inputs before proceeding.

Read [epic-execution-sot.md](../../references/epic-execution-sot.md).

## Explore Without Mutation

Read applicable repository instructions, the task entry, its parent epic, the handler-resolved execution SOT and any active dossier, `docs/README.md`, every relevant canonical role owner, current architecture, Git state, existing tests, CI and task runners, documentation synchronization rules, and configured development-tool guidance. Resolve those authorities from the canonical roadmap; do not require the user to name document paths.

When invoked directly, perform the shared semantic discovery and return the resolved dossier or composite execution SOT to the owning handler. Do not create a dossier or route to `docs-setup`. When no dossier is declared, its absence is not a semantic gap by itself, but execution requires the shared explicit waiver. Treat a declared dossier whose link cannot be resolved as a semantic gap, and report the exact missing or ambiguous semantic owner when the canonical sources are incomplete. When the work meets a creation threshold, require the owning handler's prior choice to consider a waiver before preparing the final plan; otherwise return to the owning handler to obtain that choice.

Do not create a goal, edit files, generate code, run rewriting formatters, stage changes, invoke providers, or alter external state.

## Produce and Approve the Plan

Produce a decision-complete plan containing:

- the execution SOT source paths and requirement owners, with the active dossier or its explicit absence;
- goal, requirements, non-goals, lifecycle meaning, and task boundaries;
- current architecture observations and affected behavior;
- implementation approach and meaningful tradeoffs;
- requirement-to-verification matrix;
- specifications, architecture, decision, implementation-tip, operations, public-documentation, rollout, and review impact;
- exact repository-native verification commands;
- review finding remediation, affected checks, exact restaging of already staged affected paths, and any provider re-review budget;
- known permission, tool, provider, and environment gaps.

Ask once for explicit approval of the plan. When no dossier is declared, require the user to approve the plan and waive the dossier explicitly; generic plan approval, discussion, partial agreement, or approval of a different action is insufficient. When the work meets a creation threshold, this is the second confirmation after the user chose to consider a waiver. If approval or the required waiver is refused or withheld, stop, report the exact missing decision, and do not enter implementation. A material change to the approved source set or requirements requires an updated plan, renewed approval, and a renewed waiver when the revised source set still has no dossier.

If the host is in Plan mode, remain there and end with a continuation prompt that explicitly invokes `$aquarium:task-handler` with the same repository, roadmap path, task ID, and handler-selected mode. `plan-only` ends without mutation, while `plan-handoff` prepares the approved handoff rather than implementing it. Return the plan, approval state, inspected authority paths, and unresolved gaps to the orchestrator.
