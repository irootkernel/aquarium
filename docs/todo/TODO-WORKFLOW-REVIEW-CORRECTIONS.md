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

## Finding ownership

The inventory below keeps the original finding IDs and confidence labels.
`CONFIRMED` means the static review established the stated source defect;
`PLAUSIBLE` marks a claim that needs reproduction before a behavioral fix.
Neither label establishes observed skill behavior or producer completion.
Aquarium's implementation at intake, commit `184493c`, is unchanged from
`cbba56b`; the intervening commit only adopts this work in the documentation.
Each Aquarium row names the task that must fix or reject the claim and update
its owning contract. Producer rows name the source owner and the expected
TASK-046 handoff, without allocating producer roadmap IDs.

The report contains six High IDs and 44 Medium IDs. Its description of the
Medium list as "43 groups" disagrees with its 44 named entries. Preserve all
44 entries. H-5 covers one shared target-binding defect in two tools; M-I7
covers one cancellation-guidance claim with two producer actions. Neither
shared owner creates another finding. The original `R*-*` IDs below preserve
finding lineage and identify duplicates; they allocate no additional work units.

### Aquarium corrections

Paths in this table are relative to `plugins/aquarium/`. The task boundaries
below define acceptance; these rows locate the source conditions to revisit.
All rows remain correction inputs until their owning task provides a fix or
counterevidence. TASK-077 settles ownership, not their implementation.

