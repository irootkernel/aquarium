# Documentation Profiles

Read this reference for `bootstrap` or `adopt`.

## Single Scope (`single-scope`)

Use these default paths:

```text
docs/
|-- README.md
|-- architecture/README.md
|-- architecture-decision-records/README.md
|-- deferred-feedback/README.md
|-- implementation-tips/README.md
|-- roadmap/README.md
|-- specs/README.md
`-- todo/README.md
```

The roadmap contains status definitions, an epic summary, one epic section per adopted epic, and a task table below each epic. Use a level-two `## EPIC-NNN: Title` heading, an exact `**Status:** \`Status\`` line within that section, and a Markdown table whose first column header is `Task` and whose rows begin with `TASK-NNN`. A level-two heading ends the preceding epic section even when it is not another epic. Legacy adoption preserves established identifier shapes but uses the same containment signals when the bundled inspector must analyze migration eligibility. Do not create one file per task by default.

Keep small postponed findings in the one deferred-feedback index. A TODO file represents one future epic-sized candidate and stays outside roadmap lifecycle until promotion.

## Multiple Scopes (`multi-scope`)

Use `docs/README.md` for the complete ownership map. `docs/project/` may own shared specifications, architecture, and architecture decisions; those roles are optional, and it has no implementation roadmap, TODO backlog, deferred development findings, or implementation tips.

Each independently delivered scope uses the complete single-scope role set under `docs/<scope>/`. Scope names come from repository ownership, not a fixed server/app/dashboard vocabulary.

Shared work is split into linked work units in the implementation-owning roadmaps. A scope-local ID is always qualified by its scope or canonical roadmap when referenced from another scope.

## Legacy Adoption (`legacy-adopt`)

Map an existing directory or file to a role only when its content and repository guidance establish that ownership. Names alone are insufficient. A file such as `docs/ROADMAP.md`, `docs/adr/README.md`, `docs/guides/`, or `docs/deferred-feedback.md` can remain canonical when its meaning matches the role.

Preserve established archives, semantic epic codes, slug-derived task IDs, adopted design dossiers, and language conventions. Report a missing architecture owner, competing roadmap, mixed current/future specification, or status-bearing TODO as a gap; do not silently declare it conforming.

Adoption writes the minimum root index and missing role indexes needed to make authority discoverable. It does not rename valid paths, normalize IDs, archive history, or rewrite content without a separately approved migration.
