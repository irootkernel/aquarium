---
name: task-verify
description: "Strengthen and verify evidence for one implemented roadmap task. Use when $aquarium:task-handler delegates verification or when the user explicitly invokes $aquarium:task-verify to resume that phase with an implemented task diff and exact task identity."
---

# Task Verify

Verify the implemented task established by `$aquarium:task-handler`. When invoked directly, require the repository, roadmap path, task ID, approved requirements, and exact task-owned diff.

Read [design-gates.md](../../references/design-gates.md). Resolve the effective Design Gate impact from the task first and then its parent epic, applying the documented legacy-only `Not required` rule when neither marker exists. Stop when the effective marker is missing in an enrolled repository or is `Pending`.

For every inherited or task-explicit resolved active `GATE-*` ID, run its registered local offline procedure against the exact task snapshot with declared outputs and caches redirected to a disposable root, capture the objective pass condition and outcome, and verify that source-repository status is unchanged. Keep missing, stale, failed, mutating, or unexecutable gate evidence as a verification blocker.

## Build the Requirement-to-Test Matrix

Build a requirement-to-test matrix from the roadmap rather than assuming fixed test folders. Consider only applicable layers:

- formatting, linting, static analysis, type checking, architecture rules, and builds;
- unit, component, widget, or module tests;
- integration, contract, protocol, persistence, and migration tests;
- end-to-end, system, smoke, device, browser, or live-service tests;
- security, concurrency, recovery, performance, and regression checks.

Inspect existing coverage before adding tests. Add coverage for observable requirements, failure behavior, lifecycle races, persistence boundaries, and runtime wiring that are not already proven. Do not create a test layer the project does not use merely to satisfy a label; record it as not applicable with evidence.

## Account for Existing Evidence

Before running a check, account for current user-run evidence:

- When the user explicitly confirms that an exact command or equivalent applicable test passed against the current task diff, record it as user-run evidence and do not rerun the same check merely to duplicate it.
- Ask whether the evidence covers the current diff when its revision or scope is unclear.
- Any affected task-owned change after that run makes the evidence stale.
- Repository-mandated agent checks, uncovered requirements, and checks needed to diagnose task-caused failures still run normally.

## Run Checks in Order

Run focused checks first, then repository-required broader gates. Treat the underlying process exit status as authoritative when Gaori or another evidence-compression wrapper is used. If an applicable E2E gate cannot run under repository policy or the current environment, request or accept explicit user-run evidence and keep the phase incomplete until it exists. Stop and escalate to the orchestrator when a required gate is permanently blocked by repository policy, environment, or authority; never substitute a narrower check for it.

When a selected long or noisy check is routed through Gaori, reference `$use-gaori` and follow its current CLI-or-MCP workflow when available. The installed skill decides between all connected Gaori MCP tools, including read-only `list_runs` discovery for completed standalone evidence, and the CLI fallback; do not reconstruct its execution, cancellation, cleanup, artifact, or recovery procedure here.

If the skill is unavailable and repository guidance requires it, return an exact `$aquarium:dev-setup` continuation request. Otherwise run the repository's original documented test command directly and report that Gaori evidence compression was unavailable; if the original command cannot be established from repository authority, leave an evidence gap instead of inferring it from conversation memory.

Keep the executed command result separate from Gaori artifact `status`, `extractor_status`, and truncation. Gaori evidence never selects a required gate or establishes acceptance. Include the Gaori invocation, process exit, evidence-quality fields, relevant summary paths, whether raw evidence was opened, and skipped checks in the handoff.

Do not stage, update lifecycle documentation, invoke Mulgae, commit, or publish in this phase.

Return the matrix, agent-run and user-run commands, exit codes, Gaori evidence metadata when applicable, skipped layers, task-caused failures, pre-existing failures, and unresolved evidence gaps to the orchestrator.
