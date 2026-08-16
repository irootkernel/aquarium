---
name: epic-validator
description: "Cold-validate one completed roadmap epic, group confirmed gaps into sequential remediation goals, and converge to verified completion through direct Codex audit, Mulgae review, isolated commits, and re-audit. Use when the user explicitly invokes $aquarium:epic-validator with one repository, canonical roadmap path, and exactly one epic ID after its member tasks were completed through $aquarium:task-handler, $aquarium:epic-handler, or another evidence-backed workflow; do not invoke it implicitly."
---

# Epic Validator

Validate a completed epic independently of how it was delivered. Audit first, remediate confirmed gaps as goal-centered work, and repeat from a fresh snapshot until the epic claim is supported. Do not invoke `$aquarium:task-handler`, `$aquarium:epic-handler`, their phase skills, or `$aquarium:independent-review`.

Use Podway by default. Exclude it only when the current user explicitly opts this validation out before its managed session starts or a higher-priority instruction prohibits it. For an opted-out validation, do not inspect Podway, load `$use-podway`, or read [podway-integration.md](../../references/podway-integration.md), and do not carry the opt-out into a later workflow.

Otherwise read the contract and own one `aquarium-validation-v2` session for this exact cold-validation and convergence lifecycle. Podway records the audit loop; the roadmap and current implementation remain the semantic authority.

## Establish the Validation Contract

Require one mutable Git repository, one canonical roadmap path inside it, and exactly one epic ID present in that roadmap. Reject task-only requests, multiple epics, and requests without one canonical roadmap epic identity.

Before requesting approval:

1. Read applicable instructions, the epic, every member task, linked requirements, decisions, contracts, tests, documentation, and required or generated artifacts.
2. Confirm every member task is in a roadmap-defined successful state and its implementation has a committed evidence-backed baseline. The epic itself may be in review or a successful state. When a member task is incomplete, stop and report which handler the user should run; never invoke it here.
3. Inspect branch, upstream, HEAD, staged, unstaged, untracked, and conflicted state. Record the validation baseline and separate epic-owned residue from unrelated work. Stop when the epic baseline is uncommitted or cannot be isolated safely.
4. Discover repository-native verification, Gaori, `$use-gaori`, documentation synchronization, Mulgae, `$use-mulgae`, Sanho, `$use-sanho`, lifecycle, and commit guidance. Treat each CLI, repository configuration, project MCP, and agent skill as independent state. Inspect explicit external dependencies read-only and record repository, canonical identity, exact revision, lifecycle, dirty state, evidence, and owner.
5. Inspect the current goal and stop rather than replace a different unfinished goal.
6. Honor an explicit pre-session opt-out without Podway discovery and ignore every Podway readiness or session state. Otherwise apply the shared contract's readiness and session checks. On degraded readiness, stop and ask the user to choose `$aquarium:dev-setup` repair or an explicit opt-out for this validation.
   Resume only a managed validation session matching this epic and baseline. For any healthy conflicting session, use the shared lifecycle-conflict route: resume it through its matching owner, leave it untouched through validation opt-out, or hand its cancellation or discard to an explicit `$use-podway` request. Never describe that conflict as setup repair.

Present one bounded validation envelope covering direct audit, authorized checks, disclosed Mulgae source transmission, remediation of confirmed gaps required by existing epic authority, roadmap remediation notes, isolated staging, one commit per remediation goal, and a necessary final epic validation-record commit. Ask once for explicit approval. Approval does not cover new product requirements, another repository, amend, push, PR or release changes, live rollout, destructive actions, installation, or unrelated staging.

By default the envelope must cover starting or resuming the matching validation session, bounded evidence recording, decisions, rework, goal assessment, and terminal completion. Treat approval that explicitly omits Podway as approval of the same envelope without those operations.

Accept that opt-out only before the first managed-session mutation. Afterward classify every stop or opt-out request through the shared `Handle In-Progress Stop Requests` flow; never assume pause, cancel, reset, or an in-place switch to non-Podway execution. Never reset or replace another session automatically.

Do not create a goal, edit files, invoke providers, stage, commit, or alter external state before approval.

When a selected long or noisy check is routed through Gaori, reference `$use-gaori` and follow it when available. If it is missing and repository policy requires it, stop and route to `$aquarium:dev-setup`; otherwise run the repository's original documented command directly and report that evidence compression was unavailable. Never infer an unknown original command, and keep command result, extraction quality, and acceptance authority separate throughout audits and remediation.

Before each authorized Mulgae review, reference `$use-mulgae` and follow it when available, preferring its attached MCP workflow. If the skill or project MCP is unavailable and repository policy requires it, stop and route that exact gap to `$aquarium:dev-setup`; otherwise use the supported configured CLI fallback, report the unavailable integration once, and preserve exact preflight, run, publication, and findings evidence. Never start a second MCP server or blindly retry an uncertain review mutation.

## Audit the Epic Directly

Run the audit without an active goal and without source mutation:

