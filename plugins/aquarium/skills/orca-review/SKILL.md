---
name: orca-review
description: "Run one supervised static review of a staged, HEAD, commit, or range target with a fresh requested reviewer through the local Orca runtime. Use when the user explicitly invokes $aquarium:orca-review or explicitly names a review target and reviewer, such as staged changes with Claude."
---

# Orca Review

Run the canonical Aquarium review contract with one fresh requested reviewer owned and supervised entirely by Orca. This path does not discover, launch, capture through, settle through, or otherwise use Dolgorae.

## Load the contracts

1. Read [review-contract.md](../../references/review-contract.md) completely.
2. Read [finding-disposition.md](../../references/finding-disposition.md) completely.
3. Read [orca-supervision.md](../../references/orca-supervision.md) completely.
4. Require the separately installed `$orca-cli` skill and apply its live version-matched guides.

## Establish the target

Resolve one canonical Git root, one `staged`, `head`, `commit`, or `range` source scope, one requested reviewer, and one review focus. A `task`, `epic`, or special request supplies authority and focus but must resolve to one of those four scopes. Read the roadmap and linked authority first. Ask only when the authority does not identify one unambiguous scope and applicable revision.

`staged` means the current `HEAD`-to-index change in Orca's registered worktree. Confirm through read-only Git inspection that `git diff --cached` is nonempty, and report staged, unstaged, untracked, ignored, and conflicted state without normalizing it. The reviewer reads the live staged target directly; do not capture, copy, hash, snapshot, or bind it to an alternate source representation.

For `head`, `commit`, and `range`, resolve the requested revisions with ordinary read-only Git commands and preserve the meanings in [review-contract.md](../../references/review-contract.md). Current index and worktree changes remain excluded from those committed targets. Conflicts stop the review.

`workspace` and `dirty` remain outside this workflow. Use `$aquarium:independent-review` when one of those scopes is required. Never stage paths merely to manufacture an Orca Review target.

An explicit request naming the target and reviewer authorizes transmission of that target only. "Use orca-review with Claude to review the staged changes" and "Review the staged target with Claude" both select `staged` and the native Orca `claude` reviewer.

If either the target or reviewer is missing, prefer structured ask/answer to obtain the missing selection; when unavailable, ask one focused question in ordinary conversation. Do not choose a default reviewer. Ask again only if the target, included paths, reviewer, or execution scope changes before Dispatch.

## Dispatch and supervise

Resolve the installed Orca command and ready local runtime exactly as [orca-supervision.md](../../references/orca-supervision.md) requires. Create one Run, one review Task, and one fresh native reviewer in Orca's registered `current` worktree with `worker-start --task <task-id> --worktree current --agent <requested-reviewer>`. Pass `--agent claude` when Claude is explicitly requested. Do not create another worktree, a copied checkout, a temporary repository, or a Dolgorae operation.

Place the declared target, review focus, authority paths, included and excluded state, and the following instructions in every Dispatch, regardless of target:

- This is review only.
- Never create, edit, delete, move, format, or generate any file in the current registered worktree.
- When the reviewer is Claude, it may create or update only Claude-owned session, transcript, and tool-output state beneath `~/.claude`. If the report is too large for the Orca lifecycle message, Claude may also create one unique private review directory beneath `~/.claude`, write only report files inside it, and return every retained report path. Other reviewers may not create output files. Never write under `/tmp` or anywhere else.
- Read only the declared target. For `head`, `commit`, and `range`, obtain file content and diffs from the resolved revisions through read-only Git commands; never substitute current index or worktree bytes.
- Do not modify the Git index, refs, configuration, or commits.
- Do not run tests, builds, formatters, installers, authentication, or unrelated network operations.
- Report only actionable findings with severity and exact `path:line`.
- Return `APPROVE` when no actionable finding exists.

For `staged`, also require inspection of `git diff --cached`, the relevant staged files, and their callers. Apply equivalent target-specific read instructions to `head`, `commit`, and `range`. Require the reviewer to complete the injected Orca lifecycle exactly once and label execution-dependent claims `runtime unverified`. If required evidence cannot be gathered under the restrictions, require a bounded confirmation need instead of a mutation.

Supervise, settle, acknowledge, and recover only through the live Orca guides. Never retry automatically, switch reviewers, release an active worker, or reinterpret an operational failure as `APPROVE`.

## Adjudicate and report

Independently verify every finding against the exact target and authority without changing files or running checks. Preserve reported severity, classify validity as Valid, Invalid, or Needs confirmation, assign effective priority, and recommend a disposition under the shared contract. A static functionality review can establish support in code and documentation but cannot prove runtime behavior.

This standalone workflow is report-only. Do not remediate, run checks, stage, commit, or start another review. Return the shared result, reviewer identity, remediation continuation, Orca object and lifecycle status, and any Claude oversized-report path beneath `~/.claude`. Wrong scope, output, reviewer identity, or lifecycle prevents a clean verdict. Report `dolgorae_used: false`.

## Mulgae semantic conformance

When comparing a corresponding Mulgae review, require the same user-facing source-scope meaning and included and excluded disposition. In particular, `staged` means the current `HEAD`-to-index change read through `git diff --cached`. Backend capture and lifecycle details do not need to match. Never make Mulgae depend on Orca lifecycle internals or make Aquarium or Orca own Mulgae provider, extraction, adjudication, publication, archive, or settlement state.
