# Changing the Development Channel

Read the [`dev-aquarium` skill](../../plugins/aquarium/skills/dev-aquarium/SKILL.md) and its [shared contract](../../plugins/aquarium/skills/dev-aquarium/references/development-contract.md) before changing the manager or a producer. Keep repository production behind the two common Make targets; the manager must not infer project-specific build commands or artifact layouts.

Producer changes need focused tests for clean local-main admission, committed-byte provenance, exact SHA and development-version identity, output containment, and checksum validation. Manager changes need failure-path coverage for approvals, enrollment ownership, atomic publication, fail-closed resolution, lease races, cleanup, and diagnostics. Codex changes additionally need an isolated-home scenario that proves stable-home state is untouched, login remains a user action, the plugin and bundled skills share one generation, and MCP launch resolves the enrolled external artifact.

Preserve the distinction between local development evidence and stable release evidence. An external producer handoff should identify its exact clean local-main commit and include both target outputs, checksum proof, embedded runtime identity diagnostics, and focused tests. Aquarium can consume that handoff but does not own or implement the external repository's build or release behavior.
