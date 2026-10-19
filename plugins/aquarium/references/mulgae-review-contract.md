# Mulgae Review Contract

Use a stable Mulgae release at or above the supported minimum below. The
same-release `$use-mulgae` skill owns native execution, waiting, retention,
cancellation, and recovery.
This contract owns how Aquarium consumes those results in an approved Task or
Epic review and in the explicitly requested standalone report-only entrypoint.
Read [finding-disposition.md](finding-disposition.md) and
[evidence-residency.md](evidence-residency.md) before adjudication or handoff.
Read [review-intent-contract.md](review-intent-contract.md) before dispatch to
select `change` or `completion`, construct the Review Brief, assign criterion
responsibility, and preserve the separate aggregate assessment.

## Scoped review and native result ownership

Apply [review strategies](review-strategy-contract.md) to the existing Brief:
carry the original goal and due criteria, keep native specialist scopes focused,
and aggregate assigned coverage. Preserve configured roles/providers and use
the native artist for UI-related work when applicable. Keep accepted/rejected
finding responses and their reasons in the next authorized root Brief.

Mulgae alone owns generation, storage, publication and retention. Aquarium's
[result handoff](review-result-handoff.md) checks native publication facts and
reads the returned run under its existing verified-read contract. It does not
add exports, private artifact discovery or another producer receipt protocol.

## Delegate Native Execution

Use `$use-mulgae` for asynchronous execution and every native lifecycle decision,
including transport selection, waiting, cancellation, retention, and recovery.
Aquarium supplies the canonical repository, exact complete target, Review Brief
through the native objective input, roles, and approved source-transmission
scope. An owning workflow also supplies its goal revision, review ordinal, and
mode. A standalone invocation includes those values only when the request
provides them as context and never manufactures them. Bind preflight and
execution to those same inputs.

Before preflight, check the selected native transport's objective size, encoding, and line constraints against the complete Review Brief. Follow the same-release paired skill and tool schema; MCP and CLI limits can differ. If one transport cannot carry the Brief, select another eligible native transport within the existing execution and transmission authority, then use identical inputs for its preflight and execution. Remove only redundant wording, never criteria, scope, provenance, or recovery context. If no eligible input can carry the complete Brief, stop with the exact input gap and request a bounded decision. Do not truncate the Brief, split one assessment into undisclosed reviews, invent a file-input flag, or treat an artifact path as transmitted content without a supported native contract.

Establish the requested Git worktree independently and obtain its native `project_binding` through CLI `context`. Compare it with an attached server's `get_context` before using MCP. Require `project_binding: v1` and `live_source: v1` on the selected Git transport. Pass the independently obtained binding to preflight and execution with identical target, objective, roles and selectors. Select the capable CLI before starting if the attached server cannot establish that root. A binding mismatch stops execution; never bypass it. Current execution intentionally advertises empty `execution_guard` and `capture_identity` capabilities and accepts no request-digest guard. An explicitly requested non-Git workspace uses the native CLI from its independently established canonical root without an expected Git binding. Its empty project binding is an unguarded native workspace path, not evidence of a guarded Git operation.

Select one native target: `workspace`, `stage`, `head`, `commit`, or `diff`. Workspace reads eligible current files, including non-ignored untracked files; tracked files participate regardless of Git ignore patterns. Stage reads the HEAD-to-index transition and index context. Head reads the whole resolved HEAD tree. Commit reads its first-parent transition, with an empty base for a root commit. Diff preserves direct `..` or merge-base `...` semantics. Resolve committed operands once and never substitute workspace or index bytes for them. Empty transitions retain the native provider-free no-change result. Whole-tree workspace and head reviews need no diff.

Mulgae reads the original project through a neutral reviewer home and native read-only restrictions. It creates no source snapshot or full-source replay archive. Its `source_identity_sha256` identifies selector metadata and resolved Git operands, not source content. Keep workspace/index unchanged from preflight until terminal completion, including work by other agents; Mulgae supplies no atomic view, full-tree fingerprint, lock or drift monitor. Report an observed source change as an evidence gap. Reviewers may read relevant support under the native read plan; target selection and Git ignore are not filesystem read barriers. `.mulgaeignore` has no effect and must not be proposed as an exclusion policy.

