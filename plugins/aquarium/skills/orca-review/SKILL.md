---
name: orca-review
description: "Run one supervised static review of a staged, HEAD, commit, or range target with a fresh requested reviewer through the local Orca runtime. Use when the user explicitly invokes $aquarium:orca-review or explicitly names a review target and reviewer, such as staged changes with Claude."
---

# Orca Review

Run the canonical Aquarium review contract with one fresh requested reviewer owned and supervised entirely by Orca. This path does not discover, launch, capture through, settle through, or otherwise use Dolgorae.

## Load the contracts

1. Read [review-intent-contract.md](../../references/review-intent-contract.md) completely.
2. Read [review-contract.md](../../references/review-contract.md) completely.
3. Read [finding-disposition.md](../../references/finding-disposition.md) completely.
4. Read [orca-supervision.md](../../references/orca-supervision.md) completely.
5. Require the separately installed `$orca-cli` skill and apply its live version-matched guides.

## Establish the target

Resolve one canonical Git root, one `staged`, `head`, `commit`, or `range` source scope, one requested reviewer, and one `change` or `completion` purpose. A `task`, `epic`, or special request supplies work-unit authority and intent but must resolve to one of those four scopes. Read the roadmap and linked authority first. Build the complete Review Brief, including actual criteria, checkpoint, source basis, candidate boundary, included and excluded state, verification provenance, and required result. Ask only when the authority does not identify one unambiguous scope and applicable revision.

`staged` means the current `HEAD`-to-index change in Orca's registered worktree. Confirm through read-only Git inspection that `git diff --cached` is nonempty, and report staged, unstaged, non-ignored untracked, and conflicted state without normalizing it. Do not inventory ignored runtime files or compare them before and after review. The reviewer reads the live staged target directly; do not replace it with a copied checkout, capture manifest, snapshot, or digest binding. External tool output remains a review aid under the Dispatch rules below.

For `head`, `commit`, and `range`, resolve the requested revisions with ordinary read-only Git commands and preserve the meanings in [review-contract.md](../../references/review-contract.md). Current index and worktree changes remain excluded from those committed targets. Conflicts stop the review.

`workspace` and `dirty` remain outside this workflow. Report the unsupported Orca scope and ask for an explicitly selected supported target or review route; Independent Review is disabled and is not a fallback. Never stage paths or reinterpret state merely to manufacture an Orca Review target.

An explicit request naming the target and reviewer authorizes transmission of that target only. "Use orca-review with Claude to review the staged changes" and "Review the staged target with Claude" both select `staged` and the native Orca `claude` reviewer.

If either the target or reviewer is missing, prefer structured ask/answer to obtain the missing selection; when unavailable, ask one focused question in ordinary conversation. Do not choose a default reviewer. Ask again only if the target, included paths, reviewer, or execution scope changes before Dispatch.

## Dispatch and supervise

Resolve the installed Orca command and ready local runtime exactly as [orca-supervision.md](../../references/orca-supervision.md) requires. Create one Run, one review Task, and one fresh native reviewer in Orca's registered `current` worktree with `worker-start --task <task-id> --worktree current --agent <requested-reviewer>`. Pass `--agent claude` when Claude is explicitly requested. Do not create another worktree, a copied checkout, a temporary repository, or a Dolgorae operation.

Place the complete Review Brief, declared target, purpose, authority paths, included and excluded state, and the following instructions in every Dispatch, regardless of target. Do not replace actual criteria with a Task or Epic identifier or a loose review focus:

