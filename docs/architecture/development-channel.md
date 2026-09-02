# Development Channel Architecture

The development channel separates repository production from host-local consumption:

1. A native post-commit marker queues only a completed canonical local-`main` SHA.
2. One project publisher serializes requests, builds committed bytes into fresh staging, validates the producer manifest and checksum, and promotes an immutable generation.
3. Foreground producers advance one atomic `current/<project-id>` selector immediately. Managed-service producers first advance `pending/<project-id>` and retain the old command and service until a separately approved producer-controller transition succeeds.
4. Command entries in `bin/<project-id>` are stable indirections through current. Publication, activation, and cleanup use generation and service locks so a generation is never mutated or removed while selected or in use.
5. The `aquarium-dev` launcher preserves the caller's inherited environment. An absent foreground generation alone may fall back to the caller's global PATH outside both Aquarium roots; a managed service requires a matching ready or busy development generation and otherwise fails closed without production fallback.

All owned development state is below `~/.aquarium-dev/`: enrollment records, queues, bounded diagnostics, immutable artifacts, current and pending selectors, locks, and opaque producer-owned managed-service runtime. Repositories keep only the producer targets and an exact Aquarium marker inside their native hook. No `.aquarium` repository state is created, and production state below `~/.aquarium/` is not read or changed by this channel.

The Aquarium marketplace artifact contains committed marketplace metadata and the complete committed plugin tree. Only the copied plugin manifest is derived: its stable version gains `-dev.<sha12>`. The manifest checksum covers the resulting canonical directory tree, binding plugin code and bundled skills to one generation.

Aquarium does not construct a second Codex environment. The launcher preserves the caller's `CODEX_HOME` and all other environment values except for the intentional PATH prefix. Authentication, plugin configuration, and MCP configuration stay with the caller and their selected Codex home.

Dolgorae may join this development graph as a foreground executable producer only when its repository commits an approved producer implementation and explicitly enrolls that canonical checkout. Until then, the launcher falls back to the required global executable; if neither generation exists, it fails closed and requests `$aquarium:dev-setup`. Podway is the first required managed-service producer: its immutable bundle owns the development-safe command and generic controller entrypoints, while Podway retains every LaunchAgent, daemon, socket, registry, and recovery decision. Independent Review separately resolves and validates only the official global Dolgorae release, while Orca Review launches the requested native reviewer through Orca and does not use Dolgorae. Aquarium never treats a development generation as a production review runtime. Podway, Mulgae, Gaori, and Dolgorae form the required production global-binary baseline; Sanho is explicitly optional.
