# Release-acceptance operator runbook

One release-acceptance Job (J-RA) holds the registered VM continuously from
the first baseline observation through candidate installation, the
scenarios, evidence collection and owned cleanup. The Job's `workload.argv`
performs machine preparation inside `prepare_seconds`; the Job then holds
as `awaiting_manual` and the authorized fixture operator drives every step
below over the operator channel. Every operator phase invocation runs the
supported entry point `tests/vm/recipes/guest_entry.sh` inside
`<workspace>/harness`, with the saved spec's `workload.environment` in the
environment plus `HAEPARI_PARENT_CONTEXT` read from
`<workspace>/operator-parent-context.json`. The entry point derives
`AQUARIUM_VM_JOB_ID` and `AQUARIUM_VM_LEASE_GENERATION` from that context;
never inject them by hand:

```sh
cd <workspace>/harness
export HAEPARI_PARENT_CONTEXT="$(cat ../operator-parent-context.json)"
# with the saved spec's workload.environment pairs exported:
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance \
  --phase <phase> [--fixture <fixture>]
```

The driver interpreter is `AQUARIUM_DRIVER_PYTHON`. The placeholders below
resolve as follows: `<workspace>` is the Job root (`harness/..`), the guest
driver lives at `<workspace>/checkout/tests/vm/run_acceptance.py`, the
request at `<workspace>/acceptance/request.json`, and `<run_root>` is
`<workspace>/acceptance-run`. The in-guest `make test-vm` gate resolves the
Makefile's `PYTHON` from the Job's `PATH` (recorded into
`startup-smokes.json`).

## Budgets and checkpoints

Before sealing and submitting the Job, pass the accepted hash-locked fixture
requirements file in the host environment through
`AQUARIUM_VM_FIXTURE_REQUIREMENTS=<absolute-path-to-the-accepted-hash-locked-file>`
(`host_wrapper.py` reads this path from the environment rather than
`guest-context.json`, and `build_bundle` seals that exact lock file into
`requirements/fixture-requirements.lock` before submission rather than
resolving `latest` inside the Job; `machine-prepare` rejects an absent sealed
lock). Select the queue budget from the live queue position before sealing
(26100/52200/78300 s for zero/one/two Jobs ahead) and pass it through the
wrapper's queue override. The wrapper validates it and never clamps it
silently:

```sh
AQUARIUM_VM_FIXTURE_REQUIREMENTS=<absolute-path-to-the-accepted-hash-locked-file> \
  AQUARIUM_VM_QUEUE_SECONDS=<26100|52200|78300> \
  make test-vm-host HAEPARI=<haepari-bin> RESOURCE=<resource-id> \
  MODE=manual SUITE=release-acceptance RUN_DIR=<run-dir> \
  GUEST_CONTEXT=<guest-context.json>
```

Phase ceilings: prepare 1800, manual 21600, collect 900, cleanup
1800, `run_seconds` 0. Expected phase durations: machine-prepare 10-15 min;
released setups 3 × 5-10 min; preservation prerequisites ~5 min; capture
5-10 min; candidate install and skill identity 5-10 min; runtime update and
reply 10-20 min; managed updates 3 × 5-15 min; startup smokes 2 × 20-45 min
plus replies; stale-skill 5-10 min; staging and cleanup ~10 min. The
expected total is about 2.5-4.5 h inside the 6 h manual window.
Abort-and-rerun checkpoint: if more than 3.5 h of the manual window
are consumed before `startup-smokes` completes, stop without `manual
complete` and settle as follows before any fresh J-RA: (1) settle
every operator-launched Codex session and its descendants, including
smoke child agents, through supported native operations; (2) stage the
partial originals that exist: every case is attempted and its existing originals travel in the declared archives,
with each case's missing required records named in its manifest and
`ok` staying false while any gap remains; (3) record the unfinished
consumer cleanup explicitly; (4) cancel through the native
revision-fenced cancel and await the actual native cancellation
disposition and never stop at its
acknowledgment; (5) then either verify consumer restoration directly,
or let the successor's
`machine-prepare` normalize the recorded residues (the candidate harness
marketplace registration and this candidate's own unselected `-dev.`-stamped
runtime generations, each in a preimage-recorded step while preserving and
listing other candidates' `-dev.`-stamped generations as
`foreign_dev_generations_preserved`) and refuse when the post-restoration
selection is `-dev.`-stamped, when any own generation remains, or when any
other fixture residue exists outside the Job root. Native Job cleanup does
not restore guest installation changes.

