# Review Intent Contract

Use this contract whenever an enabled Aquarium route asks a reviewer to assess a change or completion, and for the disabled `$aquarium:independent-review` entrypoint's refusal and routing decision. It defines the intent supplied to the reviewer and the completion fact consumed by Aquarium. Embedded Task, Epic, and validation workflows also read [review-routing-contract.md](review-routing-contract.md) for selection, route-neutral evidence, switching, and waiver semantics. It does not replace a backend's capture, transport, provider selection, execution, recovery, publication, or settlement contract.

## Select the purpose

Every review has one purpose:

- `change` asks whether the selected change delivers its intended effect without actionable defects or regressions. It cannot establish that a whole Task or Epic is complete.
- `completion` asks both whether the candidate has actionable defects or regressions and whether the named Task, Epic, or bounded requirement set is fully satisfied at the current checkpoint.

Purpose does not change the selected source scope, native review mode, remediation budget, or authorization. It grants no additional permission to run checks, edit files, stage, commit, publish, install, change providers, or launch another review.

## Route a disabled Independent Review request

The disabled `$aquarium:independent-review` entrypoint owns only its refusal and routing decision. Apply this matrix before any discovery, setup, source handling, provider contact, or review launch:

| Explicitly preselected supported alternative | Result |
| --- | --- |
| None | Explain the refusal and available alternatives; launch nothing. |
| Exactly one Orca route | Preserve the original target and review question, validate the requested reviewer and supported target, then invoke `$aquarium:orca-review` under its own contract. |
| Exactly one native Codex route | Preserve the original target and review question. Use a fresh host-native review subagent only when the host exposes native delegation; otherwise report the unavailable route and stop without fallback. |
| More than one alternative | Ask the user to choose exactly one route; launch nothing. |

The selected route owns execution, source handling, lifecycle, evidence, and result. The disabled entrypoint adds no fallback, translation, or backend guarantee.

## Build the Review Brief

Before an authorized dispatch through an enabled route, build one concise Review Brief from the current request and repository authority. Existing prompt, objective, context, reference, or attachment inputs may carry it; this contract does not require a new native schema.

| Field | Required content |
| --- | --- |
| Purpose and identity | `change` or `completion`, plus the Task, Epic, or bounded question when applicable. |
| Problem and outcome | Why the work exists and the observable result it should produce. |
| Acceptance criteria | Every applicable criterion for completion review, with its source; for change review, the requirements relevant to the selected change. |
| Constraints and non-goals | Approved exclusions, invariants, compatibility commitments, accepted decisions, and behavior that must remain unchanged. |
| Authority and provenance | Canonical source paths and sections, their revision or approved basis, and any explicitly approved requirement changes. |
| Candidate and context | The exact native source scope and revisions, included and excluded state, and contextual sources available to the reviewer. |
| Completion checkpoint | Readiness before closeout or assessment of an already claimed outcome, including the obligations due now. |
| Verification evidence | Relevant checks, candidate identities, unavailable evidence, author-reported results, and checks the reviewer may not run. |
| Invocation metadata | Existing goal revision, ordinal, review mode, selected roles, and lineage required by the owning workflow. |
| Requested result | Findings and limitations for `change`; findings, every criterion assessment, and evidence gaps for `completion`. |

Reuse existing requirement identifiers. When none exist, cite a source path and section or a local report label without creating a canonical identifier. The brief is a guide to authoritative sources, not a replacement for them.

## Use a native Codex review subagent

Use a fresh host-native Codex subagent only after the user explicitly selects
that review route and the current host exposes native delegation. Give it the
same Review Brief, exact target, and approved context that another enabled
static route would receive. Do not invent a delegation tool or silently choose
Orca, Mulgae, or another backend when native delegation is unavailable.

