---
name: task-verify
description: "Strengthen and verify evidence for one implemented roadmap task. Use when $aquarium:task-handler delegates verification or when the user explicitly invokes $aquarium:task-verify to resume that phase with an implemented task diff and exact task identity."
---

# Task Verify

Verify the implemented task established by `$aquarium:task-handler`. When invoked directly, require the repository, roadmap path, task ID, approved requirements, and exact task-owned diff. Read [evidence-residency.md](../../references/evidence-residency.md) before consuming or returning runtime evidence.

## Build the Requirement-to-Test Matrix

When root `TESTING.md` registers `aquarium-test-contract/v1`, read it with the executable Makefile or Bun scripts. Treat their documented complete aggregate as the repository-wide gate, reject stale or unapproved waivers, and keep any required stage that did not run as an evidence gap. A disagreement between `TESTING.md` and the executable handlers is a contract defect; do not choose whichever command is easier to run. An unenrolled repository retains its established local test authority and is not enrolled implicitly during task verification.

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

When a selected long or noisy check is routed through Gaori, reference `$use-gaori` and follow its current CLI-or-MCP workflow when available.

- Prefer one `start_configured_run` or `start_ad_hoc_run` followed by `await_run` on the same invocation when the complete tool surface is connected and the effective host timeout covers the command plus evidence finalization.
- When that deadline is missing, unverified, or inadequate, preserve the invocation and use `get_run` or bounded `wait_run` observation instead. Never repeat the start merely because an await was cancelled or timed out.
- The installed skill owns read-only `list_runs` discovery for completed standalone evidence and the CLI fallback. Do not reconstruct its execution, cancellation, cleanup, artifact, or recovery procedure here.

If the skill is unavailable and repository guidance requires it, return an exact `$aquarium:dev-setup` continuation request. Otherwise run the repository's original documented test command directly and report that Gaori evidence compression was unavailable; if the original command cannot be established from repository authority, leave an evidence gap instead of inferring it from conversation memory.

Keep the executed command result separate from Gaori artifact `status`, `extractor_status`, and truncation. Gaori evidence never selects a required gate or establishes acceptance. Include the Gaori invocation, process exit, evidence-quality fields, relevant summary paths, whether raw evidence was opened, and skipped checks in the orchestration handoff, marking every `.gaori/runs/**` path as local runtime evidence that must not be copied into tracked documentation.

Do not stage, update lifecycle documentation, invoke Mulgae, commit, or publish in this phase.

Return the matrix, agent-run and user-run commands, exit codes, Gaori evidence metadata when applicable, skipped layers, task-caused failures, pre-existing failures, and unresolved evidence gaps to the orchestrator.
