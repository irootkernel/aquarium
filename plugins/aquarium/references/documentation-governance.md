# Documentation Governance

Use this contract when `$aquarium:docs-setup` establishes a repository documentation model or `$aquarium:new-project` creates its first documentation set.

## Semantic Roles

Documentation paths may vary, but each delivery scope must assign one canonical owner to every role below.

The repository root `README.md` is the user-facing product entrypoint. It explains what the project is, why it is useful, and how to install or use it. The `docs/` tree is for maintainers and contributors who need the project's structure, contracts, decisions, development guidance, and operational knowledge. Keep that audience boundary explicit even when legacy adoption preserves different paths.

- `specs` owns required or implemented behavior and durable product contracts.
- `architecture` owns current components, boundaries, data flow, and responsibility.
- `architecture-decision-records` preserves accepted, superseded, deprecated, and rejected decisions with their rationale.
- `implementation-tips` contains non-normative guidance for changing, testing, or releasing the implementation.
- `ops` owns environment setup, deployment, configuration, operation, diagnosis, recovery, and first-aid runbooks for real development or service environments.
- `roadmap` alone owns adopted epic and task identity, ordering, dependencies, lifecycle vocabulary, and current status.
- `todo` owns future epic-sized candidates and any temporary development dossiers that the repository or an Aquarium design workflow establishes for adopted epics.
- `deferred-feedback` owns small actionable findings intentionally postponed from current work.

Promote an oversized deferred finding to one TODO candidate or an adopted roadmap work unit. Do not let TODO or deferred feedback become a second status authority. Keep generated documentation, runtime logs, provider reports, temporary plans, and ignored workflow evidence outside these canonical roles.

Every role directory contains a `README.md` index. A repository may add examples, guides, design specifications, archives, or executable contracts when its root documentation index states their owner and relationship to the eight roles.

An operations runbook identifies its target and environment, symptoms or purpose, prerequisites and required authority, safe diagnosis, resolution, success verification, rollback or failure recovery, and escalation owner. It never records credentials or live secret values; use placeholders and reference the owning secret authority instead. If a delivery scope has no independently operated surface, its operations index records that bounded fact and the actual owner instead of inventing a runbook.

## Profiles

Use `single-scope` when one implementation owner has one canonical roadmap. The defaults are the eight role directories directly below `docs/`, with `docs/roadmap/README.md` as the roadmap.

Use `multi-scope` when independently delivered surfaces such as server, app, and dashboard have separate implementation owners or roadmaps. A shared `docs/project/` scope may own only shared specifications, architecture, and decisions; each delivery scope owns the complete eight-role set, including its own operations index and roadmap. Cross-scope work and operations belong to the responsible delivery scope, not a synthetic project roadmap.

Use `legacy-adopt` when existing paths or identifiers are already authoritative and moving them is not approved. Map every existing path to exactly one semantic role in the root documentation index, report missing or competing owners, and preserve established valid identifiers. Adoption is not migration.

The root `docs/README.md` is the human-readable documentation index. It records the selected profile, delivery scopes, role-to-path ownership, canonical roadmap paths, roadmap identity contract, source-of-truth precedence, language, and repository-native documentation checks. It is documentation authority, not Aquarium state. Do not create `.aquarium`, a hidden selector, a generated mirror, or another project-state manifest.

## Optional Work Dossiers

An unadopted `TODO-*.md` file represents one future epic-sized idea and owns no roadmap identity or lifecycle state. A repository may retain it as a temporary execution dossier when a work-definition workflow adopts the epic, or may keep a smaller epic's execution requirements in the roadmap and canonical role owners. Dossier need, creation, consumption, and closeout belong to the shared [Epic Execution SOT](epic-execution-sot.md) contract, not to `docs-setup`.

When a dossier exists, the TODO index records it without becoming a second lifecycle authority. Promote accepted durable information to its owner: behavior to specifications, structure to architecture, rationale to an ADR, development guidance to implementation tips, operational guidance to operations, and user value or usage to the root README.

The bundled inspector reports explicit roadmap links and verifies their safe in-repository targets. It does not require a dossier, interpret prose, decide execution complexity, enforce a documentation lifecycle, certify semantic completeness, or establish implementation or runtime truth.

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
