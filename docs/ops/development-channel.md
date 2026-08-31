# Development Channel Runbook

## Target and Prerequisites

This runbook is for an Aquarium maintainer operating a named canonical checkout on Apple Silicon macOS. The checkout must be a regular Git root on local `main` and expose both development producer Make targets. Start through `$aquarium:aquarium-dev`; the skill owns approval handling and command paths.

Development setup changes only the named checkout's Aquarium hook marker and host-local state below `~/.aquarium-dev/`. Enrollment, hook mutation, build, managed-service activation, and installation of `~/.local/bin/aquarium-dev` each require separate approval. The workflow does not configure Codex, authentication, plugins, or MCP servers.

## Diagnose and Establish

1. Invoke `$aquarium:aquarium-dev` for the exact checkout and review its read-only diagnostic report.
2. Resolve any reported non-main, dirty-tree, identity, producer, enrollment, or hook condition before approving an effect.
3. Approve enrollment and the exact native hook marker independently. Re-enrollment additionally requires approval to transfer ownership from the displayed old checkout.
4. Approve the initial build. A foreground producer advances its current generation immediately; a managed-service producer publishes one pending generation while preserving its active command and service.
5. For a managed service, inspect the read-only service plan and separately approve application of its exact plan token. Success requires the producer-owned controller to report the target generation ready before Aquarium advances current.
6. Separately approve installation of the exact launcher at `~/.local/bin/aquarium-dev`.
7. Run `aquarium-dev <tool> [args...]` and confirm that a selected command resolves from `~/.aquarium-dev/bin`, an absent foreground generation resolves only that tool from the caller's global PATH outside both Aquarium roots, and the caller's remaining environment is unchanged. A managed service must match the selected generation and must fail closed without production fallback when absent, pending, stopped, mismatched, or recovering. Unknown commands and invalid selected generations must fail.

Success means enrollment and the owned hook are healthy, the atomic current selector and stable command indirection resolve one validated generation, every managed service reports that exact generation ready or busy, and the launcher preserves the caller's selected `CODEX_HOME`. Each tool repository performs this enrollment when its approved producer commit is created. Dolgorae production reviews continue to require the verified global release even after a development generation is enrolled. Production readiness separately requires supported global Podway, Mulgae, Gaori, and Dolgorae binaries; Sanho is optional.

## Updates and Repair

A successful commit on enrolled canonical local `main` queues an asynchronous exact-SHA build. Use diagnosis to confirm publication. Use the skill's explicit rebuild operation, with build approval, when the bounded diagnostic requests it; no additional commit is required. Use approved hook repair only for the exact stale owned marker. Never edit enrollment JSON, selectors, manifests, locks, or hook markers manually.

A failed build or service activation preserves the previous current artifact. A managed-service build may remain pending while the producer reports busy. A missing or corrupt artifact, checkout mismatch, invalid enrollment, controller failure, or service-generation mismatch fails closed. Stop and follow the machine-reported action. Escalate when repair would require replacing ambiguous hook content, selecting another canonical checkout, changing producer code, or touching state outside the displayed Aquarium-owned paths.

Do not place development state under `~/.aquarium/`, and do not treat a successful development run as release QA or distribution evidence.