The subagent review is static and report-only. Require it to inspect the
selected candidate, the applicable original requirements, and relevant callers,
contracts, or tests without running checks, editing files, changing Git state,
or spawning another review. For `completion`, require findings, one assessment
for every applicable criterion, and explicit evidence gaps. For `change`,
require findings and limitations without claiming whole-work-unit completion.
The coordinator verifies the result while preserving subagent and coordinator
evidence as separate provenance.

Use only the lifecycle and evidence the host actually provides. Do not describe
this route as Independent Review, Dolgorae, Orca, or Mulgae, and do not claim an
immutable capture, publication, settlement, or recovery guarantee that was not
observed. If the host cannot provide a fresh subagent or the selected target
cannot be bounded, report that limitation and stop without automatic fallback.

## Recover intent and provenance

An embedded handler supplies the approved Task or Epic context it already owns. A Task ID and review ordinal alone are insufficient. A standalone workflow inspects the explicit request, applicable instructions, canonical roadmap links, accepted decisions, and authorized context. It must not infer that the most recently active Epic owns every staged change.

For incomplete generic change intent, distinguish known requirements from inferred intent and disclose the limitation. The reviewer may still identify demonstrable defects without claiming requirement completeness. Ask a focused question only when unresolved ambiguity materially changes the target, transmission scope, reviewer choice, or requested judgment. An unidentified work unit or materially incomplete requirement set prevents an unqualified completion assessment; return supported findings and the missing basis instead of inventing criteria or silently converting the request to change review.

When staged changes contain multiple purposes, describe the separate purposes supported by evidence. Do not collapse them into one Task without a basis, alter the index, or split the request into additional provider calls without authority.

Preserve independent judgment. Supply rationale as evidence, but never ask the reviewer to accept the implementer's conclusion. A candidate that edits or removes its own requirement does not prove that the change was authorized. Apply repository authority precedence and distinguish approved requirement changes from candidate assertions. Source code, tests, commit messages, and lifecycle labels are evidence, not independent proof of completion.

## Preserve candidate boundaries

| Target | Interpretation |
| --- | --- |
| Staged | Judge the index candidate and its transition from HEAD. Unstaged bytes cannot satisfy a criterion. |
| HEAD | Judge the immutable resolved HEAD tree, not current index or worktree bytes. |
| Commit or range | Preserve native comparison semantics and use the resulting candidate tree for completion context. |
| Workspace or dirty | Use only the selected backend's supported native meaning and eligible files. |

Relevant unchanged files may be context, but an unrelated current-worktree version cannot substitute for a revision-bound candidate. Do not manufacture a staged change for an already committed completion review. Preserve each backend's target authority; adding intent does not authorize copied checkouts, alternate snapshots, digest bindings, or extra inventory.

If a native target exposes only a patch and cannot support the requested completion assessment, report the exact limitation and resolve a supported target without silently broadening the request.

Referenced sources must be readable in the selected review environment. A host-only path is not delivered context for an isolated provider. Additional context stays within the approved transmission scope and excludes credentials, private conversations, raw provider transcripts, and other repositories unless separately authorized. Do not silently truncate acceptance criteria or invent Aquarium-only byte limits.

When a transport or readability limit makes original authority or required evidence unavailable in the selected review environment, disclose the exact omitted context. Mark a criterion `unverified` when that omission prevents a supported assessment from the evidence the reviewer can read. If readable evidence already establishes a concrete gap, assess the criterion as `unmet` under the rules below. A Review Brief omission alone does not affect the assessment when the reviewer can independently read the original authority and applicable evidence. A coordinator summary of material the reviewer cannot read remains coordinator evidence and does not establish provider or role coverage.

## Assess change and completion

For `change`, inspect the intended effect plus relevant implementation, callers, contracts, and tests. Separate pre-existing issues from defects introduced or made reachable by the change. Do not expand into an unrelated repository-wide audit.

