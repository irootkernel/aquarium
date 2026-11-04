# Installed release orchestration

This separately authorized manual feature suite uses the existing managed VM
adapter. It prepares all original EPIC-031 obligations in the
[case inventory](../../fixtures/release-orchestration/cases.json).
TASK-176 observes the exact committed plugin and matching harness in the dedicated
UTM guest. Source tests, prepared fixtures and a native Job verdict do not qualify
skill behavior. The [release startup smoke](release-acceptance.md#release-startup)
is a separate plan-readiness check in J-RA, not this feature suite.

## Admission and baseline

Use the shared explicit `HAEPARI_HOME`, registered `utm-macos` resource and
current supported Haepari CLI/paired skill. The operator owns VM power. Do not
start a controller, create a resource, install on the host or bypass managed
occupancy. Follow [host submission and recovery](../../README.md#host-submitted-managed-vm-suites).

The feature campaign requires `AQUARIUM_VM_BASELINE_PROFILE`, an immutable
existing `aquarium.vm-profile/v1` input matching the actual current host-released
combination and the dedicated guest's starting state. The adapter validates and
seals it; its released Aquarium tag, commit, manifest and skill-tree pins must
agree with local Git objects. It is not a claim that the historical default
profile describes today's installation. The same optional input also serves
release acceptance and scoped native probe callers. Absence preserves their
historical defaults and claims; their operator still selects the policy-due
baseline. Do not automatically discover, repair or install a baseline.

Before admission, select the committed candidate, matching clean test checkout,
approved guest context, hash-locked fixture requirements and sealed official
Podway release input. Retain their exact digests, starting/target profiles and
the native immutable artifact-count/byte pin. Persist the request key and exact
spec before submission. Use the existing host entrypoint with process-local
repository Python on `PATH`:

```sh
make test-vm-host SUITE=release-orchestration MODE=manual \
  HAEPARI=<absolute-cli> RESOURCE=<registered-resource> \
  RUN_DIR=<new-private-physical-run-directory> GUEST_CONTEXT=<private-context>
```

Supply `AQUARIUM_VM_CANDIDATE_SHA`, `AQUARIUM_VM_BASELINE_PROFILE`,
`AQUARIUM_VM_PODWAY_RELEASE` and `AQUARIUM_VM_FIXTURE_REQUIREMENTS` in that
process environment. Select `AQUARIUM_VM_QUEUE_SECONDS` from actual jobs ahead:
`(jobs ahead + 1) * 26100`, within ceiling `86400`. Declared phase budgets are
prepare 1800, manual 21600, collect 900 and cleanup 1800 seconds, with run zero.
These are planning ceilings, not measured sufficiency. Reconnect never extends
them. Retain actual progress and reserve time for staging and restoration.

## Native resource sharing before the main Job

Use independently admitted disposable project callers P and Q with the existing
[minimal manual-hold suite](manual-hold.md) and the same matching baseline,
installation and resource. Each gets its own original request/key/spec and Job;
these are finite scenarios, not retries or replacement Jobs.

1. P reaches actual `awaiting_manual` and holds occupancy. Submit Q and retain
   its genuine queued state while P is held.
2. Complete P's real consumer cleanup, inventory and revision-fenced manual
   completion. Observe native collection/cleanup and actual resource release.
3. Q's already queued original Job then starts execution and reaches its own
   workload/manual-ready state. Prove ordering and non-overlap from original
   native events, Job revisions, resource observations and timeline, not the
   order in which observer commands returned. Do not submit Q again.
4. Finish Q's own consumer cleanup, manual completion and native disposition.
   Verify and retain both exports, including manifests and all declared outputs.

manual-hold installs nothing. Its smoke first validates the existing prior
marketplace/sidecar, plugin registration and status runtime. It refuses a bad
starting state rather than installing a repair. It creates a trivial owned
fixture and can remove only its declared probe leftover with a recorded
preimage. Cleanup removes that fixture and checks retained state.
`discovery-check` stays deliberately `unobserved`, yielding native INCOMPLETE.
Keep that actual result; it can prove resource facts, never skill passage.

A distinct contender R can queue during P's hold and undergo the separately
required queued cancellation. R's cancellation does not prove Q's later
execution. Keep the active-cancel demonstration separate, retaining actual
immutable native outcomes rather than treating acknowledgement as termination.
Run applicable collection/cleanup failure demonstrations as independently
authorized native probes. Reuse accepted EPIC-019 originals only with exact
unchanged-input applicability proof. Preserve every actual failure.

Start the main feature Job after these selected pre-main probes settle. Copy
their complete originals and producer/path/digest mappings into its resource
case evidence. Do not require a pre-completion archive or decision to contain a
later Job's future execution/export. The main Job's own native result/export
necessarily follows its manual completion and is retained by the host afterward.

## Guest phases

Every phase runs from the admitted `<workspace>/harness` through
`guest_entry.sh`, with the saved workload environment and the original
`operator-parent-context.json`. Never print that context or inject its lease
identity manually. Guest phases acquire no resource, submit no Job and never
block on a different nonterminal Job.

```sh
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-orchestration --phase prepare
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-orchestration --phase candidate
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-orchestration \
  --phase case --fixture <inventory-variant-id>
```

`prepare` observes meaningful actual released consumer state before upgrading:
retained sessions/custom sources, configuration, Git work and an unrelated
sentinel. Settle original writers under their installed contract. Candidate
installation and runtime/managed updates are separate concrete operator actions
under existing authority. `candidate` captures exact installed package, tools,
skill identities, configuration and inventory. Neither phase supplies a
functional PASS or installation authority.

Each selected `case` seeds a disposable local release repository with an owned
bare origin and the existing greeting product, then explicitly starts the
installed handler. It records original native request/log/receipt windows.
The operator authorizes effects after reading each assessment. A repeat start
refuses; recover or reply through its existing handle. For an actual operator reply set
`AQUARIUM_VM_REPLY_FILE` to the private reply file and invoke `--phase reply`
with the same variant. `--phase capture` reads public original results without
another provider turn. Capture completion does not establish semantic passage.

Use `--phase reconcile --fixture <inventory-variant-id>` to collect settlement
evidence from the same original invocation without starting or resuming a
provider turn. It binds every original request, input, log and process receipt
to the latest window, retains the public parent/descendant observation and
records terminal settlement separately from role/report assessment.
Reconciliation accepts a genuine recorded Popen launch error before the requested
executable runs. Once the CLI launches, a nonzero or signal exit proves only local
process termination. The recipe requires a recoverable original native handle
and terminal actor evidence before restoration; no other pre-thread no-start
proof is assumed. Missing logs or reports cannot establish no-start.
Known-handle terminal failed or interrupted
parent/child turns and terminal work with missing role reports can still settle.
Their workload or assessment remains failed or incomplete. Successful capture,
including J-RA plan readiness, still requires its original independent roles,
bound reports and due criteria.

Run capture or reconciliation after the latest reply and before restoring
consumers. A later reply, failed native collection or unsettled observation
blocks use of an earlier settlement. Keep active or uncertain actors, commands
and pending writes blocked. Recover a handle from the original log or earlier
windows only when the original process exit is recorded. A missing receipt or
unknown process exit stays incomplete; absent reports prove neither termination
nor no-start. Preserve those originals and reconcile through the native contract
without redispatching a known handle, inventing an exit or starting another Job.

Before EVERY native start/resume, including J-RA startup, pass the fixture-only
hosting environment to the actual process and its children. Resolve `gh` through
that exact `PATH`; require the expected owned regular executable, mode and hash.
Missing, changed, symlinked or wrong resolution stops before native invocation.
Never fall through to production hosting. Git bootstrap/check subprocesses use
process-only configuration and the owned local bare origin; no inherited global
hooks/configuration or credential lookup is needed. An explicit fixture hook
drift case uses only the owned hooks directory. Actual Codex uses the authorized
guest login, without copying host authentication or changing persistent settings.

## Role and release observations

Use the original fixture policy, [release role contract](../../../../plugins/aquarium/skills/release-handler/references/release-orchestration.md)
and each fixed inventory variant. The authorized fixture operator reads each
proposal/result and makes the actual version, mode, first-release, note,
execution, confirmation, equivalence and Git/publication decisions at their
normal boundaries. The initial scope request grants none of those unseen
decisions. Keep one mutating Executor and independent report-only evaluation.
Missing agents or mandatory evidence remain gaps; no Coordinator substitute.

| Fixed case | Original observation obligations |
| --- | --- |
| released-baseline | Meaningful released state, original writers and actual baseline/profile binding. |
| installed-discovery | Exact candidate/harness and fresh installed native Codex roles/configuration; unknown telemetry stays unknown. |
| full-gate-before-commit | Actual delivery and all four boundaries through fixture publication completion, post-hook bytes/parent/delta and hook drift. |
| commit-before-gate | Clean exact release commit, actual gate binding, failed unpushed commit preservation, known-unstarted recovery versus pending/uncertain/failed/stale cases. |
| first-release-full-light | Both orders for previous-release light and confirmed first-release full/light; complete first scope and actual exact-SHA prior-result confirmation. |
| negative-and-drift | Negative readiness, stale/missing/truncated evidence, unavailable required agents and affected-row invalidation before effects. |
| qa-confirmation | Original QA findings, one correction Executor, actual confirmation stop, manifest preparation/readiness before claim, exact claim intake and one permitted confirmation. |
| gate-convergence-neutrality | Public checkpoint suffixes versus final aggregate, QA-affecting stop, all six neutral conditions and actual equivalence approval; no extra QA. |
| publication-recovery | Partial objects, advanced remote, unknown effects, strict v5 routing and original target, highlights versus validation and negative completion. |
| role-replacement | Complete original results, mutating descendant settlement, independent replacement and current applicability/remaining authority. |
| managed-resource-recovery | Actual P/Q non-overlap, separate queue/active cancellation, timeout/lost reply/same-Job reconnect and replacement seam. |
| evidence-cleanup-failures | Separate native workload/evidence/cleanup, consumer cleanup, export failures and preserved retry history. |
| consumer-restoration | Actual starting consumers restored, owned work settled, receipt/inventory staged before native completion. |

For gate-before-commit, assess actual gate-tested metadata bytes before commit,
then verify the post-hook tree, sole release-basis parent and allowed delta.
Commit-before-gate first inspects the clean post-hook commit; a policy-later
gate remains globally unverified until actually run. A failed gate preserves
the unpushed commit and stops before history changes without exact disposition
authority. Diagnostic suffixes never replace an uninterrupted final aggregate.

Known-unstarted recovery requires original proof that no operation began,
unchanged original QA/frozen record or the one approved neutral binding, mode,
notes, pre-QA/light/installed applicability and current commit/input bindings.
Require clean preserved unpushed main, proved remote ancestry and no publication
effect/object. Obtain fresh actual bounded gate-execution authority before
running it. Pending/uncertain work reconnects to the same handle/Job; a missing
report alone proves neither no-start nor failure. Never manufacture gate PASS.

Preserve original QA-native withholding, fresh scenario Executors, both matrices,
FINDINGS/INCOMPLETE precedence and attempt facts. Report the full result before
one bounded correction. After actual confirmation, use the existing deterministic
prepare helper, assess the remediated candidate and exact canonical manifest
before begin, and verify claim manifest/path/digest readback before dispatch.
Negative readiness leaves the claim absent. Preserve superseded manifests and
identical-request recovery; never replay submitted clusters or add an attempt.

For QA-neutral eligibility, independently assess all six original conditions:
original PASS/frozen record; clean direct child/first reuse; proven
non-distributed classification; unchanged scenario/Design Gate/delta inputs;
no weakened tests/product expectation; no other QA-affecting surface. Preserve
separate direct-QA and release-basis identities, actual equivalence approval
and final gate. A report or small diff supplies no permission or extra QA pass.

Publication uses real local Git effects and disclosed hosting stand-in readback
through the unchanged v5 inspector. Re-observe before/after each authorized
effect; skip matching objects and retain the original release target on a
proved remote descendant. Sibling advance, divergence, unknown ancestry or
binding conflicts stop. Reconcile a lost mutation reply before replay. Settle
Executor descendants before replacement and give an independent Evaluator
original criteria/findings/results and current applicability. A negative
completion reports actual objects without rollback or repeated publication.
Retarget and next-cycle headings retain their separate bounded grants.

## Evidence, contributions and completion

Keep original assignments/reports, decisions, native captures, commands/exits,
QA records/claims, gates, Git/hosting objects and cleanup evidence under
`results/release-orchestration/originals/<case>/<variant>/`. Copy external
originals byte-for-byte with producer/path/digest provenance. Preserve failures,
earlier captures and the complete referenced artifact closure. The case index
records candidate/combination and every case's nonempty `required` file list.
Include the original observation requests, native captures and settlement
records in that closure, including failed attempts. They travel inside the
existing case archives; the thirteen cases and 34 declared outputs stay fixed.

Each case's `observations` records every variant's `variant`, actual `status`,
`evidence_class`, `decision_reference` and gaps. Classes are `native-installed`,
`fixture-helper`, `reused-with-applicability` or `unobserved`; reused evidence
also needs its exact `applicability`. Original native-required rows cannot be
filled with helper statuses. Missing work is never PASS. Keep original native
or QA negatives distinct from a successful expected-negative scenario oracle.
Each of the seven original installed table rows has a `native-complete` variant
retaining its entire required observation. One actual operation can cover several
accurately mapped variants; this does not authorize redispatch or another QA pass.

Legitimately separate predeclared campaigns may contribute exact per-variant
evidence through existing ordinary handoffs/indexes. Each owns its complete
resource transaction and cleanup. This does not require extra campaigns for
coverage, omit fixed outputs/cases, extend deadlines or replace an uncertain
original Job. Required actual-native table rows remain due. Other variants
retain only their explicitly permitted evidence classes.

The fixed inventory declares thirteen case tar files, thirteen content
manifests and eight JSON outputs: 34 files. Use `host_suites.json` as the exact
output authority. Stage incrementally with `--phase stage-evidence`, including
before restoration or an authorized early stop. Missing/unsafe originals keep
staging incomplete while available originals travel. Attempts and prior complete
archives survive retry. Native artifact limits own capacity; never truncate
reports to meet the separate J-RA archive ceiling.

Settle all run-owned native operations/descendants and background effects before
restoring the feature campaign's original CLI, full paired skill, plugin
registration/configuration/rules and consumers through the approved path.
`--phase consumer-cleanup` verifies that restoration and seals
`consumer-result.json`; it does not install or restore for the operator. Preserve
failed or malformed inventory history. Feature restoration differs from J-RA's
retained-upgrade end state.
Cleanup requires settlement bound to the exact latest original window and
unchanged native evidence. Verified restoration does not change a failed native
workload, missing role report or negative assessment into a passing case.

Restage the actual cleanup receipt/inventory, verify total outputs against the
saved native pin, then use `--phase complete-template`. Inspect its existing
`haepari.manual-result/v1` template and supply actual installation, revision,
observer and scenario decisions. Consumer cleanup precedes manual completion;
native collection/cleanup/export follow. Verify both native root result/manifest
and every declared output/member digest. Keep occupancy, workload, evidence,
consumer cleanup, native cleanup and assessment separate. Timeout is pending;
lost replies follow original key/spec and native retry hints, never a new Job.

No observation in this prepared suite is already qualified. TASK-176 retains
actual native results and installed identities separately from later document
commits. Payload or relevant harness changes renew affected observations.
Overall Epic acceptance and dossier settlement remain their original later duties.
