---
name: task-plan
description: "Plan one named roadmap task without mutation. Use when $root-kernel:task-handler delegates its planning phase or when the user explicitly invokes $root-kernel:task-plan to resume that phase with a repository, roadmap path, and exactly one task ID."
---

# Task Plan

Plan only one task. Require the repository, canonical roadmap path, and exact task ID established by `$root-kernel:task-handler`; when invoked directly, reconstruct and validate those inputs before proceeding.

## Explore Without Mutation

Read applicable repository instructions, the task entry, linked authority documents, current architecture, Git state, existing tests, CI and task runners, documentation synchronization rules, and configured development-tool guidance. Do not create a goal, edit files, generate code, run rewriting formatters, stage changes, invoke providers, or alter external state.

## Produce and Approve the Plan

Produce a decision-complete plan containing:

- goal, requirements, non-goals, lifecycle meaning, and task boundaries;
- current architecture observations and affected behavior;
- implementation approach and meaningful tradeoffs;
- requirement-to-verification matrix;
- documentation, rollout, and review impact;
- exact repository-native verification commands;
- known permission, tool, provider, and environment gaps.

Ask for explicit approval of the plan. Do not treat discussion, partial agreement, or approval of a different action as plan approval. If approval is refused, withheld, or given for a different action, stop, report the exact missing decision, and do not enter implementation.

If the host is in Plan mode, remain there and end with a continuation prompt that explicitly invokes `$root-kernel:task-handler` with the same repository, roadmap path, and task ID to execute the approved plan. Return the plan, approval state, inspected authority paths, and unresolved gaps to the orchestrator.
