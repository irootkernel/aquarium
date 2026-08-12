---
name: epic-validator
description: "Cold-validate one completed roadmap epic, group confirmed gaps into sequential remediation goals, and converge to verified completion through direct Codex audit, Mulgae review, isolated commits, and re-audit. Use when the user explicitly invokes $root-kernel:epic-validator with one repository, canonical roadmap path, and exactly one epic ID after its member tasks were completed through $root-kernel:task-handler, $root-kernel:epic-handler, or another evidence-backed workflow; do not invoke it implicitly."
---

# Epic Validator

Validate a completed epic independently of how it was delivered. Audit first, remediate confirmed gaps as goal-centered work, and repeat from a fresh snapshot until the epic claim is supported. Do not invoke `$root-kernel:task-handler`, `$root-kernel:epic-handler`, their phase skills, or `$root-kernel:independent-review`.

## Establish the Validation Contract

Require one mutable Git repository, one canonical roadmap path inside it, and exactly one epic ID present in that roadmap. Reject task-only requests, multiple epics, and requests without one canonical roadmap epic identity.

Before requesting approval:

1. Read applicable instructions, the epic, every member task, linked requirements, decisions, contracts, tests, documentation, and required or generated artifacts.
2. Confirm every member task is in a roadmap-defined successful state and its implementation has a committed evidence-backed baseline. The epic itself may be in review or a successful state. Stop and route unfinished delivery to the appropriate handler when a member task is incomplete.
3. Inspect branch, upstream, HEAD, staged, unstaged, untracked, and conflicted state. Record the validation baseline and separate epic-owned residue from unrelated work. Stop when the epic baseline is uncommitted or cannot be isolated safely.
4. Discover repository-native verification, documentation synchronization, Mulgae, lifecycle, and commit guidance. Inspect explicit external dependencies read-only and record repository, canonical identity, exact revision, lifecycle, dirty state, evidence, and owner.
5. Inspect the current goal and stop rather than replace a different unfinished goal.

Present one bounded validation envelope covering direct audit, authorized checks, disclosed Mulgae source transmission, remediation of confirmed gaps required by existing epic authority, roadmap remediation notes, isolated staging, one commit per remediation goal, and a necessary final epic validation-record commit. Ask once for explicit approval. Approval does not cover new product requirements, another repository, amend, push, PR or release changes, live rollout, destructive actions, installation, or unrelated staging.

Do not create a goal, edit files, invoke providers, stage, commit, or alter external state before approval.

## Audit the Epic Directly

Run the audit without an active goal and without source mutation:

1. Build a requirement-to-owner-to-production-to-test-to-document matrix across every member task. Trace runtime wiring, consumers, persistence, concurrency, migrations, generated artifacts, failure and recovery behavior, operational guidance, external dependencies, and roadmap consistency.
2. Inspect current code and evidence directly. Run only repository-authorized checks needed for the epic claim. Keep current agent-run, explicit user-run, unavailable, forbidden, stale, external, live, commit, and upstream publication evidence distinct; narrow green checks do not prove uncovered requirements.
3. Run Mulgae on one exact latest epic target that excludes unrelated work and includes every epic-owned staged, unstaged, untracked, generated, and derived file.
4. Treat Mulgae as complete only when `coverage_status=complete`, `ci_decision=pass`, `publication_status=committed`, the findings query succeeds, and zero unresolved valid findings remain. Provider success or exit status alone is insufficient.
5. Verify every candidate finding against current authority and implementation. Record only confirmed gaps; do not turn review hypotheses into work automatically.

## Group and Complete Remediation Goals

Group confirmed gaps by canonical requirement owner and coherent implementation boundary. Do not add new roadmap tasks or invent task IDs.

- For a gap owned by one existing task, create or resume one remediation goal containing that task ID and commit the isolated correction under `[TASK-ID]`. If the roadmap defines a reopen state, transition through it and return to success; otherwise preserve the successful state and record remediation evidence.
- For a cross-task seam or omitted epic-level design requirement owned by no existing task, create one epic remediation goal and commit the isolated correction under `[EPIC-ID]`.
- For work owned by another repository, stop with its owner, exact revision, and missing evidence. Never mutate that repository.

If ownership is ambiguous, stop before goal creation and report the missing authority. Order task-owned groups by dependencies and roadmap order, then epic-owned groups. Never run two remediation goals concurrently.

For each goal, implement the smallest complete correction, add or update regression evidence and durable documentation, run affected authorized checks, and run Mulgae on the latest complete remediation target. Fix every valid in-scope finding and repeat affected checks and review until complete. Add a concise roadmap remediation note using repository conventions with owner, summary, planned bracketed commit identity, verification evidence, Mulgae result, and audited snapshot; do not create a new task entry. Record resulting remediation commit IDs in the final validation record rather than attempting to predict a commit's own hash.

Stage only the goal-owned diff, including its lifecycle and remediation note. Confirm the reviewed implementation equals the staged diff except for the planned status or validation-record-only roadmap change, then record the staged tree and blob identities. Commit once under the owning task or epic ID, compare the commit with that snapshot byte-for-byte, verify no goal-owned residue or unintended hook change remains, then complete the goal.

## Re-audit to Convergence

After all remediation goals complete, discard the prior matrix, findings, checks, and review result. With no active goal, repeat the direct audit and whole-epic Mulgae review from the latest committed snapshot. If new gaps appear, regroup and repeat the goal cycle.

When an external blocker is resolved, revalidate its exact committed revision and evidence before restarting the audit. Any code, test, durable documentation, generated, or derived change after verification or final review makes affected evidence stale; the exact planned status or validation-record-only roadmap change is the sole exception.

Declare completion only when the fresh Codex audit has no confirmed gap, every required check has current passing evidence, whole-epic Mulgae evidence is complete, every member task and the epic have roadmap-defined successful states, and no epic-owned residue remains. Record the final audited snapshot and evidence in the roadmap. Create an `[EPIC-ID]` validation-record commit only when that produces an actual isolated diff; never duplicate an equivalent record or create an empty commit.

## Commit and Report Safely

Before a non-trivial commit, reference `$lore-commits` and follow it when available. If unavailable, report that once, inspect `git log -5 --format=fuller`, and match recurring subject, body, and trailer structure without copying unrelated content. If fewer than five commits exist, inspect all; with none use a concise imperative subject. Repository-required bracketed IDs and prefixes override Lore, which never grants commit authority.

Commit is not upstream publication. Do not push, amend, open or modify a PR, release, or claim live validation without separate authority and evidence. Request renewed approval when remediation would add a new requirement, cross repository scope, cause destructive impact, or exceed a safely isolatable existing epic requirement.

Do not create or read `.root-kernel-dev-skills` or other shadow state. Resume from roadmap, Git history and worktree, current goal, recoverable approval, repository evidence, and Mulgae records. At each stop report baseline, audit status, remediation groups and owners, current goal, commits, checks, Mulgae capture and findings status, roadmap notes, worktree boundaries, publication state, and exact next safe action.
