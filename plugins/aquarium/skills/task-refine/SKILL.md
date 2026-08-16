---
name: task-refine
description: "Deslop and optimize the verified diff for one roadmap task. Use when $aquarium:task-handler delegates refinement or when the user explicitly invokes $aquarium:task-refine with exact task identity, current verification evidence, and explicit staging authority."
---

# Task Refine

Refine only the verified task-owned diff established by `$aquarium:task-handler`. When invoked directly, require the repository, roadmap path, task ID, verified baseline, and explicit authority for the staging steps below.

## Deslop

Load and follow the bundled `$aquarium:deslop` skill against the task diff from its verified baseline. Report a broken plugin installation if it is unavailable. When the task has no task-owned code change, record deslop and optimization as not applicable with evidence.

Remove only task-introduced abnormal comments, unjustified defensive paths, type-system bypasses, needless nesting, unused artifacts, and style inconsistent with surrounding code. Preserve behavior unless correcting a demonstrated bug.

## Establish the Staged Baseline

After deslop, stage the current task-owned changes as the optimization baseline:

- Stage only exact task-owned paths or hunks, preserve all pre-existing staged content, and stop if task-owned work cannot be isolated safely.
- Orchestration through `$aquarium:task-handler` authorizes these task-owned baseline and final-refresh staging steps; direct invocation requires separate staging approval.
- Neither path authorizes commit, amend, push, or unrelated staging.

Inspect `git diff --cached` restricted to task-owned paths and use that staged snapshot as the sole optimization source of truth. Keep optimization edits unstaged during the pass so the corresponding unstaged diff shows only the proposed optimization delta. Do not reset, unstage, rewrite, or optimize unrelated staged content.

## Optimize

Inspect the staged task snapshot for:

- duplicated task logic or fixtures;
- single-use or pass-through abstractions without local precedent;
- unnecessary variables, allocations, branches, queries, or repeated work;
- an internal algorithm that can be simpler or more efficient without changing its contract.

Explicitly verify whether each task-introduced abstraction is necessary by tracing callers and consumers, comparing nearby project conventions, and identifying the contract or reuse boundary it protects. Remove an abstraction when it only adds indirection, has no justified boundary, and can be eliminated without changing behavior. Do not remove a real contract boundary merely because it currently has one caller.

Do not manufacture an edit when no safe, useful optimization exists. Record a no-change result with a concise reason. Quantitative benchmarks are unnecessary unless the roadmap or repository requires them; qualitative reasoning is sufficient, but never report an unmeasured performance gain as measured fact.

Do not broaden refinement into a general refactor. Re-run focused checks after every cleanup that touches executed code and broader gates after an optimization that changes code. After verification, stage only the confirmed task-owned optimization delta. For a no-op pass, keep the staged baseline unchanged and do not rerun gates solely because the pass made no change.

Return deslop actions, optimization reasoning, staged baseline scope, optimization delta, commands and exit codes, and the final staged task-owned implementation and test paths to the orchestrator.
