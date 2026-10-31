# Squad role coordination

Use this reference only from an explicitly invoked
[epic-squad](../skills/epic-squad/SKILL.md). The
[collaboration contract](epic-squad-collaboration.md) owns shared semantics.
The [execution consumer](epic-squad-execution.md) connects qualified definitions,
current evidence, scoped integration corrections and commit/design recovery.
These source contracts establish no installed execution result.

## Execute resolved roles

Resolve the complete role request before creating participants. Omitted roles
follow the native instructions below; an explicit CLI/model profile uses Herdr
even when it matches the Coordinator. The mapped consumer attaches requested
configuration to each assignment's `target.role_execution`, identified by display
role, scope and instance. This field records no launch, applied settings or
permission isolation. Keep actual producer handles and observations in the
existing runtime handoff after creation.

For a multi-profile Operator pool, the Coordinator selects an approved profile
for each assignment instance in `target.squad.profile_selections`. Its shape is
`{display_role: {scope: [profile_index, ...]}}`, using zero-based indexes into the
corresponding supplied pool and instance order within that role/scope. A single
profile needs no selector. There is no rotation or implicit provider choice.
Optional support with no configured pool uses an authorized native factual
helper; it cannot replace an Evaluator or required independent TO. Profile
selection chooses configuration, never a shared author/reviewer instance.

For each explicit role, load the installed Herdr skill and applicable global
Herdr instructions before control operations. Verify the supported caller context
and allocate a helper through `dev-herdr --subagent-pane <name> --cwd "$PWD"`.
Use its returned pane and session. Keep the main tab unsplit and direct EE/TE
instances separate, including common-profile Evaluators. Caller verification
failure uses the skill's separate identify-caller/probe recovery. Layout failure
has no raw split, focus inference, inherited-ID or unapproved route fallback.

Inspect the installed CLI's actual kind, model, effort and permission controls.
Start it only in the verified available shell pane, using the requested model
and effort through that native contract. Preserve scoped permissions and check
available public confirmation before work. On resume and Writer transfer, reapply
supported controls as needed and verify their effects again. Report changed
defaults, unsupported controls and mismatches. A profile mismatch
or unmet required safety control blocks its affected action; missing private
model/effort telemetry remains unconfirmed. Changing a requested/defaulted profile
or route needs user direction.
Do not change host defaults or invent CLI flags, enforcement helpers or probes.

Use the same known agent for prompt submission, waiting and complete output
retrieval under the installed Herdr contract. Acknowledged submission, idle or
done is not a result. Inspect blocked startup, permission/question UI, uncertain
submission and timeout through that operation before recovery. Obtain any user
answer required by the installed skill; do not answer it with a normal work
prompt, resubmit, or launch a replacement while state is uncertain. Preserve
Writer restrictions until modifying activity and descendants are settled.

Read the original top-level assessments and supporting descendant reports before
admission. Match each to its assignment, exact target and scope. Record public
handles, requested/applied/observed configuration and unconfirmed settings before
retirement. Do not assume a descendant matched its parent or replace distinct
direct Evaluators with nested assistance. Recover truncated output through the
same operation, using only the installed skill's supported result fallback.
No result or question may be injected into the Coordinator's interactive input.

### Recover operations and retain configuration

Use existing runtime assignments, pending-operation records and actual native
handles. For Herdr, retain the returned session, pane and agent identity so output
is recoverable after the agent exits. A newly generated dispatch describes due
scope; it is not permission to replay a known submission. Resume the existing
operation with its original assignment and selected profile, retrieve its complete
result, then decide whether any new assignment is needed. Reconcile requests and
next owners fairly across routes. Inspect enough current screen or unwrapped
output to identify a partially detected approval/question dialog; an unchanged
state or short tail cannot rule one out. Follow the installed permission contract
and wait for a required user answer without broadening access or queuing another
work prompt.

