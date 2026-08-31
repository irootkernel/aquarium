---
name: orca-review
description: "Run one supervised static review of an exact Git target with a fresh Codex worker through the local Orca runtime. Use when the user explicitly invokes $aquarium:orca-review."
---

# Orca Review

Run the canonical Aquarium review contract with one fresh Codex worker owned and supervised entirely by Orca. This path does not discover, launch, capture through, settle through, or otherwise use Dolgorae.

## Load the contracts

1. Read [review-contract.md](../../references/review-contract.md) completely.
2. Read [orca-supervision.md](../../references/orca-supervision.md) completely.
3. Require the separately installed `$orca-cli` skill and apply its live version-matched guides.

## Establish the target

Resolve one canonical Git root, one exact `head`, `commit`, or `range` source scope, and one review focus. A `task`, `epic`, or special request supplies authority and focus but must resolve to one of those three scopes. Read the roadmap and linked authority first. Ask only when the authority does not identify one unambiguous scope and revision.

Resolve the installed Aquarium plugin root, then run the independent-review target inspector in read-only mode with the matching selector:

```text
python3 <aquarium-plugin-root>/skills/independent-review/scripts/inspect_review_target.py \
  --repository <exact-git-root> \
  <--head|--commit REVISION|--range RANGE>
```

Bind its complete JSON result, exact resolved Git identity, target digest, review focus, authority paths, and included and excluded state to the Orca Task. Inspect and report staged, unstaged, untracked, ignored, and conflicted state without mutation. Conflicts stop the review. Current index and worktree changes remain excluded from `head`, `commit`, and `range`.

`workspace`, `staged`, and `dirty` are not Orca Review source scopes because Orca has no immutable capture backend for mutable worktree or index bytes. Use `$aquarium:independent-review` when one of those scopes is required. Never stage exact paths merely to manufacture an Orca-review target.

An explicit invocation naming the exact target and Codex reviewer authorizes transmission of that target only. Otherwise prefer structured ask/answer to obtain a missing target; when unavailable, ask one focused question in ordinary conversation. Ask again only if the target, included paths, reviewer, or execution scope changes before Dispatch.

## Dispatch and supervise

Resolve the installed Orca command and ready local runtime exactly as [orca-supervision.md](../../references/orca-supervision.md) requires. Create one Run, one review Task, and one fresh native Codex worker in Orca's registered `current` worktree with `worker-start --worktree current --agent codex`. Do not create a provider terminal, select another AI provider, create another worktree, or call Dolgorae.

Immediately before worker start and Dispatch, run `scripts/inspect_repository_state.py --repository <exact-git-root> --snapshot` and bind its complete JSON result as the coordinator-owned source-mutation baseline. Re-run the target inspector and require the same target digest and resolved identity.

Inject one Dispatch containing the exact target-inspector result and instructions to inspect only the selected target through immutable Git object reads. Tell the worker explicitly that this is review, not implementation. It must remain read-only; never create, modify, delete, or move a file; never alter the Git index or a ref; and never substitute excluded index or current-worktree bytes for the selected target.

Require the worker to run no tests or builds and no generators, formatters, or linters; perform no authentication, installation, update, or unrelated network operation; report only verified actionable findings; label execution-dependent claims `runtime unverified`; and complete the injected Orca lifecycle exactly once. If required evidence cannot be gathered under those restrictions, require a bounded confirmation need instead of a mutation.

Supervise, settle, acknowledge, and recover only through the live Orca guides. Never retry automatically, switch reviewers, release an active worker, or reinterpret an operational failure as `APPROVE`.

After one accepted completion and before adjudication, feed the complete baseline through non-expanding stdin to `scripts/inspect_repository_state.py --repository <exact-git-root> --compare`. Report the returned modified-file status and changed dimensions. No drift proves only the helper's bounded Git-observable state. HEAD or ref drift, worker-attributed drift, or unexplained drift is operationally incomplete and prevents `APPROVE`; report it without reverting anything.

## Adjudicate and report

Independently verify every finding against the exact target and authority without changing files or running checks. Classify findings as Valid, Invalid, or Needs confirmation under the shared contract. A static functionality review can establish support in code and documentation but cannot prove runtime behavior.

Return the applicable shared result envelope plus the Codex reviewer identity and separate Orca Run, Task, Dispatch, worker, acknowledgement, Delivery, and lifecycle status. Wrong scope, target drift, modified files, missing output, reviewer-identity mismatch, or incomplete Orca lifecycle prevents a clean verdict. Report `dolgorae_used: false`. Do not implement remediation.

## Mulgae semantic conformance

When comparing a corresponding Mulgae review, require the same source-scope meaning, resolved Git identities, included and excluded disposition, and comparable whole-target digest. A mismatch fails closed. Never make Mulgae depend on Orca lifecycle internals or make Aquarium or Orca own Mulgae provider, extraction, adjudication, publication, archive, or settlement state.
