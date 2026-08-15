---
name: task-implement
description: "Implement the approved plan for one named roadmap task. Use when $root-kernel:task-handler delegates implementation or when the user explicitly invokes $root-kernel:task-implement to resume that phase with an approved plan and exact task identity."
---

# Task Implement

Implement only the approved plan for the task established by `$root-kernel:task-handler`. When invoked directly, require the repository, roadmap path, task ID, and explicit plan approval; stop if the plan or current task-owned boundary cannot be reconstructed safely.

## Re-establish the Baseline

Before editing, re-read applicable instructions, the task entry, approved plan, current Git state, and affected architecture. Report material drift that invalidates the plan instead of silently redesigning it.

## Implement the Approved Scope

Implement the smallest maintainable change that satisfies the approved requirements:

- follow local architecture, naming, error, data, and dependency patterns;
- avoid speculative configuration, extensibility, compatibility layers, and unrelated cleanup;
- remove imports, variables, helpers, and branches made unused by the task;
- preserve all pre-existing staged, unstaged, and untracked work;
- add a focused reproducer before a bug fix when practical;
- verify each meaningful increment with the narrowest authoritative check.

Continue diagnosing task-caused failures until the focused implementation is sound or a real authority or environment blocker appears. Do not stage, update lifecycle documentation, invoke Mulgae, commit, or publish in this phase.

Return the implemented requirements, task-owned paths, focused commands and exit codes, remaining verification work, and blockers to the orchestrator.
