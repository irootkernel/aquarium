---
name: deslop
description: "Remove AI-generated code slop introduced by the current task while preserving behavior and unrelated work. Use when cleaning a task-owned code diff before final verification, especially for abnormal comments, unjustified defensive paths, type-system bypasses, needless nesting, or style inconsistent with surrounding code."
---

# Deslop

Inspect the task-owned diff from its verified baseline and remove only slop introduced by that task.

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
- Re-run the narrowest affected verification after behavior-bearing cleanup.

Report only the material cleanup and the verification performed.
