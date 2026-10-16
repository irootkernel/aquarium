# Adaptive Procedure contracts

## Status and ownership

TASK-137 implements the closed Aquarium definition formats, canonical JSON
identity helper and necessary declaration signatures described here. Selection,
composition, structural qualification, storage, admission and handler activation
remain reserved for TASK-138 through TASK-145. These interfaces do not activate
adaptive execution. Existing handlers, ordinary v2 reports, canonical/custom
sources and immutable formal v1 sessions retain their current contracts.

The repository's `docs/todo/TODO-ADAPTIVE-PROCEDURES.md` owns remaining
implementation acceptance. The roadmap owns Task identity and lifecycle. This
reference owns the durable shared adaptive definition contract. Its signatures
are reference implementations; a new operation can establish the same guarantee
through its own explicit verified contract.

## Requirement and source basis

Derive obligations from original requirements, approved scope, repository
instructions and the invoking handler. Reconcile omitted and compound criteria
independently of the generated plan. Each due obligation needs a work producer,
readable input, evidence producer, required assessor, consuming Decision and
applicable effect or acceptance boundary. Future Epic obligations remain visible
without demanding unfinished members prematurely.

Prefer an adequate unchanged definition, then bounded adaptation, useful-fragment
composition and new authoring. The approved envelope covers preparation and
local adoption. It never changes requirements, selected review, transmission
scope, exact-diff approval, effect authority, acceptance or commit grants.

An adopted repository customization contributes its actual workflow obligations.
Disclose a justified replacement and preserve those obligations in the existing
envelope. An optional template or historic local bundle contributes no mandatory
policy merely by existing. Keep installed-library diagnostics separate from
selected-source health; unrelated missing templates cannot alone block a valid
selected source.

Plan-only stays read-only. Opted-out workflows do no Podway discovery or source
rendering. Non-Git new-project retains semantic assessment and exact document
approval without Git initialization or Podway operations.

## Families and due capabilities

| Family and callers | Assessment and review controls | Acceptance and late effects |
| --- | --- | --- |
| Task: task-handler | Approved plan; due delivery with required checks; selected technical review; final independent Judge | Actual user acceptance, task-close and separately authorized task-commit; conditional refinement and documentation |
| Goal: epic-handler | Current member/correction delivery; selected review; final assessment; Epic seams when due | Delegated member/correction acceptance; final Epic closeout and stopped outcomes require actual user acceptance; closeout retains its own grant |
| Validation: epic-validator, internal epic-handler | Original-source audit/re-audit, correction-group assessment, selected technical review and final integration | Only continuing epic-handler may accept internal validation by delegation; cold validation and stopped outcomes require user acceptance |
| Design: new-feature, new-project, refactor | Context/discovery, proposal/challenge/upstream QA, approved application and final assessment | Actual exact-diff approval; current-target verification before write and applied-byte verification; no product implementation |
| Diagnosis: war-room | Baseline/investigation, proposal/quality, approved document or no-change and final assessment | Actual proposal/no-change approval; incomplete investigation is a diagnostic delivery, never a repaired defect |

Task capability applicability comes from actual postconditions. Code/test changes
retain due refinement, required Deslop and delta verification. Documentation-only
work needs no unused implementation, refinement or Deslop prerequisite unless an
independent authority requires one. Documentation capability is due when canonical
documents or their required postconditions change; coherent documentation work
may own writing and verification. Direct phase-skill and admitted legacy contracts
continue separately. Goals do not inherit Task's phase workflow.

Ordinary Worker/Judge work stays separate from technical review. The selected
route retains its expected base/UI team, original reports, finding responses,
current target, route-change authority and remaining grants. One review team,
including its internal subagents, is one operation and one completed ordinal.
Incomplete delivery first retrieves the same operation. Retrieval consumes no new
ordinal and grants no provider switch; independently authorized route changes
retain their existing contract. Completed ordinal continuity, confirmation scope,
local settlement and explicit exhausted-authority decisions retain their
[existing owner](review-routing-contract.md).

## Closed definition interfaces

