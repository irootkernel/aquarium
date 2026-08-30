---
name: task-document
description: "Update durable documentation and review status for one refined roadmap task. Use when $aquarium:task-handler delegates documentation or when the user explicitly invokes $aquarium:task-document to resume that phase with exact task identity and final behavior."
---

# Task Document

Document only the refined task established by `$aquarium:task-handler`. When invoked directly, require the repository, roadmap path, task ID, final behavior, and current task-owned diff.

Read [documentation-governance.md](../../references/documentation-governance.md), [epic-execution-sot.md](../../references/epic-execution-sot.md), [evidence-residency.md](../../references/evidence-residency.md), and [release-notes.md](../../references/release-notes.md).

## Update Durable Documentation

Resolve the task's parent epic, handler-resolved execution SOT and any linked active dossier, `docs/README.md`, and canonical role owners from the roadmap. Determine documentation impact from final behavior and the task-owned requirements.

Promote accepted behavior to specifications, current components and boundaries to architecture, accepted rationale to architecture decision records, code-changing or verification guidance to implementation tips, environment setup or deployment and recovery guidance to operations, and user-facing value or usage to the root README.

Update only affected durable owners, generated-document sources, any active dossier, and roadmap entries.

When a dossier exists, keep it current for remaining member tasks and consumer epics. Remove or revise only this task's consumed handoffs and stale assumptions; retain requirements and acceptance needed by any remaining consumer until its epic closeout.

Do not create a dossier during this leaf phase, mark checklist state as lifecycle state, or turn the execution SOT into implementation history. Stop the document phase when a durable task outcome has no canonical owner, when operational impact is left in implementation tips, or when a later task would read stale execution guidance.

Inspect Project Configuration for the exact `Aquarium release notes: <repository-relative-path>` declaration. For an enrolled repository, settle exactly one release-note decision before review: add one concise `entry` for a user-visible, compatibility, security, privacy, or operational outcome, or record `intentional no-note` for an internal-only change.

Include an approved entry in the task-owned diff and validate the open target; never infer omission from the commit prefix. For an unenrolled repository return `not-enrolled` without creating a changelog or configuration.

Read the roadmap's allowed status vocabulary. Move the task to its existing review state, preferring `In Review` only when that value is defined. Do not invent lifecycle states.

## Handoff Semantics

Write a repository handoff for future development agents, not as history of the completed task.

**Internal handoff:** Create a temporary instruction only for one or more later tasks in the same epic. Name every consuming task, identify the authoritative source or starting point, record non-obvious constraints and common misinterpretations, state required and prohibited actions, and state what change invalidates existing evidence or requires revalidation. Require the consuming task to remove or update the entry after use. Never accumulate Internal handoffs as permanent completed-task history.

**External handoff:** Create an instruction only when a stable cross-epic dependency or constraint actually remains. Name the downstream epic, task, consumer, or subsystem when known; keep the instruction concise and actionable; and require removal or update when the underlying contract changes. When no cross-epic instruction exists, follow local roadmap style by stating that no External handoff is currently required or omitting the section.

When no actionable Internal or External instruction exists, create no repository handoff; update only the affected durable documentation and lifecycle state.

Before retaining each item, ask: "Will this instruction materially reduce the next development AI's analysis time or risk of an incorrect implementation?" Remove it unless the answer is yes. A useful item should normally fit one of these categories:

- Reference this
- Be careful about this
- You must do this
- You must not do this
- Revalidate when this changes

Do not use a repository handoff as a task completion report, Git log substitute, managed-session export, test report, or list of files or commands changed by the completed task. Do not duplicate information already discoverable from Git, session evidence, test artifacts, or canonical documentation; prefer a link to the authoritative source.

Never copy ignored runtime paths or identities governed by the shared residency contract into tracked documentation as evidence. Do not create routine `Validation remediation` or `Validation record` sections. A stable promoted package may be referenced only when it independently satisfies the shared promotion contract and the reference is necessary for a named downstream consumer.

Include an exact revision, hash, command, or test result only when the exact value is required for downstream correctness, compatibility, or reproducibility and no clearer canonical reference exists. Explain why the next task needs it, when it becomes stale, and what must be revalidated after it changes. Avoid "we implemented," "we verified," and "the task completed" prose unless that fact directly changes what a future task must do.

## Synchronize and Validate

Follow repository-owned documentation synchronization rules. Run required status checks before editing, committing, or pushing documentation. If synchronization can create a commit and commit authority was not granted, stop before that action and request authority. Never bypass synchronization hooks or edit their internal metadata.

In a Sanho-managed repository, reference `$use-sanho` and follow it only when this phase reaches an explicitly requested synchronization, lifecycle, or recovery action. Do not invoke Sanho for routine documentation editing or validation. If the skill is unavailable and repository guidance requires it, return an exact `$aquarium:dev-setup` continuation request; otherwise apply the repository's native Sanho rules and report that specialized guidance was unavailable.

Run applicable documentation validation after the update. Verify the promoted canonical content, any active dossier consistency, and operations boundary separately from structural checks. Separate task-caused failures from pre-existing failures, but do not claim a complete documentation gate passed when it did not. Do not stage, invoke Mulgae, commit, or publish unless the orchestrator recorded separate authority for that exact action.

## Report Orchestration Evidence

Return changed documentation paths, the canonical promotion decisions by role, dossier updates, the exact `entry`, `intentional no-note`, or `not-enrolled` release-note decision, roadmap state, synchronization and validation commands with exit codes, staged and unstaged documentation state, and remaining gaps to the orchestrator. This phase report is orchestration evidence, not a repository handoff. Do not copy it into durable documentation unless an item independently passes the downstream usefulness test.
