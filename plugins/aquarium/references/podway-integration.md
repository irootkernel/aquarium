# Podway Integration Contract

Read this reference whenever `task-handler`, `epic-handler`, or `epic-validator` uses its default Podway path. Skip it only when the current user explicitly opts this workflow out before its managed session starts or a higher-priority instruction prohibits Podway. Podway records and guards procedure state; it does not run commands, validate the truth of evidence, mutate Git, or replace repository authority.

Reference `$use-podway` when it is installed and valid, and follow it for current Procedure v2 command grammar, state loops, lifecycle, authoring, and recovery mechanics. This contract remains authoritative for Aquarium roadmap authority, default selection, opt-out, readiness, session ownership, approval boundaries, and evidence mapping.

If the optional skill is unavailable or invalid on the default path, report that once and use the bounded mechanics below. When repository guidance requires it, stop and route the exact gap to `$aquarium:dev-setup` instead of falling back.

## Select Per Workflow

Select Podway by default for every invocation of `task-handler`, `epic-handler`, and `epic-validator`. Exclude it only when:

- the current user explicitly asks to omit Podway from this workflow before its managed session starts; or
- a higher-priority system or repository instruction prohibits Podway.

Treat an opt-out in the plan or execution-envelope approval as approval of the same disclosed envelope without its Podway operations; do not require another approval merely to remove them. Keep the opt-out local to the named task, epic, or validation workflow. Re-select Podway by default for every later workflow; never carry an opt-out forward implicitly.

For an opted-out workflow, do not load or reference `$use-podway`, run a Podway command, inspect daemon, workspace, Procedure, or session state, or let any Podway condition affect the workflow. A healthy, degraded, mismatched, or unfinished Podway session is invisible to that workflow.

## Check Readiness on the Default Path

Unless the workflow is already opted out, verify that Podway is ready for Aquarium use before requesting plan or execution-envelope approval. Readiness requires the supported stable `v0.2.3` through `v0.2.x` CLI and matching daemon on native Apple Silicon macOS, reachable healthy workspace state, `.podway/config.yaml`, `.podway/.gitignore`, and all three tracked managed files byte-identical to the plugin sources and valid under `podway procedure check --warnings-as-errors`:

- `.podway/procedures/aquarium-task-v2.yaml`;
- `.podway/procedures/aquarium-goal-v2.yaml`;
- `.podway/procedures/aquarium-validation-v2.yaml`.

These components describe availability and readiness only; the handler invocation selects Podway by default. When readiness is incomplete or degraded, stop and ask the user to choose between repair through `$aquarium:dev-setup` and an explicit opt-out for this workflow. Do not silently fall back or reinterpret the workflow as opted out.

`readiness_status=not_configured` means the three managed Procedures are absent. It is unrelated to `LEGACY_PROCEDURE_STATE_UNSUPPORTED`, which means Podway found Procedure v1 runtime state. On that error, stop, preserve the exact worktree and error code, let the user make any desired backup, and route a separately approved `podway reset --all` recovery to `$aquarium:dev-setup`; never convert, edit, or delete runtime state directly.

## Keep Authorities Separate

- The canonical roadmap owns requirements, task and epic identity, lifecycle vocabulary, and official completion state.
- Podway owns the active procedure snapshot, attempt and rework history, recorded evidence, goal revisions, criterion assessments, and procedural terminal outcome.
- The Codex goal is a temporary projection of the currently actionable Aquarium work recorded inside the Podway session. It may be absent during an explicitly goal-free read-only audit and may narrow to one owned remediation group, but it must never contradict or override the roadmap, Podway goal revision, or current node.
- Git commits, upstream publication, provider publication, live rollout, and external validation remain separate evidence states.

Podway evidence is a caller-recorded claim. Verify tests, reviews, approvals, revisions, and artifacts against their native authorities before recording them or making a decision.

## Read and Mutate Safely

Use `podway observe --json --wait-for-idle`; never parse human output. Require successful runtime commands to use `podway.output/v3`, observations to identify `podway.observation-result/v1`, and failures to use `podway.error/v1`. Treat the observation as one authoritative snapshot: read identity and queue state from `status`, current guidance and allowed actions from `guidance`, bounded item declarations from `active_items`, and copyable fenced commands from `mutation_templates`. A null `guidance` means the session is completed or cancelled. `podway version --json` retains its compact result.

Before every mutation, re-observe and pass every applicable workspace, session, session-revision, attempt, goal-revision, and item-revision fence plus a deterministic operation-specific idempotency key. Select only commands present in the latest `mutation_templates`, fill semantic placeholders only from verified work, and use only IDs from machine fields such as `allowed_option_ids` and `allowed_manual_rework_targets`. Use `podway help <route>` rather than inventing flags.

After every successful mutation, re-observe rather than calculating revisions locally. On a precondition failure, re-observe and derive the next action again. On `MUTATION_OUTCOME_UNKNOWN`, use `podway --json job lookup --idempotency-key <key>` and reconcile the durable result before considering resubmission with the same canonical request and key.

Record bounded summaries and references, not source contents, credentials, raw provider payloads, or full logs. For checks record the exact command, actor provenance, exit status, current source revision or dirty-tree identity, and a digest or stable evidence reference. For review record the exact target, run identity, coverage and publication status, findings-query status, and unresolved valid findings.

