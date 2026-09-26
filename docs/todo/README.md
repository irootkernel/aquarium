# TODO Candidates and Roadmap Work Dossiers

This index owns future epic-sized development candidates that have not entered the roadmap and catalogs optional detailed work dossiers referenced by complex adopted roadmap epics or standing-group tasks. It never assigns roadmap IDs, dependencies, ordering, or lifecycle status; [`docs/roadmap/README.md`](../roadmap/README.md) remains the sole authority for those fields.

When the [Epic Execution SOT contract](../../plugins/aquarium/references/epic-execution-sot.md) requires one, an adopted work dossier declares its exact consumer roadmap epics or standing-group tasks and temporarily owns their detailed goal, purpose, scope, approach, task checklists, exclusions, and acceptance evidence contract. Checklist state is review evidence, not roadmap lifecycle state. Each task promotes accepted durable information to specifications, architecture, ADRs, implementation tips, operations, or public documentation while keeping the dossier current for all remaining consumers.

Before an epic becomes `Completed`, its final closeout must classify and promote that epic's remaining durable statements and replace its `Detailed SOT` with valid `Canonical Outcomes` links. If another non-terminal consumer epic or canonical roadmap reference remains, keep the shared dossier and this index entry. Only the last consumer epic's closeout removes the index entry and deletes the declared dossier file without archiving a copy, after every consumer is successfully terminal and the approved deletion envelope includes that action. Git history preserves a deleted dossier.

For a dossier linked only from a task in the standing `EPIC-000`, settle its durable content and remove its task link and index entry at that task's approved closeout. Delete the dossier then if no other roadmap consumer remains.

## Adopted Roadmap Work Dossiers

- [Aquarium development environment dossier](TODO-AQUARIUM-DEV.md) provides the detailed contract for `EPIC-002`, `TASK-005` through `TASK-015`, historical `TASK-024`, corrective `TASK-031`, producer integration `TASK-042`, and the withdrawal rationale for `TASK-041`.
- [Astra skill modernization dossier](TODO-ASTRA-SKILLS.md) defines the scope and
  acceptance for `EPIC-012`, `TASK-043` through `TASK-046`, and the local producer
  source checks needed for integration.
- [Web Pro Review dossier](TODO-WEB-PRO-REVIEW.md) defines the standalone review,
  primary-account boundary, selectable `web-pro` route, and acceptance contract for
  `EPIC-017` and `TASK-072` through `TASK-075`.
- [Workflow review corrections dossier](TODO-WORKFLOW-REVIEW-CORRECTIONS.md) maps
  the 2026-09-25 review findings, Aquarium-owned corrections, producer requests,
  and acceptance for `EPIC-018` and `TASK-077` through `TASK-085`.

## Unadopted TODO Candidates

There are no current unadopted TODO candidates. A work-definition workflow promotes an approved candidate by allocating the next roadmap-local epic and task IDs, applying the shared dossier threshold, and moving or linking only the resulting approved documents in one reviewed change.
