# Exact Haepari combination qualification

Run only under explicit EPIC-033 VM authority. This manual suite uses one outer
Haepari Job P on the registered capacity-one macOS resource. It adds no scheduling
or lock policy. Ordinary tests never submit it. Follow the installed paired skills
and native release contracts for each tool operation.

## Inputs and admission

Use `make test-vm-host SUITE=haepari-combination MODE=manual` with the observed
resource ID, shared `HAEPARI_HOME` and seven-field guest context. Refresh dynamic
readiness and controller identities before submission. Bind the exact committed
Aquarium payload through `AQUARIUM_VM_CANDIDATE_SHA`; test recipes are a separate
git-visible development snapshot. The sealed inputs also record separate SHA-256
hashes of host_bundle.py, host_wrapper.py and host_suites.json. A changed harness
does not relabel the committed payload or qualify it.

Supply `AQUARIUM_VM_BASELINE_PROFILE` for the actual host-installed released
combination reproduced in the guest, rather than a historical profile. In
particular, Codex/Python versions come from the explicit profiles and observed
executables. Preserve older profiles unchanged. Supply
`AQUARIUM_VM_COMBINATION_PROFILE`, an immutable existing-schema
`aquarium.vm-profile/v1` file, and `AQUARIUM_VM_COMBINATION_INPUT`, its physical
regular-file tree. The adapter rebinds only Aquarium's candidate identities.
It preserves host Haepari and Codex/Python baseline declarations and refuses
missing or mismatching binaries and complete skills.

The current input root contains `delivery.json`, ordinary
`case-requirements.json`, the sealed custody manifest and complete skills under
`skills/{use-haepari,use-mulgae,use-gaori,use-gaori-status,use-sorage,use-sanho,use-seongge,use-gaebokchi}`.
Keep duplicate distributions, extracted binaries and source exports out of this
slim root. The complete selected input must fit the native 48MiB aggregate limit.
Both Gaori skills remain separate profile components; Haepari's skill is embedded
in its host component. Keep source pins for Seongge, decoder and Gaebokchi without
inventing release tags. Symlinks and special files are refused.

The finite delivery declaration names only the existing executables and preserves
their profile hashes/source commits. Sorage v0.1.4 and Haepari v0.1.0 use pinned
official GitHub URLs and published checksums. The six unpublished executables use
whole sealed archives or previously verified guest custody. These are complete
executables, never file chunks. One separate artifact-preparation Job may extract
all six whole archives into its disclosed fresh `haepari-artifact-custody/task100-*`
directory. It installs no baseline tool and retains a native-Job-bound receipt for
P. This is one ordinary native preparation Job, with a sealed workload calling
`prepare_artifact_custody`; it is not a new permanent suite or qualification route.
Its sidecar records the actual Job, installation and input-manifest identities
before extraction. `declared_selected_input_digest` comes from the sealed spec
environment; it is not a native observation. Malformed input is refused before
creating persistent custody. An extraction failure retains its sidecar, partial
root and failure facts.

Custody is intentionally retained for P/Q and the current last consumer,
TASK-102. CO owns removal only after verified last-consumer settlement. Record
actual paths, ownership markers, owners and content digests in the preparation
inventory and P's `consumer-cleanup.json`. P preserves the inherited snapshot
inventory and its original recipe digest without adding custody entries.
Retained custody is not a claim that its cleanup is complete.

After baseline observation, run `--phase materialize`. It verifies custody receipts
and actual executable hashes, or downloads the two official assets normally into
P's owned workspace. It records download/checksum receipts, Sorage manifest and
signature observations, and Haepari's complete archived skill comparison. It does
not install a tool. Use the resulting `materialization.json` binary paths for the
manual target installs. Failed or interrupted acquisition is retained for
same-operation reconciliation, without automatic redownload.

The native input digest covers the delivery declarations, skills and any selected
whole archives. It does not cover untransported custody/download bytes. Their
separate receipts and fresh content checks verify those identities. Installed
observations still compare the unchanged profile pins. The identity evidence
archive carries the original acquisition records. Preserve negative signature
observations and keep artifact preparation separate from qualification.

