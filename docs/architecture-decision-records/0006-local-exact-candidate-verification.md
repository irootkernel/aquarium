# ADR-0006: Use Local Deterministic and Exact-Candidate Verification

**Status:** `Accepted`

**Recorded:** `2026-08-25`

This is a retrospective record of current repository authority, not a claim about the original adoption date.

## Context

Aquarium is primarily an instruction and local-tooling plugin. Its release safety depends on cross-file contracts, black-box inspector behavior, tool compatibility, and ordered remote publication. Hosted CI would not automatically possess the required local tool state, approvals, credentials, or exact artifact observations.

## Decision

Use deterministic local inspectors and repository tests as development-contract authority. Use the selected local release gate, exact candidate SHA, required official compatibility artifacts, and ordered post-publication observations as distribution authority. This repository does not use GitHub Actions as its release gate.

Structural inspectors remain read-only, local, and conservative. They report only encoded structure. Scenario tests cover behavioral and approval paths. Release QA binds its result to the exact candidate; substantive changes invalidate prior confirmation or QA.

Release-QA evidence is frozen before remediation in a private versioned record. Any bounded confirmation is derived from that record and the exact Git remediation range, admitted through one atomic claim, and completed only when a machine check reconciles every retained scenario and finding reproduction. Human summaries remain useful reports but are not confirmation authority.

## Consequences

- Maintainers can reproduce the authoritative gate from the repository and declared local dependencies.
- Release workflows must distinguish full and light verification and preserve exact candidate identity.
- Green static checks cannot replace scenario evidence, and development binaries cannot replace required official artifacts.
- Publication is incomplete until remote `main`, the peeled tag, and the GitHub Release are re-observed at the intended commit.

## Rejected Alternatives

- Phrase-only validation as complete proof was rejected because it cannot exercise handoffs, failure paths, or effects.
- Hosted CI as the sole release authority was rejected because it does not represent the required local approval and artifact boundaries.
- Reusing test confirmation after functional changes was rejected because the evidence no longer identifies the candidate being released.
- Reconstructing a confirmation matrix from prose after remediation was rejected because omissions, reassignment, and duplicate attempts cannot be detected reliably.

## References

- [Testing contract](../../TESTING.md)
- [Makefile](../../Makefile)
- [Release handler](../../plugins/aquarium/skills/release-handler/SKILL.md)
- [Release QA](../../plugins/aquarium/skills/release-qa/SKILL.md)
- [Verification architecture](../architecture/verification.md)
