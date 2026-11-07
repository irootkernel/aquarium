# TODO Candidates and Roadmap Work Dossiers

This index owns future epic-sized development candidates that have not entered the roadmap and catalogs optional detailed work dossiers referenced by complex adopted roadmap epics or standing-group tasks. It never assigns roadmap IDs, dependencies, ordering, or lifecycle status; [`docs/roadmap/README.md`](../roadmap/README.md) remains the sole authority for those fields.

When the [Epic Execution SOT contract](../../plugins/aquarium/references/epic-execution-sot.md) requires one, an adopted work dossier declares its exact consumer roadmap epics or standing-group tasks and temporarily owns their detailed goal, purpose, scope, approach, task checklists, exclusions, and acceptance evidence contract. Checklist state is review evidence, not roadmap lifecycle state. Each task promotes accepted durable information to specifications, architecture, ADRs, implementation tips, operations, or public documentation while keeping the dossier current for all remaining consumers.

Before an epic becomes `Completed`, its final closeout must classify and promote that epic's remaining durable statements and replace its `Detailed SOT` with valid `Canonical Outcomes` links. If another non-terminal consumer epic or canonical roadmap reference remains, keep the shared dossier and this index entry. Only the last consumer epic's closeout removes the index entry and deletes the declared dossier file without archiving a copy, after every consumer is successfully terminal and the approved deletion envelope includes that action. Git history preserves a deleted dossier.

For a dossier linked only from a task in the standing `EPIC-000`, settle its durable content and remove its task link and index entry at that task's approved closeout. Delete the dossier then if no other roadmap consumer remains.

## Adopted Roadmap Work Dossiers

- [Aquarium development environment dossier](TODO-AQUARIUM-DEV.md) preserves EPIC-002's completed history and withdrawn expansion. EPIC-033 is its sole active retirement consumer and settles its historical references before approved deletion; it authorizes no new legacy integration.
- [Astra skill modernization dossier](TODO-ASTRA-SKILLS.md) defines the scope and
  acceptance for `EPIC-012`, `TASK-043` through `TASK-046`, and the local producer
  source checks needed for integration.
- [Web Pro Review dossier](TODO-WEB-PRO-REVIEW.md) defines the standalone review,
  primary-account boundary, selectable `web-pro` route, and acceptance contract for
  `EPIC-017` and `TASK-072` through `TASK-075`.
- [Workflow review corrections dossier](TODO-WORKFLOW-REVIEW-CORRECTIONS.md) maps
  the 2026-09-25 review findings, Aquarium-owned corrections, producer requests,
  and acceptance for `EPIC-018` and `TASK-077` through `TASK-085`.
- [Multi-host unification dossier](TODO-MULTI-HOST-UNIFICATION.md) defines shared
  instructions, host packages, five-host qualification and the single-repository
  migration for `EPIC-030` and `TASK-162` through `TASK-171`.
- [Integrated-tool rollout dossier](TODO-HAEPARI-TOOL-ROLLOUT.md) belongs only to EPIC-032 and existing TASK-091 through TASK-099. It reuses completed tool cleanup, plans Aquarium-owned Haepari workflow guidance and per-tool verification without a blanket producer-return campaign, retains the separate released native Mulgae lock requirement and supplies durable outcomes to EPIC-033 before its own closeout.
- [Combination qualification and retirement dossier](TODO-HAEPARI-COMBINATION-RETIREMENT.md) belongs only to EPIC-033 and existing TASK-100 through TASK-102. It consumes the completed earlier Epics' canonical outcomes, removes unnecessary Haepari integration layers, validators and harness code, verifies the simplified full environment, retires common legacy state under exact authority and settles its own and the historical legacy dossier's references and deletion. Its accepted retirement outcomes are mandatory for v0.1.23 under the [roadmap release prerequisite](../roadmap/README.md#v0123-release-prerequisite).

- [Sorage v0.1.3 adoption dossier](TODO-SORAGE-013.md) belongs to EPIC-035 and TASK-181 through TASK-184; it retains breaking-upgrade, MCP and installed qualification acceptance.

## Unadopted TODO Candidates

There are no current unadopted TODO candidates. A work-definition workflow promotes an approved candidate by allocating the next roadmap-local epic and task IDs, applying the shared dossier threshold, and moving or linking only the resulting approved documents in one reviewed change.