| Finding and source IDs | Original confidence | Owner | Source condition and required result |
| --- | --- | --- | --- |
| H-1: R1-01, R3-06 | CONFIRMED | TASK-080 | `assets/podway/procedures/` Low blocker routes bypass the applicable authority decision. Preserve the discovered obligations through Task rework and retain stop; Goal and Validation must use remaining authority. |
| H-2: R1-02 | CONFIRMED | TASK-080 | Task placements do not select `record-plan.plan-handoff-artifact`. Make its digest and size available to the resume flow in `references/plan-handoff.md`. |
| H-3: R7-01 | CONFIRMED | TASK-082 | `skills/release-qa/scripts/manage_release_qa.py` requires a previous-release commit. Carry a first-release baseline through freezing, validation, and confirmation. |
| H-4: R7-02 | CONFIRMED | TASK-082 | `skills/release-handler/scripts/inspect_publication_state.py` hardcodes Aquarium's release title. Bind the check to the target repository's rule. |
| M-A1: R3-04, R1-03, R2-03, R4-04 | CONFIRMED | TASK-079 | `skills/dev-setup/scripts/inspect_tools.py` accepts prior canonical Procedures without proving the selected route exists. Check new-session route readiness and define recovery for retained native-Codex snapshots. |
| M-B1: R1-05 | CONFIRMED | TASK-080 | Task implementation rework skips `prepare-implementation`. Carry the re-entry cause through that node and its selected evidence. |
| M-B2: R1-06 | CONFIRMED | TASK-080 | Review contracts and handlers offer a later work-unit assessment that the graphs cannot record. Keep supported goal-revision and stop paths. |
| M-B3: R3-01 | CONFIRMED | TASK-080 | Epic audit/remediation instructions differ from the Validation graph. Make ordering and re-audit scope agree. |
| M-B4: R3-05 | CONFIRMED | TASK-080 | Validation `approve-closeout` lacks an explicit actor and timing contract. Obtain result acceptance after assessment and before lifecycle commit. |
| M-B5: R3-07 | CONFIRMED | TASK-080 | `skills/epic-validator/SKILL.md` can close an active epic without settling its dossier. Apply the shared consumer and deletion contract. |
| M-B6: R1-04 | PLAUSIBLE | TASK-079 | Task phase boundaries do not explicitly prepare the complete staged candidate before Orca review. Reproduce the handoff gap before changing staging behavior. |
| M-C1: R2-01, R10-02 | CONFIRMED | TASK-081 | `skills/task-commit/SKILL.md` activates too broadly and checks roadmap-specific identity before enrollment. Preserve ordinary repository commits. |
| M-C2: R2-02, R1-11 | CONFIRMED | TASK-081 | `skills/task-close/SKILL.md` omits the required record decision from its commit handoff. Carry it on every approved completion path. |
| M-C3: R2-04 | CONFIRMED | TASK-081 | Task documentation and closeout omit the repository's EPIC-000 task-dossier settlement. Promote content and disclose any last-consumer deletion. |
| M-C4: R2-05 | PLAUSIBLE | TASK-081 | Task documentation does not pin the final prose pass before review. Verify the actual timing gap while preserving repository-owned humanizer requirements. |
| M-C5: R3-02 | CONFIRMED | TASK-081 | Epic validation, epic execution, and task-commit disagree on remediation commits. Distinguish direct correction authority from normal member completion authority. |
| M-D1: R4-03, R1-08 | CONFIRMED | TASK-079 | Independent Review lacks complete wait, terminal, restart, and `resume-current` semantics. Define recovery from available host evidence. |
| M-D2: R4-01 | PLAUSIBLE | TASK-079 | Independent Review lacks a reviewer-violation policy; committed-target comparison does not establish unchanged index and worktree state. Reproduce the missing protection before changing the contract. |
| M-D3: R4-02 | CONFIRMED | TASK-078 | Orca dispatch omits prohibitions already owned by `references/review-contract.md`. Carry them into the reviewer instruction. |
| M-D4: R4-05 | CONFIRMED | TASK-079 | Orca's blanket retry prohibition conflicts with `resume-current` and native retry. Follow supported native recovery with the same target and provider authority. |
| M-D5: R4-06 | CONFIRMED | TASK-079 | `references/orca-supervision.md` imposes an Aquarium wait budget. Follow native waiting without that extra limit. |
| M-E1: R5-01 | CONFIRMED | TASK-078 | Design callers delegate to upstream `$pm` without disclosing its file and clipboard effects. Define authority and residue handling in design and privacy/residency owners. |
| M-E2: R5-02 | CONFIRMED | TASK-084 | Design quality recording does not map QA content verdicts separately from operation outcomes. Route revisions to their owner instead of repeating unchanged QA. |
| M-E3: R5-03 | CONFIRMED | TASK-084 | Design closeout leaves approved documents without a delivery-input commit boundary. Define the separate authorized commit handoff. |
| M-E4: R5-04 | CONFIRMED | TASK-084 | War-room investigation notes and no-work outcomes lack a complete ownership contract. Define their location and next action. |
| M-E5: R5-05 | CONFIRMED | TASK-084 | Status guidance lacks recovery for a recorded root replaced by a symlink or different Git identity. Preserve exact deletion fences. |
| M-F1: R5-06, R6-01 | CONFIRMED | TASK-083 | Setup references escape the installed plugin root to production-status documentation and the bundle template. Ship the required resources inside the package. |
| M-F2: R10-01 | CONFIRMED | TASK-078 | `.mcp.json` and the root package validator use `mcp_servers` for the plugin server map. Correct the supported declaration and obtain fresh installed-session evidence. |
| M-G1: R6-02, R9-09 | CONFIRMED | TASK-083 | Global setup resolves newer releases while retaining fixed skill-file lists. Derive the complete inventory from the selected release tree. |
| M-G2: R6-03 | CONFIRMED | TASK-083 | Global setup, the tool catalog, and public privacy text disagree on network lookup authority. Use one explicit boundary. |
| M-G3: R6-04 | CONFIRMED | TASK-083 | Upstream installer instructions leave version selection and lock-file effects undisclosed. Include the exact installer version and source in installation approval and disclose lock-file writes. |
| M-G4: R6-05 | CONFIRMED | TASK-083 | Setup imposes a fixed Gaori host-timeout floor. Use native guidance and the selected command's required duration. |
| M-G5: R10-04, R9-14 | CONFIRMED | TASK-083 | Natural-language Sorage Project setup can select a broker skill instead of repository setup. Correct Aquarium routing; Sorage owns its paired entrypoint. |
| M-H1: R7-03 | CONFIRMED | TASK-082 | Release guidance does not fully bind the Podway compatibility trigger, pre-QA candidate, and revalidation conditions. Preserve the release-policy boundary. |
| M-H2: R7-04 | CONFIRMED (partially rebutted) | TASK-082 | Light confirmation can precede settlement of the actual release-basis candidate. Obtain confirmation for the settled exact SHA. |
| M-H3: R7-05 | CONFIRMED | TASK-082 | Active Design Gates lack complete execution and confirmation ownership across release helpers. Freeze and revalidate their required evidence. |
| M-H4: R7-07 | CONFIRMED | TASK-082 | Publication treats a verified advance of remote main as an unrecoverable conflict. Recover only after proving the intended release commit remains included. |