1. Build a requirement-to-owner-to-production-to-test-to-document matrix across every member task. Trace runtime wiring, consumers, persistence, concurrency, migrations, generated artifacts, failure and recovery behavior, operational guidance, external dependencies, and roadmap consistency.
2. Inspect current code and evidence directly. Run only repository-authorized checks needed for the epic claim. Keep current agent-run, explicit user-run, unavailable, forbidden, stale, external, live, commit, and upstream publication evidence distinct; narrow green checks do not prove uncovered requirements.
3. Run Mulgae on one exact latest epic target that excludes unrelated work and includes every epic-owned staged, unstaged, untracked, generated, and derived file.
4. Treat Mulgae as complete only when `coverage_status=complete`, `ci_decision=pass`, `publication_status=committed`, the findings query succeeds, and zero unresolved valid findings remain. Provider success or exit status alone is insufficient.
5. Verify every candidate finding against current authority and implementation. Record only confirmed gaps; do not turn review hypotheses into work automatically.

With Podway active, run `podway observe --json --wait-for-idle` before each bounded audit or remediation delegation and verify the expected Procedure ID, epic and baseline identity, session, attempt, goal revision, and current node from that observation. Independently verify returned native evidence before recording the baseline and fresh audit or deciding whether gaps exist.

Select only actions allowed by `guidance.allowed_actions` and represented by current `mutation_templates` entries. A clean decision advances to final review; confirmed gaps advance to remediation. Do not record candidate findings as confirmed Podway gaps before adjudication.

## Group and Complete Remediation Goals

Group confirmed gaps by canonical requirement owner and coherent implementation boundary. Do not add new roadmap tasks or invent task IDs.

- For a gap owned by one existing task, create or resume one remediation goal containing that task ID and commit the isolated correction under that task ID. If the roadmap defines a reopen state, transition through it and return to success; otherwise preserve the successful state and record remediation evidence.
- For a cross-task seam or omitted epic-level design requirement owned by no existing task, create one epic remediation goal and commit the isolated correction under the epic ID.
- For work owned by another repository, stop with its owner, exact revision, and missing evidence. Never mutate that repository.

If ownership is ambiguous, stop before goal creation and report the missing authority. Order task-owned groups by dependencies and roadmap order, then epic-owned groups. Never run two remediation goals concurrently.

For each goal:

1. Implement the smallest complete correction, add or update regression evidence and durable documentation, and run affected authorized checks.
2. Run Mulgae on the latest complete remediation target, fix every valid in-scope finding, and repeat affected checks and review until complete.
3. Add a concise roadmap remediation note using repository conventions with owner, summary, planned commit identity, verification evidence, Mulgae result, and audited snapshot; do not create a new task entry.
4. Record resulting remediation commit IDs in the final validation record rather than attempting to predict a commit's own hash.

Stage only the goal-owned diff, including its lifecycle and remediation note. Confirm the reviewed implementation equals the staged diff except for the planned status or validation-record-only roadmap change, then record the staged tree and blob identities. Commit once under the owning task or epic ID, compare the commit with that snapshot byte-for-byte, verify no goal-owned residue or unintended hook change remains, then complete the goal.

## Re-audit to Convergence

After all remediation goals complete, discard the prior matrix, findings, checks, and review result. With no active goal, repeat the direct audit and whole-epic Mulgae review from the latest committed snapshot. If new gaps appear, regroup and repeat the goal cycle.

With Podway active, record each remediation group and new audit attempt. Stale or incomplete final evidence reworks to a fresh audit, while newly confirmed gaps follow the audit decision into remediation. Assess criteria and complete the session only after the same latest snapshot satisfies the roadmap closeout conditions.

When an external blocker is resolved, revalidate its exact committed revision and evidence before restarting the audit. Any code, test, durable documentation, generated, or derived change after verification or final review makes affected evidence stale; the exact planned status or validation-record-only roadmap change is the sole exception.

Declare completion only when the fresh Codex audit has no confirmed gap, every required check has current passing evidence, whole-epic Mulgae evidence is complete, every member task and the epic have roadmap-defined successful states, and no epic-owned residue remains. Record the final audited snapshot and evidence in the roadmap. Create an epic-ID validation-record commit only when that produces an actual isolated diff; never duplicate an equivalent record or create an empty commit.

## Commit and Report Safely

Before a non-trivial commit, reference `$lore-commits` and follow it when available. If unavailable and no repository rule requires Lore, report that once, inspect `git log -5 --format=fuller`, and match recurring subject, body, and trailer structure without copying unrelated content. If fewer than five commits exist, inspect all; with none use a concise imperative subject.

If repository guidance requires Lore, stop and return an exact `$aquarium:dev-setup` continuation request instead of falling back. Repository-required IDs and prefixes override Lore, which never grants commit authority.

Before each authorized commit in a Sanho-managed repository, reference `$use-sanho` and follow its commit-boundary workflow when available; after the commit and hooks, refresh the applicable Sanho evidence. If unavailable and repository guidance requires it, stop and route to `$aquarium:dev-setup`; otherwise use the repository's required Sanho check or the minimal `sanho status --json` fallback and report the missing specialized guidance.

Use the refreshed push-boundary workflow only for a separately authorized push. Sanho status never grants commit, synchronization, or push authority.

Commit is not upstream publication. Do not push, amend, open or modify a PR, release, or claim live validation without separate authority and evidence. Request renewed approval when remediation would add a new requirement, cross repository scope, cause destructive impact, or exceed a safely isolatable existing epic requirement.

Do not create or read `.aquarium` or other shadow state. Resume from roadmap, Git history and worktree, current goal, recoverable approval, repository evidence, and Mulgae records. At each stop report baseline, audit status, remediation groups and owners, current goal, commits, checks, Mulgae capture and findings status, roadmap notes, worktree boundaries, publication state, and exact next safe action.
