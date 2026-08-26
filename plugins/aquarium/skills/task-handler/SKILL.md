---
name: task-handler
description: "Strengthen or resume the procedure around exactly one named roadmap task goal through planning, implementation, verification, refinement, documentation, Mulgae review, and user-approved closeout, including an explicitly requested plan handoff. Use when the user explicitly invokes $aquarium:task-handler with a repository, canonical roadmap path, and exactly one task ID; require explicit invocation and one canonical roadmap task identity."
---

# Task Handler

Strengthen execution of one roadmap task goal with focused phase skills. Own task identity, authority, goal lifetime, transitions, resumption, and final evidence. Select `execute` by default, `plan-only` for a non-mutating plan, `plan-handoff` only when another agent will continue, and `resume` for continuation. Treat "plan only" as `plan-only`; for `plan-handoff` or its resume, read [plan-handoff.md](../../references/plan-handoff.md) and follow it.

Always read [evidence-residency.md](../../references/evidence-residency.md) and [release-notes.md](../../references/release-notes.md). Use Podway by default. Exclude it only when the current user explicitly opts this task out before its managed session starts or a higher-priority instruction prohibits it. For an opted-out task, do not inspect Podway, load `$use-podway`, or read [podway-integration.md](../../references/podway-integration.md), and do not carry the opt-out into a later workflow.

Otherwise read the Podway contract, use one `aquarium-task-v2` session for this canonical task after plan approval, mirror its current goal in the Codex goal, and record each verified phase handoff at the matching node. In `plan-only`, create neither goal nor session; in `plan-handoff`, create them only after approval and stop at `implement` with the verified plan artifact. Do not let either goal mechanism or runtime evidence replace roadmap authority.

## Establish the Task Contract

Require one mutable Git repository or a working directory inside it, one canonical roadmap path inside that repository, and exactly one task ID present in that roadmap. Reject epic-level requests, multiple tasks, requests without one canonical roadmap task identity, non-Git work, and external roadmap paths. Normalize an ID only when repository instructions define the rule.

1. Resolve the Git root and read every applicable instruction file.
2. Read the roadmap entry, parent epic, linked active dossier, `docs/README.md`, role owners, required artifacts, and [design-gates.md](../../references/design-gates.md). Resolve document paths from the roadmap instead of asking the user. Treat a member task without its required active dossier as a gap and require an explicit `$aquarium:docs-setup` `adopt` retrofit first. Resolve the effective `Design Gate impact` from the task first and then its parent epic. Apply the legacy registry rule; for an enrolled registry, a missing marker is a gap.
   Stop before plan approval or implementation when the effective marker is missing or `Pending`. Resume only after an explicit `$aquarium:design-qa` run documents the marker as `Not required` or active `GATE-*` IDs.
3. Inspect branch, upstream, staged, unstaged, untracked, and conflicted state. Separate task-owned work from pre-existing work. Resolve whether Project Configuration declares one release-notes authority and record its open target or structural gap without inventing enrollment.
4. Discover repository-native build, verification, documentation synchronization, Gaori, `$use-gaori`, Mulgae, `$use-mulgae`, Sanho, `$use-sanho`, Lore guidance, and the upstream `$deslop` skill. Treat each CLI, repository configuration, project MCP, and agent skill as independent state.
   Require one valid upstream `$deslop` installation before plan approval; if it is missing, duplicated, symlinked, lacks the upstream LICENSE, or has invalid frontmatter, stop before implementation and return an exact `$aquarium:dev-setup` continuation request naming this repository, roadmap, task ID, `deslop`, and the observed installation gap. Never substitute an Aquarium-owned copy, inline reconstruction, or skipped cleanup pass.
5. Record authority already granted for mutation, staging, review, commit, amend, push, PR changes, provider use, and destructive actions.
6. Route a missing or unhealthy tooling or readiness prerequisite to an exact `$aquarium:dev-setup` continuation request. Do not classify a healthy conflicting Procedure v2 session as a setup prerequisite, and do not install or initialize tools here.
7. Honor an explicit pre-session opt-out without Podway discovery. Otherwise apply the shared contract's readiness and session checks. On degraded readiness, stop and ask the user to choose `$aquarium:dev-setup` repair or an explicit opt-out for this task.
   - A matching recoverable session becomes part of the plan. Only when starting a different session, present the existing session and obtain the shared contract's explicit preserve, lifecycle, delete, or eligible-replace choice. Never route by skill owner or describe the choice as setup repair.
   - A disposed terminal session with verified handoff evidence and a current `session.start_replace` template becomes an exact successor candidate. Disclose its fenced eligible replacement in this task's envelope and, after approval, use `start --replace-eligible` without a separate reset before re-observing and beginning the prepared task session.

