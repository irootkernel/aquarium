# Epic Squad collaboration contract

## Status and authority

The [epic-squad entrypoint](../skills/epic-squad/SKILL.md) and
[native coordination instructions](epic-squad-native.md) define the native
collaboration assignments. The [execution contract](epic-squad-execution.md) connects qualified definitions,
admission, current evidence, integration and recovery through commit/design
consumers. TASK-151 verifies installed native delivery. Entrypoint discovery or agent launch alone does not enable delivery.
Herdr and mixed role execution remain unavailable until their execution, commit
and recovery integration under EPIC-028 is complete.

The roadmap (`docs/roadmap/README.md`) owns work identity, dependencies and
lifecycle. The shared dossier (`docs/todo/TODO-EPIC-COLLABORATION.md`) owns the
remaining detailed execution requirements for EPIC-027 and EPIC-028.
This contract defines their shared collaboration semantics without changing
existing Handler or Validator behavior, report schemas or admitted sessions.

## Product quality and scope

Deliver working software that satisfies its original requirements, follows
understandable module boundaries and dependency direction, and supports justified
extension without speculative abstractions. Verify required reliability and
reachable failure/recovery paths. Check latency, throughput or resource use when
the requirement or changed path makes performance material under the intended
workload. A durable structural repair may be necessary even when a smaller patch
is possible; a new benchmark system is not a default Task obligation.

Assess missing requirements and unnecessary additions in both plans and results.
Every role, including the Coordinator and reviewers, must connect material new
features, abstractions, restrictions and verification work to an existing
requirement and a reachable problem. Necessary internal implementation choices
need no separate product approval. Product scope expansion or a material change
of design direction needs the user's decision under the existing authority.
Agent agreement or documentation rewritten to match an addition supplies no
missing authorization. Check cumulative restrictions against supported user
scenarios across Tasks.

For material validators, harnesses, parsers, watchers or other support tooling,
state the current obligation, concrete gap, simplest sufficient approach and
stopping condition in the existing plan or assignment. Reuse repository commands
and installed capabilities first. Return substantial unplanned support expansion
to the Coordinator, who admits, narrows or rejects it within existing authority.
Ordinary bounded helpers and task-local checks need no new approval stage.
Judge cumulative need and maintenance cost without a line quota. A support-tool
defect blocks delivery only when safe work, current acceptance or trustworthy
required evidence depends on it. Safely narrow or stop support work that no
longer advances an outcome or reduces a justified uncertainty; useful diagnosis
can advance work without changing product code.

## Roles and assignment scope

| Role | Squad responsibility | Corresponding Handler role |
| --- | --- | --- |
| Coordinator (C) | Keeps the current CLI/model/session, owns scope, dispatch, product review, Writer transfers, delegated acceptance and commits. | Existing Coordinator, with unchanged duties. |
| Epic Evaluator (EE) | Retains Epic direction, architecture, prior outputs, downstream obligations and integration context. | The existing single logical Evaluator across member Tasks, corrections, integration and closeout. |
| Task Evaluator (TE) | A distinct, directly managed Task-scoped evaluator of detailed plans and results. | No new role or instance; Handler's existing Evaluator keeps its Task duties. |
| Task Operator (TO) | Performs assigned research, planning, implementation, verification, documentation or independent review. | Existing Worker/Executor performing bounded delivery. |
| Support Operator (SO) | Optional factual investigation, assigned checks, log extraction or supported observation. | Label for an already-authorized helper; no mandatory pool or new step. |

Writer is temporary write authority, Reviewer is an assignment duty, and Leader
is optional coordination within an assignment. They add no top-level roles.
A Leader returns actual descendant results and a synthesis without extra
acceptance, Writer or commit authority. Support Operators supply original facts
and execution results, never verdicts, finding closure or independent-review
coverage. They do not select routes, transfer Writer, modify the index or advance
Podway. Assigned reports and isolated check outputs remain within their bounded
permissions; no permanent support team or support approval node is required.

Output-producing TOs and SOs follow [artifact cleanup](artifact-cleanup.md).
The creator owns disposable build/test outputs, and the Coordinator verifies
shared outputs, cleanup results and retained-output handoffs before role
retirement or the next Task. Unresolved cleanup blocks successor Tasks and
successful completion separately from test and assessment results. Read-only
roles retain their assigned limits.