## a. Machine preparation (automatic, inside the Job)

`machine-prepare` verifies the sealed artifact bytes, normalizes declared
abort residues, establishes prior-stable v0.1.21, seeds the task and epic
fixtures, prepares the preservation fixture, installs the hash-locked
fixture dependencies, records the non-secret guest Codex identity before
any model turn, and captures the prior-stage skill identity over the five
inventoried scopes. It recognizes the installed CLI's ChatGPT login message
on either stdout or stderr, records only the sanitized login mode, and
refuses an unsuccessful or unverified ChatGPT login before model work.
Outputs: `machine-prepare.json`, `skill-identity.json`
(prior stage) and the `acceptance/request.json` skeleton whose
`baseline_combination` is derived from the stable profile in the driver's
reported shapes (Podway is `v`-prefixed). The request's `codex_args` selects
the native `workspace-write` sandbox and permits the guest's `.aquarium`
and `.local/bin` roots for the approved status-runtime update. The driver
adds its run directory and runs each turn from the selected fixture's Git
root. These are per-invocation permissions; they change no Codex settings
or approval requirements.

## b. Released setup per fixture (released plugin, not the driver's setup op)

The driver's `setup` operation requires the candidate binding and
`baseline.json`, so released-baseline setup uses the native `invoke`
pattern naming the **released** plugin. For each fixture in `task`, `epic`,
`preservation`, capture both the last message and the thread JSONL. The
commands also allow the guest's `.aquarium` directory for the approved
scoped setup status record:

```sh
printf '%s\n' "Invoke the normally discovered installed \$aquarium:dev-setup for <run_root>/<fixture>, scoped only to Podway managed configuration and sources. Use the current installed source and normal concrete proposal/approval boundary. The authorized fixture operator is coordinator-fixture-operator; existing scope authority is epic-019-vm-test-authority. Preserve custom sources, original admitted sessions, Git work and reports. Ask for any actual required decision; this request does not accept an unseen proposal. Settle native agents and return the actual result. Do not commit or publish." \
| "$AQUARIUM_GUEST_CODEX" exec --json --sandbox workspace-write \
  --add-dir <run_root> --add-dir "$HOME/.aquarium" \
  -C <run_root>/<fixture> \
  --output-last-message <run_root>/released-<fixture>.last \
  > <run_root>/released-<fixture>.jsonl
```

When the session asks for a decision, reply through the same thread:

```sh
printf '%s\n' "<actual operator reply>" \
| (cd <run_root>/<fixture> && \
  "$AQUARIUM_GUEST_CODEX" exec --json --sandbox workspace-write \
  --add-dir <run_root> --add-dir "$HOME/.aquarium" \
  --output-last-message <run_root>/released-<fixture>.last \
  resume <thread-uuid> -) \
  >> <run_root>/released-<fixture>.jsonl
```

Record each thread UUID in the request with
`--phase record-setup --fixture <fixture>` and `AQUARIUM_VM_THREAD=<uuid>`.

## c. Preservation prerequisites (matching the driver's `baseline`)

- The customized managed Procedure must still pass:
  `(cd <run_root>/preservation && podway --json procedure check
  --warnings-as-errors .podway/procedures/aquarium-task-v2.yaml)`, saving the
  output to `<run_root>/podway-procedure-check.json`.
- Meaningful uncommitted Git work and a historical report stay in the tree
  (machine preparation created them; commit nothing).
- A released admitted session created through Podway v0.2.14's public CLI
  and verified by `podway --worktree <run_root>/preservation --json observe`
  returning `podway.observation-result/v5`, saved to
  `<run_root>/podway-observe.json`. Session-start command, defined from the
  installed help (`podway help`; `podway --version` is invalid syntax, and
  the version route is `podway version [--json] [--identity]`):

```sh
podway --worktree <run_root>/preservation start \
  --preset sw-dev-v2 --task 'admitted baseline session' \
  --idempotency-key aquarium-vm-release-acceptance
```

The help shape is verified read-only in the guest before submission; the
start itself runs for the first time inside this step, and any flag or
shape mismatch discovered there is reported as a gap, not worked around.

## d. Baseline capture

