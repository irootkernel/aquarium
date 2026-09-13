# Procedure workflow convergence dossier

## Authority

**Roadmap epic:** `EPIC-014`

This dossier is the temporary execution SOT for `EPIC-014` and `TASK-051`
through `TASK-061`. The [roadmap](../roadmap/README.md#epic-014-align-procedure-contracts-and-bound-low-finding-convergence)
owns identifiers, ordering, dependencies, and lifecycle state. Procedure assets,
skills, shared references, tests, and maintainer documentation own implemented
behavior after closeout.

## Goal

Make Aquarium's five managed Podway Procedures and their consumers use one
finite review-settlement contract. Historical Low findings remain part of the
source review. Completion depends on every eligible Low item receiving a
supported disposition, current local checks passing, pending dispositions and
current blockers reaching zero, and the remaining workflow gates succeeding.

No caller may start another provider review or broad re-audit solely to remove
historical Low findings or refresh provider coverage over an accepted Low-only
delta. Required first reviews and confirmation already owed after a
Medium-or-higher correction remain mandatory.

## Required contract

- Preserve review root, effective result, target, finding identifiers, reported
  severities, and coverage as immutable facts.
- Record effective priority, the frozen eligible Low set, completed dispositions,
  pending disposition count, current blocker count, final target, and local
  verification separately.
- Resolve pending invocation identity, failed or stale checks, findings needing
  confirmation, and effective Medium-or-higher findings before Low settlement.
- Use `low-self-evident-fix`, `low-bounded-fix`, `low-deferred-feedback`, or
  `low-todo-candidate`. Current correctness and acceptance defects are at least
  Medium regardless of provider severity.
- Treat review budgets as maxima. Context recovery, a revision or context label by
  itself, exact native recovery, and disposition recording do not create another
  review budget. Only an explicitly approved new goal scope or bounded additional
  pass creates new authority, with prior lineage preserved.
- Route behavior changes to implementation, cleanup to refinement, missing
  verification to verification, and documentation corrections to documentation.
- Select the supported `user-direction` route, record the exact issue set at
  `await-user-direction`, complete that action, and stop at
  `choose-user-direction`; the later user choice is never inferred.
- Accept a final target composed only of the reviewed basis, the exact verified
  Low-only delta, approved lifecycle changes, and any separately validated
  promoted-evidence projection.
- Preserve local Procedure customizations and admitted session snapshots.
  Native-valid source is not handler-compatible unless its required structural
  contract is proven.

## Task map

| Task | Durable owner and outcome |
| --- | --- |
| TASK-051 | This dossier, roadmap registration, and finite test fixtures |
| TASK-052 | Finding disposition, Mulgae review, and Podway integration references |
| TASK-053 | `aquarium-task-v2` v9 and task phase contracts |
| TASK-054 | `aquarium-goal-v2` v12 and epic goal routing |
| TASK-055 | `aquarium-validation-v2` v12 and validation callers |
| TASK-056 | All five Procedure node mappings; design and war-room v3 |
| TASK-057 | Handler, closeout, commit, and resume handoffs |
| TASK-058 | Setup inspection and customization compatibility |
| TASK-059 | Objective, native runtime, and official-artifact qualification |
| TASK-060 | Master's separately observed functional acceptance |
| TASK-061 | Canonical documentation, changelog, and unactivated handoff |

Only one task may be `In Progress`. A task completes after its stated evidence is
current. TASK-060 remains incomplete until Master observes and accepts the
required agent behavior.

## Acceptance

The acceptance inventory contains forty finite routing cases plus correction
cases C-01 through C-16. It covers Low-only
first review and direct audit, confirmation after Medium correction, failed or
inconclusive checks with zero findings, pending native invocation, exact recovery,
context restoration, user-direction waits, immutable old sessions, customized
Procedures, and commit composition.

Each correction case names its executable or observed evidence owner and keeps
specified, implemented, executed, and passed states distinct. The fixture itself
records no execution result. Native tests must exercise the canonical YAML,
reject invalid routes without domain mutation, and record the exact subvariants
and assertions completed for C-01 through C-10 and C-16. They do not establish
that an external review ran or that an agent obeyed a skill.
Observed behavior must separately confirm that eligible Low settlement starts
zero additional provider roots or broad re-audits while mandatory first and
confirmation reviews still occur.

## Exclusions

- Podway engine, SQLite, IPC, built-in presets, and native timeout or recovery
- Mulgae provider policy, storage, and native retry behavior
- automatic LLM evaluation in `make test`
- installation, activation, active-session replacement, commit, push, or release
- a central Aquarium workflow state file or a generic policy interpreter

The reported twelve-hour run remains an unconfirmed incident report unless its
exact immutable execution evidence is separately inspected.