## Own Sessions Conservatively

Only `task-handler`, `epic-handler`, and `epic-validator` may own or advance an Aquarium Podway workflow session, and only on the default Podway path for that exact workflow. A standalone user request that explicitly invokes `$use-podway` may inspect, cancel, or discard the exact current session without adopting roadmap or workflow ownership. `$aquarium:dev-setup` may inspect only the bounded session facts needed for readiness diagnosis. `$aquarium:task-commit` may inspect only bounded read-only current-session facts needed to identify the owning handler and must never advance or mutate Podway. Leaf and other utility skills stay Podway-blind and return native evidence to their caller.

Before delegating work, the owner re-observes and verifies the expected immutable Procedure ID, canonical workflow identity, session, attempt, goal revision, and current graph node. After delegation, the owner independently verifies the leaf postcondition, records only the supported bounded evidence with fresh fences, and selects only a transition allowed by the observation guidance and represented by a current mutation template. The leaf never inspects or records Podway state.

A session is owned by the current Aquarium workflow only when its immutable Procedure ID and task title or canonical identity match. If discovery reveals a different, mismatched, completed, cancelled, or unfinished current session, stop and report its session ID, Procedure ID, lifecycle, current node and attempt, and available canonical identity. Treat a healthy supported Procedure v2 session conflict as a lifecycle conflict, not as degraded readiness, and never route it to `$aquarium:dev-setup` repair.

Never cancel, reset, replace, reopen, or reinterpret the conflicting session automatically. Offer only the dispositions supported by its state and the user's intent: resume unfinished work through its matching handler, leave it untouched through an explicit opt-out for the new workflow, or manage cancellation or deletion through a standalone explicit `$use-podway` request. When deletion or freeing the session slot is desired, provide an exact `$use-podway` current-session discard handoff naming the repository and observed session ID; that handoff grants no cleanup authority by itself.

Do not mutate Podway before the workflow's existing plan or execution-envelope approval. On the default path, disclose the matching session start or resume and all bounded Podway mutations in that plan or envelope; approval covers only those disclosed operations. Accept an explicit opt-out until the first managed-session mutation.

After the session starts, do not abandon it and continue without Podway. Classify a later stop or opt-out request through the flow below. A changed desired outcome requires `podway --json goal revise` with a declared rework target; it must not be disguised as another item update.

## Handle In-Progress Stop Requests

When the user asks to stop after the first managed-session mutation, stop Aquarium work and clarify the intended disposition from the choices below. Do not interpret an unqualified stop request as permission to cancel or reset, and do not use `podway block` for an ordinary pause.

- **Resume later:** Leave the session active without a Podway mutation. Report its identity, lifecycle, current node and attempt, recorded progress, queue state, and the exact continuation request. A later matching workflow may resume it; another default Podway workflow remains blocked by the active session.
- **Abandon and preserve history:** Explain that `cancel` ends the task rather than pausing it and that a cancelled session never reactivates. Reference `$use-podway`, observe and summarize the exact current session, obtain explicit authorization to cancel that session, use only the fresh supported mutation template, then re-observe and report the terminal state.
- **Delete the session:** Explain that `reset` irreversibly deletes session-scoped history while preserving workspace initialization. Follow `$use-podway`'s current-session discard flow: observe and summarize the exact session, preview the fenced reset with `--dry-run`, show the result and history loss, obtain separate explicit authorization, re-observe, execute the fresh fenced reset, and verify `SESSION_NOT_FOUND`. Do not cancel first when deletion or freeing the session slot is the goal.

Keep Podway lifecycle, the roadmap, Git, and the Codex goal separate. None of these dispositions commits work, changes roadmap state, or proves the goal achieved. If the user wants remaining Aquarium work to continue without Podway, finish the selected disposition and start a new explicitly opted-out workflow; never switch the current workflow in place.

For sequential epic delivery, use one `aquarium-goal-v2` session per member task, pre-validation remediation, or closeout goal. Once `aquarium-validation-v2` starts, record its audit-owned remediation and re-audit inside that session because a worktree cannot host a nested goal session.

Reset only after a session is successfully terminal and its roadmap state, evidence, and required commit have been re-read and handed off. The approved epic envelope may authorize these exact terminal-to-next-goal resets. A Procedure update never migrates an active snapshot and applies only to a later session.

## Map the Managed Procedures

- `aquarium-task-v2` is owned by `task-handler`; its nodes correspond to the approved plan, implementation, verification record and decision, refinement, documentation, Mulgae review record and decision, goal assessment, the assessed outcome with its follow-up commitments, final user approval, and closeout.
- `aquarium-goal-v2` is owned by `epic-handler` for one member-task, pre-validation remediation, or closeout goal outside an active validation session. The epic closeout goal therefore starts only after the validation session is successfully terminal and reset.
- `aquarium-validation-v2` is owned by `epic-handler` for its final epic audit and by `epic-validator` for cold validation and convergence. Each remediate record covers whatever remediation its owner completes before the next audit: one goal for `epic-handler`, the full confirmed-gap group set for `epic-validator`.

The owner records a leaf report only after independently checking the leaf postcondition. A failed check or valid unresolved review finding must select the failure route and create fresh rework evidence. A final Podway `achieved` outcome cannot make a non-successful roadmap task successful, replace required approval, create a commit, or establish publication.
