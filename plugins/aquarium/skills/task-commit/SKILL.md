---
name: task-commit
description: "Prepare and create one authorized Git commit while reconciling roadmap task lifecycle state and preserving unrelated work. Use when the user asks to commit in a repository that may contain a roadmap, when an Aquarium handler hands off an approved commit, or when a direct roadmap-repository commit must pass the Aquarium commit gate."
---

# Task Commit

Create one authorized commit through a shared roadmap-aware boundary. This skill owns commit preparation and execution, not implementation evidence, task completion judgment, Podway mutation, publication, or release.

## Establish the Commit Boundary

1. Resolve the Git root and read all applicable instructions, commit conventions, branch and upstream state, staged, unstaged, untracked, and conflicted changes.
2. Identify tracked roadmap candidates: paths whose basename or directory contains `roadmap` and whose content defines lifecycle states such as `In Progress`, `In Review`, `Completed`, `Blocked`, or `Deferred`. Read the relevant task entries and their exact vocabulary.
3. Inspect the current Codex goal. When Podway was not explicitly opted out for the managed workflow, inspect only the bounded current-session facts needed to determine whether an Aquarium handler owns the work; never advance, decide, cancel, discard, reset, or otherwise mutate Podway here.
4. Record the requested commit scope and authority. A request to commit authorizes neither amend, push, PR changes, release work, destructive actions, nor unrelated staging.

When an active matching `task-handler`, `epic-handler`, `epic-validator`, or Podway-managed Aquarium session owns the work, accept a commit only from that owner's explicit commit handoff. Otherwise stop and tell the user to resume the matching handler. Do not offer an independent path around an active managed workflow.

## Reconcile Roadmap Ownership

When no managed workflow owns the work:

- If no roadmap candidate exists, follow repository commit rules without inventing a task relationship or lifecycle edit.
- If no `In Progress` or `In Review` task exists, do not invent one. Preserve existing terminal states and proceed only with the user's commit scope.
- If one or more `In Progress` or `In Review` tasks exist, always ask whether the commit belongs to one exact task or is unrelated to every listed task. Never infer the relationship from changed files, branch names, commit text, goals, or conversation context. With multiple candidates, require an exact task ID. Allow the user to cancel. The initial commit request does not satisfy this dedicated confirmation, even when it already names a task or checkpoint; first show the current candidates, status, and exact proposed scope.
- For an unrelated commit, preserve every task status exactly and exclude unrelated roadmap edits from the commit unless separately authorized.
- For a selected task already in a roadmap-defined terminal state, preserve that state. For a selected non-terminal task, show the exact current status and require the user to select one roadmap-defined terminal state, explicitly authorize a checkpoint commit that preserves the exact current status, or cancel. Offer only terminal states the roadmap actually defines, including `Completed`, `Blocked`, or `Deferred` when present. Never choose a terminal state for the user. When the roadmap defines none, offer only the explicit checkpoint and cancel paths.
- Treat checkpoint authorization as one-commit authority only. Report that the task remains active, do not represent the checkpoint as closeout, and reconcile lifecycle state again on every later commit request.

A handler commit handoff must include:

- repository, canonical roadmap path, exact task or epic ID, exact commit scope, and the user's commit authorization;
- the lifecycle decision as either an exact approved edit or an explicit statement that no lifecycle edit applies;
- the record decision as either an exact approved edit or an explicit statement that no record edit applies;
- verification and review evidence identifying command, actor, exit status, reviewed snapshot, verdict, and review run when applicable, with inapplicable fields marked explicitly.

Reject a stale, ambiguous, or incomplete handoff rather than reconstructing approval.

## Prepare the Exact Commit

Apply only the lifecycle or record edit explicitly selected by the user or supplied by a valid handler handoff. Preserve the selected task's exact current state for an approved checkpoint. Any other code, test, documentation, or roadmap change after approval makes that approval stale.

Stage only the authorized paths or hunks. Preserve unrelated staged and unstaged work; stop if the commit scope cannot be isolated safely. Immediately before committing, re-read the staged roadmap entry, `git diff --cached`, staged tree and blob identities, and full Git status. Confirm that:

- the selected task relationship and approved terminal or unchanged-checkpoint status still match the user's answer;
- the handler handoff's lifecycle or record edit, including an explicit absence, still matches the staged snapshot;
- a declared unrelated commit contains no unintended task lifecycle transition;
- the reviewed implementation and approved lifecycle or record decision equal the staged diff;
- unrelated pre-existing staged content is absent from the intended commit.

Before a non-trivial commit, reference `$lore-commits` and follow it when available. Repository-required IDs and prefixes override Lore, which never grants commit authority. If Lore is required but unavailable, stop and return an exact `$aquarium:dev-setup` continuation request. Otherwise report its absence once, inspect `git log -5 --format=fuller`, and match the recurring subject, body, and trailer structure; inspect all commits when fewer than five exist and use a concise imperative subject when none exist.

Before committing in a Sanho-managed repository, reference `$use-sanho` and follow its commit-boundary workflow when available. If unavailable and required, stop and route to `$aquarium:dev-setup`; otherwise use the repository-required check or minimal `sanho status --json` fallback. Sanho status never grants commit authority.

## Commit Through the Gate

Run exactly one direct commit with the hook marker scoped to that process:

```bash
AQUARIUM_COMMIT_GATE=task-commit-v1 git commit ...
```

The marker signals only that this skill completed the checks above. Never export it globally, use it outside this skill, or treat it as authority. Do not amend or push.

After the commit and its hooks, compare the commit with the recorded staged snapshot byte-for-byte, inspect staged, unstaged, and untracked state for residue or hook changes, and refresh the applicable Sanho status. Report the commit ID, task relationship, final roadmap state, committed paths, checks and evidence inherited from the owner, remaining worktree state, and publication gap.

The bundled hook is a local guardrail, not complete enforcement: it detects direct shell `git commit` invocations in roadmap repositories, while indirect commits performed by other tools may not pass through that boundary.
