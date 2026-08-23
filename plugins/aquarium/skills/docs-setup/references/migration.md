# Documentation and Roadmap Migration

Read this reference only for `migrate`.

## Identifier Eligibility

An epic ID may migrate only when the epic status is exactly `Planned` and every child task is exactly `Planned`. A task may migrate only as part of such an eligible epic. Preserve `In Progress`, `In Review`, `Completed`, `Deferred`, `Blocked`, unknown, missing, and archived identities.

If the roadmap uses another word for pre-start work, adoption may retain it, but it is not eligible for this default migration. Lifecycle normalization requires separate explicit scope.

Stop when an affected roadmap has unresolved conflicts, duplicate current identities, an active work unit, ambiguous task ownership, or references that cannot be safely rewritten. Never infer migration eligibility from identifier shape or document location.

## Mapping

Inventory epic and task identities across the canonical roadmap, archives, migration records, tracked documentation, tests, schemas, generated sources, protocol metadata, and other regular non-sensitive tracked text.

Reserve every number ever observed for each ID kind in the roadmap namespace. Allocate new `EPIC-NNN` and `TASK-NNN` values independently, each starting after the greatest reserved number of the same kind and preserving current roadmap order. Never move a task across epic boundaries or consolidate work merely to obtain a tidy sequence. A Planned epic with no child tasks is eligible for an epic-only identifier migration.

For a directory roadmap, write `id-migrations/YYYY-MM-DD.md` below the canonical roadmap. For a file roadmap such as `docs/ROADMAP.md`, write it below a sibling `docs/id-migrations/` directory. Record the canonical roadmap, migration date, exact scope, and a table with `Old ID`, `New ID`, `Kind`, `Title`, and optional `Preserved Historical Paths`. That optional cell contains exact backtick-wrapped repository-relative paths separated by `<br>`; it accepts no absolute paths, parent traversal, or globs. The old ID remains a search aid only and must not be accepted as current handler input.

## Atomic Rewrite

Before approval, show every mapping and every tracked occurrence classified as `rewrite`, `migration record`, `preserved historical`, or `unverifiable`. Include non-Markdown checked artifacts and generated-source authorities. Do not update only the roadmap.

Apply all current-reference rewrites and the permanent mapping in one approved change. Afterward, an old ID may remain only in the migration record, immutable Git history, an `archive/` or `archives/` directory owned by that canonical roadmap, an exact path declared in `Preserved Historical Paths`, or a reported unverifiable binary/external location.

Run the bundled inspector and every repository-native checker covering the affected formats. A green link or regex check proves only that bounded condition; verify roadmap ownership, task containment, lifecycle preservation, schema validity, and generated-contract consistency separately.

## Path and Profile Migration

Path or profile migration does not change roadmap identifiers or lifecycle state and is not subject to the identifier-eligibility rule above. It may proceed while work is active only when the selected canonical owners remain unambiguous, every tracked reference and repository instruction can be rewritten atomically, and the approved diff preserves current roadmap and history contents byte-for-byte apart from necessary path references. Stop on an unresolved ownership conflict, an unsafe reference, or concurrent drift in any affected path.
