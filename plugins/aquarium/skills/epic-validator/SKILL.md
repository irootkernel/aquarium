---
name: epic-validator
description: "Cold-validate one completed roadmap epic through a bounded direct audit, one remediation and confirmation review, severity-based user direction, and isolated commits. Use when the user explicitly invokes $aquarium:epic-validator with one repository, canonical roadmap path, and exactly one epic ID after its member tasks were completed through $aquarium:task-handler, $aquarium:epic-handler, or another evidence-backed workflow; do not invoke it implicitly."
---

# Epic Validator

Validate a completed epic independently of how it was delivered. Audit first, remediate the first confirmed findings once, run one confirmation review, and require user direction before any further correction or review. Do not invoke `$aquarium:task-handler`, `$aquarium:epic-handler`, their phase skills, or `$aquarium:independent-review`.

Use Podway by default. Exclude it only when the current user explicitly opts this validation out before its managed session starts or a higher-priority instruction prohibits it. For an opted-out validation, do not inspect Podway, load `$use-podway`, or read [podway-integration.md](../../references/podway-integration.md), and do not carry the opt-out into a later workflow.

Otherwise read the contract and own one `aquarium-validation-v2` session for this exact cold-validation lifecycle. Podway records each bounded pass and user disposition; the roadmap and current implementation remain the semantic authority.

## Establish the Validation Contract

Require one mutable Git repository, one canonical roadmap path inside it, and exactly one epic ID present in that roadmap. Reject task-only requests, multiple epics, and requests without one canonical roadmap epic identity.

Read [design-gates.md](../../references/design-gates.md). Resolve each member task's effective Design Gate impact from the task first and then the epic, applying the documented legacy-only `Not required` rule when neither marker exists. Treat a missing effective marker in an enrolled repository or a `Pending` marker as an incomplete epic contract and stop before remediation.

Resolve every effective active gate plus active gates whose scope covers an integration seam, and include their local offline checks in the requirement matrix and every fresh final audit. Redirect declared outputs and caches to disposable roots and verify that each gate leaves the source repository unchanged.

Before requesting approval:

1. Read applicable instructions, the epic, every member task, linked requirements, decisions, contracts, tests, documentation, and required or generated artifacts.
2. Confirm every member task is in a roadmap-defined successful state and its implementation has a committed evidence-backed baseline. The epic itself may be in review or a successful state. When a member task is incomplete, stop and report which handler the user should run; never invoke it here.
3. Inspect branch, upstream, HEAD, staged, unstaged, untracked, and conflicted state. Record the validation baseline and separate epic-owned residue from unrelated work. Stop when the epic baseline is uncommitted or cannot be isolated safely.
4. Discover repository-native verification, Gaori, `$use-gaori`, documentation synchronization, Mulgae, `$use-mulgae`, Sanho, `$use-sanho`, lifecycle, and commit guidance. Treat each CLI, repository configuration, project MCP, and agent skill as independent state. Inspect explicit external dependencies read-only and record repository, canonical identity, exact revision, lifecycle, dirty state, evidence, and owner.
5. Inspect the current goal and stop rather than replace a different unfinished goal.
6. Honor an explicit pre-session opt-out without Podway discovery and ignore every Podway readiness or session state. Otherwise apply the shared contract's readiness and session checks. On degraded readiness, stop and ask the user to choose `$aquarium:dev-setup` repair or an explicit opt-out for this validation.
   - Resume only a managed validation session matching this epic and baseline. A nonmatching prepared, running, incomplete, or undisposed terminal session uses the shared lifecycle-conflict route: resume it through its matching owner, leave it untouched through validation opt-out, or hand explicit cancellation or deletion to `$use-podway`. Never describe that conflict as setup repair.
   - A disposed terminal session with verified handoff evidence and a current `session.start_replace` template becomes an exact successor candidate. Include its fenced eligible replacement in the validation envelope and, after approval, use `start --replace-eligible` without a separate reset before re-observing and beginning the prepared validation session.

Present one bounded validation envelope covering direct audit, authorized checks, disclosed Mulgae source transmission, remediation of confirmed gaps required by existing epic authority, roadmap remediation notes, isolated staging, one commit per remediation goal, and a necessary final epic validation-record commit. Ask once for explicit approval. Approval does not cover new product requirements, another repository, amend, push, PR or release changes, live rollout, destructive actions, installation, or unrelated staging.

By default the envelope must cover creating or resuming the prepared validation session, the separate fenced `begin`, bounded evidence recording, decisions, rework, goal assessment, terminal completion, and any supported terminal disposition. Treat approval that explicitly omits Podway as approval of the same envelope without those operations.