The `capture` phase calls the unchanged driver's `baseline` in-process and
writes `capture.json` (later cleanup and completion checks require that
file; `baseline.json` alone is insufficient). The old status runtime stays
selected through this capture.

## Podway v0.2.16 transition

Supply `AQUARIUM_VM_PODWAY_RELEASE` with the official release input described
by the [Podway upgrade scenario](podway-upgrade.md). The host seals the archive,
checksum, provenance, CLI and complete paired skill and selects
`podway-candidate` for this suite. The released v0.2.14 baseline remains unchanged.

After baseline capture, update the dedicated guest's CLI and paired skill to
those sealed v0.2.16 bytes through the scoped installed setup proposal. Preserve
the original fixture workspaces and their admitted sessions. Then run:

```sh
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance \
  --phase podway-upgrade
```

This phase verifies the installed dependency and copies each fixture's Git work
into `acceptance-run/candidate-fixtures/`, excluding ignored runtime state.
Candidate operations use generation 2 and observation v6. Original session
preservation is checked through the saved original writer against the unchanged
baseline fixtures; candidate startup uses fresh workspaces. No earlier session
is represented as migrated. Resume uncertain work through its existing handles.

## e. Candidate install and skill identity

The `candidate-install` phase installs the candidate plugin, records the
`candidate` object in the request, and snapshots the candidate state.
The `skill-identity` phase inspects every applicable native scope separately
(shared `~/.agents/skills`, the active `~/.codex/skills`, per-home rules,
plugin-owned assets, project discovery roots, and the non-secret effective
configuration) and compares the installed plugin's whole skill tree
(`aquarium-skill-tree-sha256/v1`) against the candidate profile pin.

## f. Runtime update before any candidate repository setup

Candidate `dev-setup` requires a current status runtime, so the
approval-based update runs now, after candidate installation and before the
candidate repository setups of step g:

```sh
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance \
  --phase runtime-update
```

The invocation names the `$aquarium:dev-setup-global` continuation
explicitly. Only the runtime-update and runtime-reply calls add the native
`-c sandbox_workspace_write.network_access=true` override so the approved
installer can retrieve its hash-pinned wheels. The workspace-write sandbox
stays selected; the saved request and Codex configuration stay unchanged.
Read the proposal at
`<run_root>/operations/runtime-update/NNN.last`, then continue the same
native thread with the operator's actual reply:

```sh
AQUARIUM_VM_REPLY_FILE=<reply-file> \
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance \
  --phase runtime-reply
```

Approval completion is structural: the initial invocation exited 0 with a
thread ID; a reply invocation on the same thread exited 0 with the reply
file's digest; the runtime receipt changed to the candidate's `v`-prefixed
version with its generation created inside the reply window's snapshot
diff; and the recipe itself ran no installer, because the recipe never
drives installer repair.

## g. Managed updates through the candidate

One exact sequence per fixture produces the declared
`managed-update-<fixture>.json` record. For each fixture in `task`, `epic`,
`preservation`, in order:

```sh
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance \
  --phase managed-updates --fixture <name>
```

When the captured setup asks for a decision, read its proposal and continue
the same native thread through the recipe's reply phase, which folds the
reply outcome into the same declared record:

```sh
AQUARIUM_VM_CASE=<name>-setup AQUARIUM_VM_REPLY_FILE=<reply.txt> \
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance \
  --phase reply
```

Then rerun the `managed-updates` phase for that fixture; it reconciles the
existing handle and records the settled outcome. The driver CLI itself is
not the operator path here: it writes no recipe phase record, and a
successful update driven only through it leaves the declared output absent.

## h. Startup smokes (VM-UPGRADE-01, VM-TASK-START-01, VM-EPIC-START-01)

Run the unchanged EPIC-024 gate; `run_gate` verifies the upgrade
(VM-UPGRADE-01) and then dispatches both smokes in fresh Codex sessions:

```sh
AQUARIUM_VM_REQUEST=<workspace>/acceptance/request.json \
  make -C <workspace>/checkout test-vm
```

When a handler asks for a ready-plan or exact-result decision, the operator
reads the proposal and resumes the actual native thread through the driver
(these gate replies are the one operator step that uses the driver CLI;
the phase record comes from the phase itself):

```sh
"$AQUARIUM_DRIVER_PYTHON" -B \
  <workspace>/checkout/tests/vm/run_acceptance.py reply \
  --request <workspace>/acceptance/request.json \
  --case task-startup --reply-file <reply.txt>
```

