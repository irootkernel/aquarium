# Capability Catalog

Public orchestration skills require an explicit matching request except `task-commit`, which may be selected when the user asks to commit in a roadmap repository or when an Aquarium workflow hands off an approved commit, and the bounded `epic-handler` to `new-feature` design route described below.

## Design and Discovery

| Skill | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `$aquarium:new-project` | Explicit | Produces an approved greenfield PRD and initial roadmap through Ouroboros-assisted discovery and QA | Creates design documents only; it does not implement the project |
| `$aquarium:new-feature` | Explicit or pre-execution `epic-handler` design route | Creates or revises one feature epic in an existing canonical roadmap | A routed design preserves the existing epic identity and needs its own execution and exact-diff approvals; it does not implement the feature |
| `$aquarium:refactor` | Explicit | Creates or revises one refactor or behavior-change epic | Does not implement the refactor |
| `$aquarium:war-room` | Explicit | Diagnoses one difficult bug, isolates root cause, and proposes the next work unit, confirms no corrective work is needed, or reports an incomplete investigation | Does not implement the fix |

These workflows use Ouroboros only for their explicitly approved discovery or QA leaf operations. Git-backed runs select Podway by default before the first managed-session mutation and may be explicitly opted out before that boundary.

## Task and Epic Delivery

| Skill | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `$aquarium:task-handler` | Explicit | Orchestrates one roadmap task through plan, implementation, verification, refinement, documentation, review, approval, and closeout | Requires one canonical task identity and never treats runtime state as roadmap authority |
| `$aquarium:task-plan` | Delegated or explicit resume | Explores one task and produces a decision-complete approved plan without mutation | Creates no goal, Podway session, source diff, or provider request |
| `$aquarium:task-implement` | Delegated or explicit resume | Implements the approved task scope against the current baseline | Does not redesign materially drifted requirements silently |
| `$aquarium:task-verify` | Delegated or explicit resume | Maps requirements to current tests and evidence, then runs authorized checks | A green command proves only the requirements mapped to it |
| `$aquarium:task-refine` | Delegated or explicit resume | Uses upstream Deslop and task-owned optimization on a verified diff | Requires exact staging authority and preserves unrelated staged content |
| `$aquarium:task-document` | Delegated or explicit resume | Updates current specifications, architecture, handoffs, release-note decision, and review status | Does not use documentation as a Git log or execution transcript |
| `$aquarium:task-review` | Delegated or explicit resume | Dispatches the selected Mulgae, Orca, or fresh Independent Review route, or performs an explicit coordinator waiver assessment, then locally adjudicates the complete task target | Mulgae is the default; only the selected route's prerequisites apply, and provider findings remain advisory until verified locally |
| `$aquarium:task-close` | Delegated or explicit resume | Selects the terminal task state, obtains final approval, and hands off any commit | Does not infer commit or publication authority |
| `$aquarium:task-commit` | Commit request or delegated handoff | Reconciles roadmap lifecycle, roadmap-scoped or native Git identity, exact staging scope, Lore context, Sanho checks, and one authorized commit | A commit never authorizes amend, push, merge, or release |
| `$aquarium:epic-handler` | Explicit | Orders one epic's tasks, completes task goals and commits, then audits and hardens the integrated epic | External prerequisites require exact committed revisions and independent evidence |

Task delivery uses at most three `work-unit` assessments followed by one `remediation-confirmation` under the initial workflow envelope. Every later correction and confirmation requires a fresh explicit user decision through the task's recorded user-direction gate. Epic delivery and cold validation use the same three-work-unit plus one-remediation-confirmation boundary. These limits are maxima, not quotas: clean evidence ends immediately, and a Low-only result proceeds after its frozen finding set receives complete supported dispositions, current local verification, and zero unmet or unverified completion criteria. A Medium-or-higher correction still requires its owed confirmation review.

On an `execute` entry, `epic-handler` routes an ordinary feature epic with a required missing dossier or semantic owner to `new-feature` in the same conversation before creating an Epic session. Design finishes with an exact new-conversation `epic-handler` request once its approved documents and any required commit are complete. A user-requested dossier waiver retains the composite-SOT approval flow when the semantic requirements are complete.

## Validation and Review

| Skill | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `$aquarium:epic-validator` | Explicit | Cold-validates one completed epic, remediates confirmed gaps, and runs one bounded confirmation path | It does not create new requirements, rewrite history, or publish changes |
| `$aquarium:independent-review` | Explicit | Runs one static review with three fresh Codex subagents for a selected exact target | Standalone or explicitly selected in Task, Epic, and validation workflows; requires fresh host delegation and has no automatic fallback |
| `$aquarium:mulgae-review` | Explicit | Runs one report-only standalone Mulgae review for an exact change or Task or Epic completion target | `$use-mulgae` owns capture, execution, recovery, publication, and retention; Aquarium owns intent delivery and local adjudication |
| `$aquarium:orca-review` | Explicit target and reviewer request | Applies the shared purpose, Review Brief, and target meanings through a fresh reviewer selected by the user and supervised by Orca | Supports staged, HEAD, commit, and range targets in the current registered worktree; workspace and dirty targets are unavailable |

