---
name: task-verify
description: "Strengthen and verify evidence for one implemented roadmap task. Use when $root-kernel:task-handler delegates verification or when the user explicitly invokes $root-kernel:task-verify to resume that phase with an implemented task diff and exact task identity."
---

# Task Verify

Verify the implemented task established by `$root-kernel:task-handler`. When invoked directly, require the repository, roadmap path, task ID, approved requirements, and exact task-owned diff.

Build a requirement-to-test matrix from the roadmap rather than assuming fixed test folders. Consider only applicable layers:

- formatting, linting, static analysis, type checking, architecture rules, and builds;
- unit, component, widget, or module tests;
- integration, contract, protocol, persistence, and migration tests;
- end-to-end, system, smoke, device, browser, or live-service tests;
- security, concurrency, recovery, performance, and regression checks.

Inspect existing coverage before adding tests. Add coverage for observable requirements, failure behavior, lifecycle races, persistence boundaries, and runtime wiring that are not already proven. Do not create a test layer the project does not use merely to satisfy a label; record it as not applicable with evidence.

Before running a check, account for current user-run evidence. When the user explicitly confirms that an exact command or equivalent applicable test passed against the current task diff, record it as user-run evidence and do not rerun the same check merely to duplicate it. Ask whether the evidence covers the current diff when its revision or scope is unclear. Any affected task-owned change after that run makes the evidence stale. Repository-mandated agent checks, uncovered requirements, and checks needed to diagnose task-caused failures still run normally.

Run focused checks first, then repository-required broader gates. Treat the underlying process exit status as authoritative when an evidence-compression wrapper is used. If an applicable E2E gate cannot run under repository policy or the current environment, request or accept explicit user-run evidence and keep the phase incomplete until it exists.

Do not stage, update lifecycle documentation, invoke Mulgae, commit, or publish in this phase. Return the matrix, agent-run and user-run commands, exit codes, skipped layers, task-caused failures, pre-existing failures, and unresolved evidence gaps to the orchestrator.
