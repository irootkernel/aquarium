# Supervised agent orchestration contract

## Qualification and authority

Required Worker and Judge placements need an admitted Procedure and native
qualification applicable to their exact operative role snapshot, assignment and
supported recovery path. Source declarations, completed task labels and reading
this reference do not activate delegation or reinterpret an existing session.
Released managed copies and admitted snapshots keep their own execution rules.
Use [Procedure node contracts](procedure-node-contracts.md) and the owning
workflow reference for the admitted placement.

The operative role instructions are in
[Goal Judge](../skills/goal-judge/SKILL.md) and
[Worker guidance](worker-guidance.md). The
[native mapping profiles](native-agent-mappings.md) describe local preparation
and delivery-mapping components and their qualification domains. An unsupported
required binding or recovery path blocks execution without direct fallback.

The assignment supplies the repository's current canonical requirements and
execution SOT. Its canonical roadmap owns identities, dependencies and status;
qualification evidence must identify its actual source and target. This
reference owns the frozen shared role, assessment, handoff and recovery
contracts. Native tool contracts remain authoritative for their actual fields
and lifecycle operations.

## Roles and lifetime

| Role | Owns | Authority boundary |
| --- | --- | --- |
| Orchestrator | Current authority and criteria inputs, bounded assignments, native supervision, Judge continuity, candidate applicability checks, and permitted Podway Decisions | The Primary accepts native deliveries under their placement's delivery checks and execution authority. Semantic progression requires an applicable Judge verdict; the Primary cannot replace a disputed verdict with its own pass. |
| Judge | Semantic assessment of all applicable canonical criteria against the exact candidate and original evidence | Report-only: no implementation, source or Git mutation, Podway mutation, commits, or grant of user authority. A negative verdict creates no correction or review authority. |
| Workers | Assigned research, analysis, implementation, verification, and authorized corrections | Stay within the assignment's effects, scope, and checks; return a complete candidate handoff. Delivery establishes neither goal achievement nor user acceptance. |

The logical Judge lifetime is the entire standalone Task, Epic-handler, Design,
or War-room invocation. Epic-handler retains one logical Judge across member
Tasks, pre-validation corrections, internal Epic validation, and closeout. An
independently invoked cold Epic-validator starts a fresh Judge and reads original
evidence independently. It cannot inherit an Epic-handler completion verdict as
proof. A persistent Judge retains identity and assessment context when supported,
without running continuously.

Use a resumable host-native agent kind for the Judge. Preserve explicitly
selected model and effort values and otherwise preserve host defaults. Role
identity covers complete immutable role content and its resolved dependencies,
not just a role name. Reading and research can run in parallel. A shared checkout
has one implementing Worker at a time; replacement requires verified quiescence.
Selected technical reviews keep their own native concurrency and isolation.

The Orchestrator supplies conflicting evidence or a disputed applicability claim
to the Judge for reassessment. The existing verdict remains unusable until the
Judge resolves it against the current target. Neither a majority of reports nor
an Orchestrator summary can erase a supported gap.

## Work and evaluation boundaries

Every work-bearing assignment states its objective, purpose, node instruction,
authoritative inputs, complete selected evidence, permitted mutations, excluded
effects, deliverables, and success criteria. Common role instructions do not
substitute for node-specific work. The Judge has read access to original criteria,
artifacts, and evidence within the approved source scope, independently of the
Orchestrator's summary. Unreadable required material remains an evidence gap.

Structure semantic work as a Worker candidate Action, a Judge assessment Action,
and an Orchestrator Decision selecting progress, rework, or evidence collection.
Worker Action completion records candidate delivery. Only the separate assessment
supports a semantic pass. Delegate Action placements only. The Primary retains
Decisions; a Judge assessment Action is never itself recursively judged.

For the Worker Action, the Primary checks the complete delivery, its native
bindings, required records, and permitted effects, accepts that delivery, and
completes the Action so the Judge can assess it. This acceptance records delivery
even when the candidate has unresolved goals. For the Judge Action, the Primary
checks report completeness, criterion coverage, provenance, applicability, and
execution authority, then accepts the report and completes the Action. It does
not repeat the Judge's semantic assessment or require another Judge verdict to
accept that report. The following Decision uses the current checkpoint assessment
to select progress, rework, or evidence collection. A phase checkpoint verifies
every obligation due at that phase and applicable parent constraints. It does
not require unfinished later work to be complete. Keep those later obligations
and other original gaps in the full global assessment; do not erase rows, report
false zero counts, or mark them globally not applicable to advance.