For a staged Task, the owning handler records base HEAD, the exact index tree OID and complete staged path inventory immediately before preflight and after terminal completion. Compute the tree with `git write-tree` only under the handler's existing staging authority: it writes tree objects without changing refs or index, and a report-only reviewer must not prepare it. Record the caller observation as `unchanged`, `changed` or `unknown`; changed or unknown blocks claims requiring a stable reviewed candidate. Equal endpoint bindings do not erase an intervening change or prove stable worktree context. Preserve relevant workspace/index state throughout the review.

Carry this content binding into reviewed-to-final comparison alongside the separate native selector identity. The final candidate must equal the reviewed basis plus the exact authorized local-settlement, lifecycle and promoted-evidence deltas allowed by the shared finding-disposition contract.

Retain the exact public preflight `target` and metadata digest for downstream v2 evidence. Match that digest to receipt-bound inspection after completion. Inspection exposes the digest but not the full identity or consistency; the shared evidence contract defines canonical digest recomputation and scope-derived consistency without private artifact reads.

Follow native source admission without weakening it: regular files only, whole-selection rejection of unsupported source symlinks, skipped gitlinks, and data-only local Git configuration admission. A conflicted index rejects stage; an unrelated index conflict does not by itself reject a fixed committed target. Preserve typed native reasons rather than rewriting configuration or substituting another target.

The agent that will select the transport or start the review must first load the
installed `$use-mulgae` skill in its own execution context and follow its
same-release instructions. Naming the skill or loading it only in a coordinator
does not load it for a delegated executor. Already loaded guidance may be reused
while its version, scope, and relevant state remain applicable. If the skill or
a required capability is missing, use the prerequisite and fallback contracts
below; do not reconstruct a Mulgae lifecycle from memory or Aquarium examples.

Aquarium supports this minimum release and later stable releases that preserve
or advance its machine contracts:

| Mulgae release | Command envelope | Doctor | Review preflight | Configuration |
| --- | --- | --- | --- | --- |
| Stable `>=v0.1.25` | `mulgae-command-result.v19` or later | `mulgae-doctor-result.v5` or later | `mulgae-review-preflight.v8` or later | Native supported configuration, Config v5 at the minimum |

Reject prereleases and releases below the minimum. SemVer build metadata does
not make an otherwise stable release ineligible. Do not impose an upper release
bound: a later stable CLI remains eligible when its command, Doctor, and
preflight schemas meet these floors. Accept additive fields, reason codes,
and canonical provider family identifiers while preserving the required typed
fields on every reported provider row. Provider membership and order remain
native Doctor authority. A breaking removal of a required field or another
incompatible shape remains an unsupported contract, not a reason to reject a
release number by itself.
Doctor v5 still exposes the field named
`config_v3`; consume that native field name without treating it as the project
configuration version.

Global CLI or required paired-skill gaps belong to `$aquarium:dev-setup-global`;
repository configuration and required project MCP gaps belong to
`$aquarium:dev-setup`. Preserve independent CLI, registration, and connected-tool
readiness. A registered server is not proof that this session exposes its tools.
When the paired skill is optional and unavailable, disclose the gap and use the
selected release's native help and documentation for supported execution. If
that authority cannot be established, return the missing prerequisite rather
than reconstructing a lifecycle from Aquarium examples.

A pending invocation represents unfinished work. It establishes neither review
completion nor a durable run ID. Preserve its identity and delegate continuation
and completion waiting to the paired skill. Do not advance a workflow from a
start or cancellation acknowledgement, or infer live state from completed run
inventory. Return terminal run identity and evidence only when the native result
supplies them.

