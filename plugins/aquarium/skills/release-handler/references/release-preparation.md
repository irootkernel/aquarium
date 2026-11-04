# Release preparation and QA handoffs

Use this reference from [release-handler](../SKILL.md) for a publication request.
The [release orchestration contract](release-orchestration.md) owns roles,
original evidence and the four assessment boundaries. This reference implements
preparation, plan readiness, QA readiness and the QA caller seam. Post-QA gates,
publication and recovery follow [gate convergence](gate-convergence.md) and
[publication evidence and recovery](publication-recovery.md).

Finish active releases with their installed workflow before updating. Start new
invocations under the updated contract; old Coordinator summaries do not replace
independent assessments. Current source ships the Codex edition. Development
teams using other CLIs establish no additional shipped host support or installed
qualification. TASK-175/176 retain integrated scenarios and installed observations.

## Route intent and establish roles

Route a retarget-only request through the handler's existing heading-edit branch
before mandatory release-role dispatch. Preserve its baseline/version/conflict
discovery, exact approved heading diff, release-notes inspector, documentation
checks, `intentional no-note` commit handoff and separate commit/push authority.
It requires no new Executor discovery, Evaluator cycle, QA or release publication.
Invalid facts or withheld authority stop the corresponding effect; do not switch
to publication. Next-cycle opening keeps its existing separate path.

For publication, the same Coordinator owns the invocation, user decisions,
assignments, complete result intake, commit handoffs and publication authority.
Use supported native Executors and an independent report-only
[Evaluator](../../goal-evaluator/SKILL.md) in the Coordinator's harness, preserving
supported selected options or defaults. Keep one logical Evaluator when supported.
Read [Executor guidance](../../../references/executor-guidance.md). Missing required
agents or evidence remain gaps; Coordinator self-assessment cannot replace them.
Unavailable private model telemetry remains unknown.

Use ordinary v3 assignments, Executor handoffs and Evaluator assessments. Release
work uses `procedure: null`, leaving unrelated development sessions untouched.
No synthetic roadmap Task, release Procedure, resume manifest or new schema is
needed. Only one mutating Executor may operate in the shared checkout. Settle its
commands, descendants and pending writes before replacement or candidate freeze.

Carry these inputs in existing fields for every bounded assignment:

| Field | Required release content |
| --- | --- |
| `work` | Repository, release objective, intended version, original policy/requirement sources and their revision or approved basis; established baseline ref/SHA or confirmed first-release basis. |
| `target` | Current candidate identity and relevant bytes/diff, proposed outputs, check inputs, included/excluded surfaces and current boundary. A proposal is not yet a settled candidate. |
| `authority` | Actual allowed effects, exact proposal approvals, separate check/installation/Git grants, correction and attempt facts, exclusions and remaining authority. |
| `procedure`, `native` | Null release Procedure context; actual public agent/operation handles, supported configuration observations and explicit unknowns. |
| `evidence`, `results`, `gaps` | Complete original artifacts and command results with provenance, performed/omitted checks, changed paths, uncertain effects, cleanup/retention and next owners. |

The Coordinator reads complete actual handoffs and original artifacts, reconciles
omitted or compound requirements and records pending operations in the existing
conversation/handoff. Keep runtime evidence local under
[evidence residency](../../../references/evidence-residency.md) and
[artifact cleanup](../../../references/artifact-cleanup.md). A verdict grants no
edits, checks, installation, commits, publication, correction or additional QA.

## Deliver preparation and assess the plan

1. Assign substantive read-only discovery and note preparation to bounded Executors.
   Supply the original release instructions, version/notes authorities, exact Git
   baseline/candidate and authorized remote/hosting observations. Preserve ambient
   authentication limits and operations reserved to the Coordinator. First-release
   scope requires actual confirmation and covers complete reachable history and
   current public surfaces without inventing a previous baseline.
2. Require actual handoffs with every material commit/surface mapped to a proposed
   final note or a supported omission, the exact proposed diff, intended output
   inventory, planned gate order/commands/pass conditions, environment and gaps.
   The notes inspector proves structure only. The user retains actual version,
   mode, first-release and proposal decisions. Preserve completed note sections.