In a Sanho-managed repository, record whether `$use-sanho` is available. If repository guidance requires it and it is missing or invalid, route an exact `$aquarium:dev-setup` continuation request. Otherwise keep it optional and let the document and close phases apply the repository's fallback Sanho guidance at their actual Git boundary.

When repository guidance selects Gaori for verification, record whether `$use-gaori` and the configured CLI or project MCP are available. Route a missing or invalid skill to `$aquarium:dev-setup` only when repository policy requires it; otherwise keep it optional and let the verify phase use the repository's original documented command when specialized Gaori guidance is unavailable.

Record whether `$use-mulgae`, the supported configured CLI, and the attached project MCP are available. Route a missing or invalid skill or required MCP to `$aquarium:dev-setup` only when repository policy requires that component; otherwise keep the optional integration independent and let the review phase use `$use-mulgae` when available or its bounded CLI fallback when specialized guidance is unavailable.

Repository and system instructions override this workflow. Explicit invocation authorizes task-scoped Mulgae review, the task-owned staging steps defined by `$aquarium:task-refine`, and an approved lifecycle edit; it does not authorize commit, amend, push, PR changes, destructive commands, source transmission outside the disclosed Mulgae review, or unrelated staging. An authorized commit is handed to `$aquarium:task-commit`.

Do not start or mutate Podway before plan approval. The plan discloses session start or resume, the separate fenced `begin`, evidence, decisions, rework, goal assessment, completion, and supported disposition. It also names any downstream consumer and approved `repository-required` or `external-handoff` promotion; otherwise task promotion is unavailable. `plan-only` stops without mutation. `plan-handoff` additionally discloses the temporary plan, attachment, session stop, successor propagation, resume report, and cleanup.

Approval explicitly omitting Podway approves the plan without those operations. Accept opt-out only before the first managed-session mutation. Afterward classify every stop or opt-out request through the shared `Handle In-Progress Stop Requests` flow; never assume pause, cancel, reset, or an in-place switch to non-Podway execution.

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

Immediately after plan approval and before implementation, re-read the task lifecycle vocabulary; in `plan-handoff`, defer this roadmap edit until `resume`. Preserve `In Progress` or `In Review`. For a terminal task, ask whether to reopen it through a roadmap-defined active state and stop without approval. Otherwise change it to `In Progress` only when that exact state is defined; when absent, preserve the current status. Verify this task-owned edit before loading `$aquarium:task-implement`.

## Gate Transitions

After each phase, re-read the roadmap entry, Git state, affected files, and phase evidence. A leaf skill's report is a handoff summary, not proof by itself. Continue only when these postconditions hold:

| Phase | Required postcondition |
|---|---|
| Plan | A decision-complete plan is explicitly approved; `plan-only` makes no mutation; `plan-handoff` makes no roadmap edit, records the verified artifact, stops at `implement`, and returns the exact session-bound continuation; any roadmap-defined `In Progress` transition is applied and verified only before implementation. |
| Implement | The approved behavior exists as an isolated task-owned diff and focused implementation checks have current evidence. |
| Verify | Every applicable roadmap requirement maps to current passing agent-run or explicit user-run evidence, no required check is failing or stale, and any layer recorded as not applicable carries evidence for that judgment. |
| Refine | Deslop and bounded optimization are complete; the post-deslop baseline and confirmed optimization delta follow the staged-diff contract. |
| Document | Canonical documents, the active dossier, roadmap, and release note are current; documentation validation has current evidence; accepted task information is promoted to its canonical owner; every repository handoff is actionable for a named future consumer with a clear Internal or External lifecycle; completion or runtime evidence is not duplicated as handoff prose; consumed or stale Internal entries are removed or updated. |
| Review | One exact complete task target received bounded Mulgae review and every valid finding is resolved or explicitly dispositioned. |
| Close | The user approved tests, documentation, the exact final implementation, and the terminal status; any authorized commit succeeded through `$aquarium:task-commit`. |

- Before each review, derive the ordinal from operationally complete committed root runs for the goal revision. Such a run consumes it even on `request_changes` or failing CI; preflight, reads, and internal retry or extraction do not. Use Podway verbose exact IDs when active or an exact recoverable chain after opt-out; never use `latest`, objective inference, or an uncertain candidate. A session created from an earlier version of this managed Procedure is not migrated, and an unprovable ordinal stops. Do not use `followup`, `delta`, or `rerun`.
- In rounds one through three, supply `remediation-eligible` and stop immediately on approval. Otherwise verify the hypotheses, record `changes-requested`, rework to the earliest owning phase, fix every valid in-scope finding there, rerun invalidated evidence, and review the latest complete target with the next ordinal. `$aquarium:task-review` never performs these fixes. An incomplete run stops without blind retry.
- Round four is confirmation-only, as is every user-authorized extra confirmation. Stop on approval; otherwise make no fix or review decision and ask for one additional fix-and-confirmation budget, an exact goal revision accepting the named risk, or a stop. After extra authorization, fix through the owning phase and run exactly one next-ordinal confirmation. Ask again if it still finds a valid issue. Reset the ordinal only for an explicitly approved new goal revision.
- After the final review completes, create and stage a task package only when the plan or separate approval names its consumer and purpose. Verify live native evidence, target digest, and copied projection before presenting the final diff; otherwise pass an explicit absence to closeout. Leaf phases never create a package implicitly.

