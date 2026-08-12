---
name: task-close
description: "Confirm, mark complete, and optionally commit one reviewed roadmap task. Use when $root-kernel:task-handler delegates closeout or when the user explicitly invokes $root-kernel:task-close with exact task identity, complete review evidence, and a final task diff."
---

# Task Close

Close only the reviewed task established by `$root-kernel:task-handler`. When invoked directly, require the repository, roadmap path, task ID, final task diff, verification summary, documentation state, and complete Mulgae evidence.

## Assemble Existing Evidence

Determine whether repository authority makes an authorized commit, publication, merge, or other lifecycle evidence part of completion. Keep the task in review when required evidence is missing or its action is unauthorized.

Assemble evidence already produced by the agent and explicitly supplied by the user. Do not rerun user-confirmed tests or documentation checks solely to mark the task complete or prepare a commit. Repository-required hooks, generators, and synchronization commands still apply when they cannot be waived; disclose and report them separately.

Confirm that approved requirements, applicable verification, deslop, optimization, durable documentation, Mulgae review, and finding dispositions are represented in the final task evidence. Do not invent a completed state when the roadmap lacks one.

## Ask for Final Approval

Re-read the roadmap vocabulary, present or identify the exact final task diff, and show the exact proposed status-only edit. Determine whether the repository requires a commit and whether the user requested one. Use structured `request_user_input` when available and ask all three questions together:

1. Tests: "Have you reviewed the current applicable test evidence, including who ran each check, and accepted it for this final implementation?" Offer `Evidence accepted`, `Not yet or failed`, and `Not applicable`.
2. Documentation: "Have you reviewed and accepted the documentation and roadmap changes in this final diff?" Offer `Docs approved`, `Needs revision`, and `Not applicable`.
3. Implementation: When a commit is requested or required, ask "Do you fully approve this implementation and want it marked complete and committed?" and offer `Approve and commit`, `Request changes`, and `Do not commit`. Otherwise ask "Do you fully approve this implementation and want it marked complete without a commit?" and offer `Approve and close without commit`, `Request changes`, and `Keep in review`.

If structured ask/answer is unavailable, ask the same three concise questions one at a time. Count `Not applicable` as affirmative only when explicitly selected and consistent with repository requirements. Never infer approval from silence, an earlier commit request, or general satisfaction.

If any answer is negative, pending, ambiguous, or inconsistent with a required gate, keep the review or other non-terminal state, do not commit, and return the feedback or exact gap.

## Transition and Optional Commit

Only after all three answers are affirmative:

1. Re-read the exact task entry and allowed lifecycle vocabulary.
2. Classify terminal states from that roadmap. Treat `Completed`, `Blocked`, and `Deferred` as terminal only when defined with those meanings.
3. Preserve an existing terminal state. For a non-terminal state, select the existing successful terminal state, normally `Completed`, based on the recorded approvals and assembled evidence.
4. Never select `Blocked` or `Deferred` merely to enable a commit, and never convert either to `Completed` without fresh evidence that work resumed and received approval.
5. Run only mandatory status-specific documentation synchronization and validation not covered by current evidence.
6. If `Approve and commit` was selected, apply the exact approved status edit and stage the complete task-owned final diff while preserving unrelated staged content. Stop if exact task-owned paths or hunks cannot be isolated safely, then re-read the staged roadmap entry and complete staged task diff immediately before committing.
7. If `Approve and close without commit` was selected, apply only the exact approved status edit, do not stage or commit anything, and verify the task is terminal while the task-owned final diff remains uncommitted. This path is unavailable when repository authority requires a commit for completion.

The exact proposed status-only edit is part of approval and does not invalidate it. Any other task-owned code, test, documentation, or roadmap change after the answers invalidates all three confirmations; show the updated final diff and ask again.

The `Approve and commit` answer authorizes one commit of the displayed task-owned diff. The `Approve and close without commit` answer authorizes only the displayed status edit and no Git staging or commit. Neither answer authorizes amend, push, PR changes, or unrelated staging. Use repository commit conventions and safe lease checks for any separately authorized publication action.

When repository guidance selects Lore for a non-trivial commit, load `$lore-commits`. Repository title prefixes and task-ID rules override Lore's summary line. Lore never grants Git authority. If Lore is required but unavailable, stop and return an exact `$root-kernel:dev-setup` continuation request.

Return the three answers, final roadmap state, mandatory commands and exit codes, staged paths, commit identifier when created, publication state, and remaining gaps to the orchestrator.
