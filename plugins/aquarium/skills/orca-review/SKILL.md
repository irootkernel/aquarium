---
name: orca-review
description: "Run the canonical independent-review target contract through a user-selected Claude Fable, Kimi, Agy, or Cursor Agent in Orca. Use when the user explicitly invokes $aquarium:orca-review and asks for a non-Codex independent review."
---

# Orca Review

Extend `$aquarium:independent-review` with a removable non-Codex provider layer. Immutable target selection, static-review limits, adjudication, and the result envelope remain identical to the canonical independent-review contract, while Orca retains complete provider lifecycle ownership.

## Load the Contracts

1. Read [review-contract.md](../../references/review-contract.md) completely.
2. Read [dolgorae-review-contract.md](../../references/dolgorae-review-contract.md) completely.
3. Read [orca-supervision.md](../../references/orca-supervision.md) completely.
4. Read [provider-contracts.md](references/provider-contracts.md) completely, then apply only the selected provider section.
5. Resolve the installed `dev-aquarium` manager from this plugin generation.

## Establish the Target

Classify and resolve one `workspace`, `staged`, `dirty`, `head`, `commit`, or `range` source scope exactly as the shared review contract specifies. A `task`, `epic`, or special request supplies authority and focus only. Inspect current state without mutation and never stage or normalize content.

Create the Orca Run and review Task first and record their authoritative identities without Dispatching source. Admit and revalidate the exact enrolled Dolgorae generation, then create one protected owner-credential carrier outside the repository.

Through the guarded manager, call checked `review-target.capture` with backend `orca` and the immutable Run and Task lifecycle identity. Bind its complete capture result, immutable root, exact authority paths, included and excluded state, target and manifest digests, and review focus to the Task.

If capture fails, close the still-empty Orca lifecycle through its native authority. Delete an unused carrier after a failed capture; preserve an admitted carrier until authoritative settlement or recovery.

The provider still runs in Orca's current registered checkout, not a private repository snapshot, but the Task authorizes review only from the immutable capture root. Disclose that the same operating-system user can technically read excluded source-worktree bytes. Never substitute the current checkout for captured review input.

## Discover and Select the Provider

Probe only `claude`, `kimi`, `agy`, and `cursor-agent` with `command -v`. Resolve each available command to one absolute path and canonical regular-file target outside the repository, record its symlink chain, file type, SHA-256 digest, and local `--version` output, and revalidate that identity immediately before terminal creation and Dispatch. Do not authenticate, list remote models or agents, inspect credentials, update software, or contact a provider during discovery.

Offer only choices whose local probe succeeds:

- Claude with a Fable lead; Opus and Sonnet subagents are optional when useful;
- Kimi with K3;
- Agy with installed defaults, or the exact agent, model, and effort the user supplies;
- Cursor Agent with Grok 4.6.

An explicit request that already names the exact target and one available reviewer is transmission consent for that scope. Otherwise prefer structured ask/answer to obtain the missing target or reviewer choice; when that surface is unavailable, ask one focused question in ordinary conversation. Do not require separate preparation and transmission approvals. Ask again only if the target, included paths, reviewer, or execution scope changes before Dispatch.

The selection record must disclose the exact provider command, requested lead identity or Agy override, observed version, target digest, included and excluded state, current-worktree execution, same-user visibility boundary, static-only restrictions, and source categories sent in the Task. Consent authorizes only this review; it grants no authentication change, installation, source edit, test, build, generator, formatter, linter, staging beyond separately approved exact paths, commit, push, publication, retry, or provider switch.

## Dispatch and Supervise

Resolve the installed Orca command and live guides exactly as [orca-supervision.md](../../references/orca-supervision.md) requires. Reuse the exact Run and Task created before capture; do not allocate another lifecycle object. Then create one fresh provider terminal in the current worktree only through `scripts/create_provider_terminal.py` with the selected logical argv from [provider-contracts.md](references/provider-contracts.md).

