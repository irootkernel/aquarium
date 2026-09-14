# Standalone Mulgae Review Examples

These examples select review intent and an existing Mulgae target. They do not authorize tests, remediation, staging, lifecycle changes, commits, or another review.

## Generic staged change

```text
Use $aquarium:mulgae-review to review the staged change.

Purpose: change
Target: stage
Intent: Prevent duplicate webhook delivery after a worker restart while preserving the existing retry policy.
Roles: logic, security, testing
```

Judge the HEAD-to-index candidate and its intended effect. Report excluded unstaged and untracked state, and do not claim that a whole Task or Epic is complete.

## Named Task completion in a staged candidate

```text
Use $aquarium:mulgae-review to determine whether TASK-123 is complete in the staged candidate.

Purpose: completion
Target: stage
Authority: docs/roadmap/README.md and the Task's linked dossier
Checkpoint: ready for the existing closeout decision
```

Assess every applicable Task requirement against the staged index and relevant readable context. Unstaged implementation cannot satisfy a criterion. The result is a report, not permission to change lifecycle or create the commit.

## Named Epic completion in a committed candidate

```text
Use $aquarium:mulgae-review to determine whether EPIC-123 was actually completed at commit <full-commit-id>.

Purpose: completion
Target: diff <resolved-parent>..<full-commit-id>
Authority: docs/roadmap/README.md and the Epic's linked dossier
Checkpoint: claimed completed outcome
```

Resolve both revisions before dispatch and assess the immutable candidate, all applicable member requirements, and integration seams. Do not manufacture a staged diff when the work is already committed, and do not start an Epic handler or validator.
