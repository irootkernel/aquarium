# Documentation Governance

Use this contract when `$aquarium:docs-setup` establishes a repository documentation model or `$aquarium:new-project` creates its first documentation set.

## Semantic Roles

Documentation paths may vary, but each delivery scope must assign one canonical owner to every role below.

- `specs` owns required or implemented behavior and durable product contracts.
- `architecture` owns current components, boundaries, data flow, and responsibility.
- `architecture-decision-records` preserves accepted, superseded, deprecated, and rejected decisions with their rationale.
- `implementation-tips` contains non-normative guidance for changing, testing, operating, or releasing the implementation.
- `roadmap` alone owns adopted epic and task identity, ordering, dependencies, lifecycle vocabulary, and current status.
- `todo` owns future development candidates that have not entered the roadmap.
- `deferred-feedback` owns small actionable findings intentionally postponed from current work.

Promote an oversized deferred finding to one TODO candidate or an adopted roadmap work unit. Do not let TODO or deferred feedback become a second status authority. Keep generated documentation, runtime logs, provider reports, temporary plans, and ignored workflow evidence outside these canonical roles.

Every role directory contains a `README.md` index. A repository may add examples, guides, design specifications, runbooks, archives, or executable contracts when its root documentation index states their owner and relationship to the seven roles.

## Profiles

Use `single-scope` when one implementation owner has one canonical roadmap. The defaults are the seven role directories directly below `docs/`, with `docs/roadmap/README.md` as the roadmap.

Use `multi-scope` when independently delivered surfaces such as server, app, and dashboard have separate implementation owners or roadmaps. A shared `docs/project/` scope may own only shared specifications, architecture, and decisions; each delivery scope owns the complete seven-role set and its own roadmap. Cross-scope work belongs to linked work units in the owning delivery roadmaps, not a synthetic project roadmap.

Use `legacy-adopt` when existing paths or identifiers are already authoritative and moving them is not approved. Map every existing path to exactly one semantic role in the root documentation index, report missing or competing owners, and preserve established valid identifiers. Adoption is not migration.

The root `docs/README.md` is the human-readable documentation index. It records the selected profile, delivery scopes, role-to-path ownership, canonical roadmap paths, roadmap identity contract, source-of-truth precedence, language, and repository-native documentation checks. It is documentation authority, not Aquarium state. Do not create `.aquarium`, a hidden selector, a generated mirror, or another project-state manifest.

## New Roadmap Identity

For a new `single-scope` or `multi-scope` roadmap, use these defaults unless the user explicitly approves another repository-local contract:

- Epic IDs match `EPIC-[0-9]{3,}`.
- Task IDs match `TASK-[0-9]{3,}`.
- Epic and task sequences are independent and monotonic within one canonical roadmap, including its archive and migration records.
- Task numbering does not restart for each epic.
- A number is never reused, including after deletion, deferral, archival, or migration.
- Identity does not encode execution order; roadmap order and dependencies do.
- The canonical roadmap path is the namespace. A cross-scope reference names both the scope or roadmap and the ID; use `scope:ID` when the reference must be machine-readable.

New allocations use the greatest number ever present for that ID kind in the namespace plus one. Preserve an established legacy scheme under `legacy-adopt`; do not classify semantic codes, slugs, compact historical IDs, or unpadded historical IDs as defects until migration to the new contract is explicitly selected.

## Lifecycle and History

The roadmap defines its own lifecycle vocabulary. New roadmaps default to `Planned`, `In Progress`, `In Review`, `Completed`, `Deferred`, and `Blocked`; an existing roadmap keeps its established vocabulary unless lifecycle normalization is separately approved.

Epic status remains independent of child task status. Completing every child does not complete the epic without the repository's explicit epic acceptance.

Do not move or rewrite completed history merely to normalize layout. Archives are optional compaction owned by repository policy. Specifications describe current behavior; roadmaps and archives describe delivery state and history.
