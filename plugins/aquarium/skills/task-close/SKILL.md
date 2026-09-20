---
name: task-close
description: "Confirm and close one reviewed roadmap task, including an explicitly selected terminal status and optional commit handoff. Use when $aquarium:task-handler delegates closeout or when the user explicitly invokes $aquarium:task-close with exact task identity, complete review evidence, and a final task diff."
---

# Task Close

Close only the reviewed task established by `$aquarium:task-handler`. When invoked directly, require the repository, roadmap path, task ID, final task diff, verification summary, documentation state, already authorized review route or waiver, and the selected route's complete evidence. Direct invocation grants no route-selection or waiver authority. Read [review-routing-contract.md](../../references/review-routing-contract.md), [evidence-residency.md](../../references/evidence-residency.md), and [finding-disposition.md](../../references/finding-disposition.md). This phase owns completion evidence and lifecycle selection; `$aquarium:task-commit` owns any actual commit.

## Assemble Existing Evidence

Determine whether repository authority makes an authorized commit, publication, merge, or other lifecycle evidence part of completion. Keep the task in review when required evidence is missing or its action is unauthorized.

Assemble evidence already produced by the agent and explicitly supplied by the user. Do not rerun user-confirmed tests or documentation checks solely to mark the task complete or prepare a commit. Repository-required hooks, generators, and synchronization commands still apply when they cannot be waived; disclose and report them separately.

Confirm that approved requirements, applicable verification, deslop, optimization, durable documentation, selected-route completion assessment, and finding dispositions are represented in the final task evidence. Require the route-neutral fields from the shared routing contract, including the consumed `assessment-ordinal` and `assessment-kind` when applicable, plus the exact reviewed and final target identities. Admit only a completed evidence combination for the selected route. An incomplete or failed delegated operation cannot support closeout.

For Mulgae, retain its exact root or verified composite, reviewer provenance, committed publication, complete coverage, successful findings query, and passing backend check. For Orca or native Codex, require authoritative native lifecycle or host-delegation evidence, reviewer provenance, and `backend-check-result=not-provided`. For a waiver, require explicit waiver authority, `assessment-provenance=coordinator-waiver`, the exact target, reason, assurance limitation, and `backend-check-result=not-provided`; record `review waived` and do not imply that a reviewer ran. Never require or invent another route's native evidence.

Successful closeout also requires current workflow verification, zero `unmet` and zero `unverified` completion criteria, no unresolved valid Medium-or-higher or confirmation-needed finding, and complete disposition of every admitted Low finding. A waiver removes only delegated review. It does not remove verification or completion assessment. Do not invent a terminal state when the roadmap lacks one.

When the review predates an accepted Low-only delta, require the complete
Low-settlement composition defined by the shared finding-disposition contract.
Verify that the final diff contains only that permitted
delta plus separately approved lifecycle and promoted-evidence changes. Do not
request another provider review solely because the target changed in this allowed
way. Reject any stale, failed, ambiguous, or additional change.

Keep final evidence in the orchestration report and native runtime. Do not add a completion log or validation record to the roadmap, and never treat an ignored runtime path or run ID as durable documentation.

## Select the Terminal Status

Before final approval, re-read the exact task entry and classify terminal states only from the roadmap vocabulary. Treat `Completed`, `Blocked`, and `Deferred` as terminal only when that roadmap defines them with completion meanings.

Preserve an existing terminal state. For a non-terminal task, show its exact current status and ask the user to select one available roadmap-defined terminal state, keep the current state, or cancel. When only one terminal state exists, ask for confirmation rather than choosing it. Never select a terminal state from evidence, prior intent, or the usual successful outcome.

If the user keeps the task non-terminal or cancels, do not commit and return the exact remaining gap. Otherwise show the exact proposed status-only edit before asking for final approval.

## Ask for Final Approval

Present or identify the exact final task diff, selected status edit, and whether a commit is proposed. Use structured `request_user_input` when available and ask all three questions together:

1. Tests: "Have you reviewed the current applicable test evidence, including who ran each check, and accepted it for this final implementation?" Offer `Evidence accepted`, `Not yet or failed`, and `Not applicable`.
2. Documentation: "Have you reviewed and accepted the documentation and roadmap changes in this final diff?" Offer `Docs approved`, `Needs revision`, and `Not applicable`.
3. Implementation: Ask whether the user fully approves this implementation with the displayed terminal status. Offer `Approve and commit` only when a commit is requested or required, offer `Approve and close without commit` unless repository authority requires a commit, and always offer `Request changes`; include `Keep in review` when only one approval option applies.

If structured ask/answer is unavailable, ask the same three concise questions one at a time. Count `Not applicable` as affirmative only when explicitly selected and consistent with repository requirements. Only `Approve and commit` and `Approve and close without commit` are affirmative implementation answers. Never infer approval from silence, an earlier commit request, or general satisfaction.

If any answer is negative, pending, ambiguous, or inconsistent with a required gate, preserve the current non-terminal state, do not commit, and return the feedback or exact gap. Treat `Keep in review` as a hold without requested changes and `Request changes` as a correction request naming the exact objection.

## Apply and Hand Off

Only after all three answers are affirmative, apply the exact approved status edit and run mandatory status-specific documentation synchronization or validation not covered by current evidence. The approved status-only edit does not invalidate approval; any other task-owned code, test, documentation, or roadmap change does, so show the updated final diff and ask again.

For `Approve and close without commit`, do not stage or commit anything. Verify the task is terminal while the complete task-owned diff remains uncommitted. This path is unavailable when repository authority requires a commit for completion.

For `Approve and commit`, invoke `$aquarium:task-commit` with a closeout handoff naming the repository, canonical roadmap path, exact task ID, approved terminal status edit, exact commit scope, the documented `entry`, `intentional no-note`, or `not-enrolled` release-note decision, verification evidence, `review-route`, `review-operation`, `review-evidence-reference`, `backend-check-result`, `assessment-provenance`, consumed `assessment-ordinal` and `assessment-kind` when applicable, waiver summary when applicable, exact reviewed and final target identities, the accepted Low-only composition fields or their explicit inapplicability, zero or more approved promoted manifest path and digest pairs plus their owning-workflow native validation results or their explicit absence, and the user's one-commit authorization. Include Mulgae-specific evidence only for the Mulgae route. For Orca, native Codex, or waiver, state explicitly that no hardening deferral applies.

Do not stage or commit independently. The handoff grants no amend, push, PR, release, or unrelated staging authority.

Return the three answers, final roadmap state, selected terminal status, release-note target and decision, mandatory commands and exit codes, task-commit result and commit identifier when created, publication state, and remaining gaps to the orchestrator.