Let one attached Mulgae process manage its native invocation window. Terminal
identities may be discarded for later admissions; `invocation_limit_reached`
means 64 reviews are still running, not that 64 historical invocations exist.

Once the paired skill starts an operation, Aquarium does not add a competing
observation loop. Do not issue recurring status queries, inspect files or
processes for liveness, start another observer while an earlier observer remains
pending, or start another review to produce a progress update. Repeated bounded
host waits on the same deferred handle are not native polling. If an observer
actually times out or fails, let `$use-mulgae` continue or recover the existing
operation under its native contract. A user-requested progress response uses
only the observation that contract permits and leaves the original operation
authoritative. Aquarium defines no polling interval, universal wait duration,
retry quota, or timeout policy.

Before delegating a new root, the Aquarium caller must establish an independent
reason and remaining authority for that exact target. When an owning workflow
supplies a mode, ordinal, and goal revision, bind the root to them. Eligible local
settlement and its permitted verified delta are
explicit negative authorization for another root. Do not replace a pending or
uncertain invocation, reset an ordinal after context restoration, or run a broad
self-audit under another name to make historical Low findings disappear. A
required first review and a confirmation owed by a correction ineligible for local
settlement remain independent reasons to dispatch.

## Reconcile Incomplete Reviews

Delegate uncertain outcomes and provider-free publication reconciliation to the same-release `$use-mulgae` skill. Preserve one pending invocation and await it before terminal inspection. Inspect only the exact returned run; an unknown identity or `run_status_unavailable` remains an operational gap. Publication reconciliation follows native P0/P1/P2 classification and does not replay source or complete missing role coverage.

New execution has no followup, delta, rerun, recovery-provider replay or compose operation. Historical `failed_run_recovery`, accepted roles, attempts, manifests and composite lineage are verified inspection facts only. They grant no new execution authority. Preserve historical artifacts and use their supported reads without reconstructing inputs from private logs.

An authoritatively not-started preflight or prerequisite failure retains the unused review grant and pending ordinal. `resume-current` returns to preflight and first execution on that same route, preserving the selected arrangement and source-transmission scope. Require native evidence that no invocation or run was created; an uncertain start or `review_preparation_failed` cannot use this path. Refresh the Brief, target, affected verification and applicable staged content binding before the new preflight.

A terminal incomplete or failed review does not consume an assessment ordinal. After native work started, `resume-current` can continue its existing invocation or reconcile publication, but cannot create a replacement run. An explicit `new-review-current-route` direction may authorize one fresh root after the previous operation is authoritatively settled. Preserve its evidence, findings, pending ordinal, goal revision and remaining authority; refresh the authorized Brief, target, affected verification and preflight for current source. The new root must cover the full selected reviewer arrangement. Do not merge accepted roles from separate live runs or silently substitute a provider. A standalone report returns the missing authority rather than granting another review.

## Classify Provider Rate Limits

When MCP `run_review` or terminal `await_review` returns
`provider_rate_limited`, every selected-role qualification failure was a rate
limit and no higher failure class took precedence. Inspect the exact returned
run once. This diagnostic-only result has no accepted role, failed attempt, or
source replay. Do not use doctor or heartbeat to probe the limit, replay a
role, substitute another provider, or start another root without independent
review authority. The non-retryable mutation result does not mean the provider
condition is permanent. Apply the same rule to a CLI
`provider_qualification_failed` result whose listed reasons are all
`rate_limit`.

A rate limit during provider execution is different. MCP completes with a
successful tool outcome, terminal exit 4, and a `rate_limit` reason; the CLI
reports the attributed `provider_rate_limited` failure. Reconcile the returned
run. When it committed with incomplete coverage, retain that result and require explicit authority for a fresh current-source review. Transport success does not make the review clean.

Treat CLI exit 10 with `review_preparation_failed` as an internal failure after
accepted planning but before a durably recorded run start. Preserve its
diagnostic run identity and closed stage, and diagnose that run instead of
substituting Doctor or starting another review. Preserve
`provider_protocol_event_decode_failed` as a typed malformed-event reason while
allowing additive provider telemetry that does not violate the required
protocol event shape. Provider stdout and stderr may use variable-sized
publication support and must not be rejected merely for exceeding the former
fixed-size boundary.

