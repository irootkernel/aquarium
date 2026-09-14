---
name: mulgae-review
description: "Run one report-only standalone Mulgae review of an exact supported change target or named Task or Epic completion candidate. Use when the user explicitly asks Aquarium to use Mulgae outside an active Task or Epic handler."
---

# Mulgae Review

Run one standalone review through Mulgae and return an advisory report. This skill supplies review intent and consumes the result; `$use-mulgae` owns capture, provider execution, waiting, recovery, publication, retention, and every other native lifecycle action.

## Load the contracts

1. Read [review-intent-contract.md](../../references/review-intent-contract.md) completely.
2. Read [mulgae-review-contract.md](../../references/mulgae-review-contract.md) completely.
3. Read [finding-disposition.md](../../references/finding-disposition.md) completely.
4. Read [evidence-residency.md](../../references/evidence-residency.md) completely.
5. Require the separately installed `$use-mulgae` skill and follow its release-matched instructions.

## Resolve purpose and target

Preserve an already supplied purpose, target, roles, work-unit identity, and revision. Do not ask for them again.

- Select `change` for a request to judge the intended effect of a selected change. Never turn that result into Task or Epic completion approval.
- Select `completion` when the request asks whether a named Task, Epic, or bounded requirement set is fully satisfied. Resolve and read its canonical authority and applicable checkpoint before dispatch.
- Reject an unidentified or materially underspecified completion basis as unqualified. Return the supported defect review and the missing authority; do not invent criteria, assign the latest active Epic, or silently convert the request to `change`.

Resolve exactly one target supported by the installed Mulgae release: `stage`, `workspace`, `dirty`, `diff`, or `patch`. Keep its native meaning. For `stage`, inspect Git state read-only and require a nonempty HEAD-to-index candidate; unstaged or untracked bytes remain excluded. Resolve every revision used by `diff` before dispatch and record the immutable endpoints. A completion request with no new diff must use an existing immutable committed target, such as an exact resolved commit range; never stage files or manufacture a change. If `patch` cannot expose enough context for completion, report the limitation and obtain a supported target instead of broadening it.

Read relevant unchanged implementation and authority as context only when the selected capture makes them available. Do not transmit another repository, private conversation, credential, or raw provider artifact without separate authority. Stop on conflicts, an ambiguous target, or a target that cannot be isolated safely.

See [examples.md](references/examples.md) for the three required standalone request shapes.

## Build and dispatch the review

Construct one concise Review Brief under the shared intent contract. Include the purpose and identity, problem and outcome, actual criteria with sources, constraints and non-goals, authority basis, exact candidate and excluded state, completion checkpoint, existing verification and its provenance, unavailable checks, selected roles, and any native lineage. For a generic change with incomplete intent, distinguish known facts from inferred intent and state the limitation.

A standalone invocation has no embedded goal revision, review ordinal, review mode, or owning-workflow advancement. Include such values only when the request supplies them as relevant context, and never manufacture them to satisfy an embedded-workflow rule.

Assign every applicable criterion to at least one responsibility in the already selected role arrangement. Do not add roles or provider calls merely to fill a gap. If the authorized arrangement leaves a criterion uncovered, keep it `unverified` in the result.

Give `$use-mulgae` the exact target, roles, and identical Review Brief for preflight and execution. Follow its asynchronous start-and-await flow, retention advisory, and exact recovery rules. Do not duplicate or override provider selection, budgets, capture, retries, cancellation, extraction, composition, or publication. Do not replace a pending or uncertain invocation, and do not start another root merely to obtain a cleaner result.

Operational completion requires one authoritative committed root or verified composite with complete selected-role coverage and a successful findings query. A transport success, provider success, passing CI, `reports_only`, or zero findings cannot substitute for those facts or for the criterion assessment.

## Aggregate and adjudicate

Read every accepted selected-role Markdown report admitted for the exact candidate. Preserve report identity and verified composite lineage. Aggregate criterion evidence conservatively under the shared contract:

Apply the intent contract's assessment-state, partial-coverage, conflict-resolution, silence, non-applicability, duplicate-gap, and coordinator-evidence rules directly. Do not restate or weaken them locally. In particular, evidence that establishes a real gap makes the criterion `unmet`; an otherwise unresolved conflict remains `unverified`.

Adjudicate every finding as a hypothesis using read-only evidence. Preserve reported severity, validity, effective priority, owner, affected paths, disposition, and missing authority. Do not fabricate a source line for missing implementation. Do not modify native findings or treat an aggregate assessment as a native Mulgae status.

## Return the standalone report

Report these sections distinctly:

1. Purpose, work unit, checkpoint, exact target, immutable identities, and included or excluded state.
2. Native lifecycle facts: invocation, session, root or composite run, accepted reports, coverage, publication, CI, extraction quality, findings-query status, and recovery lineage.
3. Adjudicated findings and counts by reported severity, effective priority, validity, and disposition.
4. For `completion`, every criterion with source, assigned responsibility, `met`, `unmet`, `unverified`, or `not-applicable` state, evidence provenance, remaining gap, and aggregate counts. For `change`, state explicitly that whole-work-unit completion was not assessed.
5. Verification evidence and limitations, separating observed results from author-reported claims.
6. The advisory technical result, completion support when requested, backend lifecycle status, and the exact bounded continuation for any remediation or missing authority.

Apply the intent contract's completion-support rule directly. When it does not support completion, report the exact unmet or unverified basis without starting implementation.

This workflow is report-only. Do not run tests or formatters; edit, create, move, or delete repository files; remediate findings; alter the index; commit; change roadmap lifecycle; start a Task or Epic handler; invoke Epic validation; install tools; change providers; publish; or grant another review round. Reviewer-owned private runtime artifacts remain governed by Mulgae and the evidence-residency contract.