Keep Podway inputs separate, with no copies in the combination root.
Use the existing `AQUARIUM_VM_PODWAY_RELEASE` official v0.2.17 seal layout,
published archive/checksum and all five release-pinned skill files. Supply
`AQUARIUM_VM_PODWAY_PREVIOUS_RELEASE` for a v0.2.16 baseline and its authentic
original-writer test. Current catalog and host_bundle constants own these pins.
If the baseline uses another original writer, preserve it and resolve the
supported writer path before the affected test. Never reset its Store.

## Guest phases and originals

Inside P, reuse its managed parent context and sealed harness. Run
`<guest-python> -B tests/vm/recipes/guest_main.py --suite haepari-combination --phase <phase>`
from the harness directory. No inner case acquires the shared VM again.
`ready` creates a candidate/profile/Job-bound case index with every variant
unobserved. Its result remains INCOMPLETE until manual work is recorded;
the ready command exits zero so the native manual hold can begin.

Retain commands, full outputs/exits, native requests/handles, reports and failures
under `results/haepari-combination/originals/<case>/`. Update that case's
`case-index.json` observations with the actual status, evidence_class,
decision_reference and nonempty Job-relative `required` original-file list.
Use `native-installed`, `fixture-helper`, or `reused-with-applicability`;
reuse requires an explicit applicability record binding exact current
binary/dependency/profile inputs. A stub cannot fill a native-required variant.
Negative source verdicts and future/global gaps stay in their originals.
A behavioral negative case may pass only when its expected refusal is observed.

The recipe does not dispatch providers or decide functional acceptance. Its
phase documents and archives carry observations to native manual completion.
Preserve failed phase files without overwriting them.

| Phase / case | Required execution and original records |
| --- | --- |
| `baseline` / identity | Observe actual released tool/skill identities, meaningful admitted sessions, custom Procedures, configuration, Git index/worktree sentinels and runtime history before replacement. Capture prior plugin skill bytes and actual target profile. |
| `clean-install` | First call creates an empty private Job-owned home and ownership sidecar. Record product absence. Install binaries from the verified `materialization.json` paths, complete sealed skills and the candidate through their supported native paths using process-local HOME/CODEX_HOME and separate paths. For Codex plugin operations use the selected guest executable, `plugin marketplace add <sealed-artifact>`, then `plugin add aquarium@<marketplace>`. Run discovery/use in that home; repeat the phase to observe installed bytes. It must not borrow ambient tool binaries. |
| `transition-upgrade` / upgrade | Observe enabled prior release. Keep `plugins."aquarium@<marketplace>".enabled=true`; apply the native boolean server selector `plugins."aquarium@<marketplace>".mcp_servers."aquarium-dev".enabled=false` in the scoped guest Codex configuration. Verify binding on the actual selected Codex, settle existing consumers, then prove fresh sessions do not launch the channel. Rehearse scoped launcher/runtime absence while preserving released skills, tools and setup/status without implicit reinstall. Do not patch plugin caches. Upgrade only from that observed interim state. |
| upgrade continued | Settle original writers, then update supported binaries and complete skills, candidate plugin, separately authorized status runtime and repository managed files, followed by fresh discovery/startup. Preserve baseline fixtures. Observe newer Podway read/write/original-request-replay refusal on the authentic older Store with unchanged bytes; use new generation-2 candidate workspaces. Capture whether the old server override is accepted after upgrade; if rejected, its scoped removal belongs to the recorded transition. |
| `tool-cases` / tools | Exercise Haepari, Podway, Mulgae, Gaori, Sorage, Sanho, Seongge/decoder and Gaebokchi representative behavior and inter-tool use. Verify actual Task/Epic startup and initial Executor/Evaluator progression plus bounded release-handler plan readiness; stop before settlement commit, pre-QA gates, QA or publication. Record fresh complete skill discovery. Dolgorae/Gul functional adoption remains Deferred; passive residual detachment still belongs to the Task report. |
| `busy-cases` / busy | Hold original Podway writer/session, Haepari Job, Mulgae grant and Gaori invocation. Refuse affected updates while unsettled, retain identities/requests/history/files/results, and resume or wait on those same operations. Settle before replacement. Record refusal by the operator; do not claim a native installer guard. |
| `lock-cases` / locks | Use the isolated guest Haepari controller and same capacity-one lock for CLI/MCP callers; preserve native role concurrency, FIFO serialization, renewal/release, queued cancellation, raced-grant release, borrower validation, loss/drain and expiry-without-physical-termination evidence. No direct-dispatch fallback; unverified drain blocks cleanup. |
| locks continued | Partial-role termination preserves accepted original reports and releases the lock before user-decision wait. Interrupted start/await recovers the original invocation without invented run IDs. A separately authorized new full review takes a fresh FIFO grant without prior-role coverage. Receipt-bound publication reconciliation dispatches no provider and acquires no new lock. |
| `assessment-cases` / assessments | Exercise original EPIC-031 plan, QA-ready, publication-ready and publication-complete evidence consumption through existing isolated native/manual paths. Cover missing cleanup, stale identity, timeout/unknown and Executor replacement; dependent effects remain blocked. Local publication stand-ins only; no new 81-variant campaign. |
| `resource-p` | While P is held, the host submits Q once from the distinct selected Gaori source-bound fixture through native Haepari, without inherited P parent context. Preserve Q's actual queued state and P-local occupancy. Q's presealed profile names P's declared final state. P never requires Q completion. |
| `consumer-cleanup` | Settle all run-owned actors with native receipts, preserve original evidence/history, and manually remove only the settled owned clean-install home. Keep its sidecar. Retain the declared target combination in the dedicated guest; do not restore obsolete binaries. Record final tool/skill inventory, target plugin state, unchanged protected history and actual consumer settlement. Then run this phase to verify current bytes and write the cleanup receipt/inventory. |