Retain machine roles `coordinator`, `executor` and `evaluator` and ordinary
identifiers such as `aquarium.assignment/v3`, `aquarium.executor-handoff/v3` and
`aquarium.evaluator-assessment/v3`. TO assignments use executor semantics; SO
assignments narrow those execution permissions. EE/TE assignments use evaluator
semantics with explicit scope. Carry human role, duty and Task/Epic/support scope
in the existing assignment context. Display names require no protocol migration,
node rename or rewrite of historical reports.

The [ordinary contract](ordinary-agent-orchestration.md) remains the default for
existing callers. Squad must define its scoped evaluator assignments explicitly:
project files are read-only, assigned non-mutating checks and supported native
descendants may be permitted, and proposed mutations return to the Coordinator.
The unchanged [goal-evaluator](../skills/goal-evaluator/SKILL.md) prohibits check
execution and nested dispatch; invoking it unchanged cannot grant Squad's wider
assignment capabilities. Handler gains no separate TE, Squad panel, profile
interface or mandatory support participant from this vocabulary.

## Invocation, context and design continuation

Require an explicit invocation with one mutable repository, its canonical roadmap
and exactly one delivery Epic. Standing groups such as EPIC-000 retain their
repository-defined Task workflows. Use the existing meanings of `execute`,
`plan-only`, `plan-handoff` and `resume`. Inspect applicable instructions, original
canonical sources, implementation, dependencies and Git state; preserve unrelated
staged, unstaged and untracked work. Maintain affected documentation under
[directory guidance](directory-agent-guidance.md) without inventing adoption or
making an absent guide a prerequisite.

The Context Brief identifies purpose and users, conventions and architecture
sources, Epic/Task outcomes and dependencies, required and prohibited effects,
criteria and user scenarios, non-goals, candidate or plan revision, Writer,
result channel and unresolved questions. Resolve discoverable questions first.
Give each assignment readable original sources and enough local context for its
scope. Keep one active Task delivery goal in dependency order. A workflow call,
plan approval or Podway goal does not authorize a Codex goal; its native contract
requires an explicit user request. Read-only preparation of later work does not
activate another delivery goal or require a second state store.

Apply [execution-SOT routing](epic-execution-sot.md). For `execute`, ordinary
feature work needing a dossier or semantic clarification continues through
`new-feature` in the same conversation with the exact repository, roadmap and
Epic identity. Preserve Design approvals and the delivery-input commit boundary.
After successful design delivery, return an exact new-conversation `epic-squad`
request carrying supplied profiles and omitted roles; do not automatically resume
delivery in the design conversation. Report pending commit authority or other
blockers. Other modes report the continuation. Refactor, diagnosis and new-project
work keep their appropriate explicit routes. Missing meaning cannot be waived;
the shared composite-SOT waiver and active-session recovery rules still apply,
without a separate member-Task dossier waiver. Implement this caller/return path
in the shared consumers before claiming it works.

## Profiles and native readiness

Resolve each role independently before launch. An omitted whole profile selects
the current Coordinator's native harness, model and effort. Keep configuration
inheritance separate from conversation inheritance. A native default needs no
Herdr installation or inspection. Explicit CLI plus model selects Herdr even
when they match the Coordinator; omitted effort in that explicit profile means
`high`. An explicit effort remains unchanged. These external inputs must be
recognized and reported unavailable during the native-only implementation,
before affected delivery or design continuation. Never silently run them natively.
Unaffected authorized design work may continue with the blocker visible.

Accept `Epic Evaluator:` and `Task Evaluator:` profiles or the common
`Evaluator:` shorthand for both. Common and scoped entries together conflict;
there is no override precedence. Common configuration still denotes two direct
instances. An omitted scoped role remains native. `Task Operators:` accepts one
or more profiles; `Task Operator:` denotes a one-profile pool. CLI and model are
both required for an explicit profile. Reject partial/empty profiles and an
explicit empty TO pool before launch; resolve ambiguity without guessing a CLI
or splitting an opaque model ID at its internal slashes.

