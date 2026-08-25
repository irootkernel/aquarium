# ADR-0002: Keep Workflow Authority Planes Separate

**Status:** `Accepted`

**Recorded:** `2026-08-25`

This is a retrospective record of current repository authority, not a claim about the original adoption date.

## Context

Aquarium workflows observe product contracts, roadmap status, Procedure execution, Git state, Codex goal state, external tool runs, and distribution state. These sources change independently and answer different questions. Collapsing them into one status risks declaring work complete when only one plane advanced.

## Decision

Keep the following authority planes separate: shipped workflow contract, canonical roadmap, Podway runtime, Git repository state, Codex goal state, native tool runtime, and distribution state. Each workflow reads the exact owner needed for its current decision and updates only the plane it is authorized to mutate.

Handoffs carry bounded identity and evidence; they do not synchronize owners implicitly. Completion requires the owning workflow's acceptance criteria across every relevant plane. Cross-repository closure requires the exact downstream commit and independent revalidation rather than a consumer assertion alone.

## Consequences

- A green validator, completed Procedure node, local commit, or host goal can be reported accurately without being promoted to overall completion.
- Orchestrators must re-observe state after effects and reconcile disagreements explicitly.
- Reports are more verbose about evidence boundaries but safer under interruption, concurrency, and cross-repository delivery.
- No single status command is expected to answer every lifecycle question.

## Rejected Alternatives

- Treating Podway as the canonical roadmap was rejected because runtime sessions do not own durable delivery identity.
- Treating Git commits as workflow completion was rejected because acceptance, external dependencies, and distribution may remain unresolved.
- Treating a Codex goal as project state was rejected because host lifecycle is conversational and not repository authority.

## References

- [Documentation governance](../../plugins/aquarium/references/documentation-governance.md)
- [Podway integration](../../plugins/aquarium/references/podway-integration.md)
- [Task handler](../../plugins/aquarium/skills/task-handler/SKILL.md)
- [Epic handler](../../plugins/aquarium/skills/epic-handler/SKILL.md)
- [State and evidence architecture](../architecture/state-and-evidence.md)
