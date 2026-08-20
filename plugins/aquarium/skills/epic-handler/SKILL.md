---
name: epic-handler
description: "Deliver one named roadmap epic through sequential goal-centered task execution, evidence-gated commits, and repeated epic-wide remediation. Use when the user explicitly invokes $aquarium:epic-handler with a repository, canonical roadmap path, and exactly one epic ID and wants epic-level goal orchestration without the procedure-strengthening $aquarium:task-handler workflow; do not invoke it implicitly."
---

# Epic Handler

Deliver one roadmap epic as a sequence of goal-centered task executions. Own the outcome, ordering, evidence, and commit boundaries without prescribing one implementation procedure. Do not invoke `$aquarium:task-handler` or its phase skills; they separately strengthen the procedure around one user-guided task goal.

Use Podway by default. Exclude it only when the current user explicitly opts this epic out before its first managed session starts or a higher-priority instruction prohibits it. For an opted-out epic, do not inspect Podway, load `$use-podway`, or read [podway-integration.md](../../references/podway-integration.md), and do not carry the opt-out into a later workflow.

Otherwise read the contract and own one `aquarium-goal-v2` session per member-task, pre-validation remediation, or closeout goal and one `aquarium-validation-v2` session for the final epic audit and its audit-owned remediation. Podway strengthens durable execution memory but does not prescribe a phase workflow or replace the roadmap DAG.

## Establish and Approve the Epic

Require one mutable Git repository, one canonical roadmap path inside that repository, and exactly one epic ID present in that roadmap. Reject task-only requests, multiple epics, requests without one canonical roadmap epic identity, and external roadmap authorities. Inspect another repository read-only only when the roadmap explicitly names it; never mutate or create a goal for it.

Read [design-gates.md](../../references/design-gates.md). Resolve every member task's effective `Design Gate impact` from the task first and then the epic before plan approval. Apply the documented legacy-only `Not required` rule when neither marker exists; in an enrolled repository, a missing effective marker is a contract gap.

Stop before plan approval or implementation when any selected work is missing or `Pending`, and require an explicit `$aquarium:design-qa` run to document it. Carry every resolved active `GATE-*` ID into the plan, task checks, and final seam audit.

Before requesting approval:

1. Read repository instructions, the epic, every member task, linked authority, required artifacts, and explicit dependencies.
2. Inspect branch, upstream, HEAD, staged, unstaged, untracked, and conflicted state. Separate epic-owned work from existing work and record the starting revision.
3. Discover repository-native verification, Gaori, `$use-gaori`, documentation synchronization, Mulgae, `$use-mulgae`, Sanho, `$use-sanho`, lifecycle, and commit guidance. Treat each CLI, repository configuration, project MCP, and agent skill as independent state.
4. Build a dependency DAG. Distinguish member-task edges from pre-epic local or explicit external prerequisites. For every prerequisite record repository, canonical ID, exact revision, lifecycle state, dirty state, evidence, and owner. An incomplete member-task predecessor determines execution order and does not block initial approval. A pre-epic or external prerequisite is satisfied only by committed work at the required revision with verified evidence; if unmet, stop before goal creation or mutation and report the owner and required sequence.
5. Order tasks by dependencies and then roadmap order. Split a cycle only when authority defines pre-validation and finalization; otherwise stop and report its nodes, owners, and missing authority.
6. Preserve successfully terminal tasks, start at the earliest non-terminal task, and retain every task for the final audit. Stop rather than replace a different active goal.
7. Honor an explicit pre-session opt-out without Podway discovery. Otherwise apply the shared contract's readiness and session checks. On degraded readiness, stop and ask the user to choose `$aquarium:dev-setup` repair or an explicit opt-out for this epic.
   A matching recoverable Aquarium session becomes part of the plan. For any healthy conflicting session, use the shared lifecycle-conflict route: resume it through its matching owner, leave it untouched through epic opt-out, or hand its cancellation or discard to an explicit `$use-podway` request. Never describe that conflict as setup repair.

Produce one concise, decision-complete epic plan: goal and non-goals, dependency DAG, exact task order, requirement owners, expected task outcomes and commit boundaries, relevant checks, Mulgae targets, lifecycle changes, external handoffs, and known authority or environment gaps. Avoid prescribing phase order, file-by-file mechanics, or a full task implementation design unless the authority makes them necessary.

