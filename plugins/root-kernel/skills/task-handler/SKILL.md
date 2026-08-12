---
name: task-handler
description: "Strengthen the procedure around exactly one named roadmap task goal through planning, implementation, verification, refinement, documentation, Mulgae review, and user-approved closeout. Use when the user explicitly invokes $root-kernel:task-handler with a repository, canonical roadmap path, and exactly one task ID; require explicit invocation and one canonical roadmap task identity."
---

# Task Handler

Strengthen execution of one roadmap task goal by loading focused phase skills in order. Own task identity, authority, goal lifetime, phase transitions, resumption, and final evidence; leave phase-specific work to the corresponding leaf skill.

## Establish the Task Contract

Require one repository or working directory, one canonical roadmap path inside that repository, and exactly one task ID present in that roadmap. Reject epic-level requests, multiple tasks, requests without one canonical roadmap task identity, and external roadmap paths. Normalize an ID only when repository instructions define the rule.

Before planning:

1. Resolve the Git root and read every applicable instruction file.
2. Read the roadmap entry and its linked specifications, decisions, contracts, and required artifacts.
3. Inspect branch, upstream, staged, unstaged, untracked, and conflicted state. Separate task-owned work from pre-existing work.
4. Discover repository-native build, verification, documentation synchronization, Gaori, Mulgae, Sanho, and Lore guidance.
5. Record authority already granted for mutation, staging, review, commit, amend, push, PR changes, provider use, and destructive actions.
6. Route a missing or unhealthy prerequisite to an exact `$root-kernel:dev-setup` continuation request. Do not install or initialize tools here.

Repository and system instructions override this workflow. Explicit invocation authorizes task-scoped Mulgae review and the task-owned staging steps defined by `$root-kernel:task-refine`; it does not authorize commit, amend, push, PR changes, destructive commands, source transmission outside the disclosed Mulgae review, or unrelated staging.

## Load Phase Skills in Order

Resolve every phase skill from the installed Root Kernel plugin, read its complete `SKILL.md`, and follow it in this exact order:

1. `$root-kernel:task-plan`
2. `$root-kernel:task-implement`
3. `$root-kernel:task-verify`
4. `$root-kernel:task-refine`
5. `$root-kernel:task-document`
6. `$root-kernel:task-review`
7. `$root-kernel:task-close`

Treat a missing phase skill as a broken plugin installation. Do not silently inline, reconstruct, reorder, or substitute its workflow.

## Gate Transitions

After each phase, re-read the roadmap entry, Git state, affected files, and phase evidence. A leaf skill's report is a handoff summary, not proof by itself. Continue only when these postconditions hold:

| Phase | Required postcondition |
|---|---|
| Plan | A decision-complete plan is explicitly approved; when Plan mode requires a handoff, it ends with an exact continuation prompt for that approved plan. |
| Implement | The approved behavior exists as an isolated task-owned diff and focused implementation checks have current evidence. |
| Verify | Every applicable roadmap requirement maps to current agent-run or explicit user-run evidence, with gaps reported. |
| Refine | Deslop and bounded optimization are complete; the post-deslop baseline and confirmed optimization delta follow the staged-diff contract. |
| Document | Durable documentation is current, the roadmap uses its defined review state, and applicable documentation checks have evidence. |
| Review | One exact complete task target received Mulgae review and every valid finding is resolved or explicitly dispositioned. |
| Close | The user approved tests, documentation, and the exact final implementation; the intended terminal status and any authorized commit are verified. |

If a postcondition fails, keep the goal active, preserve the latest safe repository state, report the exact gap, and do not load the next phase.

## Own Goal Lifetime

Do not create a goal before plan approval. After approval, inspect the current goal, resume it when it represents the same task, create one containing the task ID and evidence boundary when none exists, and stop rather than replace a different unfinished goal. Omit a token budget unless the user explicitly supplied one.

Keep the goal active through every phase. Mark it complete only after `$root-kernel:task-close` succeeds and no required task work or authorized lifecycle action remains. Mark it blocked only under the goal tool's repeated-blocker rule.

## Resume Without Shadow State

Do not create or read `.root-kernel-dev-skills` or another orchestration state file. On continuation, reconstruct progress from the named roadmap, current Git index and worktree, goal state, repository-native documentation state, verification evidence in the conversation or repository, and Mulgae run and finding evidence.

Resume at the earliest phase whose postcondition is not currently proven. Do not repeat a proven phase merely to recreate a report, but invalidate affected evidence when task-owned code, tests, documentation, roadmap state, review target, or repository authority changed after that evidence was recorded.

## Report Orchestration State

Keep progress updates concise. At every stop and final handoff, report the completed phase, next phase, task-owned paths, current roadmap status, agent-run and user-run checks, staged and unstaged state, Mulgae run and findings status, goal state, and any remaining commit or publication gap.
