# Podway Integration Contract

Read this reference whenever `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, `war-room`, or `design-qa` uses its default Podway path. Each workflow reads [evidence-residency.md](evidence-residency.md) independently even when Podway is opted out or unavailable. Skip only this Podway reference when the current user explicitly opts the workflow out before its managed session starts or a higher-priority instruction prohibits Podway. A non-Git `new-project` also skips Podway completely. Podway records and guards procedure state; it does not run commands, validate the truth of evidence, mutate Git, or replace repository authority.

Reference `$use-podway` when it is installed and valid, and follow it for current Procedure v2 command grammar, state loops, lifecycle, goal, and recovery mechanics. Route Procedure authoring to the separately installed `$create-podway-procedure` maintainer skill. Aquarium defines when its workflows request a Podway session and how they map evidence; Podway remains authoritative for session lifecycle, archival, and deletion mechanics.

If the optional skill is unavailable or invalid on the default path, report that once and use the bounded mechanics below. When repository guidance requires it, stop and route the exact gap to `$aquarium:dev-setup` instead of falling back.

## Select Per Workflow

Select Podway by default for every Git-backed invocation of `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, `war-room`, and `design-qa`. Exclude it only when:

- the current user explicitly asks to omit Podway from this workflow before its managed session starts; or
- a higher-priority system or repository instruction prohibits Podway.

Treat an opt-out in the plan or execution-envelope approval as approval of the same disclosed envelope without its Podway operations; do not require another approval merely to remove them. Keep the opt-out local to the named workflow. Re-select Podway by default for every later workflow; never carry an opt-out forward implicitly.

For an opted-out workflow, do not load or reference `$use-podway`, run a Podway command, inspect daemon, workspace, Procedure, or session state, or let any Podway condition affect the workflow. A healthy, degraded, mismatched, or unfinished Podway session is invisible to that workflow.

## Check Readiness on the Default Path

Unless the workflow is already opted out, verify that Podway is ready for Aquarium use before requesting plan or execution-envelope approval. Readiness requires the supported stable `v0.2.6` through `v0.2.x` CLI and matching daemon on native Apple Silicon macOS, reachable healthy workspace state, `.podway/config.yaml`, `.podway/.gitignore`, and all five tracked managed files byte-identical to the plugin sources and valid under `podway procedure check --warnings-as-errors`. Use bounded `podway --json daemon wait-ready --timeout 120s`; healthy requires ready state and stage plus completed worktree recovery. A nonzero failed count may represent quarantined completed recovery and does not independently degrade readiness. An exact v0.2.5 Procedure workaround is migration evidence, not readiness, and must be replaced with canonical bytes before a managed workflow starts:

- `.podway/procedures/aquarium-task-v2.yaml`;
- `.podway/procedures/aquarium-goal-v2.yaml`;
- `.podway/procedures/aquarium-validation-v2.yaml`;
- `.podway/procedures/aquarium-design-v2.yaml`;
- `.podway/procedures/aquarium-war-room-v2.yaml`.

These components describe availability and readiness only; the current Aquarium invocation selects Podway by default. When readiness is incomplete or degraded, stop and ask the user to choose between repair through `$aquarium:dev-setup` and an explicit opt-out for this workflow. Do not silently fall back or reinterpret the workflow as opted out.

`readiness_status=not_configured` means the five managed Procedures are absent. It is unrelated to `LEGACY_PROCEDURE_STATE_UNSUPPORTED`, which means Podway found Procedure v1 runtime state. On that error, stop, preserve the exact worktree and error code, let the user make any desired backup, and route a separately approved `podway reset --all` recovery to `$aquarium:dev-setup`; never convert, edit, or delete runtime state directly.

## Keep Authorities Separate

- The canonical roadmap owns requirements, task and epic identity, lifecycle vocabulary, and official completion state.
- Podway owns the active procedure snapshot, attempt and rework history, recorded evidence, goal revisions, criterion assessments, and procedural terminal outcome.
- The Codex goal is a temporary projection of the currently actionable Aquarium work recorded inside the Podway session. It may be absent during an explicitly goal-free read-only audit and may narrow to one owned remediation group, but it must never contradict or override the roadmap, Podway goal revision, or current node.
- Git commits, upstream publication, provider publication, live rollout, and external validation remain separate evidence states.