`Support Operators:` is optional. Omission or an empty support pool launches no
support team and leaves authorized native factual helpers available. An explicit
support pool uses the same profile rules and cannot fill required TO/evaluator
coverage. Disclose unavailable optional support before reassigning its obligation
to an authorized existing role; user-required participation remains required.
Profiles do not configure separately selected technical-review operations.

The existing Squad consumer's `resolve_profiles` reads structured profiles from
`target.squad.profiles`. Use the role keys above without trailing colons, with
`cli`, `model` and optional `effort` strings in each profile. Plural Operator
keys contain lists; the singular Task Operator key contains one profile. Resolve
ambiguous free-text input before constructing this object. Do not split model IDs
or infer missing fields. Unknown roles or profile fields require input correction.

The resolver returns the unchanged requested object and independently resolved
role configuration. Native configuration refers to the current Coordinator;
resolve it again on resume and retain earlier observations separately. Common
Evaluator configuration expands to separate EE and TE entries without creating
agents. Profile resolution runs before Squad source preparation and dispatch,
and validates supplied Squad profiles on Design return. It performs no CLI
inspection, authentication, launch or availability check. Explicit Herdr profiles
still block delivery until execution, commit and recovery integration is complete.

Before an affected role launches, the Coordinator reads the applicable installed
paired tool contract and native model, effort and permission controls. Resolve
display names to the actual CLI model ID without changing the requested model.
On launch, resume and Writer transfer, distinguish requested configuration,
applied controls, public confirmation and unconfirmed values. Unsupported effort,
an unavailable model or a mismatch needs an explicit disposition and proposed
alternative; changing the profile or route needs user direction. Assignment-only
read-only instructions establish no OS isolation. These checks do not authorize
host-default edits, probe frameworks or an automatic fallback.

Discover native creation, result retrieval, continuation, termination, context,
configuration and permission controls through current public tools, paired
skills, complete relevant help and startup observations. Use a bounded smoke
check only for a concrete unresolved prerequisite under actual authority. Direct
EE, TE and delivery/review TO instances suffice; nesting is optional. All native
roles, selected helpers and descendants match the Coordinator through supported
inheritance or explicit matching controls. Do not change the Coordinator or
select per-role alternatives. Private model telemetry is not required when
supported inheritance applies; distinguish unconfirmed observations from an
unsupported required capability.

Use supported read-only controls where available. When enforcement is assignment
only, disclose that limit without claiming OS isolation or changing host defaults.
A required unsafe or unsupported action stays blocked; finish unaffected work
without impersonating roles or switching route, CLI or model without user
direction. Recheck capabilities on resume, retain earlier configuration records
and disclose changed native inheritance. Record requested, applied, observed and
unconfirmed settings separately, including relevant descendants and replacements.

Start new delivery/review TO instances and a dedicated TE at each Task, with fresh
conversations where supported. Carry concise verified outputs, consequential
decisions, remaining obligations and source references. Disclose unavoidable
inherited conversation; do not describe it as clean context. Retain EE context
across Tasks and useful same-Task context through correction and commit
verification. Schedule within actual concurrency, thread and depth limits,
including sequential review waves without reducing required coverage. Before
release or replacement, collect results, configuration, findings, candidate and
pending operations; settle modifying activity and descendants. Restore those
inputs to a replacement on the same route. Restored reports are not fresh passes.

## Plan and result assessments

Use independent non-authoring instances. Plan authors cannot independently assess
their plan. Result review excludes both implementation authors and authors of the
guiding plan; feedback or factual scouting alone is not authorship. A reviewer who
becomes a Writer needs replacement independent
coverage. Matching profiles establish neither model diversity nor independence
by themselves. First-assessment briefs include original sources and factual
evidence without peer verdicts; compare findings after independent views form.

Record risk and its basis in the Task plan. Standard first plan and result panels
use TE plus one distinct independent TO; elevated work uses TE plus two with
complementary concerns. Elevate when a change affects shared contracts,
persistence, authorization, concurrency, recovery, process lifecycle, material
architecture/performance obligations or other high-consequence behavior, or when
its impact cannot yet be bounded. Recheck actual delivery and raise coverage
for new risk; lower it only when its triggering premise is disproved.