The schemas are [binding v1](../assets/schemas/procedure-binding-v1.schema.json)
and [fragment v1](../assets/schemas/procedure-fragment-v1.schema.json).
[adaptive_definitions.py](../shared/adaptive_definitions.py) parses them, rejects
duplicate JSON fields/non-finite numbers and checks local references. Native
Procedure fields embedded in a fragment remain governed by Podway's native
schema. Schema success is definition validity only.

Binding checks cover placement references, including closeout prerequisites;
fragment Action ports also resolve their declared native items. Cross-checking
binding item references against the separate native source belongs to TASK-141.

The helper currently requires Python and `jsonschema` from a supported
environment. This repository supplies them through its development requirements;
arbitrary target repositories cannot assume this checkout's `.venv` exists.
TASK-138 must provide a usable selected-admission interpreter and preserve legacy
paths without eager adaptive dependencies. TASK-142 establishes runtime readiness
before family activation; TASK-145 owns global/setup guidance. Each uses a
supported installed environment and reports missing prerequisites. This contract
authorizes no dependency installation or host runtime change.

A binding contains:

- `schema`, one `family`, its supported `entrypoints`, and compatibility
  `aquarium.adaptive/v1`. Invoking entrypoint belongs in existing runtime context.
- `procedure`: native `id`, supported native `version`, canonical native
  `digest` and exact file-byte `source_sha256`, both `sha256:<64 lowercase hex>`.
- `nodes`: placement keys mapping native `kind`, intended `role`, bounded
  `effects` and capability signature/typed `fields` aliases.
- `parameters`: declared input types, requiredness and descriptions, with no
  per-invocation values. Work-specific fixed text remains part of source identity.
- `obligations`: original source references, applicability rule, producer and
  evidence endpoints, optional assessor, consuming Decision and effects.
- `goal_assessments`: native placement and exact option-to-outcome mappings;
  `closeout`: descriptive accepted/stopped/shared boundaries and prerequisites.
- `origins`: exact definition ID/version/hash and source provenance.

A fragment contains stable `id`/`version`, purpose/applicability, declared
parameters, typed `inputs`/`outputs` with explicit endpoints, one `entry`, named
`exits`, native `node_definitions`/`placements`, internal and external rework,
effects, assessor boundaries, origins and exact dependencies. External rework
names a control port for composition to bind. An ordinary fragment cannot
assess `session_goal`. Session-level control templates may be composition building
blocks. Their whole-Procedure result receives full family qualification without
requiring one fixed template representation or topology.

The schema examples in the repository's `tests/fixtures/adaptive/` directory
define interface use only. Their hashes are synthetic and they are neither
admitted bundles nor runtime success evidence.

Neither format carries actual work IDs, approval, reviewer choices, candidate
results, native handles, session/attempt state, receipts, findings or consumed
grants. Those remain in ordinary v2 records and Podway. Bindings describe the
execution definition without becoming another progress database.

### Canonical bytes and exact identities

Aquarium JSON uses UTF-8, sorted keys, compact separators, preserved array order,
no non-finite numbers and no trailing newline. `definition_id` returns lowercase
SHA-256 hex of these bytes. A bundle ID is the canonical binding hash; the binding
has neither its own ID nor final absolute location. Procedure bytes contain no
bundle ID or binding path. Bootstrap locations are runtime item values. Complete
all definition bytes and identities before exact-target suitability assessment.

Use Podway's native canonicalization for the Procedure digest. Source-byte SHA-256
is a separate identity; formatting/comments may change it without changing the
native digest. Never substitute Aquarium JSON or a YAML serializer for native
canonicalization.

New authored/adapted identities use `aquarium-adapt-<family>-<token>` within native
limits. Allocate a collision-checked authoring token before hashing. It is not a
session, bundle digest or credential. New definitions start at version `1`; a
changed definition under the same ID increments the positive decimal version.
Unchanged reuse keeps identity. Canonical and unchanged foreign sources keep
their supported native identities and version strings. A changed mapping requires a new native revision,
usually a derived adaptive identity when the source was canonical.

Recovery resolves exactly `(procedure_id, procedure_version, procedure_digest)`.
Before adoption, one authoritative binding must exist for that key across every
approved root the worktree actually searches. Byte-identical copies are aliases.
Same native key with different source bytes, compatibility or mappings cannot
create another adopted binding: reuse the original complete bundle or author a
new native revision. This prevents lookup ambiguity independently of hash
collision assumptions.

