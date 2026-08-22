---
name: orca-review
description: "Run one supervised, read-only review of an exact repository snapshot through a user-selected installed AI CLI in Orca, using a bounded multi-agent hierarchy and locally adjudicating the result. Use when the user explicitly invokes $aquarium:orca-review and asks to review staged changes, working-tree changes, a commit or range, or one named task or epic."
---

# Orca Review

Review one exact repository snapshot through one user-selected AI CLI while preserving the checkout, supervising the worker through Orca, and independently verifying the returned findings. This is a standalone utility; it does not replace `$aquarium:independent-review` or the Mulgae phase owned by `$aquarium:task-review`.

Explicit invocation authorizes read-only local discovery, starting the installed Orca runtime when needed, and the structured provider-selection question. Selecting an option authorizes transmission of only the disclosed review snapshot and authority context to that provider. It does not authorize edits, tests, builds, generators, formatters, staging, commits, pushes, publication, authentication changes, software installation, or another provider request.

## Fail Closed on Orca

1. Require the separately installed `$orca-cli` skill to be available in the active skill catalog. If its availability cannot be established, stop; do not approximate its contract from this skill.
2. Resolve the Orca executable exactly as `$orca-cli` requires and reuse it for the complete invocation. If the selected executable is missing or fails, report the exact error and stop; do not try another executable.
3. Load the version-matched guides with the selected executable's `skills get orca-cli` and `skills get orchestration` commands before using Orca. Follow those live guides rather than cached command syntax, including the examples in this skill and its reference. Stop when either guide cannot be retrieved.
4. Confirm `status --json`. If the CLI exists but the app is stopped, attempt `open --json` once and confirm status again.
5. Require a ready runtime and the current orchestration contract. Stop when the selected executable fails, either version-matched guide cannot be retrieved, the runtime cannot start, orchestration is unavailable, or Run, Task, Dispatch, terminal, or lifecycle provenance cannot be verified.

Never substitute a generic subagent, raw AI CLI process, ad hoc PTY, another Orca executable, Mulgae, or the coordinator's own review. An operational failure is not an `APPROVE` result.

## Establish the Exact Review Target

1. Resolve one Git root, applicable instruction files, and the user-named target. Supported targets are staged changes, explicitly included staged, unstaged, and named untracked working-tree changes, one commit or commit range, or one named task or epic paired with one of those exact Git targets.
2. For a task or epic, resolve the authoritative roadmap, requirements, specifications, decisions, and contracts before dispatch. Ask one focused question when multiple authorities or Git targets remain plausible after repository discovery.
3. Inspect HEAD, branch, upstream, staged, unstaged, untracked, and conflicted state. Never include unrelated untracked content merely because it exists.
4. Record the path and SHA-256 digest of every applicable instruction file and named requirement authority. Then record the exact Git target and its SHA-256 digest without `git write-tree` or another command that writes Git objects:
   - staged target: HEAD commit plus the digest of `git diff --cached --binary`;
   - working-tree target: HEAD plus separate digests for `git diff --cached --binary`, `git diff --binary`, and each explicitly included untracked file;
   - commit or range: resolved endpoint commits plus the digest of its binary diff;
   - task or epic: the selected Git target above plus any additional authoritative roadmap, requirement, specification, decision, and contract documents.
5. Stop on an empty target, unresolved conflict, unsafe scope ambiguity, unreadable authority, or a target that cannot exclude unrelated private content.

For a staged target, require the reviewer to inspect index blobs and `git diff --cached`, not working-tree copies that may contain later unstaged changes. For a commit or range target, require the reviewer to inspect blobs and diffs at the resolved endpoint commits, not working-tree copies. Treat unstaged and untracked state as excluded context unless the disclosed target explicitly includes it.

## Discover and Select the AI

Probe only these executable names with `command -v` followed by their local version command: `claude --version`, `codex --version`, `cursor-agent --version`, and `kimi --version`. A command is available only when both probes succeed. Do not authenticate, list remote models, contact a provider, update a CLI, or inspect credentials during discovery.

Build the selection menu from successful probes only:

- `claude` exposes `claude:fable with opus/sonnet` and `claude:opus`.
- `codex` exposes `codex:gpt-5.6-sol`.
- `cursor-agent` exposes `cursor:grok-4.6`; omit every Cursor choice when `cursor-agent` is unavailable.
- `kimi` exposes `kimi:k3`.

Fail closed when no supported CLI is available. Do not infer model availability from installation; the selected launch verifies it.

Use the host's structured ask/answer tool, normally `request_user_input`, whenever available. Present no more than three choices in one call; when more are available, paginate with one navigation choice such as `More installed AIs` and then show only the remaining exact tool:model labels. Keep navigation choices separate from final provider consent. Even when one choice is available, require the user to select it.

Before presenting a final choice, build and display a complete transmission manifest. It must list every repository, target, supporting-source, instruction, and authority file whose bytes the reviewer may receive, with its source identity and SHA-256 digest, plus the explicitly excluded state. Sort the records by source identity as newline-terminated `<sha256>  <source-identity>` lines and hash those exact UTF-8 bytes as the context-manifest digest.

Each final choice must identify the exact tool:model, review target and digest, context-manifest digest, and that selecting it authorizes transmission of only that displayed scope to the provider. If structured ask/answer is unavailable, report that exact prerequisite failure and stop without selecting a provider or transmitting source.

Never auto-select, infer consent from silence, or treat approval for another provider, snapshot, or context manifest as consent.