Distinguish a leaf phase summary, Podway recovery evidence, and a durable repository handoff. Only the last belongs in project documentation. Reject audit logs, completion summaries, evidence collections, routine validation records, and ignored runtime references. On failure, re-enter the earliest phase that owns the requested change, rerun invalidated phases, keep the goal active, and stop:

- `$aquarium:task-implement` for a behavior change, including a rejected final approval whose correction changes behavior;
- `$aquarium:task-verify` for missing evidence;
- `$aquarium:task-document` for a documentation-only objection;
- `$aquarium:task-refine` for a cleanup-only correction.

When Podway is active:

- Immediately before each phase delegation, run `podway observe --json --wait-for-idle` and verify this task's Procedure ID, canonical identity, session, attempt, goal revision, and expected node from the observation. After the leaf returns native evidence, independently verify its postcondition, record the bounded result with current fences, and advance only through an action allowed by `guidance.allowed_actions` and represented by a current `mutation_templates` entry.
- Verification failure selects the failed route. In remediation-eligible review rounds, verified findings select rework; a rejected final approval does too. Match the correction to manual `implement` for behavior, manual `verify` for evidence or tests, automatic `refine` for cleanup, or no-op `refine` followed by `document` for documentation only. Apply every confirmation-only pause before any review decision.
- Record `changes-requested` only for an explicit correction request or a specifically unmet gate. For `Keep in review`, silence, or an ambiguous answer, record no decision and leave the session at its current node.
- Record the assessed outcome at `record-outcome` from the goal assessment plus the verification gaps, finding dispositions, and documentation gaps carried by the leaf reports, before requesting final approval.
- Request a successful terminal transition only after an `achieved` goal assessment. After `not-achieved`, re-enter the owning phase through manual rework or report the exact blocker; after `superseded`, use a goal revision with a declared rework target or stop and report the supersession. Neither outcome may select a successful roadmap state or complete the Codex goal as achieved.
- After terminal success, record `handed_off` only when the successful roadmap task, exact required commit SHA, evidence, and clean task-owned residue have all been re-read; otherwise leave the session undisposed. Never reset the final task session automatically.
- Any desired-outcome change uses a goal revision and declared rework target.

## Own Goal Lifetime

Do not create a goal before plan approval. After approval, inspect the current goal, resume it when it represents the same task, create one containing the task ID and evidence boundary when none exists, and stop rather than replace a different unfinished goal. Omit a token budget unless the user explicitly supplied one.

Keep the goal active through every phase. Mark it complete only after `$aquarium:task-close` succeeds and no required task work or authorized lifecycle action remains. Mark the goal blocked only when the host's goal tool defines a blocked state and its own repeated-blocker rule is met by the same unresolved external blocker persisting across consecutive goal turns with no authorized action remaining; otherwise keep it active and report the exact gap.

## Resume Without Shadow State

Do not create or read `.aquarium` or another orchestration state file. On continuation, reconstruct progress from the named roadmap, current Git index and worktree, goal state, repository-native documentation state, verification evidence in the conversation or repository, and Mulgae run and finding evidence.

When Podway is active, its latest `podway.observation-result/v2` envelope is also required reconstruction evidence. A matching prepared revision resumes through its fresh `session.begin` template; a running session resumes at the earliest unproven phase only when the active procedure ID, canonical task identity, goal revision, and current node agree. A recorded plan handoff also requires the exact artifact checks in the shared reference. Otherwise stop rather than repairing history by inference.

Resume at the earliest phase whose postcondition is not currently proven. Do not repeat a proven phase merely to recreate a report, but invalidate affected evidence when task-owned code, tests, documentation, roadmap state, review target, or repository authority changed after that evidence was recorded.

## Report Orchestration State

Keep progress updates concise. At every stop and final handoff, report the completed phase, next phase, task-owned paths, current roadmap status, release-note target and decision, agent-run and user-run checks, staged and unstaged state, Mulgae run and findings status, goal state, and any remaining commit or publication gap. A plan handoff must also report every session and artifact identity required by the shared reference.
