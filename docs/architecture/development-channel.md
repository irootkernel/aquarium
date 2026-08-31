# Development Channel Architecture

The development channel separates repository production from host-local consumption:

1. A native post-commit marker queues only a completed canonical local-`main` SHA.
2. One project publisher serializes requests, builds committed bytes into fresh staging, validates the producer manifest and checksum, and promotes an immutable generation.
3. One atomic `current/<project-id>` selector chooses a completely validated generation; executable `bin/<project-id>` entries are stable indirections through it.
4. Publication and cleanup use generation locks so a generation is never mutated and an in-use artifact is not removed.
5. The `aquarium-dev` launcher preserves the caller's inherited environment, prefers a supported executable through the development bin directory, and falls back only a missing command to the caller's global PATH outside both Aquarium roots.

All owned development state is below `~/.aquarium-dev/`: enrollment records, queues, bounded diagnostics, immutable artifacts, selectors, and locks. Repositories keep only the producer targets and an exact Aquarium marker inside their native hook. No `.aquarium` repository state is created, and production state below `~/.aquarium/` is not read or changed by this channel.

The Aquarium marketplace artifact contains committed marketplace metadata and the complete committed plugin tree. Only the copied plugin manifest is derived: its stable version gains `-dev.<sha12>`. The manifest checksum covers the resulting canonical directory tree, binding plugin code and bundled skills to one generation.

Aquarium does not construct a second Codex environment. The launcher preserves the caller's `CODEX_HOME` and all other environment values except for the intentional PATH prefix. Authentication, plugin configuration, and MCP configuration stay with the caller and their selected Codex home.

Dolgorae is outside this development graph. Independent Review resolves `dolgorae` from the current PATH and immediately validates the official v0.1.0 executable identity and capabilities before use. Orca Review launches Codex through Orca and does not use Dolgorae. Aquarium neither enrolls a Dolgorae source checkout nor creates a private runtime copy.
