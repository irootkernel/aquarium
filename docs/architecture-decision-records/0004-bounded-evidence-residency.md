# ADR-0004: Keep Runtime Evidence Native and Promote Only Bounded Artifacts

**Status:** `Accepted`

**Recorded:** `2026-08-25`

This is a retrospective record of current repository authority, not a claim about the original adoption date.

## Context

Podway, Mulgae, Gaori, Orca, terminals, and other tools produce rich local runtime records. Tracking those directories would mix volatile execution state, transcripts, unrelated source, and possibly sensitive content with durable repository documentation. Some downstream workflows still need stable evidence references.

## Decision

Keep native runtime evidence in the owning tool's ignored local storage. Do not treat it as specifications, roadmap history, or architecture authority. When a durable downstream consumer has a verified need, promote only a reviewed, bounded, non-sensitive structured artifact under `evidence/aquarium/`, unless the repository declares an exact relative `Aquarium evidence root` in project configuration.

A promoted artifact identifies its producer, exact target revision, scope, result, and limitations. It excludes credentials, raw transcripts, ambient runtime history, and unrelated repository content. Promotion requires deliberate review and follows the normal documentation and Git approval boundaries.

## Consequences

- Native tools retain complete runtime ownership and can evolve their formats independently.
- Repository history contains only evidence that has a durable consumer and a bounded disclosure surface.
- A run ID or ignored artifact path can support local investigation but is not a stable cross-repository contract.
- Maintainers must state when promoted evidence is development, runtime, or distribution proof.

## Rejected Alternatives

- Tracking complete runtime directories was rejected because they are volatile, noisy, and potentially sensitive.
- Copying raw transcripts into documentation was rejected because it widens disclosure and lacks a stable schema.
- Refusing all durable evidence was rejected because exact cross-repository and release handoffs sometimes require reviewable proof.

## References

- [Evidence residency contract](../../plugins/aquarium/references/evidence-residency.md)
- [Review contract](../../plugins/aquarium/references/review-contract.md)
- [State and evidence architecture](../architecture/state-and-evidence.md)
- [Safety and evidence specification](../specs/safety-and-evidence.md)