## Dispatch the Reviewer

Immediately after selection and before reading provider instructions, creating Orca state, or transmitting source, recompute the recorded target and every transmission-manifest file digest plus the context-manifest digest. If any digest or recorded target identity differs, do not transmit; establish the changed target again and require a new final provider selection for both disclosed digests.

After that check succeeds, materialize only those verified bytes into one private standalone Git snapshot under a fresh `/tmp` directory. Give it no remote, credential material, object alternates, or link to the source repository's Git metadata. Preserve the disclosed target form and necessary baseline evidence, store the transmission manifest inside it, make the complete snapshot read-only, and recompute every snapshot file digest. Stop unless that snapshot exactly reproduces the consented target and context-manifest digests.

After the immutable snapshot verifies, read [provider-contracts.md](references/provider-contracts.md). Create or bind one Run, create one review Task, start one fresh selected lead with the snapshot as its current worktree, and inject one supervised Dispatch through the live orchestration contract. Never expose the original checkout to a participant, register a linked Git worktree, or reuse an existing AI terminal.

The Task specification must include the original absolute Git root as report identity only, immutable snapshot root, exact target and digest, complete context-manifest digest, named requirement authority, included and excluded state, selected tool:model, the selected provider's required subagent topology and effective-model verification duties copied from the reference, participant-wide read-only restrictions, and required report schema.

Require every participant to read only the immutable snapshot and bind authoritative worker scope evidence to both consented digests. Do not include the coordinator's suspected findings or intended fixes.

Require the lead to:

- ensure every participant reads applicable instructions, authority, target code, callers, persistence and concurrency boundaries, and relevant existing tests;
- keep every participant read-only and run no tests, builds, generators, formatters, linters, provider reviews, installers, authentication commands, or unrelated network operations;
- apply the provider-specific hierarchy included in the Task, verify every effective model, and inspect subagent evidence before adopting it;
- report only verified actionable findings, omitting praise, style preferences, speculation, and duplicate findings;
- give every finding a severity, exact `path:line`, triggering scenario, violated authority, impact, and smallest remediation;
- return `APPROVE` as the verdict when no actionable finding remains;
- include a bounded topology record with each participant role, effective model, and disposition, report no modified files, and send `worker_done` exactly once through the injected Orca lifecycle. Subagents return evidence only to the lead and never report directly to the Aquarium coordinator or send lifecycle completion.

## Supervise and Settle

Use event-driven rolling waits for `worker_done`, `escalation`, and `question`, providing user updates at least once per minute. Before dispatch, disclose and record one cumulative liveness budget, using 30 minutes unless the user explicitly selected another duration. A timeout or empty delivery inside that budget is a liveness checkpoint, not a failure. Answer worker questions only from established repository facts; ask the user when an answer requires product intent or wider authority.

When the cumulative budget expires without an accepted terminal delivery, inspect the authoritative worker and terminal state once through the live guide, stop waiting, leave any active worker intact, and report the review as operationally incomplete with the exact Run, Task, Dispatch, terminal, and lifecycle status. Further waiting or cancellation requires an explicit user request; never release, retry, or cancel the active worker automatically.

For an accepted `worker_done`, retrieve the complete authoritative worker evidence through `worker-read`, process every delivered message and transcript record, and verify the reported topology. If authoritative transcript or scope evidence is unavailable, it prevents a clean verdict. Release a settled succeeded or failed worker unless the user explicitly requested retention, then acknowledge the delivery. Do not release an active worker after a timeout, question, escalation, heartbeat, stale completion, or rejected completion.

Follow the live guide's exact recovery action for launch, Dispatch, delivery, or release failures. Never retry a provider automatically, switch providers, blindly resend an exactly-once completion, or turn an operational gap into a technical verdict.

## Revalidate and Report

Immediately after completion, recompute every immutable snapshot file digest and both consented digests, then inspect the original Git state separately.

For a staged target, verify from the authoritative worker evidence that the reviewer read index blobs and `git diff --cached`, not working-tree copies.

For a commit or range target, verify from the authoritative worker evidence that the reviewer read the resolved endpoint blobs and diffs rather than working-tree copies.

Invalidate the review when the immutable snapshot or either consented digest changed, the worker modified files, authoritative worker evidence does not bind every participant to that snapshot, the reviewer examined the original checkout or another scope, or the selected provider's required subagent topology and effective models cannot be verified. Report later original-checkout drift separately and never reinterpret the review as covering those newer bytes.

Verify every returned finding against the exact authority, index or commit snapshot, production callers, persistence and race boundaries, and existing tests without changing files or running checks. Classify each item as:

- **Valid**: confirmed and actionable; include it in the primary findings with the smallest remediation and regression-coverage recommendation.
- **Invalid**: contradicted by exact evidence; omit it from primary findings and report only the rejected count.
- **Needs confirmation**: dependent on missing authority or runtime evidence; report it separately with the exact evidence needed and do not count it as valid.

If the lead returned `APPROVE`, first confirm the intended target, authority, topology, digest stability, and empty modified-file set. Missing output, unverifiable model use, scope drift, lifecycle failure, or incomplete adjudication prevents a clean verdict.

Return the target and digest, selected tool:model and CLI version, source-transmission consent, review topology, independent reviewer verdict, valid findings, confirmation needs, rejected count, recommended responses, and separate Orca Run, Task, Dispatch, terminal, and lifecycle status. Do not expose credentials, private provider payloads, raw transcripts, or subagent reasoning.
