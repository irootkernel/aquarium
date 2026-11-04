# Release orchestration target contract

## Status and integration owners

TASK-172 established this target contract. The [release handler](../SKILL.md)
and [release QA](../../release-qa/SKILL.md) implement preparation, pre-QA checks,
plan/QA readiness and bounded remediation/confirmation through
[release preparation](release-preparation.md). The conditional QA caller seam
preserves standalone behavior and the original verdict and confirmation authority.

TASK-174 retains post-QA gates, publication and recovery integration, including
removal of generic gate-before-commit assumptions. Until that integration,
[gate convergence](gate-convergence.md), [publication recovery](publication-recovery.md)
and the handler's current post-QA steps govern their operations. The reserved
publication assessments below do not override those steps. TASK-175 prepares
integrated scenarios and the bounded installed startup case; TASK-176 observes
the exact installed candidate. Source integration establishes no installed result.

## Roles and authority

Reuse the [ordinary v3 contract](../../../references/ordinary-agent-orchestration.md),
[Executor guidance](../../../references/executor-guidance.md) and
[Goal Evaluator](../../goal-evaluator/SKILL.md). The Coordinator resolves scope,
version, mode and authority, communicates with the user, assigns bounded work,
reads complete original results and retains commit handoffs and publication
actions. Executors deliver substantive investigation, note proposals, approved
edits, metadata, checks and corrections. Only one mutating Executor operates in
the shared checkout at a time. An independent report-only Evaluator assesses
original requirements, current artifacts and actual evidence.

Use supported native agents in the Coordinator's harness, preserving supported
selected options or its defaults. Keep one logical Evaluator through an invocation
when supported. Missing private telemetry remains unknown. Missing required agents
or due product evidence remain gaps; Coordinator self-assessment cannot substitute
for an independent verdict.

The Coordinator retains operations that target-repository policy reserves for it.
For example, Podway's Coordinator acquires a permitted previous-release archive
while scenario Executors receive verified local inputs.
Transport-sensitive checks belong to an Executor that loads the paired tool skill
and proves the exact command, artifact and environment survive its transport.

Role assignments and verdicts add no approval checkpoint or effect grant. Preserve
actual proposal approvals, gate-execution authority, correction limits, commits,
push, tag, hosted Release, destructive-action and next-cycle grants under their
own contracts. Carry valid grants forward only within their actual scope and
expiry. A new invocation re-establishes authority as the owning contract requires.

## Reports and original evidence

Use existing `aquarium.assignment/v3`, `aquarium.executor-handoff/v3` and
`aquarium.evaluator-assessment/v3` documents. Identify release work by repository,
intended version, baseline and candidate; require no synthetic roadmap Task.
For this non-Podway release path, use `procedure: null` and leave unrelated
development sessions untouched. This scope choice preserves existing native QA
admission and Git/hosting recovery; it is not a standing ban on separately
authorized Podway designs.

| Existing field or report | Release content and owner |
| --- | --- |
| `work` | Original release policy, objective, requirement sources and their revision or approved basis. |
| `target` | Exact candidate bytes, baseline, intended outputs, check inputs, included/excluded scope and current boundary. |
| `authority` | Actual allowed effects, approvals, consumed and remaining correction/review authority; a report supplies no grant. |
| `native` | Available public handles, actual lifecycle observations and honest configuration unknowns. |
| `evidence`, `results`, `gaps` | Original inputs, delivered artifacts, actual or omitted checks with reasons, provenance, cleanup/retention and next owners. |
| Evaluator assessment | Original criterion rows, current applicability, evidence provenance, gaps, global verdict and nonfinal `checkpoint_result`. |
| Coordinator checkpoint | Pending operations, current candidate, original reports and remaining authority, retained in the existing handoff or conversation. |

