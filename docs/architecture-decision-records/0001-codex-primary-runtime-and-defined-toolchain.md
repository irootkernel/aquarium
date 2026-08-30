# ADR-0001: Use Codex as the Primary Runtime and Keep the Toolchain Upstream

**Status:** `Accepted`

**Recorded:** `2026-08-25`

This is a retrospective record of current repository authority, not a claim about the original adoption date.

## Context

Aquarium coordinates several specialized developer tools and upstream agent skills. Copying those implementations into the plugin would blur ownership, release cadence, licensing, security updates, and runtime responsibility. Supporting multiple primary agent runtimes would also multiply workflow and approval semantics.

## Decision

Codex is Aquarium's primary workflow runtime. Aquarium integrates independently installed Dolgorae, Orca, Podway, Sanho, Mulgae, Gaori, Ouroboros, Lora, Lore, and Deslop through explicit supported interfaces and version ranges where declared.

Aquarium does not vendor their implementation or documentation sources. Setup workflows inspect and install exact approved upstream distributions or skill files, preserve provenance, and keep provider use separately authorized. An installed binary, MCP registration, native configuration, live tool exposure, and release artifact are reported as separate readiness dimensions.

## Consequences

- Aquarium can evolve its orchestration contracts without becoming the release owner for external tools.
- Maintainers must keep compatibility declarations, setup guidance, privacy disclosures, and tests synchronized with upstream interfaces.
- Missing or unsupported tools produce bounded setup or readiness results rather than hidden fallback implementations.
- Other runtimes may be invoked through an explicit integration such as Orca, but they do not replace Codex as the workflow authority.

## Rejected Alternatives

- Vendoring upstream tool or skill sources was rejected because it creates stale forks and ambiguous ownership.
- Treating every agent host as an equivalent primary runtime was rejected because approval, tool exposure, and lifecycle semantics are not interchangeable.
- Inferring readiness from a command name on `PATH` was rejected because installation identity, version, configuration, and live exposure are distinct facts.

## References

- [Development setup skill](../../plugins/aquarium/skills/dev-setup/SKILL.md)
- [Ouroboros integration](../../plugins/aquarium/references/ouroboros-integration.md)
- [Public product overview](../../README.md)
- [Privacy policy](../../PRIVACY.md)
- [Terms](../../TERMS.md)
