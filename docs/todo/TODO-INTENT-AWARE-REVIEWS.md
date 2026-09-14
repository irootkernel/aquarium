# Intent-aware review and temporary Independent Review disablement dossier

## Roadmap authority

This dossier is the temporary execution source of truth for `EPIC-015` and
`TASK-062` through `TASK-067`. The
[roadmap](../roadmap/README.md#epic-015-add-intent-aware-review-and-disable-independent-review-temporarily)
alone owns their identifiers, ordering, dependencies, and lifecycle state.
Review contracts, skills, Procedure assets, tests, and public documentation own
the implemented behavior after closeout.

## Task map

| Task | Delivery boundary |
| --- | --- |
| `TASK-062` | Disable Independent Review before dispatch, guide alternatives, and make Dolgorae optional in common production readiness. |
| `TASK-063` | Define the shared Review Brief, purpose, provenance, candidate, checkpoint, and assessment semantics. |
| `TASK-064` | Apply completion review to embedded Mulgae use and aggregate accepted Markdown role reports conservatively. |
| `TASK-065` | Add standalone Mulgae change and Task or Epic completion review. |
| `TASK-066` | Align Orca Dispatch and result handling, plus guidance for an explicitly chosen native Codex subagent. |
| `TASK-067` | Align handlers, Procedures, canonical and public documentation, deterministic checks, and manual acceptance. |

## 1. Requested outcome

Update Aquarium's enabled Mulgae and Orca review paths so the external reviewer receives the purpose of the work, its applicable requirements, and the constraints needed to judge the selected candidate. Apply the same review guidance when Master explicitly chooses a temporary native Codex subagent review.

Temporarily disable Dolgorae-based `$aquarium:independent-review` in Aquarium. An invocation must refuse execution and explain the available alternatives. Do not replace its backend automatically. Master will address Dolgorae separately; neither Dolgorae changes nor future re-enablement are deliverables or prerequisites of this request.

The reviewer must be able to answer both questions when completion is requested:

1. Does the implementation introduce actionable defects or regressions?
2. Does the selected candidate satisfy the Task or Epic requirements, including implementation that should exist but is absent from the diff?

Sharing requirements does not compromise review independence. Asking a reviewer to accept the implementer's conclusion does. Preserve independent judgment while supplying enough context to avoid findings based on misunderstood intent, obsolete behavior, or requirements that are outside the approved scope.

This dossier defines adopted work; it does not declare that the requested behavior is already implemented. It is a development handoff, not a new runtime state owner or a replacement for canonical specifications. Do not treat the section numbers below as Epic or Task IDs.

## 2. User scenarios and execution boundaries

Mulgae is normally the external review step near the end of an approved Task or Epic workflow. Master also requests standalone reviews of staged changes and Task or Epic completion. Orca remains available for those requests, and standalone Mulgae remains supported. The existing Independent Review entrypoint stays recognizable but must refuse execution while disabled.

Guide Master toward a fresh native Codex subagent where the current host actually supports one, or toward an explicitly selected Orca Review. Guidance alone must not launch either alternative, create a new backend, or imply that a native subagent has Dolgorae's guarantees.

Support the following routing without requiring additional skill names:

| Request or invocation | Review purpose | Completion boundary |
| --- | --- | --- |
| Any explicit Dolgorae-based Independent Review request, including staged changes or Task/Epic completion. | No review execution | Refuse the disabled path and guide Master to native Codex subagent review or Orca Review. Preserve the requested purpose and target in that guidance. |
| Review the staged changes with Orca, Mulgae, or an explicitly chosen native Codex subagent. | `change` | Assess the selected change in its intended context. Do not claim the entire Task or Epic is complete. |
| Review the staged candidate through an enabled route and determine whether a named Task is fully implemented. | `completion` | Assess the entire applicable Task requirement set against the index candidate, not the unstaged worktree. |
| Review whether a named completed Task or Epic was actually completed through an enabled route. | `completion` | Assess the resolved candidate and the work unit's applicable completion obligations. |
| Task handler's built-in Mulgae review. | `completion` | Assess readiness for the next authorized closeout step. |
| Epic handler's member-Task Mulgae review. | `completion` | Assess that member Task and applicable Epic constraints, not unfinished future member Tasks. |
| Epic-wide Mulgae review or Epic validator review. | `completion` | Assess all applicable member requirements and cross-Task integration. |
| Standalone request to use Mulgae to assess Task or Epic completion. | `completion` | Report the assessment without implicitly starting implementation or remediation. |

Keep these concepts separate:

| Concept | Meaning |
| --- | --- |
| Review route | Mulgae through its native integration, Orca through its native lifecycle, or an explicitly chosen host-native Codex subagent. Dolgorae-based Independent Review is disabled, not a fallback route. |
| Source scope | The exact existing backend-supported target, such as staged state or a resolved Git revision. |
| `review_purpose` | `change` or `completion`. This is a proposed semantic field, not a new native CLI flag. |
| Existing review mode | Remediation and review-budget authority, such as `remediation-eligible` or `confirmation-only`. |
| Completion checkpoint | What must be true at this point in the owning workflow. This can be described in the brief; it does not require another user-facing mode. |

Do not overload the existing `review-mode` with `change` or `completion`. Do not add a second provider pass merely to perform completion assessment. A completion review includes ordinary defect and regression review in the same authorized invocation.

Standalone review remains report-only under its current action boundaries. Embedded review retains the owning handler's approved checks, remediation, staging, and review budget. Changing the review purpose grants no additional permission to run tests, edit files, stage, commit, publish, install tools, change providers, or launch another review.

Disablement is an Aquarium routing decision, not a missing-prerequisite error. It applies to both review purposes and every Independent source scope, regardless of the installed Dolgorae version. It does not disable unrelated explicitly requested Dolgorae operations or authorize cancellation, cleanup, or recovery of existing Dolgorae work.

## 3. Establish one shared intent contract

Add a shared reference, preferably `plugins/aquarium/references/review-intent-contract.md`, and make the existing static and Mulgae review contracts reference it. Keep the common semantics there rather than duplicating a large prompt in every skill.

The contract must define purpose selection, construction of a Review Brief, requirement provenance, candidate boundaries, completion assessment, and result interpretation for enabled review routes. Temporary native Codex subagent guidance must reuse these semantics without becoming another mandatory skill or lifecycle implementation. The disabled Independent entrypoint stops before dispatch and does not invoke this contract to justify a Dolgorae call.

Backend capture, transport, provider selection, execution, recovery, publication, and settlement remain native responsibilities.

This change must not introduce a central `.aquarium` state file, a mandatory tracked review packet, a new daemon, or an Aquarium-owned replacement for native review lifecycle state.

## 4. Review Brief

### 4.1 Required information

Build a Review Brief from the current request and repository authority before an authorized dispatch through an enabled route. Use existing prompt, objective, or context inputs where they can carry it faithfully. The table defines semantics, not a mandatory native JSON schema. Do not require new producer input or output schemas when existing prompts and reports can express the requested review.

| Information | Required content |
| --- | --- |
| Purpose and identity | `change` or `completion`; Task, Epic, or explicitly scoped question when applicable. |
| Problem and intended outcome | Why the work exists and what observable behavior should result. |
| Acceptance criteria | Every applicable criterion for completion review, with its source. For change review, include the requirements relevant to the selected change. |
| Constraints and non-goals | Approved exclusions, compatibility commitments, invariants, accepted design decisions, and behavior that must remain unchanged. |
| Authority and provenance | Canonical source paths and sections, their applicable revision or approved source basis, and any explicitly approved requirement changes. |
| Candidate and context boundary | Exact native source scope and applicable revisions, included and excluded state, and relevant source or authority context available to the reviewer. |
| Completion checkpoint | Whether this is readiness before closeout or assessment of an already-claimed completed outcome, including which obligations are due now. |
| Verification evidence | Relevant checks and candidate identities, evidence the reviewer can inspect, author-reported results, unavailable evidence, and checks the review is not authorized to run. |
| Existing invocation metadata | Preserve goal revision, ordinal, review mode, role selection, and lineage where the owning workflow already requires them. |

Reuse existing requirement identifiers. When none exist, use a source path and section or local report label without creating canonical requirement IDs. Do not rewrite roadmap status or invent a new specification merely to populate the brief.

### 4.2 Recover intent without routine questioning

For embedded review, the handler supplies the approved Task or Epic context it already owns. A Task ID and review ordinal alone are insufficient.

For standalone review, inspect the explicit request, applicable instructions, canonical roadmap links, requirements, accepted decisions, and authorized existing context. Preserve any explicit target and reviewer choice. Do not guess that the most recently active Epic owns every staged change.

For a generic staged change review with incomplete intent, distinguish known requirements from inferred intent and identify the limitation. The review may assess demonstrable defects within the authorized scope without claiming requirement completeness. Ask a focused question only when unresolved ambiguity materially changes the target, transmission scope, reviewer choice, or judgment that was requested.

For completion review, an unidentified work unit or materially incomplete requirement set prevents a complete assessment. Return supported findings and the exact missing basis instead of inventing criteria or silently downgrading the request to change review.

If staged changes contain multiple purposes, describe the separate purposes supported by evidence. Do not treat them as one Task without a basis, alter the index, or split the request into extra provider calls without authority.

### 4.3 Preserve independent judgment and requirement provenance

The brief is a derived guide to authoritative sources, not a substitute for them. For completion review, the reviewer must compare the brief with the original applicable requirements and member-Task set, including criteria omitted from the brief.

Provide design rationale as evidence to evaluate. Do not tell the reviewer that the implementation is correct or ask it merely to confirm an author verdict. An authorized confirmation review may carry previous findings and the correction objective without presuming that the correction succeeded.

Distinguish the approved requirement basis from changes made to requirements in the candidate. A staged document that removes an unmet requirement does not prove that the removal was authorized. Check the accepted scope change or report an authority gap. Conversely, do not resurrect a requirement that was legitimately superseded. Apply repository-defined authority precedence and report unresolved conflicts without choosing whichever version makes the implementation pass.

Source code, tests, commit messages, and a roadmap status of `Completed` are evidence, not independent proof that every requirement is met. Existing tests must not redefine an approved requirement simply because they encode the same mistake as the implementation.

### 4.4 Keep context readable and within scope

Verify that the selected review environment can actually read the referenced sources at the stated basis. A host filesystem path that does not exist in an isolated provider workspace is not sufficient context delivery.

Distinguish the candidate being judged from contextual sources used to judge it. An approved requirements document at another revision can be context without becoming implementation evidence for the candidate. Do not silently transmit excluded source files, private conversations, credentials, raw provider transcripts, or another repository. Additional context must remain within the existing approved transmission scope or receive the required authority.

Keep the brief concise enough to use, but do not silently truncate acceptance criteria. Use native supported references or attachments when available. If native transport or readability limits prevent the required context from reaching the reviewer, disclose the exact gap. Do not add arbitrary Aquarium byte limits or bypass native bounds.

## 5. What each review purpose must do

### 5.1 Change review

Start with the selected change, identify its intended effect, and inspect related implementation, callers, contracts, and tests as needed to judge it. Check whether the change delivers its stated behavior and introduces defects or regressions.

Context inspection does not authorize an unrelated repository-wide audit. Report a pre-existing issue separately from a newly introduced defect when that distinction matters. A pre-existing issue can still be relevant when the change makes it reachable or it prevents the requested outcome.

Do not claim Task or Epic completion from a clean change review.

### 5.2 Completion review

Start with the applicable requirements and trace them to the candidate's implementation, production wiring, consumers, tests, documentation, and required artifacts. Inspect failure handling, recovery, persistence, concurrency, migrations, and operational behavior when the requirements or affected design make them relevant. Do not turn this into a universal checklist of unrelated architecture concerns.

Inspect unchanged code when it is needed to establish completion. Missing wiring, an absent module, a required migration that was never written, or an omitted acceptance test may be invisible in the diff.

For an Epic, inspect the complete applicable member-Task set and integration seams. For a member Task, identify the parent constraints that apply now and do not require future member work prematurely. A dependency genuinely required for the member Task's current acceptance remains relevant.

Embedded pre-closeout review must not reject an otherwise ready implementation merely because a later authorized step has not yet changed roadmap status or created the final commit. For an already-claimed completed outcome, inspect final artifacts and lifecycle obligations when repository authority requires them. Neither checkpoint implies push, release, deployment, or live verification unless the work unit actually requires that outcome.

### 5.3 Exact candidate rules

| Selected target | Required interpretation |
| --- | --- |
| Staged | Judge the index candidate and its change from HEAD. Unstaged code cannot satisfy a criterion, including unstaged edits to an otherwise staged path. |
| HEAD | Judge the immutable tree at the resolved HEAD, not current index or worktree bytes. |
| Commit or range | Preserve the native comparison semantics. For completion, use the resulting candidate tree as well as the diff, with the correct revisions for contextual reads. |
| Workspace or dirty | Use only the selected backend's supported native meaning and eligible files. Do not add ignored or excluded files by implication. |

The candidate's unchanged relevant files may be necessary context; an unrelated current-worktree version of those files is not an acceptable substitute. If the native target exposes only a patch and cannot support a requested completion assessment, report the limitation and resolve a supported target without silently broadening the request.

Completion review must also work for an already committed Task or Epic when there is no new diff. Do not manufacture a staged change. Orca remains limited to its supported scopes; this request does not add workspace or dirty support to Orca.

Preserve each backend's target authority. In particular, do not introduce copied checkouts, snapshots, digest bindings, or extra state-inventory requirements for Orca as a side effect of adding intent.

## 6. Findings and completion results

### 6.1 Require a reason tied to the requested review

An actionable finding must identify a violated requirement, applicable contract, or concrete correctness, security, privacy, compatibility, or data-integrity invariant. Include the triggering scenario, impact, supporting evidence, and smallest appropriate correction under the existing finding policy.

Do not restrict valid findings to the literal acceptance list. A new security defect remains relevant even when the Task did not explicitly say to avoid it. Equally, do not convert a preferred design pattern or an excluded feature into a blocking requirement.

| Observation | Expected treatment |
| --- | --- |
| A feature was intentionally removed under an approved decision. | Removal alone is not a defect. Inspect residual callers and compatibility obligations that still apply. |
| An excluded feature is absent. | Do not treat it as an unmet requirement for this work. |
| Required behavior is missing from the candidate. | Report a completion gap, even if no corresponding file was changed. |
| Unchanged code prevents the new behavior from being used. | Report the relevant integration defect with its connection to the requested outcome. |
| The implementation violates a security or persistence invariant. | Report the technical defect regardless of whether the criterion list mentions that invariant explicitly. |
| The reviewer prefers another equally valid design. | Do not report a defect without a concrete violated requirement or demonstrated problem. |

Keep existing validity, reported severity, effective priority, and disposition semantics. Distinguish validity from relevance to the selected work. Avoid expanding the current task merely to remediate unrelated findings.

### 6.2 Represent absent implementation honestly

Retain exact `path:line` evidence for findings with an actual source location. Extend the shared result contract so an omission can instead reference the violated requirement, expected implementation or integration location, and inspected evidence supporting the absence.

Do not fabricate a line number, a missing file, or a provider finding ID. A limited search alone does not establish that an implementation is absent; describe the scope actually inspected and use an unverified assessment when evidence is insufficient.

If a backend's native finding schema cannot represent an omission, report it through supported requirement-assessment output or request a producer-owned schema change. Do not force it into an invalid native finding record. Link overlapping findings and requirement gaps without double-counting them or discarding their native identities.

### 6.3 Return a requirement assessment for completion review

Return one assessment for every applicable criterion, with at least the criterion source, implementation or absence evidence, verification evidence, assessment, and remaining gap. Suggested semantic assessments are `met`, `unmet`, `unverified`, and `not-applicable`; native schema names remain the producer's decision.

`met` is limited to the stated assessment boundary and evidence. `not-applicable` requires a reason grounded in the work's scope or checkpoint. Neither value may be used to hide an unread criterion or an unavailable required check.

Example only:

| Criterion | Candidate evidence | Verification evidence | Assessment |
| --- | --- | --- | --- |
| Preserve the existing default timeout. | Default branch is present. | Applicable test result is available for this candidate. | Met within the stated evidence boundary. |
| Apply one deadline across retries. | Each retry creates a fresh deadline. | No new execution performed. | Unmet based on code evidence. |
| Cancel in-flight work on expiry. | Cancellation wiring is present. | Required runtime evidence is unavailable. | Static support found; runtime completion remains unverified. |
| Reject non-positive configuration. | No validation path was found in the inspected entrypoints. | Relevant test is absent. | Unmet if the inspected paths establish the omission; otherwise unverified. |

A zero-finding report is not a requirement assessment. The coordinator must not label its own later audit as a provider-produced assessment. Reuse supported provider reports where they carry the requested result; do not assume a new structured result already exists.

### 6.4 Separate verdicts and preserve evidence limits

Report technical findings, requirement assessment, verification coverage, and backend lifecycle status separately. Explain the overall answer in terms of the requested purpose and checkpoint.

For completion review, missing required assessments, unresolved requirement gaps, or unavailable mandatory evidence prevent an unqualified completion approval. Technical cleanliness alone must not be presented as proof of completion. Preserve the native technical verdict and explain the limitation rather than rewriting native status.

Orca and the temporary native Codex subagent review remain static and report-only. Dolgorae-based Independent Review performs no review while disabled. Reading test code is not running it. An author's statement that tests passed is not independently observed execution. Inspect existing authorized evidence and identify its provenance and candidate relevance; do not rerun checks merely to fill the table. Embedded workflows may use checks only within their existing authorization.

Do not repurpose Mulgae `coverage_status`, `publication_status`, `ci_decision`, or extraction status to mean requirement completeness. Native role coverage, operational success, code findings, and semantic completion are separate facts. Preserve existing Low disposition and stale-review rules; a matrix does not erase findings or grant another provider round.

## 7. Mulgae changes

### 7.1 Embedded reviews

Update `task-review`, Task handler handoffs, Epic member reviews, and whole-Epic review callers to provide the actual Review Brief, not just an identifier-based objective. Preflight and execution must use the same approved target, objective/context, roles, and invocation metadata.

Use Mulgae's supported objective or other native context mechanism first. Inspect the admitted producer contract before selecting an encoding or adding fields. Verify that the substantive brief reaches the external provider, not merely Mulgae's outer command metadata.

All selected roles need the same applicable work context. Define responsibility for complete requirement assessment within the authorized native review arrangement so no role assumes another role covered the missing criteria. Do not automatically add a provider, force a particular role name, or launch another review. If the configured arrangement cannot provide the requested coverage, report that limitation and resolve it through existing authority.

Consume the requirement assessment alongside native findings and independently adjudicate both. Preserve the existing handler-owned verification and Epic audit; provider assessment complements those checks and does not replace them.

The current inspected consumer contract admits Mulgae v0.1.21 and current command-result v8. Retain those adopted native contracts, including recovery and rate-limit distinctions. Verify the supported producer contract again during implementation rather than restoring older v6 assumptions from earlier discussion.

### 7.2 Standalone Mulgae completion requests

Document how the existing Aquarium entrypoints and shared contract handle an explicit standalone Mulgae Task or Epic completion request. Do not assume that changing the embedded handlers also changes direct use of the separately installed `$use-mulgae` skill.

The coordinating Aquarium path must build the same brief and consume the same completion result while delegating execution to `$use-mulgae`. Keep direct `task-review` scoped to its supported Task identity. Do not route an Epic request into a Task-only interface or automatically invoke the mutating `epic-validator` workflow to obtain report-only behavior.

A new `mulgae-review` skill is not required by this request. If a new entrypoint is needed, justify it through the repository's design process instead of creating an undocumented alias. Any necessary changes to the producer-owned paired skill belong in an explicit external handoff.

### 7.3 Result and handoff compatibility

The initial Aquarium implementation consumes Mulgae v0.1.21's accepted Markdown
role reports. Each selected role assesses the criteria applicable to that role,
and the coordinator aggregates those assessments conservatively. A criterion
that no accepted report addresses remains `unverified`. A new machine-readable
Mulgae assessment schema is not a prerequisite. If later work needs one, treat
it as a separate producer-owned handoff.

Inspect native accepted reports, extraction, and evidence resources before promising additional structured requirement output. If the existing output cannot preserve a later required assessment, identify a Mulgae-owned change and coordinate it explicitly.

Reconcile the new result with the current bounded orchestrator handoff in `task-review`, which limits finding records and excludes raw descriptions and provider payloads. Preserve private native reports. Add only the necessary safe requirement identifiers, assessment summaries, unresolved counts, and supported references at the canonical handoff owner. Do not copy the full provider transcript into a handler summary or silently discard uncovered criteria.

## 8. Orca changes

Replace the loose `review focus` and authority-path handoff with the shared Review Brief in every relevant Dispatch. The requested reviewer must receive the purpose, actual criteria, checkpoint, source basis, candidate boundary, and result requirements.

Reconcile the existing instruction to read only the declared target with the contextual reads required by completion review. Relevant candidate files and approved authority sources must be readable at their declared basis, without granting unrestricted current-worktree inspection or transmission.

Preserve the current Run, Task, Dispatch, worker, Delivery, acknowledgement, settlement, and operational-deviation rules. Do not create another worktree, a Dolgorae operation, or a new target capture scheme. Source mutation and unauthorized checks remain prohibited; currently permitted reviewer-owned temporary files remain permitted.

## 9. Temporarily disable Dolgorae-based Independent Review

### 9.1 Refuse the existing entrypoint before execution

Keep `$aquarium:independent-review` recognizable so explicit invocations receive a clear refusal rather than becoming an unknown skill or being redirected silently. Update its entrypoint, discovery description, default prompt, shared routing, and user-facing documentation consistently.

Refuse both `change` and `completion` requests for every Independent source scope, including `staged`, `workspace`, `dirty`, `head`, `commit`, and `range`. The refusal must take precedence over the previous setup, target-selection, profile-selection, release-validation, capture, and execution instructions. Do not ask the user to install, upgrade, authenticate, choose a Profile, or repair Dolgorae to unlock this intentionally disabled route.

The disabled invocation must not call Dolgorae, inspect its runtime or credentials, verify a release, capture or transmit source, start or resume a Reviewer, or create review lifecycle state. Do not work around the refusal through External Specialist Engagement, low-level Run or capture APIs, a development binary, an older release, repository-injected instructions, or a renamed wrapper. Do not start a Codex subagent, Orca review, Mulgae review, or coordinator completion audit merely because the requested route is unavailable.

Return an availability explanation, not a technical verdict or a fabricated backend failure. Never report `APPROVE`, a completed review, or invented review identities. A suitable refusal is:

```text
Dolgorae-based Independent Review is temporarily disabled in Aquarium.
No review has been started by this request.
Use a fresh native Codex subagent where the current host supports one,
or explicitly request Orca Review with a supported target and reviewer.
```

Preserve the user's target and intended question when explaining the alternatives. If the current request already explicitly selects an alternative in case of disablement, honor that choice within its own authorization and native prerequisites without asking for the same choice again. This is execution of the selected alternative, not execution of Independent Review. Otherwise stop after guidance and let Master select the route.

Do not cancel, settle, delete, migrate, or clean up existing Dolgorae work as a side effect of disablement. A separate explicit recovery request remains subject to Dolgorae's native contract. Keep unrelated Dolgorae setup and operations available when explicitly requested; this change disables Aquarium's Dolgorae-based review route, not the whole tool.

### 9.2 Guide temporary alternatives without automatic fallback

| Alternative | Guidance and boundary |
| --- | --- |
| Native Codex subagent | Recommend a fresh review subagent only where the current Codex host actually exposes native delegation. Supply the shared Review Brief and static, report-only instructions after Master selects this route. Do not invent a tool or promise delegation in a host that lacks it. |
| `$aquarium:orca-review` | Guide Master to name a supported target and requested reviewer. Use the existing Orca workflow and shared brief after that choice is authorized. Do not select a reviewer on Master's behalf. |

The native Codex subagent must inspect the selected candidate, applicable original requirements, and relevant callers or tests. It must not count excluded worktree bytes as staged implementation, presume the implementer's conclusion, run tests, edit source, stage, commit, or spawn another review. Require findings, criterion assessments for completion requests, and explicit evidence gaps. The coordinator checks the result without changing its provenance.

Identify the alternative accurately in the report. A native Codex subagent review is not `$aquarium:independent-review`, Dolgorae review, or Orca review. Use the host's actual lifecycle and available evidence; do not claim immutable capture, settlement, or other guarantees that the host did not provide. Do not add a mandatory `codex-review` skill, new daemon, persistent state owner, or synthetic native result schema for this temporary guidance.

Example requests that the refusal may offer as guidance, not execute:

```text
Use a fresh native Codex subagent to assess whether TASK-042 is complete
in the staged candidate. Include the approved requirements and return
findings, criterion assessments, and evidence gaps. Review only; do not
run tests or change files.

Use $aquarium:orca-review with Claude to assess whether TASK-042 is
complete in the staged candidate. Review only; do not run tests or
change files.
```

`TASK-042` and `Claude` are examples, not default selections. Preserve actual user selections and check only the chosen route's prerequisites. Orca still does not support `workspace` or `dirty`; do not stage files or reinterpret those scopes to make the alternative fit. Explain that limitation and resolve an explicitly authorized supported route or target. If native Codex delegation is unavailable, report it rather than substituting a different mechanism silently.

### 9.3 Keep Dolgorae work and re-enablement outside this request

Master will resolve Dolgorae's design separately. Remove the earlier requirement to extend Dolgorae's checked input/output contracts as a dependency of this Aquarium change. Do not modify the Dolgorae repository, its paired skill, protocols, releases, or installation as part of this work, and do not prescribe a replacement Dolgorae architecture here.

Completion of this request requires the disabled entrypoint and alternative guidance to work, not Dolgorae support to be restored. A future Dolgorae release, a successful capability probe, or a repaired local installation must not automatically re-enable Independent Review. Re-enablement requires a separate explicit Aquarium change requested by Master and verification of the selected integration at that time.

Existing Dolgorae contract material may remain for separately requested operations or historical reference, but active review instructions and discovery surfaces must not offer it as a runnable or fallback review path. Add no runtime switch that silently bypasses the temporary disablement.

During the disablement, Dolgorae remains an optional supported global component.
Its absence must not fail common production-binary readiness, while explicitly
requested setup and operations remain available under their existing authority
boundaries.

## 10. Owners and affected files

Inspect current owners before editing. This table identifies likely change locations, not permission to modify every file regardless of need.

| Owner or path | Required responsibility |
| --- | --- |
| New `plugins/aquarium/references/review-intent-contract.md` | Own shared purpose, brief, provenance, checkpoint, and completion semantics. |
| [Static review contract](../../plugins/aquarium/references/review-contract.md) | Reference the shared intent contract for enabled routes; reconcile context reads and results, and make Independent disablement take precedence over its former execution rules. |
| [Finding disposition](../../plugins/aquarium/references/finding-disposition.md) | Preserve severity and authority; account for requirement gaps without fake source locations or silent scope expansion. |
| [Mulgae contract](../../plugins/aquarium/references/mulgae-review-contract.md) | Own Aquarium context delivery and result consumption without taking over native lifecycle. |
| [Dolgorae consumer contract](../../plugins/aquarium/references/dolgorae-review-contract.md) | State that Aquarium Independent Review is disabled; retain other material only where still applicable. Do not introduce a producer-extension or automatic re-enablement requirement. |
| [Independent skill](../../plugins/aquarium/skills/independent-review/SKILL.md) and its `agents/openai.yaml` | Retain the recognizable entrypoint, refuse before prerequisites or execution, and guide native Codex subagent or Orca alternatives. Update metadata so discovery does not advertise an enabled path. |
| [Orca skill](../../plugins/aquarium/skills/orca-review/SKILL.md) | Deliver the brief through Dispatch and consume the purpose-specific result. |
| [Task review](../../plugins/aquarium/skills/task-review/SKILL.md) and [Task handler](../../plugins/aquarium/skills/task-handler/SKILL.md) | Supply Task criteria and checkpoint; return a safe, usable requirement assessment. |
| [Epic handler](../../plugins/aquarium/skills/epic-handler/SKILL.md) and [Epic validator](../../plugins/aquarium/skills/epic-validator/SKILL.md) | Supply member or whole-Epic context and preserve independent direct-audit responsibilities. |
| [Evidence residency](../../plugins/aquarium/references/evidence-residency.md) and downstream handoffs | Resolve any necessary schema or residency changes without promoting private review payloads. |
| Capability, workflow, integration, setup-routing, and public documentation | Distinguish enabled reviews from disabled Independent Review. Remove guidance that routes users to the disabled path, including workspace/dirty recommendations. Do not classify disablement as a broken installation. |
| Temporary native Codex subagent guidance in the shared reference and refusal | Reuse the Review Brief under actual host capabilities and explicit user choice without introducing another backend implementation. |
| Dolgorae producer work | Outside this request. Master owns the separate correction and any later request to restore Aquarium integration. |
| Mulgae producer contract, only if an enabled-path capability is genuinely missing | Reuse existing prompt and report mechanisms first; identify any unavoidable producer-owned change through a separate authorized handoff. |

Change Procedure sources and their installed copies only where the semantic contract requires it. Preserve existing operation identities, routing, budgets, and immutable session snapshots unless a separately justified contract change is necessary. Do not duplicate the complete brief or assessment in roadmap prose or Procedure history by default. Use existing evidence residency and supported references.

## 11. Delivery sequence

Complete the Aquarium work in this order. Dolgorae correction is not a prerequisite and must not block delivery of the requested disablement and enabled review improvements.

| Step | Work | Exit condition |
| --- | --- | --- |
| 1 | Disable the Independent entrypoint and update its immediate routing and discovery surfaces. | Explicit requests refuse before any Dolgorae operation or alternative launch and explain the temporary alternatives. |
| 2 | Define the common intent contract for enabled reviews. | Purpose, brief, provenance, candidate, checkpoint, result, and authority rules are consistent. |
| 3 | Update Mulgae callers and Orca Dispatch/result handling using existing native interfaces. | Actual reviewer input and returned assessments support the requested scenarios; genuine enabled-path limitations are identified without inventing native fields. |
| 4 | Add temporary native Codex subagent guidance and complete alternative routing documentation. | Explicit user choices retain their target and purpose; unavailable delegation and unsupported Orca scopes are handled honestly. No automatic fallback or new backend is introduced. |
| 5 | Validate scenarios and reconcile canonical and public documentation. | Enabled behavior and Independent refusal match the documented state, with checks and evidence limits reported. |

Deliver under the normal release policy. Intentional Independent disablement is the required outcome, not partial implementation waiting for Dolgorae. Do not claim equivalent availability or guarantees across the enabled routes and the disabled entrypoint. Any unresolved requirement of an enabled route still needs an honest completion report.

## 12. Verification

### 12.1 Deterministic checks

Test actual executable behavior where code is added or changed: input validation, context delivery through enabled routes, omitted or invalid fields, candidate selection, result interpretation, and preservation of existing lifecycle identities. Where executable routing exists, test that a disabled Independent request makes no Dolgorae, setup, source-transmission, or alternative-review call. Do not introduce runtime code merely to make a skill-only refusal testable.

Use existing native producer tests for producer-owned behavior when relevant to enabled routes. This request does not require new Dolgorae tests or live Dolgorae calls. A mock provider can prove that a brief was delivered; it cannot prove that a real model interpreted the requirements correctly.

Keep Aquarium validation focused on objective structure, references, data, and executable helpers. Do not add prose matching, exact prompt-string assertions, or automated LLM evaluations to `make test` as substitutes for functional verification. Run the repository-required focused checks and diff integrity checks for the actual changes.

### 12.2 Functional acceptance scenarios

Use controlled examples for the following checks. Review-execution cases apply to enabled routes; Independent cases verify refusal and guidance instead. Execute checks only through an authorized verification workflow; this request does not grant additional production review calls.

| Scenario | Expected behavior |
| --- | --- |
| Generic staged review with a documented purpose | The reviewer receives the purpose and evaluates the change without claiming whole-Task completion. |
| Staged changes with no reliable business intent | The limitation is explicit; no invented requirements or automatic Epic assignment. |
| Completion review with no new diff | The committed candidate is assessed without staging files or manufacturing changes. |
| Approved feature removal | The removal is not itself a defect; actual residual-call or compatibility defects remain reportable. |
| Missing feature declared as a non-goal | It does not block this work's completion. |
| Required production wiring was never changed | Completion review identifies the omission outside the diff. |
| Required implementation exists only unstaged | Staged completion remains unmet; worktree bytes do not make the index pass. |
| Brief accidentally omits a canonical criterion | The reviewer checks the original authority and identifies the omitted requirement. |
| Candidate deletes an unmet requirement without approved scope change | The review reports the unapproved change or unresolved authority instead of approving the reduced scope. |
| Requirement was legitimately superseded | The reviewer applies the approved current basis rather than reviving obsolete behavior. |
| Member-Task review before later member Tasks | Only obligations due for the current member are required; genuine current dependencies still matter. |
| Embedded review before authorized closeout | A pending terminal status or final commit is not reported as premature implementation failure. |
| Security defect absent from the acceptance list | The concrete invariant violation is still reported. |
| Missing implementation has no code line | The requirement and inspected evidence identify the gap without a fabricated location. |
| Static support exists but required runtime proof is absent | Static findings and the missing verification are reported separately; completion is not overstated. |
| Mulgae has complete native role coverage but an unread criterion | Native success does not become semantic completion approval. |
| Existing native output cannot preserve a completion table | The capability gap is disclosed; the coordinator does not invent provider output. |
| Explicit Independent staged change review | The request is refused before prerequisites, capture, source transmission, or provider work; alternatives are guidance only. |
| Explicit Independent Task/Epic completion review | The same refusal applies without a coordinator audit, fabricated result, or automatic fallback. |
| Independent request selects workspace, dirty, HEAD, commit, or range | Disablement applies regardless of source scope; no scope is treated as an exception. |
| Dolgorae is upgraded or its design is repaired later | Independent remains disabled until a separate explicit Aquarium re-enablement change. |
| Master has not selected an alternative | Neither Codex delegation nor Orca, Mulgae, setup, or review lifecycle work is launched. |
| Master explicitly selects native Codex subagent review | A fresh actually available native subagent receives the shared brief; the report identifies the real route and does not claim Dolgorae guarantees. |
| Native Codex delegation is unavailable | The limitation is disclosed and a supported alternative is explained without inventing tools or silently switching routes. |
| Master explicitly selects Orca as the alternative | The selected reviewer, purpose, and supported target are preserved under the Orca contract; an already explicit choice is not requested again. |
| Disabled Independent request originally targeted workspace or dirty | Guidance does not claim Orca supports that scope, stage files, or silently substitute staged or HEAD. |
| Dolgorae work already exists when Independent is disabled | Refusal does not resume, cancel, settle, delete, or otherwise alter that work. |
| Standalone Mulgae Epic completion request | The shared contract is actually loaded and the result is report-only without starting a handler. |
| Requirements or candidate change after review | The previous assessment remains bound to its original basis; affected evidence is not relabeled current. |

Compare representative findings before and after the change where useful. Record whether irrelevant findings were reduced and required omissions were still found. Do not promise a percentage improvement or treat one clean sample as proof of general accuracy.

## 13. Example Review Brief

The following is illustrative request content, not a claim that these native field names or identifiers already exist.

```text
Review purpose: completion
Work unit: <task-id>
Checkpoint: implementation ready for the existing closeout step
Candidate: the staged index candidate and its HEAD-to-index change
Excluded: unstaged edits and unrelated work

Problem:
Requests currently have a fixed timeout. The approved work makes the
request deadline configurable without changing the public API.

Acceptance criteria:
- Preserve the existing 30-second default when configuration is absent.
- Apply one configured deadline to the initial request and all retries.
- Cancel in-flight work when that deadline expires.
- Reject zero and negative configuration values.

Constraints and non-goals:
- Preserve the existing public API.
- Do not introduce a replacement asynchronous request engine.
- Final commit creation is a later authorized workflow step.

Authority:
- <canonical-task-source and section at its applicable basis>
- <approved-design-source and section>
- <existing-public-API-contract and section>
- No approved change to these criteria has been identified.

Evidence:
- Read existing code and tests from the declared candidate.
- <references to available authorized test evidence, if any>
- Author-reported checks remain labeled as author-reported.
- This review does not authorize running additional checks.

Requested assessment:
Review actionable defects and regressions. Independently check every
criterion against the original authority and candidate, including
unchanged integration code and absent implementation. Return supported
findings, criterion assessments, and remaining evidence gaps. Do not
assume the implementation is correct or prescribe unrelated features.
```

## 14. Completion checklist and implementation handoff

- [ ] Enabled Mulgae and Orca reviews use the same documented purpose and brief semantics; temporary native Codex subagent guidance reuses them.
- [ ] Dolgorae-based Independent Review is explicitly disabled for every scope and both purposes, with refusal preceding prerequisites, source transmission, and execution.
- [ ] The refusal guides alternatives without launching them, and separately authorized alternative choices preserve the requested target, purpose, and actual route identity.
- [ ] Embedded review receives substantive approved goals and criteria rather than only work-unit IDs.
- [ ] Standalone staged and Task/Epic requests route correctly, including standalone Mulgae use.
- [ ] The external reviewer receives readable authority and context, not merely a coordinator-side summary retained after dispatch.
- [ ] Completion assessment examines the full applicable candidate and can identify work missing from the diff.
- [ ] Requirement provenance, approved scope changes, non-goals, and completion checkpoints affect judgment correctly.
- [ ] Results distinguish findings, requirement coverage, verification limits, and backend lifecycle.
- [ ] Omission reporting and safe handoffs work without fake native fields, line numbers, findings, or evidence.
- [ ] Dolgorae modification and re-enablement are outside this request; an upgrade or capability change cannot restore the disabled route automatically.
- [ ] Existing scope, security, remediation, review-budget, Low settlement, and lifecycle boundaries remain intact.
- [ ] Deterministic tests and manual skill checks are reported separately, with unavailable or unperformed checks identified.
- [ ] Public and canonical documentation claim only the behavior actually delivered.

The implementation report must identify the changed canonical owners, enabled behavior for Mulgae and Orca, Independent refusal behavior, temporary Codex subagent guidance and host limits, any genuine enabled-path native dependency, checks performed and their scope, remaining manual verification, and unresolved blockers. Do not report Independent as operational or list Dolgorae repair as unfinished work required by this request. Report partial completion honestly for enabled-path requirements. Do not declare this request complete while an enabled route's required brief is not reaching its reviewer, a completion verdict is inferred solely from zero findings, or the disabled entrypoint can still launch review work.
