# Development Channel Runbook

## Target and Prerequisites

This runbook is for an Aquarium maintainer operating a named canonical checkout on Apple Silicon macOS. The checkout must be a regular Git root on local `main` and expose both development producer Make targets. Start through `$aquarium:dev-aquarium`; the skill owns approval handling and command paths.

Development setup changes only the named checkout's Aquarium hook marker and host-local state below `~/.aquarium/`. Enrollment, hook mutation, build, and isolated Codex configuration each require separate approval. Authentication is always a direct user action.

## Diagnose and Establish

1. Invoke `$aquarium:dev-aquarium` for the exact checkout and review its read-only diagnostic report.
2. Resolve any reported non-main, dirty-tree, identity, producer, enrollment, or hook condition before approving an effect.
3. Approve enrollment and the exact native hook marker independently. Re-enrollment additionally requires approval to transfer ownership from the displayed old checkout.
4. Approve the initial build. Success requires a healthy current generation whose SHA, development version, artifact path, and checksum match the committed checkout.
5. From the Aquarium checkout, separately approve isolated Codex configuration. This installs the exact Aquarium generation and reconciles only enrolled MCP integrations.
6. If diagnosis reports `codex_login_required`, run the exact displayed `CODEX_HOME=~/.aquarium/codex codex login` action yourself, then repeat approved configuration or diagnosis.

Success means enrollment and the owned hook are healthy, current is healthy, the isolated plugin and bundled skills report the same development generation, expected enrolled MCP servers are enabled, every enrolled project reports one validated artifact, and isolated login reports ready.

## Updates and Repair

A successful commit on enrolled canonical local `main` queues an asynchronous exact-SHA build. Use diagnosis to confirm publication. Use the skill's explicit rebuild operation, with build approval, when the bounded diagnostic requests it; no additional commit is required. Use approved hook repair only for the exact stale owned marker. Never edit enrollment JSON, selectors, manifests, locks, or hook markers manually.

A failed build preserves the previous current artifact. A missing or corrupt artifact, checkout mismatch, or invalid enrollment fails closed and never falls back to a stable tool. Stop and follow the machine-reported action. Escalate to the Aquarium maintainer when repair would require replacing ambiguous hook content, selecting another canonical checkout, changing producer code, or touching state outside the displayed Aquarium-owned paths.

Do not copy stable Codex configuration or credentials, and do not treat a successful development run as release QA or distribution evidence.
