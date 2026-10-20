# Aquarium Documentation

This index adopts one canonical documentation model for the Aquarium repository without moving or duplicating its established code-adjacent authorities.

## Audience and Version Scope

This tree is written for Aquarium maintainers and workflow authors. The root [`README.md`](../README.md) remains the user-facing product overview, while [`README.ko.md`](../README.ko.md) remains its maintained Korean translation.

The plugin manifest owns the current package version, the root CHANGELOG owns release history and the one open candidate when present, and the roadmap owns later planned releases. Maintainer documents describe the current checkout and distinguish planned behavior from implemented behavior without duplicating release state.

## Profile and Scope

- Profile: `single-scope`
- Delivery scope: `Aquarium`
- Canonical roadmap: `docs/roadmap/README.md`
- Roadmap namespace: `docs/roadmap/README.md`

## Role Ownership

| Role | Canonical owner | Purpose |
| --- | --- | --- |
| Specifications | `docs/specs/README.md` | Current requirements, implemented behavior, durable contracts, and their exact owning sources |
| Architecture | `docs/architecture/README.md` | Current components, boundaries, data flow, and responsibilities |
| Architecture decision records | `docs/architecture-decision-records/README.md` | Accepted, superseded, deprecated, and rejected decisions with rationale |
| Implementation tips | `docs/implementation-tips/README.md` | Non-normative development, verification, and release guidance |
| Operations | `docs/ops/README.md` | Environment setup, deployment, configuration, diagnosis, recovery, and first-aid runbooks |
| Roadmap | `docs/roadmap/README.md` | Adopted epic and task identity, ordering, dependencies, lifecycle vocabulary, and status |
| TODO and work dossiers | `docs/todo/README.md` | Future epic-sized candidates plus optional detailed scope and acceptance dossiers referenced by complex adopted epics or standing-group tasks |
| Deferred feedback | `docs/deferred-feedback/README.md` | Small actionable findings intentionally postponed from current work |

## Maintainer Navigation

- Start with the [capability specifications](specs/README.md) to identify current behavior and its exact owner.
- Use the [architecture map](architecture/README.md) to trace components, workflow runtime, state, evidence, and verification.
- Read the [accepted decisions](architecture-decision-records/README.md) for durable rationale behind current boundaries.
- Follow the [implementation tips](implementation-tips/README.md) when changing skills, Procedures, inspectors, tests, or releases.
- Use the [operations runbooks](ops/README.md) for environment setup, deployment, recurring failures, recovery, and other operator-facing first aid.
- Use the [roadmap](roadmap/README.md) for delivery identity and state, its linked [TODO and work dossiers](todo/README.md) for detailed planned scope and acceptance, and [deferred feedback](deferred-feedback/README.md) for smaller postponed findings rather than adding future behavior to current specifications.

## Planned Epic collaboration