For `completion`, start with the applicable requirements and trace them to implementation, production wiring, consumers, tests, documentation, and required artifacts. Inspect unchanged code when needed to detect missing wiring, modules, migrations, recovery, or acceptance evidence. For an Epic, cover every applicable member requirement and integration seam. For a member Task, apply current parent-Epic constraints without requiring unfinished future members prematurely.

Every enabled completion reviewer must reconcile the Review Brief's criterion set with the named work unit's original authority and applicable member requirements. Assess a reconciled requirement omitted from the brief as `met`, `unmet`, `unverified`, or `not-applicable` from the readable evidence. Mark it `unverified` only when the requirement is unreadable, its conflict remains unresolved, or the available evidence is insufficient. Neither the brief nor a coordinator summary may narrow the authoritative completion basis silently.

A pre-closeout review does not reject ready work merely because an already authorized later step has not yet changed lifecycle state or created the commit. An already-claimed completed outcome includes final artifacts and lifecycle obligations required by repository authority. Neither checkpoint implies push, release, deployment, or live verification unless the work unit requires it.

## Assign criterion responsibility

Before dispatch, map every applicable criterion to at least one responsibility in the already authorized reviewer arrangement. A single reviewer owns all criteria unless an explicit narrower responsibility map says otherwise. For Mulgae, assign criteria across the selected roles and aggregate their accepted Markdown reports conservatively. Do not add roles or provider calls merely to fill a gap.

Each criterion assessment is one of these Aquarium states, which are not new native backend fields:

- `met`: sufficient readable evidence supports the criterion.
- `unmet`: evidence shows the criterion is not met.
- `unverified`: required evidence or responsibility coverage is missing or inconclusive.
- `not-applicable`: the applicable authority, approved scope, or current checkpoint establishes that the criterion does not apply.

Conflicting accepted assessments resolve to `unmet` when any evidence establishes a real gap; otherwise they remain `unverified` until the conflict is resolved. Silence is never `met`. Multiple role reports do not constitute a vote, and a majority cannot erase a supported gap.

Coordinator-authored evidence retains coordinator provenance. It may explain context, map requirements, or support local adjudication, but it never counts as provider evidence, an accepted role report, or coverage by a responsibility assigned to a reviewer.

When a report assesses only part of a compound criterion, retain the supported evidence and keep the unassessed remainder `unverified`; a label for the assessed part cannot make the whole criterion `met`. When multiple reports describe the same semantic finding or criterion gap, preserve their native report identities and finding-specific dispositions but count the shared issue once in the aggregate assessment. Deduplication never discards distinct evidence, remaining gaps, or dispositions.

## Interpret results

An actionable finding identifies a violated requirement, applicable contract, or concrete correctness, security, privacy, compatibility, or data-integrity invariant, with scenario, impact, evidence, and an appropriate correction. Missing required implementation may cite the violated requirement, expected location, and inspected evidence rather than fabricating `path:line` evidence.

Keep native technical findings, criterion assessments, verification coverage, and backend lifecycle facts separate. The aggregate completion assessment is an Aquarium-consumed fact, not a rewrite of native status. It retains work-unit identity, purpose, checkpoint, candidate, criterion identities and sources, assigned review responsibility, implementation or absence evidence, verification evidence, assessment states, evidence and reviewer or coordinator provenance, accepted report identities, remaining gaps, and counts needed by the owning decision.

Completion is supported only when every applicable criterion is `met` or legitimately `not-applicable`, mandatory evidence is available, and existing verification, finding-disposition, lifecycle, and authorization conditions independently pass. Any `unmet` criterion is a completion gap. Any `unverified` criterion prevents an unqualified completion approval. A technically clean result cannot compensate for missing requirements, and a complete requirement assessment cannot waive a technical finding.

Apply the same aggregate decision at initial approval, after eligible Low settlement, member-Task goal assessment, and whole-Epic validation. Standalone review reports the assessment without implementing or remediating it; embedded workflows route it through their existing decisions and budgets.