Retained bundles are self-contained `procedure.yaml` plus canonical `binding.json`.
Origins are provenance, never mutable resume dependencies. Native readback has no
original authoring path or bundle ID. Prepared and running sessions resolve by
the tuple even without a bootstrap selector; a selected bootstrap is an additional
cross-check. Missing, corrupt, ambiguous and unsupported definitions stop before
begin/work and retain distinct recovery outcomes.

## Declaration signatures and qualification boundaries

[Capability signatures v1](../assets/adaptive/capability-signatures-v1.json)
capture necessary typed item contracts and actual operation IDs/digests from the
five ordinary canonical sources. They cover every current grouped/final Judge
operation, faithful audit and correction-group assessment, upstream quality,
approval, review control, acceptance, application currency and closeout. Extra harmless
items and different placement/definition IDs are allowed. Typed aliases preserve
operation meaning and cannot collapse distinct required fields.

`check_capability` returns `compatible`, `incompatible` or `not-established`
for a declaration slice. Unknown signatures are not-established; missing or
contradictory required native declarations are incompatible. Changed conditional
requiredness needs proof and returns not-established; making the field
unconditionally required satisfies that declaration guarantee. Provider enums,
unused outcome branches and delegated approval options are checked against the
selected workflow rather than every canonical choice. A caller can supply
an explicitly verified signature for a changed operation. Neither a label nor a
nonempty verdict text can supply a typed independent-assessment capability.
Assessment evaluation operations accept pass, fail and inconclusive so recording
can finish before routing. Unrelated native pass-only checks remain legitimate.
Finite maxima on mandatory unmet/unverified count fields need a proven capacity
for the exact assessment's original criterion basis. Without that proof,
`check_capability` returns not-established. Its optional `criterion_capacity`
input represents an independently established upper bound; a maximum below it is
incompatible, while an adequate bound can pass this declaration slice. TASK-141
owns the exact-basis proof. An operation digest supplies no capacity proof and
unrelated bounded integers retain their own contracts.

Each signature also names required relationships. TASK-141 must establish those
relationships through actual producer/evidence/Decision connections, guards and
forward effects. Declaration matching alone does not establish them. Actual
independent execution comes from the ordinary assignment and native result
observations; signatures and digests authenticate no agent.

TASK-141 must prove acceptance provenance using the actual `goal-kind` for Goals
and `workflow-owner` for Validation, exact `acceptance-source` values and consuming
guards. Every user-owned path must support and require `user`; delegated Goal
paths exclude final Epic closeout and stopped outcomes, and delegated Validation
requires continuing `epic-handler` ownership. Cold validation and stopped
Validation require actual user acceptance. These exact values/guards are reserved
qualification work; the current typed declarations alone do not prove provenance
or require unused delegation branches in a specialized Procedure.

All backed families retain `goal_tracking: true`. Native
`assessment.target: session_goal` mappings own achievement. Terminal names,
completed lifecycle or binding labels cannot establish success. Every feasible
achieved selection needs the current final Judge's actual achieved outcome,
pass verdict, zero mandatory unmet/unverified criteria and applicability through
direct guards or an established equivalent chain. A shared closeout terminal
may follow achieved, not-achieved or superseded outcomes.

Every relevant forward work/content change needs a later covering assessment.
Exact application approval likewise stays tied to current proposal/target bytes.
Use native rework invalidation for declared rework. Recognized bookkeeping,
actual acceptance, exact lifecycle-only deltas, independently verified evidence
projection and authorized commit/no-commit handoffs keep existing exemptions.
Unknown effects remain work-bearing and cannot gain exemptions through labels.

Qualification reports native-invalid, incompatible, not-established and runtime
failure separately. Native validity, graph guarantees, exact suitability and
actual runtime applicability remain separate claims. Predicate/dataflow analysis
must handle infeasible guarded paths and unknowns without exhaustive-path
assumptions. An unresolved proof reports its property and location; it neither
proves safety nor declares every noncanonical structure invalid.

## Suitability, replacement and preservation

