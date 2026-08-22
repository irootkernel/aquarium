---
name: orca-review
description: "Run one supervised, read-only review of an exact repository snapshot through a user-selected installed AI CLI in Orca, using a bounded multi-agent hierarchy and locally adjudicating the result. Use when the user explicitly invokes $aquarium:orca-review and asks to review staged changes, working-tree changes, a commit or range, or one named task or epic."
---

# Orca Review

Review one exact repository snapshot through one user-selected AI CLI while preserving the checkout, supervising the worker through Orca, and independently verifying the returned findings. This is a standalone utility; it does not replace `$aquarium:independent-review` or the Mulgae phase owned by `$aquarium:task-review`.

Explicit invocation authorizes read-only local discovery, starting the installed Orca runtime when needed, and structured preparation and final-transmission questions. A preparation choice authorizes only local creation of one disclosed private snapshot and exact Aquarium Task specification; it authorizes no Orca registration or provider transmission.

Only the later final tool:model choice authorizes transmission of the complete disclosed snapshot and Task bytes plus disclosed Orca-owned lifecycle metadata to that provider, with temporary Orca registration and cleanup.

It does not authorize source-checkout edits, tests, builds, generators, formatters, staging, commits, pushes, publication, authentication changes, software installation, or another provider request.

## Fail Closed on Orca

1. Require the separately installed `$orca-cli` skill to be available in the active skill catalog. If its availability cannot be established, stop; do not approximate its contract from this skill.
2. Resolve the Orca executable exactly as `$orca-cli` requires and reuse it for the complete invocation. If the selected executable is missing or fails, report the exact error and stop; do not try another executable.
3. Load the version-matched guides with the selected executable's `skills get orca-cli` and `skills get orchestration` commands before using Orca. Follow those live guides rather than cached command syntax, including the examples in this skill and its reference. Stop when either guide cannot be retrieved.
   When a required local route is omitted from both retrieved guides, query the selected CLI's read-only `agent-context --json` and use only the exact command schema for that route. If that schema is also absent, query only the exact route with `<ORCA> <route> --help`. Treat the selected installed CLI's agent-context or help as grammar authority for that route only; stop if neither exposes every required identity.
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

Probe only these executable names with `command -v`: `claude`, `codex`, `cursor-agent`, and `kimi`. Resolve each successful result to one canonical absolute regular executable outside the original Git root, record its SHA-256 digest, and invoke that exact path for its local `--version` command. A command is available only when path resolution, outside-root verification, hashing, and the version probe succeed. Do not authenticate, list remote models, contact a provider, update a CLI, or inspect credentials during discovery.

Require the Orca runtime itself to be local to the coordinator host and current operating-system user. Reject nonempty `ORCA_ENVIRONMENT` or `ORCA_PAIRING_CODE`, any `--environment` or `--pairing-code` route, and any agent-context or guide evidence that identifies a remote, paired, or unverifiable runtime.

Record the verified local runtime identity before selection. Revalidate it before both structured choices and immediately before every lifecycle read or mutation, including registration, Run or Task creation, terminal creation, worker start, Dispatch, retain or release, and cleanup, and stop on drift.

Build the selection menu from successful probes only:

- `claude` exposes `claude:fable with opus/sonnet` and `claude:opus`.
- `codex` exposes `codex:gpt-5.6-sol`.
- `cursor-agent` exposes `cursor:grok-4.6`; omit every Cursor choice when `cursor-agent` is unavailable.
- `kimi` exposes `kimi:k3`.

Fail closed when no supported CLI is available. Do not infer model availability from installation; the selected launch verifies it.

Use the host's structured ask/answer tool, normally `request_user_input`, whenever available. Present no more than three choices in one call; when more are available, paginate with one navigation choice such as `More installed AIs` and then show only the remaining exact tool:model labels. Even when one choice is available, require the user to select which exact tool:model snapshot to prepare.

Before presenting a preparation choice, build and display a source manifest. It must list every repository, target, supporting-source, instruction, and authority file intended for materialization, with its source identity and SHA-256 digest, plus the explicitly excluded state. Sort the records by source identity as newline-terminated `<sha256>  <source-identity>` lines and hash those exact UTF-8 bytes as the source-manifest digest.

Before displaying, hashing, materializing, command-routing, or reusing any externally derived identity or consent-visible value, parse it to the exact bounded field required by its owning schema. This includes provider version output, local runtime identity, repository and setup identity, worktree and snapshot identity, lifecycle identifiers, paths, labels, source identities, and every Task field.

Require one valid UTF-8 record with no Unicode control or format character and no line or paragraph separator. Reject extra lines, surrounding payload, missing fields, and malformed values.

Stop on an identity containing any Unicode `Cc`, `Cf`, `Zl`, or `Zp` code point, including `U+0000` through `U+001F`, `U+007F` through `U+009F`, bidirectional marks, embeddings, overrides, and isolates such as `U+202E`, and `U+2028` or `U+2029`; never escape, normalize, or substitute it into consent text, manifest records, or command arguments.

