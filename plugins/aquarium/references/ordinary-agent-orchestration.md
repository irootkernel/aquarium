# Ordinary native agent orchestration

## Contract status and authority

TASK-126 reserves these ordinary v2 interfaces. TASK-127 implements them in
handlers, role instructions, helpers and all five bundled Procedures. Until that
alignment is verified, current sources and installed handlers retain their
existing contracts. This definition alone does not fix startup or activate an
existing session.

Operational roles use supported native subagents of the current Primary's
harness: a Codex Primary uses Codex Workers and a Codex Judge; a Claude Primary
uses Claude Workers and a Claude Judge. Preserve explicitly selected supported
model options and otherwise use harness defaults. Unavailable internal model
telemetry does not block ordinary work. Selected technical reviews keep their
own provider and topology, including Claude through Herdr for a Codex workflow.

The harness executes agents; ordinary Podway Actions record work and evidence
without authenticating native calls. Declared formal delegation still requires
the integration and receipts in the [formal v1 contract](agent-orchestration.md)
and [mapping profiles](native-agent-mappings.md). Preserve v1 interpretation and
digest domains; never fabricate its fields or relabel an admitted formal session.

## Roles and assessment boundaries

| Role | Responsibility | Boundary |
| --- | --- | --- |
| Orchestrator / Primary | Resolve scope and authority, assign agents, reconcile results and make permitted workflow Decisions | Own approval conversations and lifecycle operations; preserve checks, selected reviews and exact grants; never attribute delegated acceptance to Master |
| Worker | Perform assigned research, implementation or documentation with refinement and verification; return actual artifacts, results and gaps | Stay within assigned effects; only one mutating Worker operates in a shared checkout at a time |
| Judge | Independently assess due obligations against original requirements, current artifacts and actual evidence | Report only; no implementation, check execution, nested dispatch, lifecycle mutation or grant of authority |

Keep one logical Judge throughout an invocation when supported. Internal Epic
validation uses that Judge; independent cold validation starts a fresh Judge.
A recovered or replacement Judge establishes current applicability independently.
Persistent identity and full executor history are not prerequisites for a fresh
independent assessment. The Primary cannot label its own assessment a Judge result.

Assess the plan, coherent delivery with its refinement and verification, and
completion after admitted technical review. TASK-127 expresses these groups
using supported Actions, selected evidence and Primary Decisions:

| Workflow | Meaningful assessment boundaries |
| --- | --- |
| Task | Approved plan; implementation or documentation delivery with refinement and required checks; final completion with admitted review and settled corrections |
| Epic / Goal | Current member or owned correction outcome; final integration and overall purpose, including review and internal validation where due |
| Validation | Independent original-source audit or re-audit; each correction group with checks before settlement; final integrated outcome after admitted review |
| Design | Context and discovery; draft, challenge and quality evidence; approved application with verification and final design outcome |
| War-room | Baseline and investigation for cause/scope Decisions; proposal and quality evidence; approved document or verified no-change delivery and final diagnosis outcome |

Operational bookkeeping and report assembly do not create another Judge cycle.
Judge reports are never recursively judged. The Primary checks completeness,
source coverage and applicability without repeating the semantic assessment.

Reconcile assigned criteria with canonical sources, including omitted criteria
and applicable parent constraints. Each criterion retains its source, evidence,
provenance, gap and state: `met`, `unmet`, `unverified` or `not-applicable`.
A phase assesses every due obligation while preserving the actual global state
of future obligations. Whole-goal passage requires every mandatory criterion to
be met or legitimately inapplicable. Unassessed parts of compound criteria remain
unverified. Faithful negative audit or quality output reaches its original gap
router without claiming repair or overall achievement.

Treat review findings as hypotheses until a due requirement and reachable user
impact support them. Preserve actual defects and missing required evidence;
optional future hardening does not block acceptance. Request more information
only when it can change that decision. Scope, mandatory checks, selected review,
correction authority, actual approvals and commit boundaries remain independent.

## Ordinary v2 documents

These Aquarium documents are not native wire schemas. Use the exact identifiers
below and retain source provenance. Runtime documents follow
[evidence residency](evidence-residency.md), without a tracked execution log,
central state file, collector, scheduler, provider allowlist or retry quota.