Ask once for explicit approval of the plan and execution envelope. Approval covers bounded implementation decisions, repository-authorized checks, disclosed Mulgae transmission, task and epic staging, one task-ID commit per task, and necessary remediation or closeout commits. It does not authorize amend, push, PR or release changes, live rollout, destructive actions, installation, another repository, or unrelated staging. Commit and upstream publication are separate states.

By default the envelope must cover creating or resuming each prepared managed session, the separate fenced `begin`, recording bounded evidence and decisions, goal revision and rework required by in-scope changes, terminal completion, supported terminal disposition, and eligible replacement only after the authoritative roadmap, commit, review, and worktree evidence has been re-read. Treat approval that explicitly omits Podway as approval of the same envelope without those operations.

Accept an opt-out only before the first managed-session mutation. Afterward classify every stop or opt-out request through the shared `Handle In-Progress Stop Requests` flow; never assume pause, cancel, reset, or an in-place switch to non-Podway execution. Never mutate a conflicting session automatically.

Do not create a goal, edit files, invoke providers, stage, commit, or alter external state before approval. Request renewed approval only when requirements, task membership or order, repository scope, product behavior, destructive impact, external actions, or safe diff isolation materially departs from the envelope.

When a selected long or noisy check is routed through Gaori, reference `$use-gaori` and follow it when available. If it is missing and repository policy requires it, stop and route to `$aquarium:dev-setup`; otherwise run the repository's original documented command directly and report that evidence compression was unavailable. Never infer an unknown original command, and keep command result, extraction quality, and acceptance authority separate.

Before each authorized Mulgae review, reference `$use-mulgae` and follow it when available, preferring its attached MCP workflow. If the skill or project MCP is unavailable and repository policy requires it, stop and route that exact gap to `$aquarium:dev-setup`; otherwise use the supported configured CLI fallback, report the unavailable integration once, and preserve exact preflight, run, publication, and findings evidence. Never start a second MCP server or blindly retry an uncertain review mutation.

## Complete Task Goals

For each non-terminal task in order:

1. Reconfirm every member-task predecessor is successfully terminal with its required commit and evidence, and recheck any pre-epic or external prerequisite at its exact revision. Stop on a gap; otherwise create or resume exactly one goal containing the task ID and required outcome. Omit a token budget unless the user supplied one.
2. Work from current authority and code toward the task goal. Choose the implementation, investigation, documentation, and verification sequence that best fits the repository and task; do not manufacture phase artifacts or pause for routine choices already inside the approved envelope.
3. Implement the complete task outcome, including runtime wiring, tests, generated or derived artifacts, durable documentation, and roadmap state that the authority requires. Preserve unrelated work.
4. Run proportionate repository-authorized checks. Focused green checks prove only mapped requirements; forbidden or unavailable database, E2E, live, or broad gates remain explicit evidence gaps and are never run merely because another workflow normally would.
5. Run Mulgae at least once on the latest complete task target, including task-owned staged, unstaged, untracked, generated, and derived files. Verify findings as hypotheses, fix every valid in-scope issue, rerun affected checks, and review the changed target again until no valid finding remains.
6. Treat Mulgae as complete only when `coverage_status=complete`, `ci_decision=pass`, `publication_status=committed`, the findings query succeeds, and zero unresolved valid findings remain. Provider success or exit status alone is insufficient.
   Record `structured_extraction_status` independently as `structured`, `mixed`, or `reports_only`. `reports_only` is not itself a failure and does not replace or relax any completion condition above; the accepted reports remain authoritative, and every extracted finding remains an advisory hypothesis that requires local verification.
7. Move the task to its defined successful state and hand the exact isolated task-owned diff, lifecycle evidence, task ID, and approved commit authority to `$aquarium:task-commit`. Complete the goal only after its commit exists, no task-owned residue remains, and unrelated work is unchanged; then re-read roadmap, DAG, Git state, and evidence before advancing.

With Podway active, run `podway observe --json --wait-for-idle` before each bounded work delegation and verify the expected Procedure ID, canonical goal identity, session, lifecycle, revision, and, when running, its attempt, goal revision, and current node.

Start or resume the matching prepared goal procedure only after approval, re-observe and `begin` it before work, mirror its goal in the Codex goal, and independently verify returned native evidence before recording it. Only then select decisions and assess criteria through actions allowed by `guidance.allowed_actions` and represented by current `mutation_templates` entries.

