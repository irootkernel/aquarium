---
name: task-review
description: "Run and resolve Mulgae review for one complete roadmap task diff. Use when $aquarium:task-handler delegates review or when the user explicitly invokes $aquarium:task-review with exact task identity, current verification evidence, and a safely isolatable review target."
---

# Task Review

Review only the complete implementation, tests, refinement, and review-state documentation for the task established by `$aquarium:task-handler`. Require the handler-provided positive review ordinal, current goal revision, and `remediation-eligible` or `confirmation-only` mode when delegated; a direct invocation is one isolated remediation-eligible round with ordinal one and grants no later-round budget.

One invocation consumes one round only after one root `review` run reaches committed publication with complete coverage and a successful findings query, including a `request_changes` policy outcome or failing CI decision. Preflight, status, findings and excerpt reads, and Mulgae-internal retry or extraction do not consume another round.

Fixing findings in this phase changes the diff, so all affected prior phase evidence is stale — including implementation and verification evidence when a fix changes behavior or tests; the handler then selects `changes-requested` and reworks to the phase that owns the change, and only a pass with no file changes supports `approved`.

## Run and Resolve the Mulgae Review

1. Follow repository-specific Mulgae instructions when present.
2. Verify that a supported Mulgae CLI and both Config v3 authorities are healthy; do not install, initialize, bootstrap, refresh, author credential profiles, or configure MCP here. If missing or unhealthy, keep the task in review and return an exact `$aquarium:dev-setup` continuation request.
3. Reference `$use-mulgae` and follow it when available, preferring its attached MCP workflow. If the skill or MCP is unavailable and repository guidance requires it, keep the task in review and route that exact gap to `$aquarium:dev-setup`; otherwise report the unavailable integration once and use the CLI fallback below. Do not start a second MCP server from the shell.
4. Select exactly one target that contains the complete task diff and excludes unrelated work. A clean task-only dirty state may use `--dirty` to capture staged and unstaged changes; otherwise use another exact supported target and stop if isolation is unsafe.
5. Run execution-free preflight through the selected interface, require `mulgae-review-preflight.v3`, and inspect captured files, exclusions, roles, credential-profile routing, provider timeouts, permission modes, and artist inputs when UI work is present.
6. Run the review once with machine-readable output and require `mulgae-command-result.v4` from the CLI fallback. Use the same bounded objective in preflight and execution, naming the task, current goal revision, review ordinal, and review mode. Preserve the exact returned run identity, then inspect authoritative run status and findings even when the review returns a policy outcome or typed operational failure.
   Mulgae preserves each accepted Markdown report byte-for-byte and may derive finding candidates through its private internal `002-extract` artifact. Its retry, repair, and extraction paths share the single second provider-invocation slot, so never run that artifact manually or add another review, qualification, heartbeat, extraction, or retry invocation.

For CLI fallback, replace `<target-flag>` with exactly one authorized target and keep the returned `r_...` identity fenced across the reads:

```bash
mulgae review <target-flag> --preflight --output json
mulgae review <target-flag> --output json
mulgae status --run r_... --output json
mulgae findings --run r_... --severity low --output json
```

The preflight payload must be `mulgae-review-preflight.v3`; every CLI command envelope must be `mulgae-command-result.v4`. Exit `1` is a policy outcome whose envelope still requires inspection. For any typed operational failure or allocated-but-uncertain run identity, inspect status once and stop instead of resubmitting the review.
7. Treat every finding as an advisory hypothesis. Verify it against the roadmap, current code, and tests before changing anything.
8. Verify and adjudicate every finding but do not change files. In `remediation-eligible` mode, return valid findings through the owning phase: to the handler when delegated, or to the invoking user with the exact `$aquarium:task-handler` continuation when invoked directly. In `confirmation-only` mode, return them unchanged for required user escalation.
9. Do not invoke `followup`, `delta`, `rerun`, or another root review inside this bounded invocation. Each is a separate immutable run and cannot bypass or substitute for the handler's next full-target review ordinal. On an incomplete or operationally failed run, follow recovery guidance and return without consuming a round or blindly resubmitting.

## Bound the Evidence

Treat a review round as operationally complete only when `coverage_status=complete`, `publication_status=committed`, the findings query succeeds, and the exact run has a terminal authoritative status. Record `ci_decision` independently: a failing decision or `request_changes` outcome still consumes the ordinal but cannot approve the task. Approval additionally requires `ci_decision=pass` and zero unresolved valid findings. Provider success or exit status alone is insufficient.

Record `structured_extraction_status` independently as `structured`, `mixed`, or `reports_only`. `reports_only` is not itself a failure and does not replace or relax any completion condition above; the accepted reports remain authoritative, and every extracted finding remains an advisory hypothesis that requires local verification.

Do not count a cancelled lane, operational failure, incomplete capture, unavailable findings query, or unverified finding as successful review evidence. Do not commit or publish in this phase.

Mulgae retains complete provider stdout and stderr without a product byte ceiling. Keep raw transcripts, accepted reports, extraction artifacts, and credential-profile paths in private Mulgae runtime state.

Verify every finding locally, but bound the orchestrator handoff to counts by severity and disposition plus at most 20 highest-severity records containing only finding ID, severity, disposition, and affected repository-relative paths.

When more remain, include the omitted count and authoritative run/findings identity or digest. Never include descriptions, quotes, credential-profile paths, or raw provider payloads.

Return the exact target, goal revision, review ordinal and mode, preflight summary, run and session IDs, command exit codes, operational-completion status, CI decision, findings with dispositions, and remaining operational gaps to the orchestrator.
