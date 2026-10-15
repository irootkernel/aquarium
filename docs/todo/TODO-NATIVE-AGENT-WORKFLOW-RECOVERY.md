# Native agent workflow recovery

Consumers: EPIC-024 and TASK-126 through TASK-129. The
[roadmap](../roadmap/README.md#epic-024-restore-native-agent-workflows-and-add-manual-vm-release-acceptance)
alone owns their identity, dependencies and lifecycle. This dossier owns their
temporary implementation scope and acceptance criteria.

## Goal and implementation boundary

Restore ordinary workflow startup, simplify Orchestrator/Judge/Worker duties,
and add reusable manual VM release acceptance. Aquarium v0.1.19's native
qualification requirements can prevent handlers from starting when the harness
does not expose the required executor records. Ordinary work must use supported
native subagents without making inaccessible telemetry an admission condition.

## Failure mechanism and user benefit

The bundled default work nodes declare formal Podway delegation with a pinned
role-snapshot digest. Completing those Actions needs native receipts, while
Aquarium's handlers, role instructions and v1 reports require qualified
acknowledgement of executor identity, accepted configuration, assignment and
result bindings. Ordinary harness calls do not automatically supply that
integration evidence. Its absence therefore stops work even when native agents
can perform the task. Requiring fresh qualification after instruction changes
also makes earlier bounded observations insufficient for the changed roles.

Local structural checks and instrumented native fixtures covered narrower
contracts. The Podway adoption closeout at `33f7fbc` explicitly left complete
managed Worker/Judge runs for the combined release untested; release `aa0678b`
recorded accepted bounded UTM verification. Those results did not establish that
a fresh installed default handler could pass admission and begin useful native
work. The release scenarios now require that observation. This explains the
documented failure path without requiring the original private executor history.

Users should be able to request a Task or Epic and receive actual work plus
independent assessment without preparing an internal record collector. Review
effort should resolve current product defects, and upgrades should preserve
existing work. The correction removes ordinary qualification gates while
retaining genuine formal delegation requirements and meaningful verification.

## Planning baseline

The planning baseline is main at
`fa9f79b3432ae5f7604f667a5c46ef2c54f17e17`, after EPIC-023; registration changed
documentation only. TASK-126 defines the reserved
[ordinary v2 contract](../../plugins/aquarium/references/ordinary-agent-orchestration.md)
and producer/consumer map. TASK-127 still owns implementation and startup
recovery; TASK-126 activates no bundled Procedure or installed handler. The open
v0.1.20 release remains a separate publication lifecycle. No Podway producer change or
Haepari adoption is required. Actual verification in this Epic covers Codex only.

## Source map

| Concern | Owner to inspect and update during implementation |
| --- | --- |
| Roles, assignments, handoffs and recovery | [Ordinary v2 contract and producer/consumer map](../../plugins/aquarium/references/ordinary-agent-orchestration.md), [formal v1 contract](../../plugins/aquarium/references/agent-orchestration.md), [native mappings](../../plugins/aquarium/references/native-agent-mappings.md), [specification](../specs/agent-orchestration.md) |
| Procedure semantics and installed sources | [Node contracts](../../plugins/aquarium/references/procedure-node-contracts.md), [bundled sources](../../plugins/aquarium/assets/podway/procedures/), affected handlers and their linked references |
| Technical review and correction routing | [Review routing](../specs/review-routing.md), [review intent](../../plugins/aquarium/references/review-intent-contract.md), [finding disposition](../../plugins/aquarium/references/finding-disposition.md) |
| Verification and release authority | [TESTING.md](../../TESTING.md), [AGENTS.md](../../AGENTS.md), [VM methods](../../tests/vm/README.md), [release scenarios](../../tests/vm/release-acceptance.md) |
| Later managed VM execution | [Haepari adoption dossier](TODO-HAEPARI-VM-ADOPTION.md), TASK-088 and TASK-089 |

Inspect the actual report producers and consumers, renderers, validators and
setup diagnostics as well as the entrypoint prose. Current v1 reports encode
formal native/configuration provenance; deleting a startup sentence alone does
not remove that dependency.

## Roles and evaluation boundaries

| Role | Responsibility | Authority boundary |
| --- | --- | --- |
| Orchestrator / Primary | Set scope, assign native agents, collect results, reconcile evidence and advance Podway Decisions | Preserve Master's approvals, selected reviews, checks and commit boundaries |
| Worker | Perform assigned research, implementation, documentation, refinement and verification; return actual changes, results and gaps | Stay inside the assignment; one mutating Worker in the shared checkout at a time |
| Judge | Independently assess due criteria against original requirements and actual current artifacts | Report only; no implementation, approval attribution or lifecycle mutation |

Use the current AI harness's supported native subagents. Preserve selected
supported model options or its existing defaults. A Codex Primary uses Codex
Workers and Judge; a Claude Primary uses Claude Workers and Judge. A selected
technical-review route keeps its own providers and topology. Codex verification
does not establish results for Claude, Grok, GLM or other harnesses; their ordinary use is not gated
on this Epic's verification. Unavailable internal model telemetry does not block
ordinary work.

Assess the plan, a coherent phase of implementation or documentation with its
refinement and verification, and completion after the admitted technical review.
Epic assessment covers member
outcomes and final integration; Design and War-room use their applicable
proposal, quality and delivery boundaries. Operational bookkeeping does not
create another Judge cycle. Express these groups using supported Procedure
grammar; do not add unsupported fields.

Preserve actual approval, scope, mandatory tests, technical review, failure and
rework gates. Judge findings distinguish due product obligations from future
risks. Speculative future work does not become a prerequisite for acceptance.

Treat review findings as hypotheses. Confirm each against a due requirement and
reachable user impact before making it blocking. Request more information only
when it can change that decision. Sufficient evidence of the due obligations
permits progress; optional future hardening stays separate.

## Ordinary execution and evidence

Bundled defaults use ordinary Podway Actions with explicit responsibilities,
inputs, outputs and evidence/Decision routes. The harness executes native agents;
Podway records workflow state and does not authenticate those calls. Declared
formal delegation still obeys Podway's genuine integration and receipt contract.

Remove ordinary startup and continuation requirements for prior qualification of
complete role snapshots, private transcripts, full executor history and
effective configuration digests. Retain the relevant canonical criteria,
assignment and scope, available public native handles, actual returned results,
current candidate changes, checks and applicable Judge findings. Missing data
must remain unknown; never invent an identity, result or Judge pass.

Introduce versioned ordinary v2 assignment, Worker handoff, Judge assessment and
recovery checkpoint contracts. Migrate their producers and consumers together.
Preserve historical/formal v1 meanings and digest domains; do not satisfy v1 by
fabricating fields or silently changing what they mean. Keep mandatory technical
reviews and their native obligations. Add no scheduler, collector service,
central state, provider allowlist, arbitrary quota or retry cap.

## Recovery and managed updates

Reconnect known agents through supported native capabilities. Reconcile an
unknown outcome before replaying its work, and establish mutating-worker
settlement before replacement. A Judge may reconnect; otherwise restore the
original criteria, current artifacts and authority for a fresh independent
assessment. Full private history is not an ordinary recovery prerequisite.

If the harness actually lacks native subagents, report the concrete missing
capability and obtain a supported alternative. The Primary cannot label its own
assessment an independent Judge result.

This is breaking because existing repositories need an authorized managed-source
update and compatible successor sessions. Version all five affected Procedure
sources and align their inspectors and regression coverage. Preserve old/custom
immutable snapshots and their admitted rules. Do not reinterpret a formal
delegated session as Direct, bypass its receipts or overwrite customized files.

Keep the host on released tools and its existing managed files. Candidate
installation and any verification requiring it run only in the dedicated UTM VM.

## Task acceptance

### TASK-126: Define harness-native role and recovery contracts

- [x] Define role duties, meaningful evaluation boundaries and minimal relevant evidence.
- [x] Define ordinary v2 assignments, handoffs, assessments and recovery checkpoints; map every affected producer and consumer.
- [x] Include Procedure item prompts, Task phase skills, goal-judge, worker-guidance, report helpers and setup delegation inspection in that map.
- [x] Preserve formal delegation, historical v1 interpretation, actual native capability limits and truthful unknown outcomes.
- [x] Record breaking-update, customized-source and successor-session requirements.

### TASK-127: Implement grouped roles and remove startup qualification blockers

- [x] Align all five bundled Procedure sources, affected handlers and linked contracts with ordinary Actions and grouped native roles.
- [x] Update report producers/consumers, renderers, validators and setup diagnostics together.
- [x] Remove obsolete qualification dependencies from ordinary startup, continuation and recovery while preserving admitted formal sessions.
- [x] Preserve Mulgae routing, tests, technical reviews, approvals, correction ownership and truthful failure paths.
- [x] Verify executable behavior and observed skill scenarios; prose matching is not skill verification.

### TASK-128: Add manual VM release acceptance and reusable scenarios

- [x] Implement guest-side `make test-vm` with candidate-matched test sources, fixed small fixtures and deterministic verification helpers.
- [x] Verify the dedicated guest before fixture mutation, installation or agent dispatch; reject host execution with a nonzero result and no mutation, without requiring Haepari.
- [x] Keep the target outside normal Make aggregates and automatic Task/Epic checks; allow only release-handler or Master's explicit VM-test request.
- [x] Implement the methods and cases under `tests/vm/`, using manual UTM operation and Codex only, without Haepari.
- [x] Guide manual preparation and result collection from release-handler while preserving offline release QA.
- [x] Require actual observations and truthful non-success for failed or incomplete execution, including cleanup; printing instructions cannot pass.

### TASK-129: Verify workflow recovery and release readiness

- [x] Complete development functional, failure, rework and recovery checks before release preparation; use UTM for installed-candidate behavior.
- [x] Observe first Worker/Judge progression for every affected entrypoint: task-handler, epic-handler, epic-validator, new-feature, new-project, refactor and war-room. Keep the release smoke cases limited to Task/Epic startup.
- [x] Run required local checks and admitted technical reviews; keep structural success distinct from functional results.
- [x] If the VM gate runs for this Epic, use release-handler or Master's explicit VM-test request in the execution authority. The envelope states whether an observed development run of the new gate is part of Epic acceptance; ordinary Epic implementation approval alone does not invoke it.
- [x] Promote accepted canonical contracts and settle task evidence.
- [x] Keep release-acceptance evidence separate and exact-candidate-bound; do not infer publication readiness from document registration or local checks.

After internal Epic validation and closeout preparation, request Master's overall
verification and acceptance once. Final Epic closeout remains pending that actual
acceptance.

## Development verification and release acceptance

Development verifies actual functionality, full member delivery, rework,
recovery and final integration before release preparation. Record real native
calls, artifacts, checks and Judge outcomes; installation-dependent checks run
in UTM. Do not postpone those obligations until the release smoke scenarios.

Release acceptance starts by observing the existing released combination and
meaningful state before upgrading. Verify the supported candidate upgrade,
preservation, managed updates, fresh installed skill discovery and actual
Task/Epic startup with initial Worker/Judge progression. Broad feature testing,
two-member Epic delivery and full closeout need not repeat at release.

Reuse scenario definitions; retain actual results under the existing
[evidence-residency contract](../../plugins/aquarium/references/evidence-residency.md).
Candidate/result binding supports release judgment and does not become another
ordinary-work admission qualification. EPIC-019 later reuses this guest target
and scenario catalog when adding Haepari host transport; it is not a dependency
of this manual gate.

## Next-session execution

Read the roadmap, this dossier and its named authorities; recheck worktree state
and current contracts before mutation. Because the installed epic-handler is
affected, propose a scoped direct recovery execution envelope: the Primary
coordinates actual native Worker/Judge calls while retaining roadmap, check,
review and authority boundaries. Do not invoke the broken handler as a bootstrap
dependency or fabricate formal Podway acceptance. Preserve existing host sessions
and managed copies.

The installed task-handler, goal-judge, worker-guidance and delegated managed
Procedures carry the same qualification and v1 provenance requirements. For
this recovery, assign native Workers and the Judge directly with original
criteria, scope, current artifacts, expected results and their mutation or
report-only boundaries. Do not require those installed v1 role/report wrappers.
The proposed envelope explicitly selects manual coordination without a Podway
session for this Epic. Start no session on installed delegated Procedures or
candidate Procedures in the host repository; candidate Procedure behavior is
verified separately in UTM under its applicable authority.

The Primary carries forward the handler's actual obligations: selected review
route and authorized scope, release-note decisions, applicable cleanup and prose
passes, verification, task-commit handoffs with applicable Lore decision trailers
and required Aquarium attribution naming the actual workflow owner, validation,
closeout and Master's acceptance points. Use the roadmap, Git and bounded native
handoffs for lifecycle and evidence. Attribute acceptance to its actual
authorized owner; do not claim epic-handler delegated acceptance or manufacture
formal receipts for this manual route.

Execute TASK-126, TASK-127, TASK-128 and TASK-129 in dependency order under that
accepted scope. Registration alone grants no VM execution, installation,
staging, commit or publication. Obtain any distinct authority required for those
actions; use the applicable task-commit handoff when authorized.

Suggested next-session request:

```text
Implement EPIC-024 in this repository from docs/roadmap/README.md and
docs/todo/TODO-NATIVE-AGENT-WORKFLOW-RECOVERY.md. Use the dossier's direct
recovery execution route and propose its execution envelope before mutation.
Begin with TASK-126. Preserve existing host sessions and unrelated work.
Run make test-vm only through release-handler or my explicit VM-test request.
```

At closeout, promote durable outcomes to their canonical owners, replace incoming
dossier links with those owners and replace the roadmap's Detailed SOT with
Canonical Outcomes. Remove this dossier and its index entry only when all
declared consumers are terminal and the approved deletion
scope includes them, following the TODO index's last-consumer rule.