Every document carries these common fields:

| Field | Required meaning |
| --- | --- |
| `schema` | One ordinary v2 identifier below; never relabel v1 |
| `work` | Repository and canonical work identity, objective, original requirement sources and their revision or approved basis |
| `target` | Current artifact basis, applicable base revision, included/excluded scope and identification of relevant candidate bytes and check inputs |
| `authority` | Actual envelope, allowed/excluded effects, applicable approvals and grants, consumed and remaining review/correction authority |
| `procedure` | Available public session, Procedure, node, attempt and goal context; explicit inapplicability for an authorized non-Podway path |
| `native` | Current harness, available public agent/task handles and observed lifecycle state; explicit unknown values for unavailable records |
| `evidence` | Readable original inputs, actual results, checks performed or omitted with reasons, provenance and access limits |
| `gaps` | Remaining due work, missing evidence, uncertain effects or capability gaps and their next owner; empty only when none remain |

Use Git objects or locally checked artifact content identities appropriate to
the claim, including relevant owned dirty or untracked bytes. Planning can name
the current basis before deliverables exist; delivery and verdicts identify the
actual candidate they cover. Local digests prove content identity only.
Material candidate, requirement or check-input changes invalidate affected
assessments and checks; carry unaffected evidence only with current applicability.
Unavailable identity/model records remain unknown without blocking startup.
Missing evidence for a due product obligation still prevents its pass.

| Schema | Producer and additional content |
| --- | --- |
| `aquarium.assignment/v2` | Primary adds `role` (`worker` or `judge`), purpose, `instructions`, `deliverables`, `success_criteria` and `checkpoint`; states mutation/report-only boundaries and supplies original sources and selected evidence |
| `aquarium.worker-handoff/v2` | Worker adds originating `assignment`, delivered/missing `deliverables`, exact `changed_artifacts`, actual `results`, feedback/settlement state and `next_owner`; separates firsthand and supplied evidence |
| `aquarium.judge-assessment/v2` | Judge adds `assignment` and applicable Worker result references, `checkpoint`, reconciled `criteria`, `applicability`, technical-review basis/limits and `verdict` (`pass`, `rework`, `evidence-needed`); nonfinal `checkpoint_result` is `pass`, `fail` or `inconclusive` for due obligations |
| `aquarium.orchestration-checkpoint/v2` | Primary adds last observed native/workflow state, known assignments/results, `pending_operations`, current criteria/candidate, consumed grants/ordinals, frozen findings or correction scope and `next_owner` |

Ordinary dispatch may carry the assignment through supported text or structured
input. Frozen role/dependency snapshots, effective configuration digests and a
preparation helper are not admission requirements. A summary cannot substitute
for required source access. Preserve failed, omitted and inconclusive checks and
established/evidence gaps together. Worker delivery supplies no Judge or user
acceptance. Provider reports keep their original rows; Judge provenance cannot
replace technical-provider coverage. A negative verdict grants no new effect.

## Recovery and breaking updates

Reconnect known agents through supported native operations first. Reconcile an
unknown dispatch, result or external effect before replay. Before replacing a
mutating Worker, establish settlement of that Worker and relevant descendants.
If public evidence cannot establish safe settlement, stop that mutation and name
the concrete missing capability. Full transcripts, private executor history and
configuration digests are not ordinary recovery prerequisites.

A Judge may reconnect or be replaced with a fresh independent agent supplied
the original criteria, current artifacts, prior gaps and remaining authority.
Restoring an old pass alone cannot establish current pass. Replacement does not
reset grants, review ordinals or stopped-work boundaries. If native subagents
are unavailable, report the actual capability gap and obtain a supported
alternative without silently switching harnesses or inventing independence.

Keep the five stable Procedure IDs; TASK-127 advances source versions to Task
`31`, Goal `34`, Validation `33`, Design `11` and War-room `11`. Preserve exact
prior sources, customized bytes, immutable sessions and historical reports,
including role/configuration/task/result/Podway digest domains. Recognized prior
digests prove provenance, not compatibility with the new graph. Existing formal
sessions retain their receipt obligations and supported released continuation.
Authorized managed updates and compatible successors require reconciliation of
pending effects and writer settlement; never overwrite customizations or migrate
an existing session by relabeling it.