3. Supply the independent Evaluator original requirements, discovery handoffs,
   actual decisions, approved note proposal, output and gate inventories, check
   inputs, environment and authority for plan readiness. When VM policy applies,
   name its due boundary, selected controller/resource, planned occupancy span,
   native wait/recovery owner, recipe consumer-cleanup/inventory owner and native
   collection/cleanup owner. Otherwise give the policy-grounded non-applicability
   reason. Planning acquires no occupancy, requires no idle resource and adds no
   VM gate, installation or submission grant.
4. Obtain applicable plan-readiness coverage before a settlement commit or pre-QA
   gate execution. A negative or inconclusive due result stops that effect.
   Assign exact approved preparation edits and their authorized focused checks
   to one Executor; consume its actual changes/results. Before the Coordinator's
   existing `task-commit` handoff, verify the exact approved diff and current
   assessment applicability. Changed scope or inputs refresh affected coverage.
   The settlement commit keeps `intentional no-note` and requires its actual grant.

The Evaluator retains every original criterion's source, provenance, applicability,
state and gap, including unassessed compound parts and future global obligations.
Use the nonfinal `checkpoint_result` for due readiness. Established gaps require
`rework`; evidence gaps remain `evidence-needed`, with both kinds retained when
they coexist. Whole-release passage requires all mandatory original criteria.
The Coordinator checks report completeness and applicability without replacing
the independent judgment. Bookkeeping adds no evaluation cycle.

## Bind the exact QA-ready candidate

After settlement, inspect actual post-hook bytes and require the clean committed
local `main` candidate. Preserve the handler/QA upstream and live remote rules:
record the exact candidate and remote-main SHA with equality or verified ancestry.
Retain original command outputs; cached tracking state is not a live observation.
No fetch, merge, switch, stash, clean or pre-QA push repairs a missing relationship.
Behind, diverged, inaccessible or unprovable state stops as `INCOMPLETE`.