1. TO prepares the exact Task plan: required behavior, earlier outputs, downstream
   interfaces, risks, checks, docs and necessary support work with its stopping
   condition. Use intermediate Milestones only for actual delivery dependencies
   or review boundaries. Assess intermediate results and resolve findings before
   C decides continuation, keeping the Task goal active. Task-completion acceptance
   and its normal commit remain Task-boundary effects; checkpoint commits need
   separate authority.
2. TE owns detailed feasibility, requirement coverage, assumptions, edge cases,
   verification and documentation. Collect the required independent TO plan
   reports, resolve required findings and establish Task plan readiness.
3. EE assesses every ready Task plan's Epic direction, use of verified prior
   outputs/contracts and design of downstream handoffs. Read the relevant exact
   plan, original sources and prior outputs directly. This narrow assessment is
   due even when no material cross-Task change is proposed; unfinished future
   implementation is not a current requirement.
4. C reads the concise actual TE/EE assessments, plan identity, decisions,
   exceptions and source references. Both plan scopes must be satisfied for the
   assigned revision, including eligible verified deltas, before C assigns
   implementation to the sole Writer. C investigates concrete concerns without
   adding a third routine plan review or importing full planning transcripts.
5. Freeze the delivered candidate after implementation, self-verification and
   docs. Obtain first result-panel assessments and EE's first Task-contribution
   assessment. C's substantive project/product review, independent assessments
   and required nonconflicting checks may proceed concurrently on those same
   bytes. Each judgment waits for the evidence it needs; withhold peer conclusions
   until independent first views form and reconcile one complete issue set.
6. Establish current readiness from actual first assessments, eligible closures,
   applicability, due checks and C's product judgment. All due criteria and
   substantive disagreements must be resolved before exact delegated acceptance.
   Final assembled-Epic assessment remains independently due even if every Task
   passes: EE and at least two fresh non-authoring TOs inspect original
   requirements, integration and current artifacts alongside C's product review.

Report phase, exact scope/candidate, evidence and reasons with `pass`, `rework`
or `evidence-needed`. Preserve original criterion states and unassessed compound
parts, including future global gaps. A scoped Task contribution pass is not a
whole-Epic pass. C personally inspects architecture, correctness, maintainability,
compatibility and affected user journeys, including CLI/API error and recovery
behavior; collecting favorable verdicts does not satisfy that duty.

## Corrections, deferral and evidence applicability

Establish the failing property, candidate, requirement, impact and cause before
choosing a correction. Preserve original reports, findings and priorities.
Current correctness, acceptance, security/privacy, data integrity and required
reliability/performance defects must be fixed before affected acceptance or
dependent work. Missing mandatory evidence or unknown impact stays open. Record
independent future improvements with source, reason/impact and re-entry condition
in the existing deferred-feedback owner; Epic-sized work goes to the TODO owner
without automatic roadmap adoption. Missing owners follow their approval path.
Invalid findings and preferences receive reasoned dispositions, not repairs or
clean-report reruns. A required current obligation cannot depend on deferral.