Develop on the host with released tools and unchanged installed managed sources.
Candidate installation and installation-dependent checks run only in the
dedicated UTM macOS VM. EPIC-024 verifies Codex only. Results for other harnesses
remain unverified, and these results do not gate ordinary admission. Structural
and synthetic results,
development functionality, candidate-bound release acceptance and actual Master
acceptance remain separate claims.

## Producer and consumer alignment

TASK-127 updates these owners together. Helpers remain optional for ordinary
dispatch; their schema-selected v2 support is pending.

| Owner | Required alignment |
| --- | --- |
| [Task handler](../skills/task-handler/SKILL.md), [Epic handler](../skills/epic-handler/SKILL.md), [Epic validator](../skills/epic-validator/SKILL.md) | Produce assignments/checkpoints and consume actual Worker results and applicable Judge reports; preserve actual acceptance and commit authority |
| [New feature](../skills/new-feature/SKILL.md), [new project](../skills/new-project/SKILL.md), [refactor](../skills/refactor/SKILL.md), [war-room](../skills/war-room/SKILL.md) | Use grouped native roles while preserving proposal, quality, exact-diff, leaf and non-Git boundaries |
| Task phases: [plan](../skills/task-plan/SKILL.md), [implement](../skills/task-implement/SKILL.md), [refine](../skills/task-refine/SKILL.md), [verify](../skills/task-verify/SKILL.md), [document](../skills/task-document/SKILL.md), [review](../skills/task-review/SKILL.md), [close](../skills/task-close/SKILL.md) | Produce v2 handoffs or consume final assessments under a compatible ordinary handler; retain direct-invocation authority |
| [Worker guidance](worker-guidance.md), [Goal Judge](../skills/goal-judge/SKILL.md) | Produce v2 reports without formal qualification prerequisites |
| [Shared contract](agent-orchestration.md), [native mappings](native-agent-mappings.md) | Route ordinary v2 separately from formal/historical v1 when TASK-127 changes the sources; preserve every existing v1 digest domain |
| [Task](task-orchestration.md), [Epic](epic-orchestration.md), [Validation](validation-orchestration.md), [Design/diagnosis](design-diagnosis-orchestration.md), [node contracts](procedure-node-contracts.md) | Define grouped responsibilities, original evidence, semantic progression and recovery |
| [Five bundled Procedures](../assets/podway/procedures/) | Align Action instructions, item prompts, artifact schemas, evidence selectors and Decision consumers; omit formal `delegation` from ordinary defaults |
| [Assignment preparer](../skills/goal-judge/scripts/prepare_assignment.py), [dispatch renderer](../skills/goal-judge/scripts/render_dispatch.py) | Add schema-selected ordinary v2 support through minimal `goal-judge/scripts/ordinary_assignment.py`; preserve v1 interfaces, outputs, exact bytes and digest domains |
| [Codex binder](../skills/goal-judge/scripts/bind_prepared_delivery.py), [Claude binder](../skills/goal-judge/scripts/bind_claude_delivery.py), [mapper](../skills/goal-judge/scripts/map_native_delivery.py), [capture client](../skills/goal-judge/scripts/read_codex_thread.py) | Retain formal/historical contracts and rejection behavior; never synthesize v1 native provenance from ordinary v2 |
| [Setup inspector](../skills/dev-setup/scripts/inspect_tools.py) | Align handler-structure, delegation and preview inspection; classify prior formal/custom sources without rewriting them |
| Repository Procedure tests (`tests/unit/test_procedure_alignment_contracts.py`), setup tests (`tests/test_inspect_tools.py`), runtime fixtures (`tests/podway_runtime_qualification.py`) | Check executable routes, due checks, authority and source classification; preserve separate historical formal receipt coverage |

Existing v1 Worker, Judge and recovery reports have no standalone parser or
renderer: role instructions, workflow references and Procedure items own their
production and consumption. The ordinary module supports assignment input and
rendering only, without a generic report engine or native-call authentication.
Repository package validation (`tests/validate.rb`) remains structural. Prose
matching cannot verify role behavior; actual installed native progression,
failure, rework and recovery require separate functional observations.