Podway evidence is a caller-recorded claim. Verify tests, reviews, approvals, revisions, and artifacts against their native authorities before recording them or making a decision.

## Read and Mutate Safely

Use `podway observe --json --wait-for-idle`; never parse human output. Require successful runtime commands to use `podway.output/v3`, observations to identify `podway.observation-result/v3`, prepared-aware status to identify `podway.status-result/v3` or `podway.compact-status-result/v3`, prepared-aware job reads to identify `podway.job-result/v4` or `podway.job-lookup-result/v4`, and failures to use `podway.error/v1`. Treat the observation as one authoritative snapshot: read identity and queue state from `status`, current guidance and allowed actions from `guidance`, bounded item declarations from `active_items`, and fenced recipes from `mutation_templates`. Add required semantic values only after reading command help and verifying their native authority. `podway version --json` retains its compact result.

Require prepared start or replacement to return `podway.session-start-result/v3`, begin to return `podway.session-begin-result/v1`, terminal disposition to return `podway.terminal-disposition-result/v1`, and reset to return `podway.session-reset-result/v1`. A successful envelope with another result schema is not proof of the requested mutation; stop and reconcile rather than advancing.

A fresh `start` or approved replacement creates a prepared revision-0 session with no attempt, cursor, goal, or active items. Re-observe it, require prepared guidance and the current `session.begin` mutation template, then use fresh workspace, session, and revision fences plus a distinct idempotency key to create attempt 1 and the initial goal, criteria, and actor. Do not record evidence or issue any item, goal, cursor, decision, rework, completion, or cancellation mutation before `begin` succeeds. A matching prepared session is recoverable workflow state: resume with `begin` only when its Procedure, canonical identity, and recoverable approval all match.

Running guidance carries the ordinary workflow actions. Terminal observation has null guidance and no active items; an undisposed terminal revision offers only terminal disposition, while a disposed terminal revision offers eligible reset and replacement. Never infer mutation authority from null guidance alone.

Before every mutation, re-observe and pass every applicable workspace, session, session-revision, attempt, goal-revision, and item-revision fence plus a deterministic operation-specific idempotency key. Select only commands present in the latest `mutation_templates`, fill semantic placeholders only from verified work, and use only IDs from machine fields such as `allowed_option_ids` and `allowed_manual_rework_targets`. Use `podway help <route>` rather than inventing flags.

After every successful mutation, re-observe rather than calculating revisions locally. On a precondition failure, re-observe and derive the next action again. On `MUTATION_OUTCOME_UNKNOWN`, use `podway --json job lookup --idempotency-key <key>`, require `podway.job-lookup-result/v4`, and reconcile the durable result before considering resubmission with the same canonical request and key.

Observation readback previews are bounded metadata, not complete recorded values. When a decision needs a selected full value, use the observation's evidence source and digest with `podway --json evidence read --source <source> --item <item>`, follow each `next_page_token` until the result is no longer truncated, and verify stable identity and value digest across pages. On `EVIDENCE_PAGE_TOKEN_STALE`, re-observe and restart at page one rather than mixing snapshots.

Record bounded summaries and references, not source contents, credentials, raw provider payloads, or full logs. For checks record the exact command, actor provenance, exit status, current source revision or dirty-tree identity, and a digest or stable evidence reference. For review record the ordinal and mode, exact target and run identity, coverage and publication status, findings-query status, unresolved valid findings, and any deferred run and finding identities.

These records are local runtime and orchestration evidence. Never copy them, their `.podway/runtime/**` location, or their Mulgae or Gaori runtime references into tracked documentation as a validation or remediation log. When a later repository consumer requires durable evidence, verify and promote the native evidence through the shared residency contract and use only a tracked promoted manifest and digest; Podway's recorded claim is not a promotion source.

## Reconcile an Existing Session Only When Starting Another

Aquarium does not own Podway sessions and does not assign them to skills. A skill name, actor label, Procedure ID, task title, or canonical identity is descriptive metadata, not an access-control principal. Do not route the user to a matching owner, require an owner-prefixed identity, or create a cross-owner handoff protocol.

