---
name: task-review
description: "Run and resolve Mulgae review for one complete roadmap task diff. Use when $root-kernel:task-handler delegates review or when the user explicitly invokes $root-kernel:task-review with exact task identity, current verification evidence, and a safely isolatable review target."
---

# Task Review

Review only the complete implementation, tests, refinement, and review-state documentation for the task established by `$root-kernel:task-handler`. When invoked directly, require the repository, roadmap path, task ID, and current task-owned diff.

Read [podway-integration.md](../../references/podway-integration.md). In an opted-in orchestrated run, confirm read-only that the matching `root-kernel-task-v2` session is at `review`. Return the exact target, run identity, coverage and publication states, findings-query result, dispositions, and unresolved-valid-finding count; the handler alone records review evidence and selects its decision.

Fixing findings in this phase changes the diff, so all affected prior phase evidence is stale — including implementation and verification evidence when a fix changes behavior or tests; the handler then selects `changes-requested` and reworks to the phase that owns the change, and only a pass with no file changes supports `approved`.

## Run and Resolve the Mulgae Review

1. Follow repository-specific Mulgae instructions when present.
2. Otherwise verify that Mulgae is callable and configured; do not install or initialize it. If missing or unhealthy, keep the task in review and return an exact `$root-kernel:dev-setup` continuation request.
3. Select exactly one target that contains the complete task diff and excludes unrelated work. A clean task-only dirty state may use `--dirty` to capture staged and unstaged changes; otherwise use another exact supported target and stop if isolation is unsafe.
4. Run preflight and inspect captured files, exclusions, roles, provider routing, timeouts, permission modes, and artist inputs when UI work is present.
5. Run the review with machine-readable output, then inspect run status and findings even when review returns a policy-failure exit code.
6. Treat every finding as an advisory hypothesis. Verify it against the roadmap, current code, and tests before changing anything.
7. Fix every valid in-scope finding, add regression coverage where useful, and run finding-specific follow-up when supported.
8. Re-run affected checks and final repository gates after fixes. Preserve the task-owned staging and unrelated-work boundaries established by the orchestrator.

## Bound the Evidence

Treat Mulgae as complete only when `coverage_status=complete`, `ci_decision=pass`, `publication_status=committed`, the findings query succeeds, and zero unresolved valid findings remain. Provider success or exit status alone is insufficient.

Do not count a cancelled lane, operational failure, incomplete capture, unavailable findings query, or unverified finding as successful review evidence. Do not commit or publish in this phase.

Return the exact target, preflight summary, run and session IDs, command exit codes, findings with dispositions, finding-fix paths, follow-up evidence, and remaining operational gaps to the orchestrator.