Immediately before terminal creation, run `scripts/inspect_repository_state.py --repository <exact-git-root> --snapshot` and bind its complete JSON result as the coordinator-owned source-mutation baseline. Then feed the terminal-helper request through non-expanding stdin with that same exact Git worktree root and verify its returned Orca terminal result and argv digest before continuing.

The helper copies the verified Orca executable into a private user-immutable location before launch. Its injected provider guard independently copies, rehashes, seals, executes, and removes the verified provider bytes, so later canonical-path replacement cannot change either executed object.

The helper-generated command must revalidate provider identity at provider-process start. Verify the requested lead identity when the provider exposes it. A helper failure or missing or mismatched exposed identity stops before source-bearing Dispatch.

Inject one Dispatch containing the canonical Task and immutable capture root. Tell the lead explicitly that this is review, not implementation, and that it must not enter or request a provider plan mode. Regardless of the tools available in normal mode, require the lead to remain read-only; never create, modify, delete, or move a file; and never alter the Git index or a ref.

Require the lead to run no tests or builds and no generators, formatters, or linters; perform no authentication, installation, or update; inspect exact target blobs instead of excluded working-tree copies; report only verified actionable findings; label execution-dependent claims `runtime unverified`; and complete the injected lifecycle exactly once. If required evidence cannot be gathered under those restrictions, require a bounded confirmation need instead of a mutation.

Provider-native subagents are optional evidence gatherers except where the selected provider contract says otherwise. The lead owns decomposition, evidence review, requirement-goal assessment, deduplication, decisions, and final synthesis. Record which subagents and effective models were actually used when the provider exposes that evidence; absence of optional subagents is not a review failure.

Supervise, settle, acknowledge, and recover through the live Orca guides. The exact provider-native auto-approval or permission-bypass argument must prevent ordinary permission prompts. If a permission prompt still appears, treat it as an operational failure and stop without asking the coordinator or user to approve it, sending input, switching modes, or weakening the review restrictions. Never retry automatically, switch providers, release an active worker, or reinterpret an operational failure as `APPROVE`.

After accepted completion and before adjudication, feed the complete baseline through non-expanding stdin to `scripts/inspect_repository_state.py --repository <exact-git-root> --compare`. Report the returned modified-file status and changed dimensions. No drift proves only the helper's bounded Git-observable state. HEAD or ref drift, provider-attributed drift, or unexplained drift is operationally incomplete and prevents `APPROVE`; report it without reverting anything.

After accepted Orca completion, construct only the checked terminal receipt from authoritative Run, Task, Dispatch, terminal, acknowledgement, state revision, and evidence digest. Revalidate the exact Dolgorae candidate, then call checked `review-target.settle` with the protected owner credential and expected capture revision. Active, unknown, stale, foreign-owner, lifecycle-mismatched, missing-evidence, or concurrent-losing settlement preserves capture and recovery evidence. Exact accepted replay is idempotent.

## Adjudicate and Report

Independently verify every finding against the exact target and authority without changing files or running checks. Classify findings as Valid, Invalid, or Needs confirmation under the shared contract. A static functionality review can establish support in code and documentation but cannot prove runtime behavior.

Return the complete shared result envelope plus the selected provider identity, actual optional-subagent evidence, capture and settlement evidence, and separate Orca Run, Task, Dispatch, terminal, and lifecycle status. Wrong scope, modified files, missing output, provider-identity mismatch, incomplete lifecycle, or incomplete settlement prevents a clean verdict. Do not implement remediation.

## Mulgae semantic conformance

When comparing a corresponding Mulgae review, require the same source-scope meaning, resolved Git identities, included and excluded disposition, and comparable whole-target digest. A mismatch fails closed. Never make Mulgae depend on Dolgorae capture internals or make Aquarium, Dolgorae, or Orca own Mulgae provider, extraction, adjudication, publication, archive, or settlement state.