Use `epic-startup` for the other case, rerun the gate to assess the current
result, and continue until `result.json` settles. Then run the
`startup-smokes` phase through the entry point. It moves any stale
`result.json` aside, reruns the gate once, and passes only when this
invocation's Make exit is 0 and the result it just wrote settles with the
VM-UPGRADE-01 case row present and every observed case explicitly passing;
a row without an explicit outcome stays `unobserved`.

## Release startup

After installed skill identity, approved runtime/managed updates and the existing
Task/Epic smokes, run:

```sh
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance --phase release-startup
```

This is VM-RELEASE-START-01. The normally discovered installed handler uses a fresh
local bare-Git/hosting fixture, a native read-only preparation Executor and an
independent Evaluator. The authorized fixture operator reads concrete proposals
and supplies actual decisions. Before every start/resume the driver propagates
the process-only fixture environment and verifies the expected regular owned
hosting executable identity. A missing/changed/wrong resolution stops before
invocation, without production fallback.

Stop after plan readiness, before settlement commit, pre-QA gates, QA, metadata
or publication. Future obligations remain open. This is not the full development
feature suite. For an actual reply, set `AQUARIUM_VM_REPLY_FILE` and run the same
phase; it resumes the original handle. Missing or negative original reports stay
incomplete. Preserve all invocation windows, assignments, returned reports,
public captures and actual decisions. The fixed `release-startup.json` summary
and `evidence/release-startup.tar` plus content manifest are required outputs;
staging and consumer cleanup cannot pass without this case.

## i. Stale-skill failure and restoration

`--phase stale-skill` asserts the plant target
`~/.codex/skills/task-handler` is absent, snapshots the five inventoried
scopes, plants exactly the prior v0.1.21 artifact's
`plugins/aquarium/skills/task-handler` tree there, observes one fresh
native `skills/list` read, classifies the observed failure (shadowing, duplication, or an
ignored scope, which is a reported gap and never a pass), removes the
planted tree, verifies restoration by full inventory identity (path,
sha256, executable bit and symlink target) across all five scopes plus the
marketplace registrations and normalized `config.toml` settings (`plugins.<id>`,
`features`, skill settings, and top-level non-secret settings) against the
pre-scenario state, and writes `stale-skill.json` with the plant record, the
decision and the restoration evidence. Within `stale-skill` only, differences
that the native `skills/list` read causes under non-`root-kernel` marketplace
caches (`.codex/plugins/cache/<mkt>/...` where `<mkt>` is not `root-kernel`)
are recorded in `restoration.codex_owned_cache_observations` rather than
`restoration_problems`, whereas any drift in `.codex/skills`, `.agents/skills`,
`user-global` (`.aquarium`, `.aquarium-vm-marketplaces`, rules, or normalized
`config.toml`), or `.codex/plugins/cache/root-kernel/` fails restoration.

## j. Evidence staging, consumer cleanup, completion

```sh
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance --phase stage-evidence
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance --phase consumer-cleanup
/bin/sh tests/vm/recipes/guest_entry.sh --suite release-acceptance --phase complete-template
haepari manual complete <job-id> --input <record.json> \
  --expected-revision <job_revision> --json
```

`stage-evidence` writes one fixed-name tar per case
(`evidence/<case>.tar` plus `evidence/<case>.manifest.json`) over the
originals (the released setup sessions, the operation windows, the smoke
case directories with their referenced child reports, native observations,
checks, `baseline.json` and `upgrade-observation.json`, and the
stale-skill originals). The baseline and setup archives also carry native
setup observations, including recovery captures, with their recorded
digest bindings checked before completion. Every driver operation window
requires its input, JSONL and stderr originals; setup windows also require
their before/after records. Every case is attempted, and each manifest
names its missing required records. The Podway precondition outputs are
optional members of the baseline archive. `ok` stays false while a gap
remains.