The enclosing release handler owns Evaluator evidence. Keep the existing
[task-commit](../../task-commit/SKILL.md) release handoff unchanged, including QA
and release-gate evidence or legitimate boundary-specific inapplicability. Add
no commit-leaf Evaluator input schema, release resume manifest, scheduler or
central state file. Follow [evidence residency](../../../references/evidence-residency.md)
and [artifact cleanup](../../../references/artifact-cleanup.md); runtime identities,
paths and raw reports remain local evidence.

Read original criteria and artifacts, reconciling omitted and compound obligations.
Each criterion keeps its source, provenance, gap and `met`, `unmet`, `unverified`
or `not-applicable` state. A nonfinal `checkpoint_result` covers due obligations;
future global obligations retain their actual state. Whole-release `pass` requires
every mandatory criterion to be met or legitimately inapplicable. Established
gaps require `rework`; evidence gaps require `evidence-needed`. Preserve both
when they coexist.

Candidate, requirement or material check-input changes invalidate affected rows.
Reassess before a dependent effect or at the next due boundary. Carry unaffected
evidence only with a current applicability basis. Bookkeeping, unchanged report
assembly and diagnostic suffix runs create no Evaluator cycle of their own.

## Four assessment boundaries

| Boundary | Exact target, due obligations and dependent effect |
| --- | --- |
| Plan readiness | Original baseline or confirmed first-release basis, actual intended-version/mode decisions, approved note proposal, scope, output inventory, gate inventory/order, environment and authority. Applicable coverage precedes the settlement commit and pre-QA gate execution; those effects still require their actual grants. |
| QA readiness | The settled clean committed candidate, material-change coverage, live remote-main equality or verified ancestry, required pre-QA results and exact-SHA light confirmation. Complete before the full QA handoff. For confirmation, assess the remediated candidate and prepared manifest before claim creation. |
| Publication readiness | Original passing QA and permitted binding, policy-due installed acceptance, authorized metadata delta, release parent and post-hook tree, actual required gate and final distribution-byte applicability. Complete before the first publication mutation, following repository-defined gate/commit order. |
| Publication completion | Original Git and hosting observations proving the release commit, permitted remote-main relationship, annotated tag's peeled target, hosted Release target/status and required note body. Distinguish an allowed main descendant from equality; assess settled highlights separately from validation text. |

The user decides intended version, mode and first-release confirmation where
required. Plan readiness checks their coherence with the approved proposal; it
does not make those decisions. Proposed preparation edits retain existing exact
proposal authority. Distinguish the planning gate inventory from the authoritative
public checkpoints frozen later for execution. A mode switch or retarget invalidates
affected rows.

The Coordinator checks completeness, source coverage and applicability before using
an assessment for progression. A negative or inconclusive due checkpoint prevents
the dependent effect without granting repair, another check or another review.

### Confirmation readiness and preparation

After `prepare-confirmation`, refresh candidate-bound inputs and obtain QA-readiness
coverage of the remediated candidate, ancestry, frozen record, complete retained
coverage and exact prepared manifest. Complete this assessment before
`begin-confirmation` creates its claim, not merely before scenario dispatch.
A negative assessment leaves the claim uncreated.

Within existing preparation authority, correct non-product preparation inputs such
as accurate surface mappings, references to retained evidence and faithful
finding-reproduction mappings. Preserve the frozen inventory, original results,
candidate and actual attempt facts. This grants no new scenario execution, product
correction or invented evidence.

Retain a superseded valid manifest unchanged. Re-run the deterministic preparer
into a fresh, nonconflicting create-once output under its permitted evidence root,
then assess that exact replacement before claim creation. Never edit or overwrite
the earlier manifest. Preserve the existing stop on helper rejection; this path
does not bypass validation. Recover an existing claim through its native contract.
Candidate changes retain actual QA correction authority and stop/confirmation
boundaries. Re-preparation grants no additional correction or attempt. TASK-173
owns exact output paths and caller steps, including replacement-manifest intake.

### QA-neutral eligibility

