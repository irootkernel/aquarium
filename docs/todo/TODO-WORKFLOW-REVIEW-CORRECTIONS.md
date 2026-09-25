# Workflow review corrections

## Purpose and authority

This dossier is the temporary execution SOT for `EPIC-018` and `TASK-077`
through `TASK-085`. The [roadmap](../roadmap/README.md#epic-018-correct-aquarium-workflow-and-integration-contracts)
alone owns their identities, order, dependencies, and lifecycle. This dossier
owns the findings map, task boundaries, producer handoffs, and acceptance until
the epic promotes durable corrections to their canonical owners.

The input is the 2026-09-25 static review of Aquarium commit `cbba56b` and the
paired tool skills. It reports six unique High and 44 unique Medium findings.
The static review does not prove skill behavior. The scratchpad and reviewer
files remain local evidence, so this dossier records the requirements needed
for execution. Reobserve the exact source bytes before each task. Reproduce
a `PLAUSIBLE` claim before changing behavior; if it does not hold, record
the counterevidence in that task's
handoff. Deduplicate overlapping IDs and settle adjacent Low findings only
when their contract is already being changed.

Aquarium owns its skills, references, Procedures, helpers, packaging, and
public documentation. Gaori, Mulgae, Podway, Sanho, Sorage, and Dolgorae own
their paired skill sources. Aquarium has sent one Sorage request to each of
these six Projects. The requests are broker evidence, not producer completion.
Their dispatch does not itself authorize an inbox or outbox query, another
Handoff, producer edit, installation, activation, commit, release, or
publication. Producer replies and exact source identities feed `TASK-046`;
this epic may close after its Aquarium-owned corrections and
documented handoff even when producer work remains open.

`EPIC-012` keeps its discovery, entrypoint, evidence-reuse, and cross-skill
acceptance scope. `TASK-046` consumes `TASK-085` and the producer source
handoffs.

## Task boundaries and acceptance

### TASK-077: Settle findings and record producer requests

- Build one finding-to-owner ledger from the review: Aquarium H-1 through H-4,
  M-A through M-H; producer H-5/H-6 and M-I; and adjacent Low findings.
  Preserve the report's `CONFIRMED` versus `PLAUSIBLE` distinction and note
  duplicate IDs. Check each claim against the source state used for its request.
- Record the scope of the six already-sent requests to Gaori, Mulgae, Podway,
  Sanho, Sorage, and Dolgorae. Map each request to its source-owned findings
  and expected acceptance evidence. Do not resend a request, inspect an inbox
  or outbox, or invent producer roadmap IDs as part of this task.
- Record the Claude-port installed-copy drift separately for `TASK-046` and
  do not edit installed copies as source.

Acceptance: every High/Medium finding has one accountable owner or an explicit
counterevidence disposition; the six prior requests are accounted for without
another broker operation. Producer implementation remains outside this task.

### TASK-078: Correct external effects and plugin entry

- Carry the existing reviewer prohibitions into the Orca dispatch itself so
  linters, generators, provider reviews, and delegation cannot silently change
  the selected provider or source-transmission boundary (M-D3).
- Disclose and contain the upstream `$pm` file and clipboard effects in the
  design entrypoints and privacy/residency owners (M-E1). Treat clipboard
  mutation as a distinct effect that requires authority before invocation.
- Correct the plugin MCP declaration and package validator for Codex's
  supported key, then verify a fresh installed session exposes the expected
  `aquarium_dev_*` tools (M-F2). Keep CLI diagnosis separately available.

Acceptance: the review instruction carries the same forbidden operations as
the canonical review contract; design invocation does not silently write to
the clipboard; installed plugin loading is observed, not inferred from JSON
parsing alone.

### TASK-079: Correct review-route readiness and recovery

- Reject a new `independent-review` session when its selected Procedure
  snapshot lacks the route. Preserve existing native-Codex sessions through
  an explicit failed-prerequisite disposition, authorized switch, waiver, or
  stop and successor; do not restore retired dispatch for new checkpoints
  (M-A1).
- Define the wait, restart, reviewer-violation, `resume-current`, and native
  Orca retry boundaries without Aquarium-only time or retry limits (M-D1,
  M-D2, M-D4, M-D5). Stage the complete Task candidate before a staged Orca
  review when that route is selected (M-B6, subject to reproduction).
- Align Aquarium's handoff with Podway's requested preapproval observations
  and Mulgae's objective/input limits (M-I4/M-I5); the native skill fixes
  remain producer-owned.

Acceptance: fresh and in-flight sessions select only executable routes;
reviewer source access and recovery stay within the selected target and
provider authority; restart and staged-review scenarios have a defined exit.

### TASK-080: Correct Task, Goal, and Validation Procedure routing

- Route a blocker discovered during Low settlement through the applicable
  rework-authority decision. The Task path must retain a stop choice; Goal
  and Validation must use remaining authority before reporting exhaustion
  (H-1).
- Make the optional Task plan handoff artifact selectable at record time and
  readable at implementation resume, including its digest and size (H-2).
- Align implementation rework preparation, ordinal-four wording, Validation
  audit/remediation order, and final closeout approval and dossier duties
  with the actual graph (M-B1 through M-B5). Remove route claims that no
  Procedure can record. Settle related R1-07 and R3-08 Low paths.
- Revise the managed source and repository-local mirror together; advance
  the three Procedure versions once for this bundle. Update prior-canonical
  digests, fixtures, inspector expectations, and C-08/native qualification.

Acceptance: format, validation, structural and native routing cases prove
blocker authority, plan resume, rework, and stop behavior. Report any
unperformed observed-agent checks separately. The official distribution
artifact gate remains a release-preparation or explicit-check action under
the repository release policy.

### TASK-081: Correct Task closeout and commit handoff

- Narrow the task-commit activation description and apply roadmap-specific
  identity rules only after roadmap enrollment is established (M-C1).
- Carry the record decision from task-close to task-commit on every approved
  completion path (M-C2). Settle task-linked `EPIC-000` dossiers at Task
  closeout (M-C3).
- Place the final document humanizer pass before candidate review (M-C4,
  subject to reproduction) and reconcile authorized validation-remediation
  commits across the validator, epic handler, and task-commit (M-C5).

Acceptance: roadmap and ordinary repository commits follow their distinct
rules; a complete approval handoff reaches one authorized commit without a
missing field or extra permission question; reopened and remediation work
does not inherit normal member-Task authority.

### TASK-082: Correct release helpers and gate sequencing

- Add a real first-release baseline mode to release-QA freeze, load,
  validation, and confirmation helpers. Cover the root commit and current
  public tree without a fabricated previous release (H-3).
- Bind publication title checking to the target repository's commit rule
  instead of Aquarium's hardcoded `[REL]` title. Preserve Aquarium's exact
  release-title requirement when Aquarium itself is the target (H-4).
- Define the Podway compatibility trigger, clean pre-QA candidate SHA,
  rebind-on-change rule, and light-mode confirmation point (M-H1/M-H2).
  Assign active Design Gates to release-QA evidence and give a verified
  remote-main advance a recoverable publication path (M-H3/M-H4).

Acceptance: isolated first-release, alternate commit-title, active-gate,
candidate-change, and remote-advance cases reach the documented result
without weakening exact QA and publication evidence. Actual release mode,
gate execution, commit, push, tag, and hosted Release remain separate decisions.

### TASK-083: Correct installed-package and setup contracts

- Put required references and templates inside the published plugin root;
  reject plugin-internal links that escape it with an objective structure
  check (M-F1).
- Derive the selected tool skill inventory from the resolved release tree
  so new files cannot be silently omitted (M-G1). Reconcile network lookup
  scope, installer version and lock-file disclosures, Gaori timeout policy,
  and natural-language Sorage Project setup routing (M-G2 through M-G5).

Acceptance: an isolated installed-plugin fixture resolves every required
resource; newly added producer files are detected; diagnosis, network lookup,
installation, and Project setup retain their distinct authority boundaries.

### TASK-084: Correct design and status workflows

- Map `$qa` PASS, REVISE, and FAIL to the design Procedure's quality result
  without repeating QA on an unchanged draft (M-E2).
- Define when approved design documents become committed delivery input,
  where war-room investigation notes live, how no-work outcomes are
  recorded, and how `aquarium-status forget` recovers from symlink or reused
  paths (M-E3 through M-E5).

Acceptance: each workflow has an owner and next action for success, revision,
failure, and no-work outcomes; focused helper checks cover executable
behavior while Master retains skill-functional verification.

### TASK-085: Qualify Aquarium corrections and hand off integration

- Recheck the complete finding ledger against the final Aquarium candidate
  and run focused validation for changed helpers, Procedures, package
  resources, and documentation. Run the repository-required gate only at
  its actual lifecycle boundary; do not claim that Ruby or Python tests
  verify skill behavior.
- Prepare the affected manual scenarios for Master: route selection and
  restart, ordinal-four blocker authority, Task plan resume, Orca review,
  first release, installed plugin loading, and authorization effects.
  Report observed outcomes and unperformed scenarios separately.
- Hand producer request and reply identities, exact source status, and any
  remaining cross-tool gaps to `TASK-046`. A missing producer response is
  an open external dependency, not an Aquarium correction claimed complete.

Acceptance: Aquarium-owned High/Medium findings have a verified fix or an
evidence-backed rejection; focused checks pass; required manual results are
confirmed before functional completion is claimed. The final handoff does
not claim producer release, installation, activation, or cross-skill acceptance.

## Producer request map

| Owner | Request scope | Aquarium follow-up |
| --- | --- | --- |
| Gaori | Attached MCP repository/environment proof or native CLI selection (H-5); log and estimate guidance (R8-11/12). | Check the same target and command identity before consuming a result. |
| Mulgae | Attached MCP target proof, objective limits, explicit invocation, cancellation handling, and version references (H-5, M-I5~7, R9-11). | Preserve exact Review Brief and source identity in route integration. |
| Podway | Wait-ready recovery, destructive workspace-mode boundary, custom Procedure checks, and preapproval observation (M-I1~4; R8-08~10). | Accept only the producer's supported native flow. |
| Sanho | Confirm the scoped Low findings on refresh and rejected sync or publish outcomes (R8-06, R8-13/14). | Keep current commit/push authority separate. |
| Sorage | Recovery hints as guidance, pinned-delete authority, guarded Review Note revision, idempotent send, and package/setup wording (H-6, M-I8/9; R9-13~15). | Consume only the requested broker operation and revised native skill. |
| Dolgorae | Provider-child cancellation guidance and reachable installed schema resource (M-I7/10). | Verify the resolved source tree before integration. |

Each producer decides its own task mapping and fixes. `TASK-046` compares
their resulting source trees with the accepted requests. Claude-port installed
skill drift (M-I11) remains a separate installation and acceptance question;
source correction alone does not activate an installed copy.

## Epic acceptance

Complete all Aquarium member tasks in roadmap order while preserving
unrelated work. Keep source changes, observed-agent behavior, exact artifact
qualification, producer handoffs, installation, and publication as distinct
evidence classes. Record any unresolved external finding in the `TASK-046`
handoff without promoting it to an Aquarium-owned fix. At closeout, promote
durable behavior to the canonical skill, Procedure, helper, test, public-doc,
or operations owner and settle this temporary dossier under the shared
execution-SOT contract.