| Procedure | Semantic checkpoints | Native checks and retained boundaries |
| --- | --- | --- |
| `aquarium-task-v2` | Work-bearing planning, implementation, refinement, verification, documentation, review-evidence assessment, and final Task outcome | Operational records, metadata, route entry, item consistency, approval, commit, and disposition use their native checks. Final Task assessment covers applicable parent constraints without requiring future members to be finished. |
| `aquarium-goal-v2` | Member work, pre-validation corrections, goal evidence, and final goal outcome | Epic-handler uses no Task phase workflow. Its logical Judge follows successors into internal validation. Final closeout may use the successful exact validation basis and focused closeout checks only while implementation is unchanged. Delegated member/correction acceptance and actual final user acceptance remain distinct. |
| `aquarium-validation-v2` | Direct audit, admitted corrections, re-audit, technical-review evidence, and final Epic outcome | Assess integration and overall purpose even when every Task passed. Internal validation retains the Epic-handler Judge; independent cold validation uses a fresh Judge. Audit and provider findings keep separate provenance and the existing serial gates. |
| `aquarium-design-v2` | Context/discovery work, drafts, challenge/quality evidence, document application verification, and final design outcome | Preserve the Ouroboros leaf contract and exact document-diff approval. A Judge pass cannot authorize application, installation, implementation, staging, or commits. Non-Git new-project keeps its non-Podway path. |
| `aquarium-war-room-v2` | Baseline/reproduction, investigation, cause/scope evidence, proposal quality, document verification, and final diagnosis outcome | The Primary makes cause/scope and route Decisions from recorded assessments. Preserve exact approval and every supported terminal branch, including incomplete investigation and approved no-work with verified no-change. Diagnosis success does not authorize a fix. |

Simple operational, metadata, approval, and lifecycle transitions use current
native checks without an extra semantic assessment cycle. A work-bearing node's
implementation owner defines its actual assessment placement and selected inputs;
this table neither invents node IDs nor migrates a graph. Required criteria and
checks cannot disappear through that placement choice.

The Judge reconciles assignment criteria with canonical authority. Reuse existing
criterion IDs or source path and section labels; an omitted assignment criterion
still requires assessment. Each row states its source, applicability, current
state, readable evidence, provenance, and remaining gap or reason:

- `met`: sufficient evidence supports the entire criterion.
- `unmet`: readable evidence establishes a violated obligation.
- `unverified`: required evidence, coverage, or resolved authority is missing.
- `not-applicable`: canonical scope excludes the obligation;
  record that basis explicitly.

A partially assessed compound criterion keeps its unassessed portion
`unverified`. Mandatory global `unmet` or `unverified` criteria prevent whole-goal
acceptance. A separate phase result cannot establish achievement or waive an
already-due obligation. Conflicting evidence establishes `unmet` if it proves a
real gap;
otherwise the conflict remains `unverified`. A negative assessment identifies
needed work or evidence and its owner without authorizing the effect.

## Versioned assessment documents

The following schemas describe Aquarium handoff documents, not new native wire
fields or an installed adapter. Their values must retain source provenance.
Runtime records and assessment documents follow
[evidence residency](evidence-residency.md); do not put live identities or
execution logs into tracked roadmap or product documentation. This contract
creates no central state file, scheduler, daemon, or private executor database.

All three document schemas carry these common fields:

| Field | Content and producing authority |
| --- | --- |
| `schema` | Exactly one versioned schema identifier below |
| `work` | Repository/roadmap scope, named work unit and objective, authoritative requirement sources and their revision or approved basis; supplied by the owning workflow |
| `target` | Exact candidate representation, base revision, included and excluded paths/artifacts, and immutable content binding; use actual Git content identity or historical native capture identity and retain how independently checked artifacts bind to it; record live-source selector metadata separately |
| `procedure` | Current session, Procedure ID/version, node, attempt, and goal revision from current Podway observation, or explicit inapplicability for an authorized non-Podway path |
| `native` | Actual backend, integration version, Primary/supervisor, agent, and task identities with references to supported public records; native output and the qualified integration supply these values |
| `configuration` | Complete immutable role content/dependencies and accepted agent configuration bindings with their source and digest provenance |
| `authority` | Recoverable envelope, permitted effects and exclusions, applicable unconsumed grants, and remaining correction/review authority |
| `evidence` | Complete input and output references and digests, access limitations, original-artifact provenance, and verification targets/outcomes |
| `gaps` | Unresolved requirements, evidence, native capability, safety, and handoff obligations, each with its owner |

`target` must bind all candidate bytes relevant to the claim, including owned
unstaged, untracked, generated, or derived artifacts when the chosen target
supports them. A staged assessment uses index bytes; a committed target uses its
resolved immutable tree. Context does not silently become candidate scope. Bind
requirements and external check inputs as well as source bytes. Missing or
ambiguous target identity prevents acceptance.

### Worker handoff

Schema: `aquarium.worker-handoff/v1`.

