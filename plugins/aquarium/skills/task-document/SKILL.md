---
name: task-document
description: "Update durable documentation and review status for one refined roadmap task. Use when $aquarium:task-handler delegates documentation or when the user explicitly invokes $aquarium:task-document to resume that phase with exact task identity and final behavior."
---

# Task Document

Document only the refined task established by `$aquarium:task-handler`. When invoked directly, require the repository, roadmap path, task ID, final behavior, and current task-owned diff.

Read [design-gates.md](../../references/design-gates.md) and [evidence-residency.md](../../references/evidence-residency.md). Resolve the authoritative current and retired registry paths, using `docs/gating-rules.md` and `docs/gating-rules-retired.md` only as defaults. This skill may update a work unit's existing Design Gate impact reference as directed by authoritative task scope, but it must not create, change, reactivate, retire, or otherwise edit either resolved registry. Return an explicit `$aquarium:design-qa` handoff for any registry change.

## Update Durable Documentation

Determine documentation impact from final behavior. Update only affected durable specifications, architecture decisions, contracts, operational guidance, generated-document sources, and roadmap entries.

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

Run applicable documentation validation after the update. Separate task-caused failures from pre-existing failures, but do not claim a complete documentation gate passed when it did not. Do not stage, invoke Mulgae, commit, or publish unless the orchestrator recorded separate authority for that exact action.

## Report Orchestration Evidence

Return changed documentation paths, roadmap state, synchronization and validation commands with exit codes, staged and unstaged documentation state, and remaining gaps to the orchestrator. This phase report is orchestration evidence, not a repository handoff. Do not copy it into durable documentation unless an item independently passes the downstream usefulness test.
