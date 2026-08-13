# Podway Integration Contract

Read this reference whenever a Root Kernel skill runs in a Git worktree that may use Podway. Podway records and guards procedure state; it does not run commands, validate the truth of evidence, mutate Git, or replace repository authority.

## Decide Whether Integration Is Active

Root Kernel Podway integration is repository opt-in. It is active only when all three tracked files exist and pass `podway procedure check --warnings-as-errors`:

- `.podway/procedures/root-kernel-task-v2.yaml`;
- `.podway/procedures/root-kernel-goal-v2.yaml`;
- `.podway/procedures/root-kernel-validation-v2.yaml`.

The mere presence of `podway`, `.podway/config.yaml`, or a non-Root-Kernel session does not opt a repository in. When none of the three managed procedures exists, use the skill's legacy workflow without Podway. When only some exist, a managed file differs from the plugin source or is untracked in Git, Podway is outside stable `v0.2.x`, the platform is not native Apple Silicon macOS, the CLI and daemon patch versions differ, the daemon is unreachable, doctor fails, a required v2 command is unavailable, or `.podway/config.yaml` or `.podway/.gitignore` is missing, stop and route repair or explicit opt-out to `$root-kernel:dev-setup`. Never silently fall back inside an opted-in repository.

## Keep Authorities Separate

- The canonical roadmap owns requirements, task and epic identity, lifecycle vocabulary, and official completion state.
- Podway owns the active procedure snapshot, attempt and rework history, recorded evidence, goal revisions, criterion assessments, and procedural terminal outcome.
- The Codex goal is a temporary projection of the currently actionable Root Kernel work recorded inside the Podway session. It may be absent during an explicitly goal-free read-only audit and may narrow to one owned remediation group, but it must never contradict or override the roadmap, Podway goal revision, or current node.
- Git commits, upstream publication, provider publication, live rollout, and external validation remain separate evidence states.

Podway evidence is a caller-recorded claim. Verify tests, reviews, approvals, revisions, and artifacts against their native authorities before recording them or making a decision.

## Read and Mutate Safely

Use `podway --json status` and `podway --json next`; never parse human output. Procedure v2 routes take the global flag first (`podway --json next`), while `version`, `daemon status`, and `doctor` take a trailing `--json`. Before every mutation, re-read state and pass every applicable workspace, session, session-revision, attempt, goal-revision, and item-revision fence plus a deterministic operation-specific idempotency key. Use only IDs from machine fields such as `allowed_option_ids` and `allowed_manual_rework_targets`.

After every successful mutation, re-read status rather than calculating revisions locally. On a precondition failure, re-read and derive the next action again. On `MUTATION_OUTCOME_UNKNOWN`, use `podway --json job lookup --idempotency-key <key>` and reconcile the durable result before considering resubmission with the same canonical request and key.

Record bounded summaries and references, not source contents, credentials, raw provider payloads, or full logs. For checks record the exact command, actor provenance, exit status, current source revision or dirty-tree identity, and a digest or stable evidence reference. For review record the exact target, run identity, coverage and publication status, findings-query status, and unresolved valid findings.

## Own Sessions Conservatively

Only `task-handler`, `epic-handler`, and `epic-validator` own Root Kernel Podway sessions. They start, resume, mutate, complete, and, where authorized, reset those sessions. Leaf and utility skills inspect Podway read-only and return evidence to the owner, or to the user for a user-invoked utility skill; they never start, complete, cancel, reopen, or reset a session.

A session is Root Kernel-owned only when its immutable procedure ID and task title or canonical identity match the requested workflow. Stop on any other active session. Never reset a running, cancelled, mismatched, user-owned, v1, or otherwise unproven session.

Do not mutate Podway before the workflow's existing plan or execution-envelope approval. Starting and recording the matching session is then covered only when the approval explicitly includes Podway mutations. A changed desired outcome requires `podway --json goal revise` with a declared rework target; it must not be disguised as another item update.

For sequential epic delivery, use one `root-kernel-goal-v2` session per member task, pre-validation remediation, or closeout goal. Once `root-kernel-validation-v2` starts, record its audit-owned remediation and re-audit inside that session because a worktree cannot host a nested goal session. Reset only after a session is successfully terminal and its roadmap state, evidence, and required commit have been re-read and handed off. The approved epic envelope may authorize these exact terminal-to-next-goal resets. A procedure update never migrates an active snapshot and applies only to a later session.

## Map the Managed Procedures

- `root-kernel-task-v2` is owned by `task-handler`; its nodes correspond to the approved plan, implementation, verification record and decision, refinement, documentation, Mulgae review record and decision, goal assessment, the assessed outcome with its follow-up commitments, final user approval, and closeout.
- `root-kernel-goal-v2` is owned by `epic-handler` for one member-task, pre-validation remediation, or closeout goal outside an active validation session. The epic closeout goal therefore starts only after the validation session is successfully terminal and reset.
- `root-kernel-validation-v2` is owned by `epic-handler` for its final epic audit and by `epic-validator` for cold validation and convergence. Each remediate record covers whatever remediation its owner completes before the next audit: one goal for `epic-handler`, the full confirmed-gap group set for `epic-validator`.

The owner records a leaf report only after independently checking the leaf postcondition. A failed check or valid unresolved review finding must select the failure route and create fresh rework evidence. A final Podway `achieved` outcome cannot make a non-successful roadmap task successful, replace required approval, create a commit, or establish publication.
