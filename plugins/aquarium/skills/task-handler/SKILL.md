---
name: task-handler
description: "Strengthen the procedure around exactly one named roadmap task goal through planning, implementation, verification, refinement, documentation, Mulgae review, and user-approved closeout. Use when the user explicitly invokes $aquarium:task-handler with a repository, canonical roadmap path, and exactly one task ID; require explicit invocation and one canonical roadmap task identity."
---

# Task Handler

Strengthen execution of one roadmap task goal by loading focused phase skills in order. Own task identity, authority, goal lifetime, phase transitions, resumption, and final evidence; leave phase-specific work to the corresponding leaf skill.

Use Podway by default. Exclude it only when the current user explicitly opts this task out before its managed session starts or a higher-priority instruction prohibits it. For an opted-out task, do not inspect Podway, load `$use-podway`, or read [podway-integration.md](../../references/podway-integration.md), and do not carry the opt-out into a later workflow.

Otherwise read the contract, own one `aquarium-task-v2` session for this canonical task after plan approval, mirror its current goal in the Codex goal, and record each verified phase handoff at the matching node. Do not let either goal mechanism replace roadmap authority.

## Establish the Task Contract

Require one repository or working directory, one canonical roadmap path inside that repository, and exactly one task ID present in that roadmap. Reject epic-level requests, multiple tasks, requests without one canonical roadmap task identity, and external roadmap paths. Normalize an ID only when repository instructions define the rule.

Before planning:

1. Resolve the Git root and read every applicable instruction file.
2. Read the roadmap entry and its linked specifications, decisions, contracts, and required artifacts.
3. Inspect branch, upstream, staged, unstaged, untracked, and conflicted state. Separate task-owned work from pre-existing work.
4. Discover repository-native build, verification, documentation synchronization, Gaori, `$use-gaori`, Mulgae, `$use-mulgae`, Sanho, `$use-sanho`, and Lore guidance. Treat each CLI, repository configuration, project MCP, and agent skill as independent state.
5. Record authority already granted for mutation, staging, review, commit, amend, push, PR changes, provider use, and destructive actions.
6. Route a missing or unhealthy prerequisite to an exact `$aquarium:dev-setup` continuation request. Do not install or initialize tools here.
7. Honor an explicit pre-session opt-out without Podway discovery. Otherwise apply the shared contract's readiness and session checks. A matching recoverable session becomes part of the plan; on degraded readiness or a session not owned by this exact task, stop and ask the user to choose `$aquarium:dev-setup` repair or an explicit opt-out for this task.

In a Sanho-managed repository, record whether `$use-sanho` is available. If repository guidance requires it and it is missing or invalid, route an exact `$aquarium:dev-setup` continuation request. Otherwise keep it optional and let the document and close phases apply the repository's fallback Sanho guidance at their actual Git boundary.

When repository guidance selects Gaori for verification, record whether `$use-gaori` and the configured CLI or project MCP are available. Route a missing or invalid skill to `$aquarium:dev-setup` only when repository policy requires it; otherwise keep it optional and let the verify phase use the repository's original documented command when specialized Gaori guidance is unavailable.

Record whether `$use-mulgae`, the supported configured CLI, and the attached project MCP are available. Route a missing or invalid skill or required MCP to `$aquarium:dev-setup` only when repository policy requires that component; otherwise keep the optional integration independent and let the review phase use `$use-mulgae` when available or its bounded CLI fallback when specialized guidance is unavailable.

Repository and system instructions override this workflow. Explicit invocation authorizes task-scoped Mulgae review, the task-owned staging steps defined by `$aquarium:task-refine`, and the approved final task-owned staging in `$aquarium:task-close`; it does not authorize commit, amend, push, PR changes, destructive commands, source transmission outside the disclosed Mulgae review, or unrelated staging.

Do not start or mutate Podway before plan approval. By default the plan discloses session start or resume, bounded evidence, decisions, rework, goal assessment, and completion. Approval explicitly omitting Podway approves the plan without those operations. Accept opt-out only before the first managed-session mutation. Afterward classify every stop or opt-out request through the shared `Handle In-Progress Stop Requests` flow; never assume pause, cancel, reset, or an in-place switch to non-Podway execution.

## Load Phase Skills in Order

Resolve every phase skill from the installed Aquarium plugin, read its complete `SKILL.md`, and follow it in this exact order:

1. `$aquarium:task-plan`
2. `$aquarium:task-implement`
3. `$aquarium:task-verify`
4. `$aquarium:task-refine`
5. `$aquarium:task-document`
6. `$aquarium:task-review`
7. `$aquarium:task-close`

Treat a missing phase skill as a broken plugin installation. Do not silently inline, reconstruct, reorder, or substitute its workflow.

