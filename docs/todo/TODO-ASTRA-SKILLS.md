# Aquarium skill modernization for GPT-6 Astra

## Purpose and authority

This dossier is the temporary execution SOT for `EPIC-012`. It adopts the Aquarium
portion of the workspace proposal `../new-skills.md` (relative to the Aquarium
repository root), with Master's direction to consume updated local tool sources even
when those tools have not been released. The adopted requirements are included here so
execution does not depend on that external proposal remaining available.

Master approved the Sanho team's scope refinements and an Aquarium addition to
record confirmed Sanho non-use in project guidance. That addition extends
TASK-045 and TASK-046 without expanding Aquarium's source-edit ownership into
the tool repositories. `EPIC-009` and `TASK-047` now own immediate adoption of
Sorage's explicit-request workflow. TASK-046 retains the Sorage regression
scenarios for the complete skill integration.

The [roadmap](../roadmap/README.md#epic-012-modernize-aquarium-skills-for-gpt-6-astra)
alone owns IDs, ordering, dependencies, and lifecycle state. This dossier owns scope,
task requirements, source inspection, acceptance, and handoff requirements. The
repository's [documentation authority](../README.md), [AGENTS.md](../../AGENTS.md), and
[distinct-effect approval
contract](../architecture-decision-records/0005-separate-effect-approvals.md) remain
authoritative. Skill entrypoints, shared references, and each tool's native contracts
continue to own supported behavior.

The goal is to reduce unnecessary instruction loading, repeated investigation, redundant
verification, and repeated questions. The initial audit covered 25 Aquarium entrypoints
and six paired skill entrypoints. Inspect the current source before each task to
identify the remaining gap and preserve newer improvements, including authorization
reuse and proportionate verification guidance. Do not restore an older baseline to
reproduce an audit finding. No measured token, latency, or runtime performance
improvement is promised.

| Aquarium task | Proposal label | Deliverable |
| --- | --- | --- |
| TASK-043 | SKILL-01 | Concise Aquarium discovery descriptions |
| TASK-044 | SKILL-02 | Focused entrypoints and conditional reference loading |
| TASK-045 | SKILL-03 plus approved guidance changes | Evidence reuse and Sanho non-use guidance |
| TASK-046 | SKILL-09 plus approved guidance scenarios | Integration and manual acceptance |

The tool work remains in its owning repositories. This epic does not implement
`SKILL-04` through `SKILL-08`, install or activate their sources, or publish tools.
Registration authorizes no skill implementation, provider execution, staging, commit,
release, installation, activation, or publication.

## Local source intake

At epic intake, read the current skill entrypoints and linked references in every
repository below before proposing Aquarium changes. Repository paths are relative to the
Aquarium repository root; skill paths are relative to their owning root.

| Owner | Local repository | Skill sources | Proposal label |
| --- | --- | --- | --- |
| Aquarium | `.` | `plugins/aquarium/skills/` | SKILL-01, SKILL-02, SKILL-03, SKILL-09 |
| Gaori | `../../dolgorae/gaori` | `skills/use-gaori/`, `skills/use-gaori-status/` | SKILL-04 |
| Mulgae | `../../dolgorae/mulgae` | `skills/use-mulgae/` | SKILL-05 |
| Podway | `../../dolgorae/podway` | `skills/use-podway/` | SKILL-06 |
| Sanho | `../../dolgorae/sanho` | `skills/use-sanho/` | SKILL-07 |
| Sorage | `../../dolgorae/sorage` | `skills/use-sorage/` | SKILL-08 |

Use these updated local source trees as the integration baseline. Released archives and
installed copies are comparison evidence, not substitutes for local source inspection or
source-edit targets. An unreleased tool is acceptable; release, installation, and
activation are separate operations.

Record each resolved repository root, HEAD, relevant staged, unstaged, and untracked
changes, and the identity of the actual skill and reference bytes read in existing
native execution evidence. HEAD alone does not identify uncommitted content. Preserve
unrelated changes and do not reset or clean producer trees to make them fit a previous
audit. Refresh affected observations when relevant source bytes change, evidence
conflicts, or context is unavailable. If a source is missing or its intended content is
ambiguous, report the unresolved input instead of substituting an installed copy.

Use Master's tool completion handoff and current source evidence to assess the external
requirements below. Follow any canonical task mapping established by each producer; the
proposal labels do not create a second producer roadmap. Record missing requirements for
the owning tool and keep integration acceptance open until the required evidence is
available. This source inspection does not replace Master's required manual skill
verification.

## Shared implementation requirements

- Edit Aquarium skills in the Aquarium repository and each `use-*` skill in its owning
  tool repository. Installed copies are comparison evidence, not source-edit targets.
- Keep descriptions concise and put the actual use case and activation boundary first.
  Move procedures and detailed prerequisites into the body. Do not impose an arbitrary
  character limit.
- Keep entrypoints focused on purpose, inputs, activation, routing, essential
  constraints, and completion conditions. Load supporting documents when their workflow
  or condition applies.
- Keep safety-critical instructions available before the action they govern. Splitting a
  document must not make a mandatory contract optional or unreachable.
- Preserve exact command grammar, schemas, identity and revision checks, idempotency,
  evidence freshness, and native lifecycle behavior.
- Preserve task-handler's ordered phases and epic-handler's goal-centered execution.
  Their different purposes must remain visible.
- Carry existing authorization forward when it covers the same decision and unchanged
  scope. Preserve distinct approvals required for materially different effects.
- Preserve repository test authorities, release gates, exact-candidate requirements,
  independent-review contracts, and Master's manual skill verification.
- Change executable helpers only when a changed resource layout or another explicitly
  scoped integration contract requires it. Do not add prose-matching tests or automated
  LLM evaluations.
- Preserve unrelated staged, unstaged, and untracked work.
- Follow existing authorization contracts for releases, installation, activation,
  provider execution, staging, commits, and publication. Approval for one task does not
  automatically authorize those effects.

## Aquarium task requirements

### TASK-043: Shorten Aquarium discovery descriptions

Review the current Aquarium skill inventory; the initial audit covered 25 descriptions.
The initial change candidates are
`task-handler`, `epic-handler`, `epic-validator`, `dev-setup`, `dev-setup-global`,
`task-commit`, `task-close`, and `task-refine`.

Remove phase inventories, repeated activation wording, detailed prerequisites, and
component catalogs from descriptions. Preserve the distinctions between direct
invocation, delegated execution, local setup, global setup, planning, implementation,
review, and publication. Move required details into the body when they are not already
present there.

Deliver a scoped metadata change and a manual trigger matrix covering intended requests
and nearby requests that must select another skill.

Acceptance:

- Frontmatter remains valid and skill names remain unchanged.
- Each changed description identifies its primary use before procedural detail.
- Explicit-only and delegated entry conditions retain their meaning.
- This task changes no workflow behavior.
- Descriptions already suitable for discovery remain unchanged.

### TASK-044: Restructure Aquarium entrypoints and conditional reading

Refactor the documentation structure of `task-handler`, `epic-handler`,
`epic-validator`, and `release-qa`. Replace unconditional reference bundles in
`new-project`, `new-feature`, `refactor`, and `war-room` with action-based loading
conditions.

For release QA, separate full-pass execution, confirmation, and settlement/recovery
detail. For handlers, move specialized review, remediation, resumption, and closeout
detail into supporting references while retaining transition and completion contracts at
the entrypoint.

Use existing shared references where they already own a rule. Each moved section must
have an explicit entry condition. For design workflows, load the Ouroboros contract
before provider work, the residency contract before handling governed evidence,
documentation governance before deciding document structure, and the execution-SOT
contract before defining epic scope. Preserve any earlier loading point needed to
prepare an informed proposal.

Update affected links, package resource inventories, and documentation pointers. Keep
the structural move separate from the intentional behavior changes in TASK-045.

Acceptance:

- Every moved requirement has one identifiable owner and a reachable loading condition.
- Normal execution does not require unrelated fallback or recovery detail.
- Full and confirmation QA retain their distinct admission, coverage, and settlement
  requirements.
- Handler phase order, review budgets, state transitions, and approval boundaries remain
  unchanged.
- Structural and reference checks pass without tests that pin prose.

### TASK-045: Remove redundant Aquarium rechecks and questions

Address four bounded behaviors:

1. In `task-handler`, replace unconditional rereading of every affected file after every
   phase with verification of phase postconditions and refresh of changed, conflicting,
   or unavailable information.
2. In `task-refine`, replace automatic broader gates after any optimization edit with
   affected checks plus repository-required broader gates. Reuse valid evidence in
   subsequent phases.
3. In `task-commit`, accept an explicit current task/checkpoint relationship when the
   request and inspected state agree. Ask when the relationship is missing, ambiguous,
   or conflicting.
4. In `dev-setup`, record established Sanho non-use in the target project's AGENTS.md
   and align Aquarium callers, including `task-commit`, with that guidance. Confirm
   the repository's registration and configuration; a missing executable or failed
   status command alone does not establish non-use. Preserve configured-project
   guidance and update the exclusion when Sanho is adopted.

Use the following Sanho guidance when non-use is established:

> Sanho is not configured for this project. Do not load or invoke the use-sanho
> skill, or run Sanho commands, for routine work or ordinary Git commit/push
> preparation. Use it only when the user explicitly requests Sanho adoption,
> initialization, configuration, or diagnosis. Update this guidance when Sanho
> is adopted.

Reconcile directly affected shared references and guidance without reverting newer
AGENTS.md improvements. Do not use this task to change task-close's terminal-state
selection or final acceptance contract.

Acceptance:

- Independent verification of a leaf result remains required.
- Changed targets or relevant inputs invalidate affected evidence.
- Podway's required fresh observations and fences remain intact.
- An exact task/checkpoint commit request does not trigger the same relationship
  question again.
- Ambiguous commits still require clarification.
- Lifecycle selection, commit scope, identity checks, and push authorization remain
  separate.
- Required test and release gates are not weakened.
- Established Sanho non-use suppresses routine skill loading and commands, including
  commit/push preparation. Configured projects retain their boundary-specific checks.
- A missing executable or failed query never produces a false Sanho non-use statement.
  Sanho adoption updates the exclusion so it cannot silently disable configured use.
- Agent guidance and Aquarium callers agree on the Sanho policy. Skill and CLI
  semantics outside the approved routing changes remain intact.

### TASK-046: Validate integration and complete manual acceptance

Reconcile Aquarium's references, expected paired-skill file inventories, source
provenance checks, and distribution instructions with the final source trees. Update
bounded resource-path expectations when necessary without weakening exact-source
verification. Compare source trees without installing or activating them implicitly.

Perform structural checks appropriate to changed files. Add or adjust executable tests
only where changed helper behavior requires them. Follow each repository's current
verification authority; do not substitute static inspection for required behavioral
evidence.

Prepare the following manual scenarios for Master. Manual verification requires its own
applicable execution authority and can remain pending after source preparation.

| Scenario | Required outcome |
| --- | --- |
| Direct invocation, delegated invocation, and nearby unrelated request | Correct skill selection and scope |
| Ordinary successful execution | Conditional recovery documents are not loaded unnecessarily |
| Continuation with unchanged authorization | Work continues without repeating the same decision |
| Changed target or materially expanded effect | Relevant evidence or authorization is refreshed |
| Small refinement and no-op refinement | Proportionate checks without redundant gate execution |
| Exact task/checkpoint commit request | Relationship is reused; lifecycle and publication remain separate |
| Async observer timeout | The same invocation continues without duplicate execution |
| Podway context restoration | Current identity and fences govern the next action |
| Sanho commit warning and push rejection | Correct boundary-specific continuation |
| Sanho warning followed by Git commit failure | Actual Git result and relevant state determine success; no false success claim or duplicate successful commit |
| Sanho recovery with unchanged authorization or changed effects | Continue within the existing target and effects; refresh authorization for materially different actions |
| Confirmed Sanho non-use during ordinary work and commit/push preparation | No routine use-sanho loading or Sanho invocation |
| Configured Sanho project, then adoption in a previously unconfigured project | Preserve configured checks and update the non-use guidance when adoption occurs |
| Missing Sanho executable or failed status query | No unsupported non-use guidance is written |
| Sorage registration, session start, or new task without a discovery request | No automatic inbox/outbox query or skill loading for discovery |
| Explicit Sorage inbox/outbox request and continuation | Perform the requested checks within their scope without repeating authorization |
| Another explicit Sorage operation without an inbox/outbox request | Perform the authorized operation without adding automatic discovery |
| Full and confirmation release QA | Original candidate and settlement guarantees remain intact |
| Sorage handoff under the [explicit broker-operation policy](../specs/tool-integrations.md#sorage-readiness) | Preserve revision, review, withdrawal, and Vault behavior |

Acceptance:

- All changed references and required package resources resolve.
- Aquarium and paired skills agree on tool ownership, activation, evidence, and
  recovery.
- Structural results and manual behavior results are reported separately.
- Master has confirmed the applicable manual scenarios before functional completion is
  claimed.
- Any unperformed required check remains an explicit gap.
- No runtime performance, token-saving, or latency improvement is claimed without
  measurement.

## External source acceptance

These criteria define the producer results to inspect during integration. The roadmap
owns their dependency relationship to Aquarium. Producer implementation, verification,
and lifecycle remain in the respective tool repositories.

### Gaori (SKILL-04): Restructure Gaori skills

The producer scope covers `skills/use-gaori` and `skills/use-gaori-status`.

Shorten both descriptions. Keep selected-command execution, the default async lifecycle,
terminal-result interpretation, and essential safety rules in the main execution skill.
Move transport fallbacks, existing-log analysis, retention, and detailed configuration
guidance to conditionally loaded references.

Replace detailed instructions about host reasoning and five-minute waiting cycles with
concise guidance to retain the same pending handle and follow host waiting and
communication requirements.

Acceptance:

- A connected MCP transport remains usable without an unrelated PATH CLI.
- Waiting, observer timeout, cancellation, and command completion retain their distinct
  meanings.
- Transport changes never cause duplicate command execution.
- Child results remain separate from extraction quality and workflow acceptance.
- Native timeout limits and fallback conditions remain accurate.
- Timing explanations continue to use Gaori's calculations.
- Retention advice remains nonblocking and does not authorize deletion.
- Source-distribution resource lists and links include every required reference.

### Mulgae (SKILL-05): Restructure the Mulgae skill

The producer scope covers `skills/use-mulgae`.

Shorten discovery text where procedural detail obscures its use. Retain the root-review
path, exact invocation preservation, terminal-result handling, and core transmission
boundaries in the entrypoint. Load foreground MCP, CLI, child workflows, export,
retention, and recovery instructions only when applicable.

Simplify host waiting instructions without changing native review deadlines or
observation semantics.

Acceptance:

- Preflight and execution use the same authorized target, objective, and roles.
- An uncertain start never causes a duplicate review.
- Observer cancellation remains distinct from review cancellation.
- Terminal results, publication authority, findings, and recovery composition retain
  their current meanings.
- Native recovery remains distinct from Aquarium's review-round accounting.
- Private configuration and provider artifacts retain their protections.
- Distribution instructions and resource inventories include the complete skill tree.

### Podway (SKILL-06): Restructure the Podway skill

The producer scope covers `skills/use-podway`.

Shorten the description while preserving explicit activation and authorized
workflow-envelope activation. Keep observation, identity verification, current fences,
supported recording, and justified progression prominent.

Move detailed archive advice and recovery procedures into their existing owning
references. Retain concise resumption checks in the entrypoint.

Acceptance:

- Installation or an existing session does not activate Podway by itself.
- The same authorized workflow resumes without repeated activation approval.
- Workspace or session mismatches are resolved before mutation.
- Unknown mutations retain their canonical request and idempotency key.
- Prepared sessions, `begin`, active attempts, terminal disposition, and replacement
  remain distinct.
- Required observation, evidence pagination, revision checks, and native transitions
  remain unchanged.
- Archive advice remains nonblocking and never authorizes deletion.

### Sanho (SKILL-07): Restructure the Sanho skill

The producer scope covers `skills/use-sanho`.

Shorten the description. Keep the ordinary commit and push paths concise. Move detailed
`diff`, `log`, `show`, provenance filtering, and preview guidance into references
selected by the user's question or the current Git boundary.

Apply the agreed Sanho refinements: distinguish reusable environment facts from
fresh Git and Sanho evidence, load recovery diagnostics for the actual failure,
and explain when preview is useful without making either an automatic checklist.
Carry authorization through recovery for the same target and effects. Correct
the claim that a pre-commit freshness warning proves commit success; use the
actual Git result and relevant state. Reconcile directly related README statements
with the current sync-commit and conflict-marker contracts. Sanho owns these
source, reference, distribution, and documentation changes; TASK-045 owns the
Aquarium guidance and caller changes above.

Acceptance:

- Routine editing does not invoke Sanho.
- Commit and push use their appropriate freshness checks.
- Cached information is not presented as current remote state.
- Commit warnings do not cause duplicate commits.
- A warning followed by Git failure is reported as failure, not proof of success.
- Reusable facts do not replace local commit checks, refreshed canonical push checks,
  or verification after mutations. Recovery and preview stay conditional.
- Authorized reconciliation and push recovery continue within their existing scope.
- Synchronization that creates a commit retains its Git authorization requirements.
- Initialization, destructive recovery, and publication boundaries remain unchanged.
- Manual verification covers warning-then-failure, recovery within existing authority,
  and changed targets or effects; structural results remain separate from observed
  Astra behavior.

### Sorage (SKILL-08): Explicit-request broker operations

The official Sorage v0.1.1 source completes SKILL-08 and supersedes the earlier
description-only proposal. Its `skills/use-sorage/SKILL.md` changes both discovery
and Handoff-processing guidance. `TASK-047` owns Aquarium's immediate adoption;
this epic inspects the final source and verifies that later restructuring does not
change its native contract.

Acceptance:

- Frontmatter remains valid.
- Broker operations start only after an explicit user request. Inbox and outbox
  checks report only the requested list and do not authorize Handoff processing.
- Requested sender processing reads the current Review Note before revision, while
  the bounded event timeline remains optional.
- Requested Project setup uses the repository root `.gitignore` for `.sorage/`
  without making the CLI edit repository files.
- Revision checks, withdrawal restrictions, and Vault protections remain intact.

## Handoff and epic acceptance

Each task handoff identifies the implemented scope and changed source locations,
preserved contracts and intentional behavior changes, structural or executable checks
and results, manual scenarios awaiting Master, and remaining dependencies. Report
commit, release, installation, and activation state separately. Store runtime snapshots
and detailed evidence under the existing native evidence policy rather than adding
command logs or provider transcripts to this dossier.

Apply one final English Humanizer pass to changed human-authored documentation,
preserving identifiers, technical contracts, links, and task meaning. Follow the current
repository verification authority for each changed source tree. Static inspection and
local test success do not prove manual skill behavior.

Epic acceptance requires all four Aquarium tasks to satisfy their requirements, the
external source acceptance to be established, all required integration gaps to be
resolved, and Master to confirm the applicable manual scenarios. Report structural and
manual results separately; keep every unperformed required check visible without
claiming functional completion.

At closeout, promote durable information to its canonical owners and follow the
[execution SOT contract](../../plugins/aquarium/references/epic-execution-sot.md). The
roadmap records final acceptance and links the canonical outcomes. Retain or remove this
dossier and its index entry under that contract's consumer and approved deletion rules.
