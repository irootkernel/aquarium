---
name: deslop
description: "Remove AI-generated code slop introduced by the current task while preserving behavior and unrelated work. Use when cleaning a verified task-owned code diff before review and closeout, when the user says 'clean this up', 'remove the slop', 'deslop this', or 'tidy up this diff', and especially for abnormal comments, unjustified defensive paths, type-system bypasses, needless nesting, or style inconsistent with surrounding code."
---

# Deslop

Inspect the task-owned diff from its verified baseline and remove only slop introduced by that task.

Read [podway-integration.md](../../references/podway-integration.md). When an opted-in owning workflow delegates this pass, inspect the matching session read-only and return bounded cleanup evidence to the delegating workflow. Standalone deslop never creates, mutates, advances, completes, or resets Podway.

## Focus

- Remove comments that are unnecessary or inconsistent with local style.
- Remove defensive checks or exception handling that are abnormal for trusted paths.
- Replace casts or suppressions used only to bypass the type system with a proper local solution.
- Simplify needless nesting, pass-through helpers, duplicated branches, and single-use abstractions without local precedent.
- Remove unused imports, variables, fixtures, and compatibility paths created by the task.

## Guardrails

- Preserve observable behavior unless correcting a demonstrated bug.
- Follow repository instructions and surrounding code over generic style preferences.
- Preserve pre-existing staged, unstaged, and untracked work.
- Do not broaden cleanup into a repository-wide refactor.
- Record the pass as not applicable when there is no task-owned code change.
- Re-run the narrowest affected verification after any cleanup that touches executed code, including cleanup intended to preserve behavior.

Return the material cleanup performed, the exact paths changed, every edit that touched executed code with the narrowest verification re-run and its exit status, and slop deliberately left in place, to the delegating workflow or the user.
