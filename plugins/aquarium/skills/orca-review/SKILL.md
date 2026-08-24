---
name: orca-review
description: "Run the canonical independent-review target contract through a user-selected Claude Fable, Kimi, Agy, or Cursor Agent in Orca. Use when the user explicitly invokes $aquarium:orca-review and asks for a non-Codex independent review."
---

# Orca Review

Extend `$aquarium:independent-review` with a removable non-Codex provider layer. Target selection, dirty-state handling, static-review limits, adjudication, and the result envelope remain identical to the canonical independent-review contract.

## Load the Contracts

1. Read [review-contract.md](../../references/review-contract.md) completely.
2. Read [orca-supervision.md](../../references/orca-supervision.md) completely.
3. Read [provider-contracts.md](references/provider-contracts.md) completely, then apply only the selected provider section.
4. Resolve the `independent-review` skill directory and use its `scripts/inspect_review_target.py`. Do not maintain another target inspector here.

## Establish the Target

Classify and resolve one `staged`, `commit`, `range`, `task`, `epic`, or `special request` target exactly as the shared review contract specifies. A dirty working tree is never a target. For a staged target, ask whether to stage exact displayed paths, exclude the dirty remainder, or cancel. For commit, range, and confirmed `HEAD` targets, exclude dirty content automatically.

Use the current checkout, not a private snapshot. When excluded dirty content exists, disclose that it remains outside the authorized scope but can technically be read by a reviewer process running as the same operating-system user. Bind the target inspector's complete result, exact authority paths, included and excluded state, and review focus to the Task.

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

Resolve the installed Orca command and live guides exactly as [orca-supervision.md](../../references/orca-supervision.md) requires. Create one Run and Task, then create one fresh provider terminal in the current worktree only through `scripts/create_provider_terminal.py` with the selected logical argv from [provider-contracts.md](references/provider-contracts.md).

Feed the helper request through non-expanding stdin with the exact Git worktree root and verify its returned Orca terminal result and argv digest before continuing. The helper-generated command must revalidate provider identity at provider-process start. Verify the requested lead identity when the provider exposes it. A helper failure or missing or mismatched exposed identity stops before source-bearing Dispatch.

Inject one Dispatch containing the canonical Task. Require the lead to remain read-only, run no tests or builds, inspect exact target blobs instead of excluded working-tree copies, report only verified actionable findings, label execution-dependent claims `runtime unverified`, modify no files, and complete the injected lifecycle exactly once.

Provider-native subagents are optional evidence gatherers except where the selected provider contract says otherwise. The lead owns decomposition, evidence review, requirement-goal assessment, deduplication, decisions, and final synthesis. Record which subagents and effective models were actually used when the provider exposes that evidence; absence of optional subagents is not a review failure.

Supervise, settle, acknowledge, and recover through the live Orca guides. Never retry automatically, switch providers, weaken permissions, release an active worker, or reinterpret an operational failure as `APPROVE`.

## Adjudicate and Report

Independently verify every finding against the exact target and authority without changing files or running checks. Classify findings as Valid, Invalid, or Needs confirmation under the shared contract. A static functionality review can establish support in code and documentation but cannot prove runtime behavior.

Return the complete shared result envelope plus the selected provider identity, actual optional-subagent evidence, and separate Orca Run, Task, Dispatch, terminal, and lifecycle status. Wrong scope, modified files, missing output, provider-identity mismatch, or incomplete lifecycle prevents a clean verdict. Do not implement remediation.
