# Changing the Development Channel

Read the [`aquarium-dev` skill](../../plugins/aquarium/skills/aquarium-dev/SKILL.md) and its [shared contract](../../plugins/aquarium/skills/aquarium-dev/references/development-contract.md) before changing the manager or a producer. Keep repository production behind the two common Make targets; the manager must not infer project-specific build commands or artifact layouts.

Producer changes need focused tests for clean local-main admission, committed-byte provenance, exact SHA and development-version identity, output containment, and checksum validation. Manager changes need failure-path coverage for approvals, enrollment ownership, atomic publication, executable-selector replacement, cleanup, and diagnostics. Launcher changes must prove that `~/.aquarium-dev/bin` alone is prepended and that the caller's remaining environment, including `CODEX_HOME`, is preserved.

Preserve the distinction between local development evidence and stable release evidence. An external producer handoff should identify its exact clean local-main commit and include both target outputs, checksum proof, embedded runtime identity diagnostics, and focused tests. Aquarium can consume that handoff but does not own or implement the external repository's build or release behavior.