Accept that opt-out only before the first managed-session mutation. Afterward classify every stop or opt-out request through the shared `Handle In-Progress Stop Requests` flow; never assume pause, cancel, reset, or an in-place switch to non-Podway execution. Never reset or replace another session automatically.

Do not create a goal, edit files, invoke providers, stage, commit, or alter external state before approval.

When a selected long or noisy check is routed through Gaori, reference `$use-gaori` and follow it when available. If it is missing and repository policy requires it, stop and route to `$aquarium:dev-setup`; otherwise run the repository's original documented command directly and report that evidence compression was unavailable. Never infer an unknown original command, and keep command result, extraction quality, and acceptance authority separate throughout audits and remediation.

Before each authorized Mulgae review, reference `$use-mulgae` and follow it when available, preferring its attached MCP workflow. If the skill or project MCP is unavailable and repository policy requires it, stop and route that exact gap to `$aquarium:dev-setup`; otherwise use the supported configured CLI fallback, report the unavailable integration once, and preserve exact preflight, run, publication, and findings evidence. Never start a second MCP server or blindly retry an uncertain review mutation.

For each operationally complete whole-epic root review, record the next positive ordinal for the current validation goal revision, the exact committed run ID, and valid Critical, High, Medium, and Low counts plus finding IDs. Round one is `remediation-eligible`; round two and every user-authorized later review are `confirmation-only`. On resumption, reconstruct the ordinal from verbose validation Procedure history and exact run IDs; an unprovable ordinal stops before review. Cold validation never selects `hardening-deferral-eligible` mode.

## Audit the Epic Directly

Run the audit without an active goal and without source mutation:

1. Build a requirement-to-owner-to-production-to-test-to-document matrix across every member task. Trace runtime wiring, consumers, persistence, concurrency, migrations, generated artifacts, failure and recovery behavior, operational guidance, external dependencies, and roadmap consistency.
2. Inspect current code and evidence directly. Run only repository-authorized checks needed for the epic claim. Keep current agent-run, explicit user-run, unavailable, forbidden, stale, external, live, commit, and upstream publication evidence distinct; narrow green checks do not prove uncovered requirements.
3. Run Mulgae on one exact latest epic target that excludes unrelated work and includes every epic-owned staged, unstaged, untracked, generated, and derived file.
4. Treat a Mulgae review as operationally complete only when `coverage_status=complete`, `ci_decision=pass`, `publication_status=committed`, and the findings query succeeds. Classify that complete review as clean only when zero unresolved valid findings remain; otherwise apply the bounded remediation or explicit disposition rules below. Provider success or exit status alone is insufficient.
   Record `structured_extraction_status` independently as `structured`, `mixed`, or `reports_only`. `reports_only` is not itself a failure and does not replace or relax any completion condition above; the accepted reports remain authoritative, and every extracted finding remains an advisory hypothesis that requires local verification.
5. Verify every candidate finding against current authority and implementation. Record only confirmed gaps; do not turn review hypotheses into work automatically.

With Podway active, create or resume the matching prepared validation session only after approval, re-observe and `begin` it, then run `podway observe --json --wait-for-idle` before each bounded audit or remediation delegation and verify the expected Procedure ID, epic and baseline identity, session, lifecycle, revision, attempt, goal revision, and current node. Independently verify returned native evidence before recording the baseline and fresh audit or deciding whether gaps exist.

Select only actions allowed by `guidance.allowed_actions` and represented by current `mutation_templates` entries. A clean decision advances to final review; confirmed gaps advance to remediation. Do not record candidate findings as confirmed Podway gaps before adjudication.

## Group and Complete Remediation Goals

Group confirmed gaps by canonical requirement owner and coherent implementation boundary. Do not add new roadmap tasks or invent task IDs.

- For a gap owned by one existing task, create or resume one remediation goal containing that task ID and hand the isolated correction to `$aquarium:task-commit` under that task ID. If the roadmap defines a reopen state, transition through it and return to success; otherwise preserve the successful state and record remediation evidence.
- For a cross-task seam or omitted epic-level design requirement owned by no existing task, create one epic remediation goal and hand the isolated correction to `$aquarium:task-commit` under the epic ID.
- For work owned by another repository, stop with its owner, exact revision, and missing evidence. Never mutate that repository.

If ownership is ambiguous, stop before goal creation and report the missing authority. Order task-owned groups by dependencies and roadmap order, then epic-owned groups. Never run two remediation goals concurrently.

For each goal:

1. Implement the smallest complete correction, add or update regression evidence and durable documentation, and run affected authorized checks.
2. Fix every valid in-scope finding from the initial audit and root review, then repeat affected checks without starting a per-goal or follow-up review.
3. Add a concise roadmap remediation note using repository conventions with owner, summary, planned commit identity, verification evidence, source findings, and audited snapshot; do not create a new task entry.
4. Record resulting remediation commit IDs in the final validation record rather than attempting to predict a commit's own hash.

