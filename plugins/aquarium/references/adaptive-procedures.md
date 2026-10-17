# Adaptive Procedure contracts

## Status and ownership

TASK-137 implements the closed Aquarium definition formats, canonical JSON
identity helper and necessary declaration signatures described here. TASK-138
implements selected known-source admission, atomic local retention and exact-key
recovery. TASK-139 implements fit selection and approved source-only preparation
through an ordinary Worker assignment. TASK-140 implements explicit whole/fragment
composition through that preparation path. Structural qualification and handler
activation remain reserved for TASK-141 through TASK-145. These interfaces do
not activate adaptive execution. Existing handlers, ordinary v2 reports, canonical/custom
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

## Selection and source-only preparation

`shared/adaptive_preparation.py` validates the existing
`aquarium.assignment/v2` input and returns planning or prepared-definition data
in that ordinary assignment. It adds no requirements owner or runtime executor.
The invoking Primary supplies actual approved scope and source access; the
helper cannot establish semantic completeness or approval authenticity.

`work.requirement_sources` identifies original inputs by `id`, repository-relative
`path` and exact raw-byte `sha256`. A source has role `requirements` or
`adopted-customization`; optional `template` and `historical` entries contribute
no obligations. Unknown role/family values are invalid input; a recognized
other-family source remains conditional and is not required here. An optional
`family` limits applicability. Structured original
JSON has `criteria` rows with `id`, `text` and optional `parts` (`id`, `text`).
Markdown uses the complete document or a unique `section` selector for an ATX
or Setext heading (the heading line or its title) and its body. Fenced
heading-like text remains in the body; a real heading of equal or higher level
ends the section. Missing, ambiguous or unsupported selectors return
`not-established`; malformed selector types return `invalid-input`. Paragraphs,
nested bullets and compound clauses remain in that original basis.
The helper does not infer their semantic independence from Markdown formatting.

`target.procedure_plan` holds invocation data:

- `family`, `entrypoint`, `mode` (`plan-only` or `prepare`), actual `effects` and
  selected `review`, including its team and transmission scope;
- caller-approved repository-relative `discovery_roots`, existing `candidates`
  and optional `source_dispositions` with concrete reasons;
- candidate source `path` and raw `sha256`, or an `installed` package filename;
  an optional binding reference has its own `path` and raw `sha256`;
- `coverage` rows with original `criterion`, `part`, binding `obligation` and
  concrete `reason`. Structured criterion identities are `<source-id>:<row-id>`;
  Markdown uses `<source-id>:whole`. A criterion without declared parts has part
  `whole`. All original rows and declared compound parts remain due even when the
  assignment summary omits them. `criterion_links` may trace an assigned summary
  to multiple original criterion identities;
- bounded `drafts` with `kind` (`adapt`, `compose` or `author`), concrete `reason`,
  complete native `document`, definition `mapping` and `coverage`. Adaptation
  identifies exact `base` source bytes. `revision_of` identifies an adaptive
  source whose positive decimal revision will be advanced. Composition supplies
  explicit exact imports and typed ports under the contract below.

Discovery compares package defaults and sources in approved locations. An
adequate unchanged known source is preferred; byte-identical aliases and other
optional files need no separate disposition after adequate reuse is selected.
Before generation, discoverable known sources need a current fit consideration
or concrete limitation. Invalid historical entries remain diagnostics. Source
presence or a caller's adequacy label establishes neither fit nor suitability.
Before fit or generation, read the actual conventional managed family slot even
when it is outside `discovery_roots`. Reuse the inspector's static current, prior
canonical and supported workaround byte classifications without runtime or health
probes. Keep prior-canonical/workaround provenance distinct from local
customization. The coverage plan's `source_authority` retains exact managed
source text, path and raw SHA. Arbitrary same-ID templates or historical bundles
do not become adopted sources. Explicitly adopted custom sources and workflow
rules remain original requirement inputs. Adopted customization obligations
remain due even if their Procedure has not qualified. Preserve them and record a
meaningful existing-envelope textual disposition in
`customization_disposition`; an optional template cannot become policy by being
listed in discovery.

Mechanical fit checks complete declared original-source coverage, actual
producer/evidence items and consuming Decision placements. It checks the family,
entrypoint, effect scope and any explicitly mapped review-route declarations,
including typed field aliases. Unrelated item names establish no review
capability. Provider-specialized and new operations may omit a route-choice
field; preparation preserves the selected review and reports its continuity as
`not-established` for TASK-141. A contradictory mapped choice is incompatible. Exact known reuse preserves its
established structural review contract and original assessment boundaries;
actual selected review execution remains due.
The exact `review` object must agree with `authority.review`, and definition
work effects must remain within `effects` and `authority.effects` (the abstract
`covered-work` effect is resolved by the invocation). Full evidence connections,
review-control continuity, acceptance provenance and post-gate effects remain
TASK-141 obligations. Coverage results explicitly retain
`requires-independent-original-source-assessment`; they are not Judge passage.