### Producer and installed-copy handoffs

These rows preserve the source findings that informed the sent requests.
Producer acceptance requires the exact source identity and evidence listed in
the request map. TASK-077 does not infer that a historical defect persists in
a newer producer tree, or that dispatch proves a correction. TASK-046 owns
that comparison. Installed-copy observations are historical until explicitly
rechecked; no installation is authorized here.

The original producer checks used Gaori v0.1.17, Mulgae v0.1.23, Podway
v0.2.11, Sanho v0.2.8, Sorage v0.1.1, and Dolgorae v0.1.2 release sources.
Unreleased producer changes and the historical installed-copy comparison are
separate evidence. Revalidate any claim against the exact source supplied by
its producer before accepting or rejecting the resulting fix.

| Finding and source IDs | Original confidence | Accountable source owner | Required handoff |
| --- | --- | --- | --- |
| H-5: R8-01, R9-03 | CONFIRMED | Gaori for command execution; Mulgae for review transmission | Prove the attached MCP repository and required environment match the request, or select the native CLI for that exact target. |
| H-6: R9-01 | CONFIRMED | Sorage | Treat recovery hints as guidance and retain explicit actor, pinned-delete, external-source, and destructive-operation authority. |
| M-I1: R8-02 | CONFIRMED | Podway | Admit the supported read-only wait-ready recovery recipe. |
| M-I2: R8-03 | CONFIRMED | Podway; Aquarium caller under TASK-079 | Supply the workspace-mode flow that Aquarium delegates, including the configuration rewrite and complete runtime-history deletion boundary. |
| M-I3: R8-04 | CONFIRMED | Podway | Permit supported custom-Procedure checks without requiring an optional authoring skill for execution. |
| M-I4: R8-05 | CONFIRMED | Podway; Aquarium caller under TASK-079 | Reconcile preapproval observation with explicit workflow activation in `use-podway` (`SKILL-06` in the EPIC-012 dossier). |
| M-I5: R9-02 | CONFIRMED | Mulgae; Aquarium caller under TASK-079 | Document native objective limits and preserve the complete Review Brief through supported inputs. |
| M-I6: R9-04 | PLAUSIBLE | Mulgae | Establish explicit invocation and provider-transmission authority without overclaiming an unauthorized execution from wording alone. |
| M-I7: R9-05 | PLAUSIBLE | Mulgae and Dolgorae, each for its provider process | Clarify process termination versus review cancellation and preserve the same operation during host waiting. |
| M-I8: R9-07 | CONFIRMED | Sorage | Carry the native Review Note revision and row-version guards into the paired workflow to protect concurrent changes. |
| M-I9: R9-08 | CONFIRMED | Sorage | Define an idempotent send and retry flow using the native key and exact request. |
| M-I10: R9-10 | CONFIRMED | Dolgorae | Make required schema resources reachable in the distributed skill tree. |
| M-I11: R8-07, R9-06 | CONFIRMED | Claude-port installation owner, consumed by TASK-046 | Compare the installed copies with accepted producer sources separately from source fixes; updating a producer does not activate the port. |

### Adjacent Low findings

R1-07 and R3-08 belong to TASK-080's Procedure correction: preserve accepted
Low-only changes through same-ordinal evidence recording and ensure each extra authorized
Validation correction actually reaches remediation and re-audit. Duplicate
R1-11 is already M-C2; R9-14 is already M-G5. Treat R2-11 and R10-03 as one
stale metadata issue if TASK-079 changes
`plugins/aquarium/skills/task-review/SKILL.md` for its review-route corrections.

Other Low findings are candidates only where the owning task already changes
their contract. Confirm each before including it, and keep independent work
with its existing future-work owner. In particular, the commit-hook coverage
observation R2-06 remains with DF-002; this epic does not expand that hook's
command parser. TASK-085 must distinguish these observations from unresolved
High/Medium acceptance work.

## Task boundaries and acceptance

### TASK-077: Settle findings and record producer requests