Before delegating work inside an already selected session, re-observe and verify its immutable Procedure ID, canonical identity, lifecycle, revision, attempt, goal revision, and current graph node as applicable. After delegation, independently verify the leaf postcondition, record only supported bounded evidence with fresh fences, and select only a transition allowed by current guidance and a current mutation template. Leaf capabilities such as upstream Ouroboros remain Podway-blind and return native evidence to their Aquarium caller.

Inspect an existing session conflict only when the current Aquarium invocation is about to start a different Podway session. If the current session's Procedure and canonical identity match the requested work, resume it normally. Otherwise report the current session ID, Procedure ID, lifecycle, revision, current node and attempt when present, disposition, and canonical identity, then obtain an explicit user choice before changing it:

- **Preserve:** Leave the existing session unchanged and either stop the new workflow or continue the new workflow with an explicit Podway opt-out. Do not let the preserved session otherwise affect the opted-out workflow.
- **Finish or cancel while preserving history:** Follow `$use-podway` for the exact current lifecycle action and its required approval. Do not claim that Aquarium must find or invoke the skill that previously used the session.
- **Delete:** Follow `$use-podway`'s current-session discard flow, including observation, fenced dry-run, disclosure of history loss, and separate explicit deletion authorization.
- **Start after an eligible terminal session:** Verify its disposition and current `session.start_replace` template, disclose that plain `start` automatically archives the predecessor, obtain explicit approval, and execute the template's current argv with fresh fences.

Never cancel, delete, reset, replace, or invent a terminal disposition merely to free the slot. A healthy existing session is a lifecycle choice for the user, not degraded Aquarium readiness and not a reason to route to `$aquarium:dev-setup`.

Never cancel, reset, force-replace, reopen, or reinterpret a blocking lifecycle conflict automatically. When deletion itself is the user's intent and no approved successor will replace the session, provide an exact `$use-podway` current-session discard handoff naming the repository and observed session ID; that handoff grants no cleanup authority by itself. Reset is deletion, not preparation for a successor workflow.

Do not mutate Podway before the workflow's existing plan or execution-envelope approval. On the default path, disclose prepared session start or resume, the separate fenced `begin`, all bounded workflow mutations, any terminal disposition, and any eligible replacement or reset in that plan or envelope; approval covers only those disclosed operations. Accept an explicit opt-out until the first managed-session mutation.

After the session starts, do not abandon it and continue without Podway. Classify a later stop or opt-out request through the flow below. A changed desired outcome requires `podway --json goal revise` with a declared rework target; it must not be disguised as another item update.

## Record Terminal Disposition Conservatively

Treat terminal disposition as a caller assertion about the result outside the session, not as workflow success, evidence publication, or a durable Aquarium record. It does not create a roadmap edit, commit, push, or agent handoff. Record one only after re-observing the exact completed or cancelled revision and verifying the asserted semantics against native authority.

- Use `handed_off` only when an exact authoritative external result already exists. For a roadmap task, re-read its successful lifecycle, required evidence, clean task-owned residue, and actual commit, then use a bounded summary plus a stable reference containing the exact commit SHA. The presence of a roadmap entry without that completed external result is insufficient.
- Use `not_required` only when no final external handoff or repository result is required and current roadmap, Git, review, and worktree evidence has been re-read. This covers a disclosed internal epic boundary, an epic closeout with no final repository diff, and an achieved validation run whose lifecycle, current requirements, accepted risks, and actionable handoffs require no final repository result. Earlier task or remediation commits do not prevent this disposition; record them as verified predecessors and record the concrete no-final-result reason. Never use `not_required` merely because no handoff reference is available.
- Otherwise leave the terminal revision undisposed. Do not invent a reference or reason, and never choose force reset or force replacement automatically. A final session may remain terminal after `handed_off` or remain undisposed when no disposition is supported.

After a fresh supported disposition, re-observe and use only the eligible reset or `session.start_replace` template exposed for that exact revision. When an approved successor workflow needs the worktree slot, execute the current plain `start` template so Podway atomically archives the disposed predecessor and creates the prepared successor; then re-observe and `begin` it. Prepared and running sessions follow the current start policy and are preserved unless an explicit `--on-existing delete` choice is authorized. Inactive history is inspected with `list` and `show`, purged only through separately authorized `archive purge`, and limited to 32 sessions; never auto-purge or evict it. A standalone task, validation, design, war-room, or final epic session is not reset merely because it is terminal.

