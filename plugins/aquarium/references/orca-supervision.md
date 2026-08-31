# Orca Review Supervision

This is the execution backend for `$aquarium:orca-review`. Review semantics belong to [review-contract.md](review-contract.md); Orca owns only its native Run, Task, Dispatch, Codex worker, Delivery, acknowledgement, settlement, and recovery lifecycle.

Require the separately installed `$orca-cli` skill. Resolve one Orca command exactly as that skill requires, load its version-matched `orca-cli` and `orchestration` guides, and confirm a ready local runtime. Reject nonempty `ORCA_ENVIRONMENT` or `ORCA_PAIRING_CODE`; do not route review source to a paired or remote runtime.

Use the original registered checkout and its proven `current` worktree. Do not create or register a temporary repository snapshot or another Git worktree. The target inspector result, Git object or index bytes, and included paths define reviewer scope; current worktree bytes outside that target are excluded even though the same operating-system user can technically read them.

Create one Run and one Task, then start one fresh Codex through the live guide's supervised `worker-start --worktree current --agent codex` path. Do not reuse a terminal, create a low-level provider terminal, select a non-Codex provider, or use Dolgorae.

The Task contains the complete target-inspector result, exact resolved Git identity, target digest, review focus, authority paths, included and excluded state, static-review restrictions, and required report fields. Do not include suspected findings or intended fixes. Inject it in one Dispatch only after the target and repository-state baseline are revalidated.

Use event-driven waits for `worker_done`, `escalation`, and `question`, with a cumulative 30-minute default liveness budget and a user update at least once per minute. A checkpoint timeout inside the budget is not failure. At budget exhaustion inspect authoritative worker state once, keep an active or unproven worker intact, and require explicit user direction for more waiting or cancellation.

After one accepted `worker_done`, read the complete authoritative transcript, settle the worker through the current guide, process the complete Delivery, and acknowledge it only after required release or retention succeeds. Follow the live guide's current recovery and FIFO rules rather than duplicating a fixed batch-drain protocol here. Never retry, replace, switch reviewer, release an active worker, or reinterpret an operational failure as a technical verdict.
