# Orca Review Supervision

This is the current execution backend for Aquarium's independent review contracts. Review semantics belong to [review-contract.md](review-contract.md), so this backend may later be replaced without changing target behavior.

Require the separately installed `$orca-cli` skill. Resolve one Orca command exactly as that skill requires, load its version-matched `orca-cli` and `orchestration` guides, and confirm a ready local runtime. Reject nonempty `ORCA_ENVIRONMENT` or `ORCA_PAIRING_CODE`; do not route review source to a paired or remote runtime.

Use the original registered checkout and its proven `current` worktree. Do not create or register a temporary repository snapshot. The target contract, index or commit blobs, and included paths define reviewer scope.

Create one Run and Task. For `$aquarium:independent-review`, start one fresh Codex with the live guide's supervised `worker-start --worktree current --agent codex` path. Do not reuse a terminal or create another Git worktree.

For `$aquarium:orca-review`, use only the provider contract's deterministic terminal-creation helper with its consent-bound Orca identity, provider identity, logical argument vector, `current` worktree selector, and non-expanding JSON stdin. Do not call `orca terminal create` through a shell command assembled by the coordinator.

Wait for TUI readiness, verify the requested lead identity when the provider exposes it, and inject one Dispatch. A helper failure or missing or mismatched requested lead stops before source-bearing Dispatch. Record the exact created terminal as workflow-owned.

The Task contains the target inspector result, review focus, authority paths, included and excluded state, static-review restrictions, required report fields, and any provider-specific role guidance. Do not include suspected findings or intended fixes.

Use event-driven waits for `worker_done`, `escalation`, and `question`, with a cumulative 30-minute default liveness budget and a user update at least once per minute. A checkpoint timeout inside the budget is not failure. At budget exhaustion inspect authoritative worker state once, keep an active or unproven worker intact, and require explicit user direction for more waiting or cancellation.

After one accepted `worker_done`, read the complete authoritative transcript, settle the worker through the current guide, process the complete Delivery, and acknowledge it only after required release or retention succeeds. For a low-level provider terminal, close only the exact workflow-created terminal after terminal settlement; never close it after a timeout, question, escalation, heartbeat, or unproven completion.

Follow the live guide's current recovery and FIFO rules rather than duplicating a fixed batch-drain protocol here. Never retry, replace, switch provider, release an active worker, or reinterpret an operational failure as a technical verdict.