- Build one finding-to-owner ledger from the review: Aquarium H-1 through H-4,
  M-A through M-H; producer H-5/H-6 and M-I; and adjacent Low findings.
  Preserve the report's `CONFIRMED` versus `PLAUSIBLE` distinction and note
  duplicate IDs. Check each claim against the source state used for its request.
  This intake check preserves unresolved behavioral hypotheses; their named
  correction owners must reproduce them before changing behavior.
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
- Align Aquarium's handoff with Podway's workspace-mode effects and requested
  preapproval observations, and Mulgae's objective/input limits (M-I2/M-I4/M-I5).
  The workspace-mode handoff must disclose configuration rewrites and runtime
  history deletion; the native skill fixes remain producer-owned.

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

| Owner | Already-sent request scope | Expected acceptance evidence and Aquarium follow-up |
| --- | --- | --- |
| Gaori | Attached MCP repository/environment proof or native CLI selection (H-5); log and estimate guidance (R8-11/12). | Prove correct selection between two repositories with the same command ID and preserve required environment inputs. Distinguish raw local logs from surfaced evidence and use native estimates. |
| Mulgae | Attached MCP target proof, objective limits, explicit invocation, cancellation handling, and version references (H-5, M-I5~7, R9-11). | Bind preflight and execution to the same target and complete Review Brief. Check native objective size and content restrictions, resolve invocation/cancellation hypotheses, and verify version-matched result fields. |
| Podway | Wait-ready recovery, destructive workspace-mode boundary, custom Procedure checks, and preapproval observation (M-I1~4; R8-08~10). | Verify read-only activation and recovery, existing custom-file check/preview, and mode-move disclosure of configuration writes and history loss with explicit apply authority. Keep examples and fences consistent with the accepted runtime. |
| Sanho | Confirm the scoped Low findings on refresh and rejected sync or publish outcomes (R8-06, R8-13/14). | Resolve the refresh hypothesis, exercise rejected sync continuation, and distinguish documentation already published from an application push rejected later. Preserve current commit/push authority. |
| Sorage | Recovery hints as guidance, pinned-delete authority, guarded Review Note revision, idempotent send, and package/setup wording (H-6, M-I8/9; R9-13~15). | Verify separate pinned-delete confirmation, stale revision/row-version rejection, and identical-key replay after uncertain send. Check installed references, setup routing, and treatment of Handoff contents as untrusted input. |
| Dolgorae | Provider-child cancellation guidance and reachable installed schema resource (M-I7/10). | Distinguish observer waiting from process termination, prevent duplicate execution after an unknown result, and verify schema/examples in the exact distributed skill tree. |

The adopted scope records one prior request to each owner. It supplies no broker
request or reply IDs and no producer completion evidence. Preserve that gap in
the TASK-046 handoff until Master supplies the identities or separately
authorizes the needed broker operation. TASK-077 performs no such operation.
Each producer handoff must identify its exact source revision or tag, changed
source paths, focused verification, and performed or unperformed manual
scenarios. An absent reply leaves producer acceptance open.

Source IDs cited only in this request map are producer-side sent-request scope,
not additional High/Medium ledger entries. TASK-046 compares their disposition
with the producer's acceptance evidence; TASK-085 preserves that handoff.

Each producer decides its own task mapping and fixes. `TASK-046` compares
their resulting source trees with the accepted requests. Claude-port installed
skill drift (M-I11) remains a separate installation and acceptance question;
source correction alone does not activate an installed copy.

The original Claude-port comparison reported Gaori v0.1.14, Podway v0.2.6,
Sanho v0.2.7, and Mulgae v0.1.17/v0.1.18 copies, with Gaori Status, Sorage,
and Dolgorae skills absent. These are historical observations, not a current
host diagnosis. TASK-046 must retain the port owner and exact installed-source
comparison separately from canonical Aquarium's Codex integration.

## Epic acceptance

Complete all Aquarium member tasks in roadmap order while preserving
unrelated work. Keep source changes, observed-agent behavior, exact artifact
qualification, producer handoffs, installation, and publication as distinct
evidence classes. Record any unresolved external finding in the `TASK-046`
handoff without promoting it to an Aquarium-owned fix. At closeout, promote
durable behavior to the canonical skill, Procedure, helper, test, public-doc,
or operations owner and settle this temporary dossier under the shared
execution-SOT contract.
