# ADR-0003: Do Not Create Central Aquarium Project State

**Status:** `Accepted`

**Recorded:** `2026-08-25`

This is a retrospective record of current repository authority, not a claim about the original adoption date.

## Context

A central `.aquarium` file could appear to simplify discovery and lifecycle coordination. In practice it would duplicate manifest, roadmap, Git, Podway, tool, and host state while introducing stale reconciliation rules and an attractive location for credentials or runtime residue.

## Decision

Aquarium does not create, read, or maintain `.aquarium` or any equivalent central project-state file. Repository configuration stays with existing project authorities. Roadmap state remains in canonical documentation, Git state remains in Git, Procedure state remains with Podway, and native tool state remains with each tool.

Multi-repository development setup accepts an explicit external `aquarium.dev-setup-bundle/v1` manifest as request input. It normalizes that input for the current run but does not discover, persist, or adopt it as repository state.

## Consequences

- There is no Aquarium-specific state migration or reconciliation service.
- Workflows must inspect several exact authorities instead of trusting a cached aggregate.
- Repositories avoid a hidden configuration convention and accidental credential collection.
- Bundle callers must supply their manifest explicitly for each setup request.

## Rejected Alternatives

- A tracked central state file was rejected because it competes with established sources of truth.
- An ignored central cache was rejected because it would still influence behavior without reviewable authority.
- Automatic bundle discovery was rejected because it widens filesystem scope and can apply stale setup intent.

## References

- [Development setup skill](../../plugins/aquarium/skills/dev-setup/SKILL.md)
- [Bundle setup skill](../../plugins/aquarium/skills/dev-setup-bundle/SKILL.md)
- [Documentation governance](../../plugins/aquarium/references/documentation-governance.md)
- [Repository operating rules](../../AGENTS.md)