The [Epic collaboration dossier](todo/TODO-EPIC-COLLABORATION.md) defines planned
`epic-squad` delivery with native agents by default and role-specific Herdr
profiles when supplied. Independent plan and result assessments combine Task/Epic
Evaluators with the Coordinator's project and product review. Task plans receive
detailed Task assessment and Epic direction/continuity/handoff assessment;
the Coordinator uses concise conclusions to assign implementation. All roles
assess missing requirements and unjustified additions; material additions need
a reason tied to existing requirements, and product scope expansion requires
the user's authority.
Each Task starts new Executor and Task Evaluator instances with fresh
conversations where supported, while the Epic Evaluator retains context across
Tasks. The [roadmap](roadmap/README.md#epic-027-add-native-epic-squad-collaboration) owns
implementation order: the native foundation first, then Herdr and mixed execution
in the same skill. Existing Handler/Validator behavior remains unchanged;
`epic-squad` is not implemented yet.

## Directory agent guidance

The [shared contract](../plugins/aquarium/references/directory-agent-guidance.md)
defines scoped canonical-document links, explicit adoption coverage, preservation
and affected maintenance. `dev-setup` now includes basic discovery and maintenance
rules in its root guidance source. `new-project` creates initial documentation
without adopting directory guides. `docs-setup` now defines source-grounded audit,
bootstrap, adoption and migration with explicit coverage and preserved local
instructions. Task and Epic delivery now read sources for affected paths,
maintain canonical documents and guides before review, and preserve the accepted
candidate through commit. [Testing authority](../TESTING.md#directory-guidance-verification)
now links cross-workflow path regressions and independent manual VM scenarios.
The [workflow specification](specs/workflow-contracts.md#directory-agent-guidance)
explains these boundaries, the [component map](architecture/components.md#directory-documentation-flow)
traces their ownership, and [maintenance guidance](implementation-tips/changing-skills.md#maintain-directory-guidance)
covers affected source and link changes. The
[roadmap](roadmap/README.md#epic-029-add-directory-agentsmd-documentation-indexes)
owns delivery status. These contracts do not adopt directory guides in this
repository or update its installed managed guidance.

## Adaptive Procedure work

[Adaptive Procedure contracts](../plugins/aquarium/references/adaptive-procedures.md)
cover goal-specific selection, bounded authoring, whole/fragment composition,
qualification and local retention across all seven handlers. The
[mapped execution contract](../plugins/aquarium/references/adaptive-execution.md)
preserves ordinary Executor/Evaluator reports, selected review and authority through
native execution and exact recovery. Unexpected running-session replacement uses
explicit consent and native atomic preserve-start. Optional
[reusable preservation](../plugins/aquarium/references/procedure-promotion.md)
needs specific content consent. Candidates are normally offered at closeout;
application follows original finalization. A commit needs a separate matching
grant.

[TESTING](../TESTING.md#adaptive-acceptance-scenarios) owns the durable acceptance
scenarios and separates source checks from installed observations. The
[roadmap](roadmap/README.md#epic-026-adapt-goal-adaptive-procedure-orchestration)
tracks delivery status, integrated verification and actual acceptance.
Installed skills and managed sources change only through their authorized update.

## Source-of-Truth Precedence

- `docs/roadmap/README.md` alone owns delivery identity and lifecycle state; TODO and deferred feedback never act as competing status authorities.
- The [Epic Execution SOT contract](../plugins/aquarium/references/epic-execution-sot.md) decides when complex work needs a dossier. A referenced `docs/todo/TODO-*.md` is the temporary development SOT for its consumer epics or linked standing-group tasks, covering detailed goals, scope, approach, task boundaries, and acceptance, but never owns ID, ordering, dependencies, or lifecycle status. Each task promotes accepted durable information to the appropriate canonical role; small epics use their roadmap and canonical documents directly.
- `docs/specs/README.md` owns the specification catalog and declares the exact repository files that own each detailed product contract; the index does not restate those contracts.
- `docs/architecture/README.md` and architecture decision records own current structure and durable design rationale without overriding executable behavior.
- `docs/implementation-tips/README.md` owns guidance for changing, verifying, and releasing Aquarium; `docs/ops/README.md` separately owns environment operation, diagnosis, and recovery guidance.
- The plugin manifest owns the published version, skill entrypoints and linked references own workflow behavior, `plugins/aquarium/references/development-contract.md` and its linked tool code own development-manager behavior, bundled Procedure files own installed Procedure source bytes, and `Makefile` with `TESTING.md` owns executable test behavior and its meaning.
- `CHANGELOG.md` owns cumulative release notes and the planned stable version; `README.md`, `PRIVACY.md`, and `TERMS.md` own the public product, privacy, and authority contracts.
- `tests/vm/` owns reusable manual VM acceptance scenarios and methods referenced by `TESTING.md`. Scenario definitions are distinct from actual candidate-bound execution results.
- A conflict is corrected at the exact domain owner first, followed by any affected index or summary; generated output and ignored runtime evidence never become canonical documentation.

## Roadmap Identity

- Epic IDs match `EPIC-[0-9]{3,}` and task IDs match `TASK-[0-9]{3,}`.
- Epic and task sequences are independent and monotonic within the canonical roadmap, including archives and migration records.
- Task numbering does not restart for each epic, and a number is never reused after deletion, deferral, completion, archival, or migration.
- Identity does not encode execution order; roadmap order and explicit dependencies do.
- `docs/roadmap/README.md` is the namespace. A machine-readable cross-scope reference must use `scope:ID` if another delivery scope is introduced later.

## Language

English is canonical for repository documentation and artifacts. `README.ko.md` is the established Korean translation of the public product overview and must remain aligned with `README.md`.

## Documentation Checks

Run these non-writing checks from the canonical Git root:

```bash
python3 plugins/aquarium/skills/docs-setup/scripts/inspect_docs.py --repository "$(pwd -P)"
ruby -c tests/validate.rb
ruby tests/validate.rb
git --no-pager diff --check
```

The inspector proves conservative structure and roadmap-reference rules only. Semantic review must separately confirm that the indexes match current implementation and authority.