Each preparation choice must identify the exact tool:model, canonical provider executable path, executable digest and observed version, verified local Orca runtime identity, review target and digest, source-manifest digest, private snapshot path policy, and that selecting it authorizes local preparation only. If structured ask/answer is unavailable, report that exact prerequisite failure and stop without preparing a snapshot or transmitting source.

Never auto-select, infer consent from silence, or treat preparation approval or approval for another provider, snapshot, or manifest as transmission consent.

## Dispatch the Reviewer

Immediately after the preparation choice and before reading provider instructions or creating snapshot state, recompute the recorded target and every source-manifest file digest plus the source-manifest digest. If any digest or recorded target identity differs, do not prepare or transmit; establish the changed target again and require a new preparation choice.

After that check succeeds, read [provider-contracts.md](references/provider-contracts.md) and materialize only the verified source bytes into one private standalone Git snapshot under a fresh `/tmp` directory. Give it no remote, credential material, object alternates, or link to the source repository's Git metadata. Preserve the disclosed target form and necessary baseline evidence. Reject any symlink whose resolved target escapes the snapshot.

Build the exact Aquarium-supplied Task specification before transmission. In a coordinator-only sibling directory outside the Aquarium-supplied snapshot, create the complete transmission manifest over every regular file and symlink identity Aquarium will supply in the finished snapshot, including standalone `.git` metadata, plus the exact Aquarium Task specification bytes.

Sort newline-terminated `<sha256>  <provider-visible-identity>` records and hash them as the transmission-manifest digest. Make the complete snapshot read-only, then recompute and require every manifest record to match.

Present a second, final structured choice that identifies the exact tool:model, canonical provider executable path, executable digest and observed version, verified local Orca runtime identity, review target and digest, source-manifest digest, complete transmission-manifest digest, temporary registration and cleanup, and exact snapshot and Task scope.

Disclose that the selected local CLI runs as the current operating-system user. Aquarium's manifest and read-only instructions constrain what Aquarium supplies and authorizes, but are not an operating-system read sandbox; the CLI may technically access other files already readable by that user. Require explicit acceptance of that local-process capability in the same final choice.

Disclose that Orca's version-matched orchestration layer prepends its own lifecycle preamble and identifiers when Dispatch is injected; those are Orca-owned runtime metadata, not Aquarium prompt bytes. State that this final choice alone authorizes registration and transmission of the manifested bytes plus that disclosed metadata category to the selected provider.

A decline deletes only the owned snapshot and coordinator manifest. Any unavailable structured ask/answer surface stops without registration or transmission.

Immediately after final selection and before creating Orca state or transmitting source, revalidate the local Orca runtime identity and recompute the selected provider executable's canonical path, digest, and version, the target, source manifest, every Aquarium-supplied snapshot and Task record, and the complete transmission-manifest digest. Any change invalidates final consent; delete only the owned local preparation and restart from target establishment.

After the immutable snapshot verifies, obtain exact grammar for `repo add`, `project setups`, `project setup-delete`, and the `path:<absoluteSnapshotPath>` worktree selector from the retrieved guides or the bounded agent-context and exact-route help fallbacks above.

Snapshot `project setups --json`, register only the snapshot with `repo add --path <absoluteSnapshotPath> --json`, then query `project setups --json` again. Require exactly one newly created setup whose path equals the snapshot and whose repository identity equals the returned repository identity; record that setup identity and every returned repository and worktree identity.

Require `worktree show --worktree path:<absoluteSnapshotPath> --json` to resolve exactly to the snapshot. Stop instead of supplying an unproven project, host, or setup identity.

On any failure before terminal or worker launch, including registration, path verification, Run creation, or Task creation, inspect the local runtime and every partially created identity once. Remove only the exact owned registration, snapshot, and coordinator manifest when their identities are proven. Remove an exact owned Task or Run only through cleanup grammar established by the live guide; otherwise report that bounded retained lifecycle state for manual recovery, then stop.

Create or bind one Run and create one review Task with `task-create --spec <exactAquariumTaskSpec>`. Immediately before terminal creation and again immediately before the source-bearing Dispatch, revalidate the local runtime, provider executable path, digest and version, exact setup and snapshot-path mapping, every provider-visible snapshot and Aquarium Task byte, and all three consented digests. Any drift stops before Dispatch; do not transmit and do not repair the consented bytes in place.

Start one fresh selected lead through the recorded exact snapshot path selector and the consent-bound canonical provider executable path, then use `dispatch --inject` so Orca sends that Task with its disclosed lifecycle preamble.

Never expose or identify the original checkout to a participant, register a linked Git worktree, resolve the provider from terminal `PATH`, or reuse an existing AI terminal.

After any terminal launch, worker-start, or Dispatch attempt, never clean up from a command failure alone. Inspect the authoritative worker and terminal state through the live guide. Retain the registration and snapshot for every active or unproven worker; cleanup is allowed only after the worker is proven settled and successfully released with no retention request.