Use the [finding-disposition](finding-disposition.md) meanings and
[execution-incident policy](review-contract.md#reviewer-instruction-deviations).
Record the cumulative delta, affected consumers/criteria, retained evidence,
checks, review scope and next owner in existing reports. Severity, validity,
test scope and review depth are separate decisions; mixed deltas retain every
nonlocal obligation.

| Correction | Required verification and assessment |
| --- | --- |
| Meaning-preserving prose, comments or formatting | Readback and applicable documentation/link/integrity checks; eligible C closure without product tests or routine TE/EE recall. |
| Obsolete display-string or bounded snapshot expectation | Establish intended meaning independently, change only intended literals, preserve inputs/assertion strength, run referring and previously unexecuted required cases; eligible local closure. |
| Isolated approved behavior | Direct deterministic behavior/failure checks and affected mandatory checks; use `local-verified-fix` only when no new design, contract, security or concurrency judgment is needed. |
| Bounded behavioral judgment | Affected behavior/consumer checks and TE plus one non-authoring TO delta assessment; a nonbehavioral change failing local eligibility may use TE only. |
| Elevated contract, security, data, lifecycle or concurrency correction | Relevant consumer/failure checks and required broader gates, with TE plus two non-authoring TOs on affected guarantees. |
| Missing run, wrong directory, truncated report or execution incident | Recover the same operation/result or perform the missing check; repair only the affected evidence guarantee. |
| Materially changed design/acceptance premise or unbounded impact | Pause affected implementation, reassess the affected plan scopes and broaden checks to establish the new basis. |

Local closure needs the substantive first assessments, a finite understood delta,
sufficient direct verification and no unresolved substantive objection. It cannot
replace missing first coverage or manufacture an evaluator pass. Normative
instructions, error codes, configuration/data semantics, numeric/boolean
expectations and changes to mocks, assertions, timeouts or test selection are not
editorial merely because they live in a test or document. Coordinator-authored
semantic corrections need focused non-authoring confirmation. Keep the original
finding owner engaged while its judgment is unresolved; use focused evidence
without evaluator shopping or majority voting.

Re-engage EE for changed cross-Task contracts, dependencies, downstream premises,
Epic scope or its outstanding finding. Otherwise record why that scope is
unchanged; uncertainty calls for an EE assessment of that scope only. EE is the
primary integration/closeout assessor. Reopen the Task before recalling a retired
TE for changed Task completion. A material plan change refreshes affected scopes;
bounded clarification or editorial change within reviewed direction need not
restart every plan assessment.

Reuse prior checks/assessments only where the cumulative delta preserves their
inputs, coverage, dependencies and environment. Verify changed behavior and
mandatory cases left unexecuted by fail-fast. Preserve failures and establish
their cause; later green reruns do not prove a flake or authorize weakened tests.
Honor exact-final repository gates. Unknown impact or changed shared verification
premises require broader checks. A new hash, failed test or review request alone
does not require them. Full testing and full review need separate scope decisions.
Record reviewed basis, permitted verified delta, actual checks, original verdicts,
current closures and
remaining obligations; do not call the composition a fresh review or whole-suite
run. Stop correction when required properties are established.

## Writer, supervision and result intake

Only C assigns Writer for shared source, tests, docs, generated files and rewriting
commands. Children receive no inherited write grant; C does not edit project
files or the index while another Writer is active. Before transfer or freeze,
settle modifying commands, descendants and pending writes using supported
observations, read the actual changes and handoff, and revoke/end old access as
supported. A quiet diff, missing Git lock, finished parent turn or vanished pane
alone does not establish settlement. Coordinate checks sharing mutable outputs.

Use native lifecycle state, completion notifications and result channels for
routine supervision. Keep bounded/yielding waits on the same handle responsive
to peers; paired tools retain their own observer contract without a competing
poller. Inspect enough relevant output for blocked/unknown state, unclear
submission, unexplained overrun, exit or detection limitations, including a
partially detected permission/question UI. Quiet analysis is not failure and
console activity is not progress. Continue with a reason and next observation,
recover through supported controls, or report the concrete missing capability.
Elapsed time supplies no new cancellation authority.

A participant needing C or another role returns an actionable request through
the supported channel. If only a returned turn exposes it, end that turn instead
of waiting in a circular dependency. Observe other participants fairly. Do not
send terminal status prompts into active or uncertain turns; use only interactions
the native contract supports safely. Retrieve an uncertain submission/result
before redispatch and preserve its known handle and next owner.

Read complete current reports and match assignment, scope and plan/candidate
revision. Separate actual changes/findings, commands/inputs, exit/results, original
evidence and limitations. Keep failed, omitted and inconclusive results. Recover
truncation from the same operation; an allowed temporary-file fallback re-emits
the existing report and needs complete receiver readback. Never inject output or
permission requests into C's interactive user input. A notification, idle/done
status, report path or old visible pass does not establish the current result.

## Procedure and handoff boundaries

The roadmap owns product Tasks. Aquarium owns semantic scope, role dispatch and
joins. Podway owns immutable Procedure state, one active attempt, typed evidence,
declared rework and revision fences; it does not execute agents or judge truth.
Use current released Procedure capabilities without a Podway engine/CLI/API
extension or another registry, scheduler, mailbox or policy runtime.

Podway is default with existing explicit pre-session opt-out and in-progress
stop/recovery rules. Use one selected Goal-family session per member or
pre-validation correction and one Validation-family session for assembled
integration. Its audit-scoped correction groups and intermediate commits remain
inside that same Validation cursor, with whole-Epic confirmation pending. Final
record-only closeout uses the retained or restored Validation basis, with actual
exact-candidate EE and Coordinator assessment before user acceptance. Select an
adequate Goal closeout instead when its fit requires it, after settling Validation. Never nest a Goal/Task session under an active parent in one
worktree. Reuse adequate
Squad definitions, adapt only for a missing boundary, qualify exact source and
binding, and retain the self-contained bundle before start. Task identity,
criteria and role configuration are assignment data unless the definition changes.
Preserve old source/version mappings and binding identities when adding this
caller. EE continuity spans successor sessions; helpers need no extra graph.

| Exposed boundary | Evidence and permitted next action |
| --- | --- |
| Prepare and assess plan | TO plan, TE/panel reports and subsequent scoped EE assessment; implementation waits for both plan scopes and C's assignment. |
| Deliver and assess candidate | Settled Writer handoff, exact candidate, first independent assessments and due checks; C classifies the complete issue set. |
| Classify corrections | Source findings, delta/impact, current/deferred obligations, applicability and checks; choose ready, local closure, affected/plan rework, evidence recovery or blocked boundary. |
| Settle or rework | Bounded Writer changes and actual verification, with only due independent judgment; current obligations decide re-entry scope. |
| Accept and finalize | Actual assessments plus permitted deltas, zero mandatory unmet/unverified criteria, C product judgment and exact unconsumed authority; verify commit and native finalization separately. |
| Validate Epic and close out | Independent assembled evidence and scoped remediation, followed by actual user acceptance and its conditional closeout effects. |

These are semantic boundaries, not prescribed node IDs. Do not bury them inside
legacy `complete-work`. One Action may join multiple independent read-only reports
and nonconflicting checks with original attribution while Podway retains one
cursor. C alone records and advances Decisions. A faithfully delivered negative
assessment completes its Action and follows the negative Decision; Action
completion is not a positive verdict or achieved goal.

Native rework invalidates its selected items. Preserve underlying original
artifacts only after checking current applicability, then re-record the current
composition with references and fresh fences. Do not revive stale records,
rewrite runtime databases, relabel an old test as rerun or substitute one report
for TE and EE coverage. Unknown or unreadable evidence remains open. Recover the
exact retained definition and binding, findings, checks, grants and live operations
without changing an active snapshot or replaying effects. Genuine missing topology
uses the existing consented successor contract.

Internal collaboration assessments are distinct from selected Mulgae, Subagent
Review or Herdr Review. Preserve any selected route's team, target, transmission,
ordinal, findings and recovery contract. Squad needs an explicit
no-additional-technical-review-required state across assignment, admission,
qualification, definitions, recovery and commit consumers. It means no extra
provider operation, never a waiver of collaboration coverage, fake provider
execution or a reinterpretation of existing callers' routes.

C alone invokes required commit tooling with `aquarium:epic-squad` as the real
workflow owner. Establish the disclosed execution envelope before work, including
delegated exact member/correction acceptance and their distinct commit grants.
Continue covered work without per-Task user-review pauses; uncovered effects need
their own authority. Carry exact candidate acceptance, lifecycle/record/release-note
decisions, reviewed basis and verified deltas, original results, checks and
separate unconsumed member/correction/conditional-closeout grants. Do not forge
a Handler handoff. Verify actual committed bytes, hooks and residue; refresh only
invalidated guarantees. A successful commit with pending native finalization is
recovered without creating it again. Final integration cannot be inferred from
Task passes. Actual user acceptance precedes final closeout, including no-change
outcomes; installation, host state, other repositories and publication keep their
separate authority.

Retain existing Handler/Validator final-evaluator, provider-review and cold-audit
contracts. Squad's internal integration does not claim a separate cold context.
Record any discovered forced update, shared migration or producer dependency as a
breaking impact before adopting it, with its migration and verification needs.
Never edit installed caches, skills, host configuration or managed copies to make
a candidate work. Candidate installation and installed functional verification
follow repository UTM policy. Structural checks establish no native progression
or behavioral pass; report actual candidate/harness observations and unverified
routes separately under [evidence residency](evidence-residency.md).
