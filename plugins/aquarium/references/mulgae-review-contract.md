# Mulgae Review Contract

Use Mulgae v0.1.21 or a supported later stable v0.1.x release. The same-release
`$use-mulgae` skill owns native execution, retention, cancellation, and recovery.
This contract owns how Aquarium consumes those results in an approved Task or
Epic review and in the explicitly requested standalone report-only entrypoint.
Read [finding-disposition.md](finding-disposition.md) and
[evidence-residency.md](evidence-residency.md) before adjudication or handoff.
Read [review-intent-contract.md](review-intent-contract.md) before dispatch to
select `change` or `completion`, construct the Review Brief, assign criterion
responsibility, and preserve the separate aggregate assessment.

## Delegate Native Execution

Use `$use-mulgae` for asynchronous execution and every native lifecycle decision,
including transport selection, waiting, cancellation, retention, and recovery.
Aquarium supplies the canonical repository, exact complete target, Review Brief
through the native objective input, roles, and approved source-transmission
scope. An owning workflow also supplies its goal revision, review ordinal, and
mode. A standalone invocation includes those values only when the request
provides them as context and never manufactures them. Bind preflight and
execution to those same inputs. Current command
responses use `mulgae-command-result.v8`; setup consumes Doctor v2 and review
preflight uses v3. Historical v5, v6, and v7 readability does not admit those
versions as current command responses.

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
reason and remaining authority for that exact target. When an owning workflow
supplies a mode, ordinal, and goal revision, bind the root to them. Eligible Low
settlement and its permitted locally verified delta are
explicit negative authorization for another root. Do not replace a pending or
uncertain invocation, reset an ordinal after context restoration, or run a broad
self-audit under another name to make historical Low findings disappear. A
required first review and a confirmation owed by an earlier Medium-or-higher
correction remain independent reasons to dispatch.

## Accept Recovery Evidence

The approved review envelope may cover every failed selected role on the
original immutable capture, including roles whose persisted `required` flag is
false. Delegate rerun selection and composition to `$use-mulgae` within the
authorized target, roles, provider assignments, and transmission scope. Request
additional authority only for effects outside that envelope or when the native
contract requires it. Do not introduce an Aquarium retry quota.

Inspect the exact root first. A committed incomplete review supplies its failed
attempts through publication-backed state. An unpublished failed or cancelled
review is recoverable only when its verified `failed_run_recovery` reports
`available: true`; preserve its manifest digest, accepted roles, and exact retry
attempts. Never repeat an accepted role or reconstruct a missing or invalid
recovery source from diagnostics. A new root after unavailable recovery needs an
independent reason and remaining review authority.

Run one exact rerun for each failed selected role and verify its committed
publication, target, accepted result, and lineage before composition. A failed
rerun may expose another verified recovery source, but it does not authorize an
unbounded retry loop. Composition must include one accepted recovery for every
missing selected role while preserving all accepted root results.

Accept a composite only after Mulgae has admitted and committed its exact root
and recovery mapping. Verify native target identity and `review_composition`
against the intended review. Diagnostic-only results and legacy reruns without
source-attempt bindings cannot serve as committed recovery evidence. Uncertain
publication remains an operational gap until native recovery establishes its
result; it does not authorize a new root review or consume a round.

## Classify Provider Rate Limits

When MCP `run_review` or terminal `await_review` returns
`provider_rate_limited`, every selected-role qualification failure was a rate
limit and no higher failure class took precedence. Inspect the exact returned
run once. This diagnostic-only result has no accepted role, failed attempt, or
exact rerun source. Do not use doctor or heartbeat to probe the limit, rerun a
role, substitute another provider, or start another root without independent
review authority. The non-retryable mutation result does not mean the provider
condition is permanent. Apply the same rule to a CLI
`provider_qualification_failed` result whose listed reasons are all
`rate_limit`.

A rate limit during provider execution is different. MCP completes with a
successful tool outcome, terminal exit 4, and a `rate_limit` reason; CLI v8
reports the attributed `provider_rate_limited` failure. Reconcile the returned
run. When it committed with incomplete coverage, recover only its failed roles
through the exact flow above. Transport success does not make the review clean.

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

Mulgae runtime-log v4, run-status v3, and invocation-status v2 remain native
diagnostic contracts owned by the same-release paired skill. Safe public
fingerprints and diagnostic summaries do not establish review completion,
coverage, publication, CI, findings, or approval. Keep raw provider session and
turn identifiers private.

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

For completion review, consume every accepted selected-role Markdown report and
aggregate criterion states under the review-intent contract. A clean finding
query does not establish criterion coverage. Missing, unreadable, conflicting,
or silent role evidence remains an assessment gap without changing Mulgae's
native CI, coverage, publication, extraction, finding, or lifecycle facts.