Known reuse requires unchanged bytes, an already established structural contract,
a supported binding and current fit. Unsupported bindings and materially changed
definitions are not known reuse. Adequate known reuse keeps current assessment boundaries. Include fit
in an existing plan assessment when present; a Goal without a plan Judge gains
no fictitious report or extra cycle. New/changed/composed definitions require
exact pre-start independent suitability against complete bundle/native digest
and original requirement/plan basis. One compatible Task plan assessment may
cover both scopes. Bootstrap imports the real pre-session report and timing;
it must never pretend that Judge executed in the active attempt. Changed basis
on re-entry requires affected current assessment, not replay of an old pass.

Declared rework, same-operation retrieval and approved normal successors need no
repeated question. Missing topology in an in-progress session requires explicit
replacement consent. Qualify and retain the successor first and reconcile pending
effects/descendants. Disclose current state, missing topology, pending native work,
old/new identities, cancellation/archive effects, retained history/results,
remaining grants and the exact proposed atomic transition before requesting
consent. Then use native consented atomic preserve-start with fresh fences and
one idempotency key. Recover unknown outcomes
with that same request/key. No cancel-then-start, reset, deletion, false achieved
outcome or authority reset substitutes for the transaction.

Retention is automatic inside the approved preparation scope and locally ignored,
normally under `.podway/procedures/.local/<bundle-id>/`. Approved custom roots and
existing suitable ignore policy remain supported. Atomic publication and resolver
uniqueness arrive together in TASK-138. No automatic Git inclusion, TTL eviction,
central session map or origin lookup is required for resume.

After actual successful use establishes distinct reuse value, offer useful whole
or fragment candidates together at closeout. Show exact changes, paths,
parameterization and observed limits. Preservation needs specific content consent;
broad editing/commit authority does not replace it. After original workflow
finalization, content consent permits applying the exact library diff. Committing
requires an explicitly matching promotion grant; leave the approved diff
uncommitted when that grant is absent. Content and commit consent may be one
question. Declining keeps local
recovery and completed original work. Changed/extracted definitions receive fresh
schema/port checks and representative flattened native validation; source runtime
success never transfers to them.

## Amendment owners and reserved delivery

| Task | Exact existing owner/rule to amend when implemented |
| --- | --- |
| TASK-138 | podway-integration and tool-catalog five-file readiness; dev-setup inspect_tools ID/filename/tracking coupling; selected admission plus atomic writer/resolver and supported interpreter, with lazy adaptive imports preserving legacy paths |
| TASK-139 | shared adaptive selection/preparation and source authority; existing plan/assignment requirement coverage and plan-only boundaries |
| TASK-140 | shared composition, namespaces, typed ports and self-contained flattening; preserve semantic operation IDs/digests and fragment/session control distinction |
| TASK-141 | shared structural qualifier and exact suitability/bootstrap lifecycle; procedure-node-contracts adaptive compatibility alongside current canonical inventory |
| TASK-142 | task-handler/task-orchestration fixed seven-phase loading and unconditional refine discovery; ordinary-agent-orchestration five-bundled-source restriction and goal-judge helper; epic/validation orchestration, worker-guidance, plan-handoff, task-close/task-commit adaptive mappings/recovery; runtime readiness before activation |
| TASK-143 | new-feature/new-project/refactor and design-diagnosis orchestration adaptive selection, QA, exact application and non-Git recovery |
| TASK-144 | war-room and design-diagnosis adaptive diagnosis; podway-integration and epic-handler successful-terminal-only replacement wording; task-orchestration, epic-orchestration, validation-orchestration and design-diagnosis-orchestration continuation rules for shared consented atomic supersede; preserve task-handler's prohibition on replacing a session merely to recover reports |
| TASK-145 | task-commit promotion handoff; dev-setup and global-setup dependency guidance; agents-guidance and AGENTS managed/local source distinction; cross-family recovery; committed VM driver/fixtures |
| TASK-146 | committed-candidate observations and canonical document settlement; preserve original correction owners and actual Master acceptance |

Positive fixtures must include all five canonical declarations, valid namespaced
typed aliases and genuinely different work/evidence/Decision structures. Negative
fixtures target missing required types/operations, parent-goal assessment inside
ordinary fragments, violated evidence or authority. Unknown contracts produce
not-established. ADAPT-25/26 are definition/signature controls here; whole-graph
and runtime claims remain with TASK-140/141 and activated families. Tests of
fabricated records establish rejection behavior only.
