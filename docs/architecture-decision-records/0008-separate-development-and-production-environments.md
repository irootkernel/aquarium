# ADR-0008: Separate Development and Production Environments

**Status:** `Accepted`

**Recorded:** `2026-08-31`

**Supersedes:** [ADR-0007](0007-host-local-immutable-development-artifacts.md)

## Context

The first development-channel design stored development artifacts and a dedicated Codex home below `~/.aquarium/`, and it enrolled Dolgorae as another source-built producer. That mixed unreleased development state with Aquarium's production namespace, duplicated Codex configuration and authentication concerns, and created a private Dolgorae runtime even though production reviews should use the official globally installed release.

Development artifacts still need exact clean-local-main provenance, immutable publication, cooperative hooks, atomic selection, and bounded recovery. Those properties do not require Aquarium to own a Codex home or to replace production tools.

## Decision

Reserve `~/.aquarium/` for production state. Place all Aquarium-owned development-channel metadata and artifacts below `~/.aquarium-dev/`, including stable executable indirections in `~/.aquarium-dev/bin/` backed by atomic current selectors.

Install a separately approved user-local launcher at `~/.local/bin/aquarium-dev`. It prepends only `~/.aquarium-dev/bin` to `PATH` and otherwise inherits the caller's environment, including `CODEX_HOME`. Aquarium does not create or manage a Codex home, authentication, plugin installation, or MCP configuration for this channel.

Support Aquarium, Podway, Mulgae, Gaori, and Sanho as development producers. Exclude Dolgorae. Independent Review resolves the globally installed official Dolgorae release and revalidates its pinned version, executable checksum, and required capabilities immediately before use. Orca Review launches Codex directly through Orca and does not use Dolgorae. Aquarium does not create a private Dolgorae execution copy.

Retain the exact committed producer contract, immutable generation promotion, atomic generation selection, bounded native hook marker, per-effect approvals, and fail-closed diagnosis. A development artifact remains integration evidence only and cannot satisfy release or distribution gates.

Resolve each supported executable independently: prefer its selected immutable development generation, fall back to the caller's global PATH only when that generation is absent, and fail closed when selected development state is invalid. Exclude both Aquarium roots from global resolution so production and development state cannot recursively masquerade as a global installation.

## Consequences

- Production and unreleased development state have disjoint roots.
- Developers select a Codex home through their normal environment instead of synchronizing a second Aquarium-owned configuration.
- Executable producers are selected uniformly through one PATH prefix.
- Dolgorae has one production installation and one release identity to audit for Independent Review; Orca Review has no Dolgorae dependency.
- Existing `~/.aquarium` development state must be migrated only after the new committed development manager can rebuild the corresponding generation; preserved audit records and legacy Codex data are not silently deleted.

## Rejected Alternatives

- Keeping development state under `~/.aquarium/` was rejected because the path is production-owned.
- Renaming only the launcher while retaining the old root was rejected because it would preserve the state collision.
- Continuing to manage an isolated Codex home was rejected because environment selection already belongs to the caller.
- Keeping Dolgorae as both a development producer and a stable private copy was rejected because production review must use the official global release.

## References

- [Aquarium development environment dossier](../todo/TODO-AQUARIUM-DEV.md)
- [Development channel specification](../specs/development-channel.md)
- [Separate effect approvals](0005-separate-effect-approvals.md)
