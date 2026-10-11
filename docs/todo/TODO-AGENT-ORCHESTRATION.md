# Supervised agent orchestration

## Purpose and authority

This dossier is the temporary execution SOT for `EPIC-021` and `TASK-110`
through `TASK-117`. The [roadmap](../roadmap/README.md#epic-021-adopt-supervised-agent-orchestration)
alone owns their identities, order, dependencies, and lifecycle state. This
file owns their detailed scope, role contracts, implementation approach, and
acceptance criteria under the
[Epic Execution SOT contract](../../plugins/aquarium/references/epic-execution-sot.md).

Adopt an Orchestrator, Judge, and Workers model across the Task, Goal,
Validation, Design, and War-room Procedures. The main agent manages allocation,
native agent lifecycles, authority, and Podway progression. Workers perform
bounded research, analysis, implementation, and verification. A persistent
Judge assesses whether their evidence satisfies the current node, Task, and
Epic goals.

Execute this epic after `EPIC-020`, preserving its Herdr migration and technical
review contracts. No release version is selected for this epic. Registering
this dossier changes documentation only; feature implementation, live agent
execution, installation, activation, staging, commits, and publication remain
outside this registration change.

## Fixed decisions

### Roles and authority

| Role | Responsibility | Boundary |
| --- | --- | --- |
| Orchestrator | Select work, prepare authoritative inputs, allocate Workers, maintain Judge continuity, reconcile native results, and record permitted Podway transitions. | Accept complete native deliveries and reports under their placement checks and execution authority. Require an applicable Judge verdict for semantic progression without repeating the assessment or silently overriding it. |
| Judge | Assess all applicable canonical criteria against the exact candidate and complete evidence; explain unmet goals, missing evidence, and the scope of a valid verdict. | Report-only. No source or Git mutation, commits, implementation, or grant of user authority. |
| Workers | Perform the assigned research, analysis, implementation, checks, or corrections and return a complete candidate handoff. | Stay within the assigned mutation and execution envelope. Delivery alone does not establish goal achievement. |

The Primary accepts a complete native Worker delivery under its delivery checks
and authority, then completes the Worker Action to reach the Judge assessment.
It accepts the complete Judge report under its coverage, provenance, applicability,
and authority checks without repeating the assessment or requiring another Judge.
The following semantic Decision uses the applicable Judge verdict. Return a
disputed or inconsistent assessment to the Judge with the conflicting evidence.
The Orchestrator cannot substitute its own verdict to establish a pass.

One logical Judge serves a standalone Task lifecycle. Another serves an
Epic-handler lifecycle, including its member Tasks and internal validation.
An independently invoked cold Epic-validator starts a fresh Judge and obtains
the original evidence independently. Design and War-room each retain a Judge
for their own lifecycle. Judge persistence means preserving assessment context
and identity when possible; continuous execution is unnecessary.

Use host-native subagents on Codex and Claude for the initial backend. Preserve
explicit model and effort selections and existing host defaults. Use a
resumable native agent kind for the Judge. Reading and research may run in
parallel; implementation on a shared checkout runs sequentially. Technical
review routes retain their native concurrency and isolation contracts.

### Goals and evaluation boundaries

Each work-bearing node supplies the assigned objective, purpose, instruction
prompt, authoritative inputs, full selected evidence, permitted mutations,
deliverables, and success criteria. Role definitions supply common behavior;
node instructions supply the actual work and evaluation target.

Structure work as a Worker candidate Action, a Judge assessment Action, and an
Orchestrator Decision that selects progress, rework, or evidence collection.
The Worker Action's completion means that the candidate was delivered. A
separate assessment establishes whether that candidate achieves the goal.
Delegate Action placements only; the Primary retains Decision execution.

Assess work-bearing nodes and final Task and Epic checkpoints. Simple
operational, metadata, and approval transitions need their native checks, not
another semantic Judge cycle. Do not recursively judge Judge reports.

The Judge reads the canonical criteria directly and can inspect original
artifacts and evidence, rather than depending on the Orchestrator's summary.
It checks for criteria omitted from the assignment and records each applicable
criterion as `met`, `unmet`, `unverified`, or `not-applicable`, with evidence
or a reason. Task assessment includes applicable parent constraints without
requiring unfinished future Tasks to be complete. Epic assessment covers
integration and overall purpose even when every member Task has passed.

Mandatory unmet or unverified criteria prevent semantic acceptance. Missing
evidence remains unverified. A non-applicability claim needs a reason grounded
in the canonical scope. A changed candidate or requirement invalidates the
affected verdict and requires assessment of the new target.

### Technical review and goal assessment

Preserve [review routing](../../plugins/aquarium/references/review-routing-contract.md),
the [Review Brief](../../plugins/aquarium/references/review-intent-contract.md),
and [finding dispositions](../../plugins/aquarium/references/finding-disposition.md).
Mulgae, Herdr after `EPIC-020`, and Independent Review retain their selected
technical viewpoints, reviewer topology, exact targets, complete reports, and
native recovery rules. Existing standalone completion-review capabilities
remain available.

The Judge owns embedded goal and checklist verdicts. It consumes technical
review findings and applicable evidence without replacing a selected provider
review or being counted as one. Preserve review ordinals, budgets, accepted
risks, Low dispositions, and corrective authority across handoffs and recovery.
A Judge's negative verdict does not itself authorize additional reviews,
out-of-scope corrections, or another external operation.

### Handoffs and native integration

Define three shared interfaces: Worker handoff, Judge assessment, and
recovery checkpoint. Bind them to the work identity, exact candidate, goal
revision, Procedure node and attempt, native agent and task identities,
immutable role configuration provenance, evidence references, and remaining
gaps. Specify which fields come from native records and which belong to the
assessment document; do not invent native wire fields.

The native backend owns actual dispatch, sessions, feedback, accepted task
identity, complete results, settlement, and response-loss recovery. Podway owns
formal progression, recorded evidence and receipts, and mutation fences.
Map these through a versioned integration contract using supported public
surfaces. Qualify both host paths against the native delegation contract before
activating their required placements. Use Podway's supported delegation
capabilities; this plan includes no Podway core changes. A missing required
capability must be reported before expanding the implementation scope.

Role identity must cover the complete immutable role content and dependencies,
not just its name. Specify the accepted configuration, task and result bytes,
and acknowledgement domains needed by the native contract. Unsupported
metadata or acknowledgement is a qualification blocker. Do not fabricate
identities, use private database scraping, substitute synthetic receipts for
actual agent evidence, silently fall back to direct work, or add another
scheduler or daemon.

The official [Codex subagent documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents)
and [Claude subagent resume documentation](https://code.claude.com/docs/en/sub-agents#resume-subagents)
are implementation references. Their descriptions do not qualify Aquarium's
integration. Verify the actual host version, available APIs, agent kinds,
returned identities, and durable reconnect capability. Required delegation
cannot be waived by marking an unavailable placement complete.

Native result acceptance and Podway Action completion remain separate
operations. Accept the exact applicable result first, then complete the Action
using current fences and supported evidence. Decisions consume the recorded
assessment; they do not delegate themselves.

## Implementation owners

| Workflow | Procedure source | Orchestrator skills |
| --- | --- | --- |
| Task | `aquarium-task-v2.yaml` | `task-handler` and the linked Task phase skills |
| Epic execution | `aquarium-goal-v2.yaml` | `epic-handler` |
| Epic validation | `aquarium-validation-v2.yaml` | `epic-validator` |
| Design | `aquarium-design-v2.yaml` | `new-project`, `new-feature`, `refactor` |
| Diagnosis | `aquarium-war-room-v2.yaml` | `war-room` |

Bundled sources live in `plugins/aquarium/assets/podway/procedures/`. This
repository's installed copies in `.podway/procedures/` follow the
host-installed release and change only after the new release is installed.
Skill entrypoints and linked references own role behavior and handoffs. Update
the shared Podway integration, readiness inspection, and executable
qualification alongside the affected workflows. Keep conditional detail in
references and preserve the native contracts of integrated tools.

## Upgrade classification

This is a breaking change: existing users must update managed Procedures and
start compatible successor sessions. Verify exact candidate installation and
upgrade in the dedicated UTM macOS VM over the host-installed release
combination before release, including Master's separate functional verification.
Candidate development leaves host installations and this repository's installed
managed copies on the released combination. VM candidate installation, host
installation, and downstream rollout require their applicable separate authority.

## Recovery and compatibility

Retain existing Judge and Worker identities and try native reconnect first.
Session IDs alone are insufficient. A recovery checkpoint must establish the
Podway session, node, attempt, goal revision, exact candidate, native agent and
task identities, accepted and unaccepted result references, and current
criterion assessments.

When reconnect is unavailable, reconcile uncertain work before creating a
replacement. Restore the goals, role configuration, original evidence,
assessment state, and remaining work into the replacement agent. Bind new
results to its actual identity while retaining predecessor provenance. A
replacement Judge can reuse evidence but must establish verdict applicability.

After an unknown dispatch or result response, reconcile the accepted native
task and result before dispatching again. Establish quiescence before a
replacement Worker writes to the same checkout. If the supported native
surface cannot establish it, report a concrete blocker instead of risking
duplicate effects.

A new Podway attempt does not authorize automatic re-execution of external
work. Never relabel an old receipt for a new attempt. Reusing an artifact
requires explicit revalidation and the qualified native acknowledgement.
Changes to accepted Podway item state, including optional or cosmetic state,
can invalidate receipts; acquire the new attempt and current fences as the
native contract requires.

Podway does not automatically establish the current filesystem candidate.
The integration must track the exact assessment target and invalidate affected
verdicts after code or requirement changes. Reject late results, stale goals,
wrong candidates, and results from superseded agents before progression.

Judge or Worker replacement does not imply Primary replacement support.
Preserve the current Primary identity. Main-session replacement or host
switching must use a supported, explicitly authorized native successor path;
otherwise stop safely and retain the recovery evidence.

Retain all five stable Procedure IDs and increment their versions when the
contract changes. Update the bundled sources as one compatible candidate,
together with readiness inspectors and observation contracts, and leave this
repository's installed copies on the host-installed release. Distinguish delegation-aware v4 observation from existing direct v3
behavior; verify the actual version contract during implementation.

Previously admitted session snapshots remain immutable. Source updates apply
to future sessions and must preserve repository customizations. Distinguish
native Procedure validity from handler compatibility. For an incompatible
active snapshot, explain the safe continuation or explicitly authorized
replacement path. Rollout to other repositories and installed plugin copies
is a separate operation.

## Task acceptance checklists

Checklist completion records evidence only. The roadmap owns Task status.
Every Task must preserve unrelated work and existing approval boundaries.

### TASK-110: Define orchestration contracts

- [x] Define role ownership, logical Judge lifetime, exact target applicability,
  canonical criterion coverage, and formal Primary acceptance.
- [x] Define Worker handoff, Judge assessment, and recovery checkpoint contracts,
  with supported native provenance and failure behavior.
- [x] Resolve all five Procedure evaluation boundaries and the relationship to
  existing technical review, finding dispositions, and correction authority.

The reserved [shared contract](../../plugins/aquarium/references/agent-orchestration.md)
owns these definitions; the [specification](../specs/agent-orchestration.md)
and [ADR-0009](../architecture-decision-records/0009-supervised-agent-orchestration.md)
record their status and rationale. Native mappings, acknowledgement, and actual
host execution remain unqualified TASK-111 obligations. TASK-110 intentionally
has no release-note entry because a reserved design ships no independent
capability.

### TASK-111: Integrate native delegation

- [x] Add a report-only Judge capability and Worker guidance, with node-specific
  goals, permitted scope, complete evidence access, and structured handoffs.
- [x] Implement the versioned Codex and Claude native mappings for dispatch,
  immutable role configuration, accepted task identity, complete results,
  acknowledgement, settlement, and recovery.
- [x] Demonstrate actual delegated Action acceptance on both hosts. Reject
  unsupported required metadata and response-loss ambiguity without fabricated
  evidence or automatic direct fallback.

#### Native mapping implementation and qualification

The candidate provides report-only [Goal Judge instructions](../../plugins/aquarium/skills/goal-judge/SKILL.md)
and [Worker guidance](../../plugins/aquarium/references/worker-guidance.md).
The [native mapping profiles](../../plugins/aquarium/references/native-agent-mappings.md)
own the exact public field sources, digest domains and reconciliation conditions.
They use Codex CLI 0.162.0, Claude Code 2.1.295 and Claude Agent SDK 0.3.295
for the qualified initial-assignment and serialized-feedback paths.

The executable components perform distinct operations:

- [Assignment preparation](../../plugins/aquarium/skills/goal-judge/scripts/prepare_assignment.py)
  freezes complete role/dependency bytes and selected file evidence with safe
  filesystem reads. [Dispatch rendering](../../plugins/aquarium/skills/goal-judge/scripts/render_dispatch.py)
  supplies the exact UTF-8 role text as operative instructions and evidence as
  task data. Their local digests do not establish native acceptance.
- [Native delivery mapping](../../plugins/aquarium/skills/goal-judge/scripts/map_native_delivery.py)
  correlates complete public records and distinct task/result domains.
  [Codex binding](../../plugins/aquarium/skills/goal-judge/scripts/bind_prepared_delivery.py)
  and [Claude binding](../../plugins/aquarium/skills/goal-judge/scripts/bind_claude_delivery.py)
  recompute preparation and correlation, then bind the full role snapshot and
  acknowledged applicable controls to each accepted assignment and result.
- [Codex record capture](../../plugins/aquarium/skills/goal-judge/scripts/read_codex_thread.py)
  reads complete thread history from an explicitly selected existing public
  app-server endpoint. Claude records come from native CLI events and the
  official SDK's public session and subagent readers. Neither route reads
  private executor configuration or creates a Primary through a read operation.

Both native paths have exercised isolated Podway Action acceptance and completion.
Codex exercised a journaled initial assignment and serialized feedback to the
same retained agent. Claude exercised a synchronous Agent assignment followed by
SendMessage feedback to the same agent. Each path bound the full package,
operative role/dependencies, exact accepted input, applicable configuration and
complete result. Explicit Primary acceptance, two acknowledged rounds and
post-acceptance quiescence supported native receipts and Action completion.
These scenarios qualify those mappings and their retain disposition; they do
not establish whole-skill functionality or activate required placements.

Claude's initial tool-use message had a null stop reason. The mapping preserves
that value and requires the correlated successful structured AgentOutput before
recognizing completion. Exact prompt comparison includes the final newline.
Feedback records preserve native run identity, full task-started input, completion
events and the complete public child slice through its matched terminal UUID.
Opaque coordinator wrappers and legacy preview fields remain opaque. Creation
controls and actual per-run model/background state retain separate provenance.
An early Primary success result while feedback is pending cannot establish
completion; the final child result and subsequent quiescence are required.

Actual result-read response withholding on both paths recovered identical full
public history through the supported readers without redispatch. The Claude
history projection does not reconstruct the original outer AgentOutput, which
must remain retained. Missing acknowledgement and incomplete or mismatched
records require reconciliation; consumer-record fault injection does not prove
physical dispatch-transport loss. Physical dispatch-response loss remains
unverified and must be exercised before affected placement activation.

The helpers authenticate no supplied records and grant no acceptance, settlement
or redispatch authority. The collector and Primary retain those obligations,
including complete lifetime accounting, descendant quiescence and current
Podway package/context checks. Custom or forked Claude definitions, background
initial assignment and isolation routes require their own native mappings; the
qualified inline general-purpose route does not disable those capabilities.

TASK-111 is complete under delegated Epic acceptance after source checks and
Independent Review. Dependent workflow integration,
combined compatibility and Master's actual functional outcomes belong to
TASK-112 through TASK-117. The installed release and admitted snapshots retain
their existing contracts. No candidate installation or required-placement
activation is authorized by this checkpoint.

### TASK-112: Rebuild Task execution

- [x] Rebuild the Task Procedure, task-handler, and related phase contracts
  around Worker candidates, Judge assessments, and verdict-driven rework.
- [x] Preserve refinement, planning, implementation, verification, technical
  review, documentation, acceptance, closeout, and task-commit handoffs with
  their existing authority boundaries.
- [x] Verify that Worker delivery alone cannot pass a phase or Task and that
  absent evidence, changed targets, and uncovered corrections stop acceptance.

The TASK-112 source candidate declares bundled Task version `25` and its
[phase integration](../../plugins/aquarium/references/task-orchestration.md).
Checkpoint-local semantic followup gates preserve native source dominance and
require existing effect authority; a different earlier owner uses explicit
authorized manual rework. Final evidence candidates supply complete original
criterion and artifact bytes, including permitted Low composition and stopped
boundaries. Required placements remain undistributed and inactive. Independent
Review and delegated member acceptance completed this source checkpoint. Full
Make passed 2,014 tests; all six native authoring stages and eight isolated
structural scenarios passed. These checks do not establish actual workflow
functionality or Master acceptance.

Complete Claude multi-round lifetime and tool-bearing feedback qualification
belong to TASK-116; actual host/workflow and Master functional results belong
to TASK-117. Physical dispatch-response loss remains unverified. None is
replaced by source validation or result-read recovery.

### TASK-113: Rebuild Epic execution

The Goal version-28 source candidate declares eight required Worker/Judge placements, retains serial technical admission and delegated acceptance, and adds current final Goal/Epic assessment and exact followup-effect authority. Required placements remain inactive pending TASK-116/117. Focused and full local checks, native authoring, isolated structural fixtures and Independent Review support the exact source checkpoint. The coordinator accepted this Task under the approved Epic delegation; actual integrated qualification and final Master acceptance remain pending.

- [x] Rebuild the Goal Procedure and epic-handler around one logical Judge
  across member Tasks, integration, and internal Epic validation.
- [x] Preserve delegated member acceptance and distinct commit grants without
  attributing them to Master or repeating per-Task approval pauses.
- [x] Verify overall goal failure when member Tasks pass but integration criteria
  fail; retain Master's actual overall acceptance before final closeout.

### TASK-114: Rebuild Epic validation

The Validation version-27 source candidate declares twelve required Worker/Judge
placements, faithful negative-audit routing and Primary correction-group commit
settlement. Cold validation uses a fresh Judge reading original evidence directly;
internal Validation retains the Epic Judge. Focused and full local checks, native
authoring, isolated structural fixtures and Independent Review support the exact source
checkpoint. The coordinator accepted this Task under the approved Epic delegation.
Required placements remain inactive pending TASK-116/117 qualification, actual Master
functional results and final overall acceptance.

- [x] Rebuild the Validation Procedure and epic-validator with a fresh Judge
  for independently invoked cold validation.
- [x] Assess canonical exit criteria from direct evidence and applicable
  technical reviews; preserve correction ownership and authority.
- [x] Verify that earlier completion labels, inherited verdicts, stale targets,
  and unsupported manual claims cannot establish cold-validation success.

### TASK-115: Rebuild design and diagnosis

Design and War-room version-5 source candidates declare fourteen and fifteen
required Worker/Judge placements. Both preserve complete frozen role snapshots,
original Ouroboros leaf scope, faithful negative routing and actual exact
document approval. Focused and full local checks, native source authoring,
isolated structural fixtures and Independent Review support this exact source
checkpoint. The coordinator accepted this Task under the approved Epic delegation.
Required placements remain inactive pending TASK-116/117 qualification, actual
Master functional results and final overall acceptance.

- [x] Rebuild the Design and War-room Procedures and new-project, new-feature,
  refactor, and war-room role handoffs.
- [x] Preserve the [Ouroboros leaf contract](../../plugins/aquarium/references/ouroboros-integration.md),
  [design gates](../../plugins/aquarium/references/design-gates.md), exact
  document approval, and diagnosis-specific scope.
- [x] Verify that Judge acceptance does not grant document application,
  installation, commits, or product implementation outside the approved design
  or diagnosis envelope.

### TASK-116: Align compatibility and recovery

The source candidate aligns Task version 26, Goal version 29, Validation
version 28, Design version 6 and War-room version 6. Every required placement
binds the complete nine-file Worker or Judge role snapshot. Earlier admitted
and customized snapshots remain valid for their original continuation;
current readiness requires the current declarations and separate update authority.
Phase passage preserves unfinished original Goal rows, while final achievement
still requires all applicable original criteria.

Native qualification covers four serialized Codex assignments and five Claude
assignments, including tools, an original nested Agent result, and feedback ACK
loss before the public SDK consumer. The accepted Claude assignment completed
without redispatch after its original response and public history were reconciled.
The mappings retain each assignment's configuration, task, result and complete
history. Existing two-round mappings remain unchanged. The fixture roles contain
two files and do not acknowledge the current nine-file roles. Codex direct child
input was rejected by the native host; it supplies no dispatch-loss evidence.
Current arbitrary descendant settlement, all-five actual workflows, candidate
upgrade and Master's functional results remain TASK-117 activation requirements.

The coordinator accepted this source checkpoint under the approved Epic
delegation after the required checks and Independent Review. Required
placements remain inactive until TASK-117 qualification and actual overall
acceptance.

- [x] Align all five bundled Procedures, version declarations, readiness
  inspectors, and observation contracts.
- [x] Exercise reconnect and restoration, uncertain dispatch/results, pending
  acceptance, quiescence, stale receipts, changed goals, and superseded agents.
- [x] Preserve old snapshots and customizations and document supported
  continuation, unsupported Primary replacement, and separately authorized
  successor or rollout paths.

### TASK-117: Qualify and promote outcomes

- [ ] Complete focused executable tests, required repository gates, native
  Procedure authoring checks, and exact-artifact compatibility evidence.
- [ ] Obtain actual Codex and Claude scenarios for all five workflows and
  Master's separate functional verification; distinguish structural fixtures
  from actual delegation and semantic evidence.
- [ ] Promote durable outcomes to canonical owners and reconcile the Task's
  qualification criteria for subsequent internal Epic validation.

Internal Epic validation follows TASK-117. Final Epic closeout requires actual
overall acceptance and dossier settlement under the consumer and approved
deletion rules. These remain Epic obligations after the member Task completes.

## Qualification and exit criteria

Define affected success and failure checks before implementation. Keep automated
checks focused on objective structure and executable behavior; do not pin skill
prose or add automated LLM evaluations to `make test`.

Run the focused checks and `make test` for the implementation candidate.
Qualify all five Procedures with native `format --check`, validation, vetting,
lint/check with warnings treated as errors, preview, and graph scenarios for
success, failure, and rework, using the supported command grammar. Confirm
that the actual graph and required delegation declarations are usable by the
current handlers.

The official exact Podway artifact compatibility gate must follow the
repository's candidate and Gaori environment contract for the clean committed
candidate. Local development binaries and synthetic protocol fixtures provide
development evidence only. This registration change does not run that gate or
qualify any implementation.

Actual agent scenarios on both hosts must cover:

- Worker delivery without Judge acceptance; unmet and unverified criteria;
  omitted criteria and access to original artifacts.
- Passing Tasks with an unmet Epic integration goal; fresh cold validation and
  rejection of an inherited completion claim.
- Wrong or changed candidates, changed requirements, stale receipts, late
  results, and superseded identities.
- Judge reconnect or restoration and Worker response-loss reconciliation,
  including prevention of duplicate dispatch and conflicting mutations.
- Technical review routes, finding disposition, preserved review budgets and
  correction limits, exact approval boundaries, and conditional commit grants.
- Design and War-room scope boundaries, custom Procedures, admitted old
  snapshots, and a safely refused unsupported recovery path.

Master separately verifies multi-step skill behavior, decisions,
recommendations, and cross-skill handoffs. Record the actual result and exact
candidate; test-suite success does not establish those outcomes. Required
unverified checks prevent completion.

Epic acceptance requires all mandatory Task and Epic criteria to be met, actual
required functional outcomes, no effective valid Medium-or-higher finding, and
no pending Low disposition. Retain explicit accepted-risk evidence where the
existing contract permits it. Obtain Master's actual overall acceptance before
final closeout.

Use existing Podway and native records for runtime state. Do not add a
`.aquarium` file or another central project-state owner. Promote only bounded
reviewed evidence under the
[evidence-residency contract](../../plugins/aquarium/references/evidence-residency.md);
runtime transcripts and ignored state do not become tracked documentation
authority.

Promote accepted durable requirements, architecture, decisions, implementation
guidance, and operations to their current canonical owners as each Task
finishes. Before Epic closeout, replace its Detailed SOT with valid Canonical
Outcomes links. Remove this index entry and dossier only after its last consumer
is successfully terminal and the approved deletion envelope covers settlement.
Complete a definition checklist only when its owning contract is delivered;
keep executable and functional checklists unchecked until their actual evidence
is accepted.