Before replacing a participant, preserve original sources, candidate, findings,
checks, closures, selected profile, actual observations and remaining authority.
Use the same authorized route/profile unless the user directs a team change;
another approved TO pool entry remains available for suitable new work. Omitted
roles resolve against the current Coordinator on resume, with changed inheritance
disclosed and earlier records retained. Recheck supported model/effort/permission
controls without rewriting the old result or treating unavailable telemetry as a
new mandatory gate.

Pane loss is not termination evidence. Establish settlement of modifying native
and Herdr commands, descendants, background work and pending writes before Writer
transfer, candidate freeze or destructive cleanup. If termination cannot be
established, preserve the restriction and report the uncertain operation/owner.
A delayed pane cleanup alone does not invalidate an already verified Task.

Collect minimal available settings before exact owned cleanup, including the
Coordinator, delivery/review roles, support, descendants, replacements and closeout
helpers. Record role, Task/Epic scope, instance count, route/CLI, requested profile
or default, applied model/effort/permission controls, observed confirmation and
unconfirmed values. Matching records may be grouped only with scope/count intact.
Keep them with the existing result/handoff and update them for later participants;
do not audit unrelated home settings or copy credentials. Close only verified
owned helpers after result readback and supported lifecycle settlement. Preserve
the Coordinator, continuous EE and tabs still used by other helpers or the user.
Verify disposable/shared output cleanup or its retained-output handoff under the
[cleanup contract](artifact-cleanup.md) before advancing the Task.

## Assign native roles

Keep the Coordinator's CLI, model and session. Use its actual native subagent
facilities with supported configuration inheritance for every omitted role,
including selected helpers and descendants. Discover creation, retrieval,
continuation, termination, context, configuration and permission controls from
current public tools and paired skills. Private backend telemetry may remain
unknown; a missing required capability still blocks its affected operation.
Do not add a probe program, universal launcher or permission harness for routine
readiness. Finish unaffected preparation when a required action is unsupported.

Directly manage a continuous Epic Evaluator and a distinct Task Evaluator for
each Task. Start new delivery/review Task Operators at each Task and use fresh
conversations where supported. Pass concise verified prior outputs, decisions,
remaining obligations and readable source references. Configuration inheritance
does not require conversation inheritance; disclose inherited context without a
clean-context claim. Retain useful same-Task planning/correction context through
commit verification, then collect results and recovery context before retirement.

Schedule within actual active, retained-thread and depth limits. Independent
reviewers may run sequentially without reducing their required coverage. Direct
roles suffice without nested spawning. A role needing help returns a bounded
request; the Coordinator may assign a direct helper and return its actual facts.
Supported descendants remain within their assigned permissions and configuration.

Use ordinary `aquarium.assignment/v3` fields and existing machine roles. In
`work`, identify the human-facing role, duty and Task/Epic scope; `target` binds
the exact plan or candidate and relevant inputs. Supply original requirements,
current evidence, allowed/excluded effects, configuration limits, Writer status,
result channel and the required deliverable. No schema migration is needed.

For output-producing Task and Support Operators, include
[artifact cleanup](artifact-cleanup.md) scope and ownership in that assignment.
Operators clean their disposable outputs after the last consumer; the
Coordinator verifies shared outputs and any retained-output handoff before
retiring a role, starting the next Task or completing the workflow.

| Assignment | Machine role and actual work |
| --- | --- |
| Task Operator | `executor`: bounded investigation, plan, implementation, verification, documentation or independent review. A plan/implementation author cannot provide its independent result review. |
| Task Evaluator | `evaluator`: detailed Task plan/result assessment, scope and necessity, coverage, edge cases, checks, documentation and unresolved Task findings. |
| Epic Evaluator | `evaluator`: Epic direction, verified earlier outputs, downstream handoffs and scoped Task contribution; retain consequential integration context. |
| Support Operator | `executor`: optional factual source work, assigned checks, log extraction or supported observation. Facts/results only; no verdict, finding closure, Writer transfer, index or native progression. |

