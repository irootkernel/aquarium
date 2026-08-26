# Plan Handoff

Read this reference only when `task-handler` or `epic-handler` selects `plan-handoff` or resumes a session that carries a plan handoff. No other Aquarium workflow owns this mode.

## Select the Mode Explicitly

The handlers support four entry modes:

- `execute` is the default and continues with the approving agent without persisting the complete plan.
- `plan-only` returns the plan without creating a file, goal, or Podway session and without changing repository or external state.
- `plan-handoff` prepares an approved plan for another agent, then stops before implementation.
- `resume` continues the exact matching handler session.

Treat an unqualified request to "plan only" as `plan-only`. Select `plan-handoff` only when the user explicitly says that another AI or agent will continue, asks to prepare a handoff, or supplies `mode=plan-handoff`. Select `resume` for an explicit continuation request. If an explicit mode conflicts with the user's prose, stop and resolve the conflict before mutation.

`plan-handoff` requires the default Podway path. An explicit Podway opt-out selects `plan-only` instead or requires the user to choose another continuation mechanism; never create a detached Aquarium handoff file without its owning Podway session.

## Prepare the Handoff After Approval

Do not create the handoff file, a Codex goal, or a Podway session before the user explicitly approves the decision-complete plan and the disclosed handoff operations. If the host remains in Plan mode, return an exact continuation request for the same handler, repository, roadmap identity, and `mode=plan-handoff`; perform no handoff mutation in that turn.

After approval in an execution-capable turn:

1. Re-read the approved plan, repository instructions, roadmap identity, Git state, Podway readiness, and any recoverable approval. Stop if the plan or authority cannot be reconstructed exactly.
2. Start or resume the matching prepared Procedure through the normal shared Podway contract, re-observe it, and use the current fenced `session.begin` template to create the goal, ordered criteria, attempt, and actor.
3. Derive the only plan path as `.podway/runtime/handoffs/<initial-session-id>/plan.md`, where `<initial-session-id>` is the UUID returned for the first handoff session. Never accept a caller-supplied file name or derive the path from task prose.
4. Require `.podway/runtime` and every existing path component to be real directories without symlinks. Create the session directory with private directory permissions and the file with private file permissions. Write the exact approved Markdown plan atomically, with no transcript, source dump, credentials, raw logs, provider payloads, or added narrative. Reject content larger than 65,536 UTF-8 bytes.
5. Never overwrite different bytes. An existing regular file at the exact path is idempotent only when its complete SHA-256 and byte size match the approved plan; otherwise stop with the conflicting path and digests.
6. Attach the file to the current Procedure's `plan-handoff-artifact` item as a worktree-relative local artifact with media type `text/markdown`. Re-observe, read the recorded metadata, and require path, SHA-256, and byte size to match the file before moving or stopping.

For `task-handler`, record the approved plan node, advance to `implement`, verify the running node, and stop before loading `$aquarium:task-implement`. For `epic-handler`, attach the plan at the active `complete-work` node and leave its required work evidence unrecorded. Every later member-task, validation, remediation, and closeout session in that epic execution must attach and verify the same initial plan path and digest before work so the current session remains independently resumable.

The handoff file is temporary Aquarium execution context, not roadmap authority, project documentation, Podway evidence bytes, a Git artifact, or proof that any work is complete. Keep it untracked and never stage or commit it.

## Report the Handoff

A successful `plan-handoff` response must report:

- canonical repository root, roadmap path, and task or epic ID;
- owning handler;
- Podway session ID, Procedure ID and digest, lifecycle, attempt, session revision, goal revision, and current node;
- the worktree-relative plan path, SHA-256, and byte size;
- baseline HEAD and task-owned staged, unstaged, and untracked state;
- the exact next request using the same handler, canonical identity, `mode=resume`, and `session=<uuid>`.

The session ID is mandatory output even though the generated file path is discoverable from recorded evidence. Do not require the user to repeat the plan file name.

## Resume Safely

When `session=<uuid>` is supplied, require the observed current session to match it exactly. When it is omitted, resume only when the current worktree has exactly one running session whose immutable Procedure, owning handler, canonical roadmap path, and task or epic identity all match the request. Otherwise stop and require the exact session ID.

Re-observe before work and verify the session, attempt, goal revision, current node, plan artifact metadata, complete local file digest and size, roadmap authority, applicable instructions, and Git state. Read the approved plan from the recorded artifact path rather than asking the user to repeat it. A missing file, changed bytes, mismatched session, stale goal, unexplained source drift, or invalidated requirement leaves the session running and stops before implementation; never regenerate, overwrite, or silently revise the plan.

A matching handoff session resumes through its owning handler without suspend, cancel, reset, replacement, or a new Podway session. Ordinary matching sessions without `plan-handoff-artifact` continue under the existing resume contract.

Keep the plan file while the task or epic may still resume. After successful final closeout and all required Podway completion, disposition, roadmap, commit, and residue checks have succeeded, remove only that exact handoff file and its empty session directory as a disclosed temporary-artifact cleanup. A pause, unresolved failure, cancellation that preserves history, or incomplete terminal handoff retains the file. Never sweep sibling handoff directories or infer cleanup authority from age.