After step 7, complete the Podway session, verify its terminal outcome, and repeat the handoff checks. Record `handed_off` with the exact task commit SHA. When another member task remains, use the fresh eligible replacement template to atomically create its prepared session and re-observe before `begin`; after the final member task, leave the disposed terminal session for the audit transition below. Never replace a failed, non-terminal, undisposed, or insufficiently evidenced session.

Use a fresh read-only subagent for an independent perspective when task risk or uncertainty merits it; do not substitute that review for Mulgae, do not invoke `$aquarium:independent-review`, which only the user starts, and do not let it impose the `$aquarium:task-handler` phase workflow.

Keep implementation snapshot, verification snapshot, Mulgae target, lifecycle state, commit ID, upstream publication, and external or live evidence distinct. Any code, test, durable documentation, generated, or derived change after verification or final Mulgae review makes affected evidence stale; the exact planned status-only roadmap transition is the sole exception. Do not advance after failed checks, evidence gaps required for completion, incomplete review, unresolved findings, unsafe staging, failed commit, or missing lifecycle evidence.

## Audit and Remediate the Epic

After all tasks are terminal, audit the latest committed epic state without an active goal or source mutation. Build a requirement-to-owner-to-production-to-test-to-document matrix across every task and inspect integration seams, consumers, persistence, concurrency, migrations, generated artifacts, recovery, operations, and roadmap consistency. Run only approved epic checks and one complete Mulgae review of the exact latest epic target.

With Podway active, atomically replace the disposed last-task session with a prepared `aquarium-validation-v2` session, then re-observe and `begin` the final audit. Record each fresh audit, route confirmed gaps through remediation and re-audit, and assess the epic goal only from the latest complete evidence. Remediation goals inside the active validation session are Codex goals recorded at its `remediate` node, never nested Podway sessions.

After the validation session succeeds, use `handed_off` only when an exact authoritative external result already exists. Otherwise record `not_required` only after verifying that this same approved handler retains ownership and the closeout session requires the slot. Atomically replace the disposed validation session with the prepared closeout goal and `begin` it.

Classify each verified gap by canonical requirement owner, not file count or edit location:

- A violation owned by one task remains task-owned even if that task is Completed or the fix crosses modules. Create a new goal for that task, transition through the roadmap's reopen state and back to success when one is defined, obtain fresh verification and Mulgae evidence, and hand the isolated correction to `$aquarium:task-commit` under its task ID.
- An epic seam invariant owned by no single task is cross-task. Create an epic remediation goal and hand the isolated correction to `$aquarium:task-commit` under the epic ID.
- Work requiring another repository is external. Stop with its owner, exact revision, and missing evidence; do not edit it.

If ownership is ambiguous, stop before goal creation and report the missing authority. Process task-owned gaps in canonical task order, then cross-task gaps. After each remediation goal, discard the prior audit and audit again from scratch. When an external blocker is resolved, first revalidate the DAG at its new exact revision and restart the audit.

Only after a clean latest-snapshot audit and complete Mulgae evidence may one final epic closeout goal be created. Transition the epic to its successful state, perform authorized synchronization, and hand an actual isolated epic-ID closeout diff to `$aquarium:task-commit`. Complete the closeout Podway session only after that commit is verified, record `handed_off` with its exact SHA, and leave the final terminal session intact. Never create an empty commit.

## Hand Off Commits and Report

For each approved commit, invoke `$aquarium:task-commit` with repository, canonical roadmap, task or epic ID, exact lifecycle decision or explicit absence, exact record decision or explicit absence, isolated scope, current verification and Mulgae evidence, and one-commit authority. That skill owns staging, Lore and Sanho checks, the direct commit, hook reconciliation, and snapshot verification. Never commit independently, amend, or infer push authority.

Use `$use-sanho` directly only for separately authorized synchronization outside the commit boundary. Use its refreshed push workflow only for a separately authorized push. Commit and upstream publication remain separate states.

Do not create or read `.aquarium` or other shadow state. Resume from roadmap, Git history and worktree, current goal, recoverable approval, repository evidence, and Mulgae records; request fresh approval when the envelope cannot be recovered.

At every stop and final handoff report current task and epic, dependency changes, completed and remaining goals, commits and roadmap states, checks and evidence gaps, Mulgae target and capture/findings/publication status, worktree boundaries, upstream publication state, and the exact next safe action.