Keep evaluator project files read-only. A Squad assignment may permit supported
non-mutating checks and native descendants explicitly, while coordinated mutable
outputs and proposed corrections return to the Coordinator. Use these scoped
instructions with the [ordinary v3 report fields](ordinary-agent-orchestration.md).
Do not invoke the unchanged [goal-evaluator](../skills/goal-evaluator/SKILL.md)
to claim those wider permissions: its existing callers keep report-only scope,
including no checks or nested dispatch. Preserve all machine role and report IDs.

Only the Coordinator grants a bounded Writer assignment. Planning edits, when
needed, receive their own planning scope and no implementation authority.
Children inherit no write grant. Before transfer or freeze, establish settlement
of modifying commands, descendants, background operations and pending writes;
read the actual handoff and changes and end/revoke previous write access through
supported controls. Uncertain activity blocks transfer. A done parent, stable
diff, missing lock or vanished pane alone does not establish settlement.

## Task planning and first assessments

Give the delivery Task Operator the Context Brief and original Task outcome,
criteria, non-goals, dependencies and prior outputs. Its plan identifies the
exact design, downstream deliverables, risks, relevant behavior/failure checks,
docs and necessary support work with a stopping condition. Use a Milestone only
for an actual dependency or review boundary. Check the cumulative necessity of
new features, abstractions, restrictions and support work against the original
requirements; neither peer agreement nor rewritten docs supplies missing scope.

Record the shared contract's standard/elevated risk and basis. The first plan
and result panels use TE plus one independent TO for standard work, or TE plus
two with complementary concerns for elevated work. Keep every independent
assessor separate from authorship. Give first assessors original sources and
the exact revision with factual evidence, withholding peer verdicts and proposed
acceptance conclusions until their independent views form.

The TE reads detailed plan coverage, feasibility, assumptions, edges, verification
and docs and resolves required panel findings. When that Task scope is ready,
the EE reads the relevant exact plan, original Epic requirements and verified
earlier outputs. Every Task plan needs its scoped judgment of Epic direction,
correct use of prior outputs and downstream handoff design. An unchanged
cross-Task contract does not waive this first plan assessment; future Task
implementation is not due prematurely.

The Coordinator receives actual concise phase assessments, plan identity,
material exceptions and source references. Investigate concrete concerns with
the responsible assessor instead of adding a third routine plan review. Both
plan scopes, including any eligible verified delta, must be satisfied before
the Coordinator assigns implementation to the sole Writer. Unresolved substantive
disagreement prevents readiness. A material change of design or premise refreshes
affected plan scopes before implementation resumes.

## Candidate delivery and correction

The Writer implements the bounded result, self-verifies it, maintains affected
docs and completes required cleanup/prose passes. Stop unsupported expansion
and return the exact necessity or scope question. Freeze the candidate only
after modifying activity is settled. At a meaningful Milestone, obtain its due
result assessment and resolve findings before the Coordinator decides continuation;
keep the same Task goal active and reserve Task acceptance/commit for completion.

On the first Task-completion candidate, obtain the risk-based Task result panel
and EE's first contribution assessment from direct original sources and actual
artifacts. EE assesses current contribution and remaining delivery sequence,
not whole-Epic completion. The Coordinator personally reviews architecture,
correctness, maintainability, compatibility and affected user journeys, including
CLI/API errors and recovery. Its review and ready independent assessments may
join nonconflicting due checks on the same frozen bytes. Each judgment waits for
the evidence it needs. Collect initial findings and failures into one issue set.