In addition to the common fields, provide the assigned deliverables, exact
changed-path/artifact inventory, verification performed and omitted with reasons,
complete result reference/digest, native feedback and settlement state, and the
proposed next owner. Identify delivered and still missing work separately. A
Worker's conclusion is an author claim; the Judge checks its evidence directly.
The handoff supplies no Judge verdict, formal acceptance, or receipt by itself.

### Judge assessment

Schema: `aquarium.judge-assessment/v1`.

Include the Worker handoff/result binding, the actual Judge identity and
configuration, the complete reconciled criterion rows, node/Task/Epic checkpoint,
applicable parent or seam constraints, omitted-assignment criteria, and a verdict
of `pass`, `rework`, or `evidence-needed`. `pass` requires every mandatory
criterion to be `met` or legitimately `not-applicable`; an established gap yields
`rework`, and an unresolved evidence gap prevents pass. Retain both kinds of gaps
when they coexist. Link the selected technical-review basis and its limitations;
a Judge report is never technical-provider evidence. Preserve any legitimately
carried criterion assessments with their exact applicability basis.

For a nonfinal phase, also record the current obligations, their direct original
evidence and applicable parent constraints, and a distinct checkpoint result of
`pass`, `fail`, or `inconclusive`. A phase pass requires actual satisfaction of
all due obligations and required checks. Report fidelity alone cannot prove
implementation, correction or application success. A faithful negative audit,
quality or technical-evidence result may reach its original gap router while
the global verdict and original criterion counts remain negative. Missing phase
evidence is inconclusive; an established phase failure requires owned rework.
Neither result grants an effect, new provider operation or review ordinal.

The document also states verification freshness, consumed review ordinal/kind,
finding lineage and dispositions, remaining authority, and follow-up obligations,
or their explicit inapplicability. It grants no additional assessment budget.

### Recovery checkpoint

Schema: `aquarium.orchestration-checkpoint/v1`.

Include the last independently verified native and Podway state, original
package/input/result bindings, accepted and unaccepted results, outstanding
feedback/acceptance operations and their exact request recovery references,
current criterion assessments, current candidate/requirements, and pending work.
Preserve round accounting, review ordinals, finding dispositions, grant
consumption, configuration provenance, and any frozen correction set. State
uncertainty explicitly; a checkpoint is a lookup basis and must be reconciled
with current authorities before action.

For replacement, retain predecessor provenance, quiescence evidence, the
restored goals and original evidence, and the replacement's actual native
identity/configuration. The new Judge must establish verdict applicability;
restoring a prior report alone cannot establish pass.

## Native mapping and acknowledgement responsibilities

`TASK-111` must supply a versioned mapping for each actual Codex and Claude
backend before required delegation activates. That mapping states the supported
public dispatch, session, feedback, accepted-task, complete-result, settlement,
and reconnect surfaces, their actual schemas, and how each required value is
produced and durably acknowledged. Vendor documentation and synthetic fixtures
are implementation references; neither qualifies actual host support.

The mapping must cover all execution identity fields required by the installed
Podway delegation contract, including `binding_ref`, `role_ref`,
`role_snapshot_digest`, `adapter_id`, `adapter_version`, `primary_host`,
`scope_kind`, `scope_ref`, `supervisor_ref`, `worker_ref`, `task_ref`,
`agent_configuration_digest`, and `accepted_task_digest`. Keep accepted task,
complete result, role snapshot, accepted configuration, and Podway package
digests distinct. The native backend owns actual agent/task/result identity;
the integration verifies the exact resolved role/dependencies, dispatch input,
accepted configuration and task bytes, complete immutable result, durable round
accounting, acknowledgement, and settled disposition. None may be inferred from
a role label, task prose, display status, or result summary.

The acknowledgement domains remain separate:

| Domain | Responsibility |
| --- | --- |
| Native accepted assignment | The qualified integration proves which exact configuration and task input the actual backend accepted, using supported durable acknowledgement. |
| Native result and settlement | The integration binds the complete result to that task and proves `idle` for retain or `released` for release after acceptance, with actual round accounting. |
| Semantic assessment | The Judge binds its verdict to current canonical requirements, candidate, and complete evidence; this is assessment-document content. |
| Formal native result acceptance | The Primary verifies the placement's delivery or report requirements, exact native result bindings, and execution authority, then explicitly accepts the result and retains that basis. A semantic Decision separately requires an applicable Judge verdict. |
| Podway receipt and Action completion | Podway owns current package/attempt/item identities, mutation fences, receipt applicability, and structural completion. A receipt neither proves filesystem candidate bytes nor grants user approval. |

Operate delegation through the installed `$use-podway` contract. Read the complete
current package and selected evidence; reconcile native work; record all final
selected items before accepting. Native result acceptance and Podway Action
completion are separate operations: accept the exact applicable result first,
then complete with a current applicable receipt and freshly observed fences.
A later actual item edit, including optional or cosmetic edits, can invalidate
that receipt. Historical acceptance or exact request replay does not establish
current readiness.

