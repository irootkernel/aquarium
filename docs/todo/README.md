# TODO Candidates and Roadmap Work Dossiers

This index owns future epic-sized development candidates that have not entered the roadmap and catalogs optional detailed work dossiers referenced by complex adopted roadmap epics. It never assigns roadmap IDs, dependencies, ordering, or lifecycle status; [`docs/roadmap/README.md`](../roadmap/README.md) remains the sole authority for those fields.

When the [Epic Execution SOT contract](../../plugins/aquarium/references/epic-execution-sot.md) requires one, an adopted work dossier declares its exact consumer roadmap epics and temporarily owns their detailed goal, purpose, scope, approach, task checklists, exclusions, and acceptance evidence contract. Checklist state is review evidence, not roadmap lifecycle state. Each task promotes accepted durable information to specifications, architecture, ADRs, implementation tips, operations, or public documentation while keeping the dossier current for remaining tasks and consumer epics.

Before an epic becomes `Completed`, its final closeout must classify and promote that epic's remaining durable statements and replace its `Detailed SOT` with valid `Canonical Outcomes` links. If another non-terminal consumer epic or canonical roadmap reference remains, keep the shared dossier and this index entry. Only the last consumer epic's closeout removes the index entry and deletes the declared dossier file without archiving a copy, after every consumer is successfully terminal and the approved deletion envelope includes that action. Git history preserves a deleted dossier.

## Adopted Roadmap Work Dossiers

- [Aquarium development environment dossier](TODO-DEV-AQUARIUM.md) provides the detailed contract for `EPIC-002` and `TASK-005` through `TASK-015`.

## Unadopted TODO Candidates

There are no current unadopted TODO candidates. A work-definition workflow promotes an approved candidate by allocating the next roadmap-local epic and task IDs, applying the shared dossier threshold, and moving or linking only the resulting approved documents in one reviewed change.