`plan-only` reads original sources and approved source locations. It writes no
files, renders no source, invokes no provider or native command, initializes no
repository or workflow and creates no goal/session. Unresolved fit returns
`not-established`. Approved `prepare` requires the existing envelope's
`authority.preparation` with disclosed `roots`, `write_root` and
`native_authoring: true`. These fields express authority already granted; they
supply no additional grant and do not replace `authority.allowed`/`excluded`.
The disclosed preparation effects include creating candidate parent directories
and, when needed, exclusively creating their local self-ignore file. Existing
ignore policy is honored and conflicts are preserved. Preparation performs no
product, investigation or design-document work.

Prepared source and binding are complete ignored bundles under
`<write_root>/.candidates/<binding-id>/`. They are separate from adopted `.local`
bundles and are never resolver admission evidence. Existing ignore/track policy
is checked before definition bytes are written. Formatting uses no-follow
regular-file descriptors. New identities are collision-checked across approved
roots before hashing; changed canonical sources receive an adaptive identity.
Adaptive revisions are positive decimal strings. Exact native identity and raw
source SHA remain separate, and exact source/binding bytes are verified before
atomic retention. Retention and stage directory identities remain bound to held
descriptors; cleanup removes only the owned stage. Verify the published complete
bundle and native tuple before returning success. Publication competition is a
typed conflict, and a cleanup failure remains explicit. Existing identical
candidates are reused without overwriting.
The retained copy makes custom filenames or separately located bindings safe to
handoff without depending on their mutable origins.

New or changed source uses the released native formatter, `format --check`,
`validate`, `vet`, `lint --warnings-as-errors`, `check --warnings-as-errors` and
`preview`, with supported `--` source operands and the disposable/approved source
worktree as process cwd. Native diagnostics and nonzero gate exits remain
failures. Known unchanged reuse preserves original bytes, supported reference
mapping and existing independent checkpoints, including Goal's absence of a
plan Judge. It uses the supported check/preview path and does not acquire new
authoring gates or an extra suitability cycle. Newly prepared sources retain `TASK-141-exact-target-suitability-required`; native checks alone
establish no suitability or activation.

The public source-preparation CLI is
`shared/prepare_adaptive_procedure.py --repository <path> --assignment <json-file-or->`.
A dash reads the ordinary assignment from stdin. Approved `prepare` also takes
`--podway <exact-binary>`; plan-only needs no binary. JSON success is `planned`
with selection/reasons/coverage and `writes: []`, or `prepared` with the original
assignment plus `target.prepared_definition`: exact source/binding paths, binding
ID, native tuple, source SHA, coverage plan, qualification limit and observations.
Its `storage` describes the candidate directory and the already permitted
directory/self-ignore effects.
It reports `adoption: not-performed` and unchanged handler activation. Exit 0
means this bounded operation succeeded; exit 2 reports unresolved authority,
`source-drift`, `native-invalid`, `incompatible`, `not-established`,
`unsupported-runtime`, `runtime-failure`, input/path errors or
`missing-prerequisite`. Native Error v2 codes remain available when the runtime
refuses an operation. Diagnostics are returned in JSON, not mandatory report
files. Python, PyYAML and jsonschema must exist in the selected supported helper
environment; this command installs nothing and assumes no target `.venv`.

## Explicit source-only composition

A `kind: compose` draft retains the ordinary draft's native root `document`,
root definition `mapping`, original-source `coverage` and concrete `reason`.
Its `composition` object imports exact whole definitions or ordinary fragments.
The root can be empty when an imported whole control supplies its placements,
goal assessments and closeout. Final preparation validates a complete binding
and runs the native authoring sequence on one flattened Procedure v2. Generated
source preserves long strings and escaped newline, carriage-return, NEL, line
separator and paragraph separator values using the released native
source grammar; unchanged known reuse retains its original source bytes.

`composition.components` contains objects with these fields:

- `kind`: `fragment` or `whole`; `namespace`: a unique native identifier other
  than `root`. Expanded placement and definition IDs are `<namespace>-<id>` and
  must satisfy the released native identifier contract.
- `source`: exact repository-relative `path` and raw-byte `sha256`, or an exact
  packaged `asset` path relative to Aquarium's assets plus `sha256`. Reads use the
  existing non-symlink, regular-file and containment checks.
- A fragment supplies its ordinary `mapping` slice: `nodes` and optional
  `obligations`. Native roles, effects and capability field aliases belong to
  that slice. Its declared assessor nodes map to Judge roles and select the
  covered original evidence. Grouped conditional coverage retains explicit
  optional branch selectors; exact applicability proof remains due under
  TASK-141. Fragment mappings cannot carry session-goal or closeout claims.
