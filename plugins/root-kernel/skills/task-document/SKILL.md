---
name: task-document
description: "Update durable documentation and review status for one refined roadmap task. Use when $root-kernel:task-handler delegates documentation or when the user explicitly invokes $root-kernel:task-document to resume that phase with exact task identity and final behavior."
---

# Task Document

Document only the refined task established by `$root-kernel:task-handler`. When invoked directly, require the repository, roadmap path, task ID, final behavior, and current task-owned diff.

## Update Durable Documentation

Determine documentation impact from final behavior. Update only affected durable specifications, architecture decisions, contracts, operational guidance, generated-document sources, and roadmap entries.

Read the roadmap's allowed status vocabulary. Move the task to its existing review state, preferring `In Review` only when that value is defined. Do not invent lifecycle states.

## Synchronize and Validate

Follow repository-owned documentation synchronization rules. Run required status checks before editing, committing, or pushing documentation. If synchronization can create a commit and commit authority was not granted, stop before that action and request authority. Never bypass synchronization hooks or edit their internal metadata.

In a Sanho-managed repository, reference `$use-sanho` and follow it only when this phase reaches an explicitly requested synchronization, lifecycle, or recovery action. Do not invoke Sanho for routine documentation editing or validation. If the skill is unavailable and repository guidance requires it, return an exact `$root-kernel:dev-setup` continuation request; otherwise apply the repository's native Sanho rules and report that specialized guidance was unavailable.

Run applicable documentation validation after the update. Separate task-caused failures from pre-existing failures, but do not claim a complete documentation gate passed when it did not. Do not stage, invoke Mulgae, commit, or publish unless the orchestrator recorded separate authority for that exact action.

Return changed documentation paths, roadmap state, synchronization and validation commands with exit codes, staged and unstaged documentation state, and remaining gaps to the orchestrator.
