# Orca Review Supervision

This is the execution backend for `$aquarium:orca-review`. Review semantics belong to [review-contract.md](review-contract.md); Orca owns only its native Run, Task, Dispatch, reviewer, Delivery, acknowledgement, settlement, and recovery lifecycle.

Require the separately installed `$orca-cli` skill. Resolve one Orca command exactly as that skill requires, load its version-matched `orca-cli` and `orchestration` guides, and confirm a ready local runtime. Reject nonempty `ORCA_ENVIRONMENT` or `ORCA_PAIRING_CODE`; do not route review source to a paired or remote runtime.

Use the original registered checkout and its proven `current` worktree. Do not create or register a temporary repository, copied checkout, snapshot, or another Git worktree. The declared target and included paths define reviewer scope; current worktree bytes outside that target are excluded even though the same operating-system user can technically read them.

Require the user to select a reviewer before creating the Run or Task. Then start one fresh requested reviewer through the live guide's supervised `worker-start --task <task-id> --worktree current --agent <requested-reviewer>` path. Use `--agent claude` when Claude is requested. Do not default to or substitute another reviewer. Do not reuse a terminal, create a low-level provider terminal, or use Dolgorae.

The Task contains the declared target, applicable resolved Git identity, review focus, authority paths, included and excluded state, static-review restrictions, and required report fields. Do not include suspected findings or intended fixes. Do not create a capture manifest, target digest binding, repository fingerprint, or pre/post state comparison.

Every Dispatch, regardless of target, must tell the reviewer that this is review only; absolutely prohibit creating, editing, deleting, moving, formatting, or generating any file in the current registered worktree; prohibit changes to the Git index, refs, configuration, or commits; prohibit tests, builds, formatters, installers, authentication, and unrelated network operations; require only actionable findings with severity and exact `path:line`; and require `APPROVE` when no actionable finding exists. Require the reviewer to read only the declared target. For `head`, `commit`, and `range`, require file content and diffs from the resolved revisions through read-only Git commands and prohibit substituting current index or worktree bytes.

For `staged`, additionally require inspection of `git diff --cached`, the relevant staged files, and their callers. Apply the corresponding target-specific read instructions to `head`, `commit`, and `range` without weakening the common restrictions.

Include the shared output permission in every Dispatch: All Orca reviewers may create or update review-related temporary files, native session state, tool output, and reports outside the current registered worktree. `/tmp`, `/private/tmp`, `$TMPDIR`, and `~/.claude` are examples, not an allowlist. The actual write destination must remain outside the worktree, including when a path traverses a symbolic link.

Include this distinction in every Dispatch: External tool output and reports may contain bytes of the declared target, including redirected `git diff --cached` or `git show` output read in pieces. These files are review aids; they do not replace the live index or resolved Git revisions as target authority.

Tell the reviewer to return the complete result through the Orca lifecycle message when it fits. Any reviewer may deliver a large report through external files with a concise lifecycle result and the paths of retained report files used to deliver the result. Read those reports before adjudication. Routine temporary files need no inventory. Aquarium does not automatically remove reviewer-owned files or treat them as repository state, capture evidence, or lifecycle authority. External review files alone must not trigger a rule-violation warning, an operational failure, a withheld verdict, or a demand for another review.

Use event-driven waits for `worker_done`, `escalation`, and `question`, with a cumulative 30-minute default liveness budget and a user update at least once per minute. A checkpoint timeout inside the budget is not failure. At budget exhaustion inspect authoritative worker state once, keep an active or unproven worker intact, and require explicit user direction for more waiting or cancellation.

After one accepted `worker_done`, read the complete authoritative transcript, settle the worker through the current guide, process the complete Delivery, and acknowledge it only after required release or retention succeeds. Follow the live guide's current recovery and FIFO rules rather than duplicating a fixed batch-drain protocol here. Never retry, replace, switch reviewer, release an active worker, or reinterpret an operational failure as a technical verdict.

## Output adjudication examples

These examples assume the declared worktree is elsewhere. File location does not replace finding adjudication or Orca lifecycle checks.

| Scenario | Required treatment |
| --- | --- |
| Claude writes tool output under `/tmp` or `/private/tmp`. | Allow it without an output-location warning or failure. |
| A reviewer redirects `git diff --cached` or `git show` into an external file and reads it in pieces. | Allow it as a review aid containing declared target bytes; the live index or resolved revisions remain authoritative. |
| Another requested reviewer writes a report under an external `$TMPDIR` or provider-owned directory. | Read the returned report and apply the same verdict rules as for Claude. |
| A reviewer writes scratch files in another external directory. | Allow it; the example paths are not an allowlist. |
| A reviewer creates a report or temporary file inside the current worktree, including an ignored subdirectory. | Treat it as a worktree-write violation. |
| An external path follows a symbolic link into the current worktree. | Treat the actual write as a worktree-write violation. |
| External files exist, the complete result has no actionable findings, and the Orca lifecycle is authoritative. | Permit `APPROVE` without an output-location warning or another review. |
| An external report needed for the result is missing, or the Orca lifecycle is incomplete. | Report the missing output or lifecycle evidence; do not return `APPROVE`. |
