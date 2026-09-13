# Mulgae Review Contract

Use Mulgae v0.1.19 or a supported later stable v0.1.x release. The same-release
`$use-mulgae` skill owns native execution, retention, cancellation, and recovery.
This contract owns how Aquarium consumes those results within an approved task
or epic review. Read [finding-disposition.md](finding-disposition.md) and
[evidence-residency.md](evidence-residency.md) before adjudication or handoff.

## Delegate Native Execution

Use `$use-mulgae` for asynchronous execution and every native lifecycle decision,
including transport selection, waiting, cancellation, retention, and recovery.
Aquarium supplies the canonical repository, exact complete target, objective,
roles, goal revision, review ordinal, mode, and approved source-transmission
scope. Bind preflight and execution to those same inputs. Current command
responses use `mulgae-command-result.v6`; setup consumes Doctor v2 and review
preflight uses v3. Historical v5 readability does not admit v5 as a current
command response.

Global CLI or required paired-skill gaps belong to `$aquarium:dev-setup-global`;
repository configuration and required project MCP gaps belong to
`$aquarium:dev-setup`. Preserve independent CLI, registration, and connected-tool
readiness. A registered server is not proof that this session exposes its tools.
When the paired skill is optional and unavailable, disclose the gap and use the
selected release's native help and documentation for supported execution. If
that authority cannot be established, return the missing prerequisite rather
than reconstructing a lifecycle from Aquarium examples.

A pending invocation represents unfinished work. It establishes neither review
completion nor a durable run ID. Preserve its identity and delegate continuation to the paired skill. Do not
advance a workflow from a start or cancellation acknowledgement, or infer live
state from completed run inventory. Return terminal run identity and evidence
only when the native result supplies them.

Before delegating a new root, the Aquarium caller must establish an independent
reason and remaining authority for that exact target, mode, ordinal, and goal
revision. Eligible Low settlement and its permitted locally verified delta are
explicit negative authorization for another root. Do not replace a pending or
uncertain invocation, reset an ordinal after context restoration, or run a broad
self-audit under another name to make historical Low findings disappear. A
required first review and a confirmation owed by an earlier Medium-or-higher
correction remain independent reasons to dispatch.

## Accept Recovery Evidence

The approved review envelope may cover missing required roles on the original
immutable capture. Delegate rerun selection and composition to `$use-mulgae`
within the authorized target, roles, provider assignments, and transmission
scope. Request additional authority only for effects outside that envelope or
when the native contract requires it. Do not introduce an Aquarium retry quota.

Accept a composite only after Mulgae has admitted and committed its exact root
and recovery mapping. Verify native target identity and `review_composition`
against the intended review. Diagnostic-only results and legacy reruns without
source-attempt bindings cannot serve as committed recovery evidence. Uncertain
publication remains an operational gap until native recovery establishes its
result; it does not authorize a new root review or consume a round.

## Count and Verify Review Evidence

A round completes only when the full-target root or its verified composite has
terminal authoritative status, `coverage_status=complete`,
`publication_status=committed`, and a successful findings query. Count it once
for the original root within the current goal revision. Preflight, reads,
internal retry or extraction, selected recovery reruns, and composition do not
add ordinals. A completed `request_changes` outcome or failing CI consumes the
round but cannot approve the work.

Record the effective root or composite ID in `review-run-id`. For a composite,
verify the exact root and role sources through its native `review_composition`;
preserve these identities in the bounded runtime handoff. Reconstruct ordinals
from exact recorded evidence and that lineage, without `latest`, objective
inference, or double-counting the root and composite. An unprovable chain stops
before further provider work. Existing sessions retain their original Procedure
snapshot and are not migrated in place.

Approval also requires passing CI and the owning workflow's completed finding
dispositions. Track `structured_extraction_status` independently; `reports_only`
does not waive coverage, publication, CI, or adjudication requirements. After code
or other target changes, recovery of an old capture cannot establish current
review evidence. The next provider review is the next authorized full-target
root round. `followup` and `delta` cannot substitute for it.

When every effective Medium-or-higher finding and confirmation gap is resolved,
the selected review is operationally complete with passing CI, and its finite Low
set has verified dispositions, the owning workflow may advance even though the
source Low count is nonzero. Preserve the original target and report that the
review predates any permitted Low-only correction bytes. Do not describe those
bytes as provider-reviewed.

Verify ordinary findings with the paired skill's supported evidence reads.
Composite findings support status, findings, report, and export, but not CLI
`excerpt` or MCP current-target evidence resources. Verify the supported result
and target identity against current code and authority; do not fabricate an
excerpt or finding-to-source binding. If that evidence cannot resolve a finding,
report the gap and obtain any additional authority required by its disposition.
Report and export writes retain the paired skill's explicit user-request boundary.
Keep raw provider output and runtime artifacts private under the evidence contract.