Guest stubs are the default for faults, busy/refusal/recovery and isolated
assessment negatives. Live agent/review/startup cases require the existing
approved guest identity, endpoint and budget bound before dispatch. Reuse guest
access through its supported path; never copy host authentication. Missing
live authority leaves that case unverified. No VM reset, history discard,
producer-repository mutation or host cleanup follows from this suite.

## Staging and completion

Run `stage-evidence` incrementally. It emits every fixed archive/manifest pair,
including partial originals and explicit missing requirements. The pairs are
identity, clean-install, upgrade, tools, busy, locks, assessments, resource-p
and cleanup. The declared phase JSON files, case-index, staging index,
inventories, result, consumer-cleanup, inventory-post-cleanup and
manual-complete-template are also required outputs. A failed stage preserves
the previous complete pair and its recovery material.

After verified consumer cleanup, stage again and run `complete-template`.
It refuses stale originals, changed archives/index, incomplete case coverage or
unverified cleanup. Fill only the actual installation identity, observer and
current native revision, and let CO perform revision-fenced native manual
completion. A transport/cleanup result does not replace functional judgments.

Finish P's native collection/cleanup and observe actual capacity release.
Only then can the original queued Q execute. Observe its admitted starting
state, own occupancy and consumer/native cleanup, then export both original
Jobs. Join their receipts/events/exports in the existing Task report to prove
non-overlap; Q's completed result is never an output required inside P.
Preserve deliberate INCOMPLETE results and reconnect to the original keys.

Stop the affected step on source/profile drift, missing scope/input/context,
unsettled work, unsupported transition, failed required checks, unsafe occupancy
or unverified cleanup. Host detachment uses only passive files/configuration and
existing process/service listings; confirm a native observation cannot start a
daemon before using it. Unknown observations remain unknown. Existing Task
report inventory/reduction decisions and all later TASK-101/TASK-102 acceptance
boundaries remain due.
