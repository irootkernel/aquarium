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
- Use the [artifact lifecycle](specs/workflow-contracts.md#disposable-build-and-test-outputs) for disposable build/test cleanup ownership, retention handoffs and Task-transition checks.
- Use the [roadmap](roadmap/README.md) for delivery identity and state, its linked [TODO and work dossiers](todo/README.md) for detailed planned scope and acceptance, and [deferred feedback](deferred-feedback/README.md) for smaller postponed findings rather than adding future behavior to current specifications.

## Epic Squad collaboration

The [Squad entrypoint](../plugins/aquarium/skills/epic-squad/SKILL.md),
[role coordination instructions](../plugins/aquarium/references/epic-squad-native.md)
and [collaboration contract](../plugins/aquarium/references/epic-squad-collaboration.md)
own native, Herdr and mixed role execution, readiness, first assessments,
correction and recovery. The [execution consumer](../plugins/aquarium/references/epic-squad-execution.md)
connects qualified Goal/Validation sources, original evidence and commit/design
handoffs. The original Epic/Task requirements still come from the target
repository's execution SOT. The [workflow specification](specs/workflow-contracts.md#squad-collaboration)
and [orchestration specification](specs/agent-orchestration.md#native-epic-squad-collaboration-source)
map the implemented contracts and their owners.

The shared roles are Coordinator, Epic Evaluator, Task Evaluator, Task Operator
and optional factual Support Operator. Distinct direct EE/TE and author/reviewer
instances follow their assigned native or Herdr routes. Omitted profiles inherit
the current Coordinator's native configuration; explicit CLI/model profiles use
Herdr, including same-CLI sessions, with default effort `high` only when effort
is omitted. Operator pools remain separate from optional support. Profile input
resolution establishes no account/model availability or actual launch.

Each Task retains both plan scopes, its independent first panels and scoped EE
contribution. Corrections use direct checks, eligible local closure and affected
judgment while preserving original findings and evidence applicability. The
Coordinator owns product review, sole Writer transfers, delegated acceptance and
exact commit grants. Fresh Task contexts, continuous EE, fair same-operation
supervision, complete result intake and settled descendants preserve those
boundaries through recovery. Original assignments retain their selected profiles
and requested/applied/observed/unconfirmed settings across directed team changes.
No new native telemetry gate or host configuration audit is added.

Existing Handler/Validator behavior, machine report identities and retained
bindings remain intact. Handler keeps one logical Epic Evaluator and Task
Operator wording without a separate TE or mandatory support pool. The
[roadmap](roadmap/README.md) owns delivery status. The
[installed native observations](../tests/vm/README.md#task-151-candidate-observations)
retain their exact scope; source checks and the
[mixed manual scenario](../tests/vm/recipes/scenarios/epic-squad.md) define checks
and future execution. The [installed mixed observations](../tests/vm/README.md#task-156-candidate-observations)
record named same-CLI role arrangements on the committed TASK-155 payload and
matching harness, with original recovery and correction evidence. Unavailable
CLIs and remaining scenario gaps stay explicit. The Coordinator's native-only
Squad and existing Handler checks remain separate from Master's final overall
Epic acceptance.

## Planned multi-host unification

[EPIC-030](roadmap/README.md#epic-030-unify-aquarium-delivery-across-five-agent-hosts)
plans one development and distribution repository for Codex, Claude Code, Grok,
ZCode/GLM and AGY. The [temporary dossier](todo/TODO-MULTI-HOST-UNIFICATION.md)
defines shared workflow instructions, host-specific invocation and packaging,
initial five-host qualification and migration from separate editions. Current
specifications describe implemented behavior; this plan establishes no installed
support. Final closeout must replace this pointer with the
accepted canonical outcomes before deleting the dossier.

## Haepari adoption and planned release delivery

The [roadmap](roadmap/README.md) orders four complete Epics so each can finish through `epic-handler` before the next begins formal execution. Podway, Dolgorae, Gaori and Sanho may perform their tool-owned aquarium-dev cleanup before or alongside EPIC-031; EPIC-032 later reuses the existing cleanup exchanges and verifies their applicability during its formal rollout.

| Epic | Outcome and canonical scope |
| --- | --- |
| EPIC-019 | [Accepted Haepari adoption](architecture-decision-records/0010-haepari-vm-verification-and-advisory-locks.md): published v0.1.0 CLI/skill setup, fixed profiles, managed VM adapter and the qualified installed policy cutover. |
| EPIC-031 | [Release contract](../plugins/aquarium/skills/release-handler/references/release-orchestration.md) and [preparation/QA handoffs](../plugins/aquarium/skills/release-handler/references/release-preparation.md); implemented [post-QA gates](../plugins/aquarium/skills/release-handler/references/gate-convergence.md) and [publication assessments/recovery](../plugins/aquarium/skills/release-handler/references/publication-recovery.md); [actual UTM verification and directed closeout](../tests/vm/README.md#epic-031-verification-and-directed-closeout) record the exercised behavior, failures and unverified scope; Master closed the Epic before full qualification. |
| EPIC-032 | [Integrated-tool rollout](todo/TODO-HAEPARI-TOOL-ROLLOUT.md): Aquarium-owned Haepari guidance in release/Task/Epic workflows and verification through existing tool commands, with separate released native Mulgae lock adoption. |
| EPIC-033 | [Combined qualification and retirement](todo/TODO-HAEPARI-COMBINATION-RETIREMENT.md): remove unnecessary Haepari integration layers, validators and harness code, verify the simplified installed/upgrade combination and safely remove shared legacy infrastructure. |

The [v0.1.23 release prerequisite](roadmap/README.md#v0123-release-prerequisite) requires completed and verified aquarium-dev retirement, including actual acceptance and approved shared host cleanup. It applies to both full and light releases. Early tool cleanup or a passing test gate alone does not satisfy it.

Haepari v0.1.0 is published; the repository implements setup registration, consumer profiles, host-submitted VM suites (`make test-vm-host`), the uninterrupted `release-acceptance` manual suite (`J-RA`), and qualifies the `TASK-090` policy cutover through [Haepari integration](../plugins/aquarium/references/haepari-integration.md), [tool integrations](specs/tool-integrations.md#haepari), [workflow contracts](specs/workflow-contracts.md#release-a-stable-version), [Haepari VM operations](ops/haepari-vm-verification.md), [TESTING.md](../TESTING.md#host-submitted-managed-vm-suites), and [tests/vm/README.md](../tests/vm/README.md#host-submitted-managed-vm-suites).

EPIC-031's source implements bounded Executor delivery and all four independent release assessments, including post-QA gate/commit binding and original-evidence publication recovery. TASK-175 prepared the integrated scenarios. TASK-176 exercised installed Codex roles in the dedicated UTM VM; its [closeout record](../tests/vm/README.md#epic-031-verification-and-directed-closeout) preserves partial results and unverified scope after Master stopped further qualification for a separate redesign Epic. The [roadmap](roadmap/README.md) owns delivery status and the successor Epics. The guest-side `make test-vm` gate executes inside the held managed Job. [ADR-0010](architecture-decision-records/0010-haepari-vm-verification-and-advisory-locks.md) and the [VM qualification record](../tests/vm/README.md#qualified-pilot-and-limits) preserve the accepted scope and limits. Haepari owns managed Job execution and files; recipes own guest installation/assertions and cleanup. The persistent VM is not reset. Release roles grant no additional execution or publication authority.

Each Epic promotes its accepted durable contracts, obtains actual overall acceptance and settles its own dossier at closeout. Later Epics consume Canonical Outcomes instead of retaining earlier dossiers. EPIC-033 alone retains the historical legacy dossier until its reference and deletion obligations are resolved. Publication and host activation remain separate operations.

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

## Release-role verification methods

[Full release-orchestration scenarios](../tests/vm/recipes/scenarios/release-orchestration.md)
and their [fixed inventory](../tests/vm/fixtures/release-orchestration/cases.json)
prepare integrated development verification. The separate
[managed release startup](../tests/vm/recipes/scenarios/release-acceptance.md#release-startup)
stops at plan readiness. [Testing authority](../TESTING.md#release-orchestration-verification)
distinguishes objective helper checks, fixture effects and actual installed
native results still due under TASK-176. This navigation adopts no directory
agent guides and records no functional acceptance.