The Task specification must include a stable repository report label that contains no original-checkout path, immutable snapshot root, exact target identity and digest, source-manifest digest, named requirement authority, included and excluded state, and selected tool:model with its canonical provider executable identity.

It must also include the selected provider's required subagent topology and effective-model verification duties copied from the reference, participant-wide read-only restrictions, and required report schema. Do not embed the complete transmission-manifest digest in bytes hashed by that same manifest.

Require every participant to read only the immutable snapshot and bind authoritative worker scope evidence to the exact target and source-manifest digest. Bind the complete transmission-manifest digest separately to the authoritative Run, Task, and Dispatch identities in coordinator evidence. Do not include the coordinator's suspected findings or intended fixes.

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

For an accepted `worker_done`, retrieve the complete authoritative worker evidence through `worker-read`, process every delivered message and transcript record, and verify the reported topology. If authoritative transcript or scope evidence is unavailable, it prevents a clean verdict.

For every Delivery batch, process every message completely. Only for an accepted terminal `worker_done`, either run `worker-retain --dispatch <dispatchId> --json`, verify its durable receipt, and keep the worker when retention was requested, or release the settled succeeded or failed worker and verify the release receipt. Never retain or release a worker merely for a question, escalation, heartbeat, stale completion, or rejected completion. A required retain or release failure is an operational gap.

After every message in the batch is processed and every required retain or release succeeds, acknowledge that exact batch. For the accepted terminal `worker_done` of the sole expected Dispatch, use `check --ack <deliveryId>` without `--wait`. Inspect that command's response before revalidation: if it returns another queued Delivery batch, process and acknowledge that batch under these same rules, repeating non-waiting acknowledgements until the response reports no Delivery. Any unresolved returned batch blocks revalidation.

For a question, escalation, heartbeat, rejected completion, or stale completion while the expected Dispatch remains active, use `check --ack <deliveryId> --wait --timeout-ms <remainingBudgetMs>`. The timeout must be positive and no larger than the recorded remaining cumulative liveness budget.

Never acknowledge a batch while any message is unresolved or a required retain or release failed; without acknowledgement, FIFO replay intentionally blocks later deliveries.

After successful release, retain the exact temporary registration and owned snapshot through scope revalidation. If retention was requested or the worker remains active, retain both and report their paths and identities. Do not release or clean up after a timeout, question, escalation, heartbeat, stale completion, or rejected completion.

Follow the live guide's exact recovery action for launch, Dispatch, delivery, or release failures. Never retry a provider automatically, switch providers, blindly resend an exactly-once completion, or turn an operational gap into a technical verdict.

## Revalidate and Report

Immediately after completion, recompute every provider-visible snapshot and Aquarium Task record plus all three consented digests, then inspect the original Git state separately.

For a staged target, verify from the authoritative worker evidence that the reviewer read index blobs and `git diff --cached`, not working-tree copies.

For a commit or range target, verify from the authoritative worker evidence that the reviewer read the resolved endpoint blobs and diffs rather than working-tree copies.

Invalidate the review when the immutable snapshot, exact Aquarium Task, or any consented digest changed, the worker modified files, authoritative worker evidence does not bind every participant to that snapshot, the reviewer examined the original checkout or another scope, or the selected provider's required subagent topology and effective models cannot be verified. Report later original-checkout drift separately and never reinterpret the review as covering those newer bytes.

Verify every returned finding against the exact authority, index or commit snapshot, production callers, persistence and race boundaries, and existing tests without changing files or running checks. Classify each item as:

- **Valid**: confirmed and actionable; include it in the primary findings with the smallest remediation and regression-coverage recommendation.
- **Invalid**: contradicted by exact evidence; omit it from primary findings and report only the rejected count.
- **Needs confirmation**: dependent on missing authority or runtime evidence; report it separately with the exact evidence needed and do not count it as valid.

If the lead returned `APPROVE`, first confirm the intended target, authority, topology, digest stability, and empty modified-file set. Missing output, unverifiable model use, scope drift, lifecycle failure, or incomplete adjudication prevents a clean verdict.

After scope revalidation and local adjudication finish, clean up only when the worker was settled and successfully released and no retention was requested. First revalidate the exact local runtime identity and query setups; require the recorded setup ID still to be the sole registration created by this workflow and still map to the recorded repository identity and exact snapshot path.

Only then remove it with `project setup-delete --setup <recordedSetupId> --json`, confirm that setup identity is absent from `project setups --json`, and delete only the owned snapshot and coordinator manifest.

Retained or active workers keep both until an explicitly requested later settlement. A cleanup failure is an operational gap and prevents reporting complete cleanup; never delete a pre-existing or ambiguously identified setup.

Return the target and digest, selected tool:model and CLI version, source-transmission consent, review topology, independent reviewer verdict, valid findings, confirmation needs, rejected count, recommended responses, snapshot registration and cleanup status, and separate Orca Run, Task, Dispatch, terminal, and lifecycle status. Do not expose credentials, private provider payloads, raw transcripts, or subagent reasoning.