Classify that entire set under the shared
[correction table](epic-squad-collaboration.md#corrections-deferral-and-evidence-applicability).
Establish the failing property, requirement, impact, cause, affected consumers
and exact cumulative delta. Preserve original reports, priorities and failed
checks. Current defects and missing mandatory evidence stay open; independent
future work receives an actionable canonical deferred/TODO disposition.
Invalid findings and preferences receive reasoned dispositions without a repair
or clean-report rerun. A mandatory-gate failure still needs its authorized
baseline disposition or actual repair; a later green rerun alone proves no flake.

Record each correction's check scope and assessment scope separately. Follow the
table's direct verification/local closure, TE-only, TE-plus-one, elevated
TE-plus-two or affected plan-reassessment route. Meaning-preserving prose uses
readback and applicable document/integrity checks. Normative instructions,
API/error codes, configuration/data semantics, numbers, assertions, fixtures,
timeouts and selection retain their semantic effects even in a test or document.
An eligible isolated approved-behavior repair retains its original priority.

Local closure requires substantive first coverage, a finite understood delta,
direct current proof and no unresolved substantive objection. Coordinator-authored
semantic corrections receive focused non-authoring confirmation. Keep a finding's
original owner engaged while its judgment remains unresolved. Retain the reviewed
basis, exact permitted delta, current affected criteria, checks, original verdicts,
closure owner and outstanding obligations in existing reports. Closure supplies
no new Evaluator pass and cannot fill missing first coverage.

Re-engage EE for changed cross-Task contracts, dependencies, downstream premises,
Epic scope or its own outstanding finding. Otherwise record why its assessed
scope is unchanged; uncertainty calls for that scope's assessment. Keep actual
disagreements visible and resolve them with focused original evidence, not
majority voting or replacing an assessor to obtain approval.

Reuse evidence only where the cumulative delta preserves its command, coverage,
inputs, dependencies and environment. Run changed behavior/failure checks and
mandatory cases left unexecuted by fail-fast. Broaden when a required gate or
unknown/changed premise demands it. A changed hash or failed test alone does not
require a whole-suite run or whole-review restart. State source execution and
delta coverage honestly; current readiness may compose actual first assessments
and eligible verified closures without another TE/EE acknowledgement turn.

## Supervise and receive actual results

Use supported lifecycle states, completion notifications and result channels for
routine supervision. Keep waits responsive to other roles and retain the same
handle. Honor each paired tool's waiting contract without a competing observer.
Choose observations from expected work and detection limits, without a retry
quota, fixed console length or automatic cancellation deadline.

For blocked/unknown state, uncertain submission, unexplained overrun or exit,
inspect enough current output to identify the request and follow its actual
permission/recovery contract. Quiet analysis is not failure; repetitive output
is not meaningful progress. Service peers' requests and completions while an
operation waits. Do not send terminal status prompts into active or uncertain
turns. Reconcile the existing operation before redispatch; elapsed time grants
no interruption authority.

Participants return actionable dependency/decision requests through supported
messaging or their result channel. If only a completed turn exposes a request,
end that turn instead of waiting in a circular dependency. No agent may inject
results or questions into the Coordinator's interactive user input.

Read complete actual reports and match assignment, plan/candidate and current
inputs. Preserve failures, omissions and unknowns. Recover missing/truncated
output from the same operation; an explicitly assigned temporary report may
re-emit that existing result when native controls permit it. A notification,
idle state, file path or old visible pass cannot establish the current result.
Capture actual descendant reports with any synthesis, configuration, public
handles, pending operations and next owners before retiring or replacing roles.

At assignment, result and exception boundaries, assess whether support work
advances a required outcome or resolves justified uncertainty. Safely narrow or
stop machinery that has displaced delivery, including machinery proposed by a
reviewer or the Coordinator. Required fixture/harness repair remains permitted
when current acceptance, safe execution or trustworthy required evidence depends
on it; optional missing automation creates no obligation to build a framework.
Stop correction when its required property is established, carrying only
independent future work to its canonical owner.

For final closeout, preserve actual first EE coverage and the original assembled
panel. A finite meaning-preserving record delta may use verified current
applicability under the shared correction table; a stale reference alone cannot
supply the first closeout review. Complete negative EE results remain actual
negative judgments, with findings and counts intact. Same-EE continuity and
supported same-role replacement do not permit an integration TO to become EE.
Use the [execution contract](epic-squad-execution.md#native-integration-and-recovery)
for exact closure/confirmation applicability and the integration-scope successor
restoration sequence after a true Task reopen.
