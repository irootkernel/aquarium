# Herdr migration

## Purpose and authority

This dossier is the temporary execution SOT for `EPIC-020` and `TASK-106`
through `TASK-109`. The [roadmap](../roadmap/README.md#epic-020-migrate-orca-review-to-herdr)
alone owns their identities, order, dependencies, and lifecycle state. This file
owns migration requirements and acceptance criteria until the epic promotes
them to canonical owners and settles the dossier under the
[Epic Execution SOT contract](../../plugins/aquarium/references/epic-execution-sot.md).

The target is the open `v0.1.19` release recorded in
[CHANGELOG.md](../../CHANGELOG.md). Its Aquarium package must use Herdr for the
review capability currently supplied by Orca, with no executable Orca review
route, compatibility alias, runtime prerequisite, or automatic fallback.
Published release history and completed review evidence keep their original
attribution. Removing a user's Orca installation is outside this epic.

`EPIC-016` and completed `TASK-085` supply the current routing and recovery
baseline. Preserve the [Review Brief](../../plugins/aquarium/references/review-intent-contract.md),
[static review](../../plugins/aquarium/references/review-contract.md),
[finding dispositions](../../plugins/aquarium/references/finding-disposition.md),
and [workflow routing](../../plugins/aquarium/references/review-routing-contract.md)
semantics while replacing Orca-specific execution evidence.

Registering this plan changes documentation only. It authorizes no migration
implementation, live reviewer execution, installation, Procedure activation,
source transmission, staging, commit, or publication. Each later workflow must
establish its own execution envelope and authority.

## Fixed design decisions

### Entry points, targets, and reviewer

The successor skill is `$aquarium:herdr-review`; its embedded route is `herdr`.
Mulgae remains the default, with Independent Review and explicit waiver as
separate alternatives. Readiness failures affect only the selected route.

Herdr Review is report-only and accepts these existing target meanings:

| Scope | Candidate authority |
| --- | --- |
| `staged` | The live `HEAD`-to-index transition, read through `git diff --cached` and index objects; unstaged bytes are excluded. |
| `head` | The complete tree of the commit resolved once from `HEAD`; current index and worktree changes are excluded. |
| `commit` | The first-parent transition into the resolved commit, or the empty tree into a root commit. |
| `range` | The requested `A..B` transition or merge-base-to-`B` transition for `A...B`, preserving the operator. |

`workspace` and `dirty` remain unsupported. Conflicts or an empty staged target
stop dispatch. The handler prepares the complete isolated staged Task candidate
under its existing staging authority; the reviewer never changes the index.
No copied checkout, extra Git worktree, capture manifest, or new target
fingerprint is introduced. Observed target changes invalidate the applicable
review evidence and require the owning workflow's target-refresh rules.

Require an explicitly selected reviewer kind. Honor requested native model and
effort arguments through the provider's supported interface and report the
identity actually established; do not substitute another reviewer. Use one
fresh reviewer in a sibling pane, preserving the canonical Git root, caller
working directory, and focus. The initial migration covers the current local
Herdr session and checkout. Remote review and different workspace topology are
outside this delivery scope.

### Native execution and readiness

Herdr owns pane and agent control, submission, lifecycle observation, output
reads, and supported recovery. Aquarium owns target selection, the complete
Review Brief, result admission, finding adjudication, and workflow acceptance.
Do not emulate Orca Run, Task, Dispatch, Delivery, acknowledgement, or settlement
objects inside Herdr.

Use the separately installed upstream `herdr` skill and the installed CLI's
current grammar. The initial qualification baseline is official
[Herdr v0.9.3](https://github.com/herdrdev/herdr/releases/tag/v0.9.3) and its
[release-matched skill](https://github.com/herdrdev/herdr/blob/v0.9.3/skills/herdr/SKILL.md).
This baseline is not evidence that the host has that version installed or that
its running server supports the same features. Check client, server, skill,
and requested reviewer readiness separately before relying on them.

Require `HERDR_ENV=1` before inspecting or controlling a Herdr session. Outside
Herdr, report the selected route's prerequisite gap without controlling a
focused session or launching a replacement backend. Inside Herdr, use explicit
caller context or returned IDs and preserve `--no-focus` behavior. Follow the
upstream split geometry, available-shell, fresh-agent, prompt, and wait rules.

Treat Herdr as an externally installed runtime, as Orca is today. This migration
adds the selected route's readiness and setup guidance without adding a managed
installer, a service manager, or Herdr to Aquarium's general production-binary
baseline. Do not vendor the upstream skill or create a central project-state
file. Installation, skill replacement, integration hooks, or server changes
require their separate native setup authority.

### Review restrictions and result evidence

Every prompt carries the complete approved Review Brief and the common static
restrictions: preserve source, tracked and non-ignored files, and Git state;
run no tests, builds, generators, formatters, linters, installers,
authentication, unrelated network operations, or another provider review; and
do not delegate the review. Permitted external and Git-ignored review output
retains its existing permission. These are instructions for same-user
processes, not an operating-system sandbox.

For change review, preserve proportional inspection and actionable target
findings. For completion review, require an assessment of every applicable
criterion. Keep findings, completion assessment, runtime verification gaps,
operational deviations, and execution status separate. The coordinator
validates the complete result before issuing the final technical verdict.

Herdr's `idle` or `done` status alone does not establish that the requested
review completed. Admit `review-operation=complete` only when the submission
and observed activity belong to the requested fresh reviewer, the exact target
and Brief remain applicable, and the required report is complete. Preserve
bounded session/pane and reviewer references, submission and wait outcomes,
and the report location when a retained file supplies the result. No backend
CI or immutable-capture guarantee is implied; use
`backend-check-result=not-provided`.

Read the complete report through the native agent surface. If a larger native
read still cannot recover it, use the upstream fallback: ask the same reviewer
to write the completed report as Markdown to an allowed temporary location and
read that file. Do not request file delivery in the initial prompt. Keep raw
reports and transient identities in native or disposable evidence under the
[evidence residency contract](../../plugins/aquarium/references/evidence-residency.md).
Herdr evidence cannot supply Mulgae-only hardening-deferral guarantees.

### Failure, recovery, and route continuity

A timeout or `agent_prompt_stalled` does not prove that submission failed or
the reviewer stopped. Inspect the same agent and available output before any
supported recovery; never blindly resubmit the prompt. `blocked`, `unknown`,
missing output, agent replacement, identity mismatch, or compromised target
evidence cannot become a successful review. Follow the upstream user-decision
boundary before responding to an approval or question UI.

Keep the same live operation while it is active or its terminal state is
unknown. Preserve prior reports and findings through supported recovery. A
failure remains `failed` or `incomplete` and consumes no assessment ordinal.
Route changes require the existing explicit authority and authoritative safe
state. Do not reset finding lineage, ordinals, remaining correction authority,
or the goal revision. Do not add Aquarium-only wait budgets or retry caps.

## Existing installations and sessions

Change the canonical Task, Goal, and Validation Procedure assets and the
Aquarium repository's matching tracked copies as one compatible unit with
their handlers, inspectors, fixtures, and tests. Increase each changed
Procedure version while retaining its stable ID. Follow
[Changing Procedures](../implementation-tips/changing-procedures.md) and the
[Podway integration contract](../../plugins/aquarium/references/podway-integration.md)
for exact bytes, native validation, customization preservation, and activation.

Updating source files never migrates an active Podway snapshot. Retain historical
`orca` evidence as Orca evidence; never relabel it `herdr` or fabricate Herdr
provenance. A new checkpoint selecting the retired route must stop before
dispatch. If an old snapshot cannot represent Herdr, offer only its supported
stop or route-change path, followed by a separately authorized eligible
successor using the new Procedure.

An active or unproven legacy Orca worker prevents a new review from starting.
Require its native owner or the user to establish terminal state outside the
new Aquarium execution path before a safe transition. The new package must not
invoke Orca to manufacture compatibility. Preserve earlier findings, consumed
ordinals, accepted dispositions, and remaining authority in the successor
handoff without rewriting the old snapshot or its history.

Setup must distinguish an older canonical source, a valid customization, a
selected route that is unavailable, and an incompatible handler contract.
Preserve customizations until the owner approves an exact replacement. A prior
snapshot may still use another route when that route and the full handler
contract are supported; detecting historical Orca labels does not authorize
Orca execution. Updating other repositories' installed Procedures and
user-global tools requires a separately approved rollout outside this
Aquarium implementation.

Podway, Mulgae, Gaori, Sanho, Sorage, and Dolgorae have no direct Orca runtime
dependency in the inspected source. Their Aquarium Procedure copies do carry
the old route. No producer engine change or Sorage handoff is required for this
epic. Haepari adoption remains owned by `EPIC-019` and is not a prerequisite.

## Task delivery and acceptance

The roadmap owns Task order, dependencies, and lifecycle status. These
checklists define the required results.

### TASK-106: Implement Herdr static review

- [ ] Add `herdr-review`, its host metadata, and the Herdr supervision contract
  using upstream native operations and the existing shared review semantics.
- [ ] Cover the four targets, both purposes, explicit reviewer identity, and
  report-only effects without Orca or Dolgorae execution.
- [ ] Define completion evidence, output recovery, blocked and unknown state,
  uncertain submission, and safe same-operation recovery without synthetic
  Orca lifecycle objects or new capture guarantees.
- [ ] Add focused executable checks only where helpers implement behavior;
  identify the observed-agent scenarios required by `TASK-109` separately.

### TASK-107: Integrate Herdr workflow routing

- [ ] Replace the active Orca route in Task, Epic, validation, closeout, commit,
  shared finding/evidence contracts, and standalone peer-review guidance.
- [ ] Remove the old `orca-review` package, supervision contract, implicit
  dispatch, and compatibility aliases after their consumers use Herdr.
- [ ] Update the three Procedure sources and repository mirrors, versions,
  readiness inspection, prior-source identities, structural fixtures, and
  native routing qualification together.
- [ ] Preserve complete staged-candidate preparation, prerequisite isolation,
  valid evidence combinations, ordinals, finding dispositions, correction
  budgets, safe route changes, and commit handoff semantics across all routes.

### TASK-108: Support migration from Orca workflow state

- [ ] Implement selected-route Herdr prerequisites and setup guidance without
  controlling a session outside Herdr or adding a common runtime prerequisite.
- [ ] Recognize legacy Procedure sources and snapshots, reject retired-route
  dispatch, preserve supported peer routes, and retain customizations.
- [ ] Document and verify safe handling of completed evidence, incomplete
  checkpoints, active or unknown legacy workers, and eligible successors.
- [ ] Provide exact update and verification guidance for separately authorized
  repository rollout; do not alter another repository or uninstall host tools.

### TASK-109: Qualify Herdr migration and promote documentation

- [ ] Run focused regressions and the applicable local Make gate. Verify the
  changed graphs through native Podway qualification; satisfy the official
  exact-artifact compatibility gate when preparing the release.
- [ ] Observe the required Herdr and workflow scenarios below against the exact
  candidate and native runtime, and obtain Master's actual manual outcomes.
  Missing observations remain unverified and block completion.
- [ ] Reconcile every current Orca reference across the installed package,
  handlers, setup, testing, current documentation, and planned consumers such
  as `EPIC-012` and `EPIC-017`. Keep only explicit historical or legacy-data
  references that cannot dispatch Orca, and repair links to removed files.
- [ ] Promote implemented contracts to specifications, architecture or ADRs,
  operations, implementation guidance, `TESTING.md`, public English/Korean
  documentation where affected, and the open CHANGELOG under their existing
  approval and prose-pass rules. Preserve published release notes.
- [ ] Complete internal Epic validation, obtain actual overall acceptance,
  replace this Epic's Detailed SOT link with Canonical Outcomes, and settle the
  dossier under the approved last-consumer closeout rules.

## Qualification scenarios and Epic exit criteria

| Scenario | Required evidence |
| --- | --- |
| Target and purpose | Both Codex and Claude reviews cover the four scopes, index/worktree exclusion, change findings, and criterion-level completion; unsupported, conflicted, and empty staged requests stop before dispatch. |
| Readiness and startup | Missing CLI, skill, reviewer, or Herdr caller context blocks only Herdr; client/server mismatch and startup approval do not trigger an upgrade or fallback. |
| Completion and output | Submission/activity correlation, actual reviewer identity, a complete report, and native history/file fallback are established; ready or unknown status without the result cannot pass. |
| Failure and recovery | Timeout, stalled submission, blocked UI, replaced agent, missing output, and lost observation preserve the same operation without duplicate prompts or false success. |
| Embedded workflow | Task, Epic, and validation preserve route choice, staged preparation, ordinals, findings, correction authority, closeout, and commit handoff after context restoration. |
| Existing state | Old canonical and customized Procedures, completed Orca evidence, incomplete checkpoints, active/unknown workers, and old snapshots take the documented preservation or safe-refusal paths. |
| Peer-route regression | Mulgae, Independent Review, and waiver retain their native prerequisites, evidence, recovery, verification, and acceptance behavior. |

Deterministic tests verify executable helpers and structural/native graph
behavior. They must not pin skill prose or introduce automated LLM evaluations
into `make test`. Static validation cannot establish installed skill discovery,
native reviewer behavior, or Master's manual acceptance. Keep operation outcome,
technical verdict, completion assessment, and verification results separate.

The Epic is complete only when every Task's required result is accepted, no
current execution path requires Orca, all applicable checks pass for the exact
candidate, and every required manual scenario has an actual accepted outcome.
No valid Medium-or-higher finding, pending Low disposition, unmet criterion, or
unverified required criterion may remain. Release publication and host or
cross-repository activation remain separate from Epic acceptance.