## Handle In-Progress Stop Requests

When the user asks to stop after the first managed-session mutation, stop Aquarium work and clarify the intended disposition from the choices below. Do not interpret an unqualified stop request as permission to cancel or reset, and do not use `podway block` for an ordinary pause.

- **Resume later:** Leave the session active without a Podway mutation. Report its identity, lifecycle and revision, current node and attempt when present, recorded progress, queue state, and the exact continuation request. A later Aquarium invocation may resume it; only a request that needs a different Podway session triggers the explicit existing-session choice above.
- **Abandon and preserve history:** Explain that `cancel` ends the task rather than pausing it and that a cancelled session never reactivates. Reference `$use-podway`, observe and summarize the exact current session, obtain explicit authorization to cancel that session, use only the fresh supported mutation template, then re-observe and report the terminal state.
- **Delete the session:** Explain that `reset` irreversibly deletes session-scoped history while preserving workspace initialization. Follow `$use-podway`'s current-session discard flow: observe and summarize the exact session, preview the fenced reset with `--dry-run`, show its `none`, `record_disposition`, or `force` requirement and the history loss, obtain every required semantic value, then obtain separate explicit authorization, re-observe, execute the fresh fenced eligible or explicitly confirmed force reset, and verify `SESSION_NOT_FOUND`. Do not cancel first when deletion or freeing the session slot is the goal.

Keep Podway lifecycle, the roadmap, Git, and the Codex goal separate. None of these dispositions commits work, changes roadmap state, or proves the goal achieved. If the user wants remaining Aquarium work to continue without Podway, finish the selected disposition and start a new explicitly opted-out workflow; never switch the current workflow in place.

For sequential epic delivery, use one `aquarium-goal-v2` session per member task, pre-validation remediation, or closeout goal. Once `aquarium-validation-v2` starts, record its audit-owned remediation and re-audit inside that session because a worktree cannot host a nested goal session.

Replace any Aquarium session only after it is successfully terminal, its authoritative artifacts, Design Gate or roadmap state, evidence, required commit, and worktree have been re-read, and the exact terminal revision has a supported disposition. The approved successor envelope may authorize that exact eligible replacement. A Procedure update never migrates an active snapshot and applies only to a later session.

## Map the Managed Procedures

- `aquarium-task-v2` supports the `task-handler` lifecycle; its nodes correspond to the approved plan, implementation, verification record and decision, refinement, documentation, Mulgae review record and decision, goal assessment, the assessed outcome with its follow-up commitments, final user approval, and closeout. Its plan record has an optional `plan-handoff-artifact` item that an explicit task plan handoff fills.
- `aquarium-goal-v2` supports one `epic-handler` member-task, pre-validation remediation, or closeout goal outside an active validation session. Its work record has an optional `plan-handoff-artifact` item propagated only for an explicit epic plan handoff. The epic closeout goal therefore starts only after the validation session is successfully terminal, has a supported disposition, and is atomically replaced with the prepared closeout session.
- `aquarium-validation-v2` supports final epic audit, cold validation, and convergence. Its baseline record has an optional `plan-handoff-artifact` item for continuity from `epic-handler`; `epic-validator` leaves it absent and exposes no plan-handoff mode. Each remediate record covers the verified remediation completed before the next audit: one goal for `epic-handler`, the full confirmed-gap group set for `epic-validator`.
- `aquarium-design-v2` supports `new-project`, `new-feature`, `refactor`, and `design-qa` for one Git-backed design-document lifecycle. Ouroboros discovery and QA are leaf evidence; Aquarium retains repository authority.
- `aquarium-war-room-v2` supports `war-room`; it ends with an approved task, epic, or incomplete-investigation document and never records a fix implementation.

The caller records a leaf report only after independently checking the leaf postcondition. A failed check or valid unresolved review finding must select the failure route and create fresh rework evidence while an authorized remediation budget remains. The only exceptions are epic-handler's explicit second-review member-task deferral and a confirmation-only review hold awaiting user direction; neither exception may be reinterpreted as clean review evidence. A final Podway `achieved` outcome cannot make a non-successful roadmap task successful, replace required approval, create a commit, or establish publication.