- This is review only.
- Never create, edit, delete, move, format, or generate source files or other tracked or non-ignored files in the current registered worktree.
- All Orca reviewers may create or update review-related temporary files, native session state, tool output, and reports outside the current registered worktree or in Git-ignored runtime paths within it, such as ignored files under `.omc/`. `/tmp`, `/private/tmp`, `$TMPDIR`, and `~/.claude` are external examples, not an allowlist. This permission does not cover tracked files, non-ignored worktree files, or changes to Git state, including through symbolic links. Return the paths of retained report files used to deliver the result.
- External tool output and reports may contain bytes of the declared target, including redirected `git diff --cached` or `git show` output read in pieces. These files are review aids; they do not replace the live index or resolved Git revisions as target authority.
- Treat only the declared target as candidate evidence. Read its relevant files, callers, contracts, and tests plus approved authority sources at their declared basis when needed to judge the brief. For `head`, `commit`, and `range`, obtain candidate content and diffs from the resolved revisions through read-only Git commands; never substitute current index or worktree bytes or broaden into unrelated current-worktree inspection.
- Do not modify the Git index, refs, configuration, or commits.
- Do not run tests, builds, formatters, installers, authentication, or unrelated network operations.
- Report only actionable target findings with severity, scenario, violated authority, impact, and evidence. Use exact `path:line` when implementation exists; for a supported omission, cite the requirement, expected location, and inspected evidence without inventing a line.
- Treat a finding as actionable only when the target causes a concrete current defect, regression, security or privacy failure, violated acceptance criterion, or contradiction with an applicable authority, with a plausible affected path. Do not report style preferences, prose differences, speculative future inputs, test-for-test's-sake requests, or missing repository evidence for a claim that can be checked directly. A static review limitation or unexecuted runtime behavior is a verification gap, not a defect by itself. Exact text is contractual only when an authority explicitly defines that field as a machine-readable identity.
- For `completion`, return one `met`, `unmet`, `unverified`, or `not-applicable` assessment for every applicable criterion, with evidence provenance and remaining gaps. For `change`, state that whole-work-unit completion was not assessed.
- Return an advisory technical conclusion with the target findings and report operational deviations separately under [the shared policy](../../references/review-contract.md#orca-operational-deviations). Advisory `APPROVE` means no actionable target finding was found in the evidence you could assess; disclose any known compromise or uncertainty. Complete your required native lifecycle without waiting for or certifying the coordinator's later settlement. The coordinator owns the final technical verdict.

For `staged`, also require inspection of `git diff --cached`, the relevant staged files, and their callers. Apply equivalent target-specific read instructions to `head`, `commit`, and `range`. Require the reviewer to complete the injected Orca lifecycle exactly once and label execution-dependent claims `runtime unverified`. If required evidence cannot be gathered under the restrictions, require a bounded confirmation need instead of a mutation.

Supervise, settle, acknowledge, and recover only through the live Orca guides. Never retry automatically, switch reviewers, release an active worker, or reinterpret backend failure, incomplete settlement, or compromised or unproven review guarantees as `APPROVE`. Assess other observed deviations under [the shared policy](../../references/review-contract.md#orca-operational-deviations).

## Adjudicate and report

Independently verify every finding and criterion assessment against the exact target and authority without changing files or running checks. Preserve reported severity, classify validity as Valid, Invalid, or Needs confirmation, assign effective priority, and recommend a disposition under the shared contract. Apply the intent contract's assessment, conflict, silence, non-applicability, and completion-support rules directly. A static functionality review can establish support in code and documentation but cannot prove runtime behavior.

This standalone workflow is report-only. Do not remediate, run checks, stage, commit, or start another review. Return the purpose-specific shared result, reviewer identity, remediation continuation, Orca object and lifecycle status, and the paths of retained report files used to deliver the result. Keep technical findings, criterion assessment, verification gaps, operational deviations, and backend lifecycle state distinct. A clean technical result does not establish completion. Report `dolgorae_used: false`.

Permitted external review files and Git-ignored runtime files alone must not trigger a warning, an operational deviation, an approval request, additional checks, a withheld verdict, or another review. Wrong scope, missing required output, reviewer identity mismatch, or incomplete lifecycle prevents a clean verdict.

Apply [Orca operational deviations](../../references/review-contract.md#orca-operational-deviations) when review instructions were violated. Report adjudicated target findings first and keep the technical verdict, deviation report, and backend lifecycle status distinct. A technical `APPROVE` does not certify instruction compliance. Withhold the final technical verdict when a required guarantee is compromised or cannot be established from existing authorized evidence.

## Mulgae semantic conformance

When comparing a corresponding Mulgae review, require the same user-facing source-scope meaning and included and excluded disposition. In particular, `staged` means the current `HEAD`-to-index change read through `git diff --cached`. Backend capture and lifecycle details do not need to match. Never make Mulgae depend on Orca lifecycle internals or make Aquarium or Orca own Mulgae provider, extraction, adjudication, publication, archive, or settlement state.
