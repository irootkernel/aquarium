# Workflow Contracts

Aquarium organizes work into shaping, delivery, validation, setup, and release lifecycles. The roadmap owns adopted work and status; every runtime workflow is a bounded projection of that authority.

## Shape Work

`new-project`, `new-feature`, `refactor`, and `war-room` use the shared Ouroboros integration contract and an exact-diff approval boundary. They capture current authority before provider work, treat provider output as draft evidence, route typed quality findings through fresh phase-owned rework, and apply repository documents only after the user approves the complete diff. Podway guards operational quality results, not design truth, diagnostic cause or scope, or user approval.

Git-backed shape workflows use `aquarium-design-v2`, except `war-room`, which uses `aquarium-war-room-v2`. Non-Git discovery remains Podway-free because no repository lifecycle exists to record.

## Deliver One Task

| Phase | Owning skill | Required result before transition |
| --- | --- | --- |
| Plan | `task-plan` | Decision-complete approved plan bound to one roadmap task |
| Implement | `task-implement` | Complete task-owned behavior and regression coverage |
| Refine | `task-refine` | Verified task diff cleaned without changing approved behavior |
| Verify | `task-verify` | Requirement-to-test matrix and current authorized check evidence for the refined target |
| Document | `task-document` | Current durable documentation, handoff, and release-note decision |
| Review | `task-review` | Complete target publication, successful findings query, and local adjudication |
| Close | `task-close` | Explicit terminal status and optional exact commit handoff |

`task-handler` owns phase ordering and postconditions. A code, test, canonical-documentation, or product-artifact change after verification or review makes the affected evidence stale, except for the explicitly allowed status-only roadmap transition and independently checked promoted-evidence projection.

With Podway selected, the handler creates or resumes one `aquarium-task-v2` session only after plan approval, begins the prepared session through its fenced mutation, mirrors the active goal in Codex, and records independently checked phase handoffs. Plan-only mode creates no runtime state; plan-handoff mode attaches one private session-bound artifact and stops before implementation.

An operationally complete task review records `ci-decision` separately from its finding counts. CI failure uses `ci-failed`, records an explicit failure handoff, and then returns to implementation; after CI passes, implementation or refinement findings use `implementation-changes`, documentation-only findings use `documentation-changes`, and only a clean review may use `approved`. Incomplete review capture records no decision.

## Deliver One Epic

`epic-handler` builds a dependency DAG from the canonical roadmap, resolves pre-epic and external prerequisites by exact revision, orders member tasks by dependency and roadmap order, and completes one isolated task commit at a time.

Each member task uses one `aquarium-goal-v2` session and records any durable hardening deferral before deciding whether that evidence supports the task. After all member tasks are terminal, the handler replaces the disposed final task session with `aquarium-validation-v2`, audits the latest committed epic from scratch, remediates gaps by canonical owner, re-audits the changed candidate, and repeats within the bounded review budget.

Task-owned gaps reopen the owning task when the roadmap defines that path. Cross-task seam gaps use the epic identity. External gaps stop with the other repository owner, exact required revision, and missing evidence; Aquarium never edits another repository merely to close its own epic.

## Cold-Validate a Completed Epic

`epic-validator` reconstructs a completed epic from roadmap, Git, current tests, canonical documentation, and independently verifiable evidence. It runs a direct audit, groups confirmed gaps by owner, implements bounded remediation, and performs one automatic confirmation path.

A new confirmation finding stops for user direction rather than entering an unbounded loop. A zero-finding audit creates no validation-record commit, and accepted runtime evidence never becomes roadmap history by default.

## Review Targets

The shared review contract accepts staged changes, `HEAD`, one commit, a two-dot or three-dot range, one roadmap task or epic resolved to Git, or an explicitly scoped special investigation. Dirty working-tree content is never silently added to a committed target.

Independent review uses one fresh Codex. Orca review uses one selected supported provider under supervised Run and Task state. Both are static, run no tests or builds, and return findings for local verification rather than automatic remediation.

## Set Up a Repository

`dev-setup`, `docs-setup`, and `test-setup` begin with conservative read-only inspection. They classify current state, present exact proposed changes, snapshot affected targets, and apply only the approved diff or action before rerunning the inspector and repository-native checks.

`dev-setup-bundle` accepts one external `aquarium.dev-setup-bundle/v1` manifest, normalizes defaults and explicit target selection, confirms the resulting plan, prepares shared components once, and invokes single-repository setup in manifest order. It does not discover repositories or persist bundle state.

## Release a Stable Version

`release-handler` establishes the intended version, clean main candidate, previous release, publication state, and repository release policy. It reconciles every material delta with cumulative release notes before delegating one exact candidate to `release-qa`.

Full release mode runs the complete repository gate after metadata changes. Light mode requires explicit prior test confirmation for the exact candidate and permits only release metadata changes. A functional change invalidates light-mode confirmation and requires new confirmation or full mode.

After QA, the handler normally verifies an unchanged candidate and unchanged entry text. A failed full gate may use bounded public-checkpoint suffixes for diagnosis, but each cycle settles at most one correction commit and release readiness still requires one uninterrupted final aggregate from the beginning. QA-affecting corrections require a new authorized full release QA; the sole reuse exception is one approved QA-neutral direct child whose direct-QA and release-basis SHAs remain distinct.

Release-QA workers emit versioned cluster results. A full pass freezes their complete commit, changed-surface, cluster, scenario, finding, and evidence inventory before remediation. Confirmation preparation derives the exact non-empty remediation range and coverage from Git, admission atomically claims the one permitted attempt by frozen-record digest, and finish validation rejects missing, extra, reassigned, stale, out-of-root, or source-mutating evidence. These private records under `/tmp` are workflow authority for the bounded pass, not tracked repository documentation.

The handler then creates the repository-authorized release commit, pushes main, creates and pushes an annotated tag, publishes the hosted Release, and verifies all three remote identities. Opening the next Unreleased cycle remains a separate post-release action.

## Pause, Resume, and Hand Off

Aquarium never creates a shadow orchestration file. Routine continuation reconstructs state from roadmap, Git, worktree, current goal, canonical documents, and native tool evidence.

An explicit plan handoff is the sole temporary artifact exception. It is private, untracked, content-addressed, bound to one session and goal revision, reverified before use, and deleted after the owning workflow no longer needs it.
