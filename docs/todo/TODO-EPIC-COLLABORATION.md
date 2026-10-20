# Epic Squad collaboration

## Purpose and authority

This dossier defines planned `epic-squad` delivery for Aquarium maintainers and
workflow authors. Its consumers are
[EPIC-027](../roadmap/README.md#epic-027-add-native-epic-squad-collaboration) and
[EPIC-028](../roadmap/README.md#epic-028-extend-epic-squad-with-herdr-and-mixed-collaboration).
The roadmap alone owns IDs, ordering, dependencies and lifecycle state. This
file owns the detailed requirements, implementation boundaries and acceptance
contract until each consumer promotes its implemented outcomes.

The planning baseline is Aquarium v0.1.20. This skill is unimplemented.
This documentation change records its design and planned work. Implementation,
workflow execution, candidate installation and commit authorization are outside
this change.

The design incorporates the agreed Epic Solo and Epic Harmony workflows with
the final names Coordinator, Evaluator and Executor. The standalone templates
outside this repository are planning inputs, not required execution files.
Earlier names `epic-harmony`, `epic-operator` and `epic-team` are not additional
entrypoints. The native and external capabilities share one `epic-squad` owner.

## Product outcome and preserved behavior

Squad should catch plan defects, implementation defects and cross-Task
incompatibilities during delivery. Agents investigate, challenge assumptions and
improve the implementation through verification. The Coordinator follows the
technical work and owns the assembled product. Useful behavior, correctness and
maintainability take priority over reports or process artifacts.

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
Existing handlers, their single
logical Evaluator, admitted sessions and selected technical reviews retain their
contracts. Preserve existing callers' behavior when extending shared integrations.

## Scope and implementation choices

Assess both missing required behavior and unnecessary additions against the
original requirements, approved design and applicable repository/tool contracts.
A reviewed Task plan remains an implementation proposal within those sources.
Agent agreement, internal plan approval or documentation rewritten to match an
implementation cannot authorize a product scope expansion.

Executors, Evaluators and the Coordinator share responsibility for keeping the
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
delivery in the design conversation. Carry supplied Evaluator and Executor
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
During implementation and result review, read important decisions, actual
artifacts, agent findings and relevant verification output throughout delivery.
For routine plan progression, read the Task and Epic Evaluators' actual concise assessments and
material exceptions; do not duplicate their plan reviews or routinely import
full plans, detailed review exchanges or agent transcripts into this context.
With applicable plan passes and existing authority, assign implementation to
the Writer.
Investigate or escalate a concrete concern when needed.
Check whether proposed mandatory work has a source and a necessary effect on the
current outcome. An Evaluator request alone does not make an addition required.

For result review, after the required Evaluator approvals, personally inspect
the candidate in the project and product context.
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
Assess the overall approach and material cross-Task changes. After a Task
plan passes Task-level review, perform a required Epic-context plan assessment
for every Task. Focus on three questions: does it advance the Epic's intended
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

After a Task Evaluator passes a completion candidate, independently inspect that
same candidate and original sources in the Epic context. A summary alone does not
establish approval. Review the assembled Epic separately at final integration.

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
Resolve required findings from the independent Executor reviews and refresh
affected assessment of revisions before passing the current plan revision for
Epic assessment. Report unresolved substantive disagreements
as material exceptions; they do not establish plan readiness.
Keep detailed planning and correction context within this Task role; send concise
phase-specific assessments, material exceptions and accessible source references
to the Coordinator and Epic Evaluator. Keep the role recoverable through
corrections, Epic assessment, Coordinator review and commit verification.

### Executors and optional coordination

Assign bounded investigation, analysis, planning, implementation, verification,
documentation and independent review. Delivery Executors first produce a plan.
Choose the simplest sufficient implementation and explain material additions
under the scope contract above. Assess review requests on that same basis before
implementing them; report unsupported additions for disposition.
Task implementation requires both plan passes on the current revision and the
Coordinator's bounded implementation assignment to the Writer. Earlier tracked
planning edits require a Coordinator-assigned Writer scoped to planning within
existing user authorization; that assignment grants no implementation authority.
Only the active Writer modifies project files;
Executors never modify the Git index or create commits.

Use a Leader only when coordinating a group helps. It returns actual descendant
findings and a synthesis, with no extra acceptance, Writer or commit authority.
Do not require fixed CLI-specific groups. The Coordinator manages its own native
helpers and any Leaders; a Leader cannot authorize another Writer.

### Task team contexts

At each new Task, assign new delivery and review Executor instances and a
dedicated Task Evaluator. Start fresh conversations where supported; do not
resume the preceding Task team's conversations for the new Task. Pass concise
verified outcomes, shared contracts, important decisions, remaining obligations
and original source references. A shared Executor profile supplies configuration
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
labels, a parent's synthesis or an Executor's self-check do not create independent
assessments. Separate instances may use the same profile without claiming model
or provider diversity.

Bounded factual scouting and review feedback alone are not plan authorship.
Drafting or revising the assessed plan or implementation is authorship. When a
reviewer becomes a Writer, replace its independent coverage with a non-authoring
instance. Do not require a single plan drafter or a fixed-size Executor pool.

These rules also cover Coordinator-authored work. The Coordinator performs
final acceptance review after obtaining the required non-authoring assessments;
its own review does not count toward them.

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

For every Task:

1. Start the Task team under the context rules above and align it on the original
   outcome, criteria and non-goals. Executors investigate and consolidate an
   actionable plan covering design, affected interfaces, dependencies,
   assumptions, risks, meaningful Milestones, checks and docs.
   Identify relevant earlier Task outputs and how they are used, and the
   deliverables or contracts later Tasks will consume, within this same plan.
   Identify material additions and their necessity in the same plan.
   Investigation does not grant implementation authority; tracked planning edits
   use the planning-scoped Writer assignment described above.
2. Have the Task Evaluator and at least two distinct non-authoring Executor
   instances independently assess the same plan revision before comparing
   findings. Give complementary concerns and original sources. The Task
   Evaluator assesses detailed readiness, including scope compliance and
   unnecessary additions. Resolve required independent findings
   and refresh affected assessments of any plan revisions. The Task Evaluator
   passes the resulting current revision before the Epic Evaluator assesses it
   for Epic direction, use of earlier work and downstream handoff design.
   Obtain the Epic Evaluator's explicit plan-scope pass for the revision that
   the Task Evaluator passed after finding resolution. Report unresolved
   substantive disagreements as material exceptions.
3. The Coordinator reads both actual concise assessments, confirms that their
   plan passes apply to the current revision, and addresses material scope or
   authority exceptions. Delegate warranted revisions and refresh affected
   assessments before implementation. Once both passes apply and substantive
   concerns are resolved, assign the Writer within existing authority; this is
   execution coordination, not a third routine plan approval.
4. The selected Writer implements, self-verifies and documents the result.
   Report actual changes, checks, outcomes, gaps and deviations from the plan.
5. At meaningful Milestone and Task result boundaries, stop project modifications.
   The Task Evaluator and at least two distinct non-authoring Executor instances
   independently assess the same candidate, actual behavior, verification and
   documentation against the original sources. Check for overimplementation in
   both the reviewed plan and the actual result. Plan passage does not establish
   implementation correctness or justify an unnecessary addition.
6. Resolve findings and verify corrections. Refresh the affected independent
   assessments, retaining still-applicable evidence. After Task Evaluator passage,
   obtain the Epic Evaluator's explicit Task-context approval of that candidate.
7. The Coordinator performs its final project and product review, discusses
   substantive concerns with the relevant Evaluators and resolves them through
   the procedure below. Both approvals must apply to the accepted Task candidate.
8. The Coordinator records its delegated acceptance, takes the Writer role,
   includes approved lifecycle and record changes, and creates the authorized
   local Task commit. Apply changed-candidate reassessment to any post-review
   lifecycle or record edits before committing. Inspect the committed result,
   hooks and remaining worktree.
9. Complete the Task goal only after all required evidence, assessments,
   Coordinator acceptance and commit inspection are satisfied. Preserve its
   handoff and configuration records, retire owned helpers safely and continue
   to the next eligible Task under the existing authorization.

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
as those proposed by an Executor. A mandatory correction needs a source or
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

Assign agreed corrections to a Writer and refresh affected checks and independent
reviews. For a changed Task result candidate, the Task Evaluator and then Epic
Evaluator must reassess or explicitly reaffirm applicability before the Coordinator reviews
again. The Coordinator cannot carry forward an old approval on their behalf.
Current result approvals and the Coordinator's concurring final review establish
readiness without an extra acknowledgement cycle.

For a revised plan, first obtain the Task Evaluator's affected reassessment or
explicit reaffirmation for the new revision after resolving required findings.
Then obtain the Epic Evaluator's affected reassessment or explicit reaffirmation
for that same revision. The Coordinator checks both actual assessments before
assigning implementation; it cannot carry forward either plan approval on an
Evaluator's behalf.

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
explicit profile or Executor list is invalid; omission selects the native default.
Preserve resolved CLI model IDs as opaque values, including any slashes inside
them; resolve ambiguous profile boundaries instead of splitting a model ID.
Only an effort omitted from an explicit profile defaults to `high`. An omitted
whole profile retains the Coordinator's current effort.

Accept a common `Evaluator:` profile or scoped `Epic Evaluator:` and
`Task Evaluator:` profiles. Common and scoped Evaluator entries together are
conflicting input; do not invent override precedence. A common entry applies
the same profile to both roles. With scoped entries, an omitted role stays
native independently of the other role. Accept one or more explicit Executor
profiles; a singular Executor entry denotes a one-profile pool.

```text
Target Epic: EPIC-017

Task Evaluator: codex / gpt 6.1 sol / high

Executors:
- opencode / glm 5.3 / max
```

With a Codex Coordinator, this example uses a native Codex Epic Evaluator, a
Herdr Codex Task Evaluator and Herdr opencode Executors. The Epic Evaluator
matches the Coordinator's current model and effort, which need not match the
explicit Task profile. These names are requested inputs, not availability claims.

```text
Target Epic: EPIC-017

Evaluator: agy / gemini 4 argon / high
```

This example assigns both Evaluator roles to Herdr while omitted Executors use
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

A profile is not an instance. Executors may share a profile but must use separate
authoring and non-authoring instances. If Executor profiles are omitted, required
delivery and independent Executor reviews use native instances. If a pool is
explicitly supplied, those assignments, including plan, result and integration
reviews, use its profiles through Herdr. Not every profile must participate in
every assignment. The Coordinator's native helpers may add findings; they do not
replace required Executor or Evaluator coverage from the configured route.

Resolve and disclose each role's route and configuration in the execution plan.
Preserve supplied profiles and omitted roles through design-return and recovery.
Omitted roles resolve against the current Coordinator in the new or resumed
session; retain earlier configuration records and disclose changed inheritance.
This default does not freeze an earlier Coordinator's model or effort. Recheck
capabilities on resume. Changing a selected route or explicit profile requires
user direction; disclosure alone does not authorize substitution after failure.
Recover or replace an instance on its existing route/profile under current
authority while retaining pending findings.
Another already approved Executor profile may handle suitable work; obtain user
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
Native roles and the Coordinator's own native helpers match the Coordinator's
current model and effort through supported inheritance or explicit matching
controls. Descendants assigned that configuration follow the same rule. Do not
select per-role alternatives or change the Coordinator's configuration.
Matching configuration does not require copying its conversation.

Verify actual creation, result retrieval, continuation, termination, context,
configuration and permission capabilities for roles selected as native. Distinct
direct agents for native Epic/Task Evaluators and delivery/review Executors suffice;
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

## Herdr configuration

Use Herdr for explicitly profiled roles, including same-CLI profiles. Evaluators
use distinct directly managed sessions even when they share a common profile.
Executors use independent instances from the supplied pool. CLI-native descendants
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
Inspect available public launch or configuration information. Report unavailable
models, unsupported efforts and observed mismatches. The default `high` is part
of a resolved explicit profile. Changing its model, requested or defaulted effort,
or execution route requires user direction; disclosure alone is insufficient.
Keep the Coordinator's session unchanged. Another already approved
Executor profile may handle suitable work, but a change to the required team
configuration needs user direction.

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

## Writer, result and commit boundaries

### One active Writer

The Coordinator assigns the sole Writer for shared project files, including
source, tests, tracked docs, generated files and commands that rewrite them.
Normally an Executor writes; the Coordinator may take the role when useful.
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

Recover truncated or missing existing output through the supported interface
first. When necessary, ask the producing agent to write its existing result to an
assigned temporary file and read it completely. This is result recovery, not a
new implementation or review pass. File deliverables explicitly assigned are
also allowed. Use distinct locations per session/assignment outside the repository
or in permitted ignored runtime storage. An agent unable to write report files
in its native read-only mode uses its console or native result channel instead
of receiving broad project write access.

Reports identify assignment and status, actual changes or findings, files, checks
and results, gaps and next actions. Evaluators also give scope, verdict and
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
worktree. Substantive post-review changes require affected checks and independent
reassessment, including Task then Epic Evaluator approval for a Task candidate,
before renewed Coordinator acceptance. Committing unchanged reviewed content
alone requires no new review. Recover a successful commit with pending workflow
finalization without replaying the commit or consuming its grant twice.

## Integration, authorization and reporting

After all Task commits are verified, independently assess the assembled Epic
with the Epic Evaluator and at least two fresh non-authoring Executor instances.
Use the configured Executor route and profiles. Supply original requirements,
Task commits, actual implementation, docs and check results. Check purpose,
cross-Task behavior, shared interfaces, architecture, end-to-end user scenarios,
documentation, regressions and missing evidence.

Resolve findings with bounded corrections and updated affected assessments.
Apply plan reassessment to material changes. A correction author cannot
independently review that correction. After Epic Evaluator passage, the
Coordinator performs the whole-project/product final review and resolves concerns
with the Epic Evaluator before accepting integration corrections and committing.
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
changes refresh affected assessment; unchanged content needs no redundant commit
question. No required closeout diff means no manufactured commit.

If the user requests closeout-only record changes, revise that candidate within
the applicable closeout lifecycle, refresh affected checks and Epic assessment,
and present the revised candidate for actual acceptance. If the request changes
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
commits, each Task's applicable Evaluator approvals and Coordinator acceptance,
integration outcome, and substantive disagreements with their dispositions.
Record user acceptance only after it occurs.

Include a concise agent configuration table by role and Task/Epic scope, execution
route, CLI, requested profile or omitted-profile default, applied model selection
and effort, available observed confirmation and unconfirmed information. For
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
Goal-family sessions for member/correction/closeout work and Validation-family
execution for final integration. Adapt only where fit requires it. The actual
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

### Assessment and record mapping

The implementing Tasks must bind these obligations to the selected definition's
actual nodes and existing ordinary reports. Keep original reports, producer
identity, scope and exact plan/candidate references accessible through permitted
result storage. Use the selected definition's actual native fields and existing
report schemas for these obligations.

| Phase | Producer and retained basis | Consumer and completion meaning |
| --- | --- | --- |
| Task plan | Author's plan revision; Task Evaluator and at least two non-authoring Executor reports, followed by the Epic Evaluator's direction/continuity/handoff assessment | Both Evaluators pass the same revision within their plan scopes; the Coordinator reads concise actual assessments and assigns the Writer under existing authority, without a third routine plan approval. In the canonical Goal graph this gate runs within `complete-work`; an adapted graph may expose it explicitly after qualification. The explicit Epic plan-handoff artifact is not a Task-plan gate. |
| Intermediate Milestone | Same frozen candidate; Task Evaluator and at least two non-authoring Executor reports, checks and dispositions | Coordinator decides continuation within the selected Task work phase (`complete-work` in the canonical Goal graph), keeping the Task goal active. This does not complete the Task or grant its completion commit. |
| Task result | Task Evaluator's original result assessment and at least two non-authoring Executor reports for the complete candidate | Epic Evaluator receives the actual candidate and findings after Task Evaluator passage. |
| Epic-context Task approval | Epic Evaluator's distinct scoped assessment of that same candidate and original sources | Coordinator's final project/product review requires this approval and the Task approval. Preserve unfinished future-Task criteria; do not turn this checkpoint into a global Epic pass. |
| Task acceptance and finalization | Applicable Task/Epic approvals, Coordinator decision, current checks and exact authorized candidate | The member-Task Goal's final assessment concerns its Task goal and due Epic obligations. Its achieved gate needs pass and zero mandatory gaps for that goal; retain the Epic-wide scoped report separately. Only the Coordinator commits and verifies the result. |
| Assembled Epic and closeout | Fresh integration reviews, Epic Evaluator assessment, Coordinator review and actual user acceptance when due | Validation-family execution assesses the assembled Epic; the closeout Goal consumes applicable validation evidence and focused closeout assessment. Delegated Task acceptance cannot satisfy final user acceptance. |

Preserve both Evaluator reports even when a selected node has only one assessment
slot. Reference additional original assessments in the existing handoff/evidence
basis or qualify an appropriate adapted definition; never overwrite provenance
or put a global Epic report with future gaps into a member-Task achieved gate.
Do not label internal Executor findings as route-specific provider evidence.
One report may cover compatible obligations, including a combined final
Milestone/Task boundary, but cannot count as multiple independent reviewers.

### Additional technical review

Internal plan/result Executor reviews and Evaluator assessments are distinct
from selected Mulgae, Subagent Review or Herdr Review operations. Add a technical
review at approved useful boundaries rather than automatically stacking every
route on every Task. Preserve a selected route's prerequisites, team, authority,
result/ordinal and finding contracts. Two internal Executors do not constitute
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

This design adds one skill with existing Handler/Validator behavior
preserved. Planning alone requires no migration or tool update. The implementing
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

- Establish the single Squad collaboration contract and native-first scope without
  changing existing handlers or the generic Evaluator's default permissions.
- Define actual native readiness, inheritance, context, result and lifecycle
  discovery; distinguish unsupported features from missing private telemetry.
- Define source-based plan/result criteria, scoped Epic approvals, independent
  authorship and the permission-enforcement disclosure.
- Define detailed Task plan assessment, mandatory Epic plan assessment of
  direction/prior-output use/downstream handoff, and concise Coordinator intake.
- Define shared necessity criteria for proposed work and review corrections,
  including unjustified additions as rework and new Task team contexts.
- Define the phase-to-record mapping, intermediate-Milestone boundary and bounded
  design continuation, including `new-feature` eligibility and return handoffs
  for the new entrypoint while preserving existing callers.
- Define profile omission, explicit CLI/model routing, effort defaults, input
  conflicts and the boundary that blocks explicit profiles until their required
  EPIC-028 execution, commit and recovery integration is complete.
- Acceptance: assignments can explain and preserve each required role, native
  limit and actual candidate; unsupported execution cannot produce fake passage.

### TASK-148: Native Squad collaboration

- Add the explicitly invoked Squad entrypoint and supported invocation modes,
  with conditional detail in linked references.
- Accept omitted-profile native delivery; recognize explicit profiles and report
  the unimplemented external route. Do not run those roles natively unless the
  user directs a configuration change.
- Implement direct native role assignments, independent plan and result reviews,
  both scoped plan passes, Coordinator Writer assignment and bounded corrections.
- Start new Task teams, preserve same-Task corrections and apply scope/necessity
  assessment to both plans and actual results.
- Preserve actual results, context limits and configuration across sequential
  scheduling, direct helpers, descendants and one-shot replacements.
- Acceptance: the same candidate receives the required independent assessments;
  implementation waits for both plan passes on the current revision and the
  Coordinator's assignment, authors cannot review their work and
  uncertain Writer activity prevents transfer. Unjustified additions cannot pass
  merely because required behavior works or reviewers requested them.

### TASK-149: Squad execution and commit authority

- Connect Squad's actual owner to adaptive Goal/Validation admission, assessment,
  recovery and authorized commit handoffs; support explicit Podway opt-out.
- Carry exact candidate acceptance and separate member/correction/conditional
  closeout grants through the Coordinator's required commit tooling.
- Add focused behavioral checks for changed executable boundaries and retain
  installed managed copies and admitted snapshots unchanged.
- Preserve legacy reference mappings while admitting the real Squad owner;
  implement the no-additional-technical-review state and assessment consumption.
- Connect approved design handoffs and current session recovery to the original
  collaboration owner, preserving Design approval and delivery-input commit rules.
- Acceptance: no handler impersonation, duplicate native goal creation, grant
  reuse or per-Task user acceptance pause; old caller behavior and retained-bundle
  resume remain intact, including absence of an additional technical review.

### TASK-150: Squad integration and recovery

- Complete fresh integration reviews, Coordinator project/product review,
  disagreements, Task reopens and authorized correction/closeout handling.
- Recover missing output, interrupted roles, changed candidates, hook changes
  and committed-but-not-finalized work without losing findings or replaying effects.
- Distinguish closeout-only edits, rejected or stopped outcomes, implementation
  rework and Task reopens through the applicable native lifecycle.
- Acceptance: integration cannot be inferred from Task passes, both Task
  approvals apply before completion, actual user acceptance gates final closeout,
  and every needed result/configuration is retained before helper retirement.

### TASK-151: Squad verification and documentation

- Verify the committed installed candidate using the repository's UTM policy,
  exercising native collaboration, failure/recovery and existing-handler paths.
- Cover Codex and Claude native scenarios with actual results where available;
  identify unverified harnesses and capability gaps rather than generalizing
  observations or imposing cross-harness proof as ordinary startup admission.
- Require actual installed end-to-end observation for at least one named supported
  native harness; unobserved harnesses do not acquire a passing result.
- Complete Master's separate functional verification, keeping source checks,
  installed observations and actual Epic acceptance distinct.
- Promote implemented contracts to capabilities, workflow/orchestration specs,
  architecture, testing and public guidance as affected. Preserve this shared
  dossier for EPIC-028's remaining Herdr and mixed-execution requirements.

### TASK-152: Squad profiles and capabilities

- Extend the same entrypoint's profile interpretation for independent role routes,
  common/scoped Evaluators, explicit Executor pools, effort default and installed
  CLI model/effort controls without a universal launch syntax.
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
- Acceptance: caller/layout failures use supported Herdr recovery without raw
  layout fallback or an unapproved route change. Required explicit roles remain
  external, omitted roles remain native, and the Coordinator reads actual
  complete results without interactive-prompt injection or fake multi-agent provenance.

### TASK-154: Squad mixed delivery and commit integration

- Reuse the shared plan/result/Task/Epic/Coordinator sequence and Writer rules
  while preserving each configured role route and optional Coordinator helpers.
- Apply the same necessity criteria and new-Task context boundaries to native,
  Herdr and mixed teams.
- Extend and verify Squad's existing workflow owner and adaptive execution/commit
  handoffs for mixed execution, Podway opt-out and selected technical reviews.
- Reuse the no-additional-technical-review state and preserve retained bindings,
  including native-only Squad bundles, when recovering or extending sessions.
  Do not create a second owner, relabel a bundle or replay completed effects.
- Acceptance: the same candidate and current approvals reach Coordinator-owned
  commits; no existing handler, provider-review team or acceptance source is
  relabeled as Squad evidence, and required reviews use their configured routes.

### TASK-155: Squad mixed recovery and configuration reporting

- Recover native handles, uncertain external submissions and existing results
  before replay; settle modifying descendants across both routes and preserve
  replacement findings, route/profile selection and authority.
- Collect minimal public configuration for every participating role/descendant,
  including changes and closeout helpers, before exact owned-session cleanup.
- Acceptance: pane loss is not proof of termination, uncertain writes block
  handoff, matching profiles may be grouped only with their scopes retained,
  and applied/observed/unconfirmed settings are reported honestly.

### TASK-156: Squad mixed verification and documentation

- Verify available same-CLI and cross-CLI Herdr execution, all-native preservation,
  common/scoped direct Evaluators and mixed roles, correction and closeout.
- Cover external Executors with native Evaluators, native Executors with external
  Evaluators, and native Epic with explicit same-CLI external Task Evaluator.
- Exercise unsupported profile/control and failure/recovery paths; distinguish
  synthetic contract checks from real account/model availability and observed
  settings. The seven examples are not a mandatory seven-profile live test matrix.
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
| Normal multi-Task delivery | Each plan precedes implementation; current Task and Epic approvals precede Coordinator acceptance and a verified Task commit. | TASK-148 / TASK-154; both |
| Plan defect or material design change | Refresh affected plan assessments before implementation; both Evaluator passes apply to the same revision before Coordinator Writer assignment. | TASK-148 / TASK-154; both |
| Task plan direction and continuity | Every plan receives detailed Task review and an Epic review of direction, verified prior-output use and downstream deliverable design, including plans with no material cross-Task change. | TASK-147, TASK-148 / TASK-154; both |
| Role-scoped planning context | Actual concise assessments and source references reach the Coordinator; the Epic role retains consequential continuity decisions and the Task role retains detail. Concrete concerns allow targeted source inspection; final product review remains substantive. | TASK-147, TASK-148 / TASK-154; both |
| New Task team | Each new Task starts distinct Executor and Task Evaluator instances with fresh conversations where supported, concise source-based handoffs and disclosed inheritance limits; same-Task roles remain recoverable through commit verification while the Epic Evaluator retains continuity. | TASK-147, TASK-148 / TASK-153, TASK-154; both |
| Executor scope expansion | A plan or result adds an unsupported feature, abstraction or restriction; required behavior working does not prevent rework of the unjustified addition. | TASK-147, TASK-148 / TASK-154; both |
| Reviewer scope expansion | An Evaluator or Coordinator proposes optional hardening, an unsupported prerequisite or disproportionate tests; the team excludes it from mandatory work despite reviewer agreement. | TASK-148 / TASK-154; both |
| Necessary internal implementation | A required outcome needs an internal mechanism or defect correction omitted from the design detail; a concrete necessity basis allows it without demanding literal specification of every implementation choice. | TASK-148 / TASK-154; both |
| Required and excessive verification | Required checks and tests for reachable failure paths remain due; speculative or implementation-mirroring tests are excluded, and sufficient evidence permits pass without extra tests. | TASK-148 / TASK-154; both |
| Cumulative restrictions and rewritten docs | Epic review catches normal supported user scenarios blocked by accumulated restrictions; agent approval or documentation changed to match those restrictions does not establish scope authority. | TASK-150 / TASK-154, TASK-155; both |
| Result defect or missing evidence | Required corrections/evidence are distinguished from preferences; due gaps prevent passage. | TASK-148 / TASK-154; both |
| Coordinator/Evaluator disagreement | Original findings remain visible; focused evidence resolves readiness without forced consensus or evaluator shopping. | TASK-150 / TASK-155; both |
| Changed candidate | Affected checks and approvals are refreshed or explicitly reaffirmed by the responsible Evaluators. | TASK-149 / TASK-154; both |
| Limited native capacity | Native independent reviewers can run sequentially with complete actual results and preserved scope, including in mixed teams; roles are not impersonated or omitted. | TASK-148 / TASK-153; both |
| One-shot/replaced Task or Epic role | Original sources, candidate, findings and remaining authority survive; restored reports do not create fresh approval. | TASK-148 / TASK-155; both |
| Different worktree or snapshot | Required reviews inspect the integrated acceptance candidate, including owned dirty/untracked content. | TASK-149 / TASK-154; both |
| Native permission limit | Assignment-only read-only restrictions are disclosed; unsupported technical isolation is never claimed. | TASK-147 / TASK-153; both |
| Uncertain Writer/background work | No next Writer begins until modifying activity is safely settled. | TASK-148 / TASK-155; both |
| Truncated output or uncertain submission | Existing output/operation is inspected first, without duplicate implementation or a disguised new review. | TASK-148 / TASK-155; both |
| Hook change or pending finalization | Substantive post-review bytes get affected reassessment; an existing commit is not replayed. | TASK-150 / TASK-155; both |
| Final integration without a new diff | Fresh independent integration and Coordinator review still occur; no empty commit is manufactured. | TASK-150 / TASK-154; both |
| Same-CLI explicit profile | The explicitly configured role uses Herdr while omitted roles stay native and the Coordinator's session remains unchanged. | TASK-153; Herdr/mixed |
| Distinct Evaluator roles | Direct distinct Epic and Task instances receive original criteria and separate scoped approvals; optional descendants do not replace direct management. | TASK-148 / TASK-153; both |
| Common/scoped explicit Evaluators | A common profile expands into two direct Herdr roles; scoped entries affect only their roles, and omissions stay native. | TASK-152 / TASK-153; Herdr/mixed |
| Unsupported profile or effort | Report the limitation and proposed alternative; changing the requested profile or route requires user direction. | TASK-152; Herdr/mixed |
| Configuration replacement/descendants | Final reporting includes actual applied controls and available confirmation, with unknown values retained. | TASK-150 / TASK-155; both |
| Podway default, opt-out and resume | Correct owner, source and pending lifecycle remain intact; no in-place relabeling or duplicate goal is introduced. | TASK-149 / TASK-154; both |
| Selected additional technical review | Route-specific team, result, source transmission and authority remain distinct from collaboration assessments. | TASK-149 / TASK-154; both |
| Final user acceptance | Only actual user acceptance unlocks the conditional closeout commit; delegated Task acceptance is attributed to the Coordinator. | TASK-150 / TASK-154; both |
| Existing workflows | Handler/Validator defaults, admitted sources and generic Evaluator permissions remain unchanged. | TASK-149 / TASK-154; both |
| Intermediate versus final Milestone | Intermediate reviews preserve the active Task; only the completed Task reaches completion acceptance and its normal commit grant. | TASK-148 / TASK-154; both |
| No additional technical review selected | New-owner definitions and consumers accept the explicit state without provider execution, a fake waiver or missing collaboration reviews. | TASK-149 / TASK-154; both |
| Pre-upgrade retained bundle resume | Legacy Goal/Validation source and binding identities remain usable after new callers are admitted. | TASK-149 / TASK-154; both |
| Missing dossier or semantic owner | Execute enters bounded design, preserves its approval/commit rules and ends with an exact new-conversation Squad invocation carrying explicit profiles and omitted roles. Waiver and active-session rules remain due. | TASK-147, TASK-148 / TASK-152, TASK-153; both |
| Final rejection or requested changes | Record-only edits and implementation changes follow their respective lifecycle and affected review paths; revised final content needs actual acceptance. | TASK-150 / TASK-155; both |
| Stopped before achievement | Pending effects and unmet obligations remain visible; a stopped assessment neither resumes work nor declares completion. | TASK-150 / TASK-155; both |
| One Executor profile, several instances | A single approved profile supplies distinct authoring and non-authoring instances without an invented provider-diversity requirement. | TASK-152 / TASK-153; Herdr/mixed |
| Cold validation after collaboration delivery | An explicitly invoked epic-validator resolves Squad-origin evidence through its existing cold-validation contract. | TASK-151 / TASK-156; both |
| Unsupported native role | Report unsupported creation or matching configuration and preserve unaffected preparation; no impersonated roles or switch to Herdr without user direction. Fully external roles do not require optional native support. | TASK-147, TASK-148 / TASK-153; both |
| No role profiles | All required roles use matching native instances; Herdr availability is not an admission condition. | TASK-148 / TASK-153; both |
| External Executors only | Native Epic/Task Evaluators assess Herdr Executor work; required independent Executor reviewers use distinct instances of the supplied pool. | TASK-153 / TASK-154; Herdr/mixed |
| External Evaluators only | Explicit Evaluators use distinct Herdr sessions while omitted Executor assignments stay native. | TASK-153 / TASK-154; Herdr/mixed |
| Native Epic and same-CLI external Task | An omitted Epic profile uses the Coordinator's native configuration; explicit Codex Task and opencode Executor profiles use Herdr with their own resolved settings. | TASK-153 / TASK-154; Herdr/mixed |
| Omitted effort versus omitted profile | Explicit CLI/model with omitted effort applies high; an omitted whole profile matches the Coordinator's current effort. | TASK-147 / TASK-152; both |
| Invalid or conflicting input | Partial/empty profiles, an empty explicit Executor list or common plus scoped Evaluator entries are resolved before affected agents launch. | TASK-147 / TASK-152; both |
| Native-first and partial Herdr extension | Explicit profiles remain unimplemented until required execution, commit and recovery integration is complete; no native substitution without user direction. Existing native-only delivery remains usable. | TASK-147, TASK-148 / TASK-153, TASK-154, TASK-155; both |
| Unavailable route and resume | Preserve selected roles, pending findings and actual route-specific handles; route/profile changes need user direction. Omitted roles match the current Coordinator, with inheritance changes disclosed and prior records retained. | TASK-150 / TASK-155; both |
| Blocked external permission/question UI | Inspect and preserve the same operation, apply the installed Herdr permission contract, obtain a required user answer and retain the Writer restriction while modifying activity is uncertain. | TASK-153 / TASK-155; Herdr/mixed |
| Native-only retained Squad session | The Herdr extension preserves the original Squad owner, binding identity, grants and pending operations; no in-place route change or effect replay occurs. | TASK-154 / TASK-155; Herdr/mixed |

Automated tests cover objective structure and executable helper behavior where
applicable. Do not add prose matching or automated LLM evaluations to `make test`.
Structural checks do not establish skill behavior. Reuse the existing guest-side
verification facilities for candidate installation, and report manual/installed
results only for the actual candidate, harness and configuration observed.

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
