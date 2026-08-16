---
name: task-review
description: "Run and resolve Mulgae review for one complete roadmap task diff. Use when $root-kernel:task-handler delegates review or when the user explicitly invokes $root-kernel:task-review with exact task identity, current verification evidence, and a safely isolatable review target."
---

# Task Review

Review only the complete implementation, tests, refinement, and review-state documentation for the task established by `$root-kernel:task-handler`. When invoked directly, require the repository, roadmap path, task ID, and current task-owned diff.

Fixing findings in this phase changes the diff, so all affected prior phase evidence is stale — including implementation and verification evidence when a fix changes behavior or tests; the handler then selects `changes-requested` and reworks to the phase that owns the change, and only a pass with no file changes supports `approved`.

## Run and Resolve the Mulgae Review

1. Follow repository-specific Mulgae instructions when present.
2. Verify that a supported Mulgae CLI and both Config v3 authorities are healthy; do not install, initialize, bootstrap, refresh, author credential profiles, or configure MCP here. If missing or unhealthy, keep the task in review and return an exact `$root-kernel:dev-setup` continuation request.
3. Reference `$use-mulgae` and follow it when available, preferring its attached MCP workflow. If the skill or MCP is unavailable and repository guidance requires it, keep the task in review and route that exact gap to `$root-kernel:dev-setup`; otherwise report the unavailable integration once and use the CLI fallback below. Do not start a second MCP server from the shell.
4. Select exactly one target that contains the complete task diff and excludes unrelated work. A clean task-only dirty state may use `--dirty` to capture staged and unstaged changes; otherwise use another exact supported target and stop if isolation is unsafe.
5. Run execution-free preflight through the selected interface, require `mulgae-review-preflight.v3`, and inspect captured files, exclusions, roles, credential-profile routing, provider timeouts, permission modes, and artist inputs when UI work is present.
6. Run the review once with machine-readable output and require `mulgae-command-result.v3` from the CLI fallback. Preserve the exact returned run identity, then inspect authoritative run status and findings even when the review returns a policy outcome or typed operational failure; never blindly retry an uncertain review mutation.

For CLI fallback, replace `<target-flag>` with exactly one authorized target and keep the returned `r_...` identity fenced across the reads:

```bash
mulgae review <target-flag> --preflight --output json
mulgae review <target-flag> --output json
mulgae status --run r_... --output json
mulgae findings --run r_... --severity low --output json
```

The preflight payload must be `mulgae-review-preflight.v3`; every CLI command envelope must be `mulgae-command-result.v3`. Exit `1` is a policy outcome whose envelope still requires inspection. For any typed operational failure or allocated-but-uncertain run identity, inspect status once and stop instead of resubmitting the review.
7. Treat every finding as an advisory hypothesis. Verify it against the roadmap, current code, and tests before changing anything.
8. Fix every valid in-scope finding, add regression coverage where useful, and run finding-specific follow-up when supported.
9. Re-run affected checks and final repository gates after fixes. Preserve the task-owned staging and unrelated-work boundaries established by the orchestrator.

## Bound the Evidence

Treat Mulgae as complete only when `coverage_status=complete`, `ci_decision=pass`, `publication_status=committed`, the findings query succeeds, and zero unresolved valid findings remain. Provider success or exit status alone is insufficient.

Do not count a cancelled lane, operational failure, incomplete capture, unavailable findings query, or unverified finding as successful review evidence. Do not commit or publish in this phase.

Mulgae retains complete provider stdout and stderr without a product byte ceiling. Keep raw transcripts and credential-profile paths in private Mulgae runtime state.

Verify every finding locally, but bound the orchestrator handoff to counts by severity and disposition plus at most 20 highest-severity records containing only finding ID, severity, disposition, and affected repository-relative paths.

When more remain, include the omitted count and authoritative run/findings identity or digest. Never include descriptions, quotes, credential-profile paths, or raw provider payloads.

Return the exact target, preflight summary, run and session IDs, command exit codes, findings with dispositions, finding-fix paths, follow-up evidence, and remaining operational gaps to the orchestrator.
