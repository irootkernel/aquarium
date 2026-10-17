# Podway Integration Contract

Read this reference whenever `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, or `war-room` uses its default Podway path. Each workflow reads [evidence-residency.md](evidence-residency.md) independently even when Podway is opted out or unavailable. Skip only this Podway reference when the current user explicitly opts the workflow out before its managed session starts or a higher-priority instruction prohibits Podway. A non-Git `new-project` also skips Podway completely. Podway records and guards procedure state; it does not run commands, validate the truth of evidence, mutate Git, or replace repository authority.

Reference the independently pinned `$use-podway` source defined in [tool-catalog.md](tool-catalog.md#podway) when it is installed and valid, and follow it for current Procedure v2 command grammar, state loops, lifecycle, goal, and recovery mechanics. Route Procedure authoring to the separately installed `$create-podway-procedure` maintainer skill. Aquarium defines when its workflows request a Podway session and how they map evidence; Podway remains authoritative for session lifecycle, archival, and deletion mechanics.

If the optional skill is unavailable or invalid on the default path, report that once and use the bounded mechanics below. When repository guidance requires it, stop and route the exact global skill gap to `$aquarium:dev-setup-global` instead of falling back.

## Select Per Workflow

Select Podway by default for every Git-backed invocation of `task-handler`, `epic-handler`, `epic-validator`, `new-project`, `new-feature`, `refactor`, and `war-room`. Exclude it only when:

- the current user explicitly asks to omit Podway from this workflow before its managed session starts; or
- a higher-priority system or repository instruction prohibits Podway.

Treat an opt-out in the plan or execution-envelope approval as approval of the same disclosed envelope without its Podway operations; do not require another approval merely to remove them. Keep the opt-out local to the named workflow. Re-select Podway by default for every later workflow; never carry an opt-out forward implicitly.

For an opted-out workflow, do not load or reference `$use-podway`, run a Podway command, inspect workspace, Procedure, or session state, or let any Podway condition affect the workflow. A healthy, degraded, mismatched, or unfinished Podway session is invisible to that workflow.

## Check Readiness on the Default Path

An explicit request for a Podway-backed workflow or Podway diagnosis authorizes the read-only observations needed to prepare its proposal. It does not authorize initialization, configuration changes, session start, or other mutations before the execution envelope is approved. Follow the paired skill's activation and observation contract within that request.

For Task, Goal, Validation, Design and Diagnosis, use [adaptive execution](adaptive-execution.md) and its exact selected-source readiness after read-only fit planning. Runtime/workspace compatibility and the selected source/route are required; unrelated library completeness and unselected provider availability are not startup prerequisites. Preserve full library diagnostics and adopted source obligations.

For legacy managed/admitted sessions, verify that Podway is ready before requesting plan or execution-envelope approval. Its aggregate readiness requires a stable CLI `>=v0.2.14` without a version upper bound on native Apple Silicon macOS, the target worktree with healthy, writer-compatible workspace state, `.podway/config.yaml`, `.podway/.gitignore`, and all five managed Procedure paths as tracked regular non-symlink files with the expected filename and Procedure ID that pass `podway procedure check --warnings-as-errors`. Each file must also satisfy the objective handler contract in [Procedure Node Contracts](procedure-node-contracts.md). Canonical bytes are compatible by definition; a same-ID customization remains preserved but cannot enter automatic managed execution when its required nodes, items, selected evidence, or routes are missing or cannot be established. An exact v0.2.5 Procedure workaround is migration evidence, not readiness, and must be replaced with canonical bytes before a managed workflow starts:

- `.podway/procedures/aquarium-task-v2.yaml`;
- `.podway/procedures/aquarium-goal-v2.yaml`;
- `.podway/procedures/aquarium-validation-v2.yaml`;
- `.podway/procedures/aquarium-design-v2.yaml`;
- `.podway/procedures/aquarium-war-room-v2.yaml`.

The explicit [selected-admission path](adaptive-procedures.md#selected-admission-retention-and-recovery)
checks compatible runtime, the exact selected source/binding, invoking entrypoint
and selected route independently of this five-file aggregate. Its CLI needs an
available supported Python environment with YAML and `jsonschema`; missing
dependencies return `missing-prerequisite` without native work or installation.
The setup inspector loads those dependencies only for explicit selected mode.
The selected launcher now forwards exact binding and ordinary qualification context for Task, Goal, Validation, Design and Diagnosis; changed/new bundles require current structural proof and actual ordinary suitability. Preserve
canonical/custom/formal inspection and complete library diagnostics; unrelated
missing templates, optional historic bundles or filename differences cannot alone
invalidate selected compatibility. Adopted same-family custom obligations still
need their existing envelope disposition. Source health never resolves a session
conflict or establishes that a matching definition serves the same goal.

For an adopted session, resolve its native ID/version/digest across every approved
searched root before `begin` or work, including prepared and non-bootstrap running
states. Verify retained source natively and its binding exactly; stop on missing,
corrupt, ambiguous or unsupported selected material. Do not reconstruct from a
mutable library or fall back silently to managed defaults. A selected bootstrap
reference is an additional cross-check. Legacy admitted sessions retain their
original contract without fabricated adaptive metadata.

In the initialized owning worktree, use `podway --json observe` before starting or resuming a managed session. Require Output `podway.output/v4` and `podway.observation-result/v5` for both direct and delegated Procedures. Error `podway.error/v2` with `SESSION_NOT_FOUND` means no current session; it does not authorize initialization. Reconcile matching prepared or running sessions through the native contract. Preserve session identities, choices and mutation fences.

Check the compact CLI version and `version --json --identity`, configuration, native Procedure validity, handler compatibility and workspace health independently. Later stable versions pass the version floor but must still provide the required machine contracts. Use `doctor` for health diagnosis and observation for routine admission. Follow stable Error v2 codes and native read-only recovery recipes for writer/schema mismatch, maintenance, contention or unreadable state. Do not poll a service or use retired wait/mode flags.

These components describe availability and readiness only; the current Aquarium invocation selects Podway by default. When readiness is incomplete or degraded, route a missing or unsupported global Podway CLI or `use-podway` skill to `$aquarium:dev-setup-global`, and route repository configuration or managed-Procedure gaps to `$aquarium:dev-setup`. Stop and ask the user to choose the exact routed repair or an explicit opt-out for this workflow. Do not silently fall back or reinterpret the workflow as opted out.

For an adaptive Task, Goal or Validation, preserve the actual selected route through its qualified binding and ordinary authority. Capability aliases and provider-specialized definitions need no literal `review-route` item. Use the shared selected admission consumer. For the existing canonical/custom/formal path, verify the selected review route directly in the exact installed Procedure file after its native check and handler-contract check pass. Read every `review-route` choice declaration under `node_definitions`; require at least one declaration and the selected route in every declaration. Bind that result to the exact installed source bytes, recheck them before `start`, and verify the admitted session's immutable Procedure snapshot before dispatch. Podway's `--expect-procedure-digest` compares a canonical Procedure digest, not the source-file hash. A recognized prior-canonical digest alone does not establish route membership. Missing, malformed, or unreadable declarations cannot authorize the route. Check provider prerequisites separately. The setup inspector's `review_route_readiness` map depends on compatible CLI identity and workspace readiness and is not the routine session-admission check. A source-file update affects successors only. For an existing session, inspect its immutable Procedure snapshot and actual route declarations instead of substituting the current installed file's result; apply the [legacy route disposition](review-routing-contract.md#procedure-route-compatibility) before dispatch.

Neither a setup repair nor an Aquarium workflow may invoke `workspace remove`. That command deletes the selected worktree's complete `.podway` tree and belongs only to the pinned `$use-podway` flow after an explicit exact-worktree request, complete deletion disclosure, fresh root and workspace-UUID validation, and a `podway.workspace-removal-result/v2` success. It preserves the Git worktree and grants no global cleanup, Git cleanup, commit, or publication authority.

`readiness_status=not_configured` means the managed Procedures are absent. It is unrelated to `LEGACY_RUNTIME_STATE_UNSUPPORTED` or `WORKSPACE_CONTRACT_MISMATCH`. Preserve unsupported state and route repository diagnosis to `$aquarium:dev-setup`. Any separately approved runtime discard belongs to `$use-podway` under the [catalog upgrade contract](tool-catalog.md#upgrade-from-older-writers). A reset creates fresh runtime state; it does not migrate historical sessions. Native recovery output never grants deletion authority.

For Orca-era sources and snapshots, distinguish recognized provenance, native
validity, complete handler compatibility and selected-route membership. Preserve
custom source bytes and session snapshots; prior-source identity alone cannot
admit a new checkpoint. Use [herdr-migration.md](herdr-migration.md) for legacy
worker handling and an exact, separately approved repository update.

## Keep Authorities Separate

- The canonical roadmap owns requirements, task and epic identity, lifecycle vocabulary, and official completion state.
- Podway owns the active procedure snapshot, attempt and rework history, recorded evidence, goal revisions, criterion assessments, and procedural terminal outcome.
- Codex goals and Podway goals have separate creation rules and lifecycles. Create a Codex goal only when explicitly requested under its current tool contract; a Podway goal does not authorize one. When both are authorized, keep their scope consistent with the user objective and roadmap without copying the complete criteria or status history. A bounded Podway session may cover only part of the Codex goal.
- Git commits, upstream publication, provider publication, live rollout, and external validation remain separate evidence states.

Podway evidence is a caller-recorded claim. Verify tests, reviews, approvals, revisions, and artifacts against their native authorities before recording them or making a decision.

## Resume and Coordinate Goals

Follow the pinned skill's context recovery guidance when resuming an authorized Podway workflow. Read its `references/goal.md` when a Codex goal accompanies that workflow. Context restoration or automatic continuation of the same workflow retains its established authorization and boundaries; it does not repeat activation or the entry archive advisory.

Before the next Podway action after restoration, observe the authorized owning worktree and compare its workspace UUID and session ID with the recorded workflow identities. Stop session mutations on an identity mismatch unless existing authorization covers it. Within the same authorized session, use the current attempt and revisions without renewed activation. Recover an uncertain submitted mutation with its original canonical request and idempotency key before issuing another mutation.

Keep notes focused on the objective, scope, decisions, unresolved dependencies, evidence locations, and identity or request-recovery information. Historical observations are lookup hints, not current mutation templates. Context loss alone does not invalidate external checks whose target and relevant inputs still match and whose reuse the Procedure permits; preserve required readback and freshness checks.

A terminal session, null guidance, or an `achieved` assessment does not independently prove the Codex objective complete. Verify the actual requirements and external results, and continue any remaining authorized work. A Podway blocker does not automatically block a Codex goal: follow the current Codex tool contract, including any recurrence threshold, and continue useful independent work. Never change Podway lifecycle state to synchronize goal statuses.

## Read and Mutate Safely

Use `podway observe --json`; never parse human output. Require Output v4, observation-result v5, status/compact-status v5 and Error v2. The observation is one authoritative snapshot: read identities and lifecycle from `status`, current guidance and allowed actions from `guidance`, bounded item declarations from `active_items`, and fenced requests from `mutation_templates`. Add semantic values only after reading command help and verifying their authority. `podway version --json` retains its compact result; `--identity` supplies the complete writer identity. Native `--timeout` bounds admission waits, not execution time.

Require prepared start or replacement to return `podway.session-start-result/v4`, begin to return `podway.session-begin-result/v2`, terminal disposition to return `podway.terminal-disposition-result/v2`, and reset to return `podway.session-reset-result/v2`. A successful envelope with another result schema is not proof of the requested mutation; stop and reconcile rather than advancing.

A fresh `start` or approved replacement creates a prepared revision-0 session with no attempt, cursor, goal, or active items. Re-observe it, require prepared guidance and the current `session.begin` mutation template, then use fresh workspace, session, and revision fences plus a distinct idempotency key to create attempt 1 and the initial goal, criteria, and actor. Do not record evidence or issue any item, goal, cursor, decision, rework, completion, or cancellation mutation before `begin` succeeds. A matching prepared session is recoverable workflow state: resume with `begin` only when its Procedure, canonical identity, and recoverable approval all match.

Running guidance carries the ordinary workflow actions. Terminal observation has null guidance and no active items; an undisposed terminal revision offers only terminal disposition, while a disposed terminal revision offers eligible reset and replacement. Never infer mutation authority from null guidance alone.

Before every mutation, re-observe and pass every applicable workspace, session, session-revision, attempt, goal-revision, and item-revision fence plus a deterministic operation-specific idempotency key. Select only commands present in the latest `mutation_templates`, fill semantic placeholders only from verified work, and use only IDs from machine fields such as `allowed_option_ids` and `allowed_manual_rework_targets`. Use `podway help <route>` rather than inventing flags.

After every successful mutation, re-observe rather than calculating revisions locally. On a precondition failure, re-observe and derive the next action again. On `MUTATION_OUTCOME_UNKNOWN`, use `podway --json outcome lookup --idempotency-key <key>`, require `podway.outcome-lookup-result/v1`, and reconcile the retained successful outcome and current state before considering exact replay. Only successful mutations retain outcomes; a miss outside retention does not disprove a historical effect. Replay preserves the original canonical request, key and fences.

Observation readback previews are bounded metadata, not complete recorded values. When a decision needs a selected full value, use the observation's evidence source and digest with `podway --json evidence read --source <source> --item <item>`, follow each `next_page_token` until the result is no longer truncated, and verify stable identity and value digest across pages. On `EVIDENCE_PAGE_TOKEN_STALE`, re-observe and restart at page one rather than mixing snapshots.

Record bounded summaries and references, not source contents, credentials, raw provider payloads, or full logs. For checks record the exact command, actor provenance, exit status, current source revision or dirty-tree identity, and a digest or stable evidence reference. For review record the ordinal and mode, exact target and run identity, coverage and publication status, findings-query status, reported severity, effective priority, validity, disposition, unresolved valid findings, findings that still need confirmation, whether prior review predates changed bytes, and any deferred run and finding identities.

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

## Finalize Before Reporting Completion

The current Aquarium caller must finish its approved Podway closeout before reporting the managed workflow complete or starting an approved successor. Final closeout is relative to the current session: its accepted terminal Action result, including a member Task or `pre-validation-remediation` Goal, must be finalized even when the enclosing Epic still requires validation. When `$aquarium:task-close` or `$aquarium:task-commit` returns that result, continue from it. A roadmap completion, commit SHA, achieved assessment, or terminal graph node does not prove that the session is `completed`.

A commit is intermediate only when required work remains inside the same session, such as correction groups within an active Validation session. Continue that work and keep the session running. The caller states this session-relative continuation in its commit handoff; the leaf returns it with the verified commit result.

1. Verify the exact accepted result, required checks and goal assessment, roadmap state when applicable, any required post-hook commit, and remaining worktree state. A permitted closeout without commit retains its approved uncommitted diff; do not demand a clean tree or invent a commit for that path. A missing required result remains a closeout gap.
2. Observe the same authorized workspace and session with fresh fences. Record the verified result in the remaining closeout items and complete the terminal Action through its current mutation template. Follow any unfinished graph prerequisites under existing authority; do not skip approval, assessment, or required evidence to reach the terminal node.
3. Re-observe and verify that the same session's lifecycle is `completed` with the expected assessed outcome. Reaching a terminal node or filling its items leaves this check pending until the terminal Action has actually completed.
4. Apply [terminal disposition](#record-terminal-disposition-conservatively) from the verified result, then re-observe the same session to verify any recorded `handed_off` or `not_required` disposition. When neither is supported, preserve the completed session undisposed and report the concrete reason and remaining handoff. An allowed no-commit path does not justify `not_required` merely because it has no commit SHA.
5. Report these finalization fields: session ID and revision, observed lifecycle, disposition or undisposed reason, final commit or approved no-commit/no-change result, and remaining finalization work. Finalization is verified when the same session is observed `completed` and either its supported, approved disposition is verified or the concrete reason no disposition is supported is reported. A failed or uncertain supported disposition leaves finalization pending. Report workflow completion only after these postconditions hold, and preserve the final session and its history under the native contract.

If a commit succeeds but session completion or disposition fails or is uncertain, report the verified commit separately from incomplete Podway finalization. Reconcile any uncertain submitted mutation through [Read and Mutate Safely](#read-and-mutate-safely) using its original request, key and fences before deriving a new mutation from a fresh observation. Preserve the commit SHA and resume the same session from the first unproven step in the numbered procedure above. After context restoration, re-verify an existing accepted final result and resume these steps instead of repeating `$aquarium:task-close` or `$aquarium:task-commit` whose result is already proven. Do not repeat the commit, replace the session, reopen completed work, or rerun valid checks merely to recover finalization. Completion and disposition already disclosed and approved in the workflow envelope need no additional approval. If the user explicitly limits the continuation to a commit, return that result with finalization pending; do not perform the withheld lifecycle actions.

Reuse acceptance after context restoration only when its actual decision, authority and exact candidate binding remain recoverable. A commit SHA or workflow attribution alone does not prove the user's closeout answers or delegated acceptance. If that proof is unavailable, preserve the existing result and session, report the acceptance gap, and obtain the required decision before recording approval or advancing an acceptance-dependent action. This does not authorize another commit.

## Record Terminal Disposition Conservatively

Treat terminal disposition as a caller assertion about the result outside the session, not as workflow success, evidence publication, or a durable Aquarium record. It does not create a roadmap edit, commit, push, or agent handoff. Record one only after re-observing the exact completed or cancelled revision and verifying the asserted semantics against native authority.

- Use `handed_off` only when an exact authoritative external result already exists. For a roadmap task, re-read its successful lifecycle, required evidence, clean task-owned residue, and actual commit, then use a bounded summary plus a stable reference containing the exact commit SHA. The presence of a roadmap entry without that completed external result is insufficient.
- Use `not_required` only when no final external handoff or repository result is required and current roadmap, Git, review, and worktree evidence has been re-read. This covers a disclosed internal epic boundary, an epic closeout with no final repository diff, an approved war-room no-work outcome with verified no-change, and an achieved validation run whose lifecycle, current requirements, accepted risks, and actionable handoffs require no final repository result. Earlier task or remediation commits do not prevent this disposition; record them as verified predecessors and record the concrete no-final-result reason. Never use `not_required` merely because no handoff reference is available.
- Otherwise leave the terminal revision undisposed. Do not invent a reference or reason, and never choose force reset or force replacement automatically. A final session may remain terminal after `handed_off` or remain undisposed when no disposition is supported.

After a fresh supported disposition, re-observe and use only the eligible reset or `session.start_replace` template exposed for that exact revision. When an approved successor workflow needs the worktree slot, execute the current plain `start` template so Podway atomically archives the disposed predecessor and creates the prepared successor; then re-observe and `begin` it. Prepared and running sessions follow the current start policy and are preserved unless an explicit `--on-existing delete` choice is authorized. Inspect inactive history through `archive list` (`podway.session-archive-list-result/v2`) and `archive show`. The list reports an exact count, a newest-first window, and the oldest summary. Purge only through separately authorized `archive purge`; never auto-purge or evict history. A standalone task, validation, design, war-room, or final epic session is not reset merely because it is terminal.

## Handle In-Progress Stop Requests

When the user asks to stop after the first managed-session mutation, stop Aquarium work and clarify the intended disposition from the choices below. Do not interpret an unqualified stop request as permission to cancel or reset, and do not use `podway block` for an ordinary pause.

- **Resume later:** Leave the session active without a Podway mutation. Report its identity, lifecycle and revision, current node and attempt when present, recorded progress, queue state, and the exact continuation request. A later Aquarium invocation may resume it; only a request that needs a different Podway session triggers the explicit existing-session choice above.
- **Abandon and preserve history:** Explain that `cancel` ends the task rather than pausing it and that a cancelled session never reactivates. Reference `$use-podway`, observe and summarize the exact current session, obtain explicit authorization to cancel that session, use only the fresh supported mutation template, then re-observe and report the terminal state.
- **Delete the session:** Explain that `reset` irreversibly deletes session-scoped history while preserving workspace initialization. Follow `$use-podway`'s current-session discard flow: observe and summarize the exact session, preview the fenced reset with `--dry-run`, show its `none`, `record_disposition`, or `force` requirement and the history loss, obtain every required semantic value, then obtain separate explicit authorization, re-observe, execute the fresh fenced eligible or explicitly confirmed force reset, and verify `SESSION_NOT_FOUND`. Do not cancel first when deletion or freeing the session slot is the goal.

Keep Podway lifecycle, the roadmap, Git, and the Codex goal separate. None of these dispositions commits work, changes roadmap state, or proves the goal achieved. If the user wants remaining Aquarium work to continue without Podway, finish the selected disposition and start a new explicitly opted-out workflow; never switch the current workflow in place.

For sequential epic delivery, use one `aquarium-goal-v2` session per member task, pre-validation remediation, or closeout goal. Once `aquarium-validation-v2` starts, record its audit-owned remediation and re-audit inside that session because a worktree cannot host a nested goal session.

For an ordinary successor, replace an Aquarium session only after it is successfully terminal, its authoritative artifacts, roadmap state, evidence, required commit, and worktree have been re-read, and the exact terminal revision has a supported disposition. The approved successor envelope may authorize that exact eligible replacement. A Procedure update never migrates an active snapshot and applies only to a later session. The sole running-session topology exception is the [explicitly consented atomic supersede](adaptive-execution.md#consented-atomic-supersede): qualify and retain the successor first, disclose the exact old/new identities and effects, obtain actual replacement consent, then use released fenced `start --on-existing preserve --supersede-reason`. Running observations need not advertise a start-replace template; native preview and the supported released grammar supply its source/command contract. Preserve the exact request/key for unknown-outcome lookup and verify archived superseded lineage before the separately authorized begin. No cancel/start or deletion substitute is permitted.

## Map the Managed Procedures

Read [Procedure Node Contracts](procedure-node-contracts.md) for the concise
capability, input, prohibited-effect, return-evidence, rework, and resume contract
used by action instructions and handler compatibility inspection.

- `aquarium-task-v2` supports the `task-handler` lifecycle; its nodes correspond to the approved plan, implementation, refinement, typed verification record and guarded decision, documentation, selected-route review record and decision, goal assessment, the assessed outcome with its follow-up commitments, final user approval, and closeout. Its plan record has an optional `plan-handoff-artifact` item that an explicit task plan handoff fills.
- `aquarium-goal-v2` supports one `epic-handler` member-task, pre-validation remediation, or closeout goal outside an active validation session. It records and selects any hardening-deferral evidence before the guarded evidence decision, then records the adopted handoff separately. Its work record has an optional `plan-handoff-artifact` item propagated only for an explicit epic plan handoff. The epic closeout goal therefore starts only after the validation session is successfully terminal, has a supported disposition, and is atomically replaced with the prepared closeout session. Only that final closeout may select `closeout-not-required` and omit a new review ordinal and run ID; its evidence binds the successful validation session and focused closeout checks instead.
- `aquarium-validation-v2` supports final epic audit, cold validation, and convergence. Its baseline record has an optional `plan-handoff-artifact` item for continuity from `epic-handler`; `epic-validator` leaves it absent and exposes no plan-handoff mode. Typed audit and review results guard operational routing, and every remediation reaches a fresh re-audit decision before final review. Each remediate record covers the verified remediation completed before the next audit: one goal for `epic-handler`, the full confirmed-gap group set for `epic-validator`.
- `aquarium-design-v2` supports `new-project`, `new-feature`, and `refactor` for one Git-backed design-document lifecycle. It records bounded context, discovery, draft, challenge, guarded phase-owner quality, explicit approval, application, assessment, and closeout. Ouroboros discovery and QA are leaf evidence; Aquarium retains repository authority.
- `aquarium-war-room-v2` supports `war-room`; it records baseline or reproduction, investigation, unguarded cause and scope judgments, guarded proposal quality, explicit approval, documentation, assessment, and closeout. It ends with an approved task, epic, incomplete-investigation document, or evidence-backed no-work outcome, including verified no-change. Every branch passes quality and approval; none records a fix implementation.

The caller records a leaf report only after independently checking the leaf postcondition. A failed check stays on its failure route. Valid findings follow the shared finding-disposition contract: current Task, Goal and Validation snapshots classify eligible local corrections before provider-rework authority, while corrections requiring further independent judgment use the authorized rework and review path. A completed local settlement may advance with its exact required checks and an explicit record that the preceding review predates changed bytes. Epic-handler's second-review member-task deferral remains limited to small independent Low future risks with a canonical deferred-feedback owner. Confirmation-only corrections need user direction only for uncovered effects or a necessary provider assessment with no remaining grant. Local settlement preserves the source review and supplies separate current evidence; deferral does not create clean review evidence. A final Podway `achieved` outcome cannot make a non-successful roadmap task successful, replace required approval, create a commit, or establish publication.

### Epic acceptance provenance

Goal v25 and Validation v24 distinguish `user` acceptance from
`epic-delegation`. The handler records the authority reference and exact candidate before committing. Member Tasks, pre-validation corrections, and the
continuing Epic's internal validation use delegated closeout; final Epic closeout
and independently invoked cold validation require actual user acceptance.
Setup preserves prior Goal and Validation source bytes but reports them as incompatible
with the current handler contract until an authorized managed-file update. Existing
sessions keep their admitted Procedure snapshot. An older user-only gate
cannot be recorded as delegated acceptance. Resume its original contract only with
recoverable authority; otherwise report the precise legacy gate and required
continuation without resetting or replacing active work.
