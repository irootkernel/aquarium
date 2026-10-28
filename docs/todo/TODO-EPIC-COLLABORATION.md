# Epic Squad collaboration

## Purpose and authority

This dossier defines planned `epic-squad` delivery for Aquarium maintainers and
workflow authors. Its consumers are
[EPIC-027](../roadmap/README.md#epic-027-add-native-epic-squad-collaboration) and
[EPIC-028](../roadmap/README.md#epic-028-extend-epic-squad-with-herdr-and-mixed-collaboration).
The roadmap alone owns IDs, ordering, dependencies and lifecycle state. This
file owns the detailed requirements, implementation boundaries and acceptance
contract until each consumer promotes its implemented outcomes.

The original planning baseline is Aquarium v0.1.20. The 2026-10-27 revision
uses the current ordinary/adaptive contracts and the product-first delivery
requirements below. This skill remains unimplemented. This documentation change
authorizes no implementation, workflow execution, candidate installation or commit.

The design incorporates the agreed Epic Solo and Epic Harmony workflows with
five role names: Coordinator, Epic Evaluator, Task Evaluator, Task Operator and
Support Operator. These names also apply to corresponding epic-handler roles
under the mapping below. The standalone templates outside this repository are
planning inputs, not required execution files.
Earlier names `epic-harmony`, `epic-operator` and `epic-team` are not additional
entrypoints. The native and external capabilities share one `epic-squad` owner.
Epic Harmony v0.0.3 and selected lessons from Claude's v0.0.4 proposal inform
this revision; Squad does not adopt or execute v0.0.4. Retain purpose-bound
support work, independent assessment, candidate provenance and honest runtime
configuration reporting. Do not import a line-count quota, recurring host-wide
configuration audit, CLI-version-specific launch recipes or a second policy
runtime. Proposed Pilot remedies are not evidence that Squad already works.

## Shared role names

Use these names in workflow instructions, assignments, profile examples and
current reports for both Epic workflows. The abbreviations are C, EE, TE, TO and
SO respectively. The mapping changes terminology without adding participants,
permissions, checkpoints or required reviews to epic-handler.

| Role | epic-squad | epic-handler |
| --- | --- | --- |
| Coordinator | Owns delivery coordination, scope, acceptance and commits. | The existing Coordinator keeps those responsibilities. |
| Epic Evaluator | Maintains Epic context and assesses Task contributions and final integration. | Names the existing single logical Evaluator, which continues to assess member Tasks, corrections, integration and closeout at its existing checkpoints. |
| Task Evaluator | A distinct Task-scoped independent evaluator. | No separate role or instance is introduced; the Epic Evaluator retains the handler's existing Task assessment duties. |
| Task Operator | Plans, implements, verifies, documents or independently reviews assigned work. | Names the existing Worker/Executor carrying out bounded delivery work. |
| Support Operator | Optional factual investigation, assigned execution or supervision support. | Use this label only for an already-authorized helper doing such support. No support pool, helper launch or additional step becomes mandatory. |

Writer is temporary write authority; Reviewer is an assignment duty; Leader is
optional coordination within an assignment. None is a sixth top-level role.
A Task Operator may perform independent review only when non-authorship and the
existing reviewer rules hold. A Support Operator supplies facts, not verdicts.
Both evaluator names identify scope, not a change in permissions.

Keep epic-handler's single Epic Evaluator continuous across its existing scopes;
do not rename it Task Evaluator during a member Task or count that one assessment
as two independent evaluations. Missing roles need no placeholder, empty report
or extra approval. This mapping does not import Squad's role-profile interface,
Task teams, review panels or correction policy into epic-handler. Other workflows,
including the separately invoked epic-validator, keep their own role contracts.

Terminology and machine compatibility are separate. Retain existing lower-level
`coordinator`, `executor` and `evaluator` role values, ordinary report identifiers
such as `aquarium.executor-handoff/v3` and `aquarium.evaluator-assessment/v3`,
node IDs, admitted source identities and historical reports. Task Operator assignments map
to the existing executor contract; Support Operator assignments use that contract
with their narrower support permissions. Epic/Task Evaluator assignments map to
the evaluator contract with explicit work scope. Do not add a schema migration,
Podway change or rewrite of an admitted snapshot just to change display names.

EPIC-027 owns the bounded epic-handler terminology update alongside native Squad.
Implement it at the skill, Epic orchestration references, relevant assignment
wording and affected documentation/guidance. Shared contracts retain their generic
machine meanings and other callers' behavior. This dossier plans that update;
it does not claim the installed handler already uses the new labels.

## Product outcome and preserved behavior

Aquarium should help AI teams deliver enterprise-grade software through systematic,
efficient engineering. Squad's result is a working product that is correct,
maintainable, straightforward to extend for justified needs, and responsive under
its intended workload. The Coordinator owns that result, including architectural
coherence, understandable interfaces, operational reliability and affected user
journeys. Checks and reports establish evidence for those product outcomes.

Use small coherent delivery units, explicit contracts, independent review and
risk-based verification. Assess module boundaries and dependency direction,
necessary failure/recovery behavior, and performance-sensitive paths against the
project's requirements. Measure latency, throughput or resource use when a change
or requirement makes those properties material; do not require a new benchmark
system for every Task. Prefer a durable structural repair over a fragile small
patch when the current obligation needs it. Extensibility does not justify
speculative abstractions or support infrastructure.

Catch plan defects, implementation defects and cross-Task incompatibilities early.
Resolve important current defects before dependent work proceeds. Defer genuinely
independent future improvements with a useful re-entry condition. Reuse applicable
evidence, keep correction reviews focused and stop when the required outcome is
established. Faster delivery must not conceal missing requirements or weaken tests.

| Workflow | Intended use |
| --- | --- |
| `epic-handler` | Existing goal-centered Epic delivery, with its current internal assessments and integration validation preserved. |
| `epic-validator` | Explicit cold validation of a committed Epic from fresh context, independently of its delivery workflow. |
| `epic-squad` | Collaboration with independent plan and result reviews during implementation; omitted role profiles use native agents, and explicit CLI/model profiles use Herdr. |

Preserve the existing Handler/Validator pairing and the option to cold-validate
in a later session. Squad completes its own integration and closeout procedure
without a mandatory later `epic-validator` invocation. Its internal
assessment does not claim the fresh-context assurance of a separate cold audit.

Implement and verify the native foundation in EPIC-027 before adding role-specific
Herdr and mixed execution to the same skill in EPIC-028. During the native-only
phase, recognize explicit role profiles and report that their execution is not
implemented before starting affected delivery; never ignore them or run them
natively. Keep native-only delivery working as the extension develops. Explicit
profiles remain unavailable until their required Herdr/mixed execution, commit
and recovery integration is implemented; adding profile parsing or agent launch
alone does not enable delivery. Disclose unimplemented routes when inputs are
received, before entering a design continuation; unaffected authorized design
work may continue with that delivery blocker visible.
Keep the shared collaboration and integration contract. Do not invoke
`epic-handler` at runtime and layer contradictory instructions over it.
Existing handlers retain their behavior, admitted sessions and selected technical
reviews. Epic-handler's single logical Evaluator receives the Epic Evaluator name
under the shared mapping, with no new role or checkpoint. Preserve existing
callers' behavior when extending shared integrations.

## Scope and implementation choices

Assess both missing required behavior and unnecessary additions against the
original requirements, approved design and applicable repository/tool contracts.
A reviewed Task plan remains an implementation proposal within those sources.
Agent agreement, internal plan approval or documentation rewritten to match an
implementation cannot authorize a product scope expansion.

Task Operators, Evaluators and the Coordinator share responsibility for keeping the
solution within scope. Whoever proposes an addition must explain which existing
requirement it serves and what reachable problem would remain without it.
Apply this to material additions of features, abstractions, configuration,
constraints and verification. Use the existing plan or finding report; ordinary
implementation choices need no separate justification record.

Allow internal implementation choices and defect corrections needed to satisfy
existing requirements, even when the design omits their details. Prefer the
simplest sufficient approach that fits the project. Changes beyond those sources
to product capabilities, usage restrictions, operational obligations or design
direction need the user's scope decision before implementation; reuse existing
authorization when it covers the proposed change. Leave optional additions out
of current delivery when necessity is not established.
General claims of safety, extensibility or possible future need are insufficient.

Keep checks proportionate to required behavior, reachable failure paths and
actual regression risk. Preserve mandatory checks and necessary protections.
Do not add tests that merely mirror implementation, pin prose or cover states
excluded by established invariants. A complete result may pass without an
additional improvement or test. Do not add a review stage, scorecard or state
store to enforce this assessment.

For Aquarium, check whether a proposed restriction would block behavior supported
by an integrated tool's native contract. Such a restriction needs a basis in
applicable instructions, user authority, repository requirements, that native
contract or a concrete safety or external-action boundary. Do not invent
Aquarium-only quotas, retry caps, evidence demands or approval prerequisites.

### Purpose-bound support work

Validators, test harnesses, report parsers, candidate-ID helpers, agent watchers
and orchestration scripts are supporting work unless they are themselves an
explicit product requirement. Reuse repository commands and installed tool
capabilities first. Every material support addition, including one proposed by
the Coordinator or a Reviewer, must identify the current obligation it serves,
the concrete gap, the simplest sufficient approach and its stopping condition
in the existing plan or assignment.

Before substantial unplanned support expansion, the proposing agent returns that
basis to the Coordinator. The Coordinator admits, narrows or rejects it within
existing authority; only an uncovered effect or product/scope decision needs the
user. Ordinary task-local tests, short command combinations and necessary bounded
helpers need no new approval round. Judge cumulative purpose and maintenance cost,
not whether code is inline, saved, reusable or below an arbitrary line count.
A small script can be unnecessary; a larger required repair can be justified.

A support-tool defect blocks delivery only when current acceptance, trustworthy
required evidence or safe execution depends on it. Otherwise stop using it, use
an adequate existing path or defer its independent improvement. When the tool is
the required product, apply normal product criteria. Missing optional automation
is not a reason to build an enforcement or validation framework.

At existing assignment, result and exception boundaries, check whether work has
advanced an approved outcome or reduced a justified uncertainty. Product code
need not change during useful diagnosis. If support work grows while no required
outcome advances, safely pause that work, select a sufficient next step and report
the material diversion. Add no support dashboard, polling loop, validator or
extra review stage to enforce this rule.

## Invocation and shared context

The skill requires an explicit invocation identifying one mutable repository,
its canonical roadmap and one delivery Epic. Respect repository-defined standing
groups such as EPIC-000; they are not Epic-wide delivery targets. Reuse the
existing meanings of `execute`, `plan-only`, `plan-handoff` and `resume`.

Read repository instructions, the documentation index, canonical Epic and Task
requirements, architecture and existing implementation. Discover applicable
directory guidance and maintain affected documents under the existing
[directory guidance contract](../../plugins/aquarium/references/directory-agent-guidance.md).
This does not add a per-Task setup operation or make absent guides a prerequisite.
Resolve the execution SOT under the existing
[dossier contract](../../plugins/aquarium/references/epic-execution-sot.md).
Inspect branch, HEAD, staged, unstaged, untracked and conflicted state; identify
owned changes and preserve unrelated work. Start from the appropriate unfinished
Task and preserve accepted earlier work.

For Squad, `execute` enters the existing bounded `new-feature` design route in
the same conversation when ordinary feature work needs a dossier or
semantic clarification. Carry the exact repository, roadmap and Epic into that
phase. Preserve Design approvals and the required delivery-input commit boundary.
After successful design delivery, provide an exact new-conversation request
naming `epic-squad`, repository, roadmap and Epic; do not automatically resume
delivery in the design conversation. Carry supplied Evaluator and Task Operator
profiles, including which roles were omitted, as requested inputs separately
from observed configuration for resolution in the new session. Report pending
commit authority or other blockers before claiming delivery is ready.

Implement the new incoming/return caller in `new-feature`, the shared execution
SOT routing and repository guidance templates, preserving existing `epic-handler`
behavior. Other modes report the required continuation; refactor, diagnosis and
new-project work retain their appropriate explicit routes. Missing meaning cannot
be waived. Apply the linked dossier contract's Epic-level composite-SOT waiver
and active-session recovery rules; member Task delivery adds no separate dossier
waiver. Report unmet external prerequisites and keep delivery blocked; authorized
read-only helpers may investigate discoverable gaps.

Prepare a concise Context Brief containing project purpose and users, conventions
and architectural principles with their sources, the Epic outcome, member Tasks
and dependencies, Must-Do and Must-Not-Do constraints, acceptance criteria and
user scenarios, non-goals, boundaries and unresolved questions. Give agents
original source references and enough local context for their assignment.
Identify the scope, expected result, plan revision or implementation candidate,
current Writer and result channel. Investigate discoverable questions before
asking the user.

Maintain one active Task delivery goal in dependency order. Native goal creation
follows the current harness's actual contract; in Codex it requires an explicit
user request. A workflow invocation, approved plan or Podway goal does not supply
that request. Use existing planning facilities when native goals are inapplicable;
do not create a second project-state system. Read-only preparation for a later
Task may proceed without activating another delivery goal.

## Roles and independence

### Coordinator

Keep the current CLI, model and session. Establish direction, assign meaningful
work, coordinate results and control Writer transfers. Delegate substantial
investigation, planning, implementation, verification and documentation.
Supervise execution through lifecycle state and reported exceptions. Read
important decisions, actual artifacts, findings and relevant verification at
the applicable plan, Milestone, result, exception and Writer-transfer boundaries.
For routine plan progression, read the Task and Epic Evaluators' actual concise assessments and
material exceptions; do not duplicate their plan reviews or routinely import
full plans, detailed review exchanges or agent transcripts into this context.
When actual first assessments and any eligible closures satisfy both current
plan scopes, assign implementation to the Writer within existing authority.
Investigate or escalate a concrete concern when needed.
Check whether proposed mandatory work has a source and a necessary effect on the
current outcome. An Evaluator request alone does not make an addition required.

For result review, personally inspect the same frozen candidate in the project
and product context. This review may run alongside independent assessments;
withhold acceptance conclusions until those assessors have formed their own
views. Acceptance still waits for every due assessment and check.
Evaluate conventions, architecture, maintainability,
correctness, compatibility, product direction and affected user journeys. For a
CLI, API or library, include interface consistency, error and recovery behavior
and documentation. Native review helpers may assist; read their actual findings
and form your own final judgment. Confirming verdicts alone is insufficient.
Examine cumulative usage restrictions and whether normal supported user
scenarios remain usable.

The Coordinator may edit, integrate or debug after taking the Writer role.
Exclusively own staging, unstaging and local commits through the required commit
skill and tools in the Coordinator's execution context. Own delegated acceptance
within the user's authorization; never attribute that decision to the user.

### Epic Evaluator

Maintain the Epic purpose, architecture, shared contracts, dependencies,
accumulated decisions and integration risks from preparation through closeout.
Assess the overall approach and material cross-Task changes. Once Task-level
plan readiness is established, perform the required Epic-context plan assessment
for that Task. Focus on three questions: does it advance the Epic's intended
direction; does it correctly use verified earlier Task outputs, contracts and
decisions; and does it define the outputs, interfaces and remaining obligations
that later Tasks need? Read the relevant parts of that exact plan revision,
original Epic sources, relevant delivered outputs/contracts and applicable prior
handoffs directly. Use a concise
Task assessment as support. Detailed implementation choices, local edge cases
and test design belong to the Task Evaluator unless they expose an Epic-level
direction or dependency concern. Do not require future Tasks' implementation
prematurely.
Reject unjustified expansion of the Epic's capabilities or obligations, including
complexity accumulated across individually small Task additions.

Keep Epic context focused on consequential decisions, shared contracts,
verified delivered outputs and downstream obligations or risks. Retain source
references instead of accumulating full Task plans and detailed review histories.

Independently inspect each Task's first completion candidate and original sources
in the Epic context, alongside its first result review when inputs are ready.
A summary alone does not establish approval. After that assessment, re-engage
for a changed cross-Task contract, dependency, downstream premise or Epic scope,
or an unresolved finding owned by this role. A local correction with none of those
effects needs a recorded applicability basis, not another Epic approval call.
Review the assembled Epic separately at final integration.

Task-boundary approval concerns the current Task's contribution and the
remaining delivery sequence. Preserve legitimate downstream obligations without
demanding future Tasks prematurely or declaring the whole Epic complete. Supply
the verified post-commit handoff to the Epic Evaluator; unchanged reviewed content
does not require a separate acknowledgement round.

### Task Evaluator

Use a dedicated context for each Task, fresh when supported. Independently
assess its plan and actual result against original requirements, correctness,
verification and documentation. Own detailed plan readiness: requirement
coverage, implementation feasibility, local assumptions and edge cases, checks
and documentation. Assess unnecessary additions as well as omissions, including
redundant abstractions, unsupported restrictions and disproportionate tests.
Apply the same necessity standard to proposed review corrections.
Resolve required findings from the independent Task Operator reviews and establish
Task plan readiness from the actual assessment, eligible closures and any needed
affected reassessment before Epic assessment. Report unresolved substantive disagreements
as material exceptions; they do not establish plan readiness.
Keep detailed planning and correction context within this Task role; send concise
phase-specific assessments, material exceptions and accessible source references
to the Coordinator and Epic Evaluator. Keep the role recoverable through
corrections, Epic assessment, Coordinator review and commit verification. Preserve
completed assessments through the correction rules below; an eligible local
closure does not require a new Task Evaluator turn merely to restate a verdict.

### Task Operator

Assign bounded investigation, analysis, planning, implementation, verification,
documentation and independent review. Delivery Task Operators first produce a plan.
Choose the simplest sufficient implementation and explain material additions
under the scope contract above. Assess review requests on that same basis before
implementing them; report unsupported additions for disposition.
Task implementation requires both plan scopes to be satisfied for the assigned
revision, including any permitted verified delta, and the Coordinator's bounded
implementation assignment to the Writer. Earlier tracked
planning edits require a Coordinator-assigned Writer scoped to planning within
existing user authorization; that assignment grants no implementation authority.
Only the active Writer modifies project files;
Task Operators never modify the Git index or create commits.

Use a Leader only when coordinating a group helps. It returns actual descendant
findings and a synthesis, with no extra acceptance, Writer or commit authority.
Do not require fixed CLI-specific groups. The Coordinator manages its own native
helpers and any Leaders; a Leader cannot authorize another Writer.

### Support Operator

A Support Operator is an optional bounded execution assignment, not a new approval
role. The Coordinator may assign factual source investigation, approved checks on
a frozen candidate or isolated fixture, log extraction, or supported observation
of an existing operation. Use one only when it saves more work than it creates;
a small lookup stays with the role that needs it. Reuse supported native helpers
in EPIC-027; EPIC-028 may resolve an explicitly supplied Support Operator profile
through the same native/Herdr configuration contract.

Reports identify the candidate, commands and relevant inputs, actual outcomes,
exit status, original log locations, limitations and pending operations. The
Coordinator or responsible assessor checks original evidence rather than treating
a support summary as proof. Support Operators do not judge scope, select review
routes, close findings, count as independent Reviewers, acquire Writer authority,
change the Git index or advance Podway. They may write assigned reports and
isolated test outputs within their authority, never shared product files or
conflicting resources. Retain their results before retiring them; no permanently
running support team or support-approval node is required.

### Task team contexts

At each new Task, assign new delivery and review Task Operator instances and a
dedicated Task Evaluator. Start fresh conversations where supported; do not
resume the preceding Task team's conversations for the new Task. Pass concise
verified outcomes, shared contracts, important decisions, remaining obligations
and original source references. A shared Task Operator profile supplies configuration
for distinct instances across Tasks.

Within the same Task, retain or recover the contexts needed for planning,
implementation, review, corrections and commit verification. Non-authoring plan
reviewers may also review that Task's result. Retire completed Task roles after
the verified commit and handoff. Keep the Epic Evaluator's accumulated context
throughout the Epic under the existing continuation and recovery rules.

Configuration inheritance and conversation inheritance are separate. Disclose
unavoidable inherited context and require original-source assessment; do not
claim a clean context when the CLI cannot provide one. These limitations do not
authorize reuse of the preceding Task agent's conversation.

### Independent assessment

Use separate non-authoring instances for Evaluators and independent reviewers.
An author of the plan or implementation under assessment cannot independently
review it. For result review, exclude both implementation authors and authors of
the plan that guided it. Review feedback alone is not authorship, so a
non-authoring plan reviewer may assess the implementation too. Different role
labels, a parent's synthesis or a Task Operator's self-check do not create independent
assessments. Separate instances may use the same profile without claiming model
or provider diversity.

Bounded factual scouting and review feedback alone are not plan authorship.
Drafting or revising the assessed plan or implementation is authorship. When a
reviewer becomes a Writer, replace its independent coverage with a non-authoring
instance. Do not require a single plan drafter or a fixed-size Task Operator pool.

These rules also cover Coordinator-authored work. The Coordinator's own review
does not count as independent assessment, and acceptance waits for the required
non-authoring assessments or an eligible closure of an already assessed issue.

For a first assessment, provide original requirements, the exact plan/candidate
and factual evidence without peer verdicts or proposed acceptance conclusions.
After independent views are returned, compare findings and resolve disagreements.
Correction reviewers must receive the actual source findings and prior basis;
independence does not mean hiding the defect they are checking. Keep instructions
complete for each assignment, retrieve truncated required text or reports, and
never infer missing conclusions from a summary or completion notification.

Evaluator assignments keep project files read-only. They may inspect and perform
supported non-mutating checks within their assignment. Request corrections or
checks requiring project changes or coordinated mutable outputs through the
result channel. Native descendants are allowed where the role and tool support
them. Reuse existing criterion and evidence semantics, but define these scoped
collaboration assignments separately: the existing
[`goal-evaluator`](../../plugins/aquarium/skills/goal-evaluator/SKILL.md) forbids
check execution and nested dispatch and must not be invoked unchanged to claim
those capabilities. Preserve its default contract for existing callers.

## Planning, implementation and acceptance

### First assessments and review participation

Record the Task's risk and basis in its existing plan. A standard Task uses the
Task Evaluator and one distinct non-authoring Task Operator for its first plan
and result assessments. An elevated Task uses the Task Evaluator and two such
Task Operators with complementary concerns. Elevate when the change affects shared
contracts, persisted data, authorization, concurrency, recovery, process lifecycle,
material architecture/performance obligations or other high-consequence behavior,
or when its impact cannot yet be bounded. Recheck against actual delivery and
raise coverage for previously unassessed work. File count and elapsed time alone
do not decide risk; lower it only when the triggering premise is disproved.

Every Task still receives the narrow Epic-context plan assessment and its first
Epic-context completion assessment. Final assembled-Epic review uses the Epic
Evaluator and at least two fresh non-authoring Task Operators. These are first
assessments, not panels to recall for every correction. A larger expressly
required team remains required; another optional review must answer a concrete
unresolved concern. Sharing a model does not remove instance independence.

For every Task:

1. Start the Task team and recover the original outcome, criteria, non-goals and
   dependencies. Prepare a plan covering design, earlier outputs, downstream
   contracts, material risks, checks and affected docs. Include necessary support
   work and its stopping condition; create Milestones only where an actual
   delivery dependency or review boundary needs one.
2. Obtain independent Task plan assessments from the panel above. Resolve required
   findings, then obtain the Epic Evaluator's direction/continuity/handoff
   assessment of that plan. A clarification within the reviewed direction may
   be carried as a bounded implementation instruction; material design or premise
   changes need affected reassessment. Preserve unresolved disagreements.
3. The Coordinator checks the concise reports and current applicability, handles
   scope or authority exceptions and assigns the sole Writer. Both plan scopes
   must be satisfied before implementation; this adds no routine third plan review.
4. The Writer implements, self-verifies and documents the authorized result.
   Report actual changes, checks, gaps and deviations before expanding work.
5. Freeze the candidate at a meaningful result boundary. Obtain the first Task
   result assessments. On the first Task-completion candidate, the Epic Evaluator
   and Coordinator may inspect it concurrently, alongside already-required tests
   that can run without conflicting writes or resources. Each assessment still
   waits for evidence it needs. Keep initial conclusions independent and collect
   required findings and failures into one correction set.
6. Classify the complete issue set under the correction policy below. Resolve
   current defects and evidence gaps; record eligible deferrals. Apply only the
   necessary tests, closures and affected assessments. Local corrections do not
   automatically recall the Epic Evaluator or restart a full review.
7. Establish final-candidate readiness from the actual first assessments, current
   evidence, valid closures/applicability decisions and the Coordinator's
   substantive product review. No due criterion or material disagreement may
   remain unresolved. An unchanged opinion needs no acknowledgement round.
8. Include authorized lifecycle/record edits before final verification where
   practical, apply the same delta rules to late edits, and record delegated
   acceptance. The Coordinator takes the Writer role, stages only the accepted
   scope and creates the authorized Task commit. Inspect its actual bytes, hooks
   and remaining worktree; refresh only guarantees those effects invalidate.
9. Complete the Task goal after required evidence, acceptance, commit inspection
   and Podway finalization when applicable. Preserve the handoff, safely retire
   owned helpers and continue to the next eligible Task.

Each Task has distinct plan and result checkpoints. One plan may cover its
Milestones; one result assessment may cover a Milestone that also completes the
Task. Routine bookkeeping is not a new delivery boundary. Do not accumulate all
Tasks into one final implementation commit or close a goal merely to advance.

Follow the role-specific context boundaries above. The Coordinator receives concise
verdicts, plan identity, important decisions, material exceptions and source
locations. Use existing plan/result channels and project documentation; no
separate handoff document or new state store is required. Fetch relevant source
details when a concrete concern needs them. These plan-stage boundaries do not
reduce the required completion assessments or the Coordinator's personal final
project and product review.

The reviewed Task plan identifies meaningful intermediate Milestones; none are
required for a Task that is one delivery unit. At an intermediate boundary,
perform the result assessment and finding resolution, then let the Coordinator
decide continuation. Keep the Task goal active. The Task-completion Epic approval,
final acceptance and completion commit in steps 6 through 9 apply to the complete Task
candidate. Material cross-Task changes still need Epic assessment. Internal
Milestone reviews do not themselves execute an additional technical-review route
or consume its provider ordinal; checkpoint commits need their own authority.

### Verdicts and issue resolution

State phase, scope, exact plan or candidate, evidence and concrete reasons with
`pass`, `rework` or `evidence-needed`. Distinguish required corrections and
mandatory evidence gaps from optional preferences. A plan needs phase-appropriate
evidence, not completed implementation. Preserve original criterion states,
including unverified future obligations and unassessed parts of compound criteria.

Use `rework` for an addition shown to violate the scope or necessity criteria,
even when required features work. Identify the violated requirement or scope
boundary and the unnecessary behavior or burden; a preference for a smaller
design is insufficient.
Apply this rule to additions requested by reviewers or the Coordinator as well
as those proposed by a Task Operator. A mandatory correction needs a source or
contract basis, a reachable problem and its impact if left unchanged, with a
bounded correction direction. Assess result evidence independently of the plan;
post-hoc documentation does not supply missing scope authority. Optional
suggestions remain non-blocking, and a sufficient candidate may receive `pass`
without more work. Missing evidence for a due requirement remains a gap.

Respect the
[ordinary v3](../../plugins/aquarium/references/ordinary-agent-orchestration.md)
distinction between a scoped checkpoint and whole-goal passage. A Task-boundary
Epic approval is a passing assessment of that scope; it is not a global Epic
`pass`. Use the existing scoped checkpoint representation where applicable and
require whole-Epic passage at final integration.

When the Coordinator finds a concern, provide expected behavior, observed
evidence, affected scope and reasoning to the relevant Evaluator; include both
when their scopes overlap. Read their reassessment. Decide whether readiness
requires correction, evidence or no change using original requirements and actual
behavior. Neither role's seniority nor an earlier verdict resolves the concern.
Keep original findings and concise dispositions; do not invent agreement or
convert optional redesign into a mandatory correction.

Separate the original Evaluator verdict, a finding's verified closure and the
current conditions for progression. Keep the original report unchanged. The
Coordinator may record an eligible local closure and an evidence-backed
applicability decision under the policy below; that is not a new Evaluator pass,
an independent review or authority to override an actual objection. Other
corrections receive the affected independent assessment, not automatic sequential
Task and Epic reapproval.

For plan revisions, preserve first assessments and check the cumulative change.
Editorial corrections and bounded instructions within an assessed direction use
local applicability. Changes to detailed feasibility or verification need Task
reassessment; changes to Epic direction, dependencies or handoff contracts also
need Epic reassessment. The Coordinator cannot invent a missing first plan pass
or treat new unassessed work as a correction.

For unresolved substantive disagreement, seek focused investigation, reproduction
or another non-authoring assessment. Keep the required Evaluators engaged; do
not replace one to obtain approval, use majority voting or use a round count as
proof of correctness. Do not commit an affected completion candidate with a
material unresolved acceptance concern. Ask the user only for a missing product,
scope or authority decision that actually requires them.

Pause affected implementation when findings materially change reviewed design,
interfaces, dependencies, requirement coverage or verification. Revise and
independently reassess that plan scope before the Coordinator resumes it.
Ordinary corrections preserving the reviewed direction need no plan restart.

## Failure triage and adaptive correction

This section owns Squad's correction policy for both native and Herdr/mixed
execution. Implement it through shared references and existing reports, then
connect it to the selected Procedure, recovery and commit consumers. It does not
change existing Handler/Validator callers by implication. Reuse the meanings in
[finding disposition](../../plugins/aquarium/references/finding-disposition.md)
and [review incident handling](../../plugins/aquarium/references/review-contract.md#reviewer-instruction-deviations).

### Decide what must be fixed now

A test failure or change request starts investigation, not an automatic full
rerun. Establish the exact candidate, failing property, applicable requirement,
actual impact and cause. Preserve the original failure and reported severity;
severity, validity, correction scope and review depth are separate decisions.

| Classification | Required disposition |
| --- | --- |
| Current correctness, acceptance, security/privacy, data integrity, required reliability or performance defect | Resolve promptly before accepting the affected Task or advancing dependent work. Preserve its effective priority; a small deterministic repair may still use local verification. Escalate uncovered effects instead of editing another repository or silently deferring a blocker. |
| Missing mandatory evidence or unbounded failure | Keep the obligation open, investigate its cause and obtain the needed evidence. A passing unrelated test or reviewer agreement cannot close it. |
| Obsolete expectation, editorial error or established execution incident | Restore the approved meaning or execution condition and follow the bounded routes below. Do not presume that every mismatch is merely a stale test. |
| Independent future improvement or optional hardening | Record an actionable entry in the repository's canonical deferred-feedback owner with source, reason, impact and re-entry condition. Epic-sized work belongs in its TODO candidate owner, without automatic roadmap adoption. No required current criterion may depend on the deferred work. |
| Invalid finding or preference with no established defect | Explain the disposition with evidence. No repair or clean-report rerun is required; optional advice stays nonblocking. |

A missing deferred-work owner needs the existing proposal/approval path, not an
invented second backlog. Deduplicate existing entries without erasing provenance.
Defer unrelated work instead of repairing it merely to make a gate green, but a
failure in a mandatory gate still needs an applicable repository/user-authorized
baseline disposition or waiver. Do not quietly skip, weaken, delete or relabel a
failing test. Unexplained flakes remain unresolved; passing reruns alone prove
neither an environment cause nor a pre-existing failure.

### Separate test scope from review scope

The Coordinator records the correction basis, exact delta, affected consumers and
criteria, retained evidence, required checks, review scope/participants and next
owner in the existing result or handoff. A short reason plus source references is
enough. Judge the cumulative delta from each evidence source, not just the latest
edit. Assess mixed deltas together where they interact; an eligible prose change
cannot hide an accompanying contract change.

| Correction | Checks | Additional assessment |
| --- | --- | --- |
| Meaning-preserving prose/comment/format correction | Read back the change and run applicable document/link/integrity checks. No product tests solely for this delta. | Coordinator closure when the relevant first assessment is complete and eligibility is established; no routine TE/EE or provider recall. |
| Stale expected display string or bounded snapshot field | Establish the intended value from an approved requirement/decision/contract or prior independent assessment, then run referring tests and any previously unexecuted required cases. Inputs, assertion logic and strength remain unchanged. | Eligible local closure; a mismatch alone never authorizes changing the expected result. |
| Other isolated repair of an already approved requirement | Direct deterministic regression checks of the changed behavior and failure paths, plus affected mandatory checks. | Use `local-verified-fix` only when direct verification establishes the effect without new design, contract, security or concurrency judgment. Otherwise obtain focused Task assessment. |
| Behavioral correction requiring bounded judgment | Exercise the changed behavior, direct consumers and relevant integration paths. | TE plus one non-authoring Task Operator on the correction and its impact. A nonbehavioral change that fails local eligibility may use TE-only delta assessment. |
| Shared contract, security, data, lifecycle, concurrency or other elevated correction | Relevant contract/consumer/failure-path checks and required broader gates. | TE plus two non-authoring Task Operators for the affected guarantees; include EE only for cross-Task effects or its own unresolved finding. Depth can increase without restarting unrelated review. |
| Missing run, wrong working directory, truncated report or recoverable tool failure | Recover the same result/operation or execute the missing checks on the right candidate. | Repair the affected evidence guarantee. No new implementation review solely because execution or retrieval failed; changed product/harness bytes are classified separately. |
| Changed design/acceptance premise or impact still unbounded after focused investigation | Reassess the relevant plan and broaden tests to establish the new basis. | Full reassessment of the affected delivery boundary, Task or assembled Epic. Repetition count alone is not a trigger. |

Strings used as API/error codes, authorization instructions, configuration keys,
numeric/boolean expectations, data semantics and normative workflow instructions
are not editorial corrections. Changing fixtures, mocks, matchers, assertions,
timeouts or selection can change what a test proves even when production code is
untouched. Check the intended behavior independently and assess affected consumers.
Test-only location does not establish harmlessness or require full review by itself.

Local closure requires the relevant substantive first assessments, a finite
understood delta, sufficient direct checks and no unresolved substantive objection.
It never replaces missing reviewer coverage or first assessment of new delivery.
For Coordinator-authored corrections, obtain focused non-authoring confirmation
when closure needs semantic judgment; mechanically established nonbehavioral fixes
need no new framework. A missing optional mechanical helper is not a blocker or
an instruction to build one. The original finding owner participates when its
judgment remains unresolved, without recalling every prior reviewer.

EE re-engagement follows cross-Task contracts, dependencies, downstream premises,
Epic scope or its outstanding findings. Record a supported no-cross-Task-impact
basis when none changed. If uncertain, ask the EE about that scope only. A required
new independent assessment cannot be replaced by Coordinator agreement. The EE
acts as primary assessor for Epic integration/closeout corrections; do not recall
retired TEs unless a Task's completion is actually reopened.

### Reuse evidence without hiding gaps

Use the target repository's real test commands, inputs, layers and mandatory
completion/release gates. Record their applicable selection and conditions in the
existing plan or verification profile. A temporary run-directory script cannot
invent a standing gate. Prefer focused checks while iterating; do not mandate two
whole-suite runs or a new full suite for every Task merely because Squad is used.

A prior result is reusable only for obligations the cumulative delta leaves
unchanged under comparable commands, coverage, dependencies, inputs and environment.
Verify every changed behavior and complete mandatory cases left unexecuted by a
prior fail-fast run. When the repository permits reuse, final verification can
combine an applicable reviewed/tested basis with checks for the later delta and
its consumers. Record the sources and limits; never call that composition a fresh
whole-suite run. An exact-final-candidate gate required by the repository still
runs as required. A starting baseline alone proves no new behavior.

Broaden to the relevant complete gate when a repository rule requires it, when
impact/consumers or execution comparability remain unknown, or when changes to
shared behavior, fixtures, selection, environment or verification premises
invalidate the prior coverage. Contract or risk-area changes require direct
consumer and failure-path evidence; bound the valid remainder or execute the
broader gate. The fact that a test failed, a report requested a change or the Git
candidate ID changed is not itself a full-test/full-review trigger. Full testing
and full review are independent choices, each needing its own basis.

Perform an assembled-Epic integration assessment even if the last Task's tests
are reusable. Reuse that execution only when candidate, inputs and coverage
include the Epic's required integration scenarios. Lifecycle edits, hooks and
closeout changes follow the same applicability rules rather than a blanket rerun.

### Correction completion and recovery

Bundle related required findings and known test failures before dispatching a
correction. Sweep equivalent instances of the established cause and affected
consumers within the authorized behavior. Repeated symptoms call for focused
root-cause diagnosis, not endless isolated patches or generic malformed-input
hardening. Broaden only on evidence. Judge readiness and failure from evidence, not a fixed round count. Unused review
budget does not justify another operation.

Stop correction when its required property and affected criteria are established.
Record deferred and rejected findings separately from repaired ones. Preserve
original verdicts, current closures, applicability, candidate/check identities,
remaining grants and pending operations across compaction, replacement and resume.
A corrected candidate may be accepted from its original assessments plus eligible
verified deltas; never rewrite a historical verdict or claim those deltas received
an assessment that did not occur. Unknown applicability keeps the affected
obligation open. Final user acceptance and Coordinator-owned commit boundaries
remain unchanged.

## Role profiles and execution routes

Keep the Coordinator's current CLI, model and session. Resolve each operational
role independently before launching its agents:

| Role input | Execution route and configuration |
| --- | --- |
| Entire profile omitted | Native subagents of the Coordinator's current CLI, matching its current model and effort. |
| Explicit CLI and model | Herdr with the requested model and default effort `high`. |
| Explicit CLI, model and effort | Herdr with the requested model and effort. |
| Explicit profile matching the Coordinator | Herdr; matching a CLI or model does not change the selected route. |

The profile consists of CLI, model and optional effort, in that order. Require
both CLI and model for an explicit profile; do not infer a CLI from a model,
complete a partial profile without user direction or use automatic model selection. Resolve
incomplete or conflicting input before launching the affected roles. An empty
explicit profile or Task Operator list is invalid; omission selects the native default.
Preserve resolved CLI model IDs as opaque values, including any slashes inside
them; resolve ambiguous profile boundaries instead of splitting a model ID.
Only an effort omitted from an explicit profile defaults to `high`. An omitted
whole profile retains the Coordinator's current effort.

An optional `Support Operators:` pool configures support assignments only; its
omission or an empty pool requires no support launch. Without an explicit pool,
selected native factual helpers remain available under the Coordinator's normal
scope. An explicit support pool uses the same CLI/model/effort resolution and
Herdr route as other explicit profiles. It cannot fill required Task Operator
review or Evaluator roles, and an explicit Task Operator pool does not silently
supply it.
Disclose unavailable optional support before omitting it and assigning its
obligation to an authorized existing role. Do not claim the explicit profile ran;
user-required participation remains required, and no evidence obligation is waived.

Accept a common `Evaluator:` profile or scoped `Epic Evaluator:` and
`Task Evaluator:` profiles. Common and scoped Evaluator entries together are
conflicting input; do not invent override precedence. A common entry applies
the same profile to both roles. With scoped entries, an omitted role stays
native independently of the other role. `Evaluator:` is shared configuration
shorthand for Epic Evaluator and Task Evaluator, not an additional role. Use the
scoped names in new examples. Accept one or more explicit `Task Operators:`
profiles; a singular `Task Operator:` entry denotes a one-profile pool. Use these
canonical keys in new Squad invocations, examples and generated assignments.

```text
Target Epic: EPIC-017

Task Evaluator: codex / gpt 6.1 sol / high

Task Operators:
- opencode / glm 5.3 / max
```

With a Codex Coordinator, this example uses a native Codex Epic Evaluator, a
Herdr Codex Task Evaluator and Herdr opencode Task Operators. The Epic Evaluator
matches the Coordinator's current model and effort, which need not match the
explicit Task profile. These names are requested inputs, not availability claims.

```text
Target Epic: EPIC-017

Epic Evaluator: agy / gemini 4 argon / high
Task Evaluator: agy / gemini 4 argon / high
```

This example assigns both Evaluator roles to Herdr while omitted Task Operators use
native agents. Omitting every role profile gives all-native delivery and requires
no Herdr installation or readiness check. Inspect the execution routes needed by
all resolved roles, including omitted native roles in mixed teams, and any
optional helpers actually selected.

### Role instances and topology

The Coordinator directly manages distinct Epic and Task Evaluator instances,
whether native or Herdr. A common Evaluator profile is shorthand for identical
configuration of two roles, not one assessment or an Epic-parent/Task-child relay.
Keep the Epic role's context across the Epic and use a dedicated context for
each Task. Their actual assessments, scope and configuration remain distinct.
No role requires nested spawning; useful descendants may assist within supported
capabilities without replacing the required directly managed Evaluators.

A profile is not an instance. Task Operators may share a profile but must use
separate authoring and non-authoring instances. If Task Operator profiles are
omitted, required delivery and independent Task Operator reviews use native instances. If a pool is
explicitly supplied, those assignments, including plan, result and integration
reviews, use its profiles through Herdr. Not every profile must participate in
every assignment. The Coordinator's native helpers may add findings; they do not
replace required Task Operator or Evaluator coverage from the configured route.

Resolve and disclose each role's route and configuration in the execution plan.
Preserve supplied profiles and omitted roles through design-return and recovery.
Omitted roles resolve against the current Coordinator in the new or resumed
session; retain earlier configuration records and disclose changed inheritance.
This default does not freeze an earlier Coordinator's model or effort. Recheck
capabilities on resume. Changing a selected route or explicit profile requires
user direction; disclosure alone does not authorize substitution after failure.
Recover or replace an instance on its existing route/profile under current
authority while retaining pending findings.
Another already approved Task Operator profile may handle suitable work; obtain user
direction when the required team configuration itself must change. Finish
unaffected preparation when one route is unavailable.

Role profiles do not configure separately selected Mulgae, Subagent Review or
Herdr Review operations. Their native selection and authority remain distinct.

### Independence and operational differences

Native and Herdr instances follow the same non-authorship and original-source
assessment rules. A separate Herdr CLI session provides a distinct process,
conversation and lifecycle; it can outlive the Coordinator and needs explicit
recovery and cleanup. It does not establish model diversity, uncontaminated
context, OS isolation or correctness. Apply actual supported permission controls
and disclose context inheritance or enforcement limitations on either route.
Omitted profiles select native collaboration for convenience; explicit profiles
allow a different model or a deliberately separate same-CLI session.

## Native configuration and lifecycle

Use actual subagent facilities of the Coordinator's current CLI for native roles.
Discover capability through existing paired skills, complete relevant help,
configuration and startup observations. Use a bounded smoke check only for a
concrete unresolved prerequisite within current authority. Do not write probe
programs, permission-enforcement harnesses or a universal CLI adapter to establish
ordinary readiness. Report unsupported capabilities and unconfirmed observations
separately; a required safety/control gap still blocks the affected action.
Native roles and the Coordinator's own native helpers, including selected support
assignments, match the Coordinator's current model and effort through supported
inheritance or explicit matching controls. Descendants assigned that configuration follow the same rule. Do not
select per-role alternatives or change the Coordinator's configuration.
Matching configuration does not require copying its conversation.

Verify actual creation, result retrieval, continuation, termination, context,
configuration and permission capabilities for roles selected as native. Distinct
direct agents for native Epic/Task Evaluators and delivery/review Task Operators suffice;
nested spawning is not a prerequisite. A role that needs help can return a bounded
request to the Coordinator, which creates a direct helper and returns its findings.
Native descendants may be used within supported depth and resource limits.

Prefer fresh reviewer contexts. Disclose unavoidable conversation inheritance
and require original-source assessment. Do not describe a forked conversation
as clean context. If native execution or matching configuration is unavailable,
report the concrete limitation and finish unaffected preparation; do not
impersonate independent agents or switch the affected role to Herdr, another CLI
or an external agent manager without user direction. An explicitly configured
Herdr role does not require native agent support; unavailable optional native
helpers do not block an otherwise supported team. Private backend telemetry is not required when
supported inheritance has been applied; unavailable records remain unconfirmed.

Preserve a role's context and obligations across executions without requiring a
permanently running agent or open thread. Schedule within actual concurrency,
retained-thread and nesting limits; independent reviewers may run sequentially.
Completed, idle, stopped and closed states may differ. Use supported lifecycle
controls without assuming that an execution ending releases every limit. Do not
reduce required review counts to fit capacity.

Before releasing an execution, collect actual results, configuration, candidate,
pending operations and unresolved findings. A one-shot or replacement agent
receives original sources, current candidate, prior findings and remaining
authority. Restoring an earlier report is not a new assessment. Keep Task roles
recoverable through commit verification without occupying idle slots unnecessarily.
Free capacity through supported lifecycle controls after collecting the settled
role's results and recovery context. A role with an active or blocked operation
is not disposable; reconcile it before release or use sequential scheduling.

## Herdr configuration

Use Herdr for explicitly profiled roles, including same-CLI profiles. Evaluators
use distinct directly managed sessions even when they share a common profile.
Task Operators use independent instances from the supplied pool. CLI-native descendants
may assist where supported; they do not replace the required top-level sessions.
Descendants inherit scope, permission, Writer and independence restrictions and
receive no extra acceptance or commit authority. Preserve their actual reports
and configuration, without assuming a child matched its parent's settings.

### Model and effort resolution

For an explicit profile, default an omitted effort to `high`; retain the effort
included in a chosen example profile. Resolve display names to installed CLI
model IDs and supported effort controls before launch. Effort may be a separate option or part
of model selection. Read the current native contract; do not invent universal
launch flags, rely on automatic model choice or treat a prose request as a native
configuration change.

Apply the requested profile to every assigned instance and relevant descendant.
Inspect available public launch or configuration information. On launch, resume
and Writer transfer, reapply supported controls as needed and check their actual
model, effort and permission effect; resume may restore different defaults.
Record an available confirmation or a limitation. Assignment-only read-only rules
are not OS isolation. If an actually required restriction cannot be established,
leave the affected operation blocked rather than building enforcement machinery. Report unavailable
models, unsupported efforts and observed mismatches. The default `high` is part
of a resolved explicit profile. Changing its model, requested or defaulted effort,
or execution route requires user direction; disclosure alone is insufficient.
Keep the Coordinator's session unchanged. Another already approved
Task Operator profile may handle suitable work, but a change to the required team
configuration needs user direction. Keep version-specific launch and recovery
recipes in the current paired tool/native contract, not copied Pilot commands.
Do not edit user-global defaults, trust settings or hooks to satisfy a role unless
that exact effect is separately authorized. Report an observed unexpected host
mutation; blanket home-configuration snapshots or audits are not a Squad step.

The following are user-supplied input examples. They are not verified availability
claims, required execution coverage or a fixed provider allowlist.

| CLI | Model display name | Effort |
| --- | --- | --- |
| codex | gpt 6.1 sol | high |
| claude | opus 5.5 | extra high |
| agy | gemini 4 argon | high |
| agy | opus 5.5 | high |
| grok | grok 4.7 | high |
| cursor agent | grok 4.7 | high |
| opencode | glm 5.3 | max |

Herdr's native support and the installed CLI's capabilities determine whether a
new CLI can participate. Do not add an Aquarium provider allowlist or use raw
terminal allocation to bypass unsupported agent execution. Using the same model
through different CLIs does not establish model diversity.

### Herdr ownership

Load the installed Herdr skill and use its supported execution, caller identity,
layout, input, output-reading and permission controls. Follow the installed
skill's current layout rules and applicable user/repository instructions.
The current contract keeps the main tab unsplit; allocate helpers through
`dev-herdr --subagent-pane <name> --cwd "$PWD"`, read `.result.pane.pane_id`, and
keep nested helpers with the original main. Use verified caller recovery and
returned session context; never infer identities from UI focus or ask the user
to discover pane IDs. Allocation failure does not authorize raw layout fallback.

Keep role contexts recoverable through their Task or Epic obligations. Collect
results and configuration before closing helpers by their verified identities.
Preserve the Coordinator, the Epic Evaluator and tabs still used by other agents
or the user. A pane disappearing does not prove background work stopped. A cleanup
delay alone does not invalidate a verified Task; uncertain modifying work prevents
another Writer from starting.

Inspect a startup or runtime approval/question UI through the same known agent.
Keep the original operation and Writer state recoverable; do not resubmit work,
create a replacement or infer completion merely because a pane is blocked.
Use only the installed Herdr skill's supported permission mechanisms within
actual user authority. When that contract requires a user answer, report the
concrete requested action and wait for it; the execution envelope cannot
override that requirement. Prefer supported bounded launch permissions for
already authorized work. Do not change host configuration or grant broader
access to suppress prompts, and do not start another Writer while blocked
modifying activity remains uncertain.

## Supervision and progress

Use supported native lifecycle observations, completion notifications and result
channels for routine supervision. Avoid routine console tails and repeated
transcript reads when those observations suffice. Choose bounded or yielding
waits that return control in time to service other pending participants; retain
the same operation handle across waits. Set observation intervals from the work's
expected duration and the route's detection limits, without fixed line counts,
retry quotas or an automatic cancellation deadline. Paired-tool operations keep
their installed skill's waiting and recovery contract, without a competing
observation loop.

Keep known assignments, handles, pending requests and next owners recoverable
through existing runtime records. For Herdr, retain the returned session and pane
identity as well as the agent name so an exited agent's output remains locatable.
An agent needing a Coordinator decision, another role's output or an unavailable
capability returns an actionable request through a supported channel. If only a
returned turn exposes the request, end that turn instead of sleeping or polling
for the Coordinator. Preserve supported native messaging and role interactions;
no new mailbox or heartbeat protocol is required.

Inspect relevant output when state is blocked or unknown, submission or completion
is uncertain, a wait expires without explained progress, an agent exits, or the
route's documented detection limits require it. A harness-paused approval or
question UI may prevent the agent from reporting its own blocker. Inspect enough
of the current screen or unwrapped output to identify the complete request and
follow the existing permission contract. A short recent excerpt may suffice for
triage, but neither a fixed tail nor unchanged lifecycle state rules out a missed
dialog. Do not let waiting on one participant hide another participant's request
or completion.

Meaningful progress is a checkable advance in an approved product outcome or a
justified reduction in uncertainty, such as a resolved request, delivered
Milestone, relevant check result or established failure cause. Apply the
purpose-bound support-work rule when machinery grows without such progress. Console
activity and heartbeats establish neither progress nor correctness. Read-only
analysis may expose no mid-turn progress; assess it against expected duration
and available diagnostics without treating silence alone as failure. Worktree
inspection during another Writer's work must be non-mutating.

Do not send terminal status prompts into an active or uncertain turn: they may
queue another turn or change the current work. Use read-only observation unless
the native contract supports an interaction that is safe for the active turn.
Recover the existing operation before resubmission. After investigation, choose
continued observation with a stated basis and next check, supported recovery
within existing authority, or a report of the unresolved capability or authority
gap. Revisit repeated unexplained overruns instead of treating uncertainty as
progress. Native cancellation, interruption and recovery still follow the tool's
contract and existing authority; elapsed time supplies no new grant.

## Writer, result and commit boundaries

### One active Writer

The Coordinator assigns the sole Writer for shared project files, including
source, tests, tracked docs, generated files and commands that rewrite them.
Normally a Task Operator writes; the Coordinator may take the role when useful.
A child does not inherit Writer authority merely because its parent holds it.
Parent and child cannot write concurrently. The Coordinator does not edit project
files or the Git index while another Writer is active.

Use supported native read-only modes or tool restrictions where available.
When separate per-agent enforcement is unavailable, disclose that read-only is
an assignment boundary; do not claim technical isolation or change global/session
permissions to simulate it. Preserve permitted report output and coordination.

For transfer, finish or safely stop modifying operations and descendants, read
the current Writer's actual changes, decisions, pending work and checks, and
establish that modifying work has stopped. Revoke or end former writing access
through supported controls as applicable before granting the next bounded
assignment. The next Writer inspects the handoff and actual worktree. A report
alone does not transfer authority; uncertain activity blocks transfer.
Account for modifying background commands, descendants and pending writes in the
handoff, and establish their settlement through supported observations before
Writer transfer or candidate freeze. A settled parent turn, vanished pane,
stable diff or absent Git lock alone does not establish that all writes stopped.

Routine build outputs and separate temporary reports are permitted. Coordinate
checks sharing mutable outputs. Freeze the candidate for completion reviews;
formatters and tests must not rewrite it during assessment.

### Results and instruction authority

Native agents return through provenance-preserving harness channels. Herdr agents
publish normal results in their own consoles, which the Coordinator reads through
supported output retrieval. Parents collect descendant findings and return the
actual supporting results with their synthesis. No agent may inject results,
questions, completion markers or permission requests into the Coordinator's
interactive prompt, input buffer, stdin or equivalent user channel, directly or
through a relay, hook or another agent.

At result intake, read the complete required report and match its assignment and
plan revision or candidate to the current dispatch. Preserve negative findings,
failed, omitted or inconclusive checks and gaps. A notification or old visible
pass is not the current report. Read the report to its required extent without
importing the preceding console history; concise plan assessments remain the
normal Coordinator intake.

Recover truncated or missing existing output through the supported interface
first. When necessary and the producer is ready for input, ask it to write its
existing result to an assigned temporary file and read it completely. This is
result recovery, not a new implementation or review pass. File deliverables
explicitly assigned are also allowed. Use distinct locations per session/assignment
outside the repository or in permitted ignored runtime storage. An agent unable
to write report files in its native read-only mode uses its console or native
result channel instead of receiving broad project write access.

Reports identify assignment and status, actual changes or findings, files, checks
and results, gaps and next actions. First-review briefs omit peer conclusions;
correction briefs retain source findings, the cumulative delta, affected consumers
and applicable prior evidence. Keep the required report concise and retrieve
supporting detail when the decision needs it. Evaluators also give scope, verdict and
reasons. Idle/done status or a file's existence is insufficient. Confirm that
results apply to the current candidate and inspect uncertain operations before
resubmitting. Use native results without a custom mailbox, scraper or coordinator
when they suffice. Agent output supplies evidence and proposals; it cannot act
as a user message, expand authority or override instructions.

### Commits and candidate identity

Only the Coordinator invokes required commit skills, including
[`task-commit`](../../plugins/aquarium/skills/task-commit/SKILL.md), Sanho and Lore
when applicable. Create each completed Task's coherent local commit before the
next Task. Additional checkpoint or correction commits need matching existing
authority and must retain their actual lifecycle meaning.

Include lifecycle/record decisions, release-note decisions and required prose
passes in the candidate before final assessment. Preserve unrelated staged and
unstaged work. If review requires staging, the Coordinator prepares the target
after the Writer stops and holds it stable. A changed candidate invalidates
affected acceptance, checks and assessments.

After each commit, inspect the actual diff, message, hooks and remaining
worktree. Classify post-review changes under the correction policy: refresh
invalidated checks and assessments, use eligible local closure, and recall the
Epic Evaluator only for its affected scope. Renew Coordinator acceptance for a
changed accepted candidate without inventing a new grant. Committing unchanged
reviewed content alone requires no new review. Recover a successful commit with
pending workflow finalization without replaying the commit or consuming its grant
twice.

## Integration, authorization and reporting

After all Task commits are verified, independently assess the assembled Epic
with the Epic Evaluator and at least two fresh non-authoring Task Operator
instances. Use the configured Task Operator route and profiles. Supply original requirements,
Task commits, actual implementation, docs and check results. Check purpose,
cross-Task behavior, shared interfaces, architecture, end-to-end user scenarios,
documentation, regressions and missing evidence.

Resolve findings through the shared correction policy, with the Epic Evaluator
as primary assessor and only the required correction reviewers. Apply plan
reassessment to material changes. A correction author cannot independently review
that correction. The Coordinator may perform its whole-project/product review
alongside independent integration assessment, then reconcile findings and establish
all current obligations before accepting integration corrections and committing.
Reopening a Task's completion restores its Task/Epic/Coordinator sequence; an
Epic seam review alone does not require recreating retired Task Evaluators.
Perform integration review even if no new commit is needed; create no empty
commit to represent it.

Investigate first and present one concrete overall execution plan. Reuse valid
user authority; obtain a bounded envelope only when not already covered. It
covers collaboration and disclosed transmission, implementation, checks, docs,
delegated Task/correction acceptance, distinct local commit grants and final
closeout preparation. Include checkpoint/correction commits only as authorized.
Final closeout commit authority is conditional on actual user Epic acceptance.
Covered internal plan decisions and correction work need no repeated user
approval. Supported permission delegation never overrides platform restrictions.

Uncovered scope expansion, destructive effects, host installation/configuration,
other repositories, push, deployment and publication require separate authority.
If blocked, finish unaffected work and identify the concrete missing decision.
Preserve the active Task and remaining obligations instead of marking it complete.

Prepare repository-required closeout changes and review the actual candidate
with the Epic Evaluator and Coordinator before asking once for overall user
acceptance. After acceptance, confirm that the reviewed scope still matches,
apply any already authorized closeout commit and verify final state. Substantive
changes follow the correction policy; unchanged content needs no redundant commit
question. No required closeout diff means no manufactured commit.

If the user requests closeout-only record changes, revise that candidate within
the applicable closeout lifecycle and refresh affected checks. Apply local closure
or affected Epic assessment according to the correction policy, then present the
revised candidate for actual acceptance. If the request changes
validated implementation, settle the active closeout session through its
authorized native lifecycle before returning to owned correction and integration;
do not nest incompatible sessions or reuse `validated-closeout` for changed
implementation. Reopened Task completion restores its Task/Epic/Coordinator
sequence. Apply the current envelope or obtain only missing authority.

Rejection or stopping does not establish success or consume the conditional
closeout commit grant. Preserve unfinished goals, findings and pending effects;
use the existing stopped-boundary assessment and actual user decision when a
stopped closeout is requested. Do not resume implementation solely to tidy a
stopped report or mark the Epic complete. A materially revised final candidate
requires actual acceptance of that candidate.

Final reporting covers delivered behavior, checks and limitations, docs, local
commits, each Task's original assessments with current closures/applicability and
Coordinator acceptance, integration outcome, deferred work and substantive
disagreements with their dispositions. Report material support work and its
necessity when it affected delivery, without a mandatory script-size ledger.
Record user acceptance only after it occurs.

Include a concise agent configuration table by role and Task/Epic scope, execution
route, CLI, requested profile or omitted-profile default, applied model selection
and effort, available observed confirmation and unconfirmed information. Include
the Coordinator's available current settings, relevant permission limitations and
selected Support Operators; do not infer hidden telemetry or copy credentials. For
native roles, state the Coordinator's available settings and each role's applied
inheritance or matching controls. Include implementation, review and final-review
helpers, descendants, replacements and configuration
changes; group matching instances by scope/count when useful. Collect records
before session closure, without assuming children matched their parents or
requiring private telemetry. Update the report for any closeout participants.

Keep durable technical decisions and concise change history in existing project
docs. Keep runtime handoffs and configuration observations in existing permitted
result storage, with enough context for recovery; do not track full transcripts
or create a parallel state system. Keep progress updates focused on outcomes,
important decisions and blockers.

## Integration and compatibility approach

Reuse the existing
[adaptive contracts](../../plugins/aquarium/references/adaptive-procedures.md),
[mapped execution](../../plugins/aquarium/references/adaptive-execution.md),
[review handoff](../../plugins/aquarium/references/review-result-handoff.md),
[review routing](../../plugins/aquarium/references/review-routing-contract.md),
and [evidence residency](../../plugins/aquarium/references/evidence-residency.md).
Use the paired native tool skills for actual operations, including Gaori checks
and Herdr execution. Do not introduce another engine, central registry or schema
version merely to rename scoped roles.

Podway is enabled by default, with existing explicit pre-session opt-out and
in-progress stop/recovery rules preserved. On the managed path, reuse selected
Goal-family sessions for member and pre-validation remediation work and
Validation-family execution for assembled integration. The qualified native
adaptation keeps audit-scoped correction groups in that same Validation and
uses an adequate retained or restored Validation closeout scope for final record
work, with actual exact-candidate EE review before user acceptance. A separately
selected adequate Goal closeout remains available when fit requires it. Adapt
only where fit requires it. The actual
Coordinator alone advances the workflow. Record `aquarium:epic-squad` as the
single owner for native, Herdr and mixed execution; do not forge an
`epic-handler` handoff. Extend admission, qualification, ownership and delegated
commit consumption explicitly for this caller; preserve existing caller behavior
and immutable sources. A mere entrypoint description is not working integration.

Podway's existing Procedure capabilities are the implementation baseline; this
design requires no Podway engine, CLI or API extension. New-owner definitions,
bindings, admission, assessment and commit consumers belong to Aquarium. Preserve
the established source/version reference mappings and retained binding identities
when registering new callers: expanding a shared entrypoint list must not change
the expected binding for an existing admitted bundle. Qualify applicable
collaboration-owner variants where needed rather than recording `epic-handler`
to bypass a legacy owner guard. Keep installed managed copies and historical
snapshots intact. Verify old-bundle resume alongside new-owner execution.

### Roadmap, Procedure and assignments

The roadmap defines product Tasks and their dependencies. A Procedure defines
execution and assessment boundaries for the current work unit. Aquarium maps
those boundaries to bounded agent assignments. None of these is a second project
manager, and one node need not correspond to one agent or one roadmap Task.

| Layer | Owner and responsibility |
| --- | --- |
| Epic sequencing and product judgment | Aquarium Coordinator, using canonical requirements, roadmap dependencies, authority and actual results. |
| Current work-unit state | Podway's immutable Procedure, single active attempt, typed items, declared decisions/rework and revision fences. Podway does not execute agents or judge semantic truth. |
| Node-to-role mapping | Aquarium's qualified binding and existing ordinary assignments: role, scope, effects, due capabilities, evidence and consuming decision. |
| Agent execution and tests | The selected native harness or Herdr route, paired tools and repository commands. |

Use one Goal-family session per active member or pre-validation remediation
work unit and one Validation-family session for assembled-Epic assessment,
intermediate audit-scoped correction groups and adequate final closeout. This is
a qualified template-fit adaptation, not an explicit topology acceptance by the
user. If Task completion truly reopens, settle active Validation before the
Task-owned remediation Goal and restore its Task/EE/Coordinator sequence; then
restore the audit in an adequately qualified successor Validation. A separately
selected adequate Goal may own closeout when needed, after settling Validation.
Keep actual final-candidate EE and Coordinator review, user acceptance and each
distinct grant due on either topology. Do not keep an active parent Epic session
with nested Task sessions in the same worktree. EE continuity
belongs to Aquarium and spans successive sessions; TE and delivery/review contexts
belong to the current Task. Support assignments have only their useful assignment
lifetime. Reuse approved successor/finalization contracts without making an old
session's successful result apply automatically to a new Task.

Prefer an adequate existing Squad definition. Task IDs, requirements, candidate
references and profile selections are assignment data unless they actually change
the source definition. Adapt or compose only for a missing required boundary or
route, qualify the exact source and binding, and retain the self-contained bundle
before start. Integrate suitability with the due plan assessment when its coverage
permits. No per-Task graph generation or fresh Procedure evaluator is required for
unchanged adequate reuse. Additional helpers do not require a new graph.

### Node boundaries and dispatch

Squad-owned definitions must expose planning readiness before implementation,
candidate assessment, correction routing and finalization through qualified
Action/Decision boundaries. Do not bury all control inside the legacy
`complete-work` Action. Reuse suitable existing fragments and capability meanings;
keep legacy Goal definitions and running snapshots intact. The stage names below
are design meanings, not mandatory native node IDs or an executable YAML schema.

| Stage | Assignment and evidence | Coordinator progression |
| --- | --- | --- |
| Prepare Task plan | Authoring Task Operator; optional factual support; original requirements, plan revision, risk and necessary support work. | Enter independent plan assessment; no implementation authority yet. |
| Assess Task plan | TE and the first-assessment panel, then scoped EE direction/continuity/handoff assessment. | Proceed only with both plan scopes satisfied; use declared affected rework for an unresolved plan defect. |
| Deliver work | Sole Writer performs implementation, self-verification and docs; optional isolated support checks. | Require the actual handoff, candidate and results before result assessment. |
| Assess frozen candidate | TE, required independent Reviewers, first Task-level EE assessment and permitted checks; original reports remain separate. | Record actual positive or negative results, then classify the complete issue set. |
| Classify corrections | Coordinator records validity, present/deferred obligations, delta impact, evidence applicability, tests and needed assessment scope. | Select ready, local settlement, evidence recovery, affected rework, plan rework or a concrete blocked boundary. |
| Settle local corrections | Writer makes the bounded correction; direct checks and eligible closure, with non-authoring confirmation where required. | Proceed without a fresh full assessment only when every due obligation is covered. Mixed nonlocal obligations keep their affected route. |
| Rework affected obligations | Only the necessary Writer, tests and assessment roles, supplied cumulative delta and original findings. | Return through the declared assessment/decision path with current evidence; unbounded impact or premise changes receive broader reassessment. |
| Accept and finalize | Actual assessments plus permitted verified deltas, current required checks, Coordinator product judgment and exact authority. | Assess the current Goal, accept its exact candidate, commit through Coordinator tooling and verify native finalization. |
| Validate Epic and close out | Validation-family integration evidence and scoped correction handling, followed by closeout obligations. | Keep integration, actual user acceptance and conditional closeout effects distinct. |

One current Action may collect several independent read-only agent results and
nonconflicting checks concurrently. Aquarium dispatches and joins those operations;
Podway still has one active cursor. Preserve One Active Writer, resource scheduling,
exact candidate freeze and original producer attribution. Supporting commands,
messages and status observations are not separate mandatory graph nodes. The same
semantic graph supports native and Herdr roles through assignment routing.

Apply the shared role-name mapping to existing machine contracts with Task/Epic/support scope
in assignments. Support is a restricted execution assignment, never an additional
Evaluator or native engine role. Ordinary report delivery needs no fabricated
formal delegation receipts. Only the Coordinator records and advances the session.
A completed assessment Action means the assessment occurred: record `rework` or
`evidence-needed` truthfully, complete the Action when its delivery conditions hold,
and follow the negative Decision route. Never require a positive verdict merely
to record a negative result or treat Action completion as goal achievement.

### Assessment and record mapping

Retain original reports, producer identities, scope and exact plan/candidate
references in permitted result storage. Bind due capability fields and their
consuming decisions to the selected definition's actual native items. Neither a
report's existence nor nonempty summary text establishes criterion satisfaction.

| Record | Meaning and consumer |
| --- | --- |
| First Task plan/result assessments | Actual TE and required non-authoring Reviewer reports. A new delivery boundary cannot use correction closure instead. |
| EE Task checkpoint | Direction, prior-output use, downstream obligations and current Task contribution; future Task gaps remain visible without blocking an otherwise complete current Task. |
| Correction disposition | Source findings, original verdict, before/after candidate, authorized delta, direct checks, closure owner, deferred entries and remaining obligations. Preserve severity and source history. |
| Applicability | Why each retained assessment/check still covers its obligations, or exactly what became invalid. Unknown applicability cannot support passage. |
| Final Task basis | Complete actual Task assessments, applicable EE checkpoint, permitted closures, all due criteria and required checks on the accepted composition. Goal achievement requires zero mandatory unmet/unverified criteria for this Task and its currently due parent obligations. |
| Final Epic basis | Independent whole-Epic assessment and integration evidence. Every Task passing does not establish global Epic passage; final user acceptance remains separate. |

A single assessment slot cannot erase one of the TE/EE reports. Reference additional
original assessments through the existing handoff/evidence basis or qualify an
appropriate Squad definition. Never put a global Epic report's future gaps into a
member Task's achieved gate, count one report as several independent Reviewers,
or label internal collaboration reports as provider-review evidence.

Implement current-composition acceptance explicitly in Squad admission, qualification,
node consumers, recovery and commit handoffs. A local closure may satisfy an
already assessed obligation without another Evaluator call, but cannot fabricate
a final Evaluator verdict or bypass an outstanding independent judgment. Bind the
actual reviewed basis, permitted delta and checks to the native result fields and
conditions. Missing composition support is an implementation gap, not permission
to forge a pass or fall back to mandatory full reapproval for every correction.
Preserve existing callers' final-Evaluator and selected-provider contracts.

### Rework, invalidation and recovery

Separate missing execution evidence, retrieval/operational incidents, local fixes,
behavioral defects and changed plans. Predeclare their supported routes using the
native Procedure contract. Do not send every correction back to full implementation
or every evidence failure back to full review. Scope re-entry assignments to the
actual invalidated obligations while preserving first assessments that remain due.

Native rework creates a new attempt and applies its evidence invalidation rules.
An old native record is historical even when its underlying external artifact is
still useful. On re-entry, validate applicable original artifacts, checks and the
cumulative delta, then record the current composition with source references under
fresh fences. Do not revive stale selected items, change runtime databases or
claim an old test was rerun. Qualification must exercise both eligible reuse and
rejection of changed/unreadable/unknown evidence.

Retain exact Procedure/binding identities, original assessments, candidate and
check inputs, closures, deferred work, live operations and consumed/remaining
grants through existing recovery channels. Source updates do not rewrite an
active snapshot; genuine missing topology follows the existing consented successor
contract. Do not copy Pilot's generator/runtime system or introduce another
registry, scheduler, trust system or evidence archive.

### Additional technical review

Internal plan/result Task Operator reviews and Evaluator assessments are distinct
from selected Mulgae, Subagent Review or Herdr Review operations. Add a technical
review at approved useful boundaries rather than automatically stacking every
route on every Task. Preserve a selected route's prerequisites, team, authority,
result/ordinal and finding contracts. Two internal Task Operators do not constitute
the three-base-reviewer Subagent Review route, and Herdr team execution is not
itself `herdr-review`. No extra technical route selected means no fabricated
provider execution or review waiver. Required collaboration assessments remain due.

Define an explicit no-additional-technical-review-required state for Squad
through assignment, admission, qualification, selected Procedure definitions,
recovery and commit handoffs. Its scope is absence of an extra provider operation;
it never waives required collaboration assessments. Preserve existing callers'
route semantics. Current consumers that admit only provider routes or `waived`
must be extended for the new callers rather than supplied misleading evidence.

### Compatibility impact

This design adds one skill and aligns epic-handler's human-facing role names.
Existing Handler/Validator behavior and machine contracts are preserved. Planning
alone requires no migration or tool update. The implementing
Tasks must record any discovered forced user update, shared-contract migration
or producer change as a breaking impact before adopting it, with the concrete
migration and verification requirements. Do not edit installed plugin caches,
skills, host configuration or managed copies to make a candidate work. Candidate
installation and installed functional verification belong in the dedicated UTM
VM under the repository policy. No release version is assigned by these Epics.

## Task deliverables and acceptance

The roadmap owns the sequence and dependencies. The following sections define
what each Task must deliver and demonstrate; they do not record lifecycle state.

### TASK-147: Collaboration contracts and native readiness

- Establish the single Squad collaboration contract and native-first scope.
  Define the shared five-name vocabulary and epic-handler mapping, preserving
  existing handler behavior and generic evaluator permissions. The handler's
  single Epic Evaluator keeps its current assessment duties; no Task Evaluator,
  support pool or Squad review panel is added.
- Define actual native readiness, inheritance, context, result and lifecycle
  discovery; distinguish unsupported features from missing private telemetry.
- Define state-first supervision, actionable dependency requests and complete
  current-result intake using the selected route's actual capabilities.
- Define product quality criteria covering maintainability, justified extensibility,
  intended workload performance and required reliability. Define first-assessment
  panels, scoped Epic checkpoints, independent authorship and honest permission
  disclosure, including the optional Support Operator's nonjudgment role.
- Define detailed Task plan assessment, mandatory Epic plan assessment of
  direction/prior-output use/downstream handoff, and concise Coordinator intake.
- Define purpose-bound support work for every role, including the Coordinator,
  with cumulative scope triage and no new harness or numerical quota to enforce it.
  Preserve new Task team contexts and useful same-Task correction context.
- Specify issue triage, required fixes versus eligible deferral, local closure,
  separate test/review scope, EE re-engagement and evidence applicability using
  existing reports. These are implementation requirements, not optional future
  efficiency improvements.
- Define roadmap/Procedure/assignment ownership, explicit plan-readiness and
  correction boundaries, multi-agent work within one active node and native
  rework invalidation. Keep implementation in Aquarium without a Podway engine,
  CLI or API dependency. Preserve intermediate Milestones and bounded
  `new-feature` design continuation for the new caller.
- Define profile omission, explicit CLI/model routing, effort defaults, input
  conflicts and the boundary that blocks explicit profiles until their required
  EPIC-028 execution, commit and recovery integration is complete.
- Acceptance: assignments can explain and preserve each required role, native
  limit and actual candidate; unsupported execution cannot produce fake passage.

### TASK-148: Native Squad collaboration

- Add the explicitly invoked Squad entrypoint and supported invocation modes,
  with conditional detail in linked references. Use the shared role names in
  instructions, assignments, profile examples and reports.
- Align epic-handler's corresponding role labels in its skill, Epic orchestration
  references, assignment wording and affected guidance/docs. Preserve its single
  evaluator, goal-centered execution and existing checkpoints. Do not rewrite
  other workflows, old reports, installed copies or admitted Procedure snapshots.
- Accept omitted-profile native delivery; recognize explicit profiles and report
  the unimplemented external route. Do not run those roles natively unless the
  user directs a configuration change.
- Implement direct native role assignments, optional bounded support, risk-based
  first plan/result panels, satisfaction of both plan scopes and Coordinator Writer
  control.
  Keep first assessments independent, and join same-candidate result reviews and
  required checks where safe instead of serializing repeated correction cycles.
- Implement correction triage, eligible local closure, focused/deep delta review,
  EE re-engagement, test selection/reuse and genuine deferred-work dispositions.
  Preserve mandatory gates, first assessment of new work and actual disagreements.
- Start new Task teams, preserve same-Task corrections and apply scope/necessity
  assessment to both plans and actual results.
- Preserve actual results, context limits and configuration across sequential
  scheduling, direct helpers, descendants and one-shot replacements.
- Implement supervision and progress handling without routine transcript reads,
  unsafe active-turn status prompts or competing paired-tool observers.
- Acceptance: the same candidate receives the required first assessments;
  implementation waits for both satisfied plan scopes and the Coordinator's
  assignment. Authors cannot supply independent review and uncertain Writer
  activity prevents transfer. Required fixes are not deferred, eligible nits do
  not trigger full review, and unsupported support-tool expansion is stopped even
  when a Reviewer or the Coordinator proposed it.

### TASK-149: Squad execution and commit authority

- Connect Squad's actual owner to adaptive Goal/Validation admission, assessment,
  recovery and authorized commit handoffs; support explicit Podway opt-out.
- Supply qualified Squad definitions/bindings with explicit planning, delivery,
  assessment and correction routes. Reuse adequate definitions, let Aquarium join
  multiple assignments at a node and keep all Decisions with the Coordinator.
- Carry original verdicts, local closures, current evidence composition and
  unresolved criteria through native records and commit consumption without fake
  passes or automatic TE/EE reapproval. Re-record applicable evidence after native
  rework; never reuse invalidated items as current records.
- Carry exact candidate acceptance and separate member/correction/conditional
  closeout grants through the Coordinator's required commit tooling.
- Add focused behavioral checks for changed executable boundaries and retain
  installed managed copies and admitted snapshots unchanged.
- Preserve legacy reference mappings while admitting the real Squad owner;
  implement the no-additional-technical-review state and assessment consumption.
  Map Task/Support Operator and Epic/Task Evaluator labels to existing machine
  roles with explicit assignment scope. Keep report schema identifiers and
  admitted identities intact; terminology alone needs no protocol migration.
- Connect approved design handoffs and current session recovery to the original
  collaboration owner, preserving Design approval and delivery-input commit rules.
- Acceptance: plan gates and negative-result routes work, eligible settlement
  bypasses unnecessary new assessment, stale evidence is rejected and the exact
  accepted composition reaches commit. There is no handler impersonation,
  duplicate native goal, grant reuse or per-Task user pause. Preserve old callers
  and retained bundles, including no additional technical review for Squad.

### TASK-150: Squad integration and recovery

- Complete fresh integration reviews, Coordinator project/product review,
  disagreements, Task reopens and authorized correction/closeout handling.
- Recover missing output, interrupted roles, changed candidates, hook changes
  and committed-but-not-finalized work without losing findings or replaying effects.
- Preserve correction classification, closures, applicable test/assessment sources,
  deferred-work reasons and outstanding mandatory gates across recovery. Exercise
  Task/Epic seam corrections without blanket reruns or silent evidence reuse.
- Resolve unexplained overruns and circular waits through current owners and
  supported recovery, preserving settled Writer and candidate boundaries.
- Distinguish closeout-only edits, rejected or stopped outcomes, implementation
  rework and Task reopens through the applicable native lifecycle.
- Acceptance: integration cannot be inferred from Task passes; actual first
  assessments and eligible verified deltas cover current completion. Corrected
  obligations stay settled after resume, unknown guarantees stay open, and actual
  user acceptance gates final closeout. Retain results/configuration before
  helper retirement.

### TASK-151: Squad verification and documentation

- Verify the committed installed candidate using the repository's UTM policy,
  exercising native collaboration, failure/recovery and existing-handler paths.
- Cover Codex and Claude native scenarios with actual results where available;
  identify unverified harnesses and capability gaps rather than generalizing
  observations or imposing cross-harness proof as ordinary startup admission.
- Use existing scenario records to compare unnecessary whole-suite runs, repeated
  assessments, support-work diversion and supervision reads against missed defects,
  detection delay and false recovery. Record actual durations or usage only when
  available; no new benchmark service, telemetry stack or simulated savings claim.
- Exercise both saved work and preserved assurance: editorial/expectation repair,
  real contract/security defects, required versus deferred findings, misleading
  green tests, stale candidates and genuine required harness work.
- Verify consistent role names in Squad and handler assignments and reports.
  Observe that the handler still uses one continuous evaluator, adds no Task
  Evaluator or required support participant, and resumes retained records under
  their original schemas. Do not turn terminology checks into prose-pinning tests.
- Require actual installed end-to-end observation for at least one named supported
  native harness; unobserved harnesses do not acquire a passing result.
- Complete Master's separate functional verification, keeping source checks,
  installed observations and actual Epic acceptance distinct.
- Promote implemented contracts to capabilities, workflow/orchestration specs,
  architecture, testing and public guidance as affected. Preserve this shared
  dossier for EPIC-028's remaining Herdr and mixed-execution requirements.

### TASK-152: Squad profiles and capabilities

- Extend the same entrypoint's profile interpretation for independent role routes,
  common/scoped Evaluators, explicit Task Operator and optional Support Operator pools,
  effort default and installed CLI model/effort controls without universal launch
  syntax or an implicit support-team requirement.
- Preserve omitted roles and requested profiles across design-return and resume;
  inspect only applicable native/Herdr capabilities.
- Keep all seven supplied examples as examples and inspect only applicable
  installed contracts; no live model access is established by a static fixture.
- Acceptance: unsupported, ambiguous or mismatched settings get an explicit
  disposition and alternatives; changing requested configuration needs user direction.

### TASK-153: Squad Herdr and mixed execution

- Extend the existing Squad entrypoint with verified helper allocation,
  role-specific native/Herdr assignments and same-CLI explicit Herdr execution.
- Directly manage distinct Epic and Task Evaluators, including identical common
  profiles and mixed native/Herdr roles. Optional nested assistance does not
  replace direct Task Evaluator management.
- Collect original assessments and applied configuration for top-level roles and
  supported descendants. Preserve supplied profiles and omitted roles in Squad
  design-return handoffs.
- Handle blocked approval/question UI under the installed Herdr contract,
  preserving the operation, actual authority and Writer state.
- Verify available model/effort/permission effects on launch, resume and Writer
  transfer through native controls. Disclose limits, block required unsafe actions
  and do not build enforcement harnesses or change host defaults to hide gaps.
- Acceptance: caller/layout failures use supported Herdr recovery without raw
  layout fallback or an unapproved route change. Required explicit roles remain
  external, omitted roles remain native, and the Coordinator reads actual
  complete results without interactive-prompt injection or fake multi-agent provenance.

### TASK-154: Squad mixed delivery and commit integration

- Reuse the same five role names, first-assessment panels, concurrent result intake,
  correction closures, evidence reuse, deferral and EE re-engagement policy across
  native and Herdr roles. Preserve role routes, optional support and One Active Writer.
- Apply the same necessity criteria and new-Task context boundaries to native,
  Herdr and mixed teams.
- Extend and verify Squad's existing workflow owner and adaptive execution/commit
  handoffs for mixed execution, Podway opt-out and selected technical reviews.
- Reuse the no-additional-technical-review state and preserve retained bindings,
  including native-only Squad bundles, when recovering or extending sessions.
  Do not create a second owner, relabel a bundle or replay completed effects.
- Acceptance: original assessments and eligible closures cover the candidate
  reaching Coordinator-owned commits. No existing handler, provider-review team
  or acceptance source is relabeled as Squad evidence, and required reviews use
  their configured routes.

### TASK-155: Squad mixed recovery and configuration reporting

- Recover native handles, uncertain external submissions and existing results
  before replay; settle modifying descendants across both routes and preserve
  replacement findings, route/profile selection and authority.
- Preserve fair supervision, actionable dependency requests and complete report
  intake across mixed routes, including partially detected blocked UIs.
- Collect minimal public configuration for the Coordinator and participating
  roles/descendants, support and closeout helpers before exact owned cleanup.
  Preserve requested/applied/observed distinctions and resumed-control limitations;
  do not add blanket user-configuration audits or copy sensitive settings.
- Acceptance: pane loss is not proof of termination, uncertain writes block
  handoff, matching profiles may be grouped only with their scopes retained,
  and applied/observed/unconfirmed settings are reported honestly.

### TASK-156: Squad mixed verification and documentation

- Verify available same-CLI and cross-CLI Herdr execution, all-native preservation,
  common/scoped direct Evaluators and mixed roles, correction and closeout.
- Cover external Task Operators with native Evaluators, native Task Operators with external
  Evaluators, and native Epic with explicit same-CLI external Task Evaluator.
- Exercise unsupported profile/control, resumed defaults, optional support and
  failure/recovery paths, including local correction without full review and
  changed contracts that require EE participation. Distinguish synthetic checks
  from real account/model availability and observed settings. The seven examples
  are not a mandatory seven-profile live test matrix.
- Verify native-only Squad and existing-handler preservation. Obtain Master's
  separate functional verification before claiming those outcomes.
- Require actual installed mixed Squad delivery observation for a named supported
  configuration; report unobserved CLIs/routes explicitly.
- Promote implemented outcomes, settle each consumer's remaining requirements
  and prepare last-consumer dossier disposition under actual closeout authority.

## Verification scenarios

These scenarios are acceptance requirements for the future implementation Tasks,
not claims of execution in this documentation change.

During development, TASK-148 adds the native entrypoint and TASK-153 extends it
with Herdr/mixed execution. Each new execution route remains unavailable for
delivery until its required execution, commit and recovery integration is
implemented. Report missing integration explicitly and preserve existing
native-only delivery; entrypoint discovery or agent launch alone is insufficient.

Implementation ownership below supplements the roadmap's Task definitions;
TASK-151 verifies the native foundation; TASK-156 verifies Herdr/mixed additions
and native-only preservation. Shared scenarios apply to both phases on their
actual routes.

| Scenario | Required observation | Implementation owner / applicability |
| --- | --- | --- |
| Normal multi-Task delivery | Both plan scopes precede implementation; required first assessments, applicable closures/checks and Coordinator acceptance precede a verified Task commit. No Task waits for future Task functionality. | TASK-148 / TASK-154; both |
| Plan defect or material design change | Refresh affected plan scopes before implementation; a material change cannot use local closure, while editorial or bounded clarification does not restart all plan reviews. Both scoped obligations cover the assigned plan. | TASK-148 / TASK-154; both |
| Task plan direction and continuity | Every plan receives detailed Task review and an Epic review of direction, verified prior-output use and downstream deliverable design, including plans with no material cross-Task change. | TASK-147, TASK-148 / TASK-154; both |
| Role-scoped planning context | Actual concise assessments and source references reach the Coordinator; the Epic role retains consequential continuity decisions and the Task role retains detail. Concrete concerns allow targeted source inspection; final product review remains substantive. | TASK-147, TASK-148 / TASK-154; both |
| Routine supervision and quiet work | State-first observation avoids repeated console reads; healthy quiet work is not restarted merely for silence, and repetitive output alone is not progress. Compare read count/volume with detection delay, missed incidents and false recovery. | TASK-147, TASK-148 / TASK-153, TASK-154; both |
| Dependency and supervision starvation | Requests needing Coordinator action reach it without an in-turn circular wait; one pending participant does not hide a peer's blocked or completed state. Supported safe native interactions remain usable. | TASK-148, TASK-150 / TASK-153, TASK-155; both |
| Uncertain progress or missed dialog | An overrun, hung tool or partially detected UI triggers enough inspection to choose continued observation, supported recovery or a reported gap without duplicate dispatch or an endless unexplained wait. | TASK-148, TASK-150 / TASK-153, TASK-155; both |
| Active-turn input and stale report | No terminal status prompt queues unintended work; complete reports match the current assignment and revision even after stalled submission or an older visible pass. | TASK-148, TASK-150 / TASK-153, TASK-155; both |
| Coordinator context recovery | Pending handles, requests, candidate and next owners survive recovery through existing runtime records without a new state store or transcript import. | TASK-148, TASK-150 / TASK-155; both |
| New Task team | Each new Task starts distinct Task Operator and Task Evaluator instances with fresh conversations where supported, concise source-based handoffs and disclosed inheritance limits; same-Task roles remain recoverable through commit verification while the Epic Evaluator retains continuity. | TASK-147, TASK-148 / TASK-153, TASK-154; both |
| Task Operator scope expansion | A plan or result adds an unsupported feature, abstraction or restriction; required behavior working does not prevent rework of the unjustified addition. | TASK-147, TASK-148 / TASK-154; both |
| Reviewer scope expansion | An Evaluator or Coordinator proposes optional hardening, an unsupported prerequisite or disproportionate tests; the team excludes it from mandatory work despite reviewer agreement. | TASK-148 / TASK-154; both |
| Necessary internal implementation | A required outcome needs an internal mechanism or defect correction omitted from the design detail; a concrete necessity basis allows it without demanding literal specification of every implementation choice. | TASK-148 / TASK-154; both |
| Required and excessive verification | Required checks and tests for reachable failure paths remain due; speculative or implementation-mirroring tests are excluded, and sufficient evidence permits pass without extra tests. | TASK-148 / TASK-154; both |
| Cumulative restrictions and rewritten docs | Epic review catches normal supported user scenarios blocked by accumulated restrictions; agent approval or documentation changed to match those restrictions does not establish scope authority. | TASK-150 / TASK-154, TASK-155; both |
| Result defect or missing evidence | Required corrections/evidence are distinguished from preferences; due gaps prevent passage. | TASK-148 / TASK-154; both |
| Coordinator/Evaluator disagreement | Original findings remain visible; focused evidence resolves readiness without forced consensus or evaluator shopping. | TASK-150 / TASK-155; both |
| Changed candidate | Classify the cumulative delta; retain unaffected evidence, close eligible local repairs and refresh only invalidated assessments/checks. Neither changed bytes nor a new hash alone triggers full reapproval. | TASK-148, TASK-149 / TASK-154; both |
| Limited native capacity | Native independent reviewers can run sequentially with complete actual results and preserved scope, including in mixed teams; roles are not impersonated or omitted. | TASK-148 / TASK-153; both |
| One-shot/replaced Task or Epic role | Original sources, candidate, findings and remaining authority survive; restored reports do not create fresh approval. | TASK-148 / TASK-155; both |
| Different worktree or snapshot | Required reviews inspect the integrated acceptance candidate, including owned dirty/untracked content. | TASK-149 / TASK-154; both |
| Native permission limit | Assignment-only read-only restrictions are disclosed; unsupported technical isolation is never claimed. | TASK-147 / TASK-153; both |
| Uncertain Writer/background work | No Writer transfer or candidate freeze occurs until modifying activity, including descendants and background commands, is settled; a settled parent turn, vanished pane, stable diff or absent Git lock alone is insufficient. Recheck the exact candidate before admitting assessments. | TASK-148 / TASK-155; both |
| Truncated output or uncertain submission | Existing output/operation is inspected first, without duplicate implementation or a disguised new review. | TASK-148 / TASK-155; both |
| Hook change or pending finalization | Classify post-review bytes by their actual effects; use eligible local closure or affected reassessment and preserve a successful commit without replay. | TASK-150 / TASK-155; both |
| Final integration without a new diff | Fresh independent integration and Coordinator review still occur; no empty commit is manufactured. | TASK-150 / TASK-154; both |
| Same-CLI explicit profile | The explicitly configured role uses Herdr while omitted roles stay native and the Coordinator's session remains unchanged. | TASK-153; Herdr/mixed |
| Distinct Evaluator roles | Direct distinct Epic and Task instances receive original criteria and separate scoped approvals; optional descendants do not replace direct management. | TASK-148 / TASK-153; both |
| Common/scoped explicit Evaluators | A common profile expands into two direct Herdr roles; scoped entries affect only their roles, and omissions stay native. | TASK-152 / TASK-153; Herdr/mixed |
| Unsupported profile or effort | Report the limitation and proposed alternative; changing the requested profile or route requires user direction. | TASK-152; Herdr/mixed |
| Configuration replacement/descendants | Final reporting includes actual applied controls and available confirmation, with unknown values retained. | TASK-150 / TASK-155; both |
| Podway default, opt-out and resume | Correct owner, source and pending lifecycle remain intact; no in-place relabeling or duplicate goal is introduced. | TASK-149 / TASK-154; both |
| Selected additional technical review | Route-specific team, result, source transmission and authority remain distinct from collaboration assessments. | TASK-149 / TASK-154; both |
| Final user acceptance | Only actual user acceptance unlocks the conditional closeout commit; delegated Task acceptance is attributed to the Coordinator. | TASK-150 / TASK-154; both |
| Shared Epic role names | Squad uses C/EE/TE/TO/SO. Handler uses C, its single continuous EE and TO, with SO only for existing authorized support. No separate TE, extra checkpoint, doubled assessment or required support launch is introduced. Writer/Reviewer/Leader remain assignment duties. | TASK-147, TASK-148, TASK-149 / TASK-154; both |
| Existing workflows | Handler terminology follows the shared mapping; Handler/Validator behavior, admitted sources, generic machine roles/report schemas and evaluator permissions remain unchanged. Other workflow roles are not renamed implicitly. | TASK-149 / TASK-154; both |
| Intermediate versus final Milestone | Intermediate reviews preserve the active Task; only the completed Task reaches completion acceptance and its normal commit grant. | TASK-148 / TASK-154; both |
| No additional technical review selected | New-owner definitions and consumers accept the explicit state without provider execution, a fake waiver or missing collaboration reviews. | TASK-149 / TASK-154; both |
| Pre-upgrade retained bundle resume | Legacy Goal/Validation source and binding identities remain usable after new callers are admitted. | TASK-149 / TASK-154; both |
| Missing dossier or semantic owner | Execute enters bounded design, preserves its approval/commit rules and ends with an exact new-conversation Squad invocation carrying explicit profiles and omitted roles. Waiver and active-session rules remain due. | TASK-147, TASK-148 / TASK-152, TASK-153; both |
| Final rejection or requested changes | Record-only edits and implementation changes follow their respective lifecycle and affected review paths; revised final content needs actual acceptance. | TASK-150 / TASK-155; both |
| Stopped before achievement | Pending effects and unmet obligations remain visible; a stopped assessment neither resumes work nor declares completion. | TASK-150 / TASK-155; both |
| One Task Operator profile, several instances | A single approved profile supplies distinct authoring and non-authoring instances without an invented provider-diversity requirement. | TASK-152 / TASK-153; Herdr/mixed |
| Cold validation after collaboration delivery | An explicitly invoked epic-validator resolves Squad-origin evidence through its existing cold-validation contract. | TASK-151 / TASK-156; both |
| Unsupported native role | Report unsupported creation or matching configuration and preserve unaffected preparation; no impersonated roles or switch to Herdr without user direction. Fully external roles do not require optional native support. | TASK-147, TASK-148 / TASK-153; both |
| No role profiles | All required roles use matching native instances; Herdr availability is not an admission condition. | TASK-148 / TASK-153; both |
| External Task Operators only | Native Epic/Task Evaluators assess Herdr Task Operator work; required independent Task Operator reviewers use distinct instances of the supplied pool. | TASK-153 / TASK-154; Herdr/mixed |
| External Evaluators only | Explicit Evaluators use distinct Herdr sessions while omitted Task Operator assignments stay native. | TASK-153 / TASK-154; Herdr/mixed |
| Native Epic and same-CLI external Task | An omitted Epic profile uses the Coordinator's native configuration; explicit Codex Task Evaluator and opencode Task Operator profiles use Herdr with their own resolved settings. | TASK-153 / TASK-154; Herdr/mixed |
| Omitted effort versus omitted profile | Explicit CLI/model with omitted effort applies high; an omitted whole profile matches the Coordinator's current effort. | TASK-147 / TASK-152; both |
| Invalid or conflicting input | Partial/empty profiles, an empty explicit Task Operator list or common plus scoped Evaluator entries are resolved before affected agents launch. | TASK-147 / TASK-152; both |
| Native-first and partial Herdr extension | Explicit profiles remain unimplemented until required execution, commit and recovery integration is complete; no native substitution without user direction. Existing native-only delivery remains usable. | TASK-147, TASK-148 / TASK-153, TASK-154, TASK-155; both |
| Unavailable route and resume | Preserve selected roles, pending findings and actual route-specific handles; route/profile changes need user direction. Omitted roles match the current Coordinator, with inheritance changes disclosed and prior records retained. | TASK-150 / TASK-155; both |
| Blocked external permission/question UI | Inspect and preserve the same operation, apply the installed Herdr permission contract, obtain a required user answer and retain the Writer restriction while modifying activity is uncertain. | TASK-153 / TASK-155; Herdr/mixed |
| Native-only retained Squad session | The Herdr extension preserves the original Squad owner, binding identity, grants and pending operations; no in-place route change or effect replay occurs. | TASK-154 / TASK-155; Herdr/mixed |

The following cases specifically test product focus and correction efficiency.
Observe both required actions and the absence of unnecessary launches/reruns using
existing run records; a policy sentence or synthetic pass is insufficient.

| Scenario | Required observation | Implementation owner / applicability |
| --- | --- | --- |
| Durable product repair | An in-scope structural fix improves a required maintainability or extension boundary instead of applying a brittle patch; supporting work stays proportional and original behavior remains verified. | TASK-148 / TASK-154; both |
| Required performance behavior | A change on a performance-sensitive path checks the affected requirement under representative conditions; no unrelated benchmark system is built. | TASK-148 / TASK-154; both |
| Standard versus elevated first review | Standard work gets TE plus one independent Task Operator; elevated work gets TE plus two. Actual changed risk expands coverage; local corrections do not recreate the initial panel automatically. | TASK-147, TASK-148 / TASK-154; both |
| Concurrent first result intake | Ready independent reviews and nonconflicting required checks use one frozen candidate and produce one correction set; peer verdicts are withheld until first views are formed. | TASK-148 / TASK-154; both |
| Editorial-only correction | An already assessed non-normative typo receives document/integrity checks and closure without product tests, full review or routine TE/EE recall. A missing optional helper does not start validator development. | TASK-148, TASK-149 / TASK-154; both |
| Obsolete expectation | A display-string expectation traces to an approved external basis, only intended literals change, and referring/previously unexecuted required tests run. Other applicable evidence survives. | TASK-148, TASK-149 / TASK-154; both |
| False expectation repair | A changed error code, numeric expectation, matcher or assertion weakening cannot be called an editorial fix just because tests become green. Resolve intended behavior and the actual defect. | TASK-148 / TASK-154; both |
| Mixed correction delta | An eligible typo beside a contract change never exempts that contract; assess their combined effects and retain only genuinely unaffected evidence. | TASK-148, TASK-149 / TASK-154; both |
| Serious but isolated repair | An important current defect is fixed before acceptance; direct deterministic proof can establish local eligibility without downgrading its priority or hiding a required independent judgment. | TASK-148 / TASK-154; both |
| Contract/security correction | A small high-consequence change gets relevant consumer/failure checks and elevated delta review, with EE for cross-Task impact. A required full test gate does not automatically create a full review of unrelated work. | TASK-148 / TASK-154; both |
| Deferred versus blocking work | A genuine independent improvement reaches the existing deferred owner with reason and re-entry condition; a current correctness/acceptance gap is repaired or blocked, never postponed for speed. | TASK-148, TASK-150 / TASK-154; both |
| Existing failure or suspected flake | Preserve failing evidence and establish the cause; no silent skip, relaxed assertion or automatic allowance based solely on later green reruns. Applicable mandatory-gate authority remains due. | TASK-148 / TASK-154; both |
| Execution/retrieval incident | A wrong directory, interrupted run or truncated report repairs only affected execution/evidence; retrieve the same operation before redispatch and do not restart source review without a changed guarantee. | TASK-148, TASK-150 / TASK-155; both |
| Coordinator-authored correction | Semantic closure gets focused non-authoring confirmation; the Coordinator does not count its own check as an independent review or require a new generic checker. | TASK-148 / TASK-154; both |
| Support work displaces product work | Task Operator, Reviewer or Coordinator support expansion is paused/narrowed when no required outcome advances; an existing sufficient command is used instead. Useful diagnosis counts despite no code change. | TASK-148 / TASK-154; both |
| Necessary harness work | A required behavior/evidence gap permits the smallest sufficient fixture or harness repair, without a blanket prohibition, unjustified expansion or unrelated hardening. | TASK-148 / TASK-154; both |
| Optional Support Operator | Assigned facts/checks match the fixed candidate, original results are inspected, and the SO supplies no verdict, Writer transfer, finding closure or extra approval stage. | TASK-148 / TASK-153, TASK-154; both |
| Explicit plan gate and negative assessment | Implementation cannot precede satisfied plan scopes. A faithful negative assessment completes its Action and follows the declared corrective Decision without fabricated passage. | TASK-149 / TASK-154; both |
| One node with several agents | Aquarium joins independent results/checks while Podway retains one active attempt; no nested Task session, extra cursor or concurrent Writer is needed. | TASK-149 / TASK-154; both |
| Rework evidence invalidation | Native stale items remain unusable; applicable original artifacts are checked and re-recorded as a current composition. Changed inputs or unknown applicability keep obligations open. | TASK-149, TASK-150 / TASK-154, TASK-155; both |
| Recovery after local closure | Restored original verdicts, verified deltas and pending obligations avoid repeating settled reviews/tests; missing or changed evidence receives focused recovery rather than assumed success. | TASK-150 / TASK-155; both |
| Source drift and retained definition | A distribution update does not rewrite the active Procedure/binding or turn old assessment into fresh evidence. Existing retained-bundle recovery works without a second Pilot runtime. | TASK-149, TASK-150 / TASK-155; both |
| Resume changes effective controls | Supported model/effort/permission settings are rechecked; mismatch or unavailable enforcement is disclosed and required unsafe work stops. No copied version-specific workaround or host-default edit is invented. | TASK-153, TASK-155; Herdr/mixed |

Automated tests cover objective structure and changed executable helper behavior
where applicable. Do not pin skill prose or add automated LLM evaluations to
`make test`. Structural checks do not establish agent behavior. Reuse existing
fixtures and guest-side facilities; these cases do not authorize a new validation
framework or broad harness-hardening project. Report manual/installed results only
for the actual candidate, harness and configuration observed. Collect available
run/review counts, durations and usage from those records; compare like scenarios
and disclose unmeasured costs instead of claiming unverified savings.

## Documentation promotion and closeout

Keep planned behavior here until implemented or explicitly frozen under the
documentation rules. Task-owned implementation updates the exact skill/reference
authority first, then affected specifications, architecture, implementation tips,
operations, testing and public documentation. Keep technical explanations and
important decisions concise, and run required prose passes before final review.
Do not add shipped claims or release notes merely for this planning change.

Update the documentation index's planned-collaboration description as each phase
ships, retaining accurate planned wording for any unfinished consumer. Replace
or remove its dossier link before the last consumer deletes the dossier.

At EPIC-027 closeout, promote accepted shared and native outcomes and replace
that Epic's dossier link with valid canonical outcomes. Retain this dossier and
its TODO index entry while EPIC-028 remains a consumer. At the last consumer's
approved closeout, promote remaining durable content, reconcile every roadmap
reference, and remove the dossier and index entry under the existing
[last-consumer rules](../../plugins/aquarium/references/epic-execution-sot.md#close-out-without-manufacturing-documentation).
Do not archive a duplicate dossier or treat its checklist as lifecycle authority.
