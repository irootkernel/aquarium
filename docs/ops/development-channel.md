# Development Channel Runbook

## Target and Prerequisites

This runbook is for an Aquarium maintainer operating a named canonical checkout on Apple Silicon macOS. The checkout must be a regular Git root on local `main` and expose both development producer Make targets. Start through `$aquarium:aquarium-dev`; the skill owns approval handling and command paths.

Development setup changes only the named checkout's Aquarium hook marker and host-local state below `~/.aquarium-dev/`. Enrollment, hook mutation, build, and installation of `~/.local/bin/aquarium-dev` each require separate approval. The workflow does not configure Codex, authentication, plugins, or MCP servers.

## Diagnose and Establish

1. Invoke `$aquarium:aquarium-dev` for the exact checkout and review its read-only diagnostic report.
2. Resolve any reported non-main, dirty-tree, identity, producer, enrollment, or hook condition before approving an effect.
3. Approve enrollment and the exact native hook marker independently. Re-enrollment additionally requires approval to transfer ownership from the displayed old checkout.
4. Approve the initial build. Success requires a healthy current generation whose SHA, development version, artifact path, and checksum match the committed checkout.
5. Separately approve installation of the exact launcher at `~/.local/bin/aquarium-dev`.
6. Run `aquarium-dev <tool> [args...]` and confirm that a selected executable resolves from `~/.aquarium-dev/bin`, a missing development generation resolves only that tool from the caller's global PATH outside both Aquarium roots, and the caller's remaining environment is unchanged. Unknown commands and invalid selected generations must fail.

Success means enrollment and the owned hook are healthy, the atomic current selector and stable executable indirection resolve one validated generation, and the launcher preserves the caller's selected `CODEX_HOME`. Dolgorae is not enrolled here; reviews require the verified global release.

## Updates and Repair

A successful commit on enrolled canonical local `main` queues an asynchronous exact-SHA build. Use diagnosis to confirm publication. Use the skill's explicit rebuild operation, with build approval, when the bounded diagnostic requests it; no additional commit is required. Use approved hook repair only for the exact stale owned marker. Never edit enrollment JSON, selectors, manifests, locks, or hook markers manually.

A failed build preserves the previous current artifact. A missing or corrupt artifact, checkout mismatch, or invalid enrollment fails closed. Stop and follow the machine-reported action. Escalate when repair would require replacing ambiguous hook content, selecting another canonical checkout, changing producer code, or touching state outside the displayed Aquarium-owned paths.

Do not place development state under `~/.aquarium/`, and do not treat a successful development run as release QA or distribution evidence.