Assess a proposed QA-neutral direct child as a nonfinal checkpoint within
publication readiness, before the user is asked to approve the exact equivalence
decision. Its target includes the exact diff, original passing QA and frozen
scenarios, repository distribution classification, affected inputs and the actual
first-and-only reuse fact. Check every existing eligibility condition from
[gate convergence](gate-convergence.md#reuse-qa-once-for-a-neutral-direct-child).

Report a separate `checkpoint_result` within the existing publication-readiness
boundary; the four top-level boundaries stay unchanged.
Eligibility passage grants no equivalence approval or final readiness. Publication
readiness remains incomplete until actual approval, the final uninterrupted gate
and every other due obligation are established. Keep direct-QA and release-basis
SHAs distinct; neither eligibility nor a verdict transfers SHA-bound evidence.

## Gate order and exact commit binding

Resolve the target repository's full, light or reduced-patch policy during planning
and follow its gate/commit order. Aquarium's own policy runs the gate before commit.

| Policy | Required target sequence |
| --- | --- |
| Gate before commit | Apply approved metadata; run the authorized gate on identified bytes and inputs; assess those bytes. After `task-commit`, inspect the actual post-hook tree, allowed metadata delta and release-basis parent. Bind passing evidence to the release commit only when that comparison supports it. Material hook changes invalidate affected evidence. |
| Commit before gate | Approve the exact metadata delta; commit through `task-commit`; inspect the post-hook commit and clean state; run the required gate on that exact commit. Complete publication readiness before push, tag or hosted Release mutation. Record the later gate as inapplicable to the commit boundary under that policy while keeping it globally unverified and required before publication. |

Podway's `make dist` and `make dist-patch` are illustrative clean-commit examples,
not commands to run or an authority to inspect another repository. Fixtures model
the precondition without invoking producer distribution targets.

A failed commit-first gate preserves the unpushed release commit. Diagnostics may
continue within existing authority. Stop before a correction requiring history
changes until the user explicitly authorizes disposition of that exact commit;
do not reset, amend or replay publication implicitly. Re-establish affected evidence
for the resulting candidate.

Keep authoritative public checkpoints, mismatch pass conditions and separate gate
execution authority. Suffix completion remains diagnostic evidence; release readiness
requires the complete final aggregate to pass uninterrupted. Preserve existing
correction limits and QA-affecting routing. Where uncommitted metadata must be
restored for a correction commit, follow the exact restoration contract without
changing settled entry text. The commit-first failure path grants no history
exception. TASK-174 integrates these orders into the handler and convergence owner.

## Observations, QA and recovery

The Coordinator or an authorized Executor captures read-only Git and hosting
outputs with commands, actual results, identities and provenance, alongside the
exact `aquarium-release-publication-observation/v5` and inspector result. The
Evaluator reads those originals and local Git objects, distinguishing firsthand
artifact reads from supplied remote observations. Missing or inapplicable due
evidence yields `evidence-needed`. Explicitly assigned remote observations remain
reads under existing discovery authority, with no credential inspection,
authentication change, check execution or mutation permission.

Retain distinct direct-QA and release-basis candidates, original QA records,
pre-metadata installed candidate/artifact/profile identities, actual release
commit/parent/delta, final gate evidence and published payload. The v5 inspector
selects one structural next action; it does not prove semantic readiness. The
Coordinator still obtains fresh native observations before every publication
mutation and after each successful step. Freshness follows candidate/input and
action boundaries, without an invented time limit.

The same Coordinator calls release-QA and directly assigns its fresh scenario
Executors. Preserve their QA-native withholding brief, fixture-only permissions,
cluster results, frozen matrices, confirmation records and one-attempt facts.
Enclosing v3 context must not weaken those restrictions. An Evaluator cannot turn
original `FINDINGS` or `INCOMPLETE` into QA `PASS`.

Report full-pass findings before leaving QA mode. Route existing authorized bounded
remediation through one correction Executor, retain focused results and preserve
the stop and explicit confirmation boundary. Standalone release-QA behavior stays
intact. Evaluator rework grants no extra correction, QA invocation, confirmation
attempt or provider review. TASK-173 owns these pre-QA and QA seams; TASK-174 owns
post-QA convergence.

Before a resumed invocation's first remaining publication mutation, require an
applicable independent publication-readiness assessment. Reconnect the logical
Evaluator when supported, or supply an independent replacement with original
criteria, current artifacts, prior findings/gaps, original results and remaining
authority. Across restarts, neither agent identity nor a restored pass establishes
readiness. Carry unaffected rows only with current applicability.

Reconcile uncertain effects before replay. Establish settlement of every mutating
Executor and relevant descendants or background writes before replacement,
including non-VM work. For Haepari, also reconcile the original request/spec/Job
and possible effects. Missing agents, unsettled modifying activity or mandatory
evidence remain gaps; the Coordinator cannot supply its own independent verdict.
A negative completion assessment reports actual published state and unresolved
obligations without automatic rollback or repeated publication.

## Haepari resource and evidence handoff

Consume completed EPIC-019's [Haepari contract](../../../references/haepari-integration.md),
[manual acceptance](manual-vm-acceptance.md) and the target's adapter/scenario owners.
Aquarium's VM operations at `docs/ops/haepari-vm-verification.md` and VM guide at
`tests/vm/README.md#host-submitted-managed-vm-suites` select
`make test-vm-host SUITE=release-acceptance MODE=manual`, explicit shared
`HAEPARI_HOME` and the registered `utm-macos` resource. Resolve concrete identities
during the release invocation. Other repositories retain their declared paths;
this contract adds no VM gate where policy requires none and offers no direct-VM
fallback for the adopted managed path.

| Responsibility | Owner and existing interface |
| --- | --- |
| Policy, candidate and resource selection | Coordinator supplies exact candidate, due boundary, installation/controller, registered resource, starting/target profiles, admitted effects, budgets and cleanup/disposition responsibility in existing assignment fields. Readiness inspection acquires no occupancy; contention uses the native queue. |
| Submission and recovery | Bounded Executor persists request key, exact spec, installation/resource and sealed candidate/artifact/profile identities before submission. Retain returned or recovered Job/revision and original native envelopes. Wait and reconnect to that same Job. |
| Manual work and completion | Authorized Executor performs guest steps under the held Job and recipe environment, stages evidence, verifies consumer cleanup/inventory and submits persisted actual completion input with the current revision fence. Native collection/cleanup and verified export follow. |
| Fixture decisions | Authorized fixture operator reads each required proposal/result and supplies an actual decision. The Coordinator acts as that operator only when its actual envelope assigns the role. Existing `aquarium.vm-acceptance-request/v1` uses the applicable `authority.kind` (`release-handler` or `explicit-vm-test`), actual `reference` and authorized `observer`; the initial envelope is not blanket acceptance. |
| VM power | The user controls power; agents do not start, stop or reset the VM. |
| Assessment | Independent Evaluator reads original candidate-bound results and cleanup evidence without execution, occupancy or resource-release authority. |

One managed Job holds occupancy across baseline observation, installation, manual
work, evidence staging, verified consumer cleanup, revision-fenced completion and
native collection/cleanup. Nested guest work stays inside that allocation.
Automatic workloads finish consumer cleanup before exiting. Haepari owns collection
and native Job cleanup; recipes own consumer cleanup and the declared inventory.
The persistent guest is not reset, and each suite retains its own final-state
contract. Preserve suite-declared outputs separately from native export-root
`result.json` and `manifest.json`.

A wait timeout remains pending and does not cancel the Job or return capacity.
Uncertain admission/execution follows native `error.code` and `error.retry` with
the original key/spec/Job; a lost admission reply may replay only the identical
key/spec as the native contract directs. Never create a replacement Job because
of timeout, lost reply or Executor replacement. Reconcile possible effects before
replacement. Keep occupancy/disposition, workload outcome, evidence completeness,
native cleanup, consumer cleanup and assessment verdict separate. A manual-ready
state or smoke command cannot replace required observations.

Release occupancy after native work and required collection/cleanup settle.
Active hands-on work retains it; later report assembly, publication or user
decisions with no VM work do not extend it. Evaluator rework grants no new Job.
EPIC-032's future Mulgae adoption is not a prerequisite. Advisory grant expiry can
occur while native work continues; defer that lifecycle to Mulgae's released
integration and paired skill. Add no outer review lock or wrapper and do not
substitute grant status for review coverage.

### Evidence due by boundary and mode

| Boundary | Full mode | Light mode |
| --- | --- | --- |
| Plan readiness | Identify required checks, installed path and target-policy timing. | Identify reduced execution and required prior results/confirmation. |
| QA readiness | Require actual pre-QA results; VM evidence is due here only when target policy says so. | Require actual positive exact-SHA confirmation and the prior results it must cover, including VM and compatibility results when required. |
| Publication readiness | Require all now-due actual gate, installed and cleanup evidence. Aquarium's full VM gate remains after QA and before metadata under its policy. | Verify prior exact-SHA confirmation/results remain applicable and the reduced gate actually passed. Neither require omitted runs nor claim they ran in this invocation. |
| Publication completion | Assess retained applicable evidence and original publication observations without reacquiring a settled Job. | Preserve the distinction between prior results and current reduced execution. |

Missing required prior light evidence remains a gap. Candidate drift follows fresh
confirmation or an explicitly selected full-mode path; do not silently run omitted
checks or switch modes. Reconcile final distributed bytes with installed evidence
under the [distribution identity contract](../../../references/haepari-integration.md#final-distribution-identity).

## Bounded paths, updates and output scope

Heading-only retargeting and separately requested next-cycle opening retain their
existing approved-diff, inspector, documentation and commit/push boundaries. They
add no Evaluator cycle, QA or publication requirement for the unreleased cycle.
Normal continuation after publication requires all due completion observations
and the applicable completion assessment. A negative or pending assessment blocks
treating that release flow as complete. A separately requested bounded next-cycle
path still verifies required publication facts and branch synchronization, reports
unresolved release facts/assessment honestly and does not establish release success
by opening a heading.

Mandatory operational adoption is a breaking continuation-contract update. Finish
active releases under their installed workflow before updating; start new
invocations under the updated contract. Add no in-place migration mechanism.
For Aquarium's own development, candidate installation and installation-dependent
verification run only in its dedicated UTM environment under applicable authority.
A target release invocation follows its repository's declared verification
environment and adapter; this contract adds no VM gate where policy requires none.
Source checks, fixture outcomes, installed results and actual user acceptance
remain separate.
This contract adds no blanket ban on publishing an Epic member before all members
finish; apply existing release requirements to its actual candidate and effects.

The current output is one Codex plugin: the
marketplace declaration at `.agents/plugins/marketplace.json` selects
`plugins/aquarium`; its [manifest](../../../.codex-plugin/plugin.json) owns version,
skills and MCP entrypoints. The payload includes skills, references, assets,
hooks, helpers and bundled tools. The
[development producer](../../../tools/aquarium-dev/build_aquarium_artifact.py)
copies the marketplace declaration and plugin tree as `artifact_kind: codex-plugin`
with a development-version stamp. That artifact does not prove official
distribution readiness.

The selected installed qualification claim is the Codex edition only. Generic
ordinary Codex/Claude semantics and development Herdr participation by other CLIs
establish no additional shipped host coverage. EPIC-030 owns broader packaging
and qualification; whichever Epic lands second reconciles current outputs, shared
release contracts and scenarios without assuming support or adding a dependency.
TASK-172's unintegrated contract has an intentional no-note decision; operational
wiring owns the breaking user-action entry. Revisit that decision if the candidate
activates behavior. TASK-175/176 retain scenario preparation and actual installed
observations, including the Haepari role seams. No new report/helper schema,
Podway release Procedure, automated LLM gate or retry quota is introduced.
