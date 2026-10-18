# Adaptive Procedure contracts

## Status and ownership

TASK-137 implements the closed Aquarium definition formats, canonical JSON
identity helper and necessary declaration signatures described here. TASK-138
implements selected known-source admission, atomic local retention and exact-key
recovery. TASK-139 implements fit selection and approved source-only preparation
through an ordinary Worker assignment. TASK-140 implements explicit whole/fragment
composition through that preparation path. TASK-141 implements guarded structural
qualification and exact ordinary pre-start suitability with bootstrap import.
Task, Goal, Validation, Design and Diagnosis now use [adaptive execution](adaptive-execution.md), including shared explicitly consented atomic supersede. Cross-family recovery and consent-based preservation are implemented. Existing ordinary v2 reports, canonical/custom sources and immutable formal v1 sessions retain their supported contracts.

The source repository's `TESTING.md#adaptive-acceptance-scenarios` owns durable
acceptance scenarios. Its roadmap owns Task identity and lifecycle, and tracks
integrated verification and actual acceptance. This reference owns the shared
adaptive definition contract. Its signatures are reference implementations; a new operation can establish the same guarantee
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
Pre-start preparation and adoption verify the exact raw source pins. In-session
re-entry preserves those original provenance values while comparing the complete
currently extracted criteria and parts with the approved coverage basis. Changes
outside that basis do not refresh the original report target. Relevant criterion,
source identity, adopted status, plan, review, authority and execution-definition
changes still require their affected checks; see
[adaptive execution](adaptive-execution.md#mapped-handoff-and-recovery).

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

Before adoption, qualification compares this managed-source authority with the
prepared coverage plan again, including at publication. A changed managed slot
requires renewed reconciliation and affected assessment. An intact admitted
session resumes from its self-contained bundle; later origin-library or managed
template changes do not replace its adopted obligations.

Mechanical fit checks complete declared original-source coverage, actual
producer/evidence items and consuming Decision placements. It checks the family,
entrypoint, effect scope and any explicitly mapped review-route declarations,
including typed field aliases. Unrelated item names establish no review
capability. Provider-specialized and new operations may omit a route-choice
field; preparation preserves the selected review and reports its continuity as
`not-established` until shared qualification. A contradictory mapped choice is incompatible. Exact known reuse preserves its
established structural review contract and original assessment boundaries;
actual selected review execution remains due.
The exact `review` object must agree with `authority.review`, and definition
work effects must remain within `effects` and `authority.effects` (the abstract
`covered-work` effect is resolved by the invocation). Full evidence connections,
review-control continuity, acceptance provenance and post-gate effects remain
shared qualification obligations. Coverage results explicitly retain
`requires-independent-original-source-assessment`; they are not Judge passage.

The ordinary assignment may carry `target.qualification_context`. Only the
following input keys are supported. They describe original work and static
definitions and grant no effects:

| Key | Value and applicable use |
| --- | --- |
| `operation_contracts` | Operation-definition digest to static semantic contract. New or changed definitions retain these exact entries in binding `semantic_contracts`. |
| `signatures` | Signature ID to capability definition, retained in binding `capability_definitions`. Established meanings cannot be overridden. |
| `goal_kind` | Actual Goal scope: `member-task`, `pre-validation-remediation` or `epic-closeout`. Supply it when that scope determines delegated versus user acceptance. |
| `workflow_owner` | Actual Validation owner: `epic-handler` or `epic-validator`. Supply it when continuing Epic validation versus cold validation determines acceptance. |
| `due_capabilities` | Guarantee-kind names required by the actual approved workflow. Supply every conditionally due capability; omission cannot waive an original obligation. Unused implementation, refinement or Deslop is not required for documentation-only work. |
| `required_endpoints` | `{node, item}` producer endpoints required by the actual work even when their native items are optional. Supply them when original coverage requires their presence. |
| `criterion_capacity` | Exact-basis upper bound used by structural checking. Public suitability requires the independent report's `applicability.criterion_capacity` proof (`value`, original `basis`, `evidence`); a caller number alone establishes nothing. |
| `review_required` | Boolean identifying a due selected technical review. It cannot waive the original selected route or team; Design/Diagnosis qualification enforces a selected review independently. |
| `expected_outcome` | Original intended `achieved`, `not_achieved` or `superseded` outcome; defaults to `achieved`. Stopped work must not be represented as achieved. |

Handlers carry applicable values into preparation, qualification and recovery
alongside the unchanged original sources and authority. These inputs establish
neither actual agent execution nor suitability passage. Live ordinals, grants
and handles remain ordinary execution records rather than static context.

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
A dash reads the ordinary assignment from stdin. Design `--podway-opt-out` (API `opt_out=True`) and non-Git `new-project` return exit 0 with `podway-inapplicable` before source selection/rendering or native imports. Repository inputs use `expanduser().resolve()` before the Git-ancestor check. An explicit flag with a missing or non-Design entrypoint fails with `invalid-arguments` JSON and exit 2 before native/source work; other-family skill-level opt-out remains its existing separate contract. Approved native `prepare` also takes
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
claims remain due through shared qualification and exact suitability.

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
the shared qualifier checks binding item references against the separate native source.

The helper currently requires Python and `jsonschema` from a supported
environment. This repository supplies them through its development requirements;
arbitrary target repositories cannot assume this checkout's `.venv` exists.
Selected admission reports its interpreter and missing `jsonschema` or YAML
dependency before native work. Use an available supported Python environment;
the launcher performs no installation. The setup inspector imports adaptive
dependencies only on its explicit selected path, preserving legacy invocations.
All five activated families use selected runtime readiness before work. Setup
selects an available compatible installed environment and reports missing
prerequisites; target repositories need no development checkout. This contract
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
input is a caller-established exact-basis upper bound. Public suitability uses an
actual current ordinary Judge report's `applicability.criterion_capacity`, with
`value`, the complete original `basis` and readable `evidence`; a bare invocation
number supplies no proof. Established reuse can carry a prior report's capacity
proof only while its original criterion basis equals the current basis. A bound
below that capacity is incompatible. A missing
capacity proof can be included in the same exact suitability assessment. An
operation digest supplies no capacity proof; unrelated bounded integers retain
their own contracts.

Recognized guarantees have independent minimum declarations. Custom signatures
retain the required original report, applicable negative assessment/check
outcomes, mandatory gap-count fields and approval alternatives. Their own
labels or narrowed field specifications cannot weaken those minima. New
assessment-like guarantees retain the common report, verdict, gap-count and
applicability floor. Necessary consumed fields remain in the analysis even when
a custom signature omits their declarations. Exact
custom operation identities and typed aliases remain supported; review records
may stay conditional when the relevant path proves their presence. Unrelated
pass-only native checks retain their existing contract.

Each signature names its structural guarantee. The shared qualifier checks its
producer/item/evidence/Decision connections, native guards and relevant forward
effects. Declaration matching alone does not establish those relationships. Actual
independent execution comes from the ordinary assignment and native result
observations; signatures and digests authenticate no agent.

The qualifier checks acceptance provenance using the actual `goal-kind` for Goals
and `workflow-owner` for Validation, exact `acceptance-source` values and consuming
guards. Every user-owned path must support and require `user`; delegated Goal
paths exclude final Epic closeout and stopped outcomes, and delegated Validation
requires continuing `epic-handler` ownership. Cold validation, stopped Validation and stopped Goals require actual user
acceptance. Discriminator
semantics come from an established operation, its executed source and selected
evidence under current ordinary context. An unrelated same-named choice cannot
supply delegation. Specialized Procedures need only their applicable branches.

All backed families retain `goal_tracking: true`. Native
`assessment.target: session_goal` mappings own achievement. Terminal names,
completed lifecycle or binding labels cannot establish success. Every feasible
achieved selection needs the current final Judge's actual achieved outcome,
pass verdict, zero mandatory unmet/unverified criteria and applicability through
direct guards or an established equivalent chain. A shared closeout terminal
may follow achieved, not-achieved or superseded outcomes.

Every relevant forward work/content change needs a later covering assessment.
Exact application approval likewise stays tied to current proposal/target bytes.
Static re-entry checks follow native target-and-later invalidation for declared
and allowed manual rework. A downstream target may preserve an earlier gate;
product effects made before re-entry therefore require the corresponding renewed
assessment or approval on successful continuation. Reapplying an exactly approved
application retains its own approval/result contract. A renewal covers every
applicable original obligation and selected producer; an unrelated assessor or
partial replacement cannot clear other changed scopes. Inactive conditional
alternatives create no additional coverage obligation. Recognized bookkeeping,
actual acceptance, exact lifecycle-only deltas, independently verified evidence
projection and authorized commit/no-commit handoffs keep existing exemptions.
Declared product effects take precedence over custom non-work labels. Existing
reference bindings have coarse effect declarations; established individual
operation meanings retain their original contracts. Unknown effects receive no
bookkeeping exemption and remain not-established. A definite violation remains
incompatible even when other paths contain unknown effects.

Qualification reports native-invalid, incompatible, not-established and runtime
failure separately. Native validity, graph guarantees, exact suitability and
actual runtime applicability remain separate claims. Predicate/dataflow analysis
must handle infeasible guarded paths and unknowns without exhaustive-path
assumptions. An unresolved proof reports its property and location; it neither
proves safety nor declares every noncanonical structure invalid.

Custom static operation contracts remain part of the exact binding and suitability
target. A non-work Worker claim without established semantics is unknown. Privileged
correction, user-direction and faithful-relay declarations need their actual
verifier, user-evidence or typed original-evidence connection; a boolean or map
alone supplies no exemption. Discriminator and output-scope maps require an
established operation, its verified derivation or exact independent semantic
evidence in the existing ordinary suitability report. An unestablished map is
removed and reports `not-established`; it cannot grant delegation or exempt
product work from the plan-handoff frontier. Harmless custom Orchestrator evidence and result
delivery remain supported. Composition retains a bounded `derivation` for changed
established operations: the original individual definition plus only its native
reference and item rewrites. Qualification checks its original definition hash,
unchanged operation meaning and exact rewritten body without reading origin
libraries. The checks apply to individual operations and establish no agent authentication.

A genuinely new operation can use the same due report's optional
`applicability.operation_contracts` map. Each key is the exact canonical
operation-definition digest; its value contains `contract` (the exact object in
binding `semantic_contracts`) and readable, nonempty `evidence` supporting that
meaning. Qualification first validates the report against the full current
bundle and original basis, then consumes this proof separately from declaration
maps. Typed choice domains and role/effect obligations still apply; product
effects remain product effects. The released operations are reference
implementations, not a complete operation allowlist.

Before that report exists, conditional analysis may establish that only this
semantic proof or exact criterion-capacity proof remains due. It returns
`assessment-required` with overall `not-established` and no execution frontier;
independent structural violations still stop. The same Judge can assess both
proofs. No extra report or cycle is required. An unchanged retained definition
can reuse the exact prior report's semantic proof with current fit, without
claiming a new assessment. Running recovery uses the current applicable report;
the handoff consumer preserves its proven frontier rather than trusting a raw
binding or invocation map. The existing affected reassessment route carries
`assessment_requirements`: exact retained semantic contracts and any bounded
criterion-count fields. The already due ordinary Judge uses these inputs for
the current target and includes any necessary proof in that same report. The
context supplies no proof, additional Judge or new pre-start bootstrap. These
declarations establish no actual agent execution.

Task, Goal and Validation preserve their supported selected review route;
`not-applicable` cannot waive a due review. A review operation may retain
same-operation recovery and authorized route change internally through its
self-contained `review_recovery` contract, or compose the existing direction
operations. A custom internal contract belongs to the actual mapped review-control
and routing operation with its necessary native evidence/check fields. An unrelated
note cannot supply recovery by adding that list. Applicable missing capabilities are not-established. Explicit
exclusions belong to the original approved invocation scope, not an authoring
shortcut. Custom ordinal checks receive no completion or prior-ordinal implication
from a capability label; actual guards can establish the necessary relationship.
Task finalization requires its actual approved user route; an additional delegated
option alone supplies no acceptance.

Context discriminators use the current family vocabulary and the actual selected
source domain. The original invocation's `expected_outcome` is `achieved`, `not_achieved` or
`superseded`. It defaults to `achieved` and remains in the exact original basis. A due achieved result needs a feasible achieved
continuation. Stopped/non-achieved paths remain available without representing
success. Integer domains include every consumed `required_when` threshold.
Native Action completion enforces accepted check outcomes only for items required
now. Optional recorded nonaccepted outcomes remain possible; absent guard evidence
remains unevaluable and cannot select a route.

## Suitability, replacement and preservation

Known reuse requires unchanged bytes, an established structural contract, a
supported binding and current fit. Unsupported bindings and materially changed
definitions require qualification. Adequate known reuse keeps current assessment
boundaries. Include fit
in an existing plan assessment when present; a Goal without a plan Judge gains
no fictitious report or extra cycle. New/changed/composed definitions require
exact pre-start independent suitability against complete bundle/native digest
and original requirement/plan basis. One compatible Task plan assessment may
cover both scopes. Bootstrap imports the real pre-session report and timing for new or changed
sources. An intact already-qualified adaptive bundle can instead use actual prior
ordinary definition evidence, exact retained bytes and native identity, current
structural proof and original-source fit. Its bootstrap records
`established-reuse` timing with an ordinary selection checkpoint, preserving the
normal first-due Judge. Prior definition evidence is never a current assessment
or product pass. Material in-session basis changes require affected current
assessment; consumed ordinals, remaining grants and same-operation handles alone
do not create a new pre-start cycle.

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
uniqueness are implemented together. Adopted bundles have no automatic TTL or
size-based eviction. No automatic Git inclusion, central session map or origin
lookup is required for resume. Clean only invocation-owned unadopted drafts under
their disclosed cleanup authority. Local retention guarantees neither backup,
portability nor Git persistence. Losing a bundle may prevent exact continuation
until its original definition is recovered. Do not claim survival of destructive
native reset/removal without its verified contract; disclose any recovery-definition
loss before a separately requested destructive action.

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
success never transfers to them. The executable grouped offer and exact
post-finalization application interface is owned by
[Procedure promotion](procedure-promotion.md).

## Selected admission, retention and recovery

[manage_adaptive_procedure.py](../shared/manage_adaptive_procedure.py) exposes
`inspect`, `retain`, `resume` and mapped `context`. Supply the owning `--repository`, every approved
searched `--root` on the native path, the invoking `--entrypoint` and applicable `--review-route`. Design `--podway-opt-out` and non-Git `new-project` instead return exit 0 / `podway-inapplicable` before native imports, discovery or source work, without roots, source, qualification, binary or session. Missing or unsupported entrypoints with the Design-only flag fail as `invalid-arguments` JSON / exit 2. Native arguments remain required after that early branch.
`inspect` and `retain` also need `--source`; retention needs an approved
`--write-root`. `--podway` selects an available executable explicitly. The CLI
performs native identity, workspace health, source checks and selected-route
checks. These admission/context actions never start, begin, replace or advance a session. The separate `transition-plan`, `transition` and `transition-recover` actions use the [explicitly consented atomic transition contract](adaptive-execution.md#consented-atomic-supersede), with exact ordinary checkpoint, successor qualification and actual user consent inputs. Current native
state and a different-definition conflict remain visible; even the same
definition requires the Orchestrator to reconcile actual work and authority.
Retention can prepare a successor while preserving that conflict. Native inspection/resume success returns `ready`; retention returns `retained`. Mapped `context` exits 0 for `prepared-resolved`, `dispatch-ready`, `primary-owned`, `attachment-required`, `stop-before-work`, `terminal-resolved`, `finalization-resolved`, and Design/Diagnosis `approval-required` / `reapproval-required`. Both approval statuses return no dispatch and preserve actual exact-diff/target currency. Native context requires its existing session and exact ordinary qualification; the inapplicable branch does not. Other failures retain distinct status/message/details and exit 2; argparse usage errors use exit 2 and stderr usage text.
Aquarium's source-repository interface catalog, `docs/specs/local-interfaces.md`,
defines both CLIs' flags, result fields, failure details and exit statuses. Target
repositories do not need that development catalog for admission.

Unchanged known reuse accepts exact sources in
[known-sources-v1.json](../assets/adaptive/known-sources-v1.json), with their
supported reference binding. This bounded contract freezes source hashes and
role/capability mappings within mapping version 1. Existing entries remain stable
when unrelated templates or signatures change; necessary mapping changes require
a distinct native revision. It is separate from the existing canonical,
same-ID custom and formal-session contracts. Changed/new sources use the exact
qualification and independent suitability path below. Missing proof remains `not-established`. All seven entrypoints use the mapped consumer defined in [adaptive execution](adaptive-execution.md).

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
When the current ordinary qualification discloses `authority.preparation.roots`,
selected admission, publication, resume and supersede preparation/execution must
include every disclosed root in their exact-key search before replacement. Read-only recovery requires no write grant. Existing
direct or historical sessions without that disclosure retain their contracts;
undisclosed roots remain the caller's responsibility.

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

## Implementation owners

| Task | Implemented owner and retained boundary |
| --- | --- |
| TASK-138 | Implemented: podway-integration and tool-catalog selected/library readiness distinction; dev-setup inspect_tools selected path; atomic writer/resolver and dependency-reporting launcher with lazy imports |
| TASK-139 | Implemented: shared adaptive selection/preparation and source authority; existing plan/assignment requirement coverage and plan-only boundaries |
| TASK-140 | Implemented: shared composition through existing preparation, namespaces, typed ports, self-contained flattening and reusable review/whole-control assets; preserve semantic operation IDs/digests and fragment/session control distinction |
| TASK-141 | Implemented: guarded shared structural qualification, exact ordinary suitability/bootstrap and retained-bundle admission/reassessment; preserve canonical/custom/formal defaults until family activation |
| TASK-142 | Implemented: Task/Goal/Validation selection, public adaptive admission/context forwarding, mapped due phase and handoff consumers, self-contained prepared/running recovery and original acceptance/finalization boundaries |
| TASK-143 | Implemented: new-feature/new-project/refactor Design consumers, mapped upstream leaves, QA owner routing, exact application currency and prepared/running/non-Git/opt-out recovery |
| TASK-144 | Implemented: war-room and design-diagnosis adaptive diagnosis; podway-integration and epic-handler successful-terminal-only replacement wording; task-orchestration, epic-orchestration, validation-orchestration and design-diagnosis-orchestration continuation rules for shared consented atomic supersede; preserve task-handler's prohibition on replacing a session merely to recover reports |
| TASK-145 | Implemented: exact whole/fragment preservation offer and post-finalization consented application, separate task-commit handoff, setup/source-role guidance, cross-family recovery controls and seven-entrypoint guest driver/fixtures; installed verification methods belong to TASK-146 |
| TASK-146 | Implemented: committed-candidate verification methods and canonical document settlement; actual observations remain candidate-bound evidence, with original correction owners and actual Master acceptance preserved |

Positive fixtures must include all five canonical declarations, valid namespaced
typed aliases and genuinely different work/evidence/Decision structures. Negative
fixtures target missing required types/operations, parent-goal assessment inside
ordinary fragments, violated evidence or authority. Unknown contracts produce
not-established. ADAPT-25/26 are definition/signature controls here; whole-graph
qualification is covered by the separate shared analyzer; actual execution and
installed claims remain with activated families.
Tests of fabricated records establish rejection behavior only.

## Guarded structural qualification and exact suitability

`adaptive_qualification.qualify` analyzes the exact natively checked source and
binding. Native session-goal mappings determine achievement. Every feasible
achieved continuation needs a current final Judge's achieved outcome, pass
verdict, zero mandatory unmet/unverified counts and applicability. The analyzer
retains correlations across conditional branches and overlapping selections in a
shared predicate graph; it does not enumerate execution paths. Resource
exhaustion preserves already proven incompatibility and reports the current
property and location as not-established. It uses native rework invalidation rather
than persisting another freshness history.

The [released evaluator](https://github.com/irootkernel/podway/blob/fa29dba929777b020377bc9803cb0a3954d219b1/crates/podway-core/src/procedure_v2/items.rs)
makes absent guard evidence unevaluable, so that option
cannot be selected. A recorded Confirm is true; false is not a recorded Confirm
value. Text bounds and emptiness use trimmed Unicode character counts. The analyzer
treats the released evaluator's unevaluable operator/kind pairs as infeasible, including
`equals`/`not_equals` on Text, List or Artifact, and `empty`/`non_empty` on Artifact.
Unestablished proof semantics remain unknown. Optional producer rows can supply
grouped conditional evidence when the producer and selected item actually exist on
the relevant path. Required original endpoints must reach their assessor and outgoing
semantic Decision; a generic bookkeeping node cannot relay evidence by label.

The versioned `operation-contracts-v1.json` describes bounded effects and faithful
projections of individual existing operations. It supplies neither whole-graph
approval nor agent authentication. Unknown effects get no bookkeeping exemption
and remain `not-established`; declared unassessed product changes are incompatible.
Changed approved content needs renewed exact approval and current application
verification. Confirmation preserves finite whole-set eligible corrections under
their existing effect grant. General review remediation needs its current scope;
same-operation retrieval and ordinary declared goal/evidence rework retain their
existing contracts and consume no invented review ordinal.

A binding may include closed optional `semantic_contracts` and
`capability_definitions` maps. These contain static operation definitions, never
invocation requirements, actual results, grants or acceptance. Semantic contracts
are keyed by the exact canonical native definition-body SHA-256, separate from
the native Procedure digest. Composition rewrites their physical item references
and materializes the resulting keys. Structured provenance uses `native_version`
under the closed binding schema. Established same-operation/signature meaning
cannot be overwritten. The existing bundle hash binds these maps, so retained
custom definitions resume without mutable origin libraries. Old known bindings
and their first due checkpoints remain unchanged.

For changed/new candidates, `prepare_adaptive_procedure.py --bootstrap` inserts
an initial report-recording Action and applicability Decision before original
work. Plan-only stays read-only; unchanged known reuse keeps its original bytes.
The prefix records actual ordinary pre-start Judge evidence, the exact target
reference and typed phase passage. The target contains the candidate bundle ID,
native tuple/source hash, complete original requirements and compound parts,
coverage plan and approved static plan/review/effect basis. Live consumed grants,
agent handles and ordinary attempt progress are reconciled separately.

`qualify_adaptive_procedure.py` takes `--repository`, `--assignment <file-or->`
and `--podway <exact-binary>`. `--assessment <file>` supplies the actual ordinary
`aquarium.judge-assessment/v2`; no new receipt schema or universal report file is
required by the API. `--combined-task-plan` allows one genuinely compatible due
Task plan assessment to cover both exact scopes. A nonfinal `checkpoint_result`
pass can preserve truthful global future unmet/unverified rows and product gaps;
due scoped gaps still block. All original rows and compound parts remain covered.
Actual ordinary `state` rows and supported `status` rendering are accepted;
duplicate or contradictory rows fail. Legitimate not-applicable rows retain
current reason and evidence. A global pass alone remains an all-met claim.

Without an actual current assessment, the helper returns `assessment-required`
and an ordinary report-only Judge assignment with truthful pre-session context
(exit 3). Successful known/changed qualification returns exit 0; typed input,
native-invalid, incompatible, not-established, stale-target and runtime failures
return JSON with exit 2. Native codes/details remain available. `--retain` uses the
current disclosed preparation grant and the existing atomic ignored writer; it
creates no session or product artifact. Read-only qualification performs no
provider dispatch, goal/session mutation, setup or installation.
The CLI renders retained source as its SHA-256 and byte size; the exact source
bytes remain in the local bundle used for recovery.

Bootstrap import returns the actual ordinary report as artifact evidence and
separate typed recording values. Its dictionary is not a native ArtifactValue.
The activated handler attaches the actual returned delivery or an authorized
projection through the supported native attachment contract; it does not invent
a location, require a private transcript or create a mandatory universal report.
The retained binding contains no runtime report or target values.

Shared selected-source/retention/recovery APIs accept the original prepared
ordinary assignment and actual assessment as `qualification` context. They bind
the actual selected route to that authority, verify exact retained bytes/native
tuple and recheck current original basis before work. A running session with a
missing delivery first retrieves that same operation. A changed target/basis
returns `reassessment-required` with an existing affected planning/Judge route or
precise `missing-topology`; it never dispatches a new call labeled pre-start.
Initial bootstrap rework can re-import an existing current pre-start report.
Adequate unchanged adaptive reuse instead records prior definition evidence and
current fit with `established-reuse` timing, preserving normal first-due
assessments. Its ordinary selection checkpoint distinguishes those claims from
a new Judge result. Unexpected running-session replacement uses the [separately consented native atomic transition](adaptive-execution.md#consented-atomic-supersede).
The legacy launcher/setup selected-known path remains available under its
original contract. Task, Goal, Validation, Design and Diagnosis use the mapped execution consumer.