Unsupported required metadata, acknowledgement, durable reconnect, or quiescence
is a qualification blocker. Report the exact missing surface and owner before
activation; never fabricate identities/receipts, scrape private executor state,
relabel fixture evidence, silently perform required delegation directly, or
change Podway core within this epic. Required delegation cannot be waived by
marking an unavailable placement complete.

## Recovery and invalidation

Try supported reconnect with retained actual agent/task identities first. A
session ID or terminal display label alone cannot resolve uncertain work. After
unknown dispatch or result responses, reconcile the actual accepted assignment
and complete result before another dispatch. Recover an uncertain acceptance
request through its native owner with the original exact request and idempotency
identity; do not create a substitute acceptance to hide uncertainty.

When reconnect is unavailable, establish settlement and quiescence before
replacement. Restore goals, complete immutable configuration, original evidence,
criterion states, remaining work, and consumed authority. Stop with the concrete
missing capability when public native surfaces cannot establish safe state.
Judge or Worker replacement grants no Primary replacement or host-switching
support. Keep the current Primary unless a supported, explicitly authorized
native successor path exists.

A fresh Podway attempt never authorizes replay of external work. Revalidate any
reused artifact against current inputs and obtain the qualified acknowledgement
for the accepted task; never relabel an old receipt. Reject late results, wrong
candidates, stale goal revisions, and superseded agents before progression.
Candidate, requirement, or material check-input changes invalidate affected
verdicts and verification. Reassess invalidated criteria on the new target and
carry unaffected criteria only with a verified applicability basis. A replacement
agent or context restoration does not reset review budgets or correction grants.

## Technical review, correction, and user approval

Preserve [review routing](review-routing-contract.md), the
[Review Brief](review-intent-contract.md), and
[finding dispositions](finding-disposition.md). Selected technical routes retain
exact targets, native reviewer topology, complete reports, publication/check
requirements where applicable, recovery, and assurance limitations. Standalone
completion-review capabilities remain available. The Judge consumes their
reports and evidence and owns embedded semantic goal/checklist verdicts; it
neither replaces a selected technical operation nor counts as a technical
reviewer. A provider completion report retains its original criterion assessments
and provenance even when the Judge disagrees.

Keep the existing serial operation, confirmation, completion, finding-class,
rework-authority and settlement gates, with current local-correction classification
before provider-rework authority. Preserve consumed ordinals and
assessment kind, frozen findings, accepted-risk evidence, Low dispositions, and
remaining review/correction authority. A semantic rework verdict cannot start
another technical review or correction beyond that authority. Confirmation-only
scope remains limited to its frozen corrections and direct regression surface.
A permitted local-settlement delta retains its original review basis and required
local checks; do not claim the old review covered changed bytes. Eligible local
corrections consume no provider ordinal and remain within the existing effect
authority, including in confirmation-only mode.

A semantic pass is necessary for applicable work, but execution gates, native
checks, review evidence, and user decisions must independently pass. Preserve
Task closeout and cold-validation user acceptance, Epic-handler delegated member
and correction acceptance, internal validation delegation, and actual final
Epic acceptance. Design and War-room retain the
[Ouroboros leaf and exact-diff contract](ouroboros-integration.md) and applicable
[design gates](design-gates.md). Approval for one document or provider operation
grants no installation, product implementation, staging, commit, push, or
publication authority. Commit grants remain exact, separate, and consumable.

## Compatibility and qualification

Retain all five stable Procedure IDs and increment changed source versions.
Align bundled declarations, handler inputs, inspectors, selected evidence, and
observation expectations as one compatible candidate. Delegated Procedures use
the native delegation-aware observation contract; existing direct behavior keeps
its own observation meaning. Native-valid, handler-compatible, and qualified
execution remain separate claims.

Admitted snapshots are immutable. Source updates apply to successors only and
preserve repository customizations. An admitted old snapshot continues through
its supported released handler and native contract; current required-placement readiness is a separate
claim. An incompatible snapshot cannot be reinterpreted with the new graph.
Retain its exact state and explain either that supported continuation or a
separately authorized compatible successor after pending effects are reconciled
and writers and descendants are quiescent. Preserve customized bytes; unknown
semantic changes remain unqualified for automatic managed execution. This
repository's installed managed copies follow the host's released combination;
candidate development does not update them or installed tools.

Existing users must update managed Procedures and begin compatible successor
sessions. This is a breaking change under repository policy. Verify exact
candidate installation and upgrade over the host-installed release combination
in the dedicated UTM macOS VM, including Master's separate functional checks,
before release. Host installation, other-repository rollout, and publication
remain separately authorized operations. Local structure checks and protocol
fixtures establish neither actual native delegation nor semantic workflow
success.