A retry first marks staging incomplete and withdraws its previous declared
archives, manifests and working files. Source originals and unrelated
outputs remain in place. Each replacement is checked before publication
against the 32 MiB per-archive and 256 MiB aggregate limits, including an
interrupted retry. The collection pin is confirmed in preflight.
`consumer-cleanup` verifies that the tested Aquarium candidate, Podway v0.2.16,
complete paired skill and approved candidate status runtime remain selected.
The dedicated test VM keeps this upgraded combination. Marketplace sources stay
in the persistent guest installation outside the disposable Job workspace.
The post-cleanup inventory records this retained state. Temporary stale-skill
injections are removed and their pre-scenario state is checked separately.
Only then does
`complete-template` emit the closed `haepari.manual-result/v1` record for
the eleven required scenarios, and the operator submits `manual complete`.
Native collection and Haepari-owned cleanup follow; the host wrapper
reconnects with the same `RUN_DIR` and exports last. Missing observations
stay `unobserved` and prevent PASS.

## Session accounting

Model use stays within the guest's existing Codex 0.164.0 installation and
ChatGPT login with its default model, with no new account, endpoint or
provider. The original setup and two startup-smoke population gains one bounded
release-startup Coordinator and its native preparation/Evaluator children.
Record actual threads, resumes, children and model-free reads separately.
Historical time/count estimates do not establish sufficiency for this addition;
plan within the same manual budget with evidence/cleanup reserve, and retain
actual progress. No additional native capability quota is introduced.
`machine-prepare` records the non-secret Codex identity before any model
turn.


## Ouroboros readiness and new-feature scoped review

Before publication, verify these changed behaviors with the exact installed candidate in this dedicated VM. Preserve the released baseline session and original results; these cases do not authorize host installation or power changes.

- With official Ouroboros 0.59.9 and its native Codex setup, run the candidate global inspector for Ouroboros. Rules and skills must be configured without exceptions for the three rewritten sibling-link files. Verify the real home and package byte inventories remain unchanged and temporary probe output is removed. CLI/MCP and live runtime results retain their independent meaning.
- Start a fresh new-feature Design v13 session under a scoped invocation/envelope. Retain the actual user write grant, original requirement pins, candidate file digests, QA and native Executor/Evaluator reports. Observe document application without a separate diff-approval question, then inspect actual file links and request a same-scope correction. Verify that correction and affected QA/checks run without diff reapproval. Include a newly created document with a `create` grant and a later correction linked by continuous before/after history; confirm that existing files still require `update` and deletion requires `delete`.
- Before final acceptance, observe that applied files alone cannot pass final delivery or authorize the required commit. Record actual final content acceptance against the corrected applied digests; verify the final assessment and original Handler/Squad caller return preserve that acceptance and separate commit boundary. For adaptive feature evidence, provide document_write and document_acceptance as actual operator JSON messages and evidence fields; never fabricate them from an agent summary.
- When the final assessment leaves content acceptance unverified, verify that `accepted` is unavailable. Record the actual user acceptance and current digests, then use `reassess` for the affected final criteria. Retain the original pending report and unchanged QA/application evidence; observe a fresh independent assessment, then `accepted` and `achieved`, without rewriting files, repeating unaffected QA or asking for acceptance again. An already current positive final report permits `accepted` without a redundant assessment.
- Introduce a direct user document edit and an out-of-scope target. Preserve the former as an observed in-scope history transition, continue an agent correction from its actual digest and verify the user edit remains in the corrected result. Reject the out-of-scope agent target. Resume after application using original captures and continuous before/after records; do not replace original requirements with revised documents. Explicitly expand the same Epic scope and retain the earlier, narrower grant in its original history. Verify final content acceptance covers all applied files across rounds, and preserve concurrent edits to a file omitted from the latest correction.
- Decline applied content after an initially positive final assessment. Retain the actual rejection or replacement reference and reviewed digests in the ordinary decision record and final evidence index. Verify `not-accepted` is unavailable while the current Evaluator outcome is `achieved`. Use `reassess` to refresh the affected final report from that user evidence without reapplying documents, then record `not-achieved` or `superseded` through the negative-only goal and closeout. Verify no content acceptance, successful delivery, write or commit is fabricated and that the applied files remain available for review. Before negative closeout, request a correction after rejecting an earlier image and verify that the current decision/evidence follows the later request instead of treating the revised files as already rejected.
- Exercise the same user flow with Podway opted out. Also resume the retained version-12 baseline and inspect new-project/refactor/war-room: their exact-diff contracts remain in force. Upgrade managed copies only through approved native setup, leaving active sessions bound to their retained definitions.

Retain actual observed outcomes and missing cases separately from local synthetic test results. Master performs final skill functional acceptance; prepared scenarios alone do not establish it.
