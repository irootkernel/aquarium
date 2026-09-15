# Procedure Node Contracts

This reference maps Aquarium's managed Procedure nodes to their owning
capabilities. Podway records caller-supplied evidence and enforces declared graph
transitions. It does not load skills, run tools, authenticate approval, validate
semantic truth, or own Git and roadmap state.

For every node, reconstruct the exact work unit, current target, attempt, goal
revision, authority, and selected evidence after context restoration. Read complete
selected values through digest-bound evidence pagination when the bounded preview
is insufficient. A transition edge does not make predecessor evidence available
unless the placement selects it.

## Task Procedure

| Node family | Capability and required input | Boundary and result |
| --- | --- | --- |
| Plan and implementation entry | `task-handler` records the approved `task-plan` result and exact re-entry cause | No implementation before approval; return a bounded plan and authority basis |
| Implement | `task-implement` consumes the selected plan and implementation-entry summary | No staging, lifecycle edit, review, commit, or publication; return exact task-owned changes and focused evidence |
| Refine | `task-refine` consumes the current implementation result | Limit work to authorized cleanup and return the exact refined target |
| Verify | `task-verify` consumes the current refined target and requirement matrix | No review or commit; return a typed current result and check identities |
| Document | `task-document` consumes current implementation, refinement, verification, and verification decision evidence | Update canonical current behavior without copying runtime history |
| Review and serial routing | `task-review` receives the exact full target, ordinal, mode, and source scope; `task-handler` adjudicates confirmation, CI, completion, finding class with a finding-count consistency guard, rework authority, then implementation, verification, and documentation ownership | Native counts remain descriptive; inconsistent totals return to review before finding classification; phase obligation totals alone select owners after authority is admitted; each confirmation-only correction consumes one fresh `fix-and-review` decision when it leaves the user-choice node, so repeated rework stops at a new unset choice; no phase can bypass an earlier failing gate |
| Low settlement | `task-handler` consumes the frozen Low set and delegates only disposition-owned local work | Return exact source basis, dispositions, carried completion summary and zero gap counts, target delta, checks, pending count, blocker count, and coverage; no provider review solely for Low |
| Assessment and closeout | `task-handler` consumes the carried completion summary and gap counts, their consistency when present, and any user direction before `task-close` and an independently authorized `task-commit` | A stop direction must assess the goal as not achieved; non-achieved work cannot close, and actual user approval plus exact final-target composition remain required |

## Goal Procedure

`epic-handler` owns goal-centered member, remediation, and closeout work. It does
not invoke the task phase skills. `complete-work` returns the work summary, source
revision, and conditional plan-handoff artifact. `record-evidence` returns the goal
kind, review-evidence kind, typed verification and review-readiness results, and
applicable review and finding records.
Operational evidence, finding confirmation, completion, finding class, rework
authority, and Low handling form a serial routing chain. Finding-count consistency
is a guard axis of the finding-class decision. Unverified completion
returns to evidence; unmet completion and Medium-or-higher findings share the
explicit authority gate. Inconsistent finding totals return to evidence before
classification. A first adequate Low-only review alone records either
finite settlement or the supported bounded hardening handoff. The derived
`current-rework-obligations` total is not part of the contract. The final-closeout substitute is valid only
for `goal-kind=epic-closeout` with exact successful validation evidence. Goal
assessment consumes the carried completion summary and gap counts, their
consistency when present, and any user direction. A stop direction must produce a
not-achieved assessment rather than closing the goal.

Each `choose-user-direction: fix-and-review` decision authorizes its one transition
back to work and the next review ordinal. Later rework reaches a fresh unset choice;
no recorded authorization survives the pass or context restoration. The narrow
second-review hardening handoff remains available when independently reached, but
no caller starts a second review merely to qualify for it.

## Validation Procedure

`epic-handler` uses validation for final epic audit and `epic-validator` uses it
for cold validation. Baseline, audit, remediation, re-audit, final review, user
direction, Low settlement, assessment, and closeout stay inside one validation
session. Audit evidence separates operational result, unresolved confirmation,
current blockers, eligible Low findings, and total confirmed findings. Total count
is descriptive and never routes remediation by itself.

Blocking corrections return to remediation only within the caller's existing
envelope and keep their triggering set. A required corrected-target confirmation
still runs. Low-only audit or confirmation results use local settlement without a
new broad audit. Final review preserves applicable audit and provider identities
under separate namespaces, then admits operation, finding confirmation, completion,
required evidence, and current blockers through separate serial decisions before
the final Low-or-validated choice. When another Medium-or-higher correction needs authority,
select the supported `user-direction` route, record only the current issue set and
exhausted authority at `await-user-direction`, complete that action, and stop at
`choose-user-direction` with the actual choice unset until the user answers.
Validation assessment consumes the carried completion summary and gap counts,
their consistency when present, and any user direction. A stop direction must
produce a not-achieved assessment rather than validating or closing the epic.

## Design Procedure

`new-project`, `new-feature`, and `refactor` own context, discovery, drafting,
challenge, quality, exact-diff approval, document application, assessment, and
closeout. Ouroboros results are leaf evidence. Discovery and drafting do not
authorize implementation. Quality does not authorize applying a draft. Approval
binds the exact document diff, and application does not authorize staging, commit,
publication, or product implementation. Optional branch evidence remains optional
at merges.

## War-room Procedure

`war-room` owns safe baseline or reproduction, competing hypotheses, cause and
scope judgments, proposal quality, exact-diff approval, document application,
assessment, and closeout. Baseline-quality corrections return to the baseline
owner; classification and proposal corrections return through investigation or
the exact supported draft target. Terminal success delivers an approved task,
epic, or incomplete-investigation document. It never implements the fix or changes
shared services, stages, commits, or publishes by implication.

## Compatibility classification

Native-valid means the Podway validator admits the declaration. Handler-compatible
means the known required node IDs, item types, selected evidence, and guarded or
rework routes are present. A safe cosmetic customization may be compatible. A
missing obligation is incompatible. A semantic customization whose equivalence
cannot be established is unqualified. Preserve every customized file and request
the existing supported replacement choice; never overwrite, migrate a session, or
start a substitute workflow automatically.

The executable required-node, item, choice, evidence, and route inventory is
`PODWAY_HANDLER_CONTRACTS` in
`skills/dev-setup/scripts/inspect_tools.py`. Its structural classification does not
prove that customized instructions have equivalent meaning or that Podway executed
or verified any external work.