Assign repository-required pre-QA checks to an authorized Executor. Its handoff
retains exact command, artifact/checksum, candidate, environment, transport, exits,
results and gaps. Load the paired tool skill and prove required environment values
survive the chosen transport; do not infer an attached MCP server's environment
from the agent shell. An ordinary development commit starts no distribution gate.
Preserve [pre-QA rebinding](gate-convergence.md#rebind-pre-qa-evidence), separate
gate authority and the target's full/light rules. In light mode, obtain the user's
actual positive confirmation for this settled SHA and its required prior results.
Never claim omitted checks ran or silently switch modes.

Supply the independent Evaluator the original requirements, clean exact candidate,
settled note bytes and material-change coverage, original live remote observations,
due pre-QA results and actual exact-SHA light confirmation. Include original
candidate-bound VM results only when policy makes them due before QA. Keep later
VM obligations pending and distinguish occupancy, workload, evidence completeness,
recipe cleanup and native cleanup from assessment. Use the accepted managed path
when selected by policy; there is no direct-VM fallback or duplicate acquisition.

Complete QA readiness before the full QA handoff. Candidate, requirement, mode or
material check-input changes invalidate affected rows; refresh them before the
dependent effect. Reuse unaffected evidence only with current applicability.

## Call QA and delegate bounded remediation

The same Coordinator invokes [release-qa](../../release-qa/SKILL.md) and directly
assigns its fresh scenario Executors. Preserve the complete original QA-native
brief: exact baseline/delta and cluster objective, fixture-only permissions and
withholding of suspected findings, intended fixes and peer outputs. Do not leak
enclosing assessments into those briefs. Preserve both matrices, fresh-agent
results, source-status observations, frozen records, verdicts and attempt facts.
Existing tests are not release-delta scenarios; QA's Design Gate exception stays
separate. Missing required coverage or agents remains `INCOMPLETE`.

For a full-mode `FINDINGS` result, complete and report the original QA result and
preserve its authoritative frozen evidence before leaving QA mode or editing.
Under the existing bounded remediation authority, assign actual fixes, affected
notes and focused verification to one correction Executor. Require its complete
handoff: changed paths, original findings, actual checks/results, remaining gaps
and settled operations/cleanup. The Coordinator adjudicates that handoff and
retains the actual explicit-confirmation stop before preparing another committed
candidate or invoking QA again. It does not remediate source itself under this
caller branch. Standalone release-QA remediation remains unchanged.

An Evaluator cannot convert QA `FINDINGS` or `INCOMPLETE` to `PASS`. Incomplete
coverage or confirmation failure grants no remediation cycle. Unsupported product
choices, expanded corrections or missing actual confirmation stop the dependent
work. Neither prior approval nor focused success authorizes another QA pass.

## Prepare, assess and admit confirmation

After actual confirmation, prepare the clean remediation candidate through the
existing repository workflow. Rebind remote ancestry, required pre-QA results and
light confirmation; refresh affected plan coverage before settlement or gates
when its scope or premises changed. Preserve the frozen inventory and one attempt.

1. Run only the existing deterministic `prepare-confirmation` helper with the
   canonical full record, current candidate, complete changed-surface mappings
   and exact frozen finding-to-scenario pairs. Use
   `<full-evidence-root>/confirmation-manifest.json`. If a valid earlier manifest
   is superseded within existing non-product preparation authority, retain it
   unchanged and prepare into a fresh nonconflicting
   `<full-evidence-root>/confirmation-manifest-<unique>.json`. Correct only faithful
   mappings/references; preserve original results, candidate and actual attempts.
   Helper rejection stops as `INCOMPLETE`; do not edit or bypass its manifest.
2. Retain the preparer's returned physical `path` and helper-native `digest`.
   `digest(manifest)` hashes sorted-key compact JSON plus a trailing newline via
   `canonical_bytes`; `load_confirmation` separately requires the file bytes to
   equal those canonical bytes. Do not substitute an assumed raw-file SHA for
   this native receipt. Bind the assessed path, canonical digest and unchanged
   bytes in existing evidence fields without adding helper-schema fields.
3. Obtain independent QA-readiness coverage after preparation and before
   `begin-confirmation` creates its claim. Supply the remediated candidate,
   ancestry, due results, frozen record and complete retained coverage, actual
   confirmation and exact current manifest binding. A negative result leaves
   the claim uncreated. Non-product replacement preparation grants no extra
   product correction, scenario execution or attempt.
4. Immediately before begin, compare the current manifest path, native canonical
   digest and unchanged bytes with the assessed binding and refresh candidate-bound
   prerequisites. Supply only that assessed manifest in the begin input; never
   select a superseded valid manifest. Follow QA's existing fresh physical root
   and [native fixture-root bindings](../../release-qa/references/confirmation-bindings.md).
   A mismatch prevents begin; reconcile any already pending operation first.
5. After successful begin, read the actual claim reached through its returned
   receipt. Verify `claim.manifest` equals the assessed physical path and
   `claim.manifest_digest` equals the assessed helper-native digest before any
   scenario dispatch. Retain claim receipt path/digest separately from manifest
   identity. A mismatch or uncertain result stops dispatch and reconciles the
   same actual request/claim without replacement, redispatch or a new attempt.
6. Preserve native exact-request recovery: before settlement admission, identical
   begin may recover the same successful claim receipt. This does not authorize
   replay of submitted clusters; reconcile original dispatch/settlement state.
   After admission, use the same native settlement/recovery contract and admitted
   output, not another begin to authorize dispatch. A helper rejection remains
   `INCOMPLETE`; legitimate same-operation recovery is not an additional pass.

Only applicable readiness, actual confirmation and verified claim intake permit
fresh scenario dispatch. Rerun every retained cluster/scenario and finding
reproduction under QA's fixed inventory and environment bindings, then consume
the original finish result. Nonpassing confirmation stops without another
correction, confirmation or automatic full pass.

Hand [post-QA convergence](gate-convergence.md) and [publication readiness](publication-recovery.md)
original QA records/results, direct-QA candidate, unchanged settled entries, current
pre-QA/light evidence, due or pending VM facts, cleanup/retention and remaining
authority. A passing preparation/QA assessment supplies no publication readiness,
release acceptance or authority for a later effect.
