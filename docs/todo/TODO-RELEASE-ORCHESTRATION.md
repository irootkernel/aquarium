# Release orchestration dossier

## Authority and implementation state

The sole consumer is `EPIC-031`. The [roadmap](../roadmap/README.md#epic-031-adopt-coordinator-evaluator-and-executor-roles-in-release-workflows)
alone owns Epic and Task identity, order, dependencies and lifecycle status.
This temporary execution SOT defines detailed scope, approach and acceptance
under the [Epic Execution SOT contract](../../plugins/aquarium/references/epic-execution-sot.md).
Unchecked items specify required evidence, not completed work.

Implementation follows the applicable approved execution envelope. Installation,
managed updates, staging, commits and publication retain their own workflow
authority. This dossier grants none of those effects and records no functional
or installed verification result.

The [release orchestration target contract](../../plugins/aquarium/skills/release-handler/references/release-orchestration.md)
promotes TASK-172's frozen roles, boundaries and evidence interfaces.
[Preparation/QA handoffs](../../plugins/aquarium/skills/release-handler/references/release-preparation.md)
now implement bounded Executor delivery and independent plan/QA readiness,
including conditional remediation and exact confirmation-manifest intake.
[Post-QA convergence](../../plugins/aquarium/skills/release-handler/references/gate-convergence.md)
now implements both gate orders, post-hook binding and independent QA-neutral
eligibility. [Publication evidence/recovery](../../plugins/aquarium/skills/release-handler/references/publication-recovery.md)
implements independent readiness/completion and original operation/Job recovery.
TASK-175 prepares integrated executable regressions, committed guest fixtures
and driver support for the managed release-orchestration feature suite. It also
adds bounded release-handler plan-readiness startup to release acceptance.
TASK-176 retains actual installed/native observations against the exact committed
matching candidate. Prepared fixtures and source integration establish no
functional, installed or release result.
This dossier keeps the original acceptance criteria and remaining obligations
until final settlement.

## Goal and current authorities

Extend `release-handler` with ordinary Coordinator, Executor and independent
Evaluator responsibilities throughout one release invocation. Substantial work
returns actual deliverables and checks; stage progression uses an applicable
independent assessment of the original release requirements and current candidate.

The current [release handler](../../plugins/aquarium/skills/release-handler/SKILL.md)
owns release discovery, notes settlement, QA handoff, gates, publication and
recovery. [Release QA](../../plugins/aquarium/skills/release-qa/SKILL.md) already
requires fresh scenario Executors and Coordinator adjudication. It does not
provide a dedicated independent Evaluator for the whole release.

Reuse the [ordinary v3 contract](../../plugins/aquarium/references/ordinary-agent-orchestration.md),
[Executor guidance](../../plugins/aquarium/references/executor-guidance.md) and
[Goal Evaluator](../../plugins/aquarium/skills/goal-evaluator/SKILL.md).
[Gate convergence](../../plugins/aquarium/skills/release-handler/references/gate-convergence.md),
[publication recovery](../../plugins/aquarium/skills/release-handler/references/publication-recovery.md)
and the target repository's release policy remain authoritative for their
existing effects and evidence requirements.

## Roles and delivery

| Role | Required responsibility |
| --- | --- |
| Coordinator | Resolve scope, version, mode and authority; communicate with Master; assign work, reconcile original results and retain lifecycle Decisions, commit handoffs and publication actions. |
| Executor | Deliver bounded investigation, release-note proposals and approved edits, metadata changes, authorized checks or corrections; return exact artifacts, actual results and gaps. |
| Evaluator | Independently assess original due criteria, current artifacts and supplied execution evidence; return report-only criteria and verdicts without editing, executing checks, dispatching agents or granting authority. |

Use supported native agents in the current Coordinator's harness and preserve
selected supported options or its defaults. Keep one logical Evaluator through
the invocation when supported. Only one mutating Executor may operate in the
shared checkout at a time. Source access and actual evidence establish an
assessment; unavailable private telemetry does not block ordinary work.

Preserve role-specific effects in the target repository. An operation reserved
for its coordinator stays with the Coordinator; a legacy Worker maps to an
Executor without inheriting that operation. For example, Podway's Coordinator
may acquire the permitted previous-release archive while scenario Executors
receive only its verified local inputs. Transport-sensitive checks belong to
an Executor that loads the paired tool skill and proves the exact command,
artifact and environment survive its chosen native transport.

Use `aquarium.assignment/v3`, `aquarium.executor-handoff/v3` and
`aquarium.evaluator-assessment/v3`. Identify release work by repository, intended
version, baseline and candidate; require no synthetic roadmap Task for a release.
For the existing non-Podway release path, use `procedure: null` and leave any
unrelated development session untouched.
Keep `aquarium.orchestration-checkpoint/v3` information in the active handoff or
conversation under the existing evidence rules; it creates no release resume
manifest or second state authority.

Put release-specific detail in
`plugins/aquarium/skills/release-handler/references/release-orchestration.md`.
Align the release handler, `goal-evaluator`, shared v3 producer/consumer map and
canonical documentation. Keep the existing release handoff to `task-commit`;
Evaluator reports remain in the enclosing handler's evidence, without a new
commit-leaf input schema.

## Assessment boundaries

| Boundary | Due obligations and exact target |
| --- | --- |
| Plan readiness | Baseline, intended version and mode, scope, release-note proposal, gate inventory, required environment and applicable authority are coherent against repository policy. Name the current basis and proposed effects. |
| QA readiness | The notes cover material changes in the settled clean committed candidate; required pre-QA gates and light-mode confirmations bind to it. Live remote main is equal to or a verified ancestor of that candidate. For confirmation QA, assess the remediated candidate and retained inputs after `prepare-confirmation` and before `begin-confirmation` creates its claim. |
| Publication readiness | Before the first publication mutation, original passing QA and any permitted binding, required installed acceptance, the authorized metadata delta and repository release-gate evidence support the exact bytes to publish. Repository policy determines whether the gate runs before or after the release commit. |
| Publication completion | Original Git and hosting observations establish the actual release commit, permitted remote-main relationship, annotated tag's peeled target, hosted Release target and required release-note body. Distinguish matching main from a permitted descendant, and check settled highlights separately from validation text. |

The Coordinator checks report completeness and applicability before using it for
progression. Phase results cover due obligations; future obligations retain their
actual state. Whole-release success requires every mandatory criterion to be met
or legitimately inapplicable. Assessments cannot replace actual user acceptance,
checks, QA evidence or permission for a later effect.

A candidate, requirement or material check-input change invalidates affected
assessment rows. Reassess at the next due boundary, or before an effect that
depends on those rows. Reuse unaffected evidence and complete existing reports
only with a current applicability basis. Bookkeeping and unchanged report
assembly require no additional Evaluator cycle.

Version retargeting and next-cycle opening keep their bounded heading-edit paths.
The Coordinator checks the exact approved diff, release-notes inspector and
documentation results before the existing commit handoff. They add no Evaluator
cycle, release QA or publication requirement for the unreleased cycle.

### Haepari resource and evidence handoff

EPIC-031 starts only after EPIC-019 completes its installed pilot, accepted policy cutover, canonical promotion and dossier closeout. Read its Canonical Outcomes and current durable setup/adapter/profile/recovery owners in [Haepari integration](../../plugins/aquarium/references/haepari-integration.md), [manual VM acceptance](../../plugins/aquarium/skills/release-handler/references/manual-vm-acceptance.md), [tool integrations](../specs/tool-integrations.md#haepari), [workflow contracts](../specs/workflow-contracts.md#release-a-stable-version), [Haepari VM operations](../ops/haepari-vm-verification.md), [TESTING.md](../../TESTING.md#host-submitted-managed-vm-suites), and [tests/vm/README.md](../../tests/vm/README.md#host-submitted-managed-vm-suites). TASK-172 through TASK-176 consume that accepted Haepari path and observe its release-role integration. Missing required readiness or native results remain gaps; direct VM execution is not a fallback. This adds no VM gate to repositories whose release policy requires none.

EPIC-032's formal rollout follows this Epic and owns the nine producer acceptances, including Mulgae's released native advisory integration under TASK-092. Podway, Dolgorae, Gaori and Sanho may perform their separately authorized aquarium-dev cleanup in parallel with this Epic; EPIC-032 later reuses their applicable returns without resending the cleanup requests. EPIC-033 follows EPIC-032 and owns whole-combination qualification and common legacy retirement. Each Epic has one complete execution/acceptance boundary and its own dossier. This Epic does not wait for either successor or the early cleanup, and its durable release-role/result contract must be promoted before its dossier is deleted.

The Coordinator identifies the exact candidate, applicable VM policy, selected
controller/resource, admitted effects and cleanup/disposition responsibility.
Readiness inspection grants no occupancy and need not find the resource idle;
normal contention uses the native queue. A bounded Executor saves the native
request key and exact spec before submitting, retains the returned Job ID, and
uses native blocking wait/reconnect on that same Job. Retain original envelopes
and declared output references in the existing assignment/handoff evidence fields.
No new v3 report schema, scheduler, release-resume manifest or outer lock is needed.

The managed Job holds the VM across baseline observation, candidate installation,
automatic/manual checks, collection and owned cleanup. Consumer recipes separately
verify installation/fixture cleanup and reusable state in the persistent guest;
Haepari does not reset the VM. A native manual-ready state or successful smoke
command cannot replace required observations. Stage case evidence, finish recipe
cleanup and record its inventory evidence as required scenarios before
`manual complete` starts native collection and owned cleanup. Automatic workloads
finish recipe cleanup before exiting. Wait expiry leaves the Job pending;
unknown execution follows native reconciliation. Before replacing an Executor,
recover the original request/spec/Job identity and reconcile its possible effects.
Do not create another Job to recover from an observer timeout or lost reply.

The Evaluator reads original candidate-bound Job results, required case evidence
and cleanup observations under its report-only role. It grants no execution or
resource-release authority. Keep managed occupancy/disposition, workload outcome,
evidence completeness, consumer cleanup and assessment verdict separate. Advisory
Mulgae grant expiry has different semantics: it can end while native work remains.
Delegate that lifecycle to the released Mulgae integration and its paired skill;
the release handler neither acquires another review lock nor substitutes grant
status for native review coverage.

| Assessment | Applicable resource evidence |
| --- | --- |
| Plan readiness | Select the required VM path, controller/resource, intended occupancy, native wait/recovery and recipe cleanup responsibilities under repository policy. |
| QA readiness | Include original candidate-bound VM results only when repository policy makes them due before QA; leave later obligations pending. |
| Publication readiness | Require the policy-due installed result, required observations and cleanup evidence for the exact candidate. Preserve light mode's actual exact-SHA confirmation and prior results. |
| Publication completion | Assess retained evidence and actual publication observations without reacquiring an already settled VM Job. |

Release capacity after the native work and required collection/cleanup boundary;
later report assembly, publication or user decisions with no VM work do not extend
its occupancy. Active hands-on verification keeps its managed occupancy. Evaluator
rework does not itself grant another VM Job or review. This dossier's sole
consumer is EPIC-031; its closeout replaces temporary navigation links with
the accepted durable contract and deletes this dossier.

### Gate order and commit binding

Resolve the target repository's gate order during planning; preserve its full,
light or reduced-patch contract rather than imposing Aquarium's order.

- For a gate-before-commit policy, the Executor applies approved metadata and
  runs the authorized gate. The Evaluator assesses those exact bytes and check
  inputs. After the Coordinator's `task-commit` handoff, verify the actual
  post-hook commit tree, allowed metadata delta and release-basis parent, then
  bind the passing gate to that release commit. A material hook change
  invalidates affected evidence before publication.
- For a commit-before-gate policy, approve the exact metadata delta, commit
  through `task-commit` and inspect the post-hook result first. The Executor runs
  the required gate on that exact clean release commit. The Evaluator completes
  publication readiness against its identity, parent, delta and actual gate
  evidence before any push, tag or hosted Release mutation. In the unchanged
  commit handoff, record the not-yet-run gate as inapplicable to the commit
  boundary under that repository's policy and still required before publication.
  Use Podway's `make dist` and `make dist-patch` as planning examples; fixtures
  model their clean-commit precondition without running Podway's distribution
  targets.
- If a commit-first gate fails, preserve the unpushed release commit and report
  the failure. Do not reset, amend or replay publication implicitly. Stop for
  an explicitly authorized disposition of that exact local commit before a
  correction requiring history changes; use current authority for diagnostics
  that preserve it. Re-establish affected evidence for the resulting candidate.

TASK-174 corrects the generic handler and convergence instructions where they
assume gate-before-commit ordering. Keep current QA-binding and publication
inspector schemas. Both orders must supply the same actual release-commit
binding before publication; neither a local commit nor a suffix run proves
release readiness.

### Original observations for the Evaluator

The Coordinator or an authorized Executor captures read-only Git and hosting
outputs for the current assessment, retaining commands, actual results, target
identities and provenance together with the exact v5 observation and publication
inspector result. The Evaluator reads those original outputs and local Git
objects rather than a Coordinator summary. Its report distinguishes supplied
remote observations from firsthand artifact reads and returns `evidence-needed`
for missing or inapplicable evidence. Direct remote reads require an explicit
assignment scope within the existing discovery authority; credential inspection
is never part of that scope.

Freshness follows current candidate and action boundaries, not an invented time
limit. Before and after every publication effect, the Coordinator still obtains
the live observations required by publication recovery. The inspector supplies
structural action selection; the Evaluator also checks original due obligations
such as settled release-note text and verification coverage. In full mode, use
actual required gate and installed-acceptance results. In light mode, preserve
the repository's explicit positive confirmation for the exact settled SHA,
including its required VM and compatibility results; do not claim omitted checks
ran or rerun tests the reduced contract excludes.

## QA, authority and recovery boundaries

The same Coordinator calls `release-qa` and directly assigns its fresh scenario
Executors under the existing QA contract. Preserve cluster results, frozen
matrices, confirmation records, one-attempt facts and original QA verdicts.
The release Evaluator reads those original inputs for coverage and applicability;
its verdict cannot convert `FINDINGS` or `INCOMPLETE` into QA `PASS`.

Report a full-pass finding before leaving QA mode. Delegate any existing bounded
remediation to the single authorized correction Executor, retain focused checks
and preserve the current stop and explicit confirmation boundary. Keep standalone
QA behavior intact. Evaluator rework grants no second QA invocation, additional
correction, confirmation attempt or review authority.

TASK-173 owns pre-QA gates and QA-finding remediation. After
`prepare-confirmation`, refresh the candidate-bound inputs and obtain applicable
QA-readiness coverage for the remediated candidate, its ancestry and the prepared
manifest. Complete that assessment before `begin-confirmation` creates the
candidate-bound claim, not merely before scenario-agent dispatch. A negative
assessment leaves the claim uncreated while inputs are corrected. This reuses
the QA-readiness boundary without an extra full pass or confirmation attempt.

Preserve full/light rules, exact-SHA confirmations, separate required gate
authority, repository metadata allowlists, gate suffix versus final aggregate
results, QA-affecting correction routing and the existing QA-neutral direct-child
exception. An Evaluator passage does not transfer earlier QA to another candidate.

TASK-174 owns post-QA release-gate convergence. The Executor supplies correction,
suffix and candidate evidence under existing authority. Where uncommitted
metadata must be restored before a correction commit, follow the existing exact
restoration contract; the commit-first failure path above is not an implicit
history-rewrite exception. For a proposed QA-neutral direct child, the Evaluator
assesses the existing eligibility conditions and exact diff before the
Coordinator seeks Master's required equivalence approval. Publication readiness
remains incomplete until the final uninterrupted gate and all other due
obligations pass. No Evaluator cycle is required for each diagnostic suffix.

The Coordinator retains commits through `task-commit` and performs each authorized
publication action selected by the current publication inspector from fresh native
observations. Carry valid existing grants forward within their actual
scope; retain expiry and separate approvals required by the owning release
contract. Role assignments add no user approval checkpoint of their own.

Recover from current Git and hosting objects, available public agent handles,
original results, candidate-bound evidence and remaining authority. Reconcile an
uncertain effect before replay and settle a mutating Executor before replacement.
Reconnect the Evaluator or supply a fresh independent replacement with original
criteria, current artifacts, prior gaps and remaining authority. Missing agents
or mandatory evidence remain gaps; Coordinator self-assessment cannot supply an
independent verdict. A negative completion assessment after publication reports
the actual published state and the unresolved obligation without automatic
rollback or repeated publication.

## Compatibility and exclusions

Treat mandatory release-role adoption as a breaking workflow-contract update.
The continuation contract changes: a Coordinator-only release cannot treat its
old summaries as the new independent assessments. Finish active releases with
their installed workflow before updating, then establish new invocations under
the updated contract. This is the required operator upgrade step; do not build
an in-place invocation migration mechanism. Candidate installation and
installation-dependent verification run only in the dedicated UTM VM over the
host's released baseline with candidate-matched test sources.

Existing policy already requires affected functional verification before release
and UTM verification of a breaking candidate before publication. Apply those
rules to the actual release candidate and its effects; do not add a blanket ban
on publishing any Epic member until every Task is complete. TASK-175 extends the
existing reusable VM release-acceptance gate with one bounded installed
`release-handler` startup case through plan readiness, stopping before QA or
publication. Update its testing and repository-policy owners during that Task.
This smoke case does not repeat the development feature suite.

Begin after completed EPIC-019 and build on EPIC-024 and EPIC-026. EPIC-030 keeps ownership of host packages and
distribution; this Epic neither depends on nor implements that Planned work.
Reuse EPIC-026's ordinary role/report contracts, not adaptive Procedure selection
for a release invocation. At implementation entry, resolve the actual package
inventory and supported harnesses from current authorities. If EPIC-030 lands
first, TASK-172 applies the release assessments to its adopted output inventory;
if EPIC-031 lands first, EPIC-030's release integration must extend the same
assessments and scenarios to its outputs. Whichever lands second reconciles the
shared release, testing and policy owners before accepting its candidate. Keep
one mutating Executor for overlapping source edits; do not infer five-host support or add
an automatic Epic dependency.

Keep existing QA and publication-helper schemas. This work adds no Podway release
Procedure, central state file, automated LLM gate, retry quota or production
publication requirement for functional qualification. Controlled fixtures can
verify role progression and recovery; their outcomes are not production releases.

Keeping this Epic's release path non-Podway is a scope choice. Podway can guard
ordinary recorded progression, but a new release session would compete for the
worktree's existing session and add integration to the established QA admission
and stateless Git/hosting recovery contracts. Preserve those native mechanisms
and the existing Podway verification gates. This choice is no standing ban on
native Podway use and requires no future formal delegation or contract generation
before a separately authorized design can consider it.

## Task objectives and acceptance

### TASK-172: Define release orchestration and authority boundaries

- [ ] Establish the release-specific reference and align `release-handler`, `goal-evaluator`, shared v3 consumers and canonical owners without changing the commit-leaf input schema.
- [ ] Define all four boundaries, both gate orders, original observations, exact targets, criterion states, report ownership and applicable authority.
- [ ] Cover retargeting, next-cycle opening, breaking-update handling and current QA and recovery preservation.
- [ ] Identify the applicable VM path, selected resource and occupancy/cleanup ownership. Consume completed EPIC-019's canonical adapter through existing report interfaces and verify the release-role seams. Do not require EPIC-032's future Mulgae integration or acquire a duplicate review lock.
- [ ] Verify affected structure and links and promote the accepted contract to its durable owners.

### TASK-173: Integrate release preparation and QA handoffs

- [ ] Delegate substantive discovery, note preparation and authorized edits through bounded Executor assignments and actual handoffs.
- [ ] Obtain independent plan and QA-readiness assessments without granting edits, tests, installation or Git effects through a verdict.
- [ ] Supply complete original QA evidence and preserve fresh scenario agents, all required coverage and full/confirmation boundaries.
- [ ] Include original candidate-bound VM evidence at QA readiness only when due under repository policy. Preserve later VM obligations and the distinction between occupancy, workload/cleanup results and assessment.
- [ ] Route QA-finding corrections to the single mutating Executor, assess confirmation-candidate readiness after manifest preparation and before claim creation, preserve actual approvals and run focused checks for this Task's changes.

### TASK-174: Integrate release gates, publication and recovery assessments

- [ ] Correct generic gate-order assumptions and support both gate-before-commit and commit-before-gate policies with exact post-hook identity, parent and tested-byte binding before publication.
- [ ] Own post-QA convergence and QA-neutral eligibility assessment, preserve full/light and QA-binding rules, and stop before unauthorized disposition of a failed commit-first candidate.
- [ ] Supply original read-only observations for publication assessments; preserve repository ordering, release-note obligations and inspector next-action routing.
- [ ] Verify interrupted effects, replacement settlement, recovered Evaluator applicability and separate next-cycle handling with focused checks.
- [ ] For an adopted Haepari path, retain request/spec/Job identity, await or reconcile that Job before Executor replacement, and verify policy-due installed/cleanup evidence at publication readiness. A wait timeout, lost reply or Evaluator verdict cannot authorize duplicate dispatch or manufacture resource return.

### TASK-175: Prepare integrated regressions and manual verification scenarios

- [ ] Cover normal progression, first-release and full/light paths, changed or missing evidence, negative verdicts and absent native agents.
- [ ] Cover QA findings and confirmation stops, gate corrections, QA-neutral binding and prevention of accidental extra QA passes.
- [ ] Cover partial publication, remote advancement, unknown effect outcomes, Executor settlement and Evaluator replacement.
- [ ] Prepare applicable native VM queue contention, manual occupancy, queue/active cancellation, wait timeout, lost submission reply, same-Job reconnect, collection/consumer-cleanup failure and replacement-Executor scenarios. Exercise native contracts through isolated fixtures; no prose-matching test can prove them.
- [ ] Add objective helper regressions only where executable behavior changes. Commit required guest fixtures, driver support, testing-authority and planned startup-policy updates before TASK-176 observations; earlier Tasks retain their own focused verification.

### TASK-176: Verify installed release orchestration and promote outcomes

- [ ] Use the dedicated UTM VM and supported installation path for the exact candidate over the host's released baseline; retain meaningful existing state.
- [ ] Observe actual native Executor delivery, independent Evaluator results and Coordinator progression for the claimed harnesses in the installed scenarios below.
- [ ] Keep structural checks, fixture observations, installation results, Master-owned functional verification and actual release outcomes distinct. Missing required evidence remains non-passing.
- [ ] Verify the completed EPIC-019 Haepari path and original candidate/resource/Job/result/cleanup evidence through the installed release roles. Observe required resource and role-seam scenarios; missing prerequisite or integration evidence cannot be bypassed through pre-adoption manual qualification.
- [ ] Promote accepted contracts and operating guidance, prepare Master's actual overall acceptance and settle every temporary reference at final closeout.

## Verification and evidence

Every implementation Task owns checks for its affected behavior. TASK-175 prepares
integration scenarios; TASK-176 observes them against the committed matching
candidate. Follow [TESTING.md](../../TESTING.md) and the
[VM verification contract](../../tests/vm/README.md). Do not claim skill decisions
from prose-matching tests, a passing structural gate or scenario preparation.
Master's functional verification remains separate unless explicitly delegated.

Use disposable guest repositories with a local bare Git remote and a disclosed
hosting stand-in scoped to the fixture process environment. The stand-in
provides readback and partial-publication states consumed by the existing v5
inspector; it must not turn missing observations into synthetic success. Observe
real installed handler and native agent calls separately from stand-in outputs.
Use no production hosting, host secrets, global CLI replacement or host-state
changes. Real hosting behavior remains unverified unless separately authorized.

TASK-176 must observe these installed scenarios against committed matching
implementation and test sources:

| Scenario | Required observation |
| --- | --- |
| Full release, gate before commit | Actual role delivery and all four assessment boundaries through fixture publication completion, with post-hook byte and parent binding. |
| Commit before gate | A clean-commit policy such as Podway's reaches publication readiness with the actual gate result bound to that commit. A failed gate preserves the unpushed commit and stops before unauthorized history changes or publication. |
| Negative assessment | `rework` or `evidence-needed` prevents the dependent effect; it supplies no new authority and cannot turn QA findings or incomplete coverage into a passing result. |
| QA findings and confirmation | One correction Executor delivers the bounded fix and focused evidence; the Coordinator stops at the existing confirmation boundary. On actual fixture-operator confirmation, the remediated candidate receives refreshed QA-readiness coverage after `prepare-confirmation` and before `begin-confirmation` creates its claim. A negative assessment leaves the claim absent; only the ready candidate enters the one permitted confirmation pass. |
| Interrupted publication | A new invocation reconciles partial objects through the inspector and an applicable independent Evaluator, preserves missing-authority stops and creates no duplicate publication objects. |
| Light mode and drift | Actual fixture-operator confirmation binds to the exact candidate and required prior results; candidate drift invalidates it without silently switching modes or inventing passing checks. |
| Adopted managed VM path | Using the accepted EPIC-019 adapter, two disposable project callers share one VM resource without overlap; manual checks retain occupancy, timeout/lost reply/replacement reconnect to the original Job, and cancellation/collection/cleanup failures retain their actual native and consumer outcomes. Assessments use original due results and create no duplicate Job or review lock. Verify added role seams and retain the exact applicability basis for reused native evidence. |

TASK-175's remaining first-release, remote-advancement, hook-drift, gate-correction
and agent-replacement cases retain their required coverage; report which were
observed with native installed agents and which only at fixture/helper level.
Preparation and a fixture status alone cannot pass an installed scenario.
After installed verification, promote only non-installed documentation without
repeating unaffected observations. Changes to installed skill, reference, helper
or relevant test bytes invalidate affected observations; reverify them and retain
the actual tested candidate identity separately from later documentation commits.

Retain actual candidate, artifact, environment and result identities under the
[evidence-residency contract](../../plugins/aquarium/references/evidence-residency.md).
Keep runtime paths, agent identities, raw reports and invocation history out of
tracked planning and canonical documentation. Record only durable requirements,
accepted limits and necessary downstream instructions in their proper owners.

Reuse applicable accepted Haepari contention/manual/recovery evidence from
EPIC-019 when its exact inputs still apply. Verify this Epic's added role seams,
including Executor replacement, original-Job binding and assessment inputs;
reobserve native behavior when the affected candidate or environment changes.

## Durable promotion and deletion

| Accepted content | Durable owner |
| --- | --- |
| Roles, report interfaces and assessment boundaries | Release-specific and shared orchestration references; [orchestration specification](../specs/agent-orchestration.md) and [workflow contracts](../specs/workflow-contracts.md). |
| Coordinator, leaf and recovery ownership | [Workflow runtime](../architecture/workflow-runtime.md) and the exact release skill references. |
| Release maintenance and recovery guidance | [Skill maintenance](../implementation-tips/changing-skills.md), [release guidance](../implementation-tips/testing-and-releasing.md) and affected [operations](../ops/README.md). |
| Verification methods and actual acceptance limits | [Testing authority](../../TESTING.md), candidate-matched [VM scenarios](../../tests/vm/README.md) and the canonical requirement or risk owner. |
| Adopted resource handoff and result interpretation | Shared release VM reference, [tool integrations](../specs/tool-integrations.md), workflow specifications and operations; EPIC-019 promotes its native setup/adapter contract independently. |

Promote accepted durable statements during each Task while retaining this dossier
for remaining work. Before final closeout, obtain Master's actual overall Epic
acceptance and replace the roadmap's `Detailed SOT` with valid `Canonical Outcomes`.
Replace planned pointers with implemented-contract links and inventory all
remaining references and consumers. Under the approved final-closeout deletion
scope, remove this exact dossier and its TODO index entry only after all consumers
are successfully terminal and no canonical reference remains. Do not archive a
copy; Git history preserves the deleted plan.