## Count and Verify Review Evidence

A new round completes only when its exact current-source root has
terminal authoritative status, `coverage_status=complete`,
`publication_status=committed`, and a successful findings query. Count it once
for that root within the current goal revision. Preflight, reads, native internal retry or extraction, and provider-free publication reconciliation add no ordinals. A completed `request_changes` outcome or failing CI consumes the
round but cannot approve the work.

Record the exact new root ID in `review-run-id`, its native source identity, consistency mode and publication receipt in bounded runtime evidence. Completed historical evidence may retain its original root/composite lineage; verify it under the original artifact contract and count it once. Reconstruct ordinals from exact recorded evidence without `latest`, objective inference, or counting the same historical root and composite twice. An unprovable chain stops before provider work. Existing sessions retain their admitted snapshots; changed sources require an authorized compatible successor when the snapshot cannot record the current contract.

Approval also requires passing CI and the owning workflow's completed finding
dispositions. Track `structured_extraction_status` independently; `reports_only`
does not waive coverage, publication, CI, or adjudication requirements. After code or other target changes, an old result cannot establish current review evidence. Use the next authorized assessment kind against the precisely supplied current target; no retired child operation substitutes for its root round.

Mulgae runtime-log v4, run-status v3, and invocation-status v2 remain native
diagnostic contracts owned by the same-release paired skill. Safe public
fingerprints and diagnostic summaries do not establish review completion,
coverage, publication, CI, findings, or approval. Keep raw provider session and
turn identifiers private.

When every effective Medium-or-higher finding and confirmation gap is resolved,
the selected review is operationally complete with passing CI, and its finite local
settlement has verified dispositions, the owning workflow may advance even though the
source Low count is nonzero. Preserve the original target and report that the
review predates any permitted locally verified correction bytes. Do not describe those
bytes as provider-reviewed.

Inspect the exact committed publication through the paired skill's verified
read contract. Preserve its `publication_receipt` across every finding page,
finding detail, role report, and indexed-evidence continuation. Read every page
and complete content chunk needed for the judgment; a summary or first chunk is
not a complete finding or report. A changed receipt, cursor, content digest, or
project binding stops that read. Use the capable CLI from the requested root
when the MCP host does not expose a supported resource. Do not read private
runtime files or write a report merely to obtain verified content.

A live result advertises `source_evidence: v1` and `capture_availability=not_captured`; that expected state is not incomplete coverage. Read excerpts with the inspected `source_identity_sha256` and publication receipt. Historical results retain their target-digest selectors. Neither selector hashes today's worktree. Never fill unavailable retained evidence from current files or promote a metadata identity into a content hash.

For a historical composite, use its retained source findings, receipts, role reports,
and indexed evidence when the native read marks each item available. Its copied
evidence does not depend on continued source-run retention. A historical
composite may lack that support; report the evidence gap and withhold any
disposition that requires the missing material. Compare verified retained
evidence with current code and authority before disposition. Report and export
writes retain the paired skill's explicit user-request boundary. Keep raw
provider output and runtime artifacts private under the evidence contract.

For completion review, consume every accepted selected-role Markdown report and
aggregate criterion states under the review-intent contract. A clean finding
query does not establish criterion coverage. Missing, unreadable, conflicting,
or silent role evidence remains an assessment gap without changing Mulgae's
native CI, coverage, publication, extraction, finding, or lifecycle facts.

An owning execution envelope may settle a `local-verified-fix` through the shared finding-disposition contract after this operation is complete and all native admission and CI requirements pass. Preserve the exact root, publication and original criterion assessment. Current completion uses the locally verified composition without calling corrected bytes Mulgae-reviewed. This exception creates no capture, native result, CI pass or hardening-deferral evidence.
