# Workflow review routing

## Purpose and authority

This dossier is the temporary execution SOT for `EPIC-016`. The
[roadmap](../roadmap/README.md#epic-016-add-selectable-workflow-review-routing)
alone owns IDs, ordering, dependencies, and lifecycle state. The reserved
[workflow review routing specification](../specs/review-routing.md) owns the
approved product contract. This dossier maps that contract to implementation
work, acceptance, and handoff boundaries.

The epic removes the mandatory Mulgae dependency from Task, Epic, and cold
validation completion review. Mulgae remains the default. A user may instead
select Orca, a fresh native Codex subagent, or an explicit delegated-review
waiver. A selected backend failure never starts another route automatically.

Registration authorizes no implementation, provider execution, Procedure
installation, staging, commit, release, or publication.

## Scope and task map

| Task | Lifecycle | Delivery boundary |
| --- | --- | --- |
| `TASK-068` | Completed | Generalize review selection, valid evidence combinations, native-evidence deferral eligibility, lifecycle-safe route changes, readiness, waiver, and finding disposition. |
| `TASK-069` | Completed | Deliver the complete Task path, including its skills, Procedure copies, inspector contract, digests, fixtures, and focused tests. |
| `TASK-070` | Completed | Deliver the complete Epic and validation paths, including their Procedures, compatibility checks, commit handoff, hardening deferral, and evidence consumption. |
| `TASK-071` | In Progress | Run cross-route integration qualification, legacy and manual scenarios, and promote current-behavior documentation. |

Implementation proceeds in dependency order. Each task keeps accepted durable
behavior in the reserved specification or the current canonical owner and keeps
this dossier current for the remaining tasks.

## Shared implementation requirements

- Preserve Mulgae as the default and retain its native execution, recovery,
  publication, CI, finding, and retention contracts.
- Bind one route to the approved workflow envelope. Keep it across checkpoints
  until the user explicitly selects a bounded change.
- Check only the selected route's prerequisites. An unavailable route reports
  its own gap without making another optional backend mandatory.
- Preserve each route's source-scope vocabulary, native lifecycle, storage, and
  evidence guarantees. Never claim cross-backend equivalence.
- Require an explicit reviewer for Orca and fresh host delegation for native
  Codex. Both routes remain static and report-only.
- Launch no reviewer for `waived`. Require a complete coordinator assessment,
  current verification, and the ordinary finding dispositions before success.
- Preserve earlier findings and evidence when the route changes. A correction
  never makes the source finding or prior review disappear.
- Treat route-change intent and route-change admission separately. An active or
  uncertain native operation must reach an authoritative state through its owner
  before another reviewer starts or a waiver can support closeout.
- Keep the existing bounded remediation and confirmation authority. A backend
  change cannot reset a budget or create an extra provider call.
- Support ordinary Low dispositions for every route. Keep the promoted
  `hardening-deferral` path Mulgae-only in this epic because it requires Mulgae
  run, finding, publication, query, and native target-digest evidence.
- Do not create `.aquarium`, another project-state file, a repository preference,
  or user-global route configuration.
- Preserve unrelated staged, unstaged, untracked, and ignored runtime work.

## TASK-068: Generalize review routing and evidence contracts

Define the shared contract consumed by every embedded completion review. Update
review intent, finding disposition, evidence residency where needed, and workflow
guidance so route policy is separate from backend lifecycle.

The implementation owner is the
[workflow review routing contract](../../plugins/aquarium/references/review-routing-contract.md).
Handler integration remains with `TASK-069` and `TASK-070`.

The implementation must:

- represent `mulgae`, `orca`, `native-codex`, and `waived` without exposing the
  disabled Independent Review route as selectable;
- define route-neutral assessment ordinals, operation outcomes, evidence
  references, optional backend checks, provenance, and waiver evidence;
- define the valid route, operation, backend-check, evidence-reference, and
  provenance combinations, including rejection of missing Mulgae CI evidence;
- define explicit `resume-current`, `switch-route`, `waive`, and `stop` handling
  with no automatic fallback;
- define separate transition rules for not-started, active or uncertain,
  terminal failed or incomplete, and terminal complete operations;
- distinguish ordinary Low disposition from the Mulgae-only promoted
  hardening-deferral path;
- preserve finding lineage and corrected-target obligations across route changes;
- make readiness conditional on the selected route; and
- extend Orca's contract only enough to accept an authorized handler delegation
  while keeping the leaf review report-only.

Acceptance requires one coherent shared contract with no handler claiming the
reserved behavior before its owning integration task ships.

## TASK-069: Integrate selectable review into Task delivery

Update Task delivery to select and record one workflow review policy. Generalize
`task-review` so it dispatches the selected delegated route or performs the
waiver assessment without duplicating native backend lifecycles.

The implementation owners are `task-handler`, `task-review`, and version 17 of
`aquarium-task-v2`; the inspector contract and focused routing fixtures verify
that compatible unit while legacy Procedure snapshots retain their meanings.

The new Task Procedure version must record the effective route, prior active
route identity, completed and incomplete operations, assessment provenance,
route-specific evidence, and the user's recovery choice. `resume-current` stays
bound to the actual preceding unsettled operation, passes through a
provider-specific authorization decision, and can re-enter only that provider's
existing route entry. It cannot switch providers, resume a waiver, or act as
fallback. Failed attempts do not consume an ordinal. Existing
finding confirmation, completion, priority, owner, Low settlement, goal
assessment, and closeout decisions remain separate.

Version 17 keeps the version 16 evidence contract while splitting route entry,
operation state, evidence, provenance, backend, settlement, and recovery into
route-specific serial decisions that satisfy the Podway lint limits. Each
executable closeout path has one path-owned session-goal assessment followed by
its own bounded outcome and approval chain. Versions 15 and 16 remain admitted
immutable legacy snapshots.

Orca is eligible for a Task only when its complete staged target excludes
unrelated index entries. An unsupported target returns to route selection rather
than changing the index. Native Codex requires a fresh report-only subagent.
Waiver uses the full Task criteria and current verification evidence.

Acceptance covers clean, blocking, Low-only, unverified, failed-operation,
route-switch, and waived paths, including a prior Medium-or-higher finding that
survives the switch and is assessed again on corrected bytes.

The Task change is not complete until the plugin asset and repository-local
Procedure copy match, the inspector-derived canonical structure and digest are
current, and the Task alignment fixtures and focused routing tests pass. Do not
defer a required Task compatibility repair to `TASK-071`.

## TASK-070: Integrate selectable review into Epic delivery and validation

Apply the same workflow policy to member-task review, final whole-Epic review,
and cold validation. Update the Goal and Validation Procedures without combining
direct audit facts, delegated review findings, verification, or completion
assessment.

The implementation owners are `epic-handler`, `epic-validator`, `task-commit`,
the evidence-residency contract, version 20 of `aquarium-goal-v2`, and version 19
of `aquarium-validation-v2`. These versions preserve the version 19 and version 18
workflow meanings while splitting route, operation, provenance, backend,
settlement, and recovery checks into lint-clean serial decisions within the
Podway v0.2.10 authoring bounds. Normal and stopped
assessments use separate outcome, approval, and terminal chains. The applicable
session-goal assessment therefore dominates its terminal. Inspector contracts and
focused route fixtures verify the compatible unit while the exact older admitted
Procedure snapshots retain their original meanings.

Committed Epic and validation candidates may use Orca `HEAD`, commit, or range
targets when the exact scope is supported. Member-task candidates follow the
same isolation rule as Task delivery. A waiver does not remove the final direct
Epic audit or any required verification.

The implementation preserves audit and provider finding namespaces, bounded
confirmation authority, task ownership of remediation, cross-task seam
ownership, and exact commit handoffs. Switching after a completed review uses
the next assessment ordinal. Switching after an incomplete operation retains
the current ordinal.

Update `task-commit`, evidence residency, member-task hardening deferral, and
whole-Epic deferred-evidence consumption in this task. General review handoffs
accept route-neutral evidence. A promoted `hardening-deferral` handoff remains
Mulgae-specific and retains its exact-run, finding-membership, publication,
query, and target-digest checks. Other routes pass an explicit absence and use
the complete ordinary Low-settlement composition. Never fabricate producer
identity or a native digest.

Acceptance covers each route in member goals and whole-Epic validation, failure
and resumption, explicit switching, waiver after an earlier finding, and final
reports that distinguish waived assurance from delegated review.

The Epic and validation changes are not complete until each plugin asset matches
its repository-local Procedure copy, their inspector contracts and digests are
current, and their alignment fixtures and focused routing tests pass. Do not
defer required Goal or Validation compatibility repairs to `TASK-071`.

Compatibility remediation also requires every managed Procedure decision to stay
within eight options and four guards, every placement to stay within eight evidence
references, and every evidence reference to select at most sixteen items. Preserve
all previously selected evidence across serial gates rather than dropping fields to
meet those limits.

## TASK-071: Qualify routing and promote documentation

Run integration qualification across the shared contract and all three already
compatible managed Procedures. This task owns cross-route regression, legacy
session behavior, current-behavior documentation, and Master's separate manual
acceptance rather than repairs required to make an earlier Procedure usable.

Qualification must prove:

- the unchanged Mulgae default path;
- route-specific prerequisite isolation;
- no automatic fallback or provider launch after failure;
- an Orca liveness timeout or Mulgae await timeout followed by `switch-route`,
  with the native operation still active and no second reviewer or waiver
  closeout admitted;
- correct ordinal and lineage behavior across resume, switch, and waiver;
- rejection of invalid evidence combinations, including Mulgae completion with
  `backend-check-result=not-provided`;
- ordinary Low settlement for every route and Mulgae-only hardening promotion;
- completion refusal for failed verification, criterion gaps, confirmation
  needs, unresolved findings, or incomplete Low disposition;
- successful waiver closeout only with coordinator provenance and explicit
  `review waived` reporting;
- refusal of disabled Independent Review without Dolgorae work;
- preservation of immutable legacy Procedure sessions; and
- target rejection without staging, committing, copying, or broadening work.

Run the repository's focused checks, complete `make test`, and
`git --no-pager diff --check`. Run the official Podway v0.2.10 compatibility
gate against the required clean committed candidate before release. Master owns
the separate observed-agent verification of selection, failure recovery,
context reconstruction, and assurance wording.

After acceptance, promote shipped behavior to the capability, workflow, local
interface, public, and release-note owners that it affects. Replace the Epic's
Detailed SOT with Canonical Outcomes during final closeout, remove this dossier
from the TODO index, and delete the dossier only under the approved closeout
envelope.

## Exclusions

This epic does not re-enable Dolgorae Independent Review, add an automatic
fallback order, persist a route preference, change standalone target meanings,
weaken repository verification, or treat a same-provider native subagent as an
independent backend.