- A whole definition supplies an exact `binding` reference with the same source
  byte SHA, native ID/version and family. Native check/preview verifies its
  actual digest inside the approved ignored preparation stage. Whole controls
  preserve native goal mappings, formal declarations and manual rework targets.
- `parameters` holds actual invocation values matching the definition's declared
  types. Values remain in the ordinary coverage/preparation plan. The reusable
  binding retains only parameter declarations under namespaced keys. Parameters
  are caller inputs; the composer performs no text or command interpolation.
- Optional `fields` maps original placement IDs to native item aliases. The
  composer updates item IDs, same-action conditions, evidence selectors, guard
  endpoints, obligation endpoints and matching capability aliases, including
  implicit logical field identities. Semantic
  operation IDs, operation digests, accepted outcomes, Decision option IDs,
  criteria, prompts, instructions and commands retain their exact values.
- Optional whole `inputs`/`outputs` use the fragment port shape (`type`,
  `required`, `endpoint` with native `node`/`item`); whole `exits` maps names to
  original placements. Optional `public_targets` exposes named original
  placements for external rework. Every component's `entry` is also public.

`composition.entry` identifies a component entry or a root node.
`composition.control` holds explicit `from`/`to` edges. A component source names
`component` and `exit`; a Decision exit also names its `option`. A destination
names its component entry. Root endpoints name `component: root` and `node`.
Each exit/option has one destination. Action exits become `next` transitions;
Decision options receive native `to`/`effect: advance` routes. This does not add
another cursor or executor.

`composition.evidence` connects `from: {component, port}` outputs to
`to: {component, port}` inputs. Each input has one producer. The composer checks
actual native item types and supported value bounds, separately from control
connectivity. Narrower producer ranges and choice/outcome sets may fit a broader
consumer. Check-result operation ID/digest must agree. Unsupported differences
or missing bounds that prevent proof return `not-established`. A required input
needs an unconditional required producer; a required output must declare one.
Conditional presence without a supported proof returns `not-established` with
the affected port location.
Unresolved required inputs stop preparation. Native `evidence_from` selectors
retain their existing scope. Adding a connection preserves an omitted item
selector; an explicit item list receives only missing producer items. Repeated
rows for one producer retain their individual item scope and requiredness.
Wiring uses a compatible applicability row or adds one within the released
eight-row and sixteen-item limits. Required producers must dominate consumers
for each required selector row.
Guards require their own item in an explicitly required selector row;
optional native guard items remain supported. Stronger workflow/suitability
claims remain due under TASK-141.

A fragment's internal rework declarations must match its actual native rework
routes. Each external declaration's `port` is the unresolved `route.to` token
on the declared `from` placement. Component `rework` binds each such token to
`{component, target}`. The target is `entry` or an explicitly exposed
`public_targets` name. Root public targets are declared in
`composition.public_targets`. Undeclared, unresolved or cross-private jumps
reject; native `effect: rework` remains the invalidation authority. Imported
manual-rework declarations retain their original supported scope.

Exact fragment dependencies identify `id`, `version` and source SHA of another
resolved component. Conflicting definition identities reject; identical
semantic aliases may be imported under different namespaces. Composition checks
input bytes again before and during preparation, including binding bytes, and
checks each imported whole native tuple. The resulting source, full binding and
origin provenance are retained together. Origins and mutable libraries are no
longer execution or recovery dependencies after the candidate is intact.
Source-only preparation does not publish an adopted bundle.

`assets/adaptive/reusable/technical-review.fragment.json` retains the selected
technical-review record and faithful finding route. Its correction port must be
bound. `task-goal-control.yaml` and its exact binding provide whole-session
assessment and result delivery with native goal mappings. Its achieved path
checks the current Judge's pass verdict, zero unmet and unverified criteria and
passing applicability before the goal assessment. Declared stopped,
not-achieved and superseded outcomes retain their native mappings. These optional
building blocks impose no complete canonical topology. They establish no proof
that all Task obligations are satisfied. Full family qualification, exact-target
suitability, actual independent work and Master acceptance remain due. These
product templates are within TASK-140's implementation scope; promotion of
actually used local definitions still requires specific preservation consent.

Plan-only composition reads declared sources and reports unresolved contracts. It writes no source, ignore policy or candidate and calls no native
command. Approved preparation uses the existing disclosed `.candidates` writer;
its native source checks apply to every exact flattened instance. Fragment-only
validation and a representative native result cannot establish other parameter
values, runtime execution or installed handler behavior. Failure statuses and
CLI exit semantics remain those of source-only preparation.

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
Selected admission reports its interpreter and missing `jsonschema` or YAML
dependency before native work. Use an available supported Python environment;
the launcher performs no installation. The setup inspector imports adaptive
dependencies only on its explicit selected path, preserving legacy invocations.
TASK-142 establishes runtime readiness before family activation; TASK-145 owns
global/setup guidance. Each uses a
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
uniqueness are implemented together. No automatic Git inclusion, TTL eviction,
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

