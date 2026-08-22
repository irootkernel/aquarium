---
name: independent-review
description: "Run one supervised, read-only requirements and code review with a fresh Codex in the current Orca worktree, then adjudicate its findings and propose responses without making changes. Use when the user explicitly invokes $aquarium:independent-review with exactly one epic or task and asks to receive the independent review result."
---

# Independent Review

Coordinate exactly one fresh Codex reviewer through Orca, preserve the current checkout, and independently verify the returned findings before recommending any response. This is a standalone review workflow, not the Mulgae phase owned by `$aquarium:task-review`.

## Establish the Review Contract

1. Require exactly one epic or task identifier and one current Git repository. Resolve the repository root, applicable instruction files, and the authoritative roadmap, requirements, specifications, decisions, and contracts for that identifier.
2. Inspect HEAD, branch, upstream, staged, unstaged, untracked, and conflicted state. Define the exact review snapshot and distinguish target-owned changes from unrelated work. Include committed, staged, and unstaged target code when applicable; never expose unrelated untracked content merely because it is present.
3. Treat the user's statement that tests passed as context. Do not rerun tests, generators, formatters, linters, provider reviews, or other validation commands in either the coordinator or reviewer.
4. If the target authority or review boundary cannot be established safely, ask one focused question and do not start a worker until the ambiguity is resolved.

Explicit invocation authorizes starting Orca when installed and launching one supervised Codex reviewer in the current worktree. It does not authorize source edits, staging, commits, pushes, worktree creation, destructive actions, Mulgae, or remediation.

## Fail Closed on Orca

1. Resolve the Orca executable exactly as the installed `$orca-cli` skill requires and reuse that selection. Do not fall through to another executable when the selected command is missing or fails.
2. Load the version-matched guides with the selected executable's `skills get orca-cli` and `skills get orchestration` commands before using Orca. Follow those live guides rather than cached command syntax.
3. Confirm the runtime with `status --json`. When the CLI exists but the app is stopped, attempt `open --json` once and confirm status again.
4. Stop with the exact error and recovery requirement when the CLI is unavailable, the selected executable fails, the runtime cannot start, orchestration is disabled, or Run, Task, or Dispatch provenance cannot be verified.

Never substitute a generic subagent, chat delegation, ad hoc PTY, raw agent CLI, another Orca executable, or the coordinator's own review. An operational failure is not an `APPROVE` result.

## Dispatch One Fresh Reviewer

Create or bind one Run, create one review Task, and use the live guide's supervised `worker-start` path with `--worktree current --agent codex`. Do not reuse an existing terminal and do not create another Git worktree. Honor an explicitly requested Codex model and effort when supported; otherwise use Orca's defaults.

Build the Task specification from source evidence, including the absolute repository, target identifier, authority paths, exact review snapshot or range, relevant staged and unstaged state, and the fact that tests already passed. Do not include the coordinator's suspected findings or intended fixes.

Require the reviewer to:

- read applicable instructions, requirements, contracts, code, and relevant existing tests;
- remain strictly read-only and run no tests, generators, formatters, linters, or provider reviews;
- report only verified, actionable findings and omit style preferences, speculation, and praise;
- separate production defects from required test, specification, or current-documentation gaps;
- give each finding a severity, exact `path:line`, triggering scenario, violated requirement, impact, and smallest remediation;
- return exactly `APPROVE` when no actionable finding remains;
- leave the detailed review in its final response, report no modified files, and send `worker_done` exactly once through the injected Orca lifecycle.

## Supervise and Settle

Before dispatch, disclose and record one cumulative liveness budget, using 30 minutes unless the user explicitly selected another duration. Use rolling waits for `worker_done`, `escalation`, and `question`, keeping each wait short enough to provide a user update at least once per minute and charging every wait against the same remaining budget.

Treat a timeout or empty delivery inside that budget as a liveness checkpoint, not a failure. Answer reviewer questions only from established repository facts; ask the user when an answer requires product intent or wider authority.

When the cumulative budget expires without an accepted terminal delivery, inspect the authoritative worker and terminal state once through the live guide, stop waiting, leave any active worker intact, and report the review as operationally incomplete with the exact Run, Task, Dispatch, terminal, and lifecycle status. Further waiting or cancellation requires an explicit user request; never release, retry, cancel, or replace the active worker automatically.

For an accepted `worker_done`, retrieve the complete worker transcript, process every delivered message, release the settled worker, and acknowledge the delivery only after the release decision. Release both succeeded and failed settled workers unless the user explicitly requested retention.

Acceptance opens one five-minute settlement budget of at most 16 Delivery batches, including the terminal batch. After processing every message and completing the required release, acknowledge that exact batch without waiting and inspect the acknowledgement response.

Process and acknowledge every returned heartbeat, duplicate or stale completion, question, or escalation under the same budget until no Delivery remains; do not release the already settled worker again. An unresolved question or escalation, release failure, or exhausted budget is an operational gap. Leave its Delivery unacknowledged for FIFO replay, preserve the lifecycle state, and require explicit user direction before any further drain.

Do not release an active worker after a timeout, question, escalation, heartbeat, or rejected or stale completion. Follow the live guide's exact recovery action and never blindly resend an exactly-once `worker_done`. Keep technical review evidence and Orca lifecycle settlement as separate statuses.

## Adjudicate the Result

Verify every reviewer finding against the current authority, code, callers, persistence boundaries, and existing tests without changing files or running checks. Classify each item as:

- **Valid**: confirmed and actionable; propose the smallest implementation and regression-coverage response.
- **Invalid**: contradicted by exact evidence; explain the contradiction briefly.
- **Needs confirmation**: plausible but dependent on missing authority or runtime evidence; state the precise evidence needed.

Do not implement a proposed response. If the reviewer returned `APPROVE`, first confirm that it examined the intended snapshot and authority, then report that no actionable feedback was found. If output is missing, scope is wrong, or orchestration failed, report the operational gap without a clean verdict.

Return the target and snapshot, independent reviewer verdict, adjudicated findings, recommended responses, and separate Orca Run, Task, Dispatch, and lifecycle status.
