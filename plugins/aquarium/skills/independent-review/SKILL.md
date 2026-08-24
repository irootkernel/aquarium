---
name: independent-review
description: "Run one supervised static review with a fresh Codex against staged changes, a commit or range, one task or epic, or a roadmap-independent investigation. Use when the user explicitly invokes $aquarium:independent-review and asks for an independent verdict without remediation."
---

# Independent Review

Run the canonical Aquarium review contract with one fresh Codex reviewer. The current execution backend is Orca, but target selection and review semantics are backend-independent. Use `$aquarium:orca-review` only when the user wants a supported non-Codex provider.

## Load the Contracts

1. Read [review-contract.md](../../references/review-contract.md) completely. It owns target selection, dirty-state handling, consent, static-review limits, and the result envelope.
2. Read [orca-supervision.md](../../references/orca-supervision.md) completely. It owns the current backend lifecycle.
3. Resolve this skill directory and use `scripts/inspect_review_target.py` from it. Do not copy or approximate the inspector contract.

## Establish the Request

1. Resolve one current Git root and classify the request as `staged`, `commit`, `range`, `task`, `epic`, or `special request`.
2. For a task or epic, inspect its roadmap and linked authority first. Select a Git target automatically only when the authority identifies one unambiguous staged candidate, commit, or range; otherwise ask the user to choose among the concrete candidates.
3. For a special request, establish the exact question, then always ask the user to confirm staged, `HEAD`, one commit, or one explicit two-dot or three-dot range.
4. Inspect HEAD, branch, upstream, staged, unstaged, untracked, ignored, and conflicted state. Resolve any staged-target dirty decision exactly as the shared contract requires. Never review dirty working-tree content as a target.
5. Run the target inspector after all required choices or staging operations. Bind its complete JSON result and the resolved authority paths to the Task.

Explicit invocation with an exact target and Codex reviewer authorizes the source transmission needed for this review. Do not ask for duplicate approval unless the target, included paths, reviewer, or execution scope changes. The workflow authorizes no source edits, tests, builds, generators, formatters, linters, provider reviews, commits, pushes, publication, or remediation. The only permitted mutation is exact-path staging that the user separately approved under the dirty decision.

## Dispatch One Fresh Codex

Resolve the installed Orca command and live guides exactly as the Orca supervision contract requires. Create one Run and one review Task, then start one fresh reviewer with the live guide's supervised `worker-start --worktree current --agent codex` path. Do not reuse an existing worker or create another worktree.

The Task must include:

- the absolute repository root, target-inspector result, review focus, and authority paths;
- exact included and excluded state, including the same-user visibility disclosure when dirty content is excluded;
- instructions to use index blobs for staged targets and resolved commit blobs for commit, range, or `HEAD` targets rather than later working-tree copies;
- the static-only restrictions and `runtime unverified` requirement from the shared contract;
- the required finding fields and exact `APPROVE` condition;
- the user's test-status statement only as context, never as independently verified evidence.

Do not seed the reviewer with suspected findings or intended fixes. Require it to modify no files, leave its complete review in the final response, and send `worker_done` exactly once through the injected Orca lifecycle.

## Supervise and Adjudicate

Follow the live Orca guides and [orca-supervision.md](../../references/orca-supervision.md) for waiting, questions, completion, settlement, acknowledgement, and recovery. Keep technical review status separate from backend lifecycle status.

After accepted completion, independently check every finding against the exact target, authority, production callers, persistence and concurrency boundaries, and existing tests without running checks or changing files. Classify findings as Valid, Invalid, or Needs confirmation under the shared result contract. A functionality claim that still requires execution remains `runtime unverified`.

Return the complete shared result envelope, identify Codex as the reviewer and Orca as the current backend, and report separate Run, Task, Dispatch, worker, and lifecycle status. Wrong scope, modified files, missing output, or an incomplete lifecycle prevents a clean verdict.