Enabled static review workflows bind the reviewer to one declared source scope and purpose. Mulgae captures an immutable target and exposes an isolated read-only provider workspace. It removes temporary provider workspaces after use, while durable captures, reports, and artifacts remain under `.mulgae/`. Orca reads the selected target in its current registered worktree. All Orca reviewers may retain review-related temporary files, native state, tool output, and reports outside the worktree or in Git-ignored runtime paths within it, such as ignored files under `.omc/`. External locations include `/tmp` or `/private/tmp`. Permitted external files and ignored runtime writes do not require warnings, extra checks, approval, or another review. Independent Review gives one exact target and Review Brief to three fresh host subagents, checks mutable target state after their reports, and retains separate host provenance without claiming immutable capture.

Aquarium treats every finding as a hypothesis, preserves its reported severity, and assigns validity plus an effective `Blocker`, `Critical`, `High`, `Medium`, or `Low` priority. Standalone Mulgae, Orca, and Independent Review report without source mutation. An Independent Review operation is complete only with three reports for the same target and Brief; the coordinator adjudicates findings and criteria without a majority vote. Approved task, epic, and validation handlers fix valid Medium-or-higher findings, run affected checks, and require a fresh review. Depending on impact, a Low finding gets a self-evident fix, a focused fix with a deterministic test, a deferred-feedback entry, or a TODO candidate. The source review and its historical Low count remain immutable; completion instead requires zero pending dispositions, zero current blockers, zero unmet or unverified completion criteria, and passing local verification for the exact permitted final delta. Reviewer success, structured extraction, and publication state remain separate evidence dimensions, and a clean technical verdict never substitutes for completion assessment.

## Release

| Skill | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `$aquarium:release-handler` | Explicit | Establishes one stable release, settles cumulative notes, delegates QA, applies approved metadata, publishes in order, and optionally opens the next cycle | Preparation, each commit, push, tag, hosted Release, destructive repair, and next-cycle publication remain separate approvals |
| `$aquarium:release-qa` | Explicit or delegated | Exercises scenario-based release deltas and active Design Gates against one exact clean main candidate | It does not substitute existing automated tests for release scenarios or claim distribution readiness from development evidence |

Release QA has a full mode and a bounded confirmation mode. Any substantive candidate or release-note change after a pass creates a new candidate and invalidates that evidence.

## Repository Setup and Governance

| Entrypoint | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `aquarium-dev` MCP tools and CLI | Explicit development-channel request | Diagnoses and enrolls one supported canonical checkout, publishes exact foreground or managed-service generations below `~/.aquarium-dev`, and installs the optional inherited-environment launcher | Enrollment, hook, build, managed-service activation, and launcher installation remain separate effects; producers retain daemon ownership, and Codex configuration plus production Dolgorae setup are outside the channel |
| `$aquarium:status` and `aquarium-status` | Explicit status, language refresh, or exact-row removal request | Reports the user-global production setup ledger, declared Go, Rust, Python, TypeScript, and Dart versions, independent freshness, live root identity, and development enrollment; refreshes registered language observations on request and removes one digest- and revision-bound row after approval | Stored declarations are snapshots; release lookup, language refresh, runtime installation, and exact deletion remain independent effects |
| `$aquarium:dev-setup-global` | Explicit global setup, update, or scoped prerequisite repair | Diagnoses every selected user-global CLI, paired skill, service, global MCP registration, third-party writing or Lore skill, and Ouroboros component | Read-only freshness lookup, download, installation, replacement, configuration, and provider authority remain independent |
| `$aquarium:dev-setup` | Explicit repository setup or repair request | Automatically diagnoses evidenced repository configuration, project MCP, Podway readiness, and root AGENTS.md guidance, then proposes only verified gaps; existing root CLAUDE.md content is migrated before removal | It trusts canonical global skill presence and never installs, compares, or updates global installation state; selected Sorage diagnosis checks installation state before native database-opening probes, requires backup and restore preflight plus separately approved migration for a pre-Memo database, and keeps registration report-only unless Project setup was explicitly requested |
| `$aquarium:dev-setup-bundle` | Explicit manifest | Normalizes one external v2 manifest, prepares selected shared components and required global MCP registrations once, and applies target-specific MCP, Sorage, and Mulgae intent sequentially across named Git roots | It performs no implicit workspace discovery and persists no central bundle state |
| `$aquarium:docs-setup` | Explicit | Audits, adopts, bootstraps, or migrates canonical documentation roles and roadmap identity | It never stages, commits, publishes, or turns structural inspection into semantic proof |
| `$aquarium:test-setup` | Explicit | Audits and configures the common Make or Bun test contract and evidence-backed legacy waivers | Applying test files does not authorize side-effectful E2E execution |

## Current Integration Corrections

The current implementation keeps Dolgorae optional for explicitly delegated native operations and runs Aquarium Independent Review with three host-native Codex subagents and no Dolgorae operation. It routes Orca Review directly to the user-selected reviewer in the current worktree and provides standalone Mulgae Review and standalone Independent Review. It requires Sorage v0.1.2 or later in the v0.1.x line and Podway v0.2.12 or later in the v0.2.x line, requires named-mode daemon-readiness v3, retains the exact v0.2.5 Procedure workaround migration, and keeps workspace removal and runtime-mode moves behind the pinned `use-podway` skill's explicit exact-target boundary. It accepts the canonical isolated Ouroboros Codex launcher without probing the wrong environment, avoids redundant Codex artifact refresh, generalizes release QA confirmation matrices, and permits QA of a clean local main candidate ahead of remote main.

[`CHANGELOG.md`](../../CHANGELOG.md) remains the release-status authority for these implemented corrections.
