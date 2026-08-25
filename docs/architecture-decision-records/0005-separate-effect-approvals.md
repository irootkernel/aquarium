# ADR-0005: Require Separate Approval for Distinct Effects

**Status:** `Accepted`

**Recorded:** `2026-08-25`

This is a retrospective record of current repository authority, not a claim about the original adoption date.

## Context

Aquarium workflows can inspect local files, query networks, install tools, edit native configuration, change repositories, transmit source to providers, create commits, push refs, and publish releases. A broad approval such as “set this up” does not communicate informed consent for every possible effect.

## Decision

Preserve explicit approval boundaries between materially distinct effects. Read-only local diagnosis authorizes neither network access nor mutation. Network lookup, installation, native configuration, repository-guidance edits, effectful tests, provider transmission, staging, commits, pushes, tags, and publication follow the exact approval rules of their owning workflows.

Where approval is tied to a displayed diff, exact target, candidate SHA, tool version, or observed remote state, a change to that subject invalidates the approval. Successful completion of one effect does not grant authority for the next.

## Consequences

- Users can authorize the minimum necessary action and evaluate disclosure or recovery risk before each material effect.
- Workflows need explicit proposal, confirmation, stale-approval, and partial-failure handling.
- Batch operations may continue only across targets and effects already covered by the exact authorization.
- Commit authorization never implies push or publication authorization.

## Rejected Alternatives

- Treating invocation as blanket mutation consent was rejected because skill descriptions cover workflows with very different effects.
- Treating setup approval as provider consent was rejected because local configuration and external transmission have different privacy consequences.
- Treating a release commit as publication approval was rejected because remote mutation is separately consequential and recoverable by different means.

## References

- [Development setup skill](../../plugins/aquarium/skills/dev-setup/SKILL.md)
- [Task commit skill](../../plugins/aquarium/skills/task-commit/SKILL.md)
- [Orca supervision](../../plugins/aquarium/references/orca-supervision.md)
- [Release handler](../../plugins/aquarium/skills/release-handler/SKILL.md)
- [Privacy policy](../../PRIVACY.md)
