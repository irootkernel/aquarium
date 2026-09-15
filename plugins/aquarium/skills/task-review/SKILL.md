---
name: task-review
description: "Run and resolve Mulgae review for one complete roadmap task diff. Use when $aquarium:task-handler delegates review or when the user explicitly invokes $aquarium:task-review with exact task identity, current verification evidence, and a safely isolatable review target."
---

# Task Review

Read [mulgae-review-contract.md](../../references/mulgae-review-contract.md) for Aquarium review inputs, terminal evidence, recovery acceptance, and round counting. Read [review-intent-contract.md](../../references/review-intent-contract.md) for the shared Review Brief and criterion-level completion assessment.

Review only the complete implementation, tests, refinement, and review-state documentation for the task established by `$aquarium:task-handler`. Always read [evidence-residency.md](../../references/evidence-residency.md) and [finding-disposition.md](../../references/finding-disposition.md). Require the handler-provided positive review ordinal, current goal revision, and `remediation-eligible` or `confirmation-only` mode when delegated; a direct invocation is one isolated report-only round with ordinal one and grants no remediation or later-round budget.

One invocation consumes one round only after the full-target root or its verified composite reaches committed publication with complete coverage and a successful findings query, including a `request_changes` policy outcome or failing CI decision. Count once per original root under the shared Mulgae contract; reads, internal retry or extraction, exact recovery reruns, and composition do not consume another round.

Corrections returned to an owning phase change the diff and invalidate affected prior evidence, including implementation and verification evidence when behavior or tests change. The handler records native finding counts as descriptive source facts and derives separate phase-owned obligation totals from CI remediation, valid findings, and unmet completion criteria. It then admits finding confirmation, CI, completion, finding class, rework authority, and implementation, verification, or documentation ownership through separate serial decisions. Only passing CI, a `complete` completion state, a clean finding class, and no file change support task approval.

## Run and Resolve the Mulgae Review

1. Follow repository-specific Mulgae instructions and the shared contract's prerequisite routing. Keep the task in review when a required prerequisite is missing; setup changes belong to the routed setup skill.
2. Select one target containing the complete task diff and excluding unrelated work. Stop when safe isolation cannot be established.
3. Supply `$use-mulgae` with that target, roles, and one Review Brief naming the task, actual requirement set, checkpoint, target, verification provenance, goal revision, review ordinal, and review mode. Use the same brief for preflight and execution. Delegate native preflight, execution, waiting, and any authorized exact recovery under the shared contract.
   Before dispatch, establish the independent reason, remaining round, target, and original-root lineage. Resume the same invocation when it is pending. Do not dispatch when the only reason is eligible Low settlement or its accepted delta.
4. Consume the terminal root or verified composite result. Aggregate every accepted selected-role Markdown report into one conservative criterion-level completion assessment under the shared intent contract. Keep that assessment separate from execution completion, CI decision, extraction quality, and local finding dispositions. Pending execution and unavailable publication authority cannot support a review decision.
5. Treat every finding as an advisory hypothesis. Preserve its reported severity, verify it against the roadmap, current code, and tests, assign its effective priority, and select the applicable shared disposition.
6. Adjudicate every finding but do not change files. In delegated `remediation-eligible` mode, return valid findings through the owning phase with required checks and re-review status. A direct invocation reports findings and the exact `$aquarium:task-handler` continuation without mutation. In `confirmation-only` mode, return Medium-or-higher findings for bounded user authorization and return eligible Low handling to the approved owning envelope without granting another provider review.
7. Return unresolved operational gaps and every `unmet` or `unverified` completion criterion under the shared recovery, intent, and round-counting rules. Target changes require the handler's next full-target review; recovery of an older capture cannot prove corrected bytes.

## Bound the Evidence

Apply the shared contract's operational-completion and extraction-quality rules. Task approval separately requires passing CI, no unresolved Medium-or-higher or confirmation-needed finding, a completed verified disposition for every frozen eligible Low finding, and a completion assessment with zero `unmet` and zero `unverified` criteria. It does not require the immutable source Low count to become zero. Zero findings, native role coverage, provider success, or process exit cannot substitute for semantic completion.

Do not count a cancelled lane, operational failure, incomplete capture, unavailable findings query, or unverified finding as successful review evidence. Do not commit or publish in this phase.

Mulgae retains complete provider stdout and stderr without a product byte ceiling. Keep raw transcripts, accepted reports, extraction artifacts, and credential-profile paths in private Mulgae runtime state.

Verify every finding locally, but bound the orchestrator handoff to counts by reported severity, effective priority, validity, and disposition plus at most 20 highest-priority records containing only finding ID, reported severity, effective priority, validity, disposition, and affected repository-relative paths. Bound the separate completion assessment to criterion identity and source, assessment state, remaining gap, and reviewer or coordinator provenance.

When more remain, include the omitted count and authoritative run/findings identity or digest. Never include descriptions, quotes, credential-profile paths, or raw provider payloads.

Return the exact target, goal revision, review ordinal and mode, Review Brief identity, preflight summary, run and session IDs, command exit codes, operational-completion status, CI decision, the bounded completion-assessment summary and `unmet`/`unverified` counts, adjudicated findings, whether the review predates any corrected bytes, missing authority, and remaining operational gaps to the orchestrator. Keep full reports and private provider payloads in Mulgae runtime state.