Confirm the goal-owned diff, including its lifecycle and remediation note, equals the verified correction for the recorded source findings except for the planned status or validation-record-only roadmap change. Hand that exact scope, its evidence, owning task or epic ID, and approved one-commit authority to `$aquarium:task-commit`; verify its returned commit snapshot, residue, and hook evidence before completing the goal. The later whole-epic confirmation review, not the source review, owns coverage of those committed bytes.

## Confirm Once and Stop on New Findings

After all initial remediation goals complete, discard the prior matrix, findings, checks, and review result. With no active goal, repeat the direct audit and run exactly one round-two whole-epic Mulgae confirmation review from the latest committed snapshot. Do not start a third review automatically.

If round two is operationally incomplete, stop without retry. If it has no valid finding, continue normal closeout. Critical or High findings block validation and require user direction. One or more Medium findings stop with a recommendation to authorize exactly one correction-and-review budget, explicitly accept the named risk, or stop. When only Low findings remain, recommend either accepting their exact IDs or applying an eligible micro correction, then wait for the user's choice.

A micro correction is eligible only when it needs no product or authority choice, has no security, privacy, public API, schema, migration, persistence, lifecycle, or cross-repository impact, is safely isolated, and has a focused deterministic check. After the user selects the exact correction, implement it once, run affected checks, commit through `$aquarium:task-commit`, and proceed without another Mulgae review. Record `user-authorized-micro-fix` and state that the last root review predates the correction; never describe it as review-covered.

Record ignored Low findings as `accepted-low` with exact IDs and rationale. Record a user-accepted Medium as `accepted-medium-risk`; never call either disposition a clean review. Critical or High findings cannot use a risk-acceptance route. Each user-authorized correction grants one remediation and one next-ordinal confirmation review only. Apply this same severity decision again after that review and ask again rather than restoring an automatic loop.

With Podway active, record each remediation group, fresh audit, severity count, finding ID, and exact user disposition. Leave the decision unset while user direction is required. Assess criteria and complete the session only from the latest evidence plus any explicit accepted-risk or micro-fix record.

When an external blocker is resolved, revalidate its exact committed revision and evidence before restarting the audit. Any code, test, durable documentation, generated, or derived change after verification or final review makes affected evidence stale; the exact planned status or validation-record-only roadmap change is the sole exception.

Declare completion only when every required check has current passing evidence, whole-epic Mulgae evidence is operationally complete, every member task and the epic have roadmap-defined successful states, no epic-owned residue remains, and one of these closeout conditions holds:

- The fresh Codex audit and latest review are clean.
- Every remaining Medium and Low finding has an explicit `accepted-medium-risk` or `accepted-low` disposition, with no Critical or High finding.
- Every selected Low-only micro correction has current focused evidence and a `user-authorized-micro-fix` record that identifies the preceding review as predating the correction.

An incomplete review or `stop` disposition never supports completion. Record the final audited snapshot and evidence in the roadmap. Hand an actual isolated epic-ID validation-record diff to `$aquarium:task-commit`; never duplicate an equivalent record or create an empty commit.

With Podway active, complete the validation session only after the validation-record commit and clean residue are verified, record `handed_off` with that exact commit SHA, and leave the final terminal session intact. If no authoritative external result exists, leave it undisposed rather than inventing a reference or choosing force cleanup.

## Hand Off Commits and Report Safely

Every remediation or validation-record commit goes through `$aquarium:task-commit` with the repository, canonical roadmap, exact task or epic ID, the approved lifecycle decision as an exact edit or explicit absence, the approved record decision as an exact edit or explicit absence, exact isolated scope, current verification and Mulgae evidence, and one-commit authority. That skill owns staging, Lore and Sanho commit-boundary checks, the direct commit, hook reconciliation, and byte-for-byte snapshot verification. Never commit independently.

Use `$use-sanho` directly only for separately authorized synchronization outside the commit boundary. Commit is not upstream publication. Do not push, amend, open or modify a PR, release, or claim live validation without separate authority and evidence. Request renewed approval when remediation would add a new requirement, cross repository scope, cause destructive impact, or exceed a safely isolatable existing epic requirement.

Do not create or read `.aquarium` or other shadow state. Resume from roadmap, Git history and worktree, current goal, recoverable approval, repository evidence, and Mulgae records. At each stop report baseline, audit status, remediation groups and owners, current goal, commits, checks, Mulgae capture and findings status, roadmap notes, worktree boundaries, publication state, and exact next safe action.