## Gate Transitions

After each phase, re-read the roadmap entry, Git state, affected files, and phase evidence. A leaf skill's report is a handoff summary, not proof by itself. Continue only when these postconditions hold:

| Phase | Required postcondition |
|---|---|
| Plan | A decision-complete plan is explicitly approved; when Plan mode requires a handoff, it ends with an exact continuation prompt for that approved plan. |
| Implement | The approved behavior exists as an isolated task-owned diff and focused implementation checks have current evidence. |
| Verify | Every applicable roadmap requirement maps to current passing agent-run or explicit user-run evidence, no required check is failing or stale, and any layer recorded as not applicable carries evidence for that judgment. |
| Refine | Deslop and bounded optimization are complete; the post-deslop baseline and confirmed optimization delta follow the staged-diff contract. |
| Document | Durable documentation is current, the roadmap uses its defined review state, and applicable documentation checks have evidence. |
| Review | One exact complete task target received Mulgae review and every valid finding is resolved or explicitly dispositioned. |
| Close | The user approved tests, documentation, and the exact final implementation; the intended terminal status and any authorized commit are verified. |

If a postcondition fails, keep the goal active, preserve the latest safe repository state, report the exact gap, and do not load the next phase. Then re-enter the earliest phase that owns the requested change and re-run every later phase whose evidence that change invalidates:

- `$aquarium:task-implement` for a behavior change, including a rejected final approval whose correction changes behavior;
- `$aquarium:task-verify` for missing evidence;
- `$aquarium:task-document` for a documentation-only objection;
- `$aquarium:task-refine` for a cleanup-only correction.

When Podway is active:

- Immediately before each phase delegation, run `podway observe --json --wait-for-idle` and verify this task's Procedure ID, canonical identity, session, attempt, goal revision, and expected node from the observation. After the leaf returns native evidence, independently verify its postcondition, record the bounded result with current fences, and advance only through an action allowed by `guidance.allowed_actions` and represented by a current `mutation_templates` entry.
- Verification failure selects the procedure's failed route. Review findings, review-pass file changes, or a rejected final approval select the matching rework route even when the final re-review is clean; after recording it, match the rework depth to the correction — explicit manual rework to `implement` for a behavior change, to `verify` for evidence or test corrections, and the automatic `refine` route for cleanup-only work; for a documentation-only correction, complete `refine` with no-op evidence and advance to `document` normally.
- Record `changes-requested` only for an explicit correction request or a specifically unmet gate. For `Keep in review`, silence, or an ambiguous answer, record no decision and leave the session at its current node.
- Record the assessed outcome at `record-outcome` from the goal assessment plus the verification gaps, finding dispositions, and documentation gaps carried by the leaf reports, before requesting final approval.
- Request a successful terminal transition only after an `achieved` goal assessment. After `not-achieved`, re-enter the owning phase through manual rework or report the exact blocker; after `superseded`, use a goal revision with a declared rework target or stop and report the supersession. Neither outcome may select a successful roadmap state or complete the Codex goal as achieved.
- Any desired-outcome change uses a goal revision and declared rework target.

## Own Goal Lifetime

Do not create a goal before plan approval. After approval, inspect the current goal, resume it when it represents the same task, create one containing the task ID and evidence boundary when none exists, and stop rather than replace a different unfinished goal. Omit a token budget unless the user explicitly supplied one.

Keep the goal active through every phase. Mark it complete only after `$aquarium:task-close` succeeds and no required task work or authorized lifecycle action remains. Mark the goal blocked only when the host's goal tool defines a blocked state and its own repeated-blocker rule is met by the same unresolved external blocker persisting across consecutive goal turns with no authorized action remaining; otherwise keep it active and report the exact gap.

## Resume Without Shadow State

Do not create or read `.aquarium` or another orchestration state file. On continuation, reconstruct progress from the named roadmap, current Git index and worktree, goal state, repository-native documentation state, verification evidence in the conversation or repository, and Mulgae run and finding evidence.

When Podway is active, its latest `podway.observation-result/v1` envelope is also required reconstruction evidence. Resume at the earliest unproven phase only when the active procedure ID, canonical task identity, goal revision, and current node agree; otherwise stop rather than repairing history by inference.

Resume at the earliest phase whose postcondition is not currently proven. Do not repeat a proven phase merely to recreate a report, but invalidate affected evidence when task-owned code, tests, documentation, roadmap state, review target, or repository authority changed after that evidence was recorded.

## Report Orchestration State

Keep progress updates concise. At every stop and final handoff, report the completed phase, next phase, task-owned paths, current roadmap status, agent-run and user-run checks, staged and unstaged state, Mulgae run and findings status, goal state, and any remaining commit or publication gap.
