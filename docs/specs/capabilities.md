# Capability Catalog

Aquarium exposes 24 skills. Public orchestration skills require an explicit matching request except `task-commit`, which may be selected when the user asks to commit in a roadmap repository or when an Aquarium workflow hands off an approved commit.

## Design and Discovery

| Skill | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `$aquarium:new-project` | Explicit | Produces an approved greenfield PRD and initial roadmap through Ouroboros-assisted discovery and QA | Creates design documents only; it does not implement the project |
| `$aquarium:new-feature` | Explicit | Creates or revises one feature epic in an existing canonical roadmap | Does not implement the feature |
| `$aquarium:refactor` | Explicit | Creates or revises one refactor or behavior-change epic | Does not implement the refactor |
| `$aquarium:war-room` | Explicit | Diagnoses one difficult bug, isolates root cause, and proposes the next work unit or an incomplete result | Does not implement the fix |

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
| `$aquarium:task-review` | Delegated or explicit resume | Runs and locally adjudicates bounded Mulgae review for one complete task target | Provider findings remain advisory until verified locally |
| `$aquarium:task-close` | Delegated or explicit resume | Selects the terminal task state, obtains final approval, and hands off any commit | Does not infer commit or publication authority |
| `$aquarium:task-commit` | Commit request or delegated handoff | Reconciles roadmap lifecycle, exact staging scope, Lore context, Sanho checks, and one authorized commit | A commit never authorizes amend, push, merge, or release |
| `$aquarium:epic-handler` | Explicit | Orders one epic's tasks, completes task goals and commits, then audits and hardens the integrated epic | External prerequisites require exact committed revisions and independent evidence |

Task delivery uses up to three remediation-eligible review rounds followed by a fourth confirmation-only round; any additional fix-and-confirmation round requires explicit user approval. Epic delivery uses bounded full-target review and remediation followed by one confirmation-only pass; clean evidence ends either loop immediately.

## Validation and Independent Review

| Skill | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `$aquarium:epic-validator` | Explicit | Cold-validates one completed epic, remediates confirmed gaps, and runs one bounded confirmation path | It does not create new requirements, rewrite history, or publish changes |
| `$aquarium:independent-review` | Explicit | Dispatches one fresh Codex static review for staged changes, HEAD, a commit, a range, a task, an epic, or a special investigation | It is read-only and never runs tests, edits, or remediation |
| `$aquarium:orca-review` | Explicit | Applies the same exact-target review contract through a selected Claude Fable, Kimi, Agy, or Cursor Agent in Orca | Dirty content is excluded unless exact paths are separately approved for staging |

Both review workflows bind the reviewer to one exact Git target and require Aquarium to adjudicate findings against current repository authority. Reviewer success, structured extraction, and publication state are separate evidence dimensions.

## Release

| Skill | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `$aquarium:release-handler` | Explicit | Establishes one stable release, settles cumulative notes, delegates QA, applies approved metadata, publishes in order, and optionally opens the next cycle | Preparation, each commit, push, tag, hosted Release, destructive repair, and next-cycle publication remain separate approvals |
| `$aquarium:release-qa` | Explicit or delegated | Exercises scenario-based release deltas and active Design Gates against one exact clean main candidate | It does not substitute existing automated tests for release scenarios or claim distribution readiness from development evidence |

Release QA has a full mode and a bounded confirmation mode. Any substantive candidate or release-note change after a pass creates a new candidate and invalidates that evidence.

## Repository Setup and Governance

| Skill | Invocation | Implemented responsibility | Boundary |
| --- | --- | --- | --- |
| `$aquarium:dev-aquarium` | Explicit development-channel request | Diagnoses and enrolls one supported canonical checkout and reconciles the Aquarium-owned native hook block | Enrollment, hook, build, isolated Codex configuration, and authentication remain separate effects |
| `$aquarium:dev-setup` | Explicit setup or repair request | Diagnoses and proposes supported tools, paired skills, MCP scopes, Podway readiness, and repository guidance | Diagnosis, lookup, installation, configuration, repair, staging, and commit stay independent |
| `$aquarium:dev-setup-bundle` | Explicit manifest | Normalizes one external manifest and applies single-repository setup sequentially across named Git roots | It performs no implicit workspace discovery and persists no central bundle state |
| `$aquarium:docs-setup` | Explicit | Audits, adopts, bootstraps, or migrates canonical documentation roles and roadmap identity | It never stages, commits, publishes, or turns structural inspection into semantic proof |
| `$aquarium:test-setup` | Explicit | Audits and configures the common Make or Bun test contract and evidence-backed legacy waivers | Applying test files does not authorize side-effectful E2E execution |

## Current Integration Corrections

The current implementation raises the Podway minimum to v0.2.6, recognizes daemon-readiness v2 and the exact v0.2.5 Procedure workaround migration, accepts the canonical isolated Ouroboros Codex launcher without probing the wrong environment, avoids redundant Codex artifact refresh, generalizes release QA confirmation matrices, and permits QA of a clean local main candidate ahead of remote main.

[`CHANGELOG.md`](../../CHANGELOG.md) remains the release-status authority for these implemented corrections.