## Selected admission, retention and recovery

[manage_adaptive_procedure.py](../shared/manage_adaptive_procedure.py) exposes
`inspect`, `retain` and `resume`. Supply the owning `--repository`, every approved
searched `--root`, the invoking `--entrypoint` and applicable `--review-route`.
`inspect` and `retain` also need `--source`; retention needs an approved
`--write-root`. `--podway` selects an available executable explicitly. The CLI
performs native identity, workspace health, source checks and selected-route
checks. It never starts, begins, replaces or advances a session. Current native
state and a different-definition conflict remain visible; even the same
definition requires the Orchestrator to reconcile actual work and authority.
Retention can prepare a successor while preserving that conflict.
Aquarium's source-repository interface catalog, `docs/specs/local-interfaces.md`,
defines both CLIs' flags, result fields, failure details and exit statuses. Target
repositories do not need that development catalog for admission.

Before TASK-141, adaptive admission accepts only exact sources in
[known-sources-v1.json](../assets/adaptive/known-sources-v1.json), with their
supported reference binding. This bounded contract freezes source hashes and
role/capability mappings within mapping version 1. Existing entries remain stable
when unrelated templates or signatures change; necessary mapping changes require
a distinct native revision. It is separate from the existing canonical,
same-ID custom and formal-session contracts. Unknown sources return
`not-established`, never a fabricated qualification. Whole-graph qualification
and suitability remain planned.

The selected setup inspector retains full managed-library diagnostics and
same-family adopted-customization visibility. An alternative needs the existing
envelope's obligation disposition through `--customization-basis` on the launcher
or `--podway-customization-basis` on the inspector. This records an existing
decision; it grants no replacement or scope authority. Optional templates and
historical local bundles contribute no new obligations. Unselected providers
are not probed by this path; the selected review route owns provider readiness.

[adaptive_bundles.py](../shared/adaptive_bundles.py) publishes complete
`procedure.yaml` and canonical `binding.json` together under
`<approved-root>/.local/<bundle-id>/`. It validates regular non-symlink ancestry,
actual target ignore rules and untracked state. Suitable existing ignore policy
is preserved; a new local policy is exclusive and cannot overwrite a conflict.
A short worktree Git-directory lock serializes writers across all supplied roots;
exclusive atomic rename publishes the complete bundle. Interrupted staging is
not adopted. The lock contains no session or progress data.

Resolve by native `(id, version, digest)` readback before `begin` or work. Native
preview verifies the tuple, independently of the source-file SHA-256. Identical
aliases are accepted; an existing same-key binding reuses its original source
bytes. Different same-key bindings are ambiguous and stop. Selected missing,
corrupt, unsafe or unsupported material also stops without regeneration or a
legacy fallback. Unassociated historic damage remains diagnostic, with no claim
that its key was established. An optional bootstrap path cross-checks the result
and cannot replace exact-key lookup. Recovery uses retained source and binding;
mutable origin libraries are not dependencies.
`missing` denotes absence without an associated retained candidate. Missing
files tied to the native key or an empty exact candidate bundle location are
`corrupt`. Preflight rejects that damage before creating a new lock or ignore
policy.
Safe custom names retain their literal path meaning: native source operands use
the supported `--` separator, Git inventory uses literal pathspecs, and ignore
checks use explicit relative paths.

Report native rejection as `native-invalid`, an established contract conflict as
`incompatible`, missing proof as `not-established`, and native execution failure
as `runtime-failure`. Preserve native Error v2 codes, including writer mismatch.
A nonzero check exit fails even when its typed diagnostic says `valid: true`.
These local helpers establish neither real independent agent execution nor
installed handler behavior.

## Amendment owners and reserved delivery

| Task | Exact existing owner/rule to amend when implemented |
| --- | --- |
| TASK-138 | Implemented: podway-integration and tool-catalog selected/library readiness distinction; dev-setup inspect_tools selected path; atomic writer/resolver and dependency-reporting launcher with lazy imports |
| TASK-139 | Implemented: shared adaptive selection/preparation and source authority; existing plan/assignment requirement coverage and plan-only boundaries |
| TASK-140 | Implemented: shared composition through existing preparation, namespaces, typed ports, self-contained flattening and reusable review/whole-control assets; preserve semantic operation IDs/digests and fragment/session control distinction |
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
qualification and runtime claims remain with TASK-141 and activated families.
Tests of fabricated records establish rejection behavior only.
