# ADAPT: Goal-adaptive Procedure orchestration

## Ownership and implementation boundary

Consumer: [EPIC-026](../roadmap/README.md#epic-026-adapt-goal-adaptive-procedure-orchestration), including TASK-137 through TASK-146. The roadmap alone owns IDs, task order, dependencies and lifecycle. This dossier owns the adopted implementation scope, decisions and acceptance requirements until the Epic's closeout.

Planning baseline: `4840434b80da08e8f18302d80515a880947ecca8`, after the source closeout of EPIC-024 and EPIC-025. Recheck their canonical outcomes and intervening changes before implementation. Their completion does not establish installed functionality for a later candidate. Preserve improvements made after this baseline rather than restoring earlier behavior to match this plan.

Registration changes documentation only. Every interface, path and behavior introduced below is planned, not installed or implemented by this registration. Existing skills, managed sources and admitted sessions retain their current contracts until the corresponding implementation and authorized update. Registration grants no implementation, provider invocation, session mutation, installation, staging, commit, push or release authority.

## Goal and scope

Each supported handler selects a Procedure that fits the actual work, reuses a suitable existing definition, or authors and composes a definition when needed. It verifies the result against original requirements and applicable workflow obligations before starting a new Podway session. Actual work uses ordinary Workers, an independent report-only Judge and the Orchestrator's permitted Decisions. Later sessions can reuse whole definitions or useful fragments, but never inherit another task's pass or authority.

All seven entrypoints are in scope: `task-handler`, `epic-handler`, `epic-validator`, `new-feature`, `new-project`, `refactor` and `war-room`. Edit Aquarium only. Use the supported released Podway Procedure v2 contract; Podway optimization, new graph capabilities and continuation generations are not dependencies.

The implementation includes selection, authoring, composition, selected-source admission, semantic obligation checks, native execution handoffs, definition retention, recovery, user-approved Git promotion and observed verification. It does not add a general workflow executor, daemon, scheduler, account service, cross-repository catalog, automatic learning/ranking system, role authentication service or second progress database. It does not modify Podway's schema, add execution hooks, alter an active snapshot or create parallel outer cursors.

The design favors adequate existing Procedures over unnecessary generation. Successful adaptation must change the work structure when that helps the goal; requiring every canonical node with repeated not-applicable records does not satisfy this Epic. Shorter graphs do not justify dropping requirements, required evidence or authorization.

## Decisions approved by Master

| Decision | Required behavior |
| --- | --- |
| Automatic selection and adoption | The approved execution envelope includes bounded Procedure selection, authoring, composition, validation, local retention and adoption. Do not ask for approval of each generated definition inside that envelope. |
| Goal and authority preservation | Procedure adoption does not change requirements, selected technical review, transmission scope, effect authority, exact-diff approval, acceptance or commit grants. Obtain the applicable decision when those change. |
| Local retention | Retain adopted definitions and the minimum binding information locally for recovery and future selection. Do not automatically track or commit them. |
| Git promotion | After actual use supports both successful operation and future reuse value, ask whether to keep the whole Procedure or useful fragment in the repository's reusable library. Broad file-editing or commit authority does not replace this specific consent. |
| Promotion timing | Normally present candidates together at the relevant Task or Epic closeout, with purpose, evidence limits, proposed paths and exact definition changes. Do not interrupt routine work with repeated preservation questions. |
| Declined promotion | Make no tracked library change. Declining Git promotion does not request deletion of retained local recovery material. |
| Changed reusable definition | Parameterizing or extracting the original creates a changed candidate. Revalidate it and distinguish source execution evidence from validation of the edited definition. Never label it runtime-tested solely because its source worked. |
| Unexpected active-session replacement | Ask before settling and replacing an in-progress session because the required topology is absent. Disclose current state, missing topology, retained history and results, pending native work and the supported transition. |
| Routine continuation | Declared rework, same-operation result recovery, selection for a not-yet-started Goal and already approved terminal-successor transitions need no extra question. |
| Writes and publication | User consent to keep a definition permits only the disclosed library change. Staging and commit still require their applicable grants; push, publication and release remain separate. |

These decisions resolve the earlier operating-policy questions. Implementation may choose private function names and data structures, but must not reopen or weaken these decisions without a material new conflict.

## Current contracts to preserve

| Concern | Existing authority and preservation requirement |
| --- | --- |
| Ordinary roles and reports | [Ordinary native orchestration](../../plugins/aquarium/references/ordinary-agent-orchestration.md): reuse assignment, worker-handoff, judge-assessment and orchestration-checkpoint v2; preserve grouped assessments, original criteria, current applicability and the optional helper. |
| Review strategy | [Review strategies](../../plugins/aquarium/references/review-strategy-contract.md): recommend from scope, difficulty, impact and uncertainty; preserve the user-selected route and actual topology. |
| Reviewer responsibilities | [Independent Review](../../plugins/aquarium/skills/independent-review/SKILL.md) and [Herdr Review](../../plugins/aquarium/skills/herdr-review/SKILL.md): keep expected base/UI participants and child results. One team remains one operation and one completed ordinal. Herdr main-reviewer delegation does not authorize ordinary Judge delegation. |
| Findings and corrections | [Finding disposition](../../plugins/aquarium/references/finding-disposition.md) and [review intent](../../plugins/aquarium/references/review-intent-contract.md): preserve valid defects while rejecting goal-destroying remedies, original rows, correction responses, local settlement and consumed authority. |
| Delivery and retrieval | [Result handoff](../../plugins/aquarium/references/review-result-handoff.md): use complete native results and recipient reads; recover the same operation before repeating an assessment. Add no universal report file, acknowledgement turn, synthetic receipt or hash prerequisite. |
| Procedure lifecycle | [Podway integration](../../plugins/aquarium/references/podway-integration.md): preserve native admission, immutable snapshots, current fences, outcome recovery, archival, terminal finalization and actual authority. |
| Design and diagnosis | [Design/diagnosis orchestration](../../plugins/aquarium/references/design-diagnosis-orchestration.md) and [Ouroboros integration](../../plugins/aquarium/references/ouroboros-integration.md): retain upstream leaf QA, raw negative outcomes, exact document approval, non-implementation and non-Git boundaries. |
| Source and evidence ownership | [Execution SOT](../../plugins/aquarium/references/epic-execution-sot.md) and [evidence residency](../../plugins/aquarium/references/evidence-residency.md): roadmap and canonical requirements remain authoritative; definition retention is separate from promoting runtime evidence. |
| Verification | [TESTING.md](../../TESTING.md), [VM methods](../../tests/vm/README.md) and [VM driver](../../tests/vm/run_acceptance.py): preserve exact-candidate verification and distinct source, fixture, native, installed and user acceptance claims. |

Do not impose new provider allowlists, arbitrary quotas, mandatory private telemetry, all-role snapshots or a new evidence collection service. Preserve formal v1 sessions and their genuine receipt requirements without applying them to ordinary v2 work.

## 1. Requirement basis and workflow contracts

Resolve the execution basis from the actual user objective, approved scope, canonical requirements, repository guidance and existing handler obligations. Generated text cannot reduce that basis. Reconcile original sources independently of the planner's selected criterion list, including omitted and compound criteria. Derive applicable obligations from the work and its authority, not from the graph the generator happens to propose.

Use five workflow families with seven entrypoint overlays:

| Family | Entrypoints | Required meaning |
| --- | --- | --- |
| Task | `task-handler` | Deliver the named Task through its applicable work, checks, technical review, independent assessment, actual acceptance and closeout. Preserve separately invoked Task-phase contracts. |
| Goal | `epic-handler` | Deliver member, pre-validation correction and closeout Goals under their distinct grants. Keep the roadmap DAG outside the Procedure and preserve final integration and user acceptance. Do not impose the Task phase workflow on Epic work. |
| Validation | `epic-validator`, internal Epic validation | Audit original criteria and integration; cold validation starts a fresh Judge, while internal validation preserves the logical Epic Judge when supported. Preserve correction ownership and the appropriate acceptance source. |
| Design | `new-feature`, `new-project`, `refactor` | Produce the entrypoint's required design artifacts and actionable work definitions. Preserve upstream QA, exact-diff approval and document delivery. Do not implement product changes. |
| Diagnosis | `war-room` | Reproduce safely, test hypotheses and deliver an approved Task/Epic proposal, incomplete diagnosis or supported no-work outcome. Unexplained symptoms are incomplete, not fixed or no-work. |

Each due obligation maps to a work producer, readable input, evidence producer, assessor where required, consuming Decision and applicable effect/acceptance boundary. Keep future obligations visible without demanding unfinished Epic members prematurely. A phase may pass while the overall goal still has future gaps. Final success requires all currently applicable mandatory obligations and actual finalization.

Planning references reuse canonical IDs or source path/section references. Do not create a second requirements database or modify canonical criteria to match a generated plan.

### Native goal outcomes and acceptance

All Podway-backed families retain `goal_tracking: true`. Derive goal-assessment placements and option-to-outcome mappings from the native `assessment.target: session_goal` declarations. A terminal ID, a binding label, or session lifecycle `completed` alone does not establish goal achievement. The same closeout node may legitimately follow `achieved`, `not_achieved` or `superseded`.

Accepted success requires the latest valid native goal assessment to select an `achieved`-mapped option supported by current final-Judge evidence and the applicable family acceptance and finalization conditions. Every feasible `achieved` selection must require the final assessment's actual achieved outcome, pass verdict, zero mandatory unmet/unverified criteria and applicable evidence, directly or through a proven equivalent chain of guarded Decisions. Descriptive terminal labels cannot replace or weaken those conditions. Non-achieved, superseded and approved incomplete diagnostic deliveries remain honest outcomes; they are not product completion or defect repair.

### Task obligations and conditional capabilities

For newly admitted adaptive Tasks, preserve the approved plan, independent assessment of due delivery, required checks, affected documentation/roadmap/release-note postconditions, selected technical review, final Judge, actual user acceptance and the existing `task-close`/authorized `task-commit` boundary. Work grouping and phase order may vary while their actual prerequisites and evidence relationships remain valid.

Derive capability applicability from the real task-owned changes and repository authority before constructing the graph. Code or test changes retain due refinement, including required Deslop cleanup and verification of its delta. Documentation-only work does not require an unused implementation/refinement step or Deslop installation unless an independent repository rule requires it. Document capability is due where canonical documentation or its required postconditions are affected; a coherent documentation delivery may own both writing and verification. The generator cannot omit a capability and then use that omission to declare its postcondition inapplicable.

TASK-142 must replace the fixed seven-phase loading and unconditional refinement discovery on the adaptive path in `task-handler` and `task-orchestration`, while preserving direct phase-skill invocations and admitted legacy sessions. Map plan-handoff's approved-plan attachment, no-work stop and resume boundaries through the admitted capability/evidence mapping, not literal `implement` or `record-plan` names. Keep any repository-mandated prerequisite that is genuinely due. This does not impose Task phases on Epic Goals.

## 2. Execution definition and binding contract

A local adaptive bundle contains one complete native `procedure.yaml` and an Aquarium-only `binding.json`. A binding describes executable structure and its mapping, not current progress. Session, attempt, native handles, actual authority, result receipt, finding state and consumed grants remain in existing ordinary records and Podway.

TASK-137 materializes the following reserved contracts with closed parsing and fixtures. These are Aquarium definition formats, not additions to Podway or replacements for ordinary v2 reports:

| Definition | Required content |
| --- | --- |
| `aquarium.procedure-binding/v1` | Schema; one workflow family and its supported entrypoint set; compatibility contract version; native Procedure ID, version and canonical digest; exact source-file SHA-256; node/capability and declared parameter maps; obligation-to-evidence/Decision mappings; native session-goal assessment placements and outcome mappings; descriptive closeout boundaries; exact reusable origin references. |
| `aquarium.procedure-fragment/v1` | Schema; stable definition identity and version; purpose and applicability; parameter and evidence input/output ports; one entry and named exits; native definitions and placements; internal rework and explicit external rework ports; required effects and assessor boundaries; exact origin/dependency references. |

The binding maps each placement to its native kind and intended Worker, report-only Judge or Orchestrator responsibility. Record the invoking entrypoint in existing execution context, not by making a different binding for each invocation. Validation may support its two callers and Design its three callers through one definition. Technical review remains an existing route operation; do not relabel its team as the ordinary Judge or encode each reviewer as an outer node.

TASK-137 defines versioned structural signatures for the assessment, approval, review-control and closeout capabilities needed by each family. Start from the existing operation contracts: relevant item types, permitted values, requiredness, operation IDs/digests and evidence relationships. Validate native declarations against these signatures before trusting binding labels. Placement/definition IDs, prose and unselected item names are not evidence of a capability. Preserve the operation identity when namespacing placements. If an operation's meaning changes, define and verify that changed operation explicitly rather than keeping its old digest.

Signatures cover the fields necessary for the guarantee, not every incidental item in a canonical Action. Existing signatures are reference implementations, not a permanent whitelist of complete graphs or work capabilities. Explicitly typed ports may connect differently named items when the same operation and obligation are established. New Worker work units remain authorable. A placement whose effects cannot be bounded is conservatively work/effect-bearing; it cannot obtain a bookkeeping exemption or satisfy an independent-assessment obligation merely through its label. Unresolved capability requirements yield `not-established`, with the missing property, rather than a blanket native-invalid classification.

A recognized assessment gate consumes required, dominating, current evidence from the producers it covers and exposes a typed verdict plus applicability. Evaluation operations that must report negative results accept `pass`, `fail` and `inconclusive` so the Action can finish before the Decision routes the result. Do not impose those accepted outcomes on unrelated native checks that legitimately block Action completion until they pass. Neither signatures nor digests authenticate an agent: the existing harness assignment and actual result observations establish independent execution, and the Judge assesses meaning. The source qualifier assumes faithfully recorded caller evidence and cannot guarantee resistance to a lying caller or undeclared out-of-graph effects.

Binding parameters describe inputs and ports, not their per-run values. Keep actual work IDs, criteria instances, approval, candidate identities, reviewer choices, current progress and results in existing execution assignments/records. Work-specific wording or fixed inputs may appear in a one-off Procedure; they become part of its source identity and require explicit parameterization for reusable promotion. Binding origin references describe provenance only.

Use native canonicalization for the Procedure digest and hash source bytes separately. Aquarium JSON definitions use UTF-8 with sorted keys, compact separators, preserved array order, no non-finite numbers and no trailing newline. Verify dependency identities at composition and materialize everything needed to execute and resume into the retained bundle. Admission checks this self-contained result. Resume does not resolve or re-hash mutable origin library files; missing or updated origins alone cannot invalidate an intact bundle.

The bundle ID is the SHA-256 of canonical `binding.json`, which binds `procedure.yaml` bytes and its native digest. The binding contains neither its own ID nor its final absolute location. Procedure bytes contain neither the bundle ID nor the binding path; bootstrap artifact locations are runtime item values. Compute the complete candidate and its IDs before assessment, then retain those exact bytes. This breaks any circular dependency between a source digest, bundle path and bootstrap record.

### Generated identity and exact recovery key

Reserve `aquarium-adapt-<family>-<token>` for newly authored or structurally adapted Procedures, within native identifier limits. `<token>` is a collision-checked authoring identifier allocated before hashing, not a session ID, final bundle digest or new security credential. New definitions start at version `1`; a revised definition under the same ID increments its positive decimal version within native limits. Reuse an unchanged definition's ID/version. Canonical sources keep their existing identity, and foreign explicit sources retain theirs when no native rewrite is required. Never overwrite a canonical same-ID source to disguise a new graph.

Use the native tuple `(procedure_id, procedure_version, procedure_digest)` as the exact resolver key. Podway readback does not project the authoring path or an Aquarium bundle ID. Before publication and start, enforce one authoritative adopted binding for that key across all roots the worktree resolver actually searches. Byte-identical copies are aliases, not conflicting bindings. For the same key, reuse the existing exact adopted bundle after current fit checks, including its original source bytes. Different comments, entrypoint-specific copies or new compatibility mappings must not create another ambiguous adopted binding. When a new mapping is required, mint a distinct native revision, usually under a derived adaptive ID for a canonical source, and qualify it before start; do not alter historical files.

The minimal writer and resolver in TASK-138 publish and check this invariant together so competing preparation cannot adopt different bindings for the same key. They may use a short local critical section, but add no persistent session-to-bundle database. Resolver output is one verified self-contained bundle, exact equivalent aliases, or a specific missing/corrupt/ambiguous/unsupported result. Stop before `begin` or work on an unresolved result. Native-readback resolution works for prepared sessions and running nodes that do not select the bootstrap artifact; any selected bootstrap reference is a cross-check, not the sole locator.

## 3. Selection and authoring

Search the current repository's approved definition locations, retained bundles, reusable library and installed defaults, plus explicitly supplied sources within scope. This is Aquarium discovery. Released Podway `start` accepts a safe worktree-contained regular source path; it does not perform Aquarium library discovery or use `procedure_paths` as an enforcement boundary. Aquarium uses the configured roots and repository ownership to select its managed write/search locations. A disposable index may accelerate lookup but is never an authority.

Resolve source authority before ranking fit. The repository's adopted managed customization and explicit workflow rules contribute applicable obligations even when that source is currently unqualified. Disclose an incompatible, stale or unqualified same-family adopted source in the existing envelope, identify its additional obligations and explain how the selected alternative preserves them. Changing or retiring an adopted obligation requires the existing applicable approval, not silent bundled-source fallback.

A reusable library entry is a selectable template unless repository authority adopts its rules as mandatory. An old `.local/` bundle is a reuse candidate, not automatically a new repository obligation. Mere existence of a noncanonical or unrelated file cannot block every workflow or require approval to compare templates. If ownership is materially ambiguous and cannot be resolved from repository sources, ask one focused question rather than inventing precedence.

Within that authority, prefer an adequate existing definition, a small adaptation, suitable-fragment composition and new authoring, in that order. Record the reason, fit limitations and current requirement coverage in the existing plan/assignment. Do not invent a fitness score, regenerate to demonstrate activity or treat old successful usage as current approval.

Recommend the technical review through the existing strategy before asking for the execution envelope. Its selected route, scope, participants and source-transmission authority constrain authoring. Review unavailability does not authorize an alternate Procedure that silently removes or changes the review.

Read-only planning may inspect the repository and existing definitions. Authoring and native planning-agent work begin only under the disclosed preparation authority. The Orchestrator may draft the Procedure or delegate that bounded work to a Worker. Do not require a permanent Planner role or a new user-visible invocation for each preparation step.

Use Podway's current authoring contract and advertised native operations. The separately installed `create-podway-procedure` skill remains an optional authoring aid unless the repository explicitly requires it; its absence must not recreate the ordinary startup qualification blocker. Do not vendor or modify that upstream skill. No generated instructions may authorize shell execution by Podway.

## 4. Fragment composition

A fragment is an explicit work/evidence contract with a closed native subgraph. It may contain a Worker/Judge pair or a larger coherent unit. Ordinary work fragments cannot declare `assessment.target: session_goal` or claim parent-goal success. Session-goal assessment and family acceptance belong to the whole Procedure's control layer. Reusable review/closeout control templates may carry those whole-session responsibilities explicitly; treat them as control templates under full family validation, not as ordinary fragment-v1 work units.

Composition binds explicit parameter/control/evidence ports and assigns deterministic placement/definition namespaces. Rewrite their native references, including routes, guards, selectors and rework targets, while preserving semantic operation IDs, digests and accepted outcomes. Field aliases use a validated typed port mapping; they do not redefine an operation. Do not perform unrestricted text substitution in natural-language criteria or commands.

Control edges do not imply evidence availability. Check input type, producer, selected items, applicability and native reference/dominance rules separately. Reject ambiguous producers, dangling ports, ID collisions after expansion, incompatible item contracts and unreachable required evidence. External rework ports must bind to declared targets; no fragment may jump into another fragment's private internal node.

Flatten the result to one ordinary Procedure v2 before native validation and admission. Verify the exact imported definitions at composition and retain the executable result with its binding. Origin references document where it came from; running sessions do not depend on those library paths remaining present. There is no runtime import, expression language, hook, plugin system or nested Procedure session.

Validate the whole composed graph as well as the fragment contracts. Native authoring accepts complete Procedure v2 documents, not fragment-v1 or unbound parameter templates. Check fragments with Aquarium schema/port validation and native-check at least one exact representative flattened instantiation; check every actual instantiation before adoption. State which inputs were checked rather than claiming all parameter values or actual execution were verified.

Use verified review/control templates as convenient building blocks, but permit a different topology when the same due obligations can be established. Keep native node, selector, predicate and resource bounds. Split serial Decisions when needed; do not add unsupported OR/expression fields or truncate obligations. Native-valid behavior whose required guarantee is unresolved remains `not-established`, not native-invalid.

## 5. Preparation, qualification and admission

### Preparation sequence

1. Resolve original requirements, family, effects and review needs by read-only discovery. Reconcile an existing session before planning a different one under the native lifecycle contract.
2. Present the existing workflow envelope with bounded adaptive preparation, local definition writes, actual native planning/Judge calls, selected reviews, permitted execution and required session operations. Preserve separate exact-diff, clipboard, installation, acceptance and commit boundaries.
3. After approval, select or compose the source and binding. Prepare only the execution definition and its requirement/evidence plan. Product implementation and substantive diagnosis cannot be hidden in this preparation interval. For Design and Diagnosis, only the disclosed local execution-definition files may be written here; canonical product/design documents still require their exact-diff approval, and upstream drafts keep their existing approved external locations.
4. Finish source formatting, resolve the binding, compute its bundle ID and native digest, and run native and structural checks before assessing that exact candidate. For an adapted, composed or newly authored candidate, obtain independent suitability assessment of the original requirements and execution plan under the lifecycle below. Any later material definition/basis change requires affected checks and assessment to be renewed.
5. Retain the exact qualified bundle atomically. Recheck its resolver key, content, current basis and applicable assessment before digest-fenced native start. Re-observe the admitted snapshot, perform the separate native begin, and establish required bootstrap evidence before product work.

### Suitability assessment lifecycle

The preparation interval has no extra Podway session. An unchanged, known definition whose structural contract is already established uses an Orchestrator fit check in the existing plan/envelope and retains its normal independent assessment boundaries. Include fit where an existing plan Judge can assess it; a Goal without a plan Judge retains its actual first due outcome assessment and must not invent an earlier Judge result. Do not add a pre-start call solely because an adequate unchanged definition is being reused. Unsupported bindings or material changes are not known reuse.

Adapted, composed and newly authored definitions require the pre-start suitability assessment. Use ordinary v2 with truthful pre-session context and a target containing the complete candidate's bundle ID, native digest and original requirement/plan basis. The report remains native orchestration evidence and is excluded from the binding hash. A compatible Task plan assessment may supply both judgments when it actually covers both scopes; do not demand duplicate semantic reviews.

Generated definitions provide a bootstrap recording Action and applicability check before product work. It records the real pre-start report and target through the existing assessment/result contract with explicit pre-start timing, rather than pretending the Judge ran in the current attempt. Verify exact candidate and basis equality and consume the record through required evidence references at its admission Decision. Ordinary native report delivery remains sufficient; this creates no new receipt format. Existing exact-known Procedures without a bootstrap keep their original checkpoint semantics and use resolver-based definition recovery.

After in-session plan rework, an unchanged definition may still fit, but changed requirements, plan or candidate evidence invalidate affected judgments. Route to the existing in-session planning/Judge capability with current inputs; do not re-record an old pass as a new assessment. If the admitted graph lacks the necessary route, stop with the exact gap and use the consented supersede path only when actually needed. The preparation/bootstrap compatibility rules belong to TASK-141 and the family integration tasks.

A `plan-only` request creates no files, providers, goal or session. A `plan-handoff` retains its existing explicit mode and session-bound plan semantics; adapting it must preserve exact artifact recovery and no-work stopping. An opted-out workflow does not inspect or mutate Podway. Non-Git `new-project` uses the same semantic planning, independent assessment and document approval without Podway discovery, source rendering, session setup or implicit Git initialization; use only its approved document/draft locations.

### Qualification layers

| Layer | Required checks and limits |
| --- | --- |
| Native authoring | Format, validate, vet, lint/check with warnings as errors and preview through the supported exact binary. Use the returned canonical digest/start grammar. Native checks do not prove work suitability. |
| Binding and structural obligations | Resolve capability signatures, native goal outcomes, producer/evidence/gate relationships, review control and acceptance provenance. Check effects before and after gates; names and terminal labels supply no guarantee. |
| Independent suitability | For changed/new definitions, assess the exact bundle and original requirement/plan basis; reuse existing due assessment where it genuinely covers this scope. Adequate known reuse retains existing checkpoints. Judgment grants no effects. |
| Runtime applicability | Before consuming a result, establish its actual operation, complete delivery, candidate/criteria/check-input basis and current native attempt/evidence context. Static admission cannot prove those future facts. |

The structural qualifier analyzes the closed native predicate vocabulary, required/dominating evidence and declared rework with an explicit unknown state. A syntactic path may be proven infeasible by its predicates; never assume it is infeasible to hide an unguarded achieved outcome. Use dependency/dataflow summaries rather than assuming that bounded node counts make full path enumeration cheap. Verify sound acceptance and practical analysis cost on representative and native-bound graphs. An exhausted analysis budget is `not-established` with its property/location, not success, a product defect or an automatic user-approval request. Do not add user-facing graph caps or arbitrary workflow retry quotas beyond native limits.

Require the following properties wherever the family contract makes them due:

| Obligation | Structural condition and runtime limit |
| --- | --- |
| Native goal success | Every feasible `achieved` mapping is covered by recognized current final-Judge outcome, verdict, mandatory-gap and applicability checks. No binding terminal classification can create success. |
| Independent delivery assessment | Each covered producer's required evidence reaches the relevant assessment and semantic Decision. Negative assessment results can finish recording and take their correction/evidence/stop paths. Structural signatures do not prove actual agent identity. |
| Forward effects after a gate | Every product/evidence-changing work item precedes the last current assessment covering its scope, or a later recognized gate re-establishes that coverage. An extra polish Worker after final judgment cannot reach accepted success on the old result. |
| Exact-diff application | Required approval precedes application, and current-target/diff verification establishes that the applied content is the actual approved content. Changed proposal/target bytes follow the existing renewed approval path. Final application verification remains due. |
| Review control | Preserve completed-versus-incomplete ordinal consumption, same-provider/same-operation recovery, review mode and confirmation scope, remaining authority and fresh user-direction after exhaustion. Goal revision, new Procedure or retrieval does not reset a grant. |
| Route change | Keep the already-supported, explicitly authorized in-session switch/waiver paths and retained findings/ordinal meaning. A source may specialize the selected provider, but cannot drop an applicable recovery or switching capability solely to shorten the graph. Do not probe or require unselected providers at startup; explicit scope exclusions remain effective. |
| Acceptance provenance | Delegated member/correction/internal-validation acceptance cannot satisfy final Epic closeout, cold validation or other user-owned acceptance. Verify actual goal-kind/workflow-owner evidence and the existing commit/no-commit/finalization boundary. |
| Rework | Rely on native suffix invalidation and fresh required references. Do not implement a competing attempt/freshness engine. Rework tests do not replace tests of forward content changes after a gate. |

After a final assessment, permit recognized bookkeeping, actual acceptance and closeout effects already allowed by the family, including its exact lifecycle-only delta, independently verified evidence projection and authorized commit/no-commit handoff. These exemptions cannot hide new code, tests or canonical content. Unknown effects do not receive the exemption, and declared bookkeeping instructions cannot authorize arbitrary writes. Product changes that need a fresh assessment, and changed accepted candidates that need renewed acceptance, retain their existing owners; do not turn every harmless metadata update into a new Judge cycle.

Review/control templates may satisfy these obligations compositionally when their verified preconditions and external ports hold. They are not the only acceptable topology. Assessment, approval, source currency and actual caller evidence remain distinct; code can prove only the declaration/transition properties, not every natural-language assertion or undeclared effect.

Report native validity, workflow compatibility and proof limitations separately. Reject an incompatible or not-established selected candidate and repair its definition under existing preparation authority. Do not bypass verification, silently change the review route or continue with another workflow. No new arbitrary retry count is introduced.

### Selected-source readiness

Separate tool/workspace health, installed-library diagnostics and admission of the selected definition. Preserve the full setup report on canonical/custom files. An adaptive invocation requires its selected source and actual required capabilities, not five unrelated tracked canonical files. Missing unrelated library entries cannot be its only startup blocker.

Add an adaptive admission path alongside existing canonical/custom/formal behavior. Preserve `inspect_podway_handler_contract()` for its existing sources and add objective adaptive qualification. Limit the five-ID allowlist, filename/ID equality and tracked-file rules to canonical managed files. An adaptive native tuple and supported binding determine session compatibility; selected-route readiness must not depend on five-file aggregate readiness. Preserve the full library diagnostic without misclassifying a healthy adaptive session as setup damage.

Under Aquarium's repository policy, retained bundles use its approved configured source root and need not be tracked. This is not a claim that Podway enforces `procedure_paths`. Honor the source-authority rules above when an adopted same-family customization is present; an unrelated missing template or optional old bundle is not an admission blocker.

Keep compatible runtime identity, exact source identity, route readiness and session conflicts separate. A healthy selected bundle never repairs an incompatible writer or grants initialization, reset or replacement authority. Version-floor eligibility remains separate from actual machine-contract support.

## 6. Runtime and recovery

Reuse ordinary v2 assignment and result fields and current Podway mutation templates. The Orchestrator performs lifecycle mutations and Decisions; Workers perform assigned work; the Judge reports only. Retain one logical Judge when supported, use fresh cold validation as currently required, and recover or replace an unavailable Judge without private-history prerequisites. One mutating Worker at a time in a shared checkout remains the default constraint.

Completing an Action means its declared operation and required result recording completed. A Judge can finish with rework or evidence-needed. Route its negative result rather than leaving its assessment Action permanently incomplete. Technical review outcomes, operation failure, report delivery and semantic completion remain distinct.

Reconcile reports through the current native transport. Missing or truncated output first triggers same-operation retrieval. Do not demand a new file, acknowledgement exchange or review simply to recover delivery. Preserve expected team membership, original reports, finding responses, ordinals and grants.

Use existing local settlement for eligible corrections and final Judge assessment. Negative results do not automatically regenerate the Procedure. Preserve global Epic gaps and unaffected evidence only with current applicability. Resetting the Procedure, changing a session label or selecting another template cannot reset review authority.

For adaptive same-session resume, read the native Procedure ID/version/digest and apply section 2's exact resolver across the approved roots. Verify the self-contained bundle, supported binding contract, current requirement basis and actual candidate before using retained results and remaining authority. A prepared session must resolve before `begin`; a running node may resolve without selecting any bootstrap item. If that item is selected, verify it as an additional cross-check. Do not guess the original path from native readback or search arbitrary host directories.

Missing, corrupt or ambiguous binding content requires exact recovery or a specific stop, not regeneration. Identical copies resolve to the same bundle. Changes or deletion in an origin library do not invalidate an intact retained bundle, and an unrelated package change does not force another assessment. A real compatibility or requirement change still requires its affected checks. Legacy/formal sessions keep their original recovery contract without fabricated adaptive metadata. Preserve the separate exact plan-handoff artifact and actual invocation context.

### Consented atomic supersede

Declared rework and changing hypothesis/check inputs remain in the current graph. Only missing topology requires this exception. Released Podway v0.2.14 already supports state-aware `start` with `--on-existing preserve` and `--supersede-reason`; it atomically cancels the running predecessor, records its superseded successor, archives it and creates a prepared successor. This is a new session, not an edit of the predecessor snapshot.

The implementation uses the current native `session.start_replace` template for the qualified successor source. The semantic command is `start --procedure <retained-procedure.yaml> --task <title> --expect-procedure-digest <digest> --on-existing preserve --supersede-reason <reason>`, with the current required workspace/session/revision fences and one idempotency key supplied through the native contract. A policy `--dry-run` may obtain the concrete transition for disclosure when supported. This command description is not a performed test or authority to execute it now.

Stop new work and reconcile uncertain effects and relevant descendants. Within existing preparation authority, qualify, assess and retain the successor before changing the predecessor; otherwise obtain that bounded preparation authority first. Disclose the exact old/new identity, missing topology, cancellation/archival effect, retained results, remaining grants and proposed transition, then request explicit replacement consent. After consent, re-observe and execute the single fenced native mutation. On an unknown result, recover the same request/key before replay. Verify the superseded lineage and successor, then resolve, begin and establish current applicability under its own context.

Do not replace this transaction with cancel-then-start, reset, delete or a false achieved outcome. A failed precondition leaves the old state intact; an unknown outcome remains unresolved until native readback establishes it. If the selected installed writer cannot provide the qualified atomic transition, preserve the session and report that capability gap. Review ordinals, findings and effect grants carry forward through existing execution records; superseding creates no extra authority.

TASK-144 implements this shared exception and amends the successful-terminal-only replacement wording in `podway-integration`, `epic-handler` and the affected family references without weakening normal successor checks. Earlier family tasks stop and report a missing-topology case until that shared implementation is available. TASK-145 tests the exception across activated families. Asking is required for the unexpected running-session replacement, not for ordinary rework or an already approved terminal successor.

Keep Epic member Goals, pre-validation corrections, Validation and closeout sessions separate as currently defined. A correction inside active Validation does not start a nested Goal. Finalization after a successful commit resumes without a duplicate commit if Podway completion or disposition was interrupted.

## 7. Retention and user-approved reuse

### Local definition storage

Retain `procedure.yaml` and `binding.json` under the selected repository root's `.local/<bundle-id>/`, normally `.podway/procedures/.local/<bundle-id>/`. Choose an explicitly designated retention root first; otherwise use the configured conventional root when present, or a single unambiguous approved alternative. Support custom roots. When several alternatives remain genuinely ambiguous, resolve them through the existing setup/envelope choice, not an automatic config edit or a conventional-path-only restriction. Resolver uniqueness spans all approved searched roots, not just the write root.

Honor an existing appropriate ignore rule. Otherwise, under the disclosed local setup/preparation authority, create a regular `.local/.gitignore` containing `*`, which ignores itself and local bundle contents without editing tracked workflow files. Verify actual ignored and untracked status before retaining content. Do not overwrite a different existing ignore file, tracked path or custom rule. An existing repository policy may instead authorize its own exclude mechanism; tracked ignore changes belong to the managed-update inventory and its approval, not a hidden write. Local-root/discovery and ignore behavior are Aquarium rules.

TASK-138 supplies the minimal atomic writer and exact-key resolver before any adaptive start. Publish only a complete qualified bundle and perform the uniqueness check and publication coherently. Use regular non-symlink paths beneath the approved root. Verify identical existing content and reuse it; conflicting identity or changed bytes stop without replacement. Handle Unicode, spaces, interrupted staging and competing publication. Existing native source/path safety remains authoritative; do not infer that it supplies an Aquarium-wide root restriction.

Keep adopted bundles for recovery and subsequent selection without automatic TTL eviction or size-based deletion. Clean only invocation-owned unadopted drafts under their disclosed cleanup authority. Do not claim survival of a destructive native reset/removal without its verified contract; disclose any recovery-definition loss before a separately requested destructive action.

Existing session snapshots remain native-owned. Bundle files are retained definitions and binding metadata, not a second session store or an archive of provider reports. Local retention is not a claim of backup, portability or Git persistence. Losing it may prevent exact continuation until the original definition can be recovered.

### Reuse and promotion

Reuse definitions only after current fit and contract checks; fresh work receives fresh assignments, evidence and due assessments. Invocation-specific approval and past pass states never transfer. Generic definitions identify parameters; they do not grant tools, repository access or review budget.

After actual use, use existing results to assess whether the Procedure operated adequately and whether it has a distinct future use. A native-valid definition, successful start or clean unit suite alone cannot support that recommendation. Compare it with existing library entries to avoid preserving duplicates. Do not add a mandatory Judge round just for the preservation decision.

Offer the whole Procedure or a useful fragment with its intended use, observed limits, parameterization, exact target paths and proposed diff. Normally present candidates together in the Task/Epic closeout report; do not interrupt routine member delivery. Use the user's language and ask whether to keep the definition in the reusable library. The question is not an approval record until answered, and promotion is never a prerequisite for completing the original goal.

Show the parameterized/extracted candidate and the separate execution/commit scope before consent. Finish the original task's accepted closeout commit or verified no-commit result and its required Podway finalization before applying tracked promotion changes. This prevents the optional library diff from invalidating the original reviewed candidate or consuming its finalization evidence. Failure or delay of promotion does not reopen an already completed product goal.

Then apply only the specifically accepted library diff under the approved shared root, normally `.podway/procedures/reusable/<name>/`. Keep fragments distinguishable from complete sources in Aquarium discovery; native authoring receives only complete flattened instances. Preserve custom files and revalidate the exact transformed definition using schema/port checks and a representative native-checked instantiation where needed. Distinguish those results from actual runtime execution. A material change beyond the disclosed promotion diff needs fresh consent, not a blanket restart of the original workflow.

Keep native reports, private paths, session handles, credentials and task-specific grants out of promoted definitions. Promotion is source authoring, not promotion of Podway recorded claims as proof. Use existing evidence-residency rules for any separately required durable execution evidence.

A yes to preservation authorizes only the disclosed library content. The same concrete question may also request its separate one-commit grant; do not ask twice when both were explicitly approved. A pre-existing grant matches only if it expressly covers this promotion after original-work finalization and is unconsumed. Otherwise leave the approved library diff uncommitted until commit authority is given. Never widen, amend or reuse the original completion commit.

TASK-145 connects a bounded library-promotion handoff to `task-commit`: retain the true originating workflow/Task/Epic, exact approved library diff, required checks and assessment, release-note decision and any promotion-specific commit grant, with no original-work lifecycle edit. Use the existing applicable review/acceptance policy for this new source diff; do not add a mandatory new multiagent workflow just to store a definition. Keep promotion after the source execution's finalization and publication outside its authority.

A no changes no tracked files and retains local recovery material. Later deletion or promotion requests are independent operations; do not repeat a declined preservation question without new information.

## 8. Compatibility and deployment

This is a breaking Aquarium workflow/admission update because existing users need updated consumer contracts and supported repository setup. Keep current source versions and IDs until the affected implementation changes them deliberately. Do not change Podway's producer or its installed binary to accommodate an Aquarium candidate.

Preserve old canonical, same-ID customized and formal-delegation sources and their immutable sessions. They use their admitted rules, not fabricated adaptive bindings. New adaptive bundles use explicit family/entrypoint mappings rather than requiring a canonical filename. A compatible legacy session may finish under its original contract; unsupported continuation must name the exact mismatch and safe options without automatic migration.

Each family activates adaptive selection only with its integration task: TASK-142 for Task/Goal/Validation, TASK-143 for Design, TASK-144 for Diagnosis. TASK-139/140 exercise authoring/composition through helpers and disposable fixtures without changing ordinary handler defaults. Each activation includes its minimum working retention and resume path. TASK-145 completes cross-family recovery and promotion; it is not the first implementation of storage or resume.

Host development uses installed released tools. Candidate installation, actual candidate handler startup and managed-file upgrade verification run only in the dedicated UTM guest. Do not copy candidate assets into host managed files, change plugin caches or patch globally installed skills. TASK-145 reconciles `AGENTS.md` and its setup-guidance owner for the installed adaptive release: distinguish protected canonical managed copies from approved local bundles and specifically consented reusable sources. The change permits those definition operations under their actual authority, not candidate installation or edits to protected host state. Registration does not change today's root instructions.

Use the supported official Podway v0.2.14 compatibility artifact where the existing release contract requires it. A later supported release may be observed separately through its actual identity, but this Epic does not depend on Podway development HEAD or the optimization project's completion. Haepari, Dolgorae, Web Pro Review and skill-modernization epics are not new prerequisites. Reconcile independently changed shared contracts rather than overwriting them.

## 9. Implementation owners

Keep shared adaptive behavior in one new reference under `plugins/aquarium/references/` and its minimal definition/qualification helpers under the plugin's shared code. TASK-137 chooses private module layout without introducing a new user-facing service. Ordinary reports and native dispatch keep their current owners.

| Area | Existing owners to inspect and update when implementing |
| --- | --- |
| Entry and family semantics | Seven `skills/*/SKILL.md` entrypoints; `references/task-orchestration.md`, `epic-orchestration.md`, `validation-orchestration.md`, `design-diagnosis-orchestration.md`, `procedure-node-contracts.md` |
| Source admission and setup | `references/podway-integration.md`, `tool-catalog.md`; `skills/dev-setup/scripts/inspect_tools.py`, including current-session ID/version checks and route-readiness aggregation; applicable `dev-setup` and global setup guidance |
| Definitions and examples | `assets/podway/procedures/`; new adaptive binding/fragment schemas and reusable definition assets; preserve historical fixtures |
| Assignments, Task phases and resume | `references/ordinary-agent-orchestration.md`, `worker-guidance.md`, `plan-handoff.md`, `task-orchestration.md`; `task-handler` fixed phase/discovery rules; `skills/goal-judge/` helpers; `task-close` and `task-commit` consumers |
| Atomic replacement and promotion | `references/podway-integration.md` replacement rules, `epic-handler` and family continuation contracts; `task-commit` exact-candidate and provenance rules; no change to Podway's native transaction |
| Technical review | Existing strategy, intent, result-handoff, routing and finding-disposition references; Independent/Herdr/Mulgae entrypoints and native ownership |
| Authoring verification | `tests/unit/test_procedure_alignment_contracts.py`, `tests/test_inspect_tools.py`, `tests/podway_runtime_qualification.py`, compatibility helper and objective new helper tests |
| Installed verification | `tests/vm/run_acceptance.py`, `native_observation.py`, scenarios and fixtures; release-handler manual acceptance reference |
| Durable documentation and guidance | `docs/specs/`, `docs/architecture/`, applicable ADRs, implementation/operation guides, `TESTING.md`, `AGENTS.md` through its setup-guidance owner, public disclosures and CHANGELOG when behavior is delivered |

Do not add a release-note claim for this registration. Each implementation task makes its own release-note decision under existing policy. Promote implemented contracts to their canonical owners during delivery; do not leave the dossier as the only runtime authority.

## 10. Task acceptance

Task ordering and dependencies are in the roadmap. Every task includes its focused checks, affected documentation and truthful evidence limits. A later task cannot excuse a currently unusable or falsely admitted intermediate contract.

### TASK-137: Establish the adaptive contract and preservation baseline

- Materialize sections 1 and 2: native goal/outcome semantics, minimal capability signatures, Task invariants and conditional phases, binding/fragment formats, identity/version policy and worktree-wide exact recovery key. Keep actual invocation values out of the reusable binding.
- Define source authority, known-versus-new suitability lifecycle, consented atomic supersede and post-finalization Git promotion using the settled policies. Preserve ordinary v2 reports and existing review/delivery contracts.
- Map seven entrypoints to due review controls, acceptance provenance, late-effect rules and positive/negative/not-established fixtures. Define capability signatures by necessary guarantees, not complete canonical topology or report-authentication claims.
- Name each existing rule to amend and its owning task. Publish unimplemented reservations for later delivery; creating schemas or this task does not activate adaptive handlers.

### TASK-138: Admit selected definitions without canonical-shape coupling

- Add selected-source compatibility alongside preserved canonical/custom/formal inspection. Decouple adaptive session validity, generated IDs, filename rules and selected-route readiness from the five-file aggregate, while retaining full library diagnostics and adopted-customization disclosure.
- Ship the minimal atomic local writer and exact native-tuple resolver, including multi-root uniqueness, identical aliases, safe custom roots, ignore handling and prepared-session recovery. No start path may depend on retention deferred to TASK-145.
- Prove a disposable native preview/start/begin/resume slice using exact known Procedure bytes and a verified reference binding; test missing/ambiguous/corrupt binding and a running node without a bootstrap selector. Preserve ordinary handler defaults.
- Verify that unrelated missing templates and optional old bundles do not alone block selection, while runtime, selected review, required customization and session problems remain visible. Distinguish actual local native evidence from official clean-candidate or installed verification.

Until TASK-141 supplies full structural qualification, this slice admits only exact known Procedures whose existing contract establishes the obligations. Helpers may prepare other sources, but cannot activate them. This temporary restriction is not final adaptive acceptance. TASK-139 begins only after the slice's permitted helper/native evidence is settled; a clean-commit gate, if selected, runs against the resulting authorized commit without manufacturing a checkpoint commit.

### TASK-139: Select and author work-specific Procedures

- Implement the selection order and reasons, requirement-source reconciliation, read-only planning and approved preparation interval.
- Honor the approved route and effects; use existing native authoring mechanics without requiring unavailable authoring helpers or hidden telemetry.
- Produce exact candidate source/binding and a coverage plan from work inputs, including suitable reuse and genuinely different work structures.
- Test invalid selection, source drift, adopted-customization handling and no-authority cases; plan-only remains non-mutating. Keep handler defaults unchanged and newly generated candidates non-admissible until TASK-141 and the family activation task.

### TASK-140: Compose reusable Procedures and fragments

- Implement explicit parameter/control/evidence ports and namespace expansion while preserving semantic operation identities and the ordinary work-fragment/session-control distinction.
- Resolve dependencies at composition into a self-contained result; origins are not resume dependencies. Apply Aquarium fragment/port checks and native checks to exact flattened instances, not raw fragments.
- Demonstrate whole reuse, partial reuse and genuinely different work structures without copying execution results or grants. Provide reusable control templates without making their complete topology mandatory.
- Reject conflicting identities/types, unresolved ports, stale composition inputs and work fragments with parent session-goal assessment. Preserve valid namespaced/equivalent compositions. Exercise helpers and disposable fixtures; do not activate handlers here.

### TASK-141: Qualify structure and independent plan suitability

- Implement native goal-mapping and capability-based guarded analysis, including review control, route recovery, acceptance provenance and forward work after the last applicable gate. Rely on Podway for native rework invalidation.
- Accept all five current ordinary canonical Procedures with proper reference bindings, including stopped/non-achieved paths, and valid namespaced/equivalent compositions. Reject obligation-breaking mutations, not every change rejected by canonical equality.
- Implement changed/new pre-start suitability and current bootstrap import, known-reuse checkpoint preservation, and affected reassessment after definition or plan changes. No duplicate Judge cycle or native-authentication prerequisite is added.
- Test typed unknown/infeasible guards, pass-only assessment failures, forged capability labels, post-approval changes and `not-established` separately from invalid/incompatible outcomes. Verify bounded analysis performance without assuming all paths are cheap to enumerate. Family activation remains with TASK-142 through TASK-144.

### TASK-142: Integrate Task, Epic and Validation execution

- Activate adaptive selection for these families with working storage/resolver and same-session recovery. Amend Task fixed phase loading, conditional refinement discovery and mapped plan-handoff boundaries; preserve direct phase contracts and keep Epic goal-centered.
- Preserve member/correction/internal-validation grants, cold-versus-internal Judge behavior, native achieved outcomes and user-owned final acceptance. No delegated acceptance at final Epic or cold validation is admitted.
- Verify selected review teams, ordinal and confirmation controls, authorized in-session switch/waiver paths, same-operation retrieval, original finding responses and eligible local settlement without new routine approvals.
- Cover normal/negative/stopped delivery, prepared/running recovery, planned successors and commit-success/finalization recovery. Until TASK-144 implements shared atomic supersede, report missing topology without mutating the running session.

### TASK-143: Integrate feature, project and refactor design

- Adapt all three entrypoints while retaining distinct artifacts, upstream leaf capabilities and raw QA result/operation separation.
- Preserve exact document diff approval and changed-target reapproval, delivery-input commit boundaries and required canonical work definitions.
- Cover non-Git `new-project` and explicit Podway opt-out without Podway inspection, rendering or implicit initialization.
- Activate these entrypoints only with their same-session resolver and minimum recovery. Verify different discovery/design structures, negative QA owner routing, changed-target currency, approved application and no product implementation. Preserve exact known reuse without inventing an extra plan Judge.

### TASK-144: Integrate adaptive diagnosis

- Adapt baseline, hypothesis investigation, cause/scope assessment and proposal paths to actual symptoms.
- Preserve isolated reproduction, competing hypotheses, incomplete diagnosis and evidence-backed no-work; do not turn an unreproduced symptom into a fixed defect.
- Keep QA, exact document/no-change approval and final diagnosis assessment on all applicable terminal paths.
- Activate Diagnosis with exact recovery and implement the shared, explicitly consented atomic supersede path for all adaptive families. Amend the old successful-terminal-only rules, verify native predecessor/successor lineage and unknown-outcome recovery, and reject cancel-then-start/delete substitutes. Normal investigation changes remain in the graph and never become an implicit product fix.

### TASK-145: Complete promotion, recovery and installed-test preparation

- Integrate cross-family retention/recovery tests on top of TASK-138's writer and the activated handlers. Cover exact aliases, ambiguous keys, library changes after adoption, prepared/running/handoff recovery and superseded lineage without a second state store.
- Offer whole/fragment preservation after successful useful operation. Apply tracked promotion only after original-work finalization, under specific content consent and a matching promotion commit grant when committing. Cover yes/no/partial outcomes, ordinary no-commit retention and transformed-source checks without extra routine Judge calls.
- Reconcile current setup, tool-catalog and `AGENTS.md` ownership: preserve adopted customization and protected canonical copies while distinguishing local bundles and explicitly approved reusable source. Update public/current owners only for actually implemented behavior.
- Complete VM driver, fixture and scenario extensions here, including explicitly selected canonical regressions, admitted-mapping semantic checkpoints, seven entrypoints, required Ouroboros readiness, clipboard authority when PM is used, and non-Git/diagnosis fixtures. Keep these additions outside ordinary LLM-free Make testing.
- Commit accepted implementation/test artifacts through the ordinary authorized handoff before TASK-146 uses the clean exact candidate. Local helper/static checks precede that commit; installed outcomes remain pending until observed. No minimum start/resume safety is deferred here from an earlier family task.

### TASK-146: Verify integrated adaptive delivery and promote outcomes

- Execute section 11's helper/native/installed integration scenarios against accepted committed implementation and test artifacts from predecessors. Record exact candidate/tool/environment and separate unperformed outcomes; do not run an uncommitted version of this task's driver as installed proof.
- Use the existing guest guard, managed-update evidence and native observations with adaptive checkpoint assertions. Preserve source-pinned canonical regressions and distinguish library-readiness diagnosis from selected-source health.
- Observe full representative functionality across all seven entrypoints under explicit authority before release preparation. Release smoke remains upgrade/startup. Missing Ouroboros or required approval is incomplete, not a waived successful case.
- If integration exposes a defect, return it to its canonical task owner under the existing correction grant, commit the verified correction and rerun affected candidate-bound observations. Do not invent checkpoint commits or mark missing installed evidence complete to satisfy ordering.
- Promote durable outcomes and prepare actual integrated Master acceptance. Planned documentation settlement can follow completed observations; code, fixture or runtime-affecting changes invalidate relevant old results. Keep publication and host installation separate.

## 11. Verification and evidence

These are acceptance scenarios, not execution results. Each owning task adds objective helper or graph coverage where executable behavior exists and declares required observed skill scenarios. Do not add prose-matching assertions, a synthetic relay or an automated LLM evaluator to ordinary `make test`.

| Case | Required result | Primary owner |
| --- | --- | --- |
| ADAPT-01 | Suitable existing Procedure is reused with a concrete fit reason and no unnecessary generation. | TASK-139 |
| ADAPT-02 | Documentation and performance work both qualify with different producer/evidence/Decision structures, not just different IDs or no-op phases. Documentation-only work needs no unused implementation/refine/Deslop prerequisite absent an independent requirement. | TASK-139; TASK-141; TASK-142 |
| ADAPT-03 | Whole and partial reuse preserve operation identities and resolve ports/rework; conflicting composition inputs reject. Fragment checks use exact flattened instances and origins need not remain available for resume. | TASK-140 |
| ADAPT-04 | Reject missing final-Judge predicates, invalid applicability routed forward, unguarded achieved mappings and product work after the last covering assessment. Exercise forward post-approval/assessment content changes separately from native rework invalidation. | TASK-141 |
| ADAPT-05 | A real fail/inconclusive assessment completes its operation and routes to rework/evidence/stop without false success. | TASK-142 |
| ADAPT-06 | Seed original-source and compound-criterion omissions and goal-destroying remedies; current assessments discover them without changing the authoritative requirement set to match the plan. | TASK-141; TASK-142 |
| ADAPT-07 | Selected route and complete expected Independent UI or Herdr child team survive composition; missing required reports remain incomplete. | TASK-142 |
| ADAPT-08 | Truncated/unreadable delivery recovers the same operation, with no new reviewer, ordinal or synthetic receipt requirement. | TASK-142 |
| ADAPT-09 | Eligible local corrections use current checks and final Judge without needless re-review or Procedure regeneration. | TASK-142 |
| ADAPT-10 | Every member can pass while an Epic seam still blocks final acceptance; future members are not required prematurely. | TASK-142 |
| ADAPT-11 | Feature, project and refactor designs preserve QA verdicts, exact application approval and no-implementation boundaries. | TASK-143 |
| ADAPT-12 | Non-Git project planning and opted-out work perform no Podway discovery, source rendering, session mutation or Git initialization. | TASK-143 |
| ADAPT-13 | Reproducible, intermittent, incomplete and no-work diagnoses retain distinct truthful results and required approval. | TASK-144 |
| ADAPT-14 | Resolve prepared, running non-selecting-node and handoff-successor sessions by native ID/version/digest. Identical aliases work; conflicting bindings across roots, missing or corrupt bundles stop without guessing. Origin-library changes alone do not block an intact bundle. | TASK-138; TASK-142; TASK-143; TASK-144; TASK-145 |
| ADAPT-15 | Consented native preserve-start creates linked superseded/archive/prepared-successor state atomically, with fresh fences and same-key unknown-outcome recovery. No cancel-then-start/delete substitute, grant reset or added approval for normal rework/successors. | TASK-144; TASK-145 |
| ADAPT-16 | Bundles are local and ignored under conventional or approved custom roots. Atomic publication enforces worktree-wide key uniqueness; competing/partial writes, unsafe paths and existing ignore/track conflicts preserve existing files. | TASK-138; TASK-145 |
| ADAPT-17 | Successful/useful whole/fragment candidates prompt together at closeout. Yes/no/partial decisions preserve local copies and original completion. Tracked promotion follows original finalization; only an explicit promotion grant permits its separate commit. One combined consent/commit question suffices. | TASK-145 |
| ADAPT-18 | Parameterized/extracted promotion receives schema/port and representative flattened native checks. State tested inputs and actual runtime limits; never inherit the source's execution claim or copy its runtime/authority data. | TASK-145 |
| ADAPT-19 | Legacy canonical/custom/formal state and active snapshots survive the update; unrelated missing templates do not alone block selected-source admission. | TASK-138; TASK-145 |
| ADAPT-20 | Actual installed startup and due semantic progression work for all seven entrypoints, not only a prepared assignment or copied skill text. | TASK-146 |
| ADAPT-21 | Plan-only remains read-only; plan-handoff restores exact artifacts and source drift invalidates only affected claims. | TASK-139; TASK-142; TASK-145 |
| ADAPT-22 | Commit-success/finalization failure recovers without another commit or false workflow completion. | TASK-142 |
| ADAPT-23 | Committed driver/fixture and exact installed-candidate checks reject mismatches, missing selected Ouroboros/clipboard authority and pending descendants. Old result files cannot supply a new PASS. | TASK-145; TASK-146 |
| ADAPT-24 | Source-pinned canonical regressions keep fixed checkpoints. Adaptive smoke derives its checkpoint from the admitted verified binding plus actual native work and fixture oracle, accepting valid different node IDs without accepting missing work or a wrong family. | TASK-145; TASK-146 |
| ADAPT-25 | All five canonical bindings accept their legitimate achieved/stopped paths, including a shared closeout terminal. Missing goal tracking, arbitrary success labels and parent-goal assessment inside an ordinary work fragment cannot manufacture success. | TASK-137; TASK-140; TASK-141 |
| ADAPT-26 | Valid namespaced capability signatures and typed aliases qualify. Worker-labeled fake Judge evidence, text-nonempty verdicts and pass-only assessment records cannot satisfy independent assessment. Legitimate unrelated pass-only native checks remain usable. | TASK-137; TASK-140; TASK-141 |
| ADAPT-27 | Reject missing ordinal continuity, incomplete-operation consumption, cross-provider resume, excess confirmation without new authority and delegated final/cold acceptance. An authorized in-session switch preserves findings and authority without requiring unselected providers at startup. | TASK-141; TASK-142 |
| ADAPT-28 | Positive canonical and composed controls pass. Native-invalid, proven incompatible and valid-but-not-established cases remain distinct; test infeasible guarded paths and practical analysis cost without exhaustive-path assumptions or matching skill prose. | TASK-141; TASK-146 |
| ADAPT-29 | Preserve applicable adopted-customization obligations and disclose a justified replacement in the existing envelope. Optional reusable templates and historic local files do not become mandatory policies merely by existing. | TASK-138; TASK-139; TASK-145 |
| ADAPT-30 | Known unmodified reuse keeps existing assessment boundaries, including Goal without a plan Judge. New/changed candidates receive exact-target pre-start suitability and truthful bootstrap import; changed basis on re-entry cannot replay an old pass as a fresh assessment. | TASK-139; TASK-141; TASK-142 |

Extend the existing VM implementation rather than creating another harness. Preserve guest guards, candidate/artifact binding, actual managed-update windows, native role separation, source-byte checks, fixture oracles, same-handle recovery and cleanup. Canonical regression invocations explicitly select the corresponding canonical source. Adaptive smoke resolves the admitted binding and its first due semantic checkpoint, then verifies real work, reports and the application oracle; generator-supplied labels alone cannot pass. No fixed canonical node assertion applies to an independently valid adaptive mapping.

Mutation tests target violated obligations, not every source difference that canonical equality rejects. Include valid alternative grouping, namespacing and selector-equivalent structures as positive controls. A conservative not-established result may stop an unresolved candidate but cannot be used to claim that all noncanonical functionality is implemented. Fixture report fabrication proves rejection logic only, never real independent agent activity.

VM-only capture and native observation are test instrumentation, not ordinary admission requirements. Extend small fixtures to all seven entrypoints, including non-Git documents and isolated diagnosis. Establish only the native/upstream capabilities actually used by each case; Design/Diagnosis cases declare required Ouroboros readiness and separate clipboard authority when PM would replace it. Missing prerequisites are incomplete, not implicit installation, a new provider fallback or successful skip. Full development verification covers representative delivery, rework, recovery and closeout. Release acceptance remains upgrade/startup smoke.

Run candidate installation and installed behavior only in the dedicated UTM VM. The registered plan itself grants no VM execution: the later execution envelope must obtain the repository's separate explicit VM-test authority or use release-handler. Use Codex as the required observed harness for this Epic; preserve other supported native mappings and state their unobserved results honestly without blocking ordinary use solely for missing telemetry.

### Candidate and verification order

Use focused helper/static tests and allowed native disposable fixtures during their owning tasks, including before commit where those check contracts permit it. Record the exact code and tool basis. The clean-committed-candidate requirement belongs to the official compatibility gate and installed-candidate build/VM path; do not generalize it into a ban on all local uncommitted checks.

TASK-138's small local native slice does not need a candidate plugin installation. Its behavior evidence must be settled before dependent generation work; an explicitly selected official clean-candidate gate, if used, follows its authorized commit and remains a distinct observation. TASK-142 through TASK-144 add their functional scenarios and working recovery with their implementation. TASK-145 completes and commits the driver/fixture extensions. TASK-146 uses those clean committed bytes for installed integration; it must not modify its own driver and claim its uncommitted bytes were installed and verified.

The later execution envelope discloses this split between task-local evidence and committed-candidate integration. Missing later installed observations stay pending and prevent integrated completion. A failed installed observation returns to the original owner for a separately authorized correction commit under existing grants, followed by affected re-verification; it does not justify extra checkpoint commits, a fabricated test pass or an altered acceptance definition.

Keep ordinary Make, official Podway compatibility and installed VM result contracts authoritative and separate. Do not run formatting preparation merely to validate documentation registration. Source, helper and native-guard checks never substitute for observed handler behavior.

An optional small comparison can hold goals, fixture baseline and Worker/Judge conditions constant and compare fixed versus adaptive work: unmet criteria, unnecessary steps, rework, elapsed time and available usage. Report only observed data; no benchmark platform, mandatory percentage improvement or claim of statistical effectiveness is part of acceptance.

## 12. Implementation handoff and closeout

Begin at the earliest unfinished task in the roadmap, initially TASK-137. Read this dossier and its linked original contracts before implementation. The registration worktree may still be uncommitted; preserve it, identify its planning authority and obtain any required staging/commit grant rather than including it silently in a later code commit.

Use an installed compatible released `epic-handler` for implementation when it can start under the current host combination. Do not require the unfinished adaptive feature to implement itself or patch the host's installed handler. If installed startup is blocked, identify the exact prerequisite and obtain one scoped supported execution alternative, such as direct native coordination with an explicit Podway opt-out; no silent fallback is authorized by this dossier.

The execution envelope should cover the named Epic, sequential member delivery, selected review/transmission scope, required checks and affected documentation, separate member/correction/closeout grants, and the proposed VM verification authority where applicable. Existing user acceptance and release policy remain in force. Do not ask the user again to choose the adopted operating policies merely because another AI resumes the work.

Suggested next-session request:

```text
Open /Volumes/RootKernel/RootKernel/aquarium/aquarium using DevSpace when available,
or the receiving agent's already authorized repository tools.
Implement EPIC-026 (ADAPT) from docs/roadmap/README.md and
its Detailed SOT, docs/todo/TODO-ADAPTIVE-PROCEDURES.md.
Read current repository instructions and preserve changes after the planning baseline.
Propose the normal execution envelope before implementation, including the actual
review route and any separately required VM-test authority. Start with TASK-137
or the earliest unfinished predecessor-satisfied task.
Preserve EPIC-024/025 behavior. Do not modify Podway or host installed state.
Keep automatic adoption within the approved scope, local retention, specific
user consent for post-use Git promotion, and explicit consent for unexpected
in-progress session replacement. Do not treat this request as push or release authority.
```

At each task, promote implemented behavior to its exact canonical owners and keep this dossier accurate for remaining consumers. At Epic closeout, replace the roadmap's Detailed SOT with Canonical Outcomes, update all planned pointers added by registration, and remove this dossier and its TODO entry only after the last consumer and actual closeout approval. Retain Git history; do not create an archived copy or a tracked execution log. Implementation is complete only when required evidence is settled and Master has actually accepted the integrated result.

## 13. Review integration boundaries

The supplied static feedback uses R-01 through R-20. The decisions below explain which remedies this plan adopts or narrows; they are implementation requirements, not proof that the revisions have passed independent or runtime verification. Existing operating-policy consent remains unchanged.

| Feedback | Adopted resolution and limit |
| --- | --- |
| R-01 | Native goal mappings own achievement. Ordinary work fragments cannot assess the parent session; whole-session control templates are validated at Procedure scope. Terminal labels are descriptive. |
| R-02 | Recognize the necessary assessment/approval/control signatures and evidence edges. Do not copy every canonical item or placement, treat signatures as agent authentication, or prohibit legitimate unrelated pass-only checks. |
| R-03 | Verify existing review-control and acceptance-provenance obligations. Pinned control templates are useful but not the only topology; unselected provider availability is not a universal prerequisite. |
| R-04 | Require coverage after relevant forward mutations and exact-diff currency. Keep native rework invalidation and existing bookkeeping/closeout exceptions; do not reassess every harmless record. |
| R-05 | Adaptive Task capabilities follow actual due postconditions, including conditional refinement. Explicitly change the old fixed-order consumer while preserving direct/legacy contracts. |
| R-06 | Preserve adopted repository customization. An optional library entry or historical local bundle is not mandatory workflow policy merely because it exists. |
| R-07, R-11 | Recover via native ID/version/digest with one adopted binding across the whole searched worktree. Identical aliases reuse content; changed mappings receive a new native identity before adoption. This is lookup ambiguity, not an assumed cryptographic collision. |
| R-08 | Use consented native atomic supersede, fresh fences and same-key recovery. Do not implement a cancel/start emulation or modify an admitted snapshot. |
| R-09 | New/changed definitions get exact pre-start suitability; adequate known reuse keeps existing checkpoints. Goal's absent plan Judge is not filled with a fictitious report or an automatic extra cycle. |
| R-10 | Offer preservation at closeout, apply it after original finalization and use an explicit promotion commit grant. Content and commit consent can be one question; original completion does not depend on promotion. |
| R-12, R-13, R-14 | Storage/resolver precede start; families activate with recovery. TASK-145 commits driver/fixtures before TASK-146's installed checks. Source-pinned canonical and adaptive semantic cases coexist. Clean-commit rules do not prohibit permitted local uncommitted tests. |
| R-15 | Add positive, unsafe and not-established controls with meaningful structural differences. Do not import every canonical-equality rejection or assume bounded nodes make path enumeration cheap. |
| R-16 | Distinguish Aquarium discovery/root policy from native source loading. Support approved custom roots and existing ignore policies; do not force the conventional root or hidden tracked configuration edits. |
| R-17 | Check fragments with Aquarium contracts and representative flattened native instances; state the limits instead of claiming every possible parameter value was executed. |
| R-18 | Reconcile root guidance during implementation through its existing owner. Registration does not relax current protected host-state or managed-source rules. |
| R-19 | Resume from the self-contained admitted bundle. Origins remain provenance and mutable library changes alone do not invalidate current execution. |
| R-20 | Keep the environment's DevSpace entrypoint while allowing already authorized repository tools in other receiving environments. This is handoff wording, not an implementation blocker. |

No new Epic or Task is allocated for these revisions. The existing ten Tasks own the added contract details and scenarios. Do not translate a static review recommendation into a new approval gate, execution prohibition, provider receipt requirement or canonical topology constraint without an actual due obligation and its authority.
