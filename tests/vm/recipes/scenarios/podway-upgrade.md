# Podway v0.2.15 installed upgrade

This manual suite qualifies EPIC-034's exact Aquarium candidate with the
official Podway v0.2.15 CLI and complete `use-podway` tree. It keeps the qualified
v0.2.14 baseline profiles unchanged. It does not replace a release's separate
release-acceptance gate or turn preparation checks into installed acceptance.

## Authority and sealed inputs

Run only under Master's explicit VM-test authority for the exact candidate SHA,
dedicated guest and installation targets. Disclose the candidate plugin update,
CLI replacement, complete paired-skill replacement, fixture-local runtime
discard, managed updates, native Codex calls and restoration inventory. Each
installation or destructive proposal still needs its applicable approval. The
operator records actual decisions and completes the native Job. Master controls VM power.
Keep one Haepari Job from the original baseline through verified restoration.
Use the existing guest identity and approved provider access; never copy host
credentials or initialize another shared controller.

Prepare an external physical directory containing exactly these regular files:

```text
bin/podway
archive.tar.gz
archive.tar.gz.sha256
provenance.json
skills/use-podway/SKILL.md
skills/use-podway/references/delegation.md
skills/use-podway/references/lifecycle.md
skills/use-podway/references/goal.md
skills/use-podway/references/recovery.md
```

Use the unchanged official v0.2.15 archive, checksum file and provenance; `bin/podway` is their extracted executable. The skill files come
from release commit `9a3f94c8752298f689832d05aa827a0f6496c1af`.
The host sealer checks every file's pinned digest before and after copying,
rejects extra or unsafe files, and performs no installation or upstream-code
execution. The archive is unsigned and not notarized.

Follow the [host-submission runbook](../../../../docs/ops/haepari-vm-verification.md)
for the existing shared home, registered resource, private guest context, accepted
fixture lock, calculated queue budget and new empty physical run directory. Add:

```sh
AQUARIUM_VM_CANDIDATE_SHA="<exact-committed-sha>" \
AQUARIUM_VM_PODWAY_RELEASE="<physical-absolute-release-input>" \
make test-vm-host SUITE=podway-upgrade MODE=manual \
  HAEPARI="<verified-haepari-bin>" RESOURCE="utm-macos" \
  RUN_DIR="<new-empty-physical-run-dir>" GUEST_CONTEXT="<private-guest-context.json>"
```

The bundle seals the dependency under `dependencies/podway-0.2.15/` and creates
`profile/podway-candidate.json`; the existing stable and candidate profiles keep
their previous dependency pins. `SUITE=all` still selects every declared suite
and therefore also requires this explicit release input. It does not install
the dependency in the other suites.

## Observe and upgrade

The suite's `prepare` phase verifies the dedicated guest, sealed inputs, actual
released CLI digest and installed skill identities before capturing
`results/podway-upgrade/prepared.json`. Its original-writer identity call uses
v0.2.14 grammar. Preserve that file and the original inventory; reconnect the
same Job instead of recapturing a baseline.

Operate from the held Job's `<workspace>/harness`, with its saved workload
environment and `HAEPARI_PARENT_CONTEXT` as described in the host runbook.
Store all fixture repositories, before/after captures, native requests, responses
and original public agent handles inside this Job's owned workspace. Do not
develop in the guest.

Complete the following native manual scenarios with original evidence:

| Scenario | Required observation |
| --- | --- |
| `released-baseline` | Create meaningful fixture state through the released installed Aquarium/Podway combination. Include a real admitted session, custom valid Procedure, tracked configuration, staged and unstaged work, and an unrelated sentinel. Record original identities, bytes and installed skill discovery. Finish or explicitly abandon each session through its original writer before replacing that writer; retain the original settlement observations. |
| `writer-refusal` | Install the exact candidate plugin, official CLI and paired skill through the scoped approved setup proposals. Use generation 2 to observe the retained v0.2.14 fixture. Require `WORKSPACE_CONTRACT_MISMATCH`, details v2 naming `v0.2.14` and its stored manifest, and unchanged Store/source bytes. Verify a UUID-fenced reset is refused without effect. Retain the request and original error. |
| `approved-runtime-reset` | Review and approve history loss for each exact disposable fixture. Run the native unfenced reset-all once with its stable key. Retain its committed outcome lookup and confirm a new workspace UUID, no current session and unchanged configuration, Procedures, Git staging, custom sources and unrelated files. No old history is represented as converted or preserved. |
| `skill-discovery` | Capture fresh native discovery and load the actual installed skill. Verify generation 2, observation v6, status v5, executable lifecycle templates, supported semantic arguments and no generation-1 fallback. Exercise setup and current citation/recovery guidance through the installed sources. A pasted skill or standalone acknowledgement does not establish functionality. |
| `task-startup` | Invoke the installed Task handler in a fresh Codex conversation. Observe actual initial Executor/Evaluator delivery and Coordinator progression with native generation-2 evidence, without attributing a delegated decision to Master. Retain the public handles, complete results and the fixture's actual checks. |
| `epic-startup` | Invoke the installed Epic handler in a fresh conversation and observe first-member delivery, independent evaluation and semantic progression. Stop at the approved startup boundary with later criteria open; retain the original results and remaining authority. |
| `consumer-restoration` | Settle every run-owned native handle, then restore the exact original CLI, paired skill, released plugin registration and consumer inventory through the approved restoration path. Preserve original observations for collection; remove only this run's owned temporary effects. Verify restoration before native manual completion. |

For current commands use `--contract-generation 2`. Workspace commands also use
the exact absolute `--worktree`; local help/version/preset/procedure commands
must omit workspace request options. Original-writer settlement uses that
writer's release-tagged skill and grammar, not a fallback in the candidate.

After installation, capture the measured candidate identity and scopes:

```sh
/bin/sh tests/vm/recipes/guest_entry.sh --suite podway-upgrade --phase candidate
```

This requires the earlier baseline and verifies the actual CLI, source/manifest,
paired skill and candidate plugin skill pins against the sealed candidate
profile. It does not mark any functional scenario passed. The
standalone VM observation driver also accepts an explicit
`podway_contract_generation: 2`; it requires v6 and never retries with v5.
Its historical generation-1 baseline behavior remains separate.

## Restoration and native completion

After the approved consumer restoration, run:

```sh
/bin/sh tests/vm/recipes/guest_entry.sh --suite podway-upgrade --phase consumer-cleanup
```

The phase requires the original baseline and candidate captures, checks the
restored CLI and complete skill identities, compares native marketplace and plugin
registration, effective configuration and Codex rules, and checks every
inventoried consumer byte and executable bit against the baseline. A difference refuses
completion; it never normalizes or overwrites the guest. Its PASS covers
consumer restoration only. Functional outcomes remain owned by the seven
native manual scenario results and Master's actual functional observations.

Stage original scenario evidence and the declared output files through native
Haepari collection. Complete the existing manual Job with its current revision,
actual per-scenario verdicts and evidence references using `$use-haepari`.
Unobserved cases remain incomplete. Do not infer acceptance from setup, identity
checks, a helper exit code or a caller timeout. Follow the native collection and
cleanup result; do not report success while restoration or required evidence is
missing.

On disconnect, recover the same Job and public agent handles. Do not repeat
completed phase captures, change request keys, discard recovery files, or create
a replacement Job while its predecessor is unsettled. On a restore mismatch,
preserve evidence and request the exact repair authority. No phase starts,
stops or resets the VM.
